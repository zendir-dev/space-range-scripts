# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Cyber Defender — Space Range scenario script
=============================================

The **rogue** spacecraft (callsign *PHANTOM*) drives every active cyber
effect in this scenario:

* **Phase 2a — Multi-team capture (6 000 → 9 000 s).**
  The rogue cycles its receiver across every blue team's RF identity and
  records foreign Uplink Intercepts into per-team capture pools.
  See :class:`src.cyber_replay.MultiTeamCaptureSequence`.

* **Phase 2b — Random multi-team replay (9 500 → 14 500 s).**
  Eight bursts spread randomly through the window, each picking a random
  captured wire and re-broadcasting it at the matching team's frequency.
  See :class:`src.cyber_replay.MultiTeamReplaySequence`.

* **A7 — Light pulsed uplink jam (10 200 → 10 800 s).**
  20 % duty-cycle pulse jam on **one** blue team's frequency. The target is
  picked dynamically from :attr:`Scenario.enemy_teams` (the last enemy team
  in config order), so renaming or extending the team roster requires no
  changes here. See :func:`src.jamming.schedule_jammer_pulses`.

* **A8 / A11 — Broadcast downlink jam over AOI imaging passes.**
  Saturating jam on every blue frequency for 180 s centred on each AOI
  overhead. ``T_AOI_1`` / ``T_AOI_2`` are placeholder constants — lock from
  a dry-run (see ``cyber_defender.spec.md`` § 12.6).

Team identity is **never hard-coded** in this script — every blue-team
detail is read from :attr:`Scenario.enemy_teams` (loaded from the JSON
config) and refreshed live via :meth:`Scenario.live_enemy_frequencies_by_team`
through admin queries.

Phases 0 / 1 / 3 are passive — they fire from ``events[]`` in the JSON.

Run from the project root:

    python "scenarios/Cyber Defender/cyber_defender.py"
"""

import argparse
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "../.."))

if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src import Scenario, commands, printer
from src.cyber_replay import (
    MultiTeamCaptureSequence,
    MultiTeamReplaySequence,
)
from src.jamming import schedule_jammer_pulses


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_parser = argparse.ArgumentParser(description="Cyber Defender scenario (rogue agent)")
_parser.add_argument(
    "config",
    nargs="?",
    default=os.path.join(_SCRIPT_DIR, "cyber_defender.json"),
    help=(
        "Path to the scenario JSON config file. "
        "Defaults to cyber_defender.json in the same directory as this script."
    ),
)
_args = _parser.parse_args()

_config_path = _args.config
if not os.path.isabs(_config_path) and os.sep not in _config_path and "/" not in _config_path:
    _config_path = os.path.join(_SCRIPT_DIR, _config_path)
_config_path = os.path.abspath(_config_path)


# ---------------------------------------------------------------------------
# Scenario context — the "Rogue" team owns the PHANTOM spacecraft
# ---------------------------------------------------------------------------
# The team name and asset name are intentionally distinct: in the Operator
# UI / 3D view the spacecraft is rendered as "[team_name] [asset_name]", so
# "Rogue Phantom" reads cleanly while "Phantom Phantom" would not.
# ---------------------------------------------------------------------------

scenario = Scenario(team_name="Rogue", config_path=_config_path)
scheduler = scenario.scheduler


# ---------------------------------------------------------------------------
# Phase 2a / 2b — multi-team capture & replay
# ---------------------------------------------------------------------------
# The sequences depend on ``scenario.client`` (only populated once ``run()``
# starts), so we construct them in ``on_connect`` and tick them from
# ``on_session``.
# ---------------------------------------------------------------------------

CAPTURE_START = 6_000.0
CAPTURE_END = 9_000.0
REPLAY_START = 9_500.0
REPLAY_END = 14_500.0

capture: "MultiTeamCaptureSequence | None" = None
replay_seq: "MultiTeamReplaySequence | None" = None


def _save_capture_pools(_pools: dict) -> None:
    if capture is None:
        return
    out = os.path.join(_SCRIPT_DIR, "cyber_defender_captures.json")
    try:
        capture.save(out)
        printer.info(f"capture: pools saved → {out}")
    except Exception as e:
        printer.warn(f"capture: save failed: {e}")


def _save_replay_log(_log: list) -> None:
    if replay_seq is None:
        return
    out = os.path.join(_SCRIPT_DIR, "cyber_defender_replays.json")
    try:
        replay_seq.save(out)
        printer.info(f"replay: log saved → {out}")
    except Exception as e:
        printer.warn(f"replay: save failed: {e}")


def _build_active_sequences() -> None:
    """Construct the capture / replay sequences once the client is live."""
    global capture, replay_seq

    blue_count = max(1, len(scenario.enemy_teams))
    per_team_quota = 2 if blue_count <= 2 else 3
    # ~2 sweeps of every team across the 3 000 s capture window.
    dwell_seconds = (CAPTURE_END - CAPTURE_START) / blue_count / 2.0

    capture = MultiTeamCaptureSequence(
        scenario.client,
        scenario.enemy_teams,
        start_at=CAPTURE_START,
        end_at=CAPTURE_END,
        per_team_quota=per_team_quota,
        dwell_seconds=dwell_seconds,
    )
    replay_seq = MultiTeamReplaySequence(
        scenario.client,
        capture,
        start_at=REPLAY_START,
        end_at=REPLAY_END,
        burst_count=8,
        seed=20260415,
    )

    capture.on_complete = _save_capture_pools
    replay_seq.on_complete = _save_replay_log

    printer.info(
        f"cyber: capture window=[{CAPTURE_START:.0f}, {CAPTURE_END:.0f}]s "
        f"({blue_count} blue team(s), quota={per_team_quota}, dwell={dwell_seconds:.0f}s); "
        f"replay window=[{REPLAY_START:.0f}, {REPLAY_END:.0f}]s, bursts=8"
    )


# ---------------------------------------------------------------------------
# Live-frequency resolvers (used by jammer pre_trigger hooks)
# ---------------------------------------------------------------------------
# All resolvers operate on team **objects** from ``scenario.enemy_teams``
# (loaded from the JSON config) and ``scenario.live_enemy_frequencies_by_team``
# (live admin lookup). No team names are hard-coded.
# ---------------------------------------------------------------------------


def live_jammer_args_all(default_args: dict) -> dict:
    """``pre_trigger`` for broadcast (all-blue) jammer events."""
    freqs = [float(f) for f in scenario.live_enemy_frequencies()]
    if not freqs:
        return default_args
    return {**default_args, "frequencies": freqs}


def live_jammer_args_for(team):
    """Build a ``pre_trigger`` that resolves a single team's live frequency."""
    def _hook(default_args: dict) -> dict:
        freq = scenario.live_enemy_frequency_for(team)
        return {**default_args, "frequencies": [float(freq)]}
    return _hook


