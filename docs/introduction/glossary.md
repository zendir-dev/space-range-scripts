# Glossary

Terminology used throughout the Space Range documentation. Where a term has a Space-Range-specific meaning that differs from the general aerospace usage, both are noted.

---

## A

**ADCS — Attitude Determination and Control System**
The subsystem that measures and controls a spacecraft's orientation. In Space Range, ADCS is the target of the [`guidance`](../api-reference/spacecraft-commands.md#guidance) command and produces orientation fields in [Ping telemetry](../reference/packet-formats.md#ping).

**Admin / Admin Password**
The instructor-side identity. Has a single global password used to XOR-encrypt traffic on the `Admin/Request` and `Admin/Response` topics, and access to the [admin API](../api-reference/admin-requests.md).

**Asset**
Any controllable simulation object that belongs to a team. Most commonly a spacecraft, but ground stations are also assets in the scenario JSON. Each asset has an 8-character hex `Asset ID` used in MQTT command payloads.

**ASCII / UTF-8 / Hex / Base64**
Encodings accepted by [`transmit_bytes`](../api-reference/ground-requests.md#transmit_bytes) for raw ground-transmitter payloads.

---

## C

**Caesar cipher**
The numeric-key substitution cipher used as the **RF layer** of Space Range encryption. Applied byte-wise to telemetry before transmission. Key is an integer 0–255 and rotates with the [`encryption`](../api-reference/spacecraft-commands.md#encryption) command. See [Concepts → Encryption](../concepts/encryption.md).

**CCSDS — Consultative Committee for Space Data Systems**
The international body whose standards Space Range telemetry follows. In particular, telemetry is delivered as **CCSDS Space Packets** with primary headers conforming to CCSDS 133.0-B-2.

**Collection**
A grouping of assets within a team's scenario configuration. Used for organisation and visibility, not for control.

**Command**
A JSON object published on a team's `Uplink` topic to drive a spacecraft. See the [Spacecraft commands](../api-reference/spacecraft-commands.md) reference.

**Command schedule**
The per-asset list of commands queued for future simulation times. Managed via the [`get_schedule`](../api-reference/spacecraft-commands.md#get_schedule), [`remove_command`](../api-reference/spacecraft-commands.md#remove_command), and [`update_command`](../api-reference/spacecraft-commands.md#update_command) commands.

---

## D

**Docking**
RPO endgame in which two spacecraft mate. Commanded with the [`docking`](../api-reference/spacecraft-commands.md#docking) command.

**Downlink**
Data flowing **from** a spacecraft **to** a ground station. The team's MQTT downlink topic carries the post-RF, XOR-wrapped bytes. See [Concepts → Telemetry](../concepts/telemetry.md).

---

## E

**Event (scenario event)**
A milestone the scenario can record (success, failure, informational). Triggered by `event_triggered` (team-side) or `admin_event_triggered` (admin-side); queryable via `admin_query_events` and `admin_get_scenario_events`.

**Encryption command**
The spacecraft uplink command that rotates the team's downlink **frequency** and **Caesar key** simultaneously. Shuts the spacecraft down for a brief reboot to apply the change. See [`encryption`](../api-reference/spacecraft-commands.md#encryption).

---

## F

**Frequency**
The simulated RF channel used by a team's downlink and any ground-transmitter override. Stored in MHz at the API surface. Frequencies are part of a team's RF identity and rotate when the [`encryption`](../api-reference/spacecraft-commands.md#encryption) command is issued.

---

## G

**Game / Game name**
The string identifier for a Space Range session, used as a namespace in every MQTT topic (`Zendir/SpaceRange/<GAME>/...`). Configured in Studio at startup.

**Ground Controller**
The Studio-side controller that handles per-team **request/response** traffic and models the team's ground transmitter (power, gain, bandwidth, location). See [API Reference → Ground requests](../api-reference/ground-requests.md).

**Ground Station**
A scenario asset representing the team's physical RF transmitter/receiver. Has latitude, longitude, altitude, transmitter power, antenna gain, and bandwidth.

---

## I

**Instance ID**
A monotonic integer broadcast on the [Session](../api-reference/session-stream.md) topic that increments each time the simulation is reset. Clients use it to detect resets and re-sync state.

**Instructor**
The role of the human running the scenario. Holds the admin password and uses the admin API. Often the same person as the **scenario designer** during development; usually different roles during exercises.

---

## J

**Jammer / Jamming**
A spacecraft payload that degrades or denies RF links. Targeted with the [`jammer`](../api-reference/spacecraft-commands.md#jammer) command. From the operator's perspective, a successful jam manifests as missing or corrupt telemetry on the targeted team's downlink.

---

## L

**Link budget**
The RF calculation performed each tick to decide whether a downlink packet is delivered. Inputs include transmitter power, antenna gain, range, frequency, and active jamming.

**LVLH — Local Vertical / Local Horizontal**
The orbital reference frame whose axes are aligned with the radial vector to the central body and the orbital velocity. Used by [`guidance`](../api-reference/spacecraft-commands.md#guidance) when pointing relative to the orbit, not the inertial frame.

---

## M

**MQTT**
The publish/subscribe messaging protocol Space Range uses for all client traffic. Any MQTT 3.1.1+ broker works.

---

## O

**Operator**
The role of a person controlling spacecraft for a single team. Holds that team's password and uses the per-team uplink/downlink/request/response topics.

**Operator UI**
The bundled React web app under `space-range-operator/`. The reference operator client.

---

## P

**Password (team password)**
A 6-character alphanumeric string used as the XOR key for all of a team's MQTT traffic. Issued in the scenario configuration. Distinct from the **admin password**.

**Payload (RF)**
The byte-stream delivered after RF and encryption have been applied. Distinct from the simulation **JSON payload** of a command — context disambiguates.

**Ping**
The standard periodic spacecraft status message. See [Reference → Packet formats → Ping](../reference/packet-formats.md#ping).

---

## R

**Rendezvous**
Maneuvering one spacecraft into the proximity of another. Commanded with [`rendezvous`](../api-reference/spacecraft-commands.md#rendezvous). Often a precursor to docking.

**Request / Response**
The per-team JSON RPC channel exposed by the Ground Controller. Distinct from spacecraft uplink commands. See [API Reference → Ground requests](../api-reference/ground-requests.md).

**RF**
Radio frequency. In Space Range, used to describe the simulated link layer between spacecraft and ground stations, modelled with a link budget and (per team) frequency and Caesar key.

**RPO — Rendezvous and Proximity Operations**
The umbrella term for close-range maneuvering between two spacecraft. Includes [`rendezvous`](../api-reference/spacecraft-commands.md#rendezvous) and [`docking`](../api-reference/spacecraft-commands.md#docking).

---

## S

**Scenario**
The configured world for a session — teams, assets, ground stations, scenario questions, encryption keys. Defined in the scenario JSON.

**Schedule Report**
The downlinked telemetry message that lists currently scheduled (pending) commands on a spacecraft. Produced in response to [`get_schedule`](../api-reference/spacecraft-commands.md#get_schedule). Sensitive arguments (like raw bytes or new encryption keys) are redacted before transmission.

**Session topic**
The unencrypted MQTT topic that publishes the simulation clock and instance ID. See [API Reference → Session stream](../api-reference/session-stream.md).

**Simulation time / Sim time**
The clock used by Space Range, measured in seconds since the start of the current instance. All command `time` fields and telemetry timestamps are in simulation time unless explicitly stated otherwise.

**Space Packet**
A CCSDS-defined variable-length packet used for both telemetry and commands. Space Range uses Space Packets for downlinked telemetry.

**Spacecraft Controller**
The Studio-side controller hosting one spacecraft. Receives uplink commands and emits telemetry.

**Studio**
The Unreal Engine application that runs the simulation. The authoritative server.

---

## T

**Team**
A logical group of operators and assets sharing a password and a set of MQTT topics. Teams are isolated from each other on the broker by their XOR password.

**Telemetry**
Data flowing from a spacecraft to operators. Includes Ping, Schedule Report, imagery, and intercepted uplink records. See [Concepts → Telemetry](../concepts/telemetry.md).

**Time-tagged command**
A command whose `time` field is in the future. Stored in the spacecraft's command schedule and executed when the simulation clock reaches it. See [Concepts → Commands and scheduling](../concepts/commands-and-scheduling.md).

---

## U

**Uplink**
Data flowing from a client to a spacecraft. The team's MQTT uplink topic carries the XOR-wrapped JSON command bytes.

**Uplink Intercept**
A telemetry record produced when a spacecraft receives a (possibly foreign) uplink, used for SIGINT-style training. See [Reference → Packet formats → Uplink Intercept](../reference/packet-formats.md#uplink-intercept).

---

## X

**XOR encryption**
The transport-level cipher used on all team and admin MQTT traffic. Each byte of the payload is XOR-ed against the corresponding byte of the team (or admin) password, repeated cyclically. Cheap, deterministic, and sufficient to keep teams from accidentally reading each other's traffic.

**XTCE — XML Telemetric and Command Exchange**
The CCSDS-standard XML format used by Space Range to describe telemetry packet structures. Each team has its own XTCE schema (delivered via [`get_packet_schemas`](../api-reference/ground-requests.md#get_packet_schemas)) which clients use to parse downlinked Space Packets.

---

## Z

**Zendir**
The company that develops Space Range. The name also appears as the top-level segment of every MQTT topic (`Zendir/SpaceRange/...`), which identifies Space Range traffic on shared brokers.
