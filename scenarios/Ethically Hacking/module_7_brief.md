**Scenario:** FSSCP Module 7  
**Epoch:** 2025-10-15 00:00:00 UTC  
**Duration:** 160 minutes simulated (about 40 minutes real time at 4x speed)  
**Ground Segment:** Cape Town, Honolulu, Santiago, Singapore

---

## Overview

You are the crew of an Earth observation microsatellite. Your tasking covers two widely separated maritime areas: the **Strait of Malacca** and the waters around **Hawaii**. You have one spacecraft, one camera, and a ground network of four stations spread around the globe.

The orbit is circular at a 9000 km semi-major axis and inclined 26 deg, so your ground track stays inside a band roughly between 26 N and 26 S. Both collection areas sit inside that band. Contact with the ground is not continuous: you work inside station passes and plan around the gaps between them. The session runs a little over one orbit, so there are not many chances to get each area right.

> Questions and scoring are delivered in the **Tasks** section of the operator terminal. Use this brief for mission context, spacecraft configuration, and collection geography. It is not an answer key.

---

## Mission Goals

1. **Characterize each pass.** Use the available spacecraft and communications data to record contact conditions throughout each ground-station pass.
2. **Build a pass plan.** Use the Map to work out when your ground track crosses the Strait of Malacca and the Hawaiian area, and when each ground station comes into view. Decide what has to happen inside each contact window before the window opens.
3. **Collect the Strait of Malacca.** Point the camera and capture imagery of the Malacca operating area. Yellow-hulled vessels are present there.
4. **Collect the Hawaiian area.** Do the same over the waters around Hawaii, where green-hulled vessels are present.
5. **Downlink and check your products.** Get imagery on the ground and review each product before you treat it as usable. Decide as a team what would make you hold a product as suspect.
6. **Agree how you run a pass.** Settle who calls acquisition, who owns the link, who owns the payload, and what conditions stop routine commanding. The Tasks section will ask you to defend those calls, so make them deliberately rather than in the moment.

> Contact windows are finite. Build the pass timeline before the window opens and track your progress against it.

---

## Operational Constraints

| Constraint | Detail |
| --- | --- |
| Propulsion | No thrusters installed - the orbit you start with is the orbit you keep |
| RPO Software | Not available |
| Attitude Control | Reaction wheels only - all pointing is done by slewing the spacecraft |
| Payload Pointing | The camera is body-fixed. It shares a mounting face and boresight with the receiver and transmitter, so a pointing decision affects imaging and comms together |
| Ground Contact | A station must be at least 10 deg above the horizon. There is no additional range limit, but there are natural gaps between passes |
| Power | Two solar panels and one battery, no other source. The spacecraft protects itself at a 0.1 battery charge fraction |
| Weather | A cloud layer is modelled over the Earth, so a pass can come back obscured |

---

## Spacecraft Configuration

You operate a **Microsat** imaging spacecraft.

### Schematic

![Microsat schematic](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/module_7/schematic.png)

### Platform Summary

| Item | Configuration |
| --- | --- |
| Mass | 100 kg |
| Orbit | Earth, circular, 9000 km semi-major axis (about 2600 km altitude), 26 deg inclination |
| Orbital period | Approximately 142 minutes |
| Power storage | Single battery, 80 nominal capacity, fully charged at session start |
| Power generation | Two body-mounted solar panels, 0.3 m2 each at 40 percent efficiency |
| Payload | Optical camera, 1024 x 1024 |
| Navigation | GPS sensor |
| Comms | Receiver (3 dB antenna gain) and transmitter |
| Data | Onboard storage |
| Propulsion | None |
| ADCS | Reaction wheels |

---

## Camera

A single optical camera is mounted on the spacecraft body. There is no independent gimbal, so you aim it with guidance commands and hold the attitude while you capture.

| Specification | Value |
| --- | --- |
| Resolution | 1024 x 1024 |
| Mounting | Body-fixed, co-located and co-aligned with the receiver and transmitter |
| Mass | 5 kg |

> The camera and both radios look the same way. Plan the slew that puts a target in the boresight and the slew that keeps you talking to a station as one problem, not two.

> Imagery only works on a lit target, and the cloud layer can hide the surface. Check illumination and cloud on the Map before you commit a pass to a collection.

### Other sensors

- **GPS Sensor:** Position, velocity, latitude, longitude, and altitude for your own spacecraft. Use it to confirm where you are against your pass plan.

