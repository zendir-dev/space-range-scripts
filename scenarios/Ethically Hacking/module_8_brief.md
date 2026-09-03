**Scenario:** FSSCP Module 8  
**Epoch:** 2025-10-15 05:00:00 UTC  
**Duration:** 160 minutes simulated (about 40 minutes real time at 4x speed)  
**Ground Segment:** Ankara, Auckland, Bangkok, Santiago

---

## Overview

You are an Earth observation crew running a single **Microsat** imaging spacecraft in a mid-inclination Earth orbit. Two areas of interest are on tasking this session: surface vessel traffic in the **Aegean Sea**, and surface vessel traffic in the **Tasman Sea** between Australia and New Zealand. Four ground stations spread around the globe give you regular passes, with natural gaps between them.

The work is split three ways: satellite operations reporting on link and platform health, payload operations reporting on what was collected, and the Mission Lead merging both into a single mission SITREP for command.

> Questions and scoring are delivered in the **Tasks** section of the operator terminal. Use this brief for mission context, spacecraft configuration, and the operating areas. It is not an answer key.

---

## Mission Goals

### Phase 1 - Satellite Operations

1. **Establish operations:** Confirm your spacecraft on the **Map**, and check that telemetry is updating before you command anything.
2. **Baseline the link:** Work out which telemetry on the operator terminal actually evidences link quality for a pass, and record that evidence while conditions are nominal. A SITREP claim is only as good as the source behind it.
3. **Track command health:** Watch the automatic pings and command acknowledgements in the **Messages** and **Telemetry** views, and note the timing you observe.
4. **Set a status call:** Decide what your platform status is for the pass and be ready to justify which signatures would move it up or down a level.
5. **Separate cyber from maintenance:** Some comms observations point at interference or intrusion, others are routine health. Sort what you see into those two buckets before you report.

### Phase 2 - Payload Operations

1. **Plan the passes:** Use the **Map** to find when your ground track crosses the Aegean and the Tasman operating areas.
2. **Collect imagery:** Point with **Guidance** and capture with the **Camera** over each area. Cloud is modelled in this environment and can hide surface targets, so plan for more than one look.
3. **Gate your products:** Before you call a capture good, confirm it against the tasking you were given. Decide what your quality gate is and apply it consistently.
4. **Report the collection:** Record what you imaged in each sea for the payload SITREP.
5. **Check the payload for tampering:** Compare what your captures claim about themselves against what you actually commanded, and flag anything that suggests interference rather than wear.

### Phase 3 - Mission Lead

1. **Merge the reports:** Take the satellite operations and payload SITREPs and combine them into one mission SITREP.
2. **Cut to the decision level:** Command reads at the decision level. Agree as a team what earns a place in the report and what belongs in a supporting annex.
3. **Write the bottom line:** Fix the single most important line of the report first, then make sure the rest supports it.
4. **Submit:** Answer the scored questions in the **Tasks** section before the session ends.

> Agree your SITREP format early. Chasing the format at the end of the session costs you passes.

---

## Operational Constraints

| Constraint | Detail |
| --- | --- |
| Propulsion | No thrusters installed, the orbit is fixed for the session |
| Attitude control | Reaction wheels only |
| RPO software | Not available, no automated rendezvous or proximity guidance |
| Ground contact | Minimum elevation of 10 degrees, so passes are finite and gaps between them are normal |
| Collection | Optical camera only, no radar or ranging payload |

---

## Spacecraft Configuration

You command a 100 kg **Microsat**, an imaging platform in a circular mid-inclination Earth orbit.

### Schematic

![Microsat schematic](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/module_8/schematic.png)

### Platform Summary

