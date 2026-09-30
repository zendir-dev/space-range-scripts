**Scenario:** Tutorial  
**Epoch:** 2026-04-15 07:30:00 UTC  
**Simulation speed:** 3× real time  
**Ground stations:** Paris, Dubai, Singapore, Sydney, Auckland

---

## Overview

This is an introductory exercise in the Space Range operator environment. Your team shares a single **Microsat** in Earth orbit with basic subsystems - enough to practice commanding the spacecraft, reading telemetry, and working through scored tasks.

There is no complex mission timeline. Take your time exploring the operator terminal and completing the questions in the **Tasks** section. Use this brief for context, not as an answer key. The Tasks list for your session is the source of truth for what to collect.

---

## Mission Goals

1. **Log in and Connect:** Open the operator terminal with your team credentials and confirm you can see your spacecraft on the Map.
2. **Learn the Basics:** Practice guidance pointing, camera imaging, and reading telemetry from GPS, battery, camera, and communications panels.
3. **Image ground targets:** Use the Map to find any surface objects in your session, then capture them with guidance and the camera.
4. **Complete the Tasks:** Work through the questions in the Tasks section. They show the kinds of challenges you may see in later scenarios.
5. **Explore Freely:** Once the tasks are done, keep experimenting with the operator views until you are comfortable with the workflow.

---

## Using the Operator Terminal

The operator is a web application your whole team can use at the same time. After login, use the side navigation to move between views.

| View | What it is for |
| --- | --- |
| **Map** | See your orbit, ground track, ground objects, and which ground stations can see your spacecraft. |
| **Control** | Send commands: point the spacecraft with **Guidance**, configure the **Camera**, and capture images. |
| **Telemetry** | Check link health, frequency and key settings, and subsystem data from the spacecraft. |
| **Tasks** | Read and submit answers to the scored questions for this scenario. |

A typical workflow:

1. Open **Map** to confirm your spacecraft state and look for ground objects.
2. Use **Control → Guidance** to point the camera at a target on the ground.
3. Use **Control → Camera** to capture an image. Start wide if you need to search, then tighten the field of view once you have the target.
4. Open **Telemetry** to read GPS, battery, camera, and link-budget values needed for questions.
5. Enter your answers in **Tasks**.

If you get stuck, use the in-app chat agent. It can help with how the operator terminal works.

---

## Your Spacecraft

Each team operates the same **Microsat** design in the shared **Main** collection.

| Item | Configuration |
| --- | --- |
| Orbit | LEO around Earth |
| Mass | 100 kg |
| Power | Two solar panels and a fully charged battery |
| Attitude | Reaction wheels |
| Payload | Optical camera (1024 x 1024, 10–90° field of view) |
| Navigation | GPS sensor |
| Comms | Receiver and transmitter |
| Other | EM sensor, onboard storage |

Your team frequency is pre-configured at session start and is the same for uplink and downlink.

Every team commands the same **Microsat**, a 100 kg Earth-observation vehicle.

### Schematic

![Microsat schematic](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/orbital_intel/schematic.png)

---

## Before You Begin

1. Log in to the operator terminal with your team credentials.
2. Confirm your spacecraft appears on the **Map** and telemetry is updating.
3. Open **Tasks** and read the questions for this session before you start commanding.
4. Split roles if helpful: one person on guidance and camera, another on telemetry and answers.

---

## Learning focuses

### Operator navigation

Find your way around the Map, Control, Telemetry, and Tasks views so you can move between situational awareness, commanding, and scoring without getting lost.

### Spacecraft commanding

Point the spacecraft with guidance, capture camera imagery of ground targets, and understand how commands flow from the operator terminal to the simulated spacecraft.

### Telemetry literacy

Read GPS, battery, camera, and link-budget data from live telemetry and use those values to support task answers and basic health monitoring.

### Task workflow

Locate evidence in imagery and telemetry, interpret what you see, and submit answers through the Tasks section, the same pattern used in full competition scenarios.
