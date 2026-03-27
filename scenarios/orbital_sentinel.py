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
import threading

# Allow imports from the project root's src/ package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import load_config, EventScheduler, SpaceRangeClient, prompt_credentials
from src import commands, printer


# =============================================================================
# Credentials & Configuration
# =============================================================================

# Prompt operator for game name and admin password.
# Previously saved values are offered as defaults — press Enter to accept.
game, admin_password = prompt_credentials()

# Auto-loads scenarios/orbit_sentinel.json based on this script's filename
config = load_config(game=game)

red_team   = config.get_team("RED")
red_assets = config.get_assets_for_team(red_team)
if not red_assets:
    raise RuntimeError("No assets found for Red Team — check collection mapping in orbital_sentinel.json")

# Red Team controls its spacecraft via the RED collection.
# The asset name is matched live against the ground controller data at runtime.
ASSET_NAME = red_assets[0].name   # e.g. "Recon"

# Enemy teams: all enabled teams that are not Red Team.
# We collect names here; their live asset IDs are resolved at connect time
# via the admin API (asset IDs are stable within a running scenario).
enemy_teams = [
    team for team in config.teams
    if team.enabled and team.id != red_team.id
]
enemy_team_names = [t.name for t in enemy_teams]

# Fallback frequencies from the scenario config, used if the admin query
# fails for a particular asset (e.g. if the team has no data yet).
enemy_fallback_freqs = [t.frequency for t in enemy_teams]


# =============================================================================
# Event Schedule
# =============================================================================

scheduler = EventScheduler(asset_name=ASSET_NAME)

scheduler.add_event(
    name="Point Jammer to Madrid",
    trigger_time=50.0,
    **commands.guidance_ground("Jammer", station="Salvador"),
)


def live_jammer_args(default_args: dict) -> dict:
    """
    pre_trigger hook for the 'Start Jamming' event.

    Blocks until on_connected has finished resolving enemy asset IDs, then
    queries the current communications.frequency for every enemy asset via
    the admin API and substitutes those live values into the jammer args.

    Falls back to the scenario-config frequencies for any asset that cannot
    be queried in time.
    """
    if _client is None:
        printer.warn("Jammer pre_trigger: client not yet available — using default frequencies.")
        return default_args

    # Block until on_connected has finished (or 120s safety timeout)
    if not _ids_ready.is_set():
        printer.info("Jammer pre_trigger: waiting for enemy asset IDs to be resolved…")
        _ids_ready.wait(timeout=120.0)

    if not _enemy_asset_ids:
        printer.warn("Jammer pre_trigger: no enemy asset IDs resolved — using defaults.")
        return default_args

    printer.info("Jammer pre_trigger: querying live enemy frequencies via admin API…")
    live_freqs = _client.admin.get_live_frequencies(
        asset_ids=_enemy_asset_ids,
        fallback_frequencies=enemy_fallback_freqs,
        timeout=10.0,
    )

    if not live_freqs:
        printer.warn("Jammer pre_trigger: no frequencies resolved — using defaults.")
        return default_args

    printer.success(f"Jammer pre_trigger: live frequencies = {live_freqs} MHz")
    return {**default_args, "frequencies": live_freqs}


scheduler.add_event(
    name="Start Jamming All Enemy Teams",
    trigger_time=80.0,
    pre_trigger=live_jammer_args,
    # Default args used only if pre_trigger fails completely
    **commands.jammer_start(frequencies=enemy_fallback_freqs, power=3.0),
)

scheduler.add_event(
    name="Stop Jamming",
    trigger_time=1500.0,
    **commands.jammer_stop(),
)


# =============================================================================
# Main
# =============================================================================

# Module-level references set in main() so pre_trigger hooks can access them
_client: SpaceRangeClient | None = None
_enemy_asset_ids: list[str] = []
_ids_ready = threading.Event()   # set once on_connected finishes, even if empty


def on_connected():
    """
    Called by SpaceRangeClient in a background thread once the broker
    connection is established and all MQTT subscriptions are live.

    Retries up to 3 times in case the first request is still mid-flight.
    Always sets _ids_ready so live_jammer_args is never left waiting forever.
    """
    global _enemy_asset_ids
    printer.info("Resolving enemy asset IDs via admin API…")

    for attempt in range(1, 4):
        mapping = _client.admin.resolve_enemy_asset_ids(enemy_team_names, timeout=10.0)
        ids = []
        for team in enemy_teams:
            ids.extend(mapping.get(team.name, []))
        if ids:
            _enemy_asset_ids = ids
            printer.success(f"Enemy asset IDs resolved (attempt {attempt}): {ids}")
            break
        printer.warn(f"No enemy asset IDs resolved (attempt {attempt}/3) — retrying…")
    else:
        printer.warn("Could not resolve enemy asset IDs after 3 attempts — jammer will use fallback frequencies.")

    _ids_ready.set()   # always unblock live_jammer_args


def main():
    global _client

    _client = SpaceRangeClient(
        config=config,
        team=red_team,
        scheduler=scheduler,
        admin_password=admin_password,
        on_connect=on_connected,
    )

    _client.print_banner()
    scheduler.print_schedule()
    printer.divider()

    _client.connect_and_run()


if __name__ == "__main__":
    main()

