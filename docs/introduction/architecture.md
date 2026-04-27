# Architecture

Space Range is a hub-and-spoke system. A single **Studio backend** runs the simulation and is the source of truth for all state. Every other participant — Operator UI, Python scripts, custom apps, the Admin UI — is a **client**, and every client talks to Studio exclusively through an **MQTT broker**.

There are no direct connections between Studio and clients, and no direct connections between clients. All traffic is namespaced by **game name** and segmented by **team**, with cryptographic separation enforced via per-team passwords.

---

## High-level diagram

```text
                ┌────────────────────────────────────────────────────────┐
                │                  Studio (Unreal plugin)                │
                │                                                        │
                │   ┌──────────────────┐   ┌────────────────────────┐    │
                │   │ Spacecraft       │   │ Ground Controllers     │    │
                │   │ Controllers      │   │  (per team)            │    │
                │   │  (per asset)     │   └────────────────────────┘    │
                │   └──────────────────┘                                 │
                │                                                        │
                │   ┌──────────────────┐   ┌────────────────────────┐    │
                │   │ Admin Controller │   │ Session / Sim clock    │    │
                │   └──────────────────┘   └────────────────────────┘    │
                └───────────────────────────┬────────────────────────────┘
                                            │  MQTT publish/subscribe
                                            ▼
                            ┌──────────────────────────────────┐
                            │           MQTT broker            │
                            └──────────────────────────────────┘
                                ▲           ▲             ▲
                  XOR(team pwd) │           │ XOR(team pwd) │ XOR(admin pwd)
                                │           │               │
                       ┌────────┴───┐  ┌────┴─────────┐  ┌──┴──────────────┐
                       │ Operator UI│  │ Python /     │  │ Admin UI /      │
                       │ (per team) │  │ custom apps  │  │ instructor app  │
                       └────────────┘  └──────────────┘  └─────────────────┘
```

Two cryptographic layers are in play:

- **Transport layer** — every team-scoped MQTT payload is XOR-encrypted with the team's 6-character alphanumeric password (admin payloads use the admin password). This is what segregates teams on the broker.
- **RF layer** — telemetry packets *inside* downlink payloads are additionally Caesar-cipher-encoded with a per-team **frequency** and **numeric key**. Operators must know both to decode telemetry. The session topic is unencrypted.

Both layers are described in detail in [Concepts → Encryption](../concepts/encryption.md).

---

## Topic layout

All topics are rooted at `Zendir/SpaceRange/<GAME>/...`, where `<GAME>` is the game name configured in Studio.

| Direction | Topic | Encrypted with | Purpose |
| --- | --- | --- | --- |
| Studio → all | `Zendir/SpaceRange/<GAME>/Session` | none | Simulation clock and instance ID. |
| Client → Studio | `Zendir/SpaceRange/<GAME>/<TEAM>/Uplink` | XOR(team password) | Spacecraft commands. |
| Studio → client | `Zendir/SpaceRange/<GAME>/<TEAM>/Downlink` | XOR(team password) | RF-realistic telemetry packets (Caesar cipher inside). |
| Client → Studio | `Zendir/SpaceRange/<GAME>/<TEAM>/Request` | XOR(team password) | Ground controller requests. |
| Studio → client | `Zendir/SpaceRange/<GAME>/<TEAM>/Response` | XOR(team password) | Ground controller replies. |
| Admin → Studio | `Zendir/SpaceRange/<GAME>/Admin/Request` | XOR(admin password) | Admin / instructor requests. |
| Studio → admin | `Zendir/SpaceRange/<GAME>/Admin/Response` | XOR(admin password) | Admin / instructor replies. |

A few internal topics also exist (notably the per-frequency RF medium) but are not part of the public client API — operators and admins use only the topics above.

The full reference, including QoS recommendations and retained-message behavior, is in [API Reference → MQTT topics](../api-reference/mqtt-topics.md).

---

## Component responsibilities

### Studio backend

Studio is the only authoritative component. It:

