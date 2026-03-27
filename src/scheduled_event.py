# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Scheduled event dataclass used by the EventScheduler.
"""

from dataclasses import dataclass, field


@dataclass
class ScheduledEvent:
    """Represents a scheduled event to be executed at a specific simulation time."""
    name: str
    trigger_time: float
    command: str
    args: dict = field(default_factory=dict)
    description: str = ""
    executed: bool = False

    def reset(self):
        """Reset the event so it can be executed again."""
        self.executed = False
