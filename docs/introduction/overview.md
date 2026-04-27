# Overview

Space Range is a real-time, multi-team **spacecraft operations simulator**. It models satellites, ground stations, RF links, scenarios, and a constructive-agent instructor layer, and exposes everything over **MQTT** so any client — the bundled Operator UI, the Python scripting framework, or your own application — can participate.

A typical session involves:

- A **Studio backend** (Unreal Engine) running the simulation and exposing controllers per team.
- One or more **operator clients** (the bundled web Operator UI, custom apps, or scripts) controlling spacecraft for a team.
- An optional **admin / instructor client** that drives the scenario, queries simulation state, and triggers scenario events.
- An **MQTT broker** that all of the above connect to.

---

## What Space Range provides

Space Range is built around four capability surfaces, each available over MQTT:

1. **Spacecraft command and control** — uplink commands to a spacecraft (attitude, propulsion, payloads, telemetry configuration, scheduling, etc.) and receive RF-realistic downlinked telemetry.
2. **Ground operations** — query asset metadata, ground-station configuration, telemetry settings, transmit raw bytes, run AI chat queries, and answer scenario questions.
3. **Admin / scenario control** — read global simulation state, query historical events, trigger scenario events, list teams and assets, and start/stop/reset the simulation.
4. **Session timing** — a single, unencrypted broadcast that publishes the current simulation time and instance ID.

Spacecraft and tools are organized into **teams** (red, blue, white-cell, etc.). Each team has its own credentials, its own MQTT topics, and its own visibility rules over the scenario.

---

## Who this documentation is for

These docs target three audiences:

### 1. Spacecraft operators

You drive one or more spacecraft for a team during a scenario, either through the bundled **Operator UI** or via the **Python scripting framework** under `space-range-scripts/`.

If that's you, start with:

- [Getting Started → Operator UI quick start](../getting-started/operator-ui.md)
- [Concepts → Commands and scheduling](../concepts/commands-and-scheduling.md)
- [Guides → Decoding telemetry](../guides/decoding-telemetry.md)

### 2. Custom-client developers

You're building a bespoke application — a mission control dashboard, a training app, a scoring system, or an automated agent — that talks to Space Range over MQTT. You don't need access to the Studio (Unreal) source to do this; the entire public surface is documented in these docs.

If that's you, start with:

- [Getting Started → Connecting](../getting-started/connecting.md)
- [API Reference → MQTT topics](../api-reference/mqtt-topics.md)
- [Concepts → Encryption](../concepts/encryption.md)

### 3. Instructors and admins

You set up scenarios, monitor multiple teams, trigger events, and control the simulation clock.

If that's you, start with:

- [Guides → Instructor & admin guide](../guides/instructor-admin.md)
- [API Reference → Admin requests](../api-reference/admin-requests.md)
- [Guides → Scenario configuration](../guides/scenario-config.md)

---

## Components at a glance

| Component | Role | Where it lives |
| --- | --- | --- |
| **Studio (Unreal plugin)** | Authoritative simulation. Hosts spacecraft controllers, ground controllers, and the admin controller. Owns the simulation clock and scenario state. | `studio/Plugins/SpaceRange/` |
| **MQTT broker** | Message bus for all command, request, response, telemetry, and session traffic. | External (any standard MQTT 3.1.1+ broker). |
| **Operator UI** | React web app for operators. Lets a team view assets, see telemetry, send commands, and run a scripted-mission UI. | `space-range-operator/` (user side) |
| **Admin UI** | The admin-side of the same React app. Used by instructors. | `space-range-operator/` (admin side) |
| **Python scripting framework** | Reference Python client. Useful for automation, scripted mission rehearsals, custom dashboards, and teaching. | `space-range-scripts/` |
| **Scenario JSON** | Static configuration that defines teams, assets, ground stations, encryption keys, and scenario questions/events. | Loaded by Studio at game launch. |

---

## How a scenario flows

At a high level, a session looks like this:

1. The instructor configures a **scenario JSON** file (teams, assets, ground stations, frequencies, passwords, scenario events). See [Guides → Scenario configuration](../guides/scenario-config.md).
2. **Studio** is launched with that scenario. It connects to the MQTT broker, starts publishing on the **session topic**, and listens on the per-team **uplink** and **request** topics and on the **admin/request** topic.
3. **Operators** connect using their team's password. They subscribe to the team's **downlink** and **response** topics, and publish on the team's **uplink** and **request** topics.
4. The **instructor / admin** connects with the admin password and uses the **admin/request** and **admin/response** topics to monitor and steer the scenario.
5. As time advances, the simulation publishes telemetry on the team **downlink** topic — encrypted with a Caesar cipher and a numeric **frequency**, then re-wrapped in the team's XOR password layer. The Operator UI / scripts decrypt and decode CCSDS Space Packets per the team's **XTCE schema**.
6. Operators send commands over **uplink**, ask questions over **request**, and receive replies over **response**. Commands can be immediate or **time-scheduled**.
7. The instructor can trigger **scenario events** (success/failure milestones), pause or reset the simulation, query historical state, or list scenario questions and accept answers from teams.

---

## What is *not* covered here

This documentation deliberately excludes:

- **Studio (C++) plugin development.** If you are extending the Unreal plugin itself, that's an internal engineering concern, not a user-facing one.
- **Building a Space Range client from scratch as a tutorial.** The reference framework in `space-range-scripts/` already does that, and is documented separately in the framework's own `README.md`. These docs cover *what* a client must do on the wire, not a walkthrough of building one.

---

## Next

- For a system-level diagram and message flow, see [Architecture](architecture.md).
- For acronyms (ADCS, RPO, LVLH, CCSDS, XTCE, …) see the [Glossary](glossary.md).
