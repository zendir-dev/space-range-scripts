# Teams and Assets

Every Space Range scenario is organized around two primary entities — **teams** and **assets**. A team is a logical group of operators who share credentials and topics; an asset is a controllable simulation object (most commonly a spacecraft) that belongs to a single team.

This page describes how teams and assets are configured, how they relate to one another, and how they show up on the wire.

---

## Teams

A team is the **unit of identity and segregation** in Space Range. Every operator-side message is scoped to exactly one team, and the team's password is the key used to XOR-encrypt all of its MQTT traffic.

### Team properties

Teams are declared in the scenario JSON file under the top-level `teams` array. Each team has:

| Property | Type | Description |
| --- | --- | --- |
| `enabled` | boolean | Whether the team is active. Disabled teams cannot send or receive traffic. |
| `id` | integer | The team's numeric ID. Appears in MQTT topics and identifies the team to Studio. |
| `password` | string (6 chars) | The XOR password used for the team's MQTT encryption. |
| `key` | integer (0–255) | The Caesar cipher key used for the RF telemetry layer. |
| `frequency` | number (MHz) | The team's uplink/downlink RF frequency. |
| `color` | string (hex) | The team's display color in the Operator UI. |
| `name` | string | A human-readable team name (e.g. `"Red Team"`). |
| `collection` | string | The ID of the asset collection this team controls. |

