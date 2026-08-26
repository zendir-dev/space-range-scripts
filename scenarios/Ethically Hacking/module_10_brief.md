**Scenario:** Module 10 - Respond and Recover  
**Epoch:** 2025-11-01 17:00:00 UTC  
**Duration:** 80 minutes simulated (about 40 minutes real time at 2x speed)  
**Ground stations:** Tokyo, Anchorage, Houston, Lima, Santiago

---

## Overview

You are the duty crew for a single 100 kg Microsat carrying an optical imaging payload. The triage phase is over. The activity you worked in the previous module is now confirmed adversary activity, and this session is about acting on it: declare the incident, contain it, run the recovery playbook, protect the integrity of your payload products, and report progress on a fixed cadence.

A separate problem runs alongside the incident. A persistent attitude-control fault is present from session start and does not clear on its own. You must diagnose it from telemetry and recover it yourselves, while keeping the cyber response moving. Deciding what belongs inside the incident and what is an unrelated fault is part of the exercise.

Nine teams run the same Microsat design. Each team is assigned its own frequency and encryption key, pre-configured on the operator terminal at login.

> Questions and scoring are delivered in the **Tasks** section of the operator terminal. Use this brief for mission context, spacecraft configuration, and the response framework. It is not an answer key.

---

## Mission Goals

### Phase 1 - Declare and Scope

1. **Declare the incident:** Confirmed adversary activity requires a formal incident declaration. Make the call early and record the time you made it.
2. **Set the scope:** Agree as a crew which data paths and interfaces sit inside the declaration and which do not. Write the scope down before you start containment, and be ready to defend each inclusion with evidence from telemetry.
3. **Separate fault from attack:** Not every anomaly you see is adversary activity. Keep natural hardware faults on their own track so they do not distort the incident scope.

### Phase 2 - Contain and Recover

1. **Contain to scope:** Apply containment only to what you declared in scope. Blanket action across the whole spacecraft costs you capability you still need.
2. **Run the playbook:** Work the safe-mode and rollback steps in order rather than improvising. Confirm from live telemetry that each step had the effect you expected before moving on.
3. **Recover the attitude fault:** The attitude-control fault persists until you act on it. Identify the affected axis from spacecraft telemetry, then recover it so pointing is usable for tasking.

### Phase 3 - Payload Integrity

1. **Hold suspect products:** Put a hold on any captured product whose supporting data cannot be trusted. Do not release anything while the hold is open.
2. **Re-baseline the payload:** Re-establish the payload configuration against a known-good reference, then verify current state against it.
3. **Gate the release:** Agree the criteria that must be satisfied before the hold is lifted, and lift it only when every one of them is met and evidenced.

### Phase 4 - Report

1. **Issue Recovery SITREPs:** Report every 15 simulation minutes, which is roughly every 7 to 8 minutes of real time at this session speed. Keep the format identical each time so changes stand out.
2. **Keep an evidence log:** Record every action you take, the time you took it, and what the telemetry did next. The log is what makes your final report defensible.

> Act deliberately. A reflex action taken before you understand the effect can destroy the evidence you need for the report, and can cost you a capability you have not finished using.

---

## Operational Constraints

| Constraint | Detail |
| --- | --- |
| Propulsion | No thrusters installed |
| Attitude control | Reaction wheels only, with a persistent fault present from session start |
| Fault clearing | The attitude fault does not clear automatically, it stays until the crew recovers it |
| RPO software | Not available, no automated rendezvous or proximity guidance |
| Ground network | Minimum elevation 10 degrees, so passes are finite |
| Session pacing | 80 simulation minutes at 2x speed |

---

## Spacecraft Configuration

Every team commands an identical Microsat: a 100 kg imaging platform in a near-circular Earth orbit inclined at 70 degrees.

### Schematic

![Microsat schematic](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/module_10/schematic.png)

### Platform Summary

| Item | Configuration |
| --- | --- |
| Mass | 100 kg |
| Orbit | Near-circular Earth orbit, 8600 km semi-major axis, 70 degree inclination |
| Power generation | Two body-mounted solar panels |
| Power storage | Battery, 80 Ah nominal capacity |
| Payload | Optical camera, 1024 x 1024 |
| Navigation | GPS sensor |
| Comms | Receiver and transmitter |
| Data | Onboard storage |
| Avionics | Onboard computer |
| Propulsion | No thrusters |
| ADCS | Reaction wheels |