# ---------------------------------------------------------------------------
# Defender's static asset id (for guidance_spacecraft pointing).
# Resolved dynamically via the first enemy team's collection so a rename of
# the config id (e.g. SC_OPS → DEFENDER) requires no script changes.
# ---------------------------------------------------------------------------

_defender_assets = (
    scenario.config.get_assets_for_team(scenario.enemy_teams[0])
    if scenario.enemy_teams
    else []
)
DEFENDER_ASSET_ID = _defender_assets[0].id if _defender_assets else "SC_OPS"
printer.info(
    f"cyber: defender asset resolved → '{DEFENDER_ASSET_ID}' "
    f"({_defender_assets[0].name if _defender_assets else 'fallback'})"
)


# ---------------------------------------------------------------------------
# A7 — Light pulsed uplink jam on a single blue team (10 200 → 10 800 s)
# ---------------------------------------------------------------------------
# The target team is picked dynamically — the **last** enemy team in config
# order. Adjust the index below to single out a different team; the rest of
# the script (and the question framework) follows automatically.
# ---------------------------------------------------------------------------

UPLINK_JAM_START = 10_200.0
UPLINK_JAM_END = 10_800.0
UPLINK_JAM_ON = 8.0
UPLINK_JAM_PERIOD = 40.0       # 20 % duty cycle
UPLINK_JAM_POWER = 0.8          # well below A8/A11 saturating power

UPLINK_JAM_TARGET = scenario.enemy_teams[-1] if scenario.enemy_teams else None

if UPLINK_JAM_TARGET is None:
    printer.warn(
        "A7: no enemy teams configured — pulsed uplink jam will be skipped"
    )
else:
    printer.info(
        f"A7: uplink-jam target picked dynamically → '{UPLINK_JAM_TARGET.name}' "
        f"(team_id={UPLINK_JAM_TARGET.id}, config_freq={UPLINK_JAM_TARGET.frequency} MHz)"
    )

    scheduler.add_event(
        name=f"Point Jammer at {DEFENDER_ASSET_ID} (uplink jam prep)",
        trigger_time=UPLINK_JAM_START - 10.0,
        **commands.guidance_spacecraft("Jammer", DEFENDER_ASSET_ID),
    )

    schedule_jammer_pulses(
        scheduler,
        name=f"Uplink Pulse Jam ({UPLINK_JAM_TARGET.name})",
        start=UPLINK_JAM_START,
        end=UPLINK_JAM_END,
        on_seconds=UPLINK_JAM_ON,
        period_seconds=UPLINK_JAM_PERIOD,
        power=UPLINK_JAM_POWER,
        fallback_frequencies=[float(UPLINK_JAM_TARGET.frequency)],
        frequencies_resolver=lambda t=UPLINK_JAM_TARGET: [
            float(scenario.live_enemy_frequency_for(t))
        ],
    )


