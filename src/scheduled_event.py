# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Scheduled event dataclass used by the EventScheduler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class ScheduledEvent:
    """
    Represents a scheduled event to be executed at a specific simulation time.

    Attributes
    ----------
    name:
        Human-readable label shown in the schedule and log output.
    trigger_time:
        Simulation time (seconds) at or after which this event fires.
    command:
        The command type string sent in the uplink packet (e.g. ``"guidance"``).
    args:
        Default arguments dict for the command.  If *pre_trigger* is set, its
        return value overrides these args at the moment of execution.
    description:
        Optional extra detail shown alongside the event name in log output.
    pre_trigger:
        Optional callable invoked **just before** the command is sent.
        Signature: ``(args: dict) -> dict``
        Receives the event's current ``args`` dict and must return the
        (possibly modified) args dict that will actually be sent.  Use this
        hook to perform live data lookups (e.g. querying current enemy
        frequencies via the admin API) at the moment of firing rather than
        using values fixed at schedule-build time.
    firing:
        Set to ``True`` the instant this event is claimed by a scheduler tick,
        before ``pre_trigger`` runs.  Prevents concurrent tick threads from
        double-firing the same event while ``pre_trigger`` is blocking.
    executed:
        Set to ``True`` after the event has fully fired and the command has
        been sent.  Reset by :meth:`reset` when a simulation restart is
        detected.
    """
    name: str
    trigger_time: float
    command: str
    args: dict = field(default_factory=dict)
    description: str = ""
    pre_trigger: Optional[Callable[[dict], dict]] = field(default=None, repr=False)
    firing: bool = False
    executed: bool = False

    def reset(self):
        """Reset the event so it can be executed again."""
        self.firing  = False
        self.executed = False
