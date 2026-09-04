"""Generate the five ICEYE filming scenarios.

The scenarios deliberately use staged, repeatable states rather than claiming
that the supplied catalogue gaps reconstruct exact burn epochs or a historical
close approach. Run this file after changing the source data below:

    python "scenarios/Videos/ICEYE/scripts/generate_scenarios.py"

Use --check in CI or before filming to verify that committed JSON is current.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ICEYE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ICEYE_DIR / "config"
OUTPUT_NAMES = [f"section_{index}.json" for index in range(1, 6)]

EPOCH = "2026/05/14 00:00:00"
SECTION_4_EPOCH = "2026/05/14 22:00:00"
ICEYE_INCLINATION_DEG = 97.837601
ICEYE_ARGUMENT_OF_LATITUDE_DEG = 7.059927 + 86.065415

# Every section runs the Euler integrator at a 0.1 s step. That combination
# tops out at 8x simulation speed, which is the real constraint on these
# scenarios: a larger step would buy more speed but coarsens attitude
# integration enough to break smooth reaction-wheel slews, and every section
# either films a pointing command or needs the orbit geometry to hold. Speed
# up long stretches in the edit instead of raising STEP_SIZE here.
INTEGRATOR = "Euler"
STEP_SIZE = 0.1
MAX_SPEED = 8.0

SMALLSAT_MESH = (
    "/ZendirAssetsSpace/Blueprints/Spacecraft/ZenSat/"
    "BP_Z_SC_ZenSat_Chassis"
)
ICEYE_MESH = (
    "/ZendirAssetsSpace/Blueprints/Spacecraft/Landsat8/"
    "BP_Z_SC_Landsat8_Chassis"
)
OVERWATCH_MESH = (
    "/ZendirAssetsSpace/Blueprints/Spacecraft/MRO/"
    "BP_Z_SC_MRO_Chassis"
)

# Source: e2_range_initial_conditions.csv. Values are classical TEME elements
# at 2026-05-14T00:00:00Z, converted to the scenario's km/degree convention.
SPACECRAFT_SOURCE: dict[str, dict[str, Any]] = {
    "ICEYE-X36": {
        "norad": 59103,
        "role": "chief",
        "spaceflux_optics": False,
        "orbit": [6912.420633, 0.000258196, 97.837601, 271.486244, 7.059927, 86.065415],
    },
    "COSMOS 2610": {
        "norad": 68758,
        "role": "deputy",
        "spaceflux_optics": True,
        "orbit": [6930.102680, 0.001928257, 96.957546, 271.671926, 117.679377, 260.225198],
    },
    "COSMOS 2611": {
        "norad": 68759,
        "role": "deputy",
        "spaceflux_optics": False,
        "orbit": [6932.452847, 0.001562587, 96.950662, 271.661078, 119.740239, 246.376940],
    },
    "COSMOS 2612": {
        "norad": 68762,
        "role": "deputy",
        "spaceflux_optics": True,
        "orbit": [6917.592797, 0.002367979, 96.964342, 271.686183, 157.739911, 257.369878],
    },
    "COSMOS 2613": {
        "norad": 68763,
        "role": "deputy",
        "spaceflux_optics": True,
        "orbit": [6910.115082, 0.001476204, 96.965236, 271.699965, 194.493244, 249.082821],
    },
    "COSMOS 2614": {
        "norad": 68764,
        "role": "deputy",
        "spaceflux_optics": True,
        "orbit": [6909.520673, 0.000983558, 96.960126, 271.696564, 205.237301, 251.398552],
    },
}

# Source: e2_range_burns.csv. Timing is the compressed exercise schedule, not
# historical Russian burn timing. The impulses are illustrative reconstructions
# of catalogue-derived inclination steps.
BURNS: list[dict[str, Any]] = [
    {"spacecraft": "COSMOS 2613", "time": 1531.385, "delta_i": 0.3362, "delta_v": 44.477},
    {"spacecraft": "COSMOS 2610", "time": 2578.799, "delta_i": 0.7678, "delta_v": 101.772},
    {"spacecraft": "COSMOS 2613", "time": 4404.109, "delta_i": 0.4145, "delta_v": 54.954},
    {"spacecraft": "COSMOS 2612", "time": 4858.476, "delta_i": 0.2897, "delta_v": 38.410},
    {"spacecraft": "COSMOS 2610", "time": 5453.527, "delta_i": 0.0711, "delta_v": 9.405},
    {"spacecraft": "COSMOS 2613", "time": 7266.796, "delta_i": 0.0640, "delta_v": 8.468},
    {"spacecraft": "COSMOS 2612", "time": 7721.592, "delta_i": 0.5968, "delta_v": 78.939},
    {"spacecraft": "COSMOS 2611", "time": 8508.374, "delta_i": 0.3316, "delta_v": 43.955},
    {"spacecraft": "COSMOS 2614", "time": 9930.480, "delta_i": 0.3355, "delta_v": 44.483},
    {"spacecraft": "COSMOS 2611", "time": 11383.024, "delta_i": 0.5194, "delta_v": 68.845},
    {"spacecraft": "COSMOS 2614", "time": 12792.969, "delta_i": 0.4820, "delta_v": 63.788},
]

# The "partial" stage is 16 May 2026 around midday, which is a real moment in
# the catalogue chronology rather than a synthetic mix: 2613, 2610, and 2612 have
# each finished their whole inclination campaign, while 2611 and 2614 have not
# moved at all and will not until 20-21 May. This is the beat where three of five
# share ICEYE's plane and the pattern first becomes the leading explanation.
PARTIAL_BURN_COUNT = {
    "COSMOS 2610": 2,  # both steps done by 15 May 23:45
    "COSMOS 2611": 0,  # does not move until 20 May
    "COSMOS 2612": 2,  # both steps done by 16 May 10:43
    "COSMOS 2613": 3,  # all three steps done by 14 May 23:32
    "COSMOS 2614": 0,  # does not move until 21 May
}

# For Sections 3 and 4 only: these offsets deliberately place the five craft
# near ICEYE after the evidence-backed inclination match. They are illustrative
# phasing, not a reconstruction of the reported 29 May approach.
ILLUSTRATIVE_ALONG_TRACK_OFFSETS_DEG = {
    "COSMOS 2610": -0.18,
    "COSMOS 2611": 0.28,
    "COSMOS 2612": -0.42,
    "COSMOS 2613": 0.55,
    "COSMOS 2614": -0.70,
}

# Section 4 opens after the Section 3 closure rather than replaying its distant
# starting geometry. All five craft are placed on ICEYE's osculating orbit with
# small along-track separations. At this radius one degree is about 121 km, so
# these offsets place 2614 at ~1 km and the rest at ~4-8 km. This is illustrative
# staging for the custody demonstration, not reconstructed historical phasing.
SECTION_4_ALONG_TRACK_OFFSETS_DEG = {
    "COSMOS 2610": 0.0660,   # ~8.0 km
    "COSMOS 2611": -0.0580,  # ~7.0 km
    "COSMOS 2612": 0.0500,   # ~6.0 km
    "COSMOS 2613": -0.0330,  # ~4.0 km
    "COSMOS 2614": -0.0083,  # ~1.0 km
}

# Section 3 only. The offsets above put each Cosmos 22-85 km from ICEYE; these
# are the LVLH stations the RPO controller then closes to, so the proximity is
# a flown manoeuvre on camera rather than a fixed initial condition. Axes are
# X radial, Y along-velocity, Z orbit-normal, and the command clamps each axis
# to +/-10000 m. 2614 is held closest because Section 4 uses it as the custody
# target. This closure is the illustrative continuation, not catalogue evidence.
#
# `rendezvous` engages a station-keeping hold rather than a one-shot transfer:
# the craft flies to the offset and stays there until released. So each later
# phase below is simply the same command re-issued with a new offset.
RPO_START_TIME_S = 60.0
RPO_CLOSURE_OFFSETS_M = {
    "COSMOS 2610": [0.0, -8000.0, 1500.0],
    "COSMOS 2611": [1500.0, 6500.0, -2000.0],
    "COSMOS 2612": [-2000.0, -5000.0, -2500.0],
    "COSMOS 2613": [2500.0, 4000.0, 2000.0],
    "COSMOS 2614": [-1000.0, -2500.0, 1000.0],
}

# The bulk transit in from tens of km. Deliberately brisk so the closure is
# filmable; the notes explain how to slow it if it reads as a missile.
RPO_TRANSIT_MAX_SPEED_M_S = 40.0
RPO_TRANSIT_ACCEL_M_S2 = 0.2

# 2614 alone repeats the approach, to earn the narration line about the ability
# to approach the asset repeatedly rather than merely arriving once. Slow speeds
# here: this is meant to read as deliberate inspection, not transit.
RPO_REPEAT_SEQUENCE: list[dict[str, Any]] = [
    {
        "spacecraft": "COSMOS 2614",
        "time": 3000.0,
        "label": "Tightens To Inspection Range",
        "offset": [-400.0, -900.0, 300.0],  # ~1.0 km
        "max_speed": 2.0,
        "acceleration": 0.05,
    },
    {
        "spacecraft": "COSMOS 2614",
        "time": 4800.0,
        "label": "Withdraws To Standoff",
        "offset": [-2000.0, -5500.0, 1500.0],  # ~6.0 km
        "max_speed": 8.0,
        "acceleration": 0.1,
    },
]

# Once COSMOS 2614 begins its close inspection leg, slew a narrow-field optical
# payload onto ICEYE. The supplied data has no attitude or payload evidence, so
# this is an explicitly illustrative filming beat rather than a reconstructed
# observation. Pointing starts during the final approach and remains active.
COSMOS_2614_OPTICAL_POINTING_TIME_S = 3000.0
COSMOS_2614_OPTICAL_CAMERA = "OCS-410 Narrow-Field Inspection Camera"

# Overwatch's three custody sensors are co-located on the same boresight so that
# one Guidance command aims all of them at the target. Measured against the MRO
# chassis, which is why the offsets are metres rather than centimetres.
OVERWATCH_SENSOR_POSITION = [2.285, -0.015, 1.448]
OVERWATCH_SENSOR_ROTATION = [-180.0, 90.0, -180.0]
OVERWATCH_OPTICAL_CAMERA = "OTC-450 Optical Tracking Camera"
OVERWATCH_EVENT_CAMERA = "EVS-450 Neuromorphic Event Camera"

# Measured against the Landsat 8 chassis. These do not transfer to another
# chassis: swapping ICEYE_MESH means re-measuring the mount in Studio.
ICEYE_CAMERA_POSITION = [-0.297, 0.215, 0.106]
ICEYE_CAMERA_ROTATION = [180.0, -90.0, 0.0]

def cumulative_burns(name: str, count: int | None = None) -> list[dict[str, Any]]:
    matches = [burn for burn in BURNS if burn["spacecraft"] == name]
    return matches if count is None else matches[:count]


def inclination_after(name: str, count: int | None = None) -> float:
    initial = SPACECRAFT_SOURCE[name]["orbit"][2]
    return initial + sum(burn["delta_i"] for burn in cumulative_burns(name, count))


def total_delta_v(name: str) -> float:
    return sum(burn["delta_v"] for burn in cumulative_burns(name))


def scenario_orbit(name: str, stage: str) -> list[float]:
    orbit = list(SPACECRAFT_SOURCE[name]["orbit"])
    if name == "ICEYE-X36":
        return orbit

    if stage == "custody":
        # Section 4 is a clean retake point at the end-state of Section 3. Using
        # ICEYE's elements plus a small anomaly offset makes that proximity exist
        # at T+0; otherwise every reload returns the Cosmos craft to tens of km out.
        orbit = list(SPACECRAFT_SOURCE["ICEYE-X36"]["orbit"])
        orbit[5] = (
            orbit[5] + SECTION_4_ALONG_TRACK_OFFSETS_DEG[name]
        ) % 360.0
        return [round(value, 9) for value in orbit]

    if stage == "partial":
        orbit[2] = inclination_after(name, PARTIAL_BURN_COUNT[name])
    elif stage in {"matched", "close"}:
        orbit[2] = inclination_after(name)

    if stage == "close":
        # Match argument of latitude and then add a small along-track offset.
        orbit[5] = (
            ICEYE_ARGUMENT_OF_LATITUDE_DEG
            - orbit[4]
            + ILLUSTRATIVE_ALONG_TRACK_OFFSETS_DEG[name]
        ) % 360.0
    return [round(value, 9) for value in orbit]


def component(
    class_name: str,
    name: str,
    data: dict[str, Any],
    *,
    position: list[float] | None = None,
    rotation: list[float] | None = None,
    mesh: str = "None",
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "class": class_name,
        "name": name,
        "mesh": mesh,
        "enabled": True,
        "data": data,
    }
    if position is not None:
        result["position"] = position
    if rotation is not None:
        result["rotation"] = rotation
    return result


def bus_components(profile: str) -> list[dict[str, Any]]:
    names = {
        "iceye": {
            "solar": "SAW-X36 Deployable Solar Array",
            "battery": "BAT-28V Li-Ion Battery Module",
            "computer": "OBC-360 Flight Computer",
            "wheels": "ADCS-04 Reaction Wheel Assembly",
            "gps": "GNSS-24 Navigation Receiver",
            "receiver": "SRX-120 S-Band Command Receiver",
            "transmitter": "XTX-220 X-Band Data Transmitter",
            "storage": "SSR-512 Solid-State Mission Recorder",
        },
        "overwatch": {
            "solar": "SAW-XN High-Efficiency Solar Array",
            "battery": "BAT-42V Li-Ion Power Module",
            "computer": "OBC-750 Mission Flight Computer",
            "wheels": "ADCS-06 Precision Reaction Wheel Assembly",
            "gps": "GNSS-30 Multi-Constellation Nav Receiver",
            "receiver": "SRX-1550 Secure S-Band Command Receiver",
            "transmitter": "XTX-440 Ka-Band Intelligence Downlink",
            "storage": "SSR-2048 Intelligence Data Recorder",
        },
        "cosmos": {
            "solar": "SAW-2 Deployable Solar Array",
            "battery": "BAT-50V Li-Ion Battery Module",
            "computer": "OBC-620 Hardened Flight Computer",
            "wheels": "ADCS-08 Reaction Wheel Assembly",
            "gps": "GNSS-24 Navigation Receiver",
            "receiver": "SRX-180 S-Band Command Receiver",
            "transmitter": "STX-180 S-Band Telemetry Transmitter",
            "storage": "SSR-256 Mission Data Recorder",
        },
    }[profile]
    return [
        component("Solar Panel", names["solar"], {"Area": 0.35, "Efficiency": 0.3, "Mass": 4.0}),
        component("Battery", names["battery"], {"Nominal Capacity": 80.0, "Charge Fraction": 0.9, "Mass": 5.0}),
        component("Computer", names["computer"], {"Mass": 2.0}),
        component("Reaction Wheels", names["wheels"], {"Mass": 5.0}),
        component("GPS Sensor", names["gps"], {"Mass": 1.0}),
        component("Receiver", names["receiver"], {"Antenna Gain": 4.0, "Mass": 1.0}),
        component("Transmitter", names["transmitter"], {"Antenna Gain": 4.0, "Bit Rate": 40000.0, "Mass": 1.0}),
        component("Storage", names["storage"], {"Mass": 4.0}),
    ]


def asset(
    asset_id: str,
    name: str,
    orbit: list[float],
    *,
    mesh: str = SMALLSAT_MESH,
    scale: float = 1.0,
    components: list[dict[str, Any]] | None = None,
    mass: float = 100.0,
    rpo: bool = False,
) -> dict[str, Any]:
    visualization: dict[str, Any] = {
        "mesh": mesh,
        "scale": scale,
        "offset": [0.0, 0.0, 0.0],
        "reflectivity": 0.45,
    }

    return {
        "id": asset_id,
        "name": name,
        "orbit": {
            "planet": "Earth",
            "values": orbit,
            "offset": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        },
        "physics": {
            "override_mass": True,
            "mass": mass,
            "center_of_mass": [0.0, 0.0, 0.0],
            "inertia_tensor": [
                [12.0, 0.0, 0.0],
                [0.0, 12.0, 0.0],
                [0.0, 0.0, 12.0],
            ],
        },
        "visualization": visualization,
        "controller": {
            "safe_fraction": 0.1,
            "capture_tax": 0.001,
            "downlink_tax": 0.01,
            "ping_interval": 5.0,
            "reset_interval": 30.0,
            "jamming_multiplier": 1.0,
            "enable_rpo_software": rpo,
        },
        "components": components if components is not None else bus_components("cosmos"),
    }


def iceye_asset(*, include_camera: bool = True) -> dict[str, Any]:
    components = bus_components("iceye")
    if include_camera:
        components.append(
            component(
                "Camera",
                "SAR-X36 X-Band Imaging Payload",
                {
                    "Sample Rate": 5.0,
                    "Mass": 8.0,
                    "Aperture": 25.0,
                    "Min Field Of View": 2.0,
                    "Field Of View": 12.0,
                    "Max Field Of View": 25.0,
                    "Focusing Distance": 600000.0,
                    "Resolution": [1024, 1024],
                },
                position=ICEYE_CAMERA_POSITION,
                rotation=ICEYE_CAMERA_ROTATION,
            )
        )
    return asset(
        "SC_ICEYE_X36",
        "ICEYE-X36",
        scenario_orbit("ICEYE-X36", "initial"),
        mesh=ICEYE_MESH,
        scale=0.2,
        components=components,
        mass=100.0,
    )


def overwatch_asset(stage: str) -> dict[str, Any]:
    orbit = scenario_orbit("ICEYE-X36", "initial")
    if stage == "custody":
        # Start roughly 5 km radially outside Cosmos 2614. Section 4 is about
        # sensor tasking, so the target must already be close enough to read in
        # the optical view without replaying another long rendezvous.
        orbit[0] += 5.0
        orbit[5] = (
            orbit[5] + SECTION_4_ALONG_TRACK_OFFSETS_DEG["COSMOS 2614"]
        ) % 360.0
    else:
        orbit[0] += 15.0
        orbit[5] = (orbit[5] + 0.22) % 360.0
    components = bus_components("overwatch")
    components.extend(
        [
            component(
                "Camera",
                OVERWATCH_OPTICAL_CAMERA,
                {
                    "Sample Rate": 10.0,
                    "Mass": 6.0,
                    "Aperture": 40.0,
                    "Min Field Of View": 0.5,
                    "Field Of View": 5.0,
                    "Max Field Of View": 15.0,
                    "Focusing Distance": 250000.0,
                    "Resolution": [1024, 1024],
                    "IsMonochromatic": True,
                },
                position=OVERWATCH_SENSOR_POSITION,
                rotation=OVERWATCH_SENSOR_ROTATION,
            ),
            # The "Event Camera" class alias resolves to the same ACamera class as
            # a plain camera, so "IsEvent" is what actually puts it in event mode.
            # Without it this would just be a second ordinary camera.
            component(
                "Event Camera",
                OVERWATCH_EVENT_CAMERA,
                {
                    "Sample Rate": 10.0,
                    "Mass": 4.0,
                    "Aperture": 40.0,
                    "Min Field Of View": 0.5,
                    "Field Of View": 5.0,
                    "Max Field Of View": 15.0,
                    "Focusing Distance": 250000.0,
                    "Resolution": [1024, 1024],
                    "IsMonochromatic": True,
                    "IsEvent": True,
                },
                position=OVERWATCH_SENSOR_POSITION,
                rotation=OVERWATCH_SENSOR_ROTATION,
            ),
            component(
                "Radar",
                "SBR-900 Space Surveillance Radar",
                {
                    "Field Of View": 20.0,
                    "Power": 5000.0,
                    "Gain": 45.0,
                    "Detection Threshold": 8.0,
                    "Mass": 8.0,
                },
                position=OVERWATCH_SENSOR_POSITION,
                rotation=OVERWATCH_SENSOR_ROTATION,
            ),
            component(
                "Laser Range Finder",
                "LRP-1550 Laser Ranging Payload",
                {
                    "Operating Range": 2000000.0,
                    "Range Accuracy Constant": 1.0,
                    "Sample Rate": 1.0,
                    "Mass": 2.0,
                },
                position=OVERWATCH_SENSOR_POSITION,
                rotation=OVERWATCH_SENSOR_ROTATION,
            ),
        ]
    )
    return asset(
        "SC_SDA_OVERWATCH",
        "SDA Overwatch",
        orbit,
        mesh=OVERWATCH_MESH,
        scale=0.65,
        components=components,
        mass=220.0,
    )


def cosmos_asset(name: str, stage: str, *, rpo: bool = False) -> dict[str, Any]:
    number = name.split()[-1]
    components = bus_components("cosmos")
    if name == "COSMOS 2614" and stage == "close":
        components.append(
            component(
                "Camera",
                COSMOS_2614_OPTICAL_CAMERA,
                {
                    "Sample Rate": 10.0,
                    "Mass": 4.0,
                    "Aperture": 20.0,
                    "Min Field Of View": 0.25,
                    "Field Of View": 0.5,
                    "Max Field Of View": 5.0,
                    "Focusing Distance": 1000.0,
                    "Resolution": [1024, 1024],
                },
                position=[0.0, -0.293, -0.018],
                rotation=[90.0, 0.0, 0.0],
            )
        )
    return asset(
        f"SC_COSMOS_{number}",
        name,
        scenario_orbit(name, stage),
        scale=0.75,
        # Neutral spacecraft are targetable but not controllable by Blue.
        components=components,
        mass=120.0,
        rpo=rpo,
    )


def rpo_event(
    name: str,
    label: str,
    time: float,
    offset: list[float],
    max_speed: float,
    acceleration: float,
) -> dict[str, Any]:
    """One rendezvous event, naming exactly one chaser.

    The event reference warns that an empty `Assets` list makes every
    RPO-enabled spacecraft attempt the manoeuvre, so never widen this.

    `Max Speed` and `Approach Acceleration` are absent from the documented
    event `Data` table but are read by the handler, which strips spaces and
    ignores case before forwarding them to the operator command as `max_speed`
    and `approach_acceleration`.
    """
    return {
        "Enabled": True,
        "Name": f"{name} {label}",
        "Time": time,
        "Repeat": False,
        "Interval": 1.0,
        "Type": "Spacecraft",
        "Target": "Rendezvous",
        "Assets": [f"SC_COSMOS_{name.split()[-1]}"],
        "Data": {
            "Target": "SC_ICEYE_X36",
            "Active": True,
            "Dock": False,
            "Offset X": offset[0],
            "Offset Y": offset[1],
            "Offset Z": offset[2],
            "Max Speed": max_speed,
            "Approach Acceleration": acceleration,
        },
    }


def rpo_approach_events(cosmos_names: list[str]) -> list[dict[str, Any]]:
    events = [
        rpo_event(
            name,
            "Closes On ICEYE-X36",
            RPO_START_TIME_S,
            RPO_CLOSURE_OFFSETS_M[name],
            RPO_TRANSIT_MAX_SPEED_M_S,
            RPO_TRANSIT_ACCEL_M_S2,
        )
        for name in cosmos_names
    ]
    events.extend(
        rpo_event(
            phase["spacecraft"],
            phase["label"],
            phase["time"],
            phase["offset"],
            phase["max_speed"],
            phase["acceleration"],
        )
        for phase in RPO_REPEAT_SEQUENCE
        if phase["spacecraft"] in cosmos_names
    )
    return sorted(events, key=lambda event: event["Time"])


def iceye_nadir_event() -> dict[str, Any]:
    """Slew ICEYE to nadir at T+0 so Section 4 does not need a manual setup command.

    There is no payload camera on ICEYE in that section. The SAR camera's +z axis
    is body -Y after the 90° X rotation, so body -Y is the equivalent nadir face.
    """
    return {
        "Enabled": True,
        "Name": "ICEYE-X36 Holds Nadir",
        "Time": 0.0,
        "Repeat": False,
        "Interval": 1.0,
        "Type": "Spacecraft",
        "Target": "Guidance",
        "Assets": ["SC_ICEYE_X36"],
        "Data": {
            "Pointing": "nadir",
            "Alignment": "-y",
            "Planet": "earth",
        },
    }


def cosmos_2614_optical_guidance_event() -> dict[str, Any]:
    """Point COSMOS 2614's optical camera at the ICEYE spacecraft origin."""
    return {
        "Enabled": True,
        "Name": "COSMOS 2614 Begins Optical Inspection",
        "Time": COSMOS_2614_OPTICAL_POINTING_TIME_S,
        "Repeat": False,
        "Interval": 1.0,
        "Type": "Spacecraft",
        "Target": "Guidance",
        "Assets": ["SC_COSMOS_2614"],
        "Data": {
            "Pointing": "relative",
            "Target": COSMOS_2614_OPTICAL_CAMERA,
            "Alignment": "+z",
            "Spacecraft": "SC_ICEYE_X36",
        },
    }


