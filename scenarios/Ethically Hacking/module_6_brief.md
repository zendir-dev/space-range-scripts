**Scenario:** FSSCP Module 6  
**Epoch:** 2026-04-15 10:00:00 UTC  
**Duration:** 40 minutes (real time)  
**Ground stations:** London, Dubai, Singapore

---

## Overview

This is a basic training module in the Space Range operator environment. You operate a **Microsat** in Earth orbit with access to three ground stations.

Your job in this module is to get fluent with the operator terminal: find your spacecraft, read its telemetry, work the power and imaging subsystems, and answer the scored questions as a coordinated team. There is no anomaly timeline and no adversary activity scripted into the session.

> Questions and scoring are delivered in the **Tasks** section of the operator terminal. Use this brief for mission context and spacecraft configuration, not as an answer key.

---

## Mission Goals

1. **Confirm your connection:** Check that your Microsat is present and telemetry is updating.
2. **Learn the terminal layout:** Open every view in the side navigation and work out what data each one exposes. Several tasks depend on knowing where a given value lives.
3. **Characterize your orbit:** Use GPS and position telemetry to work out the shape and size of the orbit you are flying.
4. **Work the ground network:** Compare link performance across London, Dubai, and Singapore during the session and note how contact quality changes with pass geometry.
5. **Operate the power subsystem:** Inspect the solar panels and battery, then use guidance pointing to see how spacecraft attitude changes power generation.
6. **Exercise the payload:** Configure the optical camera, capture imagery, and downlink it, watching the effect on battery charge and onboard storage.
7. **Run as a crew:** Agree who owns which subsystem, who makes go/no-go calls, and how issues are escalated before you start commanding.

---

## Operational Constraints

| Constraint | Detail |
| --- | --- |
| Propulsion | No thrusters installed - the orbit cannot be changed |
| Propellant | No fuel system on board |
| RPO Software | **Not available** - no automated rendezvous or proximity guidance |
| Attitude Control | Reaction wheels installed and enabled |
| Power | Solar generation and battery only; image capture and downlink both draw charge |
| Low Power | The spacecraft protects itself when battery charge falls toward 10% |

---

## Spacecraft Configuration

You operate a **Microsat** design with no docked, neutral, or third-party assets in the environment.

### Schematic

The following image describes the schematic for the spacecraft, including the location of the sensors and payload.

![Microsat schematic](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/module_6/schematic.png)

### Platform Summary

| Item | Configuration |
| --- | --- |
| Mass | 100 kg |
| Orbit | Earth orbit, circular |
| Power generation | Two body-mounted solar panels (+X and -X faces) |
| Power storage | Single battery, fully charged at session start |
| Payload | Optical camera (1024 × 1024) |
| Navigation | GPS sensor |
| Comms | Receiver (3 dB antenna gain) and transmitter |
| Data | Onboard storage |
| Avionics | Flight computer |
| Attitude control | Reaction wheels |
| Propulsion | None |

### Other sensors

- **GPS Sensor:** Provides onboard position and velocity data. GPS is active in this universe configuration.
- **Storage:** Holds captured imagery until it is downlinked during a ground contact.

---

## Power Network

Both solar panels feed a single battery, and the battery supplies the spacecraft loads. Panel output depends on how the panel faces are oriented relative to the Sun, so attitude commanding and power management are the same problem. Capturing an image and downlinking it each cost charge, so plan payload activity around your battery state.

### Component starting states

| Component | Start State |
| --- | --- |
| Solar Panel +X | Enabled |
| Solar Panel -X | Enabled |
| Battery | Enabled, fully charged |
| Reaction Wheels | Enabled |
| Camera | Enabled |
| Receiver / Transmitter | Enabled |
| Storage | Enabled |

> Guidance offers several pointing modes. Try them and watch panel output in telemetry rather than assuming which attitude is best for your current objective.

---

## Communications

### Ground stations

| Station | Role |
| --- | --- |
| **London** | Uplink and downlink |
| **Dubai** | Uplink and downlink |
| **Singapore** | Uplink and downlink |

Stations track down to the horizon, so contact is close to continuous across the session. Contact quality is not constant, however: it varies with range and elevation as your spacecraft moves through each pass. Use the **Link Budget** telemetry to compare stations rather than assuming they perform alike.

---

## Using the Operator Terminal

The operator is a web application your whole team can use at the same time. The side navigation gives you these views:

- **Controls**
- **Images**
- **Schedule**
- **Telemetry**
- **Messages**
- **Plots**
- **Map**
- **Timeline**

Open each one in the first few minutes and note what it shows. Part of this module is learning where each class of data lives, so do not wait until a task asks before you go looking.

A typical workflow:

1. Confirm your spacecraft state and pass geometry before commanding.
2. Command attitude and payload from the control view.
3. Capture imagery, then downlink it during a ground contact.
4. Read subsystem telemetry and plot the channels you need for task answers.
5. Enter your answers in **Tasks**.

If you get stuck, use the in-app chat agent - it can help with how the operator terminal works.

---

## Suggested Team Roles

Split responsibilities early, and agree how decisions and escalations flow before the first command goes up. Some scored tasks depend on your team having settled its rules of engagement.

- **Mission Lead:** Keeps the team on objective and on time, and tracks which tasks are complete.
- **Satellite Operator:** Works spacecraft bus commanding and health telemetry.
- **Payload Operator:** Works the camera, image capture, and onboard storage.
- **Ground Network Coordinator:** Tracks ground station contacts, link quality, and downlink opportunities.

---

## Before You Begin

1. Confirm your Microsat appears with live telemetry and a valid GPS solution.
2. Open **Tasks** and read every question before you start commanding, so you know what evidence to gather.
3. Assign the four roles and confirm who calls go or no-go.

---

## Learning Focuses

### Operator Navigation

Move confidently between the terminal views, and build a mental map of which view exposes which class of spacecraft data.

### Orbit and Telemetry Literacy

Use GPS and position data to describe the orbit you are flying, and pull specific subsystem values out of telemetry when a task calls for them.

### Power and Payload Operations

Relate spacecraft attitude to solar panel output, manage battery charge against the cost of capture and downlink, and produce usable imagery within the session.

### Ground Network Awareness

Compare link performance across three ground stations, recognise how pass geometry drives contact quality, and time downlinks for when the link supports them.

### Crew Coordination

Run the exercise as a small operations team with clear ownership, decision authority, and escalation, so commanding and answering stay organised under time pressure.
