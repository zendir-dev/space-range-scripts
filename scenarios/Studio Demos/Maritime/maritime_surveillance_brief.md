**Scenario:** Maritime Surveillance  
**Epoch:** 2025-04-15 07:30:00 UTC  
**Simulation speed:** 3× real time  
**Session length:** 45 minutes (simulation time)  
**Ground stations:** Paris, Dubai, Singapore, Sydney, Auckland

---

## Overview

This is a studio demonstration of **maritime surveillance** from orbit. Two teams - **Team Blue** and **Team Red** - each operate the same **Microsat** imaging spacecraft in the shared **Main** collection.

Your mission is to surveil vessel traffic in the **Arabian Sea** off the west coast of India using the onboard camera, while also working through telemetry and health tasks in the **Tasks** section. Use this brief for mission context and spacecraft configuration - not as an answer key.

---

## Mission Goals

1. **Log in and connect** - Open the operator terminal with your team credentials and confirm you can see your spacecraft on the map.
2. **Acquire maritime imagery** - Use guidance pointing and the camera to image vessels in the Arabian Sea operating area.
3. **Read spacecraft telemetry** - Practise pulling values from GPS, battery, solar panels, and the Link Budget panel.
4. **Complete the tasks** - Work through the scored questions in the Tasks section before the session ends.

---

## Maritime Operating Area

Four surface vessels are active in the Arabian Sea (off the west coast of India). All share the same hull colour and are transiting on **different headings and speeds**.

| Detail | Value |
| --- | --- |
| Region | Arabian Sea, west coast of India |
| Vessel count | 4 |
| Hull colour | Same for all vessels (identify from imagery) |
| Motion | Each vessel on its own heading |

Use the **Map** to plan when your orbit passes over the area, then command **Guidance** and **Camera** to capture imagery during the collection window. Vessels are moving - you may need more than one pass to build a clear picture.

---

## Using the Operator Terminal

The operator is a web application your whole team can use at the same time. After login, use the side navigation to move between views.

| View | What it is for |
| --- | --- |
| **Map** | See your orbit, ground track, vessel positions, and which ground stations can see your spacecraft. |
| **Control** | Send commands - point the spacecraft with **Guidance**, configure the **Camera**, and capture images. |
| **Telemetry** | Check link health, frequency and key settings, and subsystem data from the spacecraft. |
| **Tasks** | Read and submit answers to the scored questions for this scenario. |

A typical workflow:

1. Open **Map** to confirm your spacecraft state and plan your pass over the Arabian Sea.
2. Use **Control → Guidance** to point the camera at the vessel cluster.
3. Use **Control → Camera** to capture an image (wide field of view is available for area searches).
4. Open **Telemetry** to read GPS, battery, link budget, and solar panel data for task answers.
5. Enter your answers in **Tasks**.

If you get stuck, use the in-app chat agent - it can help with how the operator terminal works.

---

## Your Spacecraft

Each team operates the same **Microsat** design in the shared **Main** collection.

| Item | Configuration |
| --- | --- |
| Orbit | Earth, ~7 500 km semi-major axis |
| Mass | 100 kg |
| Power | Two solar panels, fully charged battery |
| Attitude | Reaction wheels |
| Payload | Optical camera (1024 × 1024, 10°–90° field of view) |
| Navigation | GPS sensor |
| Comms | Receiver and transmitter (team-assigned frequency) |
| Other | EM sensor, onboard storage |

Your team frequency is pre-configured at session start and is the same for uplink and downlink.

### Teams

| Team | Role in this demo |
| --- | --- |
| **Team Blue** | Cyan operator identity - competes on the same spacecraft and tasks as Team Red |
| **Team Red** | Red operator identity - same spacecraft design, separate RF credentials |

Both teams command the same **Microsat** asset; your team colour and frequency distinguish your session on the operator terminal.

---

## Before You Begin

1. Log in to the operator terminal with your team credentials.
2. Confirm your spacecraft appears on the **Map** and telemetry is updating.
3. Open **Tasks** and read the questions before you start commanding.
4. Split roles if helpful - one person on guidance and camera, another on telemetry and task answers.

---

## Learning focuses

### Operator navigation

Find your way around the map, control, telemetry, and tasks views so you can move between situational awareness, commanding, and scoring without getting lost.

### Maritime collection

Plan an imaging pass over the Arabian Sea, point the camera at moving surface targets, and interpret vessel imagery for identification tasks.

### Telemetry literacy

Read GPS, battery, solar panel, and link-budget data from live telemetry and use those values to support task answers and basic health monitoring.

### Task workflow

Locate evidence in imagery and telemetry, interpret what you see, and submit answers through the Tasks section - the same pattern used in full competition scenarios.