def base_scenario(
    *,
    section_number: int,
    title: str,
    description: str,
    brief: str,
    stage: str,
    speed: float,
    end_time: float,
    include_overwatch: bool,
    include_cosmos: bool = True,
    cosmos_rpo: bool = False,
    include_iceye_camera: bool = True,
    extra_events: list[dict[str, Any]] | None = None,
    epoch: str = EPOCH,
) -> dict[str, Any]:
    if speed > MAX_SPEED:
        raise ValueError(
            f"Section {section_number} asks for speed {speed}, but Euler at a "
            f"{STEP_SIZE} s step only holds together to {MAX_SPEED}x. "
            "Speed the footage up in the edit instead."
        )

    assets = [iceye_asset(include_camera=include_iceye_camera)]
    collection_ids = ["SC_ICEYE_X36"]
    if include_overwatch:
        assets.append(overwatch_asset(stage))
        collection_ids.append("SC_SDA_OVERWATCH")

    # Section 1 leaves the Cosmos out of the file entirely rather than loading
    # them hidden. Studio still draws labels for hidden spacecraft, which named
    # all five Russian craft on screen before the story introduces them, and
    # simulating five unused buses spends CPU the 8x speed cap cannot spare.
    cosmos_names = (
        [name for name in SPACECRAFT_SOURCE if name.startswith("COSMOS")]
        if include_cosmos
        else []
    )
    assets.extend(cosmos_asset(name, stage, rpo=cosmos_rpo) for name in cosmos_names)
    neutral_ids = [f"SC_COSMOS_{name.split()[-1]}" for name in cosmos_names]
    events = rpo_approach_events(cosmos_names) if cosmos_rpo else []
    if cosmos_rpo and "COSMOS 2614" in cosmos_names:
        events.append(cosmos_2614_optical_guidance_event())
    if extra_events:
        events.extend(extra_events)
    events.sort(key=lambda event: event["Time"])

    return {
        "metadata": {
            "name": f"Intent in Orbit - Stage {section_number}",
            "description": description,
            "brief": brief,
        },
        "simulation": {
            "epoch": epoch,
            "speed": speed,
            "step_size": STEP_SIZE,
            "integrator": INTEGRATOR,
            "end_time": end_time,
        },
        "universe": {
            "atmosphere": False,
            "magnetosphere": False,
            "gps": True,
            "cloud_opacity": 0.35,
            "cloud_contrast": 2.0,
            "ambient_light": 0.35,
        },
        "ground_stations": {
            # ICEYE-X36 starts at 81.6 N / 72.1 W and descends over Arctic Canada
            # into the eastern Pacific. Anchorage acquires first at T+185s and
            # Vancouver gives the strongest pass. Reykjavik covers the northern
            # leg of later orbits.
            "locations": ["Anchorage", "Vancouver", "Reykjavik"],
            "min_elevation": 5,
            "max_range": 0,
            "scale": 100,
        },
        "teams": [
            {
                "enabled": True,
                "id": 591036,
                "password": "X36SDA",
                "name": "Blue",
                "key": 36,
                "frequency": 591,
                "collection": "Blue",
                "color": "#18D5FF",
            }
        ],
        "assets": {
            "space": assets,
            "collections": [{"id": "Blue", "space_assets": collection_ids}],
            "neutral": neutral_ids,
        },
        "objects": {"ground": [], "space": []},
        "events": events,
        "questions": [],
    }


