# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Configuration loader for Space Range scenarios.

Reads a scenario JSON file (e.g. ``scenarios/orbit_sentinel.json``) and
exposes typed helpers for looking up team and asset data.

The scenario JSON replaces the old ``configuration/Teams.json`` file and
carries the full scenario definition including simulation parameters, teams,
assets, collections, ground stations, and events.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class TeamConfig:
    """Configuration for a single team."""
    name: str
    id: int
    password: str
    frequency: float
    key: int
    color: str
    collection: str
    enabled: bool = True


@dataclass
class AssetConfig:
    """Lightweight reference to a space asset within a scenario."""
    id: str
    name: str


@dataclass
class ScenarioConfig:
    """Top-level configuration for a Space Range scenario."""
    game: str
    server: str
    port: int
    teams: list[TeamConfig]
    assets: list[AssetConfig] = field(default_factory=list)

    # collection_id → list of asset IDs
    _collections: dict[str, list[str]] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------
    # Team helpers
    # ------------------------------------------------------------------

    def get_team(self, name: str) -> TeamConfig:
        """Return the :class:`TeamConfig` whose *name* matches (case-insensitive)."""
        target = name.lower()
        for team in self.teams:
            if team.name.lower() == target:
                return team
        raise KeyError(f"No team named '{name}' found in configuration.")

    def get_team_by_id(self, team_id: int) -> TeamConfig:
        """Return the :class:`TeamConfig` for the given numeric *team_id*."""
        for team in self.teams:
            if team.id == team_id:
                return team
        raise KeyError(f"No team with id={team_id} found in configuration.")

    # ------------------------------------------------------------------
    # Asset helpers
    # ------------------------------------------------------------------

    def get_asset(self, asset_id: str) -> AssetConfig:
        """Return the :class:`AssetConfig` for the given *asset_id*."""
        for asset in self.assets:
            if asset.id == asset_id:
                return asset
        raise KeyError(f"No asset with id='{asset_id}' found in configuration.")

    def get_assets_for_team(self, team: TeamConfig) -> list[AssetConfig]:
        """
        Return all :class:`AssetConfig` objects assigned to *team* via its
        collection mapping.
        """
        asset_ids = self._collections.get(team.collection, [])
        result = []
        for aid in asset_ids:
            try:
                result.append(self.get_asset(aid))
            except KeyError:
                pass
        return result


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

_DEFAULT_SERVER = "mqtt.zendir.io"
_DEFAULT_PORT   = 1883
_DEFAULT_GAME   = "ZENDIR"


def load_config(
    path: Optional[str] = None,
    game: Optional[str] = None,
    server: Optional[str] = None,
    port: Optional[int] = None,
) -> ScenarioConfig:
    """
    Load and return a :class:`ScenarioConfig` from a scenario JSON file.

    Parameters
    ----------
    path:
        Path to the scenario ``.json`` file.  If *None*, the loader looks for
        a JSON file in the ``scenarios/`` folder whose stem matches the calling
        script's filename, then falls back to the first ``.json`` found there.
    game:
        Override the game / instance name used for MQTT topic construction.
        If *None*, defaults to ``"ZENDIR"``.
    server:
        MQTT broker hostname.  Defaults to ``"mqtt.zendir.io"``.
    port:
        MQTT broker port.  Defaults to ``1883``.
    """
    if path is None:
        path = _resolve_scenario_path()

    with open(path, "r") as f:
        raw = json.load(f)

    teams = [
        TeamConfig(
            name=t["name"],
            id=t["id"],
            password=t["password"],
            frequency=t["frequency"],
            key=t["key"],
            color=t.get("color", "#FFFFFF"),
            collection=t.get("collection", ""),
            enabled=t.get("enabled", True),
        )
        for t in raw.get("teams", [])
    ]

    # Space assets
    space_raw = raw.get("assets", {}).get("space", [])
    assets = [AssetConfig(id=a["id"], name=a["name"]) for a in space_raw]

    # Collection → asset ID mapping
    collections: dict[str, list[str]] = {}
    for col in raw.get("assets", {}).get("collections", []):
        collections[col["id"]] = col.get("space_assets", [])

    return ScenarioConfig(
        game=game or _DEFAULT_GAME,
        server=server or _DEFAULT_SERVER,
        port=port or _DEFAULT_PORT,
        teams=teams,
        assets=assets,
        _collections=collections,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_scenario_path() -> str:
    """
    Attempt to auto-locate a scenario JSON file.

    Search order:
    1. ``scenarios/<calling_script_stem>.json`` (name-matched)
    2. First ``*.json`` found in ``scenarios/``
    """
    import inspect
    import glob

    # Walk up the call stack to find the outermost non-src caller
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(src_dir)
    scenarios_dir = os.path.join(project_root, "scenarios")

    for frame_info in reversed(inspect.stack()):
        caller_file = frame_info.filename
        if caller_file and os.path.isfile(caller_file):
            stem = os.path.splitext(os.path.basename(caller_file))[0]
            candidate = os.path.join(scenarios_dir, f"{stem}.json")
            if os.path.isfile(candidate):
                return candidate

    # Fallback: first JSON in scenarios/
    matches = glob.glob(os.path.join(scenarios_dir, "*.json"))
    if matches:
        return matches[0]

    raise FileNotFoundError(
        "Could not auto-locate a scenario JSON file. "
        "Pass an explicit path to load_config(path=...)."
    )
