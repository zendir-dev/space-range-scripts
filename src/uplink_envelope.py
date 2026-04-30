# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Uplink envelope helpers — canonical JSON for spacecraft commands.

Studio expects **PascalCase** top-level keys on the wire: ``Asset``, ``Command``,
``Time``, ``Args``.  :class:`~src.event_scheduler.EventScheduler` uses a
compact legacy shape with ``id`` instead of ``Asset`` — both are accepted by
current builds; use :func:`make_scheduler_packet` for scheduled scripts and
:func:`make_uplink_envelope` when authoring scenario JSON or MQTT payloads.

``command_*`` aliases wrap :mod:`src.commands` so scenario code can read
``command_downlink()`` / ``command_guidance_sun()`` style names.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Optional

from . import commands as _commands


def make_uplink_envelope(
    asset_id: str,
    command: str,
    args: Optional[Mapping[str, Any]] = None,
    time: float = 0.0,
) -> dict[str, Any]:
    """
    Build a PascalCase uplink dict suitable for MQTT / scenario JSON.

    Parameters
    ----------
    asset_id:
        8-character hex spacecraft ID.
    command:
        Command name (e.g. ``\"guidance\"``, ``\"downlink\"``).
    args:
        Command arguments object; omitted or ``{}`` when none.
    time:
        Simulation seconds to execute (``0`` = immediate).
    """
    out: dict[str, Any] = {
        "Asset": asset_id,
        "Command": command,
        "Time": float(time),
        "Args": dict(args) if args else {},
    }
    return out


def make_scheduler_packet(
    asset_id: str,
    command: str,
    args: Optional[Mapping[str, Any]] = None,
    time: float = 0.0,
) -> dict[str, Any]:
    """
    Build the compact packet shape used by :class:`~src.event_scheduler.EventScheduler`
    (``id``, ``command``, ``time``, ``args``).
    """
    return {
        "id": asset_id,
        "command": command,
        "time": float(time),
        "args": dict(args) if args else {},
    }


def envelope_from_command_builder(asset_id: str, builder: dict, time: float = 0.0) -> dict[str, Any]:
    """
    Convert a :mod:`src.commands` builder dict (``command``, ``args``, ``description``)
    into a PascalCase uplink envelope for *asset_id*.
    """
    return make_uplink_envelope(
        asset_id,
        builder["command"],
        builder.get("args") or {},
        time=time,
    )


def envelope_json(asset_id: str, builder: dict, time: float = 0.0, indent: Optional[int] = 2) -> str:
    """Pretty-printed JSON string for a command builder envelope."""
    return json.dumps(envelope_from_command_builder(asset_id, builder, time=time), indent=indent)


# --- Readable aliases (each returns the same dict shape as commands.*) ----------

command_downlink = _commands.downlink
command_downlink_ping_on = _commands.downlink_ping_on
command_downlink_ping_off = _commands.downlink_ping_off

command_guidance_sun = _commands.guidance_sun
command_guidance_nadir = _commands.guidance_nadir
command_guidance_velocity = _commands.guidance_velocity
command_guidance_inertial = _commands.guidance_inertial
command_guidance_ground = _commands.guidance_ground
command_guidance_location = _commands.guidance_location
command_guidance_spacecraft = _commands.guidance_spacecraft
command_guidance_idle = _commands.guidance_idle

command_telemetry = _commands.telemetry_configure
command_camera_configure = _commands.camera_configure
command_capture = _commands.camera_capture

command_jammer_start = _commands.jammer_start
command_jammer_stop = _commands.jammer_stop

command_encryption_rotate = _commands.encryption_rotate
command_reset_component = _commands.component_reset

command_thrust_fire = _commands.thruster_fire
command_thrust_stop = _commands.thruster_stop

command_rendezvous_start = _commands.rendezvous_start
command_rendezvous_stop = _commands.rendezvous_stop

command_docking_dock = _commands.docking_dock
command_docking_undock = _commands.docking_undock

command_get_schedule = _commands.get_schedule
command_remove_by_id = _commands.remove_command_by_id
command_remove_by_time_command = _commands.remove_command_by_time_command
command_update = _commands.update_command