def maritime_objects() -> list[dict[str, Any]]:
    # A neutral Arctic shipping scene placed under the ICEYE-X36 ground track at
    # roughly T+120s (Viscount Melville Sound). Filming notes call for positioning
    # the Studio camera as needed rather than claiming this is a real ICEYE task.
    return [
        {
            "id": "GO_MARITIME_01",
            "type": "vessel",
            "name": "Commercial Vessel Alpha",
            "planet": "Earth",
            "latitude": 76.85,
            "longitude": -104.6,
            "altitude": 0.001,
            "scale": 140,
            "color": "#FFFFFF",
            "data": {"heading": 92.0, "speed": 8.0},
        },
        {
            "id": "GO_MARITIME_02",
            "type": "vessel",
            "name": "Commercial Vessel Bravo",
            "planet": "Earth",
            "latitude": 76.70,
            "longitude": -105.2,
            "altitude": 0.001,
            "scale": 140,
            "color": "#80DEEA",
            "data": {"heading": 275.0, "speed": 6.0},
        },
        {
            "id": "GO_MARITIME_LABEL",
            "type": "text",
            "name": "Nominal Maritime Task",
            "planet": "Earth",
            "latitude": 76.78,
            "longitude": -104.89,
            "altitude": 0.003,
            "scale": 90000,
            "color": "#0B2239",
            "data": {"text": "MARITIME TASK"},
        },
    ]


