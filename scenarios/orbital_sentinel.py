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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import Scenario, commands


# =============================================================================
# Scenario context
# =============================================================================

# Prompts for game name and admin password (saves/restores defaults),
# loads scenarios/orbital_sentinel.json, resolves Red Team and its assets,
# and enumerates all other enabled teams as enemies.
scenario = Scenario(team_name="RED")


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
    name="Point Jammer to Easter Island",
    trigger_time=5550.0,
    **commands.guidance_ground("Jammer", station="Easter Island"),
)

scheduler.add_event(
    name="Start Jamming All Enemy Teams",
    trigger_time=5559.0,
    pre_trigger=live_jammer_args,
    **commands.jammer_start(frequencies=scenario.enemy_fallback_freqs, power=3.0),
)

scheduler.add_event(
    name="Stop Jamming",
    trigger_time=7251.0,
    **commands.jammer_stop(),
)

scheduler.add_event(
    name="Point Jammer to Dubai",
    trigger_time=8900.0,
    **commands.guidance_ground("Jammer", station="Dubai"),
)

scheduler.add_event(
    name="Start Jamming All Enemy Teams",
    trigger_time=9160.0,
    pre_trigger=live_jammer_args,
    **commands.jammer_start(frequencies=scenario.enemy_fallback_freqs, power=3.0),
)

scheduler.add_event(
    name="Stop Jamming",
    trigger_time=10800.0,
    **commands.jammer_stop(),
)

scheduler.add_event(
    name="Point Jammer to Dubai",
    trigger_time=16850.0,
    **commands.guidance_ground("Jammer", station="Dubai"),
)

scheduler.add_event(
    name="Start Jamming All Enemy Teams",
    trigger_time=16980.0,
    pre_trigger=live_jammer_args,
    **commands.jammer_start(frequencies=scenario.enemy_fallback_freqs, power=3.0),
)

scheduler.add_event(
    name="Stop Jamming",
    trigger_time=18635.0,
    **commands.jammer_stop(),
)


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    # resolve_enemy_ids() is called automatically on connect.
    # Pass on_connect=your_func here to add extra setup work.
    scenario.run()

