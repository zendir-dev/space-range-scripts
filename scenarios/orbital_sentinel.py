# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Orbital Sentinel — Space Range scenario script
============================================
Red Team spacecraft performs sun-pointing, nadir-pointing, and then
jams other teams' downlink frequency before standing down.

The scenario configuration is read from ``scenarios/orbit_sentinel.json``
(auto-detected by name match).

Run from the project root:
    python scenarios/orbit_sentinel.py
"""

import sys
import os

# Allow imports from the project root's src/ package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import load_config, EventScheduler, SpaceRangeClient, prompt_game_name
from src import commands


# =============================================================================
# Configuration
# =============================================================================

# Prompt operator for game/instance name (Enter = use default "ZENDIR")
game = prompt_game_name()

# Auto-loads scenarios/orbit_sentinel.json based on this script's filename
config = load_config(game=game)

red_team  = config.get_team("RED")

# Resolve the asset assigned to Red Team via its collection
red_assets = config.get_assets_for_team(red_team)
if not red_assets:
    raise RuntimeError("No assets found for Red Team — check collection mapping in orbit_sentinel.json")

# Red Team controls SC_002 ("Recon") via the RED collection
ASSET_NAME = red_assets[0].name   # e.g. "Recon" — matched against live ground controller data

# Collect the uplink frequencies of every other enabled team — these are the
# frequencies we will jam. Excludes our own team and any disabled teams.
enemy_frequencies = [
    team.frequency
    for team in config.teams
    if team.enabled and team.id != red_team.id
]


# =============================================================================
# Event Schedule
# =============================================================================

scheduler = EventScheduler(asset_name=ASSET_NAME)

scheduler.add_event(
    name="Point Jammer to Madrid",
    trigger_time=500.0,
    **commands.guidance_ground("Jammer", station="Madrid"),
)

scheduler.add_event(
    name="Start Jamming All Enemy Teams",
    trigger_time=800.0,
    # Jam the uplink frequencies of every other enabled team simultaneously
    **commands.jammer_start(frequencies=enemy_frequencies, power=3.0),
)

scheduler.add_event(
    name="Stop Jamming",
    trigger_time=1500.0,
    **commands.jammer_stop(),
)


# =============================================================================
# Main
# =============================================================================

def main():
    client = SpaceRangeClient(
        config=config,
        team=red_team,
        scheduler=scheduler,
    )

    client.print_banner()
    scheduler.print_schedule()
    print("=" * 60 + "\n")

    client.connect_and_run()


if __name__ == "__main__":
    main()