def build_section_1() -> dict[str, Any]:
    scenario = base_scenario(
        section_number=1,
        title="Nominal Operations",
        description="ICEYE-X36 performs a routine commercial maritime imaging task.",
        brief=(
            "# Filming state\n"
            "Blue controls ICEYE-X36. The five Cosmos craft are absent from this section entirely so the "
            "opening shot shows one asset and one plane; they arrive in Stage 2. "
            "This is a neutral illustrative maritime task, not a historical ICEYE collection claim. "
            "The Camera-class SAR-X36 payload is a visual stand-in for command flow; it does not simulate SAR phenomenology."
        ),
        stage="initial",
        speed=8.0,
        end_time=900.0,
        include_overwatch=False,
        include_cosmos=False,
    )
    scenario["objects"]["ground"] = maritime_objects()
    return scenario


def build_section_2() -> dict[str, Any]:
    scenario = base_scenario(
        section_number=2,
        title="The Pattern Emerges",
        description="Several individually ambiguous plane changes begin pointing toward one destination plane.",
        brief=(
            "# Decision point\n"
            "This is 16 May 2026, a real moment in the catalogue chronology. Cosmos 2613, 2610, and 2612 have each "
            "completed their full inclination campaign and now share ICEYE-X36's plane near 97.8 deg. Cosmos 2611 and "
            "2614 have not moved and will not until 20-21 May, so they still sit near 96.95 deg. Three of five is the "
            "beat where a coordinated pattern becomes the leading explanation. "
            "Nothing manoeuvres during this section: the inclinations are staged initial conditions, because the "
            "simulator has no scheduled-impulse event. Catalogue gaps bound the changes but do not measure exact impulses."
        ),
        stage="partial",
        speed=8.0,
        end_time=1800.0,
        include_overwatch=False,
    )
    return scenario


