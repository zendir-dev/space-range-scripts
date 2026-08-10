**Scenario:** Orbital Detective  
**Epoch:** 2026-06-21 04:00:00 UTC  
**Duration:** 180 minutes simulated (about 60 minutes real time at 3x speed)  
**Ground Segment:** Dubai, Singapore, Lima, Tokyo, Honolulu, Moscow

---

## Overview

You are a Space Domain Awareness (SDA) operator team. Your job is to watch, track, image, and classify a field of objects in orbit using two spacecraft you share: a **LEO** spacecraft for close survey work and a **GEO** spacecraft in the geostationary belt on the equator. You do not command any of the targets. Everything you learn about them comes from your own sensors: the optical camera, the charge coupled device (CCD) imager, and the RADAR.

The target field has four problems in it. A six-satellite constellation is flying in front of your LEO node, and not every member is what it claims to be. A commercial debris-removal company has contracted you to triage a set of tumbling rocket bodies for capture, and each spins at a different rate. Two unidentified tracks sit in your GEO node's neighbourhood, and ground cannot tell you which one is the friendly station-keeper and which is the intruder. And an on-orbit event throws up a single high-priority object that analysts assess is transferring toward the GEO belt - it rises over your LEO horizon early in the pass and is your top collection priority.

The scenario epoch is set near the June solstice to keep your spacecraft and the targets well illuminated for photometry. Remember that a target's brightness tells you about its surface and its spin, not its identity - you distinguish objects photometrically (brightness), by RADAR range behaviour, and by orbit shape, never by any radio identifier.

> Questions and scoring are delivered in the **Tasks** section of the operator terminal. Use this brief for mission context, spacecraft configuration, sensor limits, the debris capture-safety data, and the Threat Catalog. It is not an answer key.

---

## Mission Goals

### Phase 1 - Constellation Analysis

The **Helios** constellation is a cluster of six identical satellites leading your LEO Overwatch node in the same orbit plane. Hold velocity pointing so the cluster stays in your field of view, then image the members.

1. **Survey the cluster:** Use the LEO Overwatch imaging sensors to capture all six Helios members.
2. **Find the rogues:** Some members carry an anomalous surface reflectivity and image differently from the rest. Determine how many are rogue and which specific satellites they are.
3. **Justify your method:** Be ready to state which sensor gave you the classification.

### Phase 2 - Debris Analysis (commercial tasking)

**Orbit Recovery Services (ORS)**, a commercial debris-removal company, has contracted your team to **triage** three spent rocket bodies (**R/B Titan**, **R/B Atlas**, **R/B Delta**) ahead of a servicing-tug capture mission. ORS needs to know how fast each body is spinning and whether it is safe to grab.

1. **Detect the tumble:** Use the CCD to build a light curve for each rocket body. A repeating rise and fall in brightness means the object is rotating.
2. **Measure roll rate:** Read the period between brightness peaks and convert it to a dominant spin rate in degrees per second (see the conversion note under the capture-safety table).
3. **Advise the client:** Apply the roll rate to the capture-safety table below and classify each rocket body as safe, caution, or unsafe for ORS to capture.

### Phase 3 - Friendly Approach

Two unidentified tracks share your GEO node's neighbourhood: **GEO-Sierra** and **GEO-Tango**. The callsigns are just track labels - they tell you nothing about intent, and ground cannot say which is friendly. Both are close enough to hold on RADAR.

1. **Range them:** Use the GEO node RADAR to measure range to each track over several minutes.
2. **Separate the two behaviours:** One track shares your orbital period and holds a bounded, roughly constant range - a co-orbital neighbour keeping station. The other is on a slightly different orbit and period, so its range to you changes as it drifts - the intruder. Decide which is which from the range trend alone.

### Phase 4 - High-Priority Intercept (PRIORITY TASKING)

An **on-orbit event** has just been detected. Analysts assess that the object thrown up by the event is on a **transfer orbit climbing toward the GEO belt**, and it rises over your **LEO Overwatch** horizon between roughly **T+18 and T+32 minutes** of simulated time. **This is your top collection priority and carries the most marks.**

