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
import threading
from dataclasses import asdict, dataclass
from typing import Any, Callable, Optional, TYPE_CHECKING

from . import downlink_codec as dc
from . import printer
from .replay import RFLinkSnapshot, replay_transmit_bytes, tune_ground

if TYPE_CHECKING:
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
