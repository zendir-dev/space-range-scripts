# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Scenario base class for Space Range scenario scripts.

:class:`Scenario` encapsulates every piece of boilerplate that is identical
across all scenario scripts:

* Prompting the operator for credentials
* Loading the scenario JSON config
* Looking up the Red (or any) controlling team and its primary asset
* Enumerating enemy teams from the config
* Creating an :class:`~src.event_scheduler.EventScheduler`
* Resolving live enemy asset IDs on connect (with retries)
* Creating the :class:`~src.mqtt_client.SpaceRangeClient`, printing the
  startup banner, and calling ``connect_and_run()``

Minimal scenario script example
---------------------------------
::

    from src import Scenario, commands

    scenario = Scenario(team_name="RED")

    scheduler = scenario.scheduler
    scheduler.add_event("Sun Point", trigger_time=100, **commands.guidance_sun("Solar Panel"))
    scheduler.add_event("Nadir",     trigger_time=500, **commands.guidance_nadir("Body"))

    scenario.run()

With a live frequency lookup in a ``pre_trigger`` hook
-------------------------------------------------------
::

    from src import Scenario, commands

    scenario = Scenario(team_name="RED")

    def live_jammer_args(default_args):
        freqs = scenario.live_enemy_frequencies(default_args["frequencies"])
        return {**default_args, "frequencies": freqs}

    scenario.scheduler.add_event(
        "Start Jamming",
        trigger_time=80.0,
        pre_trigger=live_jammer_args,
        **commands.jammer_start(frequencies=scenario.enemy_fallback_freqs, power=3.0),
    )

    scenario.run()

With a custom on_connect hook
------------------------------
::

    from src import Scenario, commands

    scenario = Scenario(team_name="RED")

    def on_connected():
        scenario.resolve_enemy_ids()          # built-in helper; also called by default
        scenario.client.admin.some_setup()    # extra admin work

    scenario.run(on_connect=on_connected)
