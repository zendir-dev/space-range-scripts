# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Command builder helpers for Space Range spacecraft commands.

Each function returns an ``(command_name, args_dict, description)`` tuple
that can be passed directly to :meth:`~src.event_scheduler.EventScheduler.add_event`
via the ``command`` and ``args`` parameters.

Typical usage
-------------
::

    from src.commands import guidance_sun, jammer_start, jammer_stop

    scheduler.add_event("Sun Point", t=100, **guidance_sun("Solar Panel"))
    scheduler.add_event("Jam",       t=700, **jammer_start([474.0], power=3.0))
    scheduler.add_event("Stop Jam",  t=800, **jammer_stop())

Every helper returns a dict with keys ``command``, ``args``, and ``description``
so it can be unpacked with ``**`` into :meth:`add_event`.
"""

from __future__ import annotations

from typing import Literal


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _cmd(command: str, args: dict, description: str) -> dict:
    return {"command": command, "args": args, "description": description}


# ---------------------------------------------------------------------------
# Guidance / Pointing
# ---------------------------------------------------------------------------

def guidance_sun(
    target: str,
    alignment: str = "+z",
) -> dict:
    """Point *target* component +z (or *alignment*) toward the Sun."""
    return _cmd(
        "guidance",
        {"pointing": "sun", "target": target, "alignment": alignment},
        f"Point '{target}' {alignment} toward the Sun",
    )


def guidance_nadir(
    target: str,
    alignment: str = "+z",
    planet: str = "earth",
) -> dict:
    """Point *target* component toward nadir of *planet*."""
    return _cmd(
        "guidance",
        {"pointing": "nadir", "target": target, "alignment": alignment, "planet": planet},
        f"Point '{target}' {alignment} toward {planet} nadir",
    )


def guidance_velocity(
    target: str,
    alignment: str = "+z",
) -> dict:
    """Align *target* component with the velocity vector."""
    return _cmd(
        "guidance",
        {"pointing": "velocity", "target": target, "alignment": alignment},
        f"Align '{target}' {alignment} with velocity vector",
    )


def guidance_inertial(
    target: str,
    alignment: str = "+z",
    pitch: float = 0.0,
    roll: float = 0.0,
    yaw: float = 0.0,
) -> dict:
    """Point *target* component to an inertial attitude (pitch/roll/yaw)."""
    return _cmd(
        "guidance",
        {
            "pointing": "inertial",
            "target": target,
            "alignment": alignment,
            "pitch": pitch,
            "roll": roll,
            "yaw": yaw,
        },
        f"Inertial point '{target}' {alignment} p={pitch} r={roll} y={yaw}",
    )


def guidance_ground(
    target: str,
    station: str,
    alignment: str = "+z",
) -> dict:
    """Point *target* component toward a named ground station."""
    return _cmd(
        "guidance",
        {"pointing": "ground", "target": target, "alignment": alignment, "station": station},
        f"Point '{target}' {alignment} toward ground station '{station}'",
    )


def guidance_location(
    target: str,
    latitude: float,
    longitude: float,
    altitude: float = 0.0,
    alignment: str = "+z",
    planet: str = "earth",
) -> dict:
    """Point *target* component toward a lat/lon/alt on *planet*."""
    return _cmd(
        "guidance",
        {
            "pointing": "location",
            "target": target,
            "alignment": alignment,
            "planet": planet,
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude,
        },
        f"Point '{target}' {alignment} → ({latitude}°, {longitude}°, {altitude}m) on {planet}",
    )


def guidance_spacecraft(
    target: str,
    spacecraft_id: str,
    alignment: str = "+z",
) -> dict:
    """Point *target* component toward another spacecraft."""
    return _cmd(
        "guidance",
        {"pointing": "spacecraft", "target": target, "alignment": alignment, "spacecraft": spacecraft_id},
        f"Point '{target}' {alignment} toward spacecraft '{spacecraft_id}'",
    )


def guidance_idle() -> dict:
    """Stop ADCS torque output (idle mode)."""
    return _cmd(
        "guidance",
        {"pointing": "idle"},
        "ADCS idle — reaction wheels stop torque",
    )


# ---------------------------------------------------------------------------
# Jammer
# ---------------------------------------------------------------------------

def jammer_start(
    frequencies: list[float],
    power: float,
) -> dict:
    """
    Enable the on-board jammer.

    Parameters
    ----------
    frequencies:
        List of frequencies in MHz to jam (multi-band barrage jamming).
    power:
        Transmit power in watts (0–10 000 W).
    """
    freq_str = ", ".join(f"{f} MHz" for f in frequencies)
    return _cmd(
        "jammer",
        {"active": True, "frequencies": frequencies, "power": power},
        f"Start jamming at [{freq_str}] with {power} W",
    )


def jammer_stop() -> dict:
    """Disable the on-board jammer."""
    return _cmd(
        "jammer",
        {"active": False, "frequencies": [], "power": 0},
        "Stop jamming",
    )


# ---------------------------------------------------------------------------
# Downlink
# ---------------------------------------------------------------------------

def downlink(ping: bool = False) -> dict:
    """Trigger a downlink of all cached data."""
    return _cmd(
        "downlink",
        {"downlink": True, "ping": ping},
        f"Downlink cached data (auto-ping={'on' if ping else 'off'})",
    )


def downlink_ping_on() -> dict:
    """Enable automatic downlink on every ping."""
    return _cmd(
        "downlink",
        {"downlink": True, "ping": True},
        "Enable automatic downlink on every ping",
    )


def downlink_ping_off() -> dict:
    """Disable automatic downlink on ping."""
    return _cmd(
        "downlink",
        {"downlink": False, "ping": False},
        "Disable automatic downlink",
    )


# ---------------------------------------------------------------------------
# Camera configure
# ---------------------------------------------------------------------------

def camera_configure(
    target: str = "Camera",
    fov: float = 60.0,
    resolution: int = 512,
    focal_length: float = 100.0,
    aperture: float = 1.0,
    monochromatic: bool = False,
    sample: bool = False,
    focusing_distance: float = 4.0,
    pixel_pitch: float = 0.012,
    coc: float = 0.03,
) -> dict:
    """Configure a camera component."""
    return _cmd(
        "camera",
        {
            "target": target,
            "fov": fov,
            "resolution": resolution,
            "focal_length": focal_length,
            "aperture": aperture,
            "monochromatic": monochromatic,
            "sample": sample,
            "focusing_distance": focusing_distance,
            "pixel_pitch": pixel_pitch,
            "coc": coc,
        },
        f"Configure '{target}': fov={fov}° res={resolution}px fl={focal_length}mm",
    )


# ---------------------------------------------------------------------------
# Camera capture
# ---------------------------------------------------------------------------

def camera_capture(target: str = "Camera", name: str = "image") -> dict:
    """Capture an image from *target* camera and name it *name*."""
    return _cmd(
        "capture",
        {"target": target, "name": name},
        f"Capture image '{name}' from '{target}'",
    )


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------

def telemetry_configure(frequency: float = 0, key: int = 0) -> dict:
    """Update the uplink/downlink frequency and Caesar-cypher key."""
    return _cmd(
        "telemetry",
        {"frequency": frequency, "key": key},
        f"Set telemetry frequency={frequency} MHz, key={key}",
    )


# ---------------------------------------------------------------------------
# Component reset
# ---------------------------------------------------------------------------

def component_reset(target: str) -> dict:
    """Reset (reboot) a named component on the spacecraft."""
    return _cmd(
        "reset",
        {"target": target},
        f"Reset component '{target}'",
    )


# ---------------------------------------------------------------------------
# Thruster
# ---------------------------------------------------------------------------

def thruster_fire(target: str, duration: float) -> dict:
    """Fire *target* thruster for *duration* seconds."""
    return _cmd(
        "thrust",
        {"target": target, "active": True, "duration": duration},
        f"Fire thruster '{target}' for {duration}s",
    )


def thruster_stop(target: str) -> dict:
    """Stop *target* thruster immediately."""
    return _cmd(
        "thrust",
        {"target": target, "active": False, "duration": 0},
        f"Stop thruster '{target}'",
    )


# ---------------------------------------------------------------------------
# Rendezvous
# ---------------------------------------------------------------------------

def rendezvous_start(
    target_id: str,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    offset_z: float = 0.0,
) -> dict:
    """
    Begin a perch-mode rendezvous with *target_id*.

    Offset axes are in the target's LVLH frame:
    X = radial, Y = velocity, Z = radial × velocity.
    """
    return _cmd(
        "rendezvous",
        {"target": target_id, "active": True, "offset": [offset_x, offset_y, offset_z]},
        f"Rendezvous with '{target_id}' at LVLH offset [{offset_x}, {offset_y}, {offset_z}] m",
    )


def rendezvous_stop(target_id: str) -> dict:
    """Cancel the active rendezvous maneuver."""
    return _cmd(
        "rendezvous",
        {"target": target_id, "active": False, "offset": [0, 0, 0]},
        f"Cancel rendezvous with '{target_id}'",
    )


# ---------------------------------------------------------------------------
# Docking
# ---------------------------------------------------------------------------

def docking_dock(target_id: str, component: str) -> dict:
    """Command the spacecraft to dock with *component* on *target_id*."""
    return _cmd(
        "docking",
        {"target": target_id, "component": component, "dock": True},
        f"Dock with '{component}' on '{target_id}'",
    )


def docking_undock(target_id: str, component: str) -> dict:
    """Undock from *component* on *target_id*."""
    return _cmd(
        "docking",
        {"target": target_id, "component": component, "dock": False},
        f"Undock from '{component}' on '{target_id}'",
    )
