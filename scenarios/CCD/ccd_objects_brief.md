**Scenario:** CCD  
**Epoch:** 2026-06-21 12:00:00 UTC  
**Duration:** 180 minutes simulated (about 60 minutes real time at 3x speed)  
**Ground Segment:** Casablanca, Dubai, Singapore, Sydney, Miami, Salvador, Tokyo, Honolulu, Moscow

---

## Overview

You are a Space Domain Awareness (SDA) operator team. Your job is to watch, track, image, and classify a field of objects in orbit using two spacecraft you share: a **LEO Overwatch** node for close survey work and a **GEO node** held over Singapore. You do not command any of the targets. Everything you learn about them comes from your own sensors: the optical camera, the charge coupled device (CCD) imager, and the radar.

The target field has three kinds of problem in it. A six-satellite constellation is flying in front of your LEO node, and not every member is what it claims to be. A set of large rocket bodies is tumbling near the GEO belt, and each spins at a different rate. Two objects sit in your GEO node's neighbourhood, and only one of them is minding its own orbit. On top of that, intelligence warns that your GEO node's own navigation may not be trustworthy.

The exercise runs in continuous sunlight, so your spacecraft and every target stay illuminated for the full hour. That matters for photometry: a target's brightness only tells you about its surface and its spin, not about it passing in and out of shadow.

> Questions and scoring are delivered in the **Tasks** section of the operator terminal. Use this brief for mission context, spacecraft configuration, sensor limits, and the debris capture-safety data. It is not an answer key.

---

## Mission Goals

### Phase 1 - Constellation Analysis

The **Helios** constellation is a cluster of six identical satellites leading your LEO Overwatch node in the same orbit plane. Hold velocity pointing so the cluster stays in your field of view, then image the members.

1. **Survey the cluster:** Use the LEO Overwatch imaging sensors to capture all six Helios members.
2. **Find the rogues:** Some members carry an anomalous surface reflectivity and image differently from the rest. Determine how many are rogue and which specific satellites they are.
3. **Justify your method:** Be ready to state which sensor gave you the classification.

### Phase 2 - Debris Analysis

Three spent rocket bodies (**R/B Titan**, **R/B Atlas**, **R/B Delta**) are tumbling near the GEO belt.

1. **Detect the tumble:** Use the CCD to build a light curve for each rocket body. A repeating rise and fall in brightness means the object is rotating.
2. **Measure roll rate:** Read the period between brightness peaks and convert it to a dominant spin rate in degrees per second.
3. **Rate each body for capture:** Apply the roll rate to the capture-safety table below and classify each rocket body as safe, caution, or unsafe.

### Phase 3 - Friendly Approach

Two objects share your GEO node's neighbourhood: **GEO-Companion** and **GEO-Interloper**.

1. **Range them:** Use the GEO node radar to measure range to each object over several minutes.
2. **Separate the two behaviours:** One object holds a stable, bounded orbit next to you. The other is closing. Decide which is which from the range trend.
3. **Time the approach:** Estimate when the approaching object reaches its closest point to your GEO node.

### Phase 4 - Sensor Error

Intelligence reports a supply-chain compromise on your GEO node. At some point in the exercise its onboard navigation sensor is expected to fault, and its reported altitude will drift off the true value.

1. **Confirm the fault:** Identify which subsystem is producing the bad altitude telemetry.
2. **Get an independent fix:** Do not trust the GEO node's own position. The GEO node is geostationary and held **over Singapore**. Use the **LEO Overwatch radar** to range it and work out its true altitude from the geometry.
3. **Recover:** Once you have an independent altitude, restore trustworthy navigation on the GEO node.

### Phase 5 - Orbit Determination

Your LEO Overwatch node's own navigation is healthy.

1. **Pull the state:** Use the LEO node GPS telemetry to recover its orbit.
2. **Report the elements:** Determine the semi-major axis, eccentricity, inclination, and altitude of the LEO Overwatch orbit.

---

## Operational Constraints

| Constraint | Detail |
| --- | --- |
| Targets | All targets are passive. You cannot command them, and they broadcast no telemetry to you. |
| RPO Software | Not available - no automated rendezvous or proximity guidance |
| Propulsion | No thrusters installed on either spacecraft |
| Attitude Control | Reaction wheels available - point your sensors with guidance commands |
| GEO Navigation | Expected to fault mid-exercise (supply-chain compromise). Treat GEO position telemetry as suspect until you reset it. |
| Classification Data | Photometry (CCD / optical brightness) and radar range only. No RF identification of targets. |

---

## Spacecraft Configuration

Each team operates the same two-node network: one **LEO Overwatch** craft and one **GEO** craft.

### Schematic

![CCD spacecraft schematic](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/ccd_objects/schematic.png)

### Platform Summary