- Loads the **scenario JSON** at startup and constructs teams, assets, and ground stations.
- Runs the **physics, RF link budget, and component models** (ADCS, propulsion, payloads, etc.).
- Publishes the **session clock** continuously.
- Hosts a **SpacecraftController** per asset that consumes uplink commands and emits telemetry.
- Hosts a **GroundController** per team that handles request/response queries and ground-station behaviour (transmit power, antenna gain, etc.).
- Hosts a single **SpaceRangeAdminController** that handles admin-side queries and simulation-control commands.
- Manages **command scheduling** (time-tagged uplinks executed when the simulation clock reaches them).
- Manages **encryption key/frequency rotation** when a team uplinks an `encryption` command.
- Records **scenario events** (success / failure / informational milestones) for later admin queries.

Clients should treat Studio as opaque — only the MQTT message contracts are stable.

### MQTT broker

Any MQTT 3.1.1+ broker works (Mosquitto, EMQX, HiveMQ, NanoMQ, etc.). Space Range does not require any specific broker plugin; it uses standard publish/subscribe with no broker-side ACLs (segregation is achieved through XOR passwords, which means a misconfigured client can't decrypt traffic for teams it does not have credentials for).

For development, a single-node Mosquitto on `localhost:1883` is the simplest setup.

### Operator UI

A React web app (`space-range-operator/`). It runs in two modes:

- **User mode** — drives a single team's spacecraft. Subscribes to the team's downlink/response topics and publishes on uplink/request. Decrypts telemetry, displays imagery, plots state, and provides forms for every command type.
- **Admin mode** — uses the admin password and admin topics. Provides team rosters, simulation controls, scenario events, and historical data.

The UI is one valid client, not a privileged one. Anything the UI can do, a custom client can do over MQTT.

### Python scripting framework

The `space-range-scripts/` directory contains a reference Python client and a small framework for writing scripted scenarios. It is useful for:

- **Automated test missions** and regression scenarios.
- **Teaching** — operators can read concise, well-named Python and adapt it to their own clients.
- **Headless or batch operations** when the Operator UI is not appropriate.

The framework's own `README.md` covers usage. These docs cover the wire formats it builds on.

### Custom clients

A custom client only needs to:

1. Connect to the MQTT broker.
2. Implement the XOR password layer (and Caesar cipher for telemetry).
3. Speak the JSON message formats described in the [API Reference](../api-reference/mqtt-topics.md).
4. (Optional) Decode CCSDS Space Packets using the team's **XTCE schema**, which can be pulled with the `get_packet_schemas` request.

There is no SDK requirement — any language with an MQTT client and a JSON parser can drive Space Range.

---

## End-to-end command path

When an operator issues `guidance` to point a spacecraft at a target, the path is:

1. The client builds the JSON command (command type, arguments, optional `time` for scheduling, optional `id`).
2. The client serializes to bytes and **XOR-encrypts** with the team password.
3. The client publishes to `Zendir/SpaceRange/<GAME>/<TEAM>/Uplink`.
4. Studio's per-team listener decrypts, identifies the target asset, and dispatches to that asset's `SpacecraftController`.
5. The controller validates and either executes immediately or stores the command in its **schedule** keyed by simulation time.
6. When the command runs, the simulation responds (e.g. ADCS slew begins) and any resulting telemetry is generated by the spacecraft's components on their normal cadence.

---

## End-to-end telemetry path

When the spacecraft emits telemetry (e.g. a periodic Ping):

1. The component writes a **CCSDS Space Packet** populated against the team's XTCE schema.
2. The packet is **Caesar-cipher-encoded** using the team's current numeric key, tagged with the current frequency.
3. The simulation evaluates the **RF link budget** (transmitter power, antenna gain, range, jamming, etc.). If the link closes, the bytes are emitted on the team's downlink path; otherwise they are dropped.
4. The downlink payload is **XOR-encrypted** with the team password and published on `Zendir/SpaceRange/<GAME>/<TEAM>/Downlink`.
5. The client subscribes, **XOR-decrypts**, **Caesar-decodes** with the current key, and parses Space Packets using the XTCE schema.

If the link is jammed or out of range, the operator sees nothing on downlink — the absence of telemetry is itself a meaningful signal.

---

## Next

- [Concepts → Encryption](../concepts/encryption.md) — the two crypto layers in detail.
- [API Reference → MQTT topics](../api-reference/mqtt-topics.md) — the full topic table with examples.
- [Getting Started → Connecting](../getting-started/connecting.md) — minimal end-to-end example.
