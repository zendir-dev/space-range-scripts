**Scenario:** Module 9  
**Epoch:** 2025-11-01 17:00:00 UTC  
**Duration:** 80 minutes simulated (about 40 minutes real time at 2x speed)  
**Ground Segment:** Tokyo, Anchorage, Houston, Lima, Santiago

---

## Overview

You are the duty crew for a single **Microsat** in low Earth orbit, running imagery tasking while holding watch on spacecraft health. The theme of this session is **detect and confirm**: an alert is not an incident. Something firing an alarm on your console only becomes an incident once you have looked at the evidence and can say what caused it.

Three areas will raise alerts during the session: **navigation (GPS)**, **telemetry integrity**, and **attitude control**. Each one needs the same discipline. Notice it, characterise it inside sixty seconds, collect the telemetry or imagery that proves what you saw, then classify the cause. Confirmed cyber-physical activity gets escalated to command leadership as a detection report. A fault that your evidence says is natural gets logged and handled as maintenance, not escalated as an attack. Getting that split right is the point of the exercise.

Every team flies its own copy of the same spacecraft on its own radio link, so what one crew sees is not automatically what another crew sees.

> Questions and scoring are delivered in the **Tasks** section of the operator terminal. Use this brief for mission context, spacecraft configuration, and the triage procedure. It is not an answer key.

---

## Mission Goals

1. **Establish operations:** Log in, confirm your spacecraft on the **Map**, and take a baseline of navigation, power, and link health while conditions are nominal. You cannot call something anomalous without a baseline.
2. **Hold navigation integrity:** Treat the GPS solution as evidence, not truth. Check the reported fix against your predicted ground track and the map before you act on it or report it.
3. **Watch telemetry integrity:** Inspect downlinked packet contents, not just plotted values. Content that does not belong in a packet is a finding in its own right.
4. **Monitor attitude control:** Read per-wheel reaction wheel telemetry through the session. If the platform stops responding to a pointing command as expected, work out which axis is involved and when the behaviour started.
5. **Task the Caribbean region:** Image the black-hulled vessel group in the Caribbean east of Florida and resolve the group from your imagery.
6. **Task the Peru region:** Image the orange-hulled vessel group off the west coast of Peru.
7. **Triage every alert within sixty seconds:** For each alert, state what changed, which subsystem it touches, and what evidence you hold. Sixty seconds is the working limit before you move to a call.
8. **Report your findings:** Escalate confirmed cyber incidents to command leadership in detection-report format. Log faults that your evidence assesses as natural separately, outside the cyber report.

> Alerts overlap with tasking. Payload work does not stop because an alarm appeared, and an alarm does not get ignored because a pass is open. Assign the watch and the tasking to different people.

---

## Alert Triage and Reporting

Run the same loop on every alert, regardless of which subsystem raised it.

1. **Detect.** Note the alert and the simulation time it appeared. Time of onset is evidence.
2. **Characterise (60 seconds).** Identify the affected subsystem and what the telemetry actually shows. Compare against your baseline.
3. **Collect evidence.** Pull the specific telemetry, packet content, or imagery that supports your description. A statement without a source is not a finding.
4. **Classify.** Decide on the evidence whether the behaviour is consistent with cyber-physical interference or with hardware behaving badly on its own. Do not assume every alert is an attack, and do not assume any alert is benign because it is inconvenient.
5. **Log and escalate.** Record every alert. Escalate only what you have confirmed as a cyber incident.

> A detection report should say what was observed, when it started, which subsystem it affected, the evidence behind the call, your assessed cause, and how confident you are. Keep non-cyber faults in your maintenance log with the same rigour, then keep them out of the cyber report.

> Resetting the flight computer is available from your console and can clear some conditions. If you use it, log the time you did so, because a reset changes what later telemetry can tell you.

---

## Operational Constraints

| Constraint | Detail |
| --- | --- |
| Propulsion | No thrusters installed, no orbit changes available |
| Attitude control | Reaction wheels only, pointing is commanded through guidance |
| RPO software | Not available, no automated rendezvous or proximity guidance |
| Navigation | GPS is the only onboard navigation source, there is no magnetometer to cross-check against |
| Ground contact | Minimum elevation angle is 10 degrees, so passes are finite |
| Imaging conditions | Dense cloud cover over the operating areas, low ambient light |

---

## Spacecraft Configuration

Each team commands an identical 100 kg **Microsat** in a low Earth orbit inclined at 70 degrees, with a near-circular orbit of about 8600 km semi-major axis. The ground track crosses both tasking regions and the five ground stations during the session.

### Schematic

![Microsat schematic](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/module_9/schematic.png)

### Platform Summary

| Item | Configuration |
| --- | --- |
| Mass | 100 kg |
| Orbit | Earth, low Earth orbit, about 8600 km semi-major axis, 70 degrees inclination |
| Power generation | Two body-mounted solar panels (Solar Panel +X, Solar Panel -X) |
| Power storage | Battery, 80 Ah nominal capacity, starting at 50% charge |
| Payload | Optical camera, 1024 x 1024 |
| Navigation | GPS sensor |
| Comms | Receiver (3 dB antenna gain) and transmitter |
| Data | Onboard storage and flight computer |
| Propulsion | No thrusters |
| ADCS | Reaction wheels |