| Item | LEO Overwatch | GEO Node |
| --- | --- | --- |
| Mass | 300 kg | 350 kg |
| Orbit | LEO, semi-major axis 9000 km, inclination 51.6 deg | Geostationary, held over Singapore |
| Power storage | Battery, 160 Wh | Battery, 200 Wh |
| Imaging | Optical Camera; CCD imager | Optical Camera; CCD imager |
| Ranging | Radar | Radar |
| Navigation | GPS Sensor | GPS Sensor (fault expected) |
| Comms | Receiver and transmitter | Receiver and transmitter |
| Propulsion | None | None |
| ADCS | Reaction wheels | Reaction wheels |

---

## Sensors

Both spacecraft carry the same sensor suite. Point the boresight with guidance commands before capturing.

### Charge Coupled Device (CCD)

Your primary tool for photometry: measuring how bright a target is and how its brightness changes over time. Use it to compare reflectivity across the Helios members and to build light curves of the tumbling rocket bodies.

| Specification | LEO Overwatch | GEO Node |
| --- | --- | --- |
| Resolution | 64 x 64 | 64 x 64 |
| Field of View | 5 deg | 2 deg |
| Exposure Time | 0.05 s | 0.3 s |
| Spectral Wavelength | 550 nm | 550 nm |

> The wider LEO field of view suits surveying the six-satellite constellation; the narrow GEO field of view and longer exposure suit faint, distant targets in the GEO belt.

### Radar

Active ranging. Use it to measure distance to a target and to watch how that distance changes, which is how you separate a station-keeping neighbour from an approaching object and how you range the GEO node from LEO.

| Specification | LEO Overwatch | GEO Node |
| --- | --- | --- |
| Field of View | 20 deg | 15 deg |
| Power | 5000 | 8000 |
| Gain | 40 | 42 |
| Detection Threshold | 10 | 9 |

### Other sensors

- **Optical Camera:** Visible-light imager for direct inspection of a target once it is in the boresight.
- **GPS Sensor:** Position and velocity for your own spacecraft. The GEO node's unit is the one flagged in the intelligence report.

---

## Debris Capture-Safety Reference

A servicing tug can only capture a rocket body if it is not spinning too fast. Use your measured roll rate (dominant spin rate, in degrees per second) with the thresholds below to classify each rocket body.

| Roll rate | Classification | Action |
| --- | --- | --- |
| 2.5 deg/s or less | **Safe for collection** | Capture may proceed |
| 2.5 to 4.0 deg/s | **Caution** | Despin required before capture |
| Greater than 4.0 deg/s | **Unsafe** | Do not attempt capture |

> Measure roll rate from the CCD light curve. The dominant brightness period in seconds relates to the spin rate: a shorter period means a faster roll. Convert period to rate before you read the table.

---

## Communications

### Ground stations

| Station | Role |
| --- | --- |
| Casablanca, Dubai, Singapore, Sydney, Miami, Salvador, Tokyo, Honolulu, Moscow | Distributed ground network for uplink and downlink |

The station set is spread in longitude to keep your spacecraft in contact as they move. Use the **Link Budget** panels in the operator terminal for predicted contact intervals and signal quality.

### Team Frequencies

Each team commands only its own two-node network. Your team is assigned a unique communications frequency at the start of the scenario, pre-configured and identical on the uplink and downlink. The Helios satellites, rocket bodies, and GEO-region objects are passive and are not controllable by anyone.

---

## Suggested Team Roles

Split responsibilities early. The Mission Lead should assign these roles at the start of the exercise:

- **Mission Lead:** Assigns roles, answers questions, monitors key information, and makes go/no-go calls.
- **Satellite Operator:** Manages telemetry, guidance pointing, and spacecraft health across both nodes.
- **Payload Operator:** Captures CCD and optical imagery and radar ranges, builds light curves, and reads reflectivity and roll rate.
- **Communications Specialist:** Monitors link budgets, GPS telemetry, and contact windows, and coordinates the GEO navigation reset.

---

## Before You Begin

1. Log in to the operator terminal with your team credentials.
2. Confirm both nodes report telemetry and the Link Budget is nominal.
3. Read the in-simulation Tasks to understand scored questions, then prioritise by team expertise.
4. Split roles, and agree who watches the constellation on the LEO node and who works the GEO belt.

---

## Learning focuses

### Photometric Classification

Compare reflectivity across identical-looking satellites with the CCD to pick out members whose surface brightness does not match the rest of the group.

### Light-Curve Analysis

Build brightness-versus-time curves for tumbling debris, measure the rotation period, convert it to a roll rate, and apply operational thresholds to make a capture decision.

### Radar Custody and Conjunction

Use radar range trends to tell a stable co-orbital neighbour from an approaching object and to estimate the timing of a closest approach.

### Independent Orbit Determination

Recover an orbit from GPS telemetry, and cross-check a spacecraft's altitude with an independent radar measurement when its own navigation cannot be trusted.