def build_section_3() -> dict[str, Any]:
    scenario = base_scenario(
        section_number=3,
        title="Coercive Proximity",
        description="The five inclinations have converged; an illustrative continuation places them in sustained proximity.",
        brief=(
            "# Evidence boundary\n"
            "Inclination endpoints and Delta-V totals come from the supplied reconstruction. "
            "Everything about the proximity is illustrative. The five craft start 22-85 km from ICEYE-X36 and, at "
            "T+60s, RPO flight software closes each one onto its own station between 2.9 and 8.1 km. Cosmos 2614 then "
            "tightens to 1.0 km at T+3000s, points a narrow-field optical camera at ICEYE-X36, and withdraws to 6.0 km "
            "at T+4800s, to show repeatable access rather than a single arrival. The camera, pointing and imagery are "
            "illustrative; the supplied data contains no attitude or payload evidence. These are simulated manoeuvres "
            "invented for this film: their Delta-V is not the "
            "reconstructed 108-117 m/s, the craft have no thrusters so the motion costs no propellant, and none of it "
            "reconstructs the reported 29 May approach. Do not show or narrate a 13 km claim."
        ),
        stage="close",
        cosmos_rpo=True,
        speed=8.0,
        end_time=12793.0,
        include_overwatch=False,
    )
    return scenario


