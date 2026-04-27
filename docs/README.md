# Space Range Documentation

Reference and developer documentation for **Space Range** — a real-time, multi-team spacecraft operations simulator. These docs describe the public MQTT API, message formats, scenario configuration, and the included tools (Operator UI, Python scripting framework) so you can build clients, drive scenarios, and integrate Space Range with external systems.

This documentation is for **users** of Space Range — operators, integrators, and instructors. It is not internal documentation for the C++ plugin developers.

---

## Where to start

| If you want to… | Go to |
| --- | --- |
| Understand what Space Range is and how it fits together | [Introduction](introduction/overview.md) |
| See the system architecture at a glance | [Architecture](introduction/architecture.md) |
| Look up an unfamiliar term | [Glossary](introduction/glossary.md) |
| Connect a custom client and send your first command | [Getting Started](getting-started/connecting.md) |
| Find the wire format for a command or request | [API Reference](api-reference/mqtt-topics.md) |
| Decode CCSDS / XTCE telemetry packets | [Decoding Telemetry](guides/decoding-telemetry.md) |
| Run a scenario as an instructor | [Instructor & Admin Guide](guides/instructor-admin.md) |
| Author a new scenario from scratch | [Scenario authoring reference](scenarios/README.md) |
| Use the bundled Operator UI | [Operator UI Guide](guides/operator-ui-guide.md) |

---

## Documentation map

### Introduction
- [Overview](introduction/overview.md) — what Space Range is, who uses it, and the components involved.
- [Architecture](introduction/architecture.md) — how Studio, MQTT, the Operator UI, and scripts connect.
- [Glossary](introduction/glossary.md) — acronyms and domain terminology.

### Concepts
- [Teams and assets](concepts/teams-and-assets.md) — teams, collections, asset IDs, components.
- [Simulation clock](concepts/simulation-clock.md) — session topic, simulation time, instance resets.
- [Encryption](concepts/encryption.md) — XOR password layer and Caesar cipher RF layer.
- [Commands and scheduling](concepts/commands-and-scheduling.md) — command lifecycle, time-tagging, schedule management.
- [Telemetry](concepts/telemetry.md) — CCSDS Space Packets, XTCE, link budgets, downlink path.

### Getting started
- [Prerequisites](getting-started/prerequisites.md) — broker, game name, credentials.
- [Connecting](getting-started/connecting.md) — topics, subscriptions, decryption.
- [Your first command](getting-started/first-command.md) — end-to-end example in Python and JavaScript.
- [Operator UI quick start](getting-started/operator-ui.md) — using the bundled web app.

### API reference
- [MQTT topics](api-reference/mqtt-topics.md) — full topic map with encryption keys.
- [Session stream](api-reference/session-stream.md) — simulation clock packet.
- [Spacecraft commands](api-reference/spacecraft-commands.md) — uplink command reference.
- [Ground requests](api-reference/ground-requests.md) — per-team request/response API.
- [Admin requests](api-reference/admin-requests.md) — instructor / constructive-agent API.

### Guides
- [Encryption walkthrough](guides/encryption-walkthrough.md) — XOR + Caesar in Python and JavaScript.
- [Decoding telemetry](guides/decoding-telemetry.md) — parsing Space Packets with XTCE schemas.
- [Scenario configuration](guides/scenario-config.md) — narrative tour of the scenario JSON file format.
- [Instructor & admin guide](guides/instructor-admin.md) — admin password, scenario events, simulation control.
- [Operator UI guide](guides/operator-ui-guide.md) — tour of the bundled web app.
- [Troubleshooting & FAQ](guides/troubleshooting.md) — common errors and fixes.

### Scenario authoring (deep reference)
- [Overview & top-level shape](scenarios/README.md) — index, casing rules, loading order, minimal scenario, agent quickstart.
- [`simulation`](scenarios/simulation.md) — clock, integrator, simulation speed.
- [`universe`](scenarios/universe.md) — atmosphere, magnetosphere, GPS, lighting toggles.
- [`ground_stations`](scenarios/ground-stations.md) — receiving network shared by every team.
- [`teams`](scenarios/teams.md) — team identity, credentials, frequency, collection.
- [`assets.space[]` & `assets.collections[]`](scenarios/spacecraft.md) — spacecraft definitions and team-asset map.
- [`components[]`](scenarios/components.md) — full per-class field reference for every component.
- [`objects.ground[]`](scenarios/ground-objects.md) — vessels, text labels, and other passive ground actors.
- [`events[]`](scenarios/events.md) — scripted Spacecraft and GPS events with full `Data` schemas.
- [`questions[]`](scenarios/questions.md) — Q&A scoring (text, number, select, checkbox).
- [Recipes & agent checklist](scenarios/recipes.md) — annotated end-to-end patterns and an agent-author checklist.

### Reference
- [Packet formats](reference/packet-formats.md) — Ping, Schedule Report, Uplink Intercept binary layouts.
- [Data types](reference/data-types.md) — variable types, units, and ranges used across the API.

---

## Conventions used in these docs

- **Topic placeholders** are written `<GAME>`, `<TEAM>`, `<ASSET>`. Replace them with the game name, the numeric team ID, and the 8-character hex asset ID respectively.
- **JSON schemas** show concrete example values rather than type placeholders so you can copy/paste and modify them.
- **Code examples** are provided in **Python 3** (matching the `space-range-scripts` framework) and **JavaScript** (matching the Operator UI). Other languages can follow the same wire format.
- All times are in **simulation seconds** unless explicitly labelled as UTC or wall-clock.
- All frequencies are in **MHz** at the API surface. Internally the simulation works in Hz; the conversion is handled by the controllers.