---

## Power Network

Both solar panels feed the single battery, which supplies the rest of the spacecraft. The battery starts full, and capture and downlink both draw on it, with downlink the more expensive of the two. Watch the charge fraction across eclipse and across a busy pass.

### Component starting states

| Component | Start State |
| --- | --- |
| Solar Panel +X | Enabled, 0.3 m2, 40 percent efficiency |
| Solar Panel -X | Enabled, 0.3 m2, 40 percent efficiency |
| Battery | Enabled, 80 nominal capacity, 100 percent charge fraction |
| Camera | Enabled |
| Receiver / Transmitter | Enabled |
| Reaction Wheels | Enabled |
| Storage | Enabled |

---

## Communications

### Ground stations

| Station | Note |
| --- | --- |
| **Cape Town** | Southern Africa, covers the Atlantic and western Indian Ocean legs |
| **Singapore** | Sits alongside the Strait of Malacca collection area |
| **Honolulu** | Sits alongside the Hawaii collection area |
| **Santiago** | Covers the South American and eastern Pacific legs |

All four stations need the spacecraft at least 10 deg above their local horizon. Use the **Link Budget** panels in the operator terminal for predicted contact intervals and signal quality.

### Expected Contact Profile

| Period | Expectation |
| --- | --- |
| **At acquisition** | A station rises above the elevation mask and the link conditions begin to change with the geometry. |
| **During a pass** | Commanding, capture, and downlink all happen here. The window is short compared to the orbit. |
| **Between passes** | Expect a contact gap. With four stations and a 26 deg inclination there are stretches of the orbit where no station is in view, so anything not finished in the window waits for the next one. |

Contact times are not scripted in this scenario. They fall out of your orbit and the station geometry, so derive them from the Map and Link Budget rather than assuming a fixed schedule.

---

## Collection Areas

Two maritime areas are tasked. Both contain surface vessels holding position, each on its own fixed heading, so a clean pass over the area gives you a stable picture to work from.

| Area | Location | Vessels |
| --- | --- | --- |
| **Strait of Malacca** | About 1.8 to 2.2 N, 101.7 to 102.4 E | Yellow-hulled surface vessels, stationary |
| **Hawaii** | About 20.8 to 21.6 N, 156.8 to 158.1 W | Green-hulled surface vessels, stationary |

![Collection area reference map](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/module_7/collection_map.png)

Use the map alongside live imagery:

- **Plan the pass.** Work out when the ground track brings each area into reach, and slew early so the camera is settled before the area is under you.
- **Frame the whole area.** The vessels are spread across the area rather than sitting on one point. Make sure your imagery covers the full extent before you call a collection complete.
- **Confirm the geography.** Cross-check what the camera sees against the map and your GPS position so you know which area a product actually covers.
- **Keep the products.** Capture what you need on the pass and review it after downlink. The next opportunity over the same area is most of an orbit away.

---

## Suggested Team Roles

Split responsibilities early. The Mission Lead should assign these roles at the start of the exercise.

- **Mission Lead:** Assigns roles, runs the pass plan, monitors key information, decides what the team does with the time available in each window, and makes go/no-go calls.
- **Satellite Operations:** Owns the link and the spacecraft during a contact window - telemetry, guidance pointing, power state, and spacecraft health.
- **Payload Operations:** Owns the camera - captures imagery of the tasked areas, manages onboard storage and downlink, and reviews products once they are on the ground.
- **Communications Specialist:** Tracks link budget, GPS position, station visibility, and the timing of the gaps between passes.

---

## Before You Begin

1. Confirm your spacecraft appears on the **Map**, telemetry is updating, and the Link Budget is nominal.
2. Open **Tasks** and read the scored questions before you start commanding, so you know what evidence you need to collect.
3. Split roles and agree who calls the start and end of each pass.

---

## Learning Focuses

### Pass Planning Around Contact Gaps

Predict when a ground station is in view and when your ground track reaches a target, then fit the work into the window instead of reacting to it.

### Earth Observation Tasking

Point a body-fixed camera at a surface area from orbit, allow for lighting and cloud, and capture imagery good enough to answer a question about what is on the water.

### Product Integrity

Treat a downlinked image as evidence rather than a finished answer, and set your own criteria for when a product is good enough to deliver and when it should be held for review.

### Crew Coordination

Run a contact window as a team with clear ownership of the link, the payload, and the decisions, including what conditions should stop routine commanding.