Two teams must have **distinct passwords** (otherwise their MQTT traffic decrypts identically) and **distinct frequencies** (otherwise they share an RF channel and can read each other's downlinks once they crack the Caesar key).

### Per-team MQTT topics

Each team has its own slice of the topic tree:

```text
Zendir/SpaceRange/<GAME>/<TEAM>/Uplink     ← commands to spacecraft
Zendir/SpaceRange/<GAME>/<TEAM>/Downlink   ← telemetry from spacecraft
Zendir/SpaceRange/<GAME>/<TEAM>/Request    ← ground-controller queries
Zendir/SpaceRange/<GAME>/<TEAM>/Response   ← ground-controller replies
```

`<TEAM>` is the team's numeric `id`. Studio publishes and subscribes only on these team-scoped topics for team-side traffic; the admin uses a separate pair of `Admin/Request` and `Admin/Response` topics. See [API Reference → MQTT topics](../api-reference/mqtt-topics.md) for the full table.

### Credentials

Three pieces of data make up a team's "keys to the kingdom":

1. **Password** — a 6-character alphanumeric string used as the XOR key for the team's MQTT traffic.
2. **Frequency** — a number in MHz used as the RF channel for the team's downlinked telemetry. Required to listen on the right RF stream.
3. **Caesar key** — an integer 0–255 used to byte-shift telemetry payloads inside the RF stream. Required to decode telemetry.

Operators must hold all three to participate. The Caesar key and frequency can be **rotated** at runtime by the team using the [`encryption`](../api-reference/spacecraft-commands.md#encryption) spacecraft command; the password is fixed for the duration of a scenario.

---

## Assets

An asset is anything in the scenario that the simulation owns and a team can interact with. The most common asset is a **spacecraft**, but **ground stations** are also assets. Each asset has a unique identifier; the simulation uses it to route commands and tag telemetry.

### Asset IDs

- **Asset IDs are 8-character hex strings** (e.g. `A3F2C014`).
- They are case-insensitive on the wire — Studio uppercases them before matching — so `a3f2c014` and `A3F2C014` refer to the same asset.
- IDs are assigned by Studio at scenario load and remain stable for the lifetime of the simulation instance. They change when the scenario is reset (which also changes the [instance ID](simulation-clock.md)).

In commands, the asset ID is sent as the **`Asset`** field of the uplink JSON. In ground-controller responses it appears as **`asset_id`**. (The two key names predate the unified docs; they describe the same thing.)

### Spacecraft

A spacecraft asset is a fully simulated satellite. It owns:

- A **computer** with a state (`NOMINAL`, `LOW`, `SAFE`, `FULL STORAGE`, `TRANSMIT`, `REBOOTING`).
- An **ADCS** subsystem and reaction wheels, used by [`guidance`](../api-reference/spacecraft-commands.md#guidance).
- A **propulsion** stack (RCS / main thrusters), used by [`thrust`](../api-reference/spacecraft-commands.md#thrust), [`rendezvous`](../api-reference/spacecraft-commands.md#rendezvous), and [`docking`](../api-reference/spacecraft-commands.md#docking).
- A **transmitter / receiver** pair for RF.
- A **storage buffer** holding undownlinked data and imagery.
- A list of **components** (cameras, sensors, solar panels, jammer, etc.) addressable by name.

Each spacecraft is hosted by a `SpacecraftController` on the Studio side. From the operator's perspective, the controller appears as the receiver of every `Uplink` message addressed to it.

You can list a team's spacecraft and discover their components via [`list_assets`](../api-reference/ground-requests.md#list_assets) and [`list_entity`](../api-reference/ground-requests.md#list_entity).

### Ground stations

A ground station is the team's physical RF transmitter/receiver on the surface. It has:

- `latitude`, `longitude`, `altitude` (geodetic position).
- `power` (transmitter power, watts).
- `gain` (antenna gain, dBi).
- `bandwidth` (link bandwidth).

Ground stations are not commanded directly — they participate automatically in every link budget computation that involves a team-owned spacecraft. They can be enumerated with [`list_stations`](../api-reference/ground-requests.md#list_stations). Their transmit power and antenna gain feed the [link budget](telemetry.md#the-rf-link-budget) that decides whether a downlink packet reaches the team or is lost.

The ground transmitter can also be commanded to emit raw bytes (separate from any spacecraft uplink) via [`transmit_bytes`](../api-reference/ground-requests.md#transmit_bytes) — useful for SIGINT-style training and red-team injection scenarios.

---

## Collections

A **collection** is a named bundle of asset IDs. Each team is wired up to exactly one collection in the scenario JSON, and that collection determines which spacecraft the team controls. Collections are an organisational tool: they let you reuse the same set of spacecraft across multiple team layouts, or hand a single team an entire fleet by referencing one collection.

```jsonc
{
  "teams": [
    { "id": 111111, "name": "Red Team",  "collection": "RED",  /* … */ },
    { "id": 222222, "name": "Blue Team", "collection": "Main", /* … */ }
  ],
  "assets": {
    "space": [
      { "id": "SC_001", "name": "Microsat" },
      { "id": "SC_002", "name": "Recon"    }
    ],
    "collections": [
      { "id": "Main", "space_assets": ["SC_001"] },
      { "id": "RED",  "space_assets": ["SC_002"] }
    ]
  }
}
```

In this example, Red Team controls `SC_002` and Blue Team controls `SC_001`. Neither team can command the other's spacecraft — uplinks addressed to a foreign asset are silently rejected at the controller (see [Commands and Scheduling → Validation](commands-and-scheduling.md#validation)).

The full scenario file format, including ground stations and scenario events, is documented in [Guides → Scenario configuration](../guides/scenario-config.md).

---

## Discovering assets at runtime

You typically don't hard-code asset IDs into your client. Instead, fetch them once after connecting:

```python
ground.request("list_assets")
# → {
#     "type": "list_assets",
#     "req_id": ...,
#     "args": {
#       "space": [
#         {"asset_id": "A3F2C014", "name": "Microsat", "rpo_enabled": false, "intercept_enabled": true},
#         ...
#       ]
#     }
#   }
```

Then for any specific asset, fetch its components:

```python
ground.request("list_entity", {"asset_id": "A3F2C014"})
# → "args": {
#     "asset_id": "A3F2C014",
#     "components": [
#       {"name": "Camera A",  "class": "Imager",      "component_id": 0, "is_imager": true},
#       {"name": "RW Set",    "class": "ReactionWheels", "component_id": 1, "is_imager": false},
#       ...
#     ],
#     "jammer": { "is_active": false, "frequency": 2230.0, "power": 50.0 }
#   }
```

`component_id` and `name` are interchangeable in commands that target a component (e.g. `guidance.target` accepts either). Use `name` for human-written scripts; use `component_id` for programmatic clients that want stable references.

---

## Next

- [Simulation clock](simulation-clock.md) — how time and instance IDs work.
- [Encryption](encryption.md) — the password and Caesar key in detail.
- [Commands and scheduling](commands-and-scheduling.md) — how commands flow from a client to an asset.
