# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Orbital Sentinel — Space Range scenario script
===============================================
Red Team spacecraft performs sun-pointing, nadir-pointing, and then
jams all enemy teams' uplink frequencies before standing down.

Enemy frequencies are resolved **live** at the moment of jamming via the
admin API (``admin_query_data`` with ``recent=true``), so the jammer will
target whatever frequencies the teams are actually using at that time —
not the frequencies they started with.

The scenario configuration is read from ``scenarios/orbital_sentinel.json``
(auto-detected by name match).

Run from the project root:
    python scenarios/orbital_sentinel.py
"""

import sys
import os
import argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "../.."))

if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src import Scenario, commands


# ---------------------------------------------------------------------------
# CLI: optional config file override
# ---------------------------------------------------------------------------
_parser = argparse.ArgumentParser(description="Tutorial scenario")
_parser.add_argument(
    "config",
    nargs="?",
    default=os.path.join(_SCRIPT_DIR, "tutorial.json"),
    help=(
        "Path to the scenario JSON config file. "
        "Defaults to tutorial.json in the same directory as this script. "
        "A bare filename (no path separators) is resolved relative to this script's directory."
    ),
)
_args = _parser.parse_args()

_config_path = _args.config
if not os.path.isabs(_config_path) and os.sep not in _config_path and "/" not in _config_path:
    _config_path = os.path.join(_SCRIPT_DIR, _config_path)
_config_path = os.path.abspath(_config_path)


# =============================================================================
# Scenario context
# =============================================================================

# Prompts for game name and admin password (saves/restores defaults),
# loads scenarios/orbital_sentinel.json, resolves Red Team and its assets,
# and enumerates all other enabled teams as enemies.
scenario = Scenario(team_name="Rogue", config_path=_config_path)


# =============================================================================
# Event schedule
# =============================================================================

scheduler = scenario.scheduler



def live_jammer_args(default_args: dict) -> dict:
    """
    pre_trigger hook: substitute live enemy frequencies just before jamming.

    Calls scenario.live_enemy_frequencies() which:
      1. Waits (up to 120 s) for enemy asset IDs to be resolved on connect.
      2. Queries each enemy asset's current communications.frequency via
         the admin API.
      3. Falls back to scenario-config frequencies for any asset that fails.
    """
    freqs = scenario.live_enemy_frequencies()
    return {**default_args, "frequencies": freqs}

scheduler.add_event(
    name="Point Nadir",
    trigger_time=100.0,
    **commands.guidance_nadir("Jammer"),
)

scheduler.add_event(
    name="Point Jammer to Dubai",
    trigger_time=1081.0,
    **commands.guidance_ground("Jammer", station="Dubai"),
)

scheduler.add_event(
    name="Start Jamming All Enemy Teams",
    trigger_time=1100.0,
    pre_trigger=live_jammer_args,
    **commands.jammer_start(frequencies=scenario.enemy_fallback_freqs, power=3.0),
)

scheduler.add_event(
    name="Stop Jamming",
    trigger_time=2806.0,
    **commands.jammer_stop(),
)



# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    # resolve_enemy_ids() is called automatically on connect.
    # Pass on_connect=your_func here to add extra setup work.
    scenario.run()