def build_section_4() -> dict[str, Any]:
    scenario = base_scenario(
        section_number=4,
        title="Blue Tightens Custody",
        description="With Cosmos 2614 holding near ICEYE, Blue tasks an orbital SDA asset to improve range and optical custody.",
        brief=(
            "# Operator shot\n"
            "This section starts 22 hours later with the five Cosmos spacecraft already at illustrative close stations "
            "around ICEYE-X36: Cosmos 2614 is about 1 km from ICEYE, the other four are about 4-8 km away, and SDA "
            "Overwatch is staged about 5 km radially outside Cosmos 2614. ICEYE-X36 has no imaging payload here "
            "and is slewed to nadir at T+0, so do not set it up by hand. The Cosmos craft have no cameras. "
            "Select SDA Overwatch, point SBR-900 Space Surveillance Radar, OTC-450 Optical Tracking Camera "
            "or EVS-450 Neuromorphic Event Camera at Cosmos 2614, capture/range, then downlink. "
            "The proximity and orbital sensor are illustrative; this fictional orbital sensor is not Spaceflux. "
            "Spaceflux credit is limited to optical observations of Cosmos 2610, 2612, 2613, and 2614."
        ),
        stage="custody",
        speed=5.0,
        end_time=1200.0,
        include_overwatch=True,
        include_iceye_camera=False,
        extra_events=[iceye_nadir_event()],
        epoch=SECTION_4_EPOCH,
    )
    return scenario


