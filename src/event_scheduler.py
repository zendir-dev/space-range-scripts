# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
EventScheduler — manages and fires ScheduledEvents based on simulation time.
"""

from __future__ import annotations

from typing import Callable, Optional

from .scheduled_event import ScheduledEvent
from . import printer


class EventScheduler:
    """Manages and executes scheduled events based on simulation time."""

    def __init__(self, asset_name: str):
        """
        Parameters
        ----------
        asset_name:
            The human-readable name of the spacecraft asset this scheduler
            controls (e.g. ``"Recon"``). This is matched against the names
            returned by the ground controller's ``list_assets`` response to
            resolve the live 8-character asset ID at runtime.

            The live ID is refreshed automatically by
            :class:`~src.mqtt_client.SpaceRangeClient` on connect and on every
            simulation reset.  Commands will not be sent until the ID has been
            successfully resolved.
        """
        self.asset_name = asset_name
        self.live_asset_id: str | None = None   # resolved at runtime from the ground controller
        self.events: list[ScheduledEvent] = []
        self._all_complete_logged = False

    def resolve_asset_id(self, asset_id: str):
        """Set the live 8-character asset ID returned by the ground controller."""
        self.live_asset_id = asset_id
        printer.success(f"Asset '{self.asset_name}' resolved to live ID: {asset_id}")

    def add_event(
        self,
        name: str,
        trigger_time: float,
        command: str,
        args: dict = None,
        description: str = "",
        pre_trigger: Optional[Callable[[dict], dict]] = None,
    ) -> "EventScheduler":
        """
        Add a new scheduled event. Returns *self* for method chaining.

        Parameters
        ----------
        name:
            Human-readable label for the event.
        trigger_time:
            Simulation time (seconds) at which to fire.
        command:
            Command type string (e.g. ``"guidance"``).
        args:
            Default arguments dict for the command.
        description:
            Optional detail shown in log output alongside the event name.
        pre_trigger:
            Optional callable ``(args: dict) -> dict`` called just before the
            command is sent.  Its return value replaces ``args`` at fire time.
            Use this for live data lookups (e.g. fetching current enemy
            frequencies from the admin API) that must be as fresh as possible.
        """
        event = ScheduledEvent(
            name=name,
            trigger_time=trigger_time,
            command=command,
            args=args or {},
            description=description or f"{command} at t={trigger_time}s",
            pre_trigger=pre_trigger,
        )
        self.events.append(event)
        # Keep events sorted by trigger time
        self.events.sort(key=lambda e: e.trigger_time)
        return self

    def reset_all(self):
        """Reset all events so they will be re-executed in a new simulation instance."""
        for event in self.events:
            event.reset()
        self._all_complete_logged = False
        self.live_asset_id = None   # cleared — must be re-resolved from the ground controller
        printer.warn("All scheduled events have been reset and will be re-executed.")
        printer.warn("Live asset ID cleared — will re-resolve on next connect.")

    def process(self, sim_time: float, send_func: Callable[[dict], None]):
        """
        Check pending events against *sim_time* and fire the next due event.

        Only **one** event is fired per call.  This preserves strict
        trigger-time ordering even when multiple tick threads run concurrently
        (e.g. when the script connects mid-simulation and several session
        messages arrive before the first event has finished firing).

        The sequence for each event is:
          1. ``event.firing`` is set to ``True`` — all other tick threads skip it.
          2. ``pre_trigger`` runs (may block for admin/ground responses).
          3. The command is sent.
          4. ``event.executed`` is set to ``True``.

        Because we stop after claiming one event, the *next* event in the
        sorted list is never touched until the current one is fully executed,
        so "Stop Jamming" can never fire before "Start Jamming".

        Parameters
        ----------
        sim_time:
            Current simulation time in seconds.
        send_func:
            Callable that accepts a fully-formed command packet dict and sends it.
        """
        for event in self.events:
            if event.executed:
                continue

            # An event that is already firing is mid-execution on another
            # thread.  Stop here — don't skip over it to fire later events.
            if event.firing:
                return

            if sim_time >= event.trigger_time:
                if self.live_asset_id is None:
                    printer.warn(f"t={sim_time:.1f}s — skipping '{event.name}': live asset ID not yet resolved.")
                    return

                # Claim the event immediately — before pre_trigger blocks —
                # so concurrent tick threads stop at this event and never
                # advance past it to fire a later event out of order.
                event.firing = True

                printer.event(sim_time, event.name, event.description)

                # Run the pre_trigger hook if one is registered.
                # It receives the default args and returns the final args to use.
                args = event.args
                if event.pre_trigger is not None:
                    try:
                        args = event.pre_trigger(args)
                    except Exception as e:
                        printer.error(f"pre_trigger for '{event.name}' raised an exception: {e}")
                        printer.warn(f"Falling back to default args for '{event.name}'.")

                command_packet = {
                    "asset": self.live_asset_id,
                    "command": event.command,
                    "time": 0,  # execute immediately
                    "args": args,
                }

                send_func(command_packet)
                event.executed = True
                printer.complete(event.name)

                # Stop after firing one event — the next tick will advance to
                # the following event, preserving strict ordering.
                return

        # Log once when all events are done
        if self.all_complete and not self._all_complete_logged:
            printer.success("All scheduled events have been executed.")
            printer.info("Continuing to monitor session… (Ctrl+C to exit)")
            self._all_complete_logged = True

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def all_complete(self) -> bool:
        """Return True when every event has been executed."""
        return all(event.executed for event in self.events)

    @property
    def pending_count(self) -> int:
        """Number of events that have not yet been claimed or executed."""
        return sum(1 for event in self.events if not event.firing and not event.executed)

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def print_schedule(self):
        """Pretty-print the full event schedule with execution status."""
        live_id = self.live_asset_id or "unresolved"
        printer.info(f"Scheduled Events  (asset: '{self.asset_name}'  live ID: {live_id}):")
        for event in self.events:
            status = "✓" if event.executed else "○"
            print(f"  {status} t={event.trigger_time:>8.1f}s  [{event.command:<12}]  {event.name}")
        print()
