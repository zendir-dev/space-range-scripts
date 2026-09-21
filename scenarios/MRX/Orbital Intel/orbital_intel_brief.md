**Scenario:** Orbital Intel  
**Epoch:** 2025-04-15 07:30:00 UTC  
**Duration:** Open-ended (instructor-controlled), 5x real time  
**Ground stations:** Madrid, Dubai, Singapore, Auckland, Easter Island, Salvador, Miami

---

## Overview

You are a commercial ISR crew tasked with maritime surveillance across three regions: the Red Sea, the South China Sea, and the northern coast of Venezuela. Eight blue teams share one Microsat in near-equatorial low Earth orbit. A separate Rogue team operates a co-orbital spacecraft that you do not control. That object is hidden from the default map view.

The session starts as collection and reporting: image the assigned areas, compare what you see against the tasking and AIS data in this brief, and answer the Tasks. It then adds spacecraft-operations pressure. A component will fail during the run, and communications quality will not stay clean. Your job is to keep collection going, tell a platform fault apart from external interference, and report what you found.

> Questions and scoring are delivered in the **Tasks** section. Use this brief for mission context, spacecraft configuration, and reference data. It is not an answer key.

---

## Mission Goals

At 5x speed you get more than one pass over each area of interest. If you miss a window, plan for the next orbit. Work the phases in parallel with spacecraft health.

### Phase 1 - Red Sea (Counter-Piracy)

**Task Order:** JCO-TO-001  **Priority:** HIGH  **AOI:** Southern and central Red Sea, Bab el-Mandeb to the Suez approaches

Conduct maritime ISR to support maritime situational awareness and give early warning of piracy or armed boarding against commercial shipping.

1. **Track the traffic:** Identify vessels in the strait and immediate approaches. Commercial traffic is shown as large green ships.
2. **Characterize movement:** Determine course and speed. Flag contacts that are stationary, loitering, or off the shipping lane.
3. **Assess damage:** Report imagery-derived damage indicators, including listing, fire or smoke, and vessels that remain stationary across a pass.
4. **Identify suspected bad actors:** Non-green contacts are also in the area. Note hull color, proximity to merchant traffic, and behavior that does not fit the commercial pattern.

> Dense traffic reduces contact discrimination. Priority is timely reporting, not full attribution.

### Phase 2 - South China Sea (Island Construction)

**Task Order:** JCO-TO-002  **Priority:** MEDIUM to HIGH  **AOI:** South China Sea, Paracel Island group

Detect infrastructure expansion and related support activity against the reference imagery in this brief.

1. **Compare to baseline:** Find what has changed relative to the reference photo.
2. **Fix the location:** Report the new feature in latitude and longitude.
3. **Classify nearby vessels:** Identify craft close to the site and assess whether they look like construction or support traffic. Tighten the camera field of view for this work.

### Phase 3 - Coast of Venezuela (AIS Verification)

**Task Order:** JCO-TO-003  **Priority:** MEDIUM  **AOI:** Northern coast of Venezuela

Verify vessel identity and track against the AIS table in this brief.

1. **Catalog the contacts:** Identify vessels in the area from imagery, including hull color.
2. **Correlate to AIS:** Match what you see against the provided broadcasts (name, position, heading, speed).
3. **Report discrepancies:** Flag position offsets, heading mismatches, identity errors, and any visible contact with no matching AIS row.

> Treat every AIS row as a claim. Check position, heading, and presence separately.

### Phase 4 - Rogue Spacecraft

An SDA advisory (below) flags a resident space object conducting proximity operations near coalition spacecraft. Intent is unconfirmed at issue time.

1. **Watch the link:** Monitor downlink signal-to-noise and which ground station you are working through when quality changes.
2. **Characterize the source:** Use the EM sensor to inspect radio-frequency emissions. Reorient if a reading is weak or ambiguous.
3. **Image the object:** The co-orbital spacecraft is hidden on the default map. If you acquire it on camera, look for markings that identify it.
4. **Restore service:** Use the communications controls available on your console, then confirm from telemetry that the link recovered.