def build_section_5() -> dict[str, Any]:
    scenario = base_scenario(
        section_number=5,
        title="Debrief and Replay",
        description="Reset to the early pattern and ask when Blue should have acted.",
        brief=(
            "# Closing state\n"
            "Replay the partial-burn state. The key decision window is Days 2–3 in the real chronology: "
            "the pattern is emerging, evidence is still incomplete, and low-cost responses remain available."
        ),
        stage="partial",
        speed=8.0,
        end_time=1800.0,
        include_overwatch=True,
    )
    return scenario


def build_all() -> dict[str, dict[str, Any]]:
    scenarios = [
        build_section_1(),
        build_section_2(),
        build_section_3(),
        build_section_4(),
        build_section_5(),
    ]
    return dict(zip(OUTPUT_NAMES, scenarios, strict=True))


def validate(scenarios: dict[str, dict[str, Any]]) -> None:
    expected_neutral = {f"SC_COSMOS_{number}" for number in range(2610, 2615)}
    for filename, scenario in scenarios.items():
        expected_epoch = SECTION_4_EPOCH if filename == "section_4.json" else EPOCH
        assert scenario["simulation"]["epoch"] == expected_epoch
        assert scenario["simulation"]["integrator"] == INTEGRATOR
        assert scenario["simulation"]["step_size"] == STEP_SIZE
        assert scenario["simulation"]["speed"] <= MAX_SPEED
        asset_ids = {entry["id"] for entry in scenario["assets"]["space"]}
        assert len(asset_ids) == len(scenario["assets"]["space"])
        assert scenario["questions"] == []
        iceye = next(
            entry
            for entry in scenario["assets"]["space"]
            if entry["id"] == "SC_ICEYE_X36"
        )
        assert iceye["visualization"]["mesh"] == ICEYE_MESH
        assert iceye["visualization"]["scale"] == 0.2

        # The SAR mount is measured against the Landsat 8 chassis, so it has to
        # be re-checked alongside the mesh. Section 4 carries no ICEYE camera.
        iceye_cameras = [
            entry for entry in iceye["components"] if entry["class"] == "Camera"
        ]
        if filename == "section_4.json":
            assert not iceye_cameras
        else:
            assert len(iceye_cameras) == 1
            assert iceye_cameras[0]["position"] == ICEYE_CAMERA_POSITION
            assert iceye_cameras[0]["rotation"] == ICEYE_CAMERA_ROTATION

        # Section 1 ships without the Cosmos so the opening shot cannot leak
        # their labels. Every later section needs all five, and none of them
        # should be hidden: a hidden asset still draws a Studio label.
        if filename == "section_1.json":
            assert not scenario["assets"]["neutral"]
            assert not (expected_neutral & asset_ids)
        else:
            assert set(scenario["assets"]["neutral"]) == expected_neutral
            assert expected_neutral <= asset_ids
        for entry in scenario["assets"]["space"]:
            assert "hide" not in entry["visualization"]

        # RPO belongs to Section 3 alone. Anywhere else it would turn the
        # staged evidence into a flown simulation.
        rpo_assets = {
            entry["id"]
            for entry in scenario["assets"]["space"]
            if entry["controller"]["enable_rpo_software"]
        }
        if filename == "section_3.json":
            assert rpo_assets == expected_neutral
            assert len(scenario["events"]) == len(expected_neutral) + len(
                RPO_REPEAT_SEQUENCE
            ) + 1
            times = [event["Time"] for event in scenario["events"]]
            assert times == sorted(times)
            assert max(times) < scenario["simulation"]["end_time"]
            rendezvous_events = [
                event for event in scenario["events"] if event["Target"] == "Rendezvous"
            ]
            assert len(rendezvous_events) == len(expected_neutral) + len(
                RPO_REPEAT_SEQUENCE
            )
            for event in rendezvous_events:
                assert event["Target"] == "Rendezvous"
                assert event["Data"]["Target"] == "SC_ICEYE_X36"
                # One named chaser per event, or every RPO craft joins in.
                assert len(event["Assets"]) == 1
                assert event["Assets"][0] in rpo_assets
                # The rendezvous command clamps each LVLH axis to +/-10 km.
                for axis in ("Offset X", "Offset Y", "Offset Z"):
                    assert abs(event["Data"][axis]) <= 10000.0
            guidance_events = [
                event for event in scenario["events"] if event["Target"] == "Guidance"
            ]
            assert guidance_events == [cosmos_2614_optical_guidance_event()]
            cosmos_2614 = next(
                entry
                for entry in scenario["assets"]["space"]
                if entry["id"] == "SC_COSMOS_2614"
            )
            assert any(
                component["name"] == COSMOS_2614_OPTICAL_CAMERA
                and component["data"]["Field Of View"] == 0.5
                and component["position"] == [0.0, -0.293, -0.018]
                and component["rotation"] == [90.0, 0.0, 0.0]
                for component in cosmos_2614["components"]
            )
        elif filename == "section_4.json":
            assert not rpo_assets
            assert scenario["events"] == [iceye_nadir_event()]
        else:
            assert not rpo_assets
            assert not scenario["events"]

        json.dumps(scenario, allow_nan=False)

    for name in SPACECRAFT_SOURCE:
        if not name.startswith("COSMOS"):
            continue
        final_i = inclination_after(name)
        assert abs(final_i - ICEYE_INCLINATION_DEG) < 0.07
        assert 107.0 < total_delta_v(name) < 118.0

    # Guard the two evidence boundaries most likely to drift during edits.
    section_3 = scenarios["section_3.json"]
    assert "illustrative" in section_3["metadata"]["brief"].lower()
    assert "13 km" in section_3["metadata"]["brief"]
    section_4 = scenarios["section_4.json"]
    assert "fictional" in section_4["metadata"]["brief"].lower()
    assert section_4["simulation"]["epoch"] == SECTION_4_EPOCH
    section_4_assets = {
        entry["id"]: entry for entry in section_4["assets"]["space"]
    }
    iceye_orbit = section_4_assets["SC_ICEYE_X36"]["orbit"]["values"]
    for name, offset in SECTION_4_ALONG_TRACK_OFFSETS_DEG.items():
        cosmos_orbit = section_4_assets[
            f"SC_COSMOS_{name.split()[-1]}"
        ]["orbit"]["values"]
        assert cosmos_orbit[:5] == iceye_orbit[:5]
        assert abs(cosmos_orbit[5] - ((iceye_orbit[5] + offset) % 360.0)) < 1e-8
    overwatch_orbit = section_4_assets["SC_SDA_OVERWATCH"]["orbit"]["values"]
    cosmos_2614_orbit = section_4_assets["SC_COSMOS_2614"]["orbit"]["values"]
    assert abs(overwatch_orbit[0] - cosmos_2614_orbit[0] - 5.0) < 1e-8
    assert overwatch_orbit[1:] == cosmos_2614_orbit[1:]

    iceye = section_4_assets["SC_ICEYE_X36"]
    assert not any(entry["class"] in {"Camera", "Event Camera"} for entry in iceye["components"])
    for name in SECTION_4_ALONG_TRACK_OFFSETS_DEG:
        cosmos = section_4_assets[f"SC_COSMOS_{name.split()[-1]}"]
        assert not any(
            entry["class"] in {"Camera", "Event Camera"} for entry in cosmos["components"]
        )

    # All four custody sensors must stay on one boresight, or the single
    # Guidance command in Section 4 aims the camera somewhere the radar is not.
    overwatch_sensors = [
        entry
        for entry in section_4_assets["SC_SDA_OVERWATCH"]["components"]
        if entry["class"] in {"Camera", "Event Camera", "Radar", "Laser Range Finder"}
    ]
    assert len(overwatch_sensors) == 4
    optical = next(entry for entry in overwatch_sensors if entry["name"] == OVERWATCH_OPTICAL_CAMERA)
    event_camera = next(
        entry for entry in overwatch_sensors if entry["name"] == OVERWATCH_EVENT_CAMERA
    )
    assert optical["class"] == "Camera"
    assert optical["data"]["IsMonochromatic"] is True
    assert event_camera["class"] == "Event Camera"
    assert event_camera["data"]["IsMonochromatic"] is True
    # The class alias alone does not enable event mode; IsEvent does.
    assert event_camera["data"]["IsEvent"] is True
    for entry in overwatch_sensors:
        assert entry["position"] == OVERWATCH_SENSOR_POSITION
        assert entry["rotation"] == OVERWATCH_SENSOR_ROTATION
        assert entry["mesh"] == "None"


def render(scenario: dict[str, Any]) -> str:
    return json.dumps(scenario, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if committed section JSON differs from generated output",
    )
    args = parser.parse_args()

    scenarios = build_all()
    validate(scenarios)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    stale: list[str] = []
    for filename, scenario in scenarios.items():
        path = CONFIG_DIR / filename
        expected = render(scenario)
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                stale.append(filename)
        else:
            path.write_text(expected, encoding="utf-8")
            print(f"Wrote {path.name}")

    if stale:
        print("Generated files are stale or missing: " + ", ".join(stale))
        return 1
    if args.check:
        print("All ICEYE filming scenarios are current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