# ---------------------------------------------------------------------------
# A8 / A11 — Broadcast downlink jam centred on AOI imaging passes
#
# These two times must be **locked from a dry-run** (see spec § 12.6).
# Placeholders below are derived from the analytic geometry of the chosen
# orbit (SMA=10 000 km, e=0.015, i=37.5°, RAAN=242°, ω=0°, ν=0°) and the
# 2026/02/02 12:00 UTC epoch:
#   * Orbit-1 descending pass at lat 26.5° N hits geographic lon ≈ 54° E
#     (≈ Hormuz) at t ≈ 3 730 s — this falls in **phase 1** (passive),
#     overlapping the GPS spoof + jam events so operators take a baseline
#     Hormuz image while their GPS is being spoofed/jammed (great pedagogy
#     for the GPS-attribution questions).
#   * Orbit-2 ascending pass at t ≈ 11 200 s lands at lon ≈ -80° E
#     (Caribbean band, lat 26.5° N).
#   * Orbit-2 descending pass at t ≈ 13 700 s lands at lon ≈ 13° E
#     (Mediterranean band, lat 26.5° N).
#   Both orbit-2 passes fall inside phase 2b (9 000 – 15 000 s), giving the
#   rogue a clean window to broadcast-jam the imagery downlink. They are in
#   the same imaging lat-band as Hormuz even though they cross different
#   longitudes — operators are still capturing/downlinking high-priority
#   imagery during these passes.
# Lock both values to the actual GPS trace once the scenario is dry-run.
# ---------------------------------------------------------------------------

T_AOI_1 = 11_200.0      # ≈ orbit-2 ascending pass (Caribbean band)
T_AOI_2 = 13_700.0      # ≈ orbit-2 descending pass (Mediterranean band)
AOI_HALF = 90.0                 # 180 s window each (T ± 90 s)
AOI_JAM_POWER = 3.0             # saturating — clean broadcast outage


def _add_aoi_jam(label: str, t_centre: float) -> None:
    on_at = t_centre - AOI_HALF
    off_at = t_centre + AOI_HALF

    scheduler.add_event(
        name=f"Point Jammer at {DEFENDER_ASSET_ID} ({label})",
        trigger_time=on_at - 10.0,
        **commands.guidance_spacecraft("Jammer", DEFENDER_ASSET_ID),
    )
    scheduler.add_event(
        name=f"Downlink Jam ON ({label})",
        trigger_time=on_at,
        pre_trigger=live_jammer_args_all,
        **commands.jammer_start(
            frequencies=list(scenario.enemy_fallback_freqs),
            power=AOI_JAM_POWER,
        ),
    )
    scheduler.add_event(
        name=f"Downlink Jam OFF ({label})",
        trigger_time=off_at,
        **commands.jammer_stop(),
    )


_add_aoi_jam("AOI Pass 1", T_AOI_1)
_add_aoi_jam("AOI Pass 2", T_AOI_2)


# ---------------------------------------------------------------------------
# Idle pointing bookends — keeps the rogue's body on a sensible attitude
# between jammer events.
# ---------------------------------------------------------------------------

scheduler.add_event(
    name="Initial Sun Point",
    trigger_time=100.0,
    **commands.guidance_sun("Solar Panel"),
)
scheduler.add_event(
    name="Final Sun Point",
    trigger_time=16_500.0,
    **commands.guidance_sun("Solar Panel"),
)


# ---------------------------------------------------------------------------
# on_session — drive the multi-team capture & replay state machines
# ---------------------------------------------------------------------------

def on_connect() -> None:
    """Resolve enemy IDs (default behaviour) then build the active sequences."""
    scenario.resolve_enemy_ids()
    _build_active_sequences()


def on_session(session: dict) -> None:
    """Forward sim-time to the capture/replay sequences on every Session msg."""
    sim_time = float(session.get("time", 0.0))
    if capture is not None:
        try:
            capture.tick(sim_time)
        except Exception as e:
            printer.error(f"capture.tick failed: {e}")
    if replay_seq is not None:
        try:
            replay_seq.tick(sim_time)
        except Exception as e:
            printer.error(f"replay.tick failed: {e}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    scenario.run(on_connect=on_connect, on_session=on_session)