---

## Payload and Sensors

| Component | Purpose |
| --- | --- |
| **Camera** | 1024 x 1024 optical imager for surface tasking and product capture. Mounted on the -Y face. |
| **GPS Sensor** | Primary navigation source and the origin of the geolocation metadata attached to your products. |
| **Storage** | Holds captured products onboard until they are downlinked. |
| **Computer** | Runs the flight software that produces your telemetry stream. |

> Pointing depends on the reaction wheels, and the wheels are not fully healthy at session start. Check what pointing authority you actually have before you promise a capture.

---

## Power Network

Two body-mounted solar panels, Solar Panel +X and Solar Panel -X, feed a single battery that supplies the bus. The battery starts at half charge, so power is a real constraint across an 80 minute session. Watch the charge trend during eclipse and while you are working the recovery.

![Power network diagram](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/module_10/power_network_diagram.png)

### Starting States

| Component | Setting | Value |
| --- | --- | --- |
| Solar Panel +X | Area / efficiency | 0.3 m2 at 40 percent, enabled |
| Solar Panel -X | Area / efficiency | 0.3 m2 at 40 percent, enabled |
| Battery | Nominal capacity | 80 Ah |
| Battery | Charge fraction at start | 50 percent |

---

## Communications

### Ground Stations

| Station | Region |
| --- | --- |
| Tokyo | North-west Pacific |
| Anchorage | High-latitude northern pass |
| Houston | North America |
| Lima | West coast of South America |
| Santiago | Southern South America |

The minimum elevation angle is 10 degrees, so contact is limited to real passes. Use the **Link Budget** panel for contact intervals, signal-to-noise ratio, and pass geometry. Which station you command through is an operational choice during a recovery, not a detail, so track your active pass and plan the next one before you need it.

### Team Frequencies

Each team is assigned a unique frequency and key at session start, pre-configured on the operator terminal, and identical on the uplink and downlink.

---

## Tasking Areas

Two areas hold surface vessels for imagery tasking:

- **Caribbean, off Florida and the Bahamas:** four dark-hulled vessels, all stationary.
- **Peru, off Lima:** three orange-hulled vessels, all stationary.

Plan passes using the **Map**, point the camera with **Guidance**, and capture during the window. Record the capture time and the reported geolocation for every product, because you will need both when you decide what can be released and what stays on hold.

---

## Suggested Team Roles

Split responsibilities early. The Mission Lead should assign these roles at the start of the exercise:

- **Mission Lead:** Declares the incident, owns the scope, makes go/no-go calls on containment and release, and issues the Recovery SITREPs on the 15 simulation minute cadence.
- **Satellite Operator:** Works telemetry, guidance pointing, and subsystem health, runs the recovery playbook steps, and diagnoses the attitude-control fault.
- **Payload Operator:** Captures imagery, tracks which products are affected, manages the hold, and drives the payload re-baseline.
- **Communications Specialist:** Monitors link budget, pass geometry, and navigation data quality, and advises which station to command the recovery through.

> **Working method:** One person keeps the timeline, everyone else calls their actions out loud before they take them. Log every change, the time, and the telemetry response. When two operators see different symptoms, compare notes before assuming a single cause.

---

## Before You Begin

1. Log in to the operator terminal with your team credentials.
2. Confirm your spacecraft appears on the **Map** and that telemetry and the Link Budget are updating.
3. Read the **Tasks** section, then take a baseline reading of power, navigation, pointing, and link health before you change anything.
4. Split roles, agree who holds the incident log, and set a timer for the first Recovery SITREP.

---

## Learning Focuses

### Incident Declaration and Scoping

Turn confirmed adversary activity into a declared incident with a defensible scope, and keep unrelated hardware faults outside that scope.

### Scoped Containment and Recovery

Contain only what you declared, work the safe-mode and rollback playbook in order, and confirm each step from telemetry rather than assuming it worked.

### Fault Diagnosis Under Pressure

Diagnose and recover a persistent attitude-control fault from spacecraft telemetry while a cyber response is running in parallel.

### Product Integrity

Hold suspect payload products, re-baseline the payload against a known-good reference, and release only against criteria the crew agreed and evidenced.

### Recovery Reporting

Issue consistent Recovery SITREPs on a fixed cadence and keep an evidence log that lets someone else reconstruct what happened.