### Phase 5 - Orbital Operations

1. **Baseline the platform:** Record power, storage, attitude, and link health while conditions are still nominal.
2. **Diagnose faults:** A component will fail during operations. Identify it from telemetry and apply the recovery action available to you.
3. **Recover your orbit:** Use GPS telemetry to determine semi-major axis, eccentricity, and inclination.

---

## Operational Constraints

| Constraint | Detail |
| --- | --- |
| Propulsion | No thrusters installed |
| Attitude control | Three-axis reaction wheels |
| RPO software | Not available on your spacecraft |
| Shared asset | All blue teams command the same Microsat |
| Rogue asset | Not under your control, hidden on the default map |
| Simulation speed | 5x real time |
| Session end | Open-ended, instructor-controlled |

---

## Spacecraft Configuration

Every blue team commands the same **Microsat**, a 100 kg Earth-observation vehicle.

### Schematic

![Microsat schematic](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/orbital_intel/schematic.png)

### Platform Summary

| Item | Configuration |
| --- | --- |
| Mass | 100 kg |
| Orbit | Near-equatorial low Earth orbit around Earth |
| Power storage | Battery, 80 Ah nominal capacity, 50% charge at session start |
| Payload | Optical camera |
| Sensors | GPS sensor, EM sensor |
| Comms | Receiver and transmitter |
| Storage | Onboard data storage |
| Propulsion | No thrusters |
| ADCS | Reaction wheels |

### Power System

Power is generated by two body-mounted solar panels (Solar Panel +X and Solar Panel -X) and stored in a single battery. Both panels start enabled. Watch solar and battery telemetry through the session.

| Component | Start State |
| --- | --- |
| Solar Panel +X / -X | Enabled |
| Battery | 80 Ah, 50% charge |

---

## Cameras

The Microsat carries one optical camera for all three maritime task orders and for imaging the co-orbital object.

### Camera

**Purpose:** Primary collection payload. Widen the field of view to find an area of interest, then narrow it to identify and count contacts.

| Specification | Value |
| --- | --- |
| Resolution | 1024 x 1024 |
| Mass | 5 kg |

> For South China Sea construction traffic, a narrow field of view is more useful than a wide survey pass.

### Other sensors

- **GPS Sensor:** Position and velocity for your own spacecraft, and the source for orbit determination.
- **EM Sensor:** Detects radio-frequency emissions. Directional: point it at a suspected source before you trust the reading.
- **Storage:** Holds captured imagery until it can be downlinked.

---

## Communications

### Ground Stations

| Station | Notes |
| --- | --- |
| Madrid | European pass |
| Dubai | Gulf and Red Sea arc |
| Singapore | Indo-Pacific pass, including the South China Sea tasking |
| Auckland | South Pacific pass |
| Easter Island | Pacific gap filler |
| Salvador | South Atlantic pass |
| Miami | Western hemisphere pass, nearest the Venezuela tasking |

Use the **Link Budget** panel for contact intervals, signal-to-noise ratio, and pass geometry. Track which station is active when interference appears. The configured minimum elevation is 0 degrees.

### Team Frequencies

Each blue team is assigned a unique frequency and encryption key at session start, pre-configured in the operator terminal. Your frequency is the same on the uplink and the downlink. Do not assume an effect you see on your console is visible to every other team.

---

## Maritime Observation

Three areas of interest hold the surface traffic for this exercise.

| Area of Interest | Phase | Collection Focus |
| --- | --- | --- |
| Bab el-Mandeb Strait, Red Sea | 1 | Large green commercial ships, damaged or stationary contacts, non-green vessels |
| Paracel Island group, South China Sea | 2 | New construction relative to the reference photo, nearby support craft |
| Northern coast of Venezuela | 3 | Named vessels to correlate against the AIS table |

Plan passes using the **Map**, point with **Guidance**, and capture during the collection window. Vessels are spread across each area and some are underway. Hull color is a reliable discriminator, so record it whenever you image a contact.

