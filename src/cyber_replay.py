# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Cyber replay sequences — capture foreign uplink intercepts, then re-broadcast.

Workflow (scripted / future MCP agent)
--------------------------------------

1. **Tune** your team's RF to the victim carrier using :func:`replay.tune_ground`
   (same as listening on that frequency in the Operator UI).
2. **Subscribe** to ``Downlink`` via :meth:`SpaceRangeClient.register_downlink_handler`.
3. Parse **Format = 3** frames (:mod:`src.downlink_codec`) and keep records where
   ``addressed_to_us`` is **False** (foreign / not-for-us traffic).
4. After *N* captures, optionally **save** JSON and **schedule** a replay at a
   future **simulation time** using :class:`InterceptReplaySequence`.

Requires **intercept** enabled on your spacecraft (``enable_intercept`` in scenario)
or you will never receive Format 3 records.

Call :meth:`InterceptReplaySequence.tick` from your ``on_session`` callback with
``session["time"]`` so replay fires at the chosen sim deadline.
"""

from __future__ import annotations

import base64
import json
import random
import threading
from dataclasses import asdict, dataclass
from typing import Any, Callable, Optional, TYPE_CHECKING

from . import downlink_codec as dc
from . import printer
from .replay import RFLinkSnapshot, replay_transmit_bytes, tune_ground

if TYPE_CHECKING:
    from .config import TeamConfig
    from .mqtt_client import SpaceRangeClient


@dataclass
class CapturedWire:
    """One stored on-air prefix from an Uplink Intercept record."""

    payload_b64: str
    rx_frequency_mhz: Optional[float]
    sim_time: float
    flags: int
    addressed_to_us: bool
    parse_ok: bool

    @classmethod
    def from_intercept(cls, rec: dict[str, Any]) -> "CapturedWire":
        raw = rec["payload"]
        return cls(
            payload_b64=base64.standard_b64encode(raw).decode("ascii"),
            rx_frequency_mhz=rec.get("rx_frequency_mhz"),
            sim_time=float(rec.get("sim_time", 0.0)),
            flags=int(rec.get("flags", 0)),
            addressed_to_us=bool(rec.get("addressed_to_us")),
            parse_ok=bool(rec.get("parse_ok")),
        )


class InterceptReplaySequence:
    """
    Stateful capture + delayed replay at a simulation time.

    Parameters
    ----------
    client:
        Connected :class:`~src.mqtt_client.SpaceRangeClient`.
    """

    def __init__(self, client: "SpaceRangeClient"):
        self._client = client
        self._team_password = client._team.password
        self._caesar_key = client._team.key
        self._lock = threading.Lock()
        self._listening = False
        self._needed = 3
        self._captures: list[CapturedWire] = []
        self._replay_at_sim: Optional[float] = None
        self._replay_rf: Optional[RFLinkSnapshot] = None
        self._replay_sent = False
        self.on_capture_complete: Optional[Callable[[list[CapturedWire]], None]] = None
        self.on_replay_complete: Optional[Callable[[], None]] = None

    # --- capture phase -------------------------------------------------

    def begin_capture(
        self,
        listen_rf: RFLinkSnapshot,
        foreign_count: int = 3,
    ) -> None:
        """
        Tune the ground receiver, then accumulate up to *foreign_count* **foreign**
        intercept records (``addressed_to_us == False``).

        Registers :meth:`SpaceRangeClient.register_downlink_handler` — only one
        handler at a time; detach with :func:`detach_downlink` when finished.
        """
        if foreign_count < 1:
            raise ValueError("foreign_count must be >= 1")

        with self._lock:
            self._captures.clear()
            self._needed = foreign_count
            self._listening = True
            self._replay_sent = False

        tune_ground(self._client, listen_rf)
        self._client.register_downlink_handler(self._on_dl)

    def _on_dl(self, payload: bytes) -> None:
        self._dispatch_downlink(payload)

    def _dispatch_downlink(self, payload: bytes) -> None:
        peeled = dc.decode_downlink_mqtt_payload(self._team_password, self._caesar_key, payload)
        if not peeled:
            return
        if peeled["format"] != dc.FORMAT_UPLINK_INTERCEPT:
            return
        rec = dc.parse_uplink_intercept_record(peeled["body"])
        if not rec:
            return
        if rec["addressed_to_us"]:
            return

        wire = CapturedWire.from_intercept(rec)
        done = False
        with self._lock:
            if not self._listening:
                return
            self._captures.append(wire)
            printer.info(
                f"cyber_replay: captured foreign intercept #{len(self._captures)}/{self._needed} "
                f"t≈{wire.sim_time:.2f}s rx={wire.rx_frequency_mhz} MHz"
            )
            if len(self._captures) >= self._needed:
                self._listening = False
                done = True

        if done:
            if self.on_capture_complete:
                try:
                    self.on_capture_complete(list(self._captures))
                except Exception as e:
                    printer.error(f"on_capture_complete: {e}")

    # --- replay scheduling ---------------------------------------------

    def schedule_replay_at(self, sim_time: float, transmit_rf: RFLinkSnapshot) -> None:
        """
        After capture completes, arm a one-shot replay when simulation time
        reaches *sim_time*. Uses :func:`replay.replay_transmit_bytes` for each
        stored payload on *transmit_rf*'s frequency (typically the victim link).
        """
        self._replay_at_sim = float(sim_time)
        self._replay_rf = transmit_rf

    def schedule_replay_after(
        self,
        delta_sim_seconds: float,
        transmit_rf: RFLinkSnapshot,
        *,
        now_sim_time: float,
    ) -> None:
        """Convenience: ``schedule_replay_at(now_sim_time + delta, ...)``."""
        self.schedule_replay_at(now_sim_time + float(delta_sim_seconds), transmit_rf)

    def tick(self, sim_time: float) -> None:
        """
        Call periodically (e.g. from ``on_session``) to fire replay once
        ``sim_time >=`` scheduled instant.
        """
        if self._replay_sent or self._replay_at_sim is None or self._replay_rf is None:
            return
        if sim_time < self._replay_at_sim:
            return
        self._fire_replay()

    def _fire_replay(self) -> None:
        rf = self._replay_rf
        assert rf is not None
        self._replay_sent = True
        with self._lock:
            batch = list(self._captures)
        if not batch:
            printer.warn("cyber_replay: replay armed but no captures — nothing sent")
            return
        freq = rf.frequency_mhz
        for i, w in enumerate(batch):
            fmhz = w.rx_frequency_mhz if w.rx_frequency_mhz else freq
            raw = base64.standard_b64decode(w.payload_b64.encode("ascii"))
            data_b64 = base64.standard_b64encode(raw).decode("ascii")
            resp = replay_transmit_bytes(self._client, fmhz, data_b64, encoding="base64")
            if resp and resp.get("success"):
                printer.success(f"cyber_replay: replay #{i + 1}/{len(batch)} sent ({fmhz} MHz)")
            else:
                printer.error(f"cyber_replay: replay #{i + 1} failed: {resp}")
        if self.on_replay_complete:
            try:
                self.on_replay_complete()
            except Exception as e:
                printer.error(f"on_replay_complete: {e}")

    # --- persistence ---------------------------------------------------

    def save_captures(self, path: str) -> None:
        """Write captures + replay metadata as JSON."""
        with self._lock:
            caps = [asdict(c) for c in self._captures]
            meta = {
                "captures": caps,
                "replay_at_sim": self._replay_at_sim,
                "replay_rf": asdict(self._replay_rf) if self._replay_rf else None,
            }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    @staticmethod
    def load_captures(path: str) -> dict[str, Any]:
        """Load JSON written by :meth:`save_captures`."""
        with open(path, encoding="utf-8") as f:
            return json.load(f)


def detach_downlink(client: "SpaceRangeClient") -> None:
    """Remove the Downlink handler (stop CPU work when idle)."""
    client.register_downlink_handler(None)


# ---------------------------------------------------------------------------
# Multi-team capture / replay (workshop helpers)
# ---------------------------------------------------------------------------


class MultiTeamCaptureSequence:
    """
    Cycle through every blue team's RF, capturing foreign Uplink Intercept
    records into a per-team pool.

    The rogue's Receiver overhears blue-team uplinks and packages them as
    Format-3 (Uplink Intercept) records inside its own downlink. This sequence:

    1. Re-tunes the rogue's *ground* receiver (``set_telemetry``) to each blue
       team's nominal carrier in turn, dwelling for ``dwell_seconds`` per team.
    2. Decodes every incoming Format-3 record and routes it into the pool
       belonging to the team whose channel is *currently* tuned.
    3. Stops automatically once every team has reached ``per_team_quota``
       captures, or once ``end_at`` is reached, whichever comes first.

    All work is driven from :meth:`tick` — call it from ``on_session`` with
    ``session["time"]``. The sequence is silent until ``sim_time >= start_at``,
    after which it tunes / handles downlinks / rotates dwell windows on its own.

    Parameters
    ----------
    client:
        The rogue's :class:`~src.mqtt_client.SpaceRangeClient` (must have
        ``enable_intercept: true`` on its scenario controller).
    blue_teams:
        Every :class:`~src.config.TeamConfig` whose ciphertext you want to
        capture (typically ``scenario.enemy_teams``).
    start_at:
        Sim-time at which the cycle begins.
    end_at:
        Sim-time at which the cycle stops unconditionally.
    per_team_quota:
        How many foreign captures to record per team before that team is
        considered "full" (further intercepts on its channel are dropped).
    dwell_seconds:
        How long to stay on each team's frequency before rotating to the next.
    bandwidth_mhz:
        Bandwidth used in the ``set_telemetry`` snapshot for each tune.
    """

    def __init__(
        self,
        client: "SpaceRangeClient",
        blue_teams: list["TeamConfig"],
        *,
        start_at: float,
        end_at: float,
        per_team_quota: int = 2,
        dwell_seconds: float = 600.0,
        bandwidth_mhz: float = 5.0,
    ) -> None:
        if per_team_quota < 1:
            raise ValueError("per_team_quota must be >= 1")
        if dwell_seconds <= 0:
            raise ValueError("dwell_seconds must be positive")
        if end_at <= start_at:
            raise ValueError("end_at must be > start_at")

        self._client = client
        self._teams: list["TeamConfig"] = list(blue_teams)
        self._team_by_id: dict[int, "TeamConfig"] = {t.id: t for t in self._teams}

        self._password = client._team.password
        self._home_caesar_key = int(client._team.key)
        self._quota = int(per_team_quota)
        self._dwell = float(dwell_seconds)
        self._bandwidth = float(bandwidth_mhz)
        self._start_at = float(start_at)
        self._end_at = float(end_at)

        self._pools: dict[int, list[CapturedWire]] = {t.id: [] for t in self._teams}
        self._lock = threading.Lock()
        self._started = False
        self._cycling = False
        self._completed = False
        self._team_idx = 0
        self._current_team_id: Optional[int] = None
        self._current_caesar_key: int = self._home_caesar_key
        self._next_switch_at: Optional[float] = None

        self.on_complete: Optional[Callable[[dict[int, list[CapturedWire]]], None]] = None

    # --- public API ----------------------------------------------------

    def tick(self, sim_time: float) -> None:
        """Drive the state machine — call from ``on_session``."""
        if self._completed:
            return

        if not self._started and sim_time >= self._start_at:
            self._begin_cycle(sim_time)

        if not self._cycling:
            return

        if sim_time >= self._end_at:
            printer.info(
                f"capture: window expired at t={sim_time:.0f}s — finalising"
            )
            self._finalise()
            return

        if self._all_quotas_met():
            printer.info(
                f"capture: every team reached quota={self._quota} — finalising"
            )
            self._finalise()
            return

        if self._next_switch_at is not None and sim_time >= self._next_switch_at:
            with self._lock:
                self._team_idx = (self._team_idx + 1) % len(self._teams)
            self._tune_to_index(self._team_idx)
            self._next_switch_at = sim_time + self._dwell

    def get_pools(self) -> dict[int, list[CapturedWire]]:
        """Snapshot copy of all per-team capture pools."""
        with self._lock:
            return {tid: list(pool) for tid, pool in self._pools.items()}

    def total_captured(self) -> int:
        """Total intercepts across every team."""
        with self._lock:
            return sum(len(p) for p in self._pools.values())

    def save(self, path: str) -> None:
        """Persist all per-team pools as JSON for forensics."""
        with self._lock:
            data = {
                "teams": [
                    {
                        "team_id": t.id,
                        "team_name": t.name,
                        "frequency_mhz": float(t.frequency),
                        "key": int(t.key),
                        "captures": [asdict(w) for w in self._pools[t.id]],
                    }
                    for t in self._teams
                ],
                "started": self._started,
                "completed": self._completed,
            }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # --- internals -----------------------------------------------------

    def _begin_cycle(self, sim_time: float) -> None:
        if not self._teams:
            printer.warn("capture: no blue teams configured — skipping")
            self._completed = True
            return
        self._started = True
        self._cycling = True
        self._team_idx = 0
        self._tune_to_index(0)
        self._next_switch_at = sim_time + self._dwell
        self._client.register_downlink_handler(self._on_downlink)
        printer.info(
            f"capture: started — {len(self._teams)} blue team(s), "
            f"dwell={self._dwell:.0f}s, quota={self._quota}/team, "
            f"window=[{self._start_at:.0f}, {self._end_at:.0f}]s"
        )

    def _tune_to_index(self, idx: int) -> None:
        team = self._teams[idx]
        snap = RFLinkSnapshot(
            frequency_mhz=float(team.frequency),
            key=int(team.key),
            bandwidth_mhz=self._bandwidth,
        )
        try:
            tune_ground(self._client, snap)
        except Exception as e:
            printer.error(f"capture: tune_ground failed for '{team.name}': {e}")
            return
        with self._lock:
            self._current_team_id = team.id
            self._current_caesar_key = int(team.key)
        printer.info(
            f"capture: tuned to '{team.name}' @ {team.frequency} MHz (key={team.key})"
        )

    def _on_downlink(self, payload: bytes) -> None:
        with self._lock:
            current_key = self._current_caesar_key
        peeled = dc.decode_downlink_mqtt_payload(self._password, current_key, payload)
        if not peeled or peeled["format"] != dc.FORMAT_UPLINK_INTERCEPT:
            return
        rec = dc.parse_uplink_intercept_record(peeled["body"])
        if not rec:
            return
        if rec["addressed_to_us"]:
            return

        with self._lock:
            if not self._cycling:
                return
            tid = self._current_team_id
            if tid is None or tid not in self._pools:
                return
            pool = self._pools[tid]
            if len(pool) >= self._quota:
                return
            wire = CapturedWire.from_intercept(rec)
            pool.append(wire)
            team_name = self._team_by_id[tid].name
            printer.info(
                f"capture: stored intercept for '{team_name}' "
                f"({len(pool)}/{self._quota}, rx={wire.rx_frequency_mhz} MHz, "
                f"t≈{wire.sim_time:.0f}s)"
            )

    def _all_quotas_met(self) -> bool:
        with self._lock:
            return all(len(p) >= self._quota for p in self._pools.values())

    def _finalise(self) -> None:
        with self._lock:
            if self._completed:
                return
            self._completed = True
            self._cycling = False
        try:
            self._client.register_downlink_handler(None)
        except Exception as e:
            printer.warn(f"capture: detach handler failed: {e}")
        total = self.total_captured()
        printer.success(
            f"capture: complete — {total} intercept(s) across "
            f"{len(self._teams)} team(s)"
        )
        if self.on_complete:
            try:
                self.on_complete(self.get_pools())
            except Exception as e:
                printer.error(f"capture on_complete: {e}")


class MultiTeamReplaySequence:
    """
    Schedule N replay **rounds** at random sim-times within ``[start, end]``.

    Each **round** (one tick of the state machine at a scheduled time):

    1. For **every** blue team in the capture sequence, in roster order,
       picks a **random** :class:`CapturedWire` from **that team's pool only**.
    2. Tunes the rogue's ground TX to that team's nominal frequency
       (``set_telemetry``) so the EM-sensor view shows the carrier change.
    3. Calls :func:`replay.replay_transmit_bytes` with the captured
       on-air bytes.

       If a team's pool is empty at round fire-time, that team is skipped
       for that round (logged). Otherwise every team receives one injection
       attempt per round so bursts align across crews.

    Logs every transmit for forensics (round index, team, success).

    Parameters
    ----------
    client:
        The rogue's :class:`~src.mqtt_client.SpaceRangeClient`.
    capture:
        The :class:`MultiTeamCaptureSequence` whose pools to draw from.
    start_at:
        Earliest sim-time a burst may fire.
    end_at:
        Latest sim-time a burst may fire.
    burst_count:
        How many replay bursts to schedule across the window.
    seed:
        RNG seed for reproducible random burst times. Default ``None`` = random.
    bandwidth_mhz:
        Bandwidth used in the ground-transmitter ``set_telemetry`` snapshot.
    """

    def __init__(
        self,
        client: "SpaceRangeClient",
        capture: MultiTeamCaptureSequence,
        *,
        start_at: float,
        end_at: float,
        burst_count: int = 8,
        seed: Optional[int] = None,
        bandwidth_mhz: float = 5.0,
    ) -> None:
        if end_at <= start_at:
            raise ValueError("end_at must be > start_at")
        if burst_count < 1:
            raise ValueError("burst_count must be >= 1")

        self._client = client
        self._capture = capture
        self._start_at = float(start_at)
        self._end_at = float(end_at)
        self._burst_count = int(burst_count)
        self._rng = random.Random(seed)
        self._bandwidth = float(bandwidth_mhz)

        self._times: list[float] = []
        self._next_idx = 0
        self._lock = threading.Lock()
        self._log: list[dict[str, Any]] = []
        self._armed = False
        self._completed = False

        self.on_complete: Optional[Callable[[list[dict[str, Any]]], None]] = None

    # --- public API ----------------------------------------------------

    def tick(self, sim_time: float) -> None:
        """Drive the state machine — call from ``on_session``."""
        if self._completed:
            return

        if not self._armed and sim_time >= self._start_at:
            self._arm_random_bursts()

        if not self._armed:
            return

        while self._next_idx < len(self._times) and sim_time >= self._times[self._next_idx]:
            self._fire_one(sim_time)
            self._next_idx += 1

        if self._next_idx >= len(self._times):
            self._finalise()

    def get_log(self) -> list[dict[str, Any]]:
        """Snapshot copy of every replay attempt logged so far."""
        with self._lock:
            return list(self._log)

    def save(self, path: str) -> None:
        """Persist every replay attempt as JSON for forensics."""
        with self._lock:
            log = list(self._log)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"replays": log}, f, indent=2)

    # --- internals -----------------------------------------------------

    def _arm_random_bursts(self) -> None:
        times = sorted(
            self._rng.uniform(self._start_at, self._end_at)
            for _ in range(self._burst_count)
        )
        self._times = times
        self._armed = True
        printer.info(
            f"replay: armed {self._burst_count} burst(s) between "
            f"t={self._start_at:.0f}s and t={self._end_at:.0f}s — "
            f"times={[round(x, 1) for x in times]}"
        )

    def _fire_one(self, sim_time: float) -> None:
        pools = self._capture.get_pools()
        teams = self._capture._teams
        burst_no = self._next_idx + 1

        if not teams:
            printer.warn(
                f"replay: no blue teams at t={sim_time:.0f}s — "
                f"round {burst_no}/{self._burst_count} skipped"
            )
            with self._lock:
                self._log.append(
                    {
                        "sim_time": sim_time,
                        "burst_round": burst_no,
                        "team_id": None,
                        "team_name": None,
                        "freq_mhz": None,
                        "success": False,
                        "reason": "no teams",
                    }
                )
            return

        any_candidates = any(len(pools.get(t.id, ())) > 0 for t in teams)
        if not any_candidates:
            printer.warn(
                f"replay: no captures in any pool at t={sim_time:.0f}s — "
                f"round {burst_no}/{self._burst_count} skipped entirely"
            )
            with self._lock:
                self._log.append(
                    {
                        "sim_time": sim_time,
                        "burst_round": burst_no,
                        "team_id": None,
                        "team_name": None,
                        "freq_mhz": None,
                        "success": False,
                        "reason": "no captures",
                    }
                )
            return

        for team in teams:
            tid = team.id
            ws = pools.get(tid, [])
            if not ws:
                printer.warn(
                    f"replay: no captures for '{team.name}' at t={sim_time:.0f}s "
                    f"— round {burst_no}/{self._burst_count} skipped for this team"
                )
                with self._lock:
                    self._log.append(
                        {
                            "sim_time": sim_time,
                            "burst_round": burst_no,
                            "team_id": tid,
                            "team_name": team.name,
                            "freq_mhz": None,
                            "success": False,
                            "reason": "no captures for team",
                        }
                    )
                continue

            wire = self._rng.choice(ws)
            freq = float(team.frequency)
            snap = RFLinkSnapshot(
                frequency_mhz=freq,
                key=int(team.key),
                bandwidth_mhz=self._bandwidth,
            )
            try:
                tune_ground(self._client, snap)
            except Exception as e:
                printer.warn(f"replay: tune_ground failed for '{team.name}': {e}")

            try:
                resp = replay_transmit_bytes(
                    self._client, freq, wire.payload_b64, encoding="base64"
                )
            except Exception as e:
                printer.error(f"replay: transmit_bytes raised: {e}")
                resp = None

            ok = bool(resp and resp.get("success"))
            payload_hash = ""
            try:
                import hashlib

                raw = base64.standard_b64decode(wire.payload_b64.encode("ascii"))
                payload_hash = hashlib.sha1(raw).hexdigest()[:12]
            except Exception:
                pass

            with self._lock:
                self._log.append(
                    {
                        "sim_time": sim_time,
                        "burst_round": burst_no,
                        "team_id": tid,
                        "team_name": team.name,
                        "freq_mhz": freq,
                        "payload_sha1_12": payload_hash,
                        "success": ok,
                    }
                )

            if ok:
                printer.success(
                    f"replay: t={sim_time:.0f}s round {burst_no}/{self._burst_count} "
                    f"→ '{team.name}' @ {freq} MHz (sha1={payload_hash})"
                )
            else:
                printer.error(
                    f"replay: t={sim_time:.0f}s round {burst_no}/{self._burst_count} "
                    f"failed → '{team.name}' @ {freq} MHz: {resp}"
                )

    def _finalise(self) -> None:
        with self._lock:
            if self._completed:
                return
            self._completed = True
            log_copy = list(self._log)
        n_ok = sum(1 for r in log_copy if r.get("success"))
        printer.success(
            f"replay: complete — {n_ok}/{len(log_copy)} transmit(s) succeeded "
            f"({self._burst_count} round(s) × {len(self._capture._teams)} team(s) max)"
        )
        if self.on_complete:
            try:
                self.on_complete(log_copy)
            except Exception as e:
                printer.error(f"replay on_complete: {e}")
