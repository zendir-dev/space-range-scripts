# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Cyber Defender — Space Range scenario script
=============================================

The **rogue** spacecraft (callsign *PHANTOM*) drives every active cyber
effect in this scenario:

* **Phase 2a — MQTT capture (first 15 minutes at 1×).**
  The rogue subscribes to **every** blue team's MQTT ``Uplink`` topic at once,
  XOR-decrypts with each team's password, and stores valid JSON commands per
  team (no RF dwell / no Format-3 intercept). See
  :class:`src.cyber_replay.MqttUplinkCaptureSequence`.

* **Phase 2b — Replay bursts (minutes 25–33 at 1×).**
  **Eight bursts** equally spaced in ``[1 500, 1 980]`` s; at each burst:
  loop every blue team, set that team's live frequency, wait **1.5 s** real
  time, then send **three** random stored commands back-to-back for that team.
  Replay uses data captured in minutes 0–15 only.

* **Uplink jam** (minutes ~33–38): jammer bore-sighted on the **shared
  defender spacecraft** (first blue asset); **continuous** barrage at **very
  low power** across **every** blue team's MHz (no pulses, no per-team
  frequency hopping in the schedule).

* **Broadcast downlink jam — two windows**
  Saturating jam on every blue frequency while the rogue **bore-sights the
  Dubai and Singapore ground sites** (not the defender spacecraft) during
  the **Dubai** pass segment (**15–25 min**) and the **Singapore** pass
  segment (**40–50 min**).

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
from src.cyber_replay import MqttUplinkCaptureSequence, MultiTeamReplaySequence


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

# Timeline at simulation.speed = 1.0 (wall-clock seconds == sim seconds).
# Ground visibility (workshop key): Paris 0–9 min, Dubai 9–25, Mumbai 25–38,
# Singapore 38–69, Sydney 69+ (see scenario brief).
#
# **0–900 s:** MQTT uplink capture only.
# **900–1 500 s (15–25 min):** broadcast downlink jam (Dubai segment).
# **1 500–1 980 s (25–33 min):** replay bursts (captures from 0–900 s).
# **1 980–2 280 s (33–38 min):** continuous low-power uplink jam (all blue MHz,
#    jammer aimed at defender / Mumbai keyed pass segment).
# **2 400–3 000 s (40–50 min):** broadcast downlink jam (Singapore segment).
CAPTURE_START = 0.0
CAPTURE_END = 900.0
REPLAY_START = 1_500.0
REPLAY_END = 1_980.0
# Replay pacing controls:
# - wait before each team frequency/tune step
# - wait after tuning each team to its live frequency
# - no delay between shots for the same team
REPLAY_BURST_COUNT = 8
REPLAY_POST_TUNE_DELAY = 2
REPLAY_PRE_TEAM_DELAY = REPLAY_POST_TUNE_DELAY
REPLAY_INTER_SHOT_DELAY = 0.0
REPLAY_SHOTS_PER_TEAM_PER_BURST = 1

capture: "MqttUplinkCaptureSequence | None" = None
replay_seq: "MultiTeamReplaySequence | None" = None


def _save_capture_pools(_pools: dict) -> None:
    if capture is None:
        return
    out = os.path.join(_SCRIPT_DIR, "captures.json")
    try:
        capture.save(out)
        printer.info(f"capture: pools saved → {out}")
    except Exception as e:
        printer.warn(f"capture: save failed: {e}")


def _save_replay_log(_log: list) -> None:
    if replay_seq is None:
        return
    out = os.path.join(_SCRIPT_DIR, "replays.json")
    try:
        replay_seq.save(out)
        printer.info(f"replay: log saved → {out}")
    except Exception as e:
        printer.warn(f"replay: save failed: {e}")


def live_replay_key_for(team) -> int:
    """
    Resolve live RF key for one enemy team via admin query_data.

    Used once right before burst #1 to freeze replay keys for all bursts.
    Falls back to config ``team.key`` on any lookup failure.
    """
    fallback = int(team.key)
    if scenario.client is None:
        return fallback
    if not scenario.enemy_asset_ids:
        scenario.wait_for_enemy_ids(timeout=120.0)
    if team not in scenario.enemy_teams:
        return fallback
    idx = scenario.enemy_teams.index(team)
    if idx >= len(scenario.enemy_asset_ids):
        return fallback

    asset_id = scenario.enemy_asset_ids[idx]
    response = scenario.client.admin.query_data(asset_id, recent=True, timeout=10.0)
    if response is None:
        return fallback
    rows = response.get("args", {}).get("data", [])
    if not rows:
        return fallback
    key = rows[-1].get("communications.key")
    if key is None:
        return fallback
    try:
        return int(key)
    except (TypeError, ValueError):
        return fallback