| Item | Configuration |
| --- | --- |
| Mass | 100 kg |
| Orbit | Earth, circular, 9500 km semi-major axis, 63 degree inclination |
| Power generation | Two body-mounted solar panels (Solar Panel +X and Solar Panel -X) |
| Power storage | Battery, 80 Ah nominal capacity, fully charged at session start |
| Payload | Optical camera, 1024 x 1024 |
| Sensors | GPS sensor |
| Comms | Receiver and transmitter |
| Data | Onboard storage |
| Propulsion | None |
| ADCS | Reaction wheels |

### Power Network

Both solar panels feed the single battery, which supplies the bus. Each panel is 0.3 square metres at 40 percent efficiency, so generation follows sun angle through the orbit. The battery starts at full charge. Imaging and downlink both draw on it, so keep an eye on charge fraction across a busy pass.

---

## Payload and Sensors

| Component | Purpose |
| --- | --- |
| **Camera** | 1024 x 1024 optical imager. Your only collection sensor for both operating areas. |
| **GPS Sensor** | Position and velocity for your own spacecraft, and the reference for where a capture was actually taken. |
| **Receiver / Transmitter** | Spacecraft uplink and downlink. The receiver has an antenna gain of 3. |
| **Storage** | Onboard storage holding captured products until they are downlinked. |

> Capture metadata matters as much as the picture. Log what you commanded, when you commanded it, and what came back, so you can compare the two later.

---

## Communications

### Ground Stations

| Station | Coverage |
| --- | --- |
| Ankara | Covers the Aegean side of the tasking |
| Bangkok | South East Asia pass |
| Auckland | Covers the Tasman side of the tasking |
| Santiago | South American pass, widest separation from the others |

The four stations are spread in longitude, but they do not give continuous coverage. Expect contact windows separated by gaps where you have no link, and plan uplinks and downlinks around them. Use the **Link Budget** panel for contact intervals and signal quality on the current pass.

---

## Collection Areas

Two separated areas of interest hold surface vessel traffic, roughly half a world apart. Both sit under your ground track at different points in the orbit, so they need separate pass planning.

![Operating areas reference map](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/module_8/operating_areas.png)

| Area | Location | Targets |
| --- | --- | --- |
| **Aegean Sea** | About 37 degrees north, 25 degrees east | Red-hulled vessels, holding position |
| **Tasman Sea** | About 38 to 39.5 degrees south, 161.5 to 164 degrees east, between Australia and New Zealand | Orange-hulled vessels, holding position |

The vessels are stationary and each sits on its own heading, so a clean capture over the area is repeatable. Cloud is the main obstacle. Use the map to time your look, point the camera with **Guidance**, and check the returned image covers the water you meant to image before you count on it.

---

## Suggested Team Roles

Split responsibilities early. The Mission Lead should assign these roles at the start of the exercise:

- **Mission Lead:** Assigns roles, monitors key information, merges the SatOps and payload inputs into the mission SITREP, and makes go/no-go calls.
- **Satellite Operator:** Manages telemetry, guidance pointing, power, and platform health, and owns the platform status call. Also tracks link budget, ground-station passes, GPS, and command acknowledgements, and flags anything on the link that looks non-nominal.
- **Payload Operator:** Plans and executes camera captures over both seas, checks product quality and metadata, and owns the collection report.

---

## Before You Begin

1. Confirm your spacecraft appears on the **Map** and that telemetry and the Link Budget are updating.
2. Open **Tasks** and read the questions before you start commanding, then prioritise across your roles.
3. Agree who writes each SITREP and what format they will use, and start logging observations from the first pass.

---

## Learning Focuses

### Situation Reporting

Build a SITREP that ties every claim to a named source on the operator terminal, and keep it short enough that command can act on it.

### Telemetry Interpretation

Read platform and link telemetry across a pass, recognise what nominal looks like, and justify a status call from the evidence you recorded.

### Cyber Versus Maintenance

Tell observations that point at interference or intrusion apart from those that are routine hardware health, in both the comms and payload data.

### Earth Observation Tasking

Plan a pass over a specific maritime area, capture usable imagery through cloud, and verify the product matches the tasking before you report it.
