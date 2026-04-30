# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Jamming helpers — schedule pulsed jam patterns on top of the EventScheduler.

The basic ``commands.jammer_start`` / ``commands.jammer_stop`` events fire a
*continuous* jam between two times. For workshop scenarios where the goal is
"intermittent denial" — disrupt some commands, not all — emit a duty-cycle
sequence of ON / OFF pulses across a time window via
:func:`schedule_jammer_pulses`.

Live frequency rotation is supported by passing a ``frequencies_resolver``
callable: the resolver runs as a ``pre_trigger`` on every ON pulse, so a
mid-window key/frequency change by the victim is picked up automatically
without re-scheduling the events.

Typical use
-----------
::

    from src import Scenario, commands
    from src.jamming import schedule_jammer_pulses

    scenario = Scenario(team_name="Phantom")

    schedule_jammer_pulses(
        scenario.scheduler,
        name="Uplink Pulse Jam (Blue Bravo)",
        start=10_200.0, end=10_800.0,
        on_seconds=8.0, period_seconds=40.0,    # 20% duty cycle
        fallback_frequencies=[scenario.team_by_name("Blue Bravo").frequency],
        frequencies_resolver=lambda: [scenario.team_by_name("Blue Bravo").frequency],
        power=0.8,
    )
"""

from __future__ import annotations

from typing import Callable, Optional, TYPE_CHECKING

from . import commands
from . import printer

if TYPE_CHECKING:
    from .event_scheduler import EventScheduler


def schedule_jammer_pulses(
    scheduler: "EventScheduler",
    *,
    name: str,
    start: float,
    end: float,
    on_seconds: float,
    period_seconds: float,
    power: float,
    fallback_frequencies: list[float],
    frequencies_resolver: Optional[Callable[[], list[float]]] = None,
) -> int:
    """
    Emit alternating ``jammer_start`` / ``jammer_stop`` events to pulse the
    on-board jammer over ``[start, end]`` with the requested duty cycle.

    The pattern is ``on_seconds`` ON, then ``period_seconds - on_seconds``
    OFF, repeated until ``end`` is reached. Any final pulse that would extend
    past ``end`` is truncated (its OFF event is clamped to ``end``).

    Parameters
    ----------
    scheduler:
        The :class:`~src.event_scheduler.EventScheduler` to populate.
    name:
        Human-readable label prefix for the events. Each ON / OFF pair gets
        ``" ON #k"`` / ``" OFF #k"`` appended.
    start:
        Sim-time (seconds) at which the first ON pulse fires.
    end:
        Sim-time (seconds) at which the schedule ends. The last OFF pulse is
        clamped to this time, so the jammer is guaranteed to be off at *end*.
    on_seconds:
        Duration of each ON pulse (must be positive and strictly less than
        ``period_seconds``).
    period_seconds:
        ON+OFF cycle length (must be positive). The duty cycle is
        ``on_seconds / period_seconds``.
    power:
        Transmit power in watts passed verbatim to ``commands.jammer_start``.
        Lower values produce a "light" jam — operators see a *fraction* of
        commands fail rather than a hard outage.
    fallback_frequencies:
        Frequencies passed to ``commands.jammer_start`` as the default
        ``args["frequencies"]``. Used at fire-time if ``frequencies_resolver``
        is ``None`` or raises / returns empty.
    frequencies_resolver:
        Optional callable invoked **per ON pulse** as a ``pre_trigger`` —
        return the live list of target frequencies. A return of ``[]``,
        ``None`` or an exception falls back to ``fallback_frequencies``.

    Returns
    -------
    int
        The number of ON pulses scheduled (one ``jammer_start`` event per
        pulse plus one ``jammer_stop`` event per pulse).
    """
    if on_seconds <= 0 or period_seconds <= 0:
        raise ValueError("on_seconds and period_seconds must both be positive")
    if on_seconds >= period_seconds:
        raise ValueError(
            "on_seconds must be strictly less than period_seconds "
            "(use commands.jammer_start directly for a continuous jam)"
        )
    if end <= start:
        raise ValueError("end must be > start")

    duty = on_seconds / period_seconds

    def _make_resolver(default_freqs: list[float]) -> Callable[[dict], dict]:
        # Capture the resolver via closure; default_freqs is the schedule-time fallback.
        def _live(default_args: dict) -> dict:
            if frequencies_resolver is None:
                return default_args
            try:
                freqs = frequencies_resolver()
            except Exception as e:
                printer.warn(
                    f"schedule_jammer_pulses: resolver raised {e!r} — using fallback freqs"
                )
                return default_args
            if not freqs:
                return default_args
            return {**default_args, "frequencies": list(freqs)}
        return _live

    resolver = _make_resolver(list(fallback_frequencies))

    pulse = 0
    t = float(start)
    end_f = float(end)
    while t < end_f:
        on_at = t
        off_at = min(t + on_seconds, end_f)
        pulse += 1

        scheduler.add_event(
            f"{name} ON #{pulse}",
            trigger_time=on_at,
            pre_trigger=resolver,
            **commands.jammer_start(
                frequencies=list(fallback_frequencies),
                power=power,
            ),
        )
        scheduler.add_event(
            f"{name} OFF #{pulse}",
            trigger_time=off_at,
            **commands.jammer_stop(),
        )

        t += period_seconds

    printer.info(
        f"jamming: scheduled {pulse} pulse(s) for '{name}' — "
        f"duty={duty:.0%} ({on_seconds:.1f}s ON / {period_seconds:.1f}s period), "
        f"power={power}W, window=[{start:.0f}, {end:.0f}]s"
    )
    return pulse