### South China Sea Reference Imagery

Compare live camera frames against this baseline for Phase 2.

![South China Sea reference imagery](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/orbital_intel/south_china_sea.png)

Use the map and this photo together:

- **Plan camera pointing:** Anticipate when the area enters the boresight and tighten the field of view before you try to count craft.
- **Identify change:** Confirm you are looking at the same feature as the reference photo before reporting coordinates.
- **Fix latitude and longitude:** Once a distinctive feature is in frame, estimate its position and check it on later passes.

### AIS Beacon Data (Phase 3)

The following AIS broadcasts were collected for the northern Venezuela area. Correlate these against what your camera shows.

| Date | Time | Latitude | Longitude | Name | Speed | Heading |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-04-14 | 20:12 | 13.390 deg | -60.362 deg | HARBOR SENTINEL | 10.6 kn | 290 deg |
| 2026-04-14 | 13:14 | 12.793 deg | -65.922 deg | GOLDEN BALLAST | 7.5 kn | 45 deg |
| 2026-04-14 | 13:31 | 11.932 deg | -63.547 deg | IRON HORIZON | 8.6 kn | 85 deg |
| 2026-04-14 | 17:47 | 14.471 deg | -62.871 deg | OCEAN TRIBUTE | 12.8 kn | 120 deg |
| 2026-04-14 | 18:37 | 15.517 deg | -57.367 deg | TITAN MANIFEST | 11.4 kn | 219 deg |

> This table is the reported picture, not ground truth. Check it against imagery.

---

## Other Participants

**SDA Advisory SDA-ADV-LEO-021** (UNCLASS, training only). A resident space object has been detected conducting rendezvous and proximity operations in low Earth orbit near coalition spacecraft. Relative motion is consistent with station-keeping or controlled drift across multiple passes. No debris or collision indicators were reported at issue time. Intent is undetermined. Confidence: medium.

Recommended actions:

- Increase monitoring of relative motion and predicted approach windows.
- Monitor telemetry, payload, and link performance for anomalies correlated with proximity events.
- Report anomalies with timestamps and supporting evidence.

You cannot command this object. It is not shown on the default map. Characterize it with your own camera and EM sensor.

---

## Suggested Team Roles

Split responsibilities early. The Mission Lead should assign these roles at the start of the exercise:

- **Mission Lead:** Assigns roles, prioritizes the three task orders, monitors key information, answers questions, and makes go/no-go calls.
- **Satellite Operator:** Manages telemetry, guidance pointing, subsystem health, and fault response.
- **Payload Operator:** Captures camera imagery and EM sensor data for maritime collection and rogue characterization.
- **Communications Specialist:** Monitors link budgets, ground-station passes, GPS telemetry, and interference symptoms.

> Log every frequency change, reset, and guidance command, along with what happened next. Stabilize the link or the failed subsystem first, then work out the root cause for your report.

---

## Before You Begin

1. Log in to the operator terminal with your team credentials.
2. Confirm the Microsat appears on the **Map** and that telemetry and the Link Budget are updating.
3. Read the Tasks and this brief. Agree which area of interest you collect first.
4. Take a baseline reading of power, storage, attitude, and link health while conditions are nominal.
5. Split roles. You are not expected to answer every question. Prioritize by team expertise and log evidence as you go.

---

## Learning focuses

### Imagery Interpretation

Use camera pointing and field of view to identify commercial, suspicious, damaged, and construction-related vessels, and to detect change against reference imagery.

### Multi-Source Fusion

Cross-check visible vessel position, heading, color, and behavior against the AIS table in this brief to identify false, inconsistent, or missing broadcasts.

### Subsystem Diagnosis

Diagnose a component fault from telemetry and select the appropriate recovery action, without confusing it with link degradation.

### Contested Communications

Recognize interference from link-budget and ground-station symptoms, characterize the source with the EM sensor, and apply a mitigation that restores service.