### Power

Both solar panels feed the single battery, which starts the session half charged. Image capture and downlink each draw from the battery, so a long tasking sequence across eclipse will bite. Keep an eye on the charge fraction while you are busy chasing alerts, and treat an unexplained power reading as its own alert rather than background noise.

---

## Payload and Sensors

| Component | Purpose |
| --- | --- |
| **Camera** | 1024 x 1024 optical imager for vessel tasking in the Caribbean and off Peru. |
| **GPS Sensor** | Position source for navigation telemetry, and the subsystem you will need to validate rather than trust. |
| **Reaction Wheels** | Three-axis pointing. Per-wheel telemetry is what tells you whether the platform is doing what you commanded. |
| **Receiver and Transmitter** | Uplink and downlink on your team frequency. |
| **Storage and Computer** | Onboard image storage and command handling, including the reset path. |

> With no magnetometer and no second navigation source, geometry is your cross-check. Your predicted ground track, your ground station visibility, and what your camera actually sees are all independent of the GPS solution.

---

## Communications

### Ground Stations

| Station | Notes |
| --- | --- |
| Tokyo | Western Pacific pass |
| Anchorage | High-latitude pass, suits the 70 degree inclination |
| Houston | North American pass, near the Caribbean tasking region |
| Lima | South American pass, near the Peru tasking region |
| Santiago | Southern South American pass |

The station set is spread in latitude and longitude, so contact comes in discrete passes rather than continuously. Use the **Link Budget** panel for contact intervals, signal-to-noise ratio, and pass geometry.

### Operational Expectations

- Plan tasking and downlink around passes, not around wall-clock convenience.
- Note which station you are working through when an alert appears, and record it. Station and pass context is part of your evidence.
- Expect to work alerts and tasking inside the same pass. Decide in advance who owns which.

### Team Frequencies

Nine teams are configured for this session: Blue, Green, Yellow, Orange, Pink, White, Purple, Cyan, and Red. Each team is assigned a unique frequency and key at session start, pre-configured on the operator terminal and identical on the uplink and downlink. Because each crew operates its own spacecraft, compare notes across teams carefully before assuming an effect is shared.

---

## Vessel Tasking

Two surface regions hold vessels for imagery collection.

| Region | Target description |
| --- | --- |
| Caribbean, east of Florida | A group of black-hulled vessels holding position |
| West coast of Peru | A group of orange-hulled vessels holding position |

The vessels are not underway, so a single clean capture of the right area can resolve a group. Plan the pass on the **Map**, point with **Guidance**, then capture with the **Camera**. Cloud cover is dense in this scenario, so budget for more than one attempt per region and check each image before you count on it.

> Pointing and imagery are also diagnostic data. If a capture does not frame where you commanded it to, that is worth logging along with the attitude telemetry from the same moment.

---

## Suggested Team Roles

Split responsibilities early. The Mission Lead should assign these roles at the start of the exercise:

- **Mission Lead:** Assigns roles, keeps the alert log, runs the sixty-second triage clock, decides what is escalated as a cyber incident and what is logged as a natural fault, and writes the detection report.
- **Satellite Operator:** Manages telemetry, guidance pointing, power, and attitude health, and reports per-wheel behaviour to the Mission Lead.
- **Payload Operator:** Plans and executes camera tasking over both vessel regions and reports what the imagery supports.
- **Communications Specialist:** Monitors link budgets, ground station passes, GPS telemetry, and packet content, and flags anything in the data that does not belong.

> **Working method:** Log every alert with its onset time, the evidence, and the call you made. Log every action you take, including resets and frequency changes, and what happened after. When two operators see different symptoms, compare notes before deciding whether you are looking at one problem or two.

---

## Before You Begin

1. Log in to the operator terminal with your team credentials and read the **Tasks** section.
2. Confirm your spacecraft appears on the **Map** and that telemetry and the Link Budget are updating.
3. Take a baseline of navigation, power, attitude, and link health while conditions are nominal, and write it down.
4. Split roles, agree who runs the alert log and the sixty-second clock, and agree who keeps working the payload while an alert is live.

---

## Learning focuses

### Alert Triage Under Time Pressure

Work an unexplained indication into a described, evidenced finding inside sixty seconds, without stopping the rest of the mission.

### Cause Classification

Separate interference with a subsystem from a subsystem failing on its own, using telemetry evidence rather than assumption about which is more likely.

### Navigation and Telemetry Integrity

Validate a position solution and packet contents against independent references rather than taking a subsystem at its word.

### Attitude Control Diagnosis

Use per-wheel reaction wheel telemetry and pointing results together to localise an attitude control problem to an axis and a time.

### Incident Reporting

Escalate confirmed cyber incidents in detection-report format with onset time, evidence, and confidence, and keep non-cyber faults in a separate maintenance log.