1. **Acquire:** Slew the LEO Overwatch imager to catch the object during its horizon pass - the window is short.
2. **Image:** Capture an optical image of the object.
3. **Identify:** Match its orbit and appearance against the **Threat Catalog** below and report its catalog designation.

> The object is on a highly elliptical transfer orbit - it swings from a low perigee up into and beyond the GEO belt on each revolution - which is unlike anything else in the field. Use that transfer-orbit signature to confirm the analysts' call and pick it out of the catalog.

### Phase 5 - Orbit Determination

Your LEO Overwatch node's own navigation is healthy.

1. **Pull the state:** Use the LEO node GPS telemetry to recover its orbit.
2. **Report the elements:** Determine the semi-major axis, eccentricity, inclination, and altitude of the LEO Overwatch orbit.

---

## Threat Catalog

Use this catalog for **Phase 4**. Capture an image of the high-priority object, read its orbit from your RADAR and imagery, and match it to the entry that fits. Each entry has a distinct orbit signature, so orbit class alone will identify it.

| Designation | Orbit class | Size / RADAR return | Distinguishing signature |
| --- | --- | --- | --- |
| **PHANTOM** | Highly elliptical transfer orbit (GEO-transfer / GTO-type), inclined ~46 deg | Large / strong | Swings from a low perigee up into and beyond the GEO belt on every revolution; appears low and rises quickly over the LEO horizon; the only object on a transfer orbit in the field |
| **HALCYON** | Geostationary (GEO) | Medium | Holds a fixed sub-longitude with near-zero relative motion in the GEO belt |
| **DRAKE** | Low Earth Orbit, near-circular (sun-synchronous) | Small / weak | Low altitude, fast ground track, small RADAR cross-section |
| **MERIDIAN** | Medium Earth Orbit, circular | Medium | Steady circular orbit at roughly constant medium altitude |

---

## Operational Constraints

| Constraint | Detail |
| --- | --- |
| Targets | All targets are passive. You cannot command them, and they broadcast no telemetry to you. |
| RPO Software | Not available - no automated rendezvous or proximity guidance |
| Propulsion | No thrusters installed on either spacecraft |
| Attitude Control | Reaction wheels available - point your sensors with guidance commands |
| Classification Data | Photometry (CCD / optical brightness), RADAR range, and orbit shape only. No RF identification of targets. |

---

## Spacecraft Configuration

Each team operates the same two-node network: one **LEO** spacecraft and one **GEO** spacecraft. They are nearly identical in their schematics (and components on-board), but differ in their orbits.

### Schematic

![Orbital Detective Spacecraft Schematic](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/orbital_detective/schematic.png)

### Platform Summary

| Item | LEO | GEO |
| --- | --- | --- |
| Mass | 300 kg | 350 kg |
| Power Storage | 160 Ah Battery | 200 Ah Battery |
| Imaging | Optical Camera and CCD Imager | Optical Camera and CCD Imager |
| Ranging | RADAR | RADAR |
| Navigation | GPS Sensor | GPS Sensor |
| Communications | Receiver and Transmitter | Receiver and Transmitter |
| Propulsion | None | None |
| ADCS | Reaction Wheels | Reaction Wheels |

---

## Sensors

Both spacecraft carry the same sensor suite. Point the boresight with guidance commands before capturing.

### Optical Camera

Each spacecraft is equipped with an optical imager (Optical Camera). These provide color-images of the various spacecraft in orbit and useful for detecting motion in the objects and rocket-bodies.

| Specification | LEO | GEO |
| --- | --- | --- |
| Resolution | 1024 x 1024 | 512 x 512 |
| Min Field of View | 3 deg | 0.1 deg |
| Max Field of View | 15 deg | 5 deg |
| Aperture | 15mm | 30mm |

### Charge Coupled Device (CCD)

Your primary tool for photometry: measuring how bright a target is and how its brightness changes over time. Use it to compare and identify reflectivity across the Helios members and to spot the tumbling rocket bodies.

| Specification | LEO | GEO |
| --- | --- | --- |
| Resolution | 64 x 64 | 64 x 64 |
| Field of View | 5 deg | 2 deg |
| Exposure Time | 0.05 s | 0.3 s |
| Spectral Wavelength | 550 nm | 550 nm |