"""

from __future__ import annotations

import threading
from typing import Callable, Optional

from .config import ScenarioConfig, TeamConfig, AssetConfig, load_config
from .event_scheduler import EventScheduler
from .mqtt_client import SpaceRangeClient, prompt_credentials
from . import printer


class Scenario:
    """
    High-level scenario context — owns config, team, scheduler, and client.

    Parameters
    ----------
    team_name:
        Name of the controlling team as defined in the scenario JSON
        (e.g. ``"RED"``).  Case-insensitive.
    asset_index:
        Index into the team's asset list to use as the primary controlled
        spacecraft.  Defaults to ``0`` (the first asset).
    config_path:
        Explicit path to the scenario JSON file.  If *None* the loader
        auto-detects it by matching the calling script's filename against
        files in ``scenarios/``.
    """

    def __init__(
        self,
        team_name: str = "RED",
        asset_index: int = 0,
        config_path: Optional[str] = None,
    ):
        # ------------------------------------------------------------------
        # Credentials & configuration
        # ------------------------------------------------------------------
        self._game, self._admin_password = prompt_credentials()

        self.config: ScenarioConfig = load_config(
            path=config_path,
            game=self._game,
        )

        # ------------------------------------------------------------------
        # Controlling team & primary asset
        # ------------------------------------------------------------------
        self.team: TeamConfig = self.config.get_team(team_name)

        own_assets: list[AssetConfig] = self.config.get_assets_for_team(self.team)
        if not own_assets:
            raise RuntimeError(
                f"No assets found for team '{team_name}' — "
                "check the collection mapping in the scenario JSON."
            )
        self.asset: AssetConfig = own_assets[asset_index]

        # ------------------------------------------------------------------
        # Enemy teams
        # ------------------------------------------------------------------
        self.enemy_teams: list[TeamConfig] = [
            t for t in self.config.teams
            if t.enabled and t.id != self.team.id
        ]
        """All enabled teams that are not the controlling team."""

        self.enemy_fallback_freqs: list[float] = [t.frequency for t in self.enemy_teams]
        """Fallback frequencies from config (used when the admin API is unavailable)."""

        # ------------------------------------------------------------------
        # Scheduler
        # ------------------------------------------------------------------
        self.scheduler: EventScheduler = EventScheduler(asset_name=self.asset.name)
        """The :class:`~src.event_scheduler.EventScheduler` for this scenario."""

        # ------------------------------------------------------------------
        # Runtime state (populated during run)
        # ------------------------------------------------------------------
        self.client: Optional[SpaceRangeClient] = None
        """The :class:`~src.mqtt_client.SpaceRangeClient` — available after :meth:`run` is called."""

        self.enemy_asset_ids: list[str] = []
        """Live enemy asset IDs, resolved on connect by :meth:`resolve_enemy_ids`."""

        self._ids_ready = threading.Event()
        """Set once :meth:`resolve_enemy_ids` finishes (even if empty)."""

    # ------------------------------------------------------------------
    # Helpers for pre_trigger hooks
    # ------------------------------------------------------------------

    def wait_for_enemy_ids(self, timeout: float = 120.0) -> bool:
        """
        Block until :meth:`resolve_enemy_ids` has finished (or *timeout* expires).

        Safe to call from any thread (e.g. inside a ``pre_trigger`` hook).

        Returns
        -------
        bool
            ``True`` if IDs were resolved before the timeout, ``False`` otherwise.
        """
        return self._ids_ready.wait(timeout=timeout)

    def live_enemy_frequencies(
        self,
        fallback: Optional[list[float]] = None,
        timeout: float = 10.0,
    ) -> list[float]:
        """
        Return live uplink frequencies for every resolved enemy asset.

        Blocks until enemy IDs are ready (up to 120 s), then queries the
        admin API for each asset's current ``communications.frequency``.
        Falls back to *fallback* (or :attr:`enemy_fallback_freqs`) for any
        asset that cannot be queried.

        Typical use — inside a ``pre_trigger`` hook::

            def live_jammer_args(default_args):
                freqs = scenario.live_enemy_frequencies(default_args["frequencies"])
                return {**default_args, "frequencies": freqs}

        Parameters
        ----------
        fallback:
            Per-asset fallback frequencies.  If *None*, uses
            :attr:`enemy_fallback_freqs`.
        timeout:
            Timeout in seconds for the admin API request.

        Returns
        -------
        list[float]
            List of frequencies in MHz; empty list if nothing could be resolved.
        """
        if fallback is None:
            fallback = self.enemy_fallback_freqs

        if self.client is None:
            printer.warn("live_enemy_frequencies: client not yet available — using fallback.")
            return fallback

        if not self._ids_ready.is_set():
            printer.info("live_enemy_frequencies: waiting for enemy asset IDs…")
            self._ids_ready.wait(timeout=120.0)

        if not self.enemy_asset_ids:
            printer.warn("live_enemy_frequencies: no enemy asset IDs resolved — using fallback.")
            return fallback

        printer.info("live_enemy_frequencies: querying admin API for live frequencies…")
        live = self.client.admin.get_live_frequencies(
            asset_ids=self.enemy_asset_ids,
            fallback_frequencies=fallback,
            timeout=timeout,
        )

        if not live:
            printer.warn("live_enemy_frequencies: admin query returned nothing — using fallback.")
            return fallback

        printer.success(f"live_enemy_frequencies: {live} MHz")
        return live

    # ------------------------------------------------------------------
    # on_connect helper
    # ------------------------------------------------------------------

    def resolve_enemy_ids(self) -> None:
        """
        Resolve live asset IDs for all enemy teams via the admin API.

        Retries up to 3 times (10-second timeout each).  Always sets
        :attr:`_ids_ready` so callers in ``pre_trigger`` hooks are never
        left waiting forever.

        This is called automatically by :meth:`run` unless you supply a
        custom ``on_connect`` callback.  If you supply your own callback and
        still want ID resolution, call this method from within it::

            def my_on_connect():
                scenario.resolve_enemy_ids()
                scenario.client.admin.do_something_else()

            scenario.run(on_connect=my_on_connect)
        """
        if self.client is None:
            printer.warn("resolve_enemy_ids: client not yet initialised.")
            self._ids_ready.set()
            return

        enemy_team_names = [t.name for t in self.enemy_teams]
        if not enemy_team_names:
            printer.info("resolve_enemy_ids: no enemy teams configured — skipping.")
            self._ids_ready.set()
            return

        printer.info(f"Resolving enemy asset IDs for: {enemy_team_names} …")

        for attempt in range(1, 4):
            mapping = self.client.admin.resolve_enemy_asset_ids(
                enemy_team_names, timeout=10.0
            )
            ids: list[str] = []
            for team in self.enemy_teams:
                ids.extend(mapping.get(team.name, []))

            if ids:
                self.enemy_asset_ids = ids
                printer.success(f"Enemy asset IDs (attempt {attempt}): {ids}")
                break

            printer.warn(f"No enemy asset IDs (attempt {attempt}/3) — retrying…")
        else:
            printer.warn(
                "Could not resolve enemy asset IDs after 3 attempts — "
                "jammer will use fallback frequencies."
            )

        self._ids_ready.set()

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(
        self,
        on_connect: Optional[Callable[[], None]] = None,
        on_session: Optional[Callable[[dict], None]] = None,
        on_event: Optional[Callable[[dict], None]] = None,
        on_admin_event: Optional[Callable[[dict], None]] = None,
    ) -> None:
        """
        Create the MQTT client, print the startup banner, and run until
        Ctrl+C.

        Parameters
        ----------
        on_connect:
            Called in a background thread once the broker is connected and
            all subscriptions are live.  Defaults to
            :meth:`resolve_enemy_ids`.  Supply your own callable to extend
            or replace the default behaviour (but remember to call
            ``self.resolve_enemy_ids()`` if you need live enemy IDs).
        on_session:
            Optional extra callback invoked on every incoming session message
            (after the scheduler has been ticked).
        on_event:
            Optional callback for unsolicited ground-event notifications.
        on_admin_event:
            Optional callback for unsolicited admin-event push messages.
        """
        _on_connect = on_connect if on_connect is not None else self.resolve_enemy_ids

        self.client = SpaceRangeClient(
            config=self.config,
            team=self.team,
            scheduler=self.scheduler,
            admin_password=self._admin_password,
            on_session=on_session,
            on_event=on_event,
            on_admin_event=on_admin_event,
            on_connect=_on_connect,
        )

        self.client.print_banner()
        self.scheduler.print_schedule()
        printer.divider()

        self.client.connect_and_run()