def _build_active_sequences() -> None:
    """Construct the capture / replay sequences once the client is live."""
    global capture, replay_seq

    blue_count = len(scenario.enemy_teams)

    capture = MqttUplinkCaptureSequence(
        scenario.client,
        scenario.enemy_teams,
        start_at=CAPTURE_START,
        end_at=CAPTURE_END,
        max_per_team=512,
    )
    replay_seq = MultiTeamReplaySequence(
        scenario.client,
        capture,
        start_at=REPLAY_START,
        end_at=REPLAY_END,
        burst_count=REPLAY_BURST_COUNT,
        seed=20260202,
        frequency_for_team=lambda t: float(scenario.live_enemy_frequency_for(t)),
        key_for_team=live_replay_key_for,
        freeze_rf_at_first_burst=True,
        shots_per_team_per_burst=REPLAY_SHOTS_PER_TEAM_PER_BURST,
        post_tune_delay_seconds=REPLAY_POST_TUNE_DELAY,
        pre_team_delay_seconds=REPLAY_PRE_TEAM_DELAY,
        inter_shot_delay_seconds=REPLAY_INTER_SHOT_DELAY,
    )

    capture.on_complete = _save_capture_pools
    replay_seq.on_complete = _save_replay_log

    printer.info(
        f"cyber: MQTT capture window=[{CAPTURE_START:.0f}, {CAPTURE_END:.0f}]s "
        f"({blue_count} blue team(s)); "
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


# ---------------------------------------------------------------------------
# Defender spacecraft target for guidance (live asset ID from admin).
# The JSON/config ``id`` (e.g. SC_OPS) is not what GetSpacecraftController()
# expects — we inject the 8-char runtime ID from resolve_enemy_ids() at fire
# time via pre_trigger (same source as jammer frequency resolution).
# ---------------------------------------------------------------------------

_defender_assets = (
    scenario.config.get_assets_for_team(scenario.enemy_teams[0])
    if scenario.enemy_teams
    else []
)
DEFENDER_ASSET_LABEL = _defender_assets[0].name if _defender_assets else "defender"
printer.info(
    f"cyber: defender target label → '{DEFENDER_ASSET_LABEL}' "
    f"(live asset ID applied at schedule fire via admin-resolved enemy_asset_ids)"
)


def live_defender_guidance_args(default_args: dict) -> dict:
    """Replace ``spacecraft`` with the live defender bus ID (first enemy space asset)."""
    if not scenario.enemy_asset_ids:
        scenario.wait_for_enemy_ids(timeout=120.0)
    if not scenario.enemy_asset_ids:
        printer.warn(
            "A7: no live defender asset ID — relative pointing may fail "
            "(admin enemy resolution returned no space assets)."
        )
        return default_args
    live_id = scenario.enemy_asset_ids[0]
    printer.info(f"A7: guidance spacecraft parameter → live asset ID {live_id}")
    return {**default_args, "spacecraft": live_id}


# ---------------------------------------------------------------------------
# A7 — Continuous uplink jam (all blue MHz, defender bore-sight, low power)
# ---------------------------------------------------------------------------

UPLINK_JAM_START = 1_980.0
UPLINK_JAM_END = 2_280.0
# Far below broadcast downlink jam (3 W); enough to perturb links if dry-run proves too faint, bump slightly.
UPLINK_JAM_POWER = 0.3

if not scenario.enemy_teams:
    printer.warn("A7: no enemy teams configured — uplink jam will be skipped")
else:
    printer.info(
        f"A7: uplink jam → point at defender '{DEFENDER_ASSET_LABEL}' "
        f"(live ID at fire time), "
        f"all blue MHz, {UPLINK_JAM_POWER} W, [{UPLINK_JAM_START:.0f},{UPLINK_JAM_END:.0f}]s"
    )
    scheduler.add_event(
        name=f"Point Jammer at {DEFENDER_ASSET_LABEL} (uplink jam prep)",
        trigger_time=UPLINK_JAM_START - 10.0,
        pre_trigger=live_defender_guidance_args,
        **commands.guidance_spacecraft("Jammer", ""),
    )
    scheduler.add_event(
        name="Uplink Jam ON",
        trigger_time=UPLINK_JAM_START,
        pre_trigger=live_jammer_args_all,
        **commands.jammer_start(
            frequencies=list(scenario.enemy_fallback_freqs),
            power=UPLINK_JAM_POWER,
        ),
    )
    scheduler.add_event(
        name="Uplink Jam OFF",
        trigger_time=UPLINK_JAM_END,
        **commands.jammer_stop(),
    )


# ---------------------------------------------------------------------------
# Broadcast downlink jam — Dubai segment (15–25 min) & Singapore (40–50 min)
# ---------------------------------------------------------------------------

JAM_DUBAI_START = 900.0
JAM_DUBAI_END = 1_500.0
JAM_SINGAPORE_START = 2_400.0
JAM_SINGAPORE_END = 3_000.0
BROADCAST_JAM_POWER = 3.0


def _add_broadcast_jam_window(label: str, on_at: float, off_at: float, ground_station: str) -> None:
    """Barrage jam while the rogue's jammer bore-sights the named ground site (not the defender spacecraft)."""
    scheduler.add_event(
        name=f"Point Jammer at {ground_station} ({label} prep)",
        trigger_time=on_at - 10.0,
        **commands.guidance_ground("Jammer", ground_station),
    )
    scheduler.add_event(
        name=f"Downlink Jam ON ({label})",
        trigger_time=on_at,
        pre_trigger=live_jammer_args_all,
        **commands.jammer_start(
            frequencies=list(scenario.enemy_fallback_freqs),
            power=BROADCAST_JAM_POWER,
        ),
    )
    scheduler.add_event(
        name=f"Downlink Jam OFF ({label})",
        trigger_time=off_at,
        **commands.jammer_stop(),
    )


_add_broadcast_jam_window("Dubai pass 15–25 min", JAM_DUBAI_START, JAM_DUBAI_END, "Dubai")
_add_broadcast_jam_window(
    "Singapore pass 40–50 min", JAM_SINGAPORE_START, JAM_SINGAPORE_END, "Singapore"
)


# ---------------------------------------------------------------------------
# Idle pointing bookends — keeps the rogue's body on a sensible attitude
# between jammer events.
# ---------------------------------------------------------------------------

scheduler.add_event(
    name="Initial Sun Point",
    trigger_time=10.0,
    **commands.guidance_sun("Solar Panel"),
)
scheduler.add_event(
    name="Final Sun Point",
    trigger_time=3_060.0,
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