> The wider LEO field of view suits surveying the six-satellite constellation and catching the fast intercept pass; the narrow GEO field of view and longer exposure suit faint, distant targets in the GEO belt.

### RADAR

Active ranging. Use it to measure distance to a target and to watch how that distance changes, which is how you separate a station-keeping neighbour from a drifting object in the GEO belt.

| Specification | LEO | GEO |
| --- | --- | --- |
| Field of View | 20 deg | 15 deg |
| Power | 2000 | 2000 |
| Gain | 40 | 42 |
| Detection Threshold | 10 | 9 |

> Unlike the Optical Camera and the CCD that are oriented in the same direction on the spacecraft, the RADAR is located 180 degrees away from the camera at the back. To target the RADAR sensor towards the same target spacecraft, a full rotation of the spacecraft must be made. This can be done by switching which component is the target component in the ADCS guidance controller mode.

### Other sensors

- **GPS Sensor:** Position and velocity for your own spacecraft, as well as accurate latitude, longitude and altitude readings. Both spacecraft should report healthy navigation across the mission.

---

## Debris Capture-Safety Reference

A servicing tug can only capture a rocket body if it is not spinning too fast. Use your measured roll rate (dominant spin rate, in degrees per second) with the thresholds below to classify each rocket body.

| Roll rate | Classification | Action |
| --- | --- | --- |
| 2.5 deg/s or less | **Safe for collection** | Capture may proceed |
| 2.5 to 4.0 deg/s | **Caution** | Despin required before capture |
| Greater than 4.0 deg/s | **Unsafe** | Do not attempt capture |

> **Converting a light curve to a roll rate:** measure the dominant period between repeating brightness maxima, then take roll rate (deg/s) ≈ 360 / (period in seconds). As a guide, a ~180 s period is about 2 deg/s (safe), ~120 s is about 3 deg/s (caution), and ~80 s is about 4.5 deg/s (unsafe). A shorter period means a faster roll.

---

## Communications

### Ground stations

| Station | Role |
| --- | --- |
| Dubai, Singapore, Lima, Tokyo, Honolulu, Moscow | Distributed ground network for uplink and downlink |

The station set is spread in longitude to keep your spacecraft in contact as they move. Use the **Link Budget** panels in the operator terminal for predicted contact intervals and signal quality.

### Team Frequencies

Each team commands only its own two-node network. Your team is assigned a unique communications frequency at the start of the scenario, pre-configured and identical on the uplink and downlink. The Helios satellites, rocket bodies, GEO-region objects, and the intercept are passive and are not controllable by anyone.

---

## Suggested Team Roles

Split responsibilities early. The Mission Lead should assign these roles at the start of the exercise:

- **Mission Lead:** Assigns roles, answers questions, monitors key information, and makes go/no-go calls - including prioritising the Phase 4 intercept when it appears.
- **Satellite Operator:** Manages telemetry, guidance pointing, and spacecraft health across both nodes.
- **Payload Operator:** Captures CCD and optical imagery and RADAR ranges, builds light curves, and reads reflectivity and roll rate.
- **Communications Specialist:** Monitors link budgets, GPS telemetry, and contact windows.

---

## Before You Begin

1. Log in to the operator terminal with your team credentials.
2. Confirm both nodes report telemetry and the Link Budget is nominal.
3. Read the in-simulation Tasks to understand scored questions, then prioritise by team expertise.
4. Split roles, and agree who watches the constellation on the LEO node and who works the GEO belt. Keep the LEO imager ready for the Phase 4 intercept window (T+18 to T+32 min).

---

## Learning focuses

### Photometric Classification

Compare reflectivity across identical-looking satellites with the CCD to pick out members whose surface brightness does not match the rest of the group.

### Light-Curve Analysis

Build brightness-versus-time curves for tumbling debris, measure the rotation period, convert it to a roll rate, and apply operational thresholds to make a capture decision.

### RADAR Custody

Use RADAR range trends to tell a stable co-orbital neighbour from a drifting object in the GEO belt.

### Time-Critical Tasking and Cataloguing

Acquire and image a high-priority object inside a short horizon window, then classify it by matching its orbit signature against a reference catalog.

### Orbit Determination

Recover an orbit - semi-major axis, eccentricity, inclination, and altitude - from GPS telemetry.
