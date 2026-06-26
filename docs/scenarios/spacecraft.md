# `assets.space[]` and `assets.collections[]`

The `assets` block is the part most scenario authoring time is spent on. It has two arrays:

- `assets.space[]` — the spacecraft definitions. Each entry creates one spacecraft with its attached components.
- `assets.collections[]` — the lookup that maps team `collection` strings to spacecraft IDs.

Studio reads both arrays when the scenario loads. Each `assets.space[]` entry defines one spacecraft; each `assets.collections[]` entry maps a team collection id to one or more spacecraft ids.

---

## Spacecraft top-level shape

```json
{
  "id":   "SC_001",
  "name": "Microsat",
  "orbit":         { ... },
  "physics":       { ... },
  "visualization": { ... },
  "controller":    { ... },
  "power":         { ... },
  "fuel":          { ... },
  "components":    [ ... ]
}
```

| Block | Required? | Description |
| --- | --- | --- |
| `id` | yes | Unique string referenced from `assets.collections[].space_assets`. The 8-character hex `asset_id` you see at runtime is **derived** from this. |
| `name` | yes | Display name. The Operator UI and ground-controller responses strip the team-name prefix from this for cleanliness. |
| `orbit` | no | Initial Keplerian orbit. Default is a placeholder LEO at the equator; always specify this in real scenarios. |
| `physics` | no | Mass, centre-of-mass, and 3×3 inertia tensor. Defaults are usable but pick numbers that match the spacecraft scale. |
| `visualization` | no | Unreal mesh path and rendering scale/offset. Default is a generic chassis. |
| `controller` | no | Per-spacecraft tuning — battery thresholds, ping interval, RPO flag, etc. |
| `power` | no | Optional on-board bus wiring (`bus`) and cross-spacecraft links (`interconnects`). See [`power`](#power--electrical-bus) below. |
| `fuel` | no | Optional on-board fuel network (`bus`). Cross-spacecraft fuel links are declared in the top-level [`docking`](#docking-start-the-scenario-already-docked) block. See [`fuel`](#fuel--propellant-bus) below. |
| `components` | yes (in practice) | The on-board hardware. A spacecraft with no components has nothing for teams to operate. |

---

## `orbit` — initial Keplerian elements

```json
"orbit": {
  "planet": "Earth",
  "values": [8200.0, 0.02, 17.3, 283.0, 0.0, 360.0],
  "offset": [0.0,    0.0,  0.0,  0.0,   0.0, 0.001]
}
```

| Key | JSON type | Description |
| --- | --- | --- |
| `planet` | `string` | Body to orbit. Accepts `"Earth"`, `"Moon"`, `"Mars"` (case-insensitive). Default `"Earth"`. |
| `values` | `number[6]` | Classical orbital elements. **Order is fixed** and units are: <br>`[0]` semi-major axis (km), <br>`[1]` eccentricity (unitless), <br>`[2]` inclination (deg), <br>`[3]` right ascension of ascending node Ω (deg), <br>`[4]` argument of periapsis ω (deg), <br>`[5]` true anomaly ν (deg). |
| `offset` | `number[6]` | A small per-element offset added to `values`. Same order/units as `values`. Use this to break ties between identical co-located spacecraft (a common pattern is `[0,0,0,0,0,0.001]` to give each spacecraft a slightly different starting true anomaly). |

The semi-major axis is in **kilometres** in the JSON. Internally Studio stores it in metres — the conversion is handled by the loader (`* 1000.0`).

If `values` has fewer than six entries, the missing ones are zero-filled.

### Common orbits

| Orbit | Approx. `values` |
| --- | --- |
| Equatorial low-Earth (LEO), circular, 700 km altitude | `[7078.0, 0.0, 0.0, 0.0, 0.0, 0.0]` |
| Sun-synchronous (SSO), 800 km, 98.6° inclination | `[7178.0, 0.0, 98.6, 90.0, 0.0, 0.0]` |
| ISS-like, 51.6° inclination | `[6778.0, 0.0, 51.6, 0.0, 0.0, 0.0]` |
| Mid-LEO, slight eccentricity (used by `Orbital Intel`) | `[8200.0, 0.02, 17.3, 283.0, 0.0, 360.0]` |
| Polar, ~600 km (used by `Telemetry_Drop`) | `[7000.0, 0.0, 97.88, 270.0, 0.0, 320.0]` |

---

## `physics` — mass, COM, inertia

```json
"physics": {
  "override_mass":   true,
  "mass":            100.0,
  "center_of_mass":  [0.0, 0.0, 0.0],
  "inertia_tensor":  [
    [10.0,  0.0,  0.0],
    [ 0.0, 10.0,  0.0],
    [ 0.0,  0.0, 10.0]
  ]
}
```

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `override_mass` | `bool` | `false` | If `true`, `mass` is forced. If `false`, mass is computed from the sum of component `Mass` fields. Set `true` when you want a precise total mass regardless of how component masses add up. |
| `mass` | `number` (kg) | computed | Total mass. Only used when `override_mass: true`. |
| `center_of_mass` | `number[3]` (m) | `[0,0,0]` | Body-frame offset of the centre of mass from the spacecraft origin. |
| `inertia_tensor` | `number[3][3]` (kg·m²) | identity-ish | 3×3 principal-axis inertia tensor. Diagonal is the most common case (a symmetric spacecraft). Off-diagonal terms model coupling between axes. |

Inertia matters whenever attitude control is exercised (reaction wheels, thrusters, external torque). For pure-orbit demos the defaults are fine.

The `physics` block is **optional** — omit it and Studio falls back to a sensible default mass and inertia.

---

## `visualization` — rendering

```json
"visualization": {
  "mesh":   "/ZendirAssetsSpace/Blueprints/Spacecraft/ZenSat/BP_Z_SC_ZenSat_Chassis",
  "scale":  1.0,
  "offset": [0.0, 0.0, 0.12],
  "hide":   false
}
```

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `mesh` | `string` | a default chassis | Unreal asset path to the chassis blueprint. Use `"None"` to fall back to a generic mesh. The shipped scenarios use paths such as `/ZendirAssetsSpace/Blueprints/Spacecraft/ZenSat/BP_Z_SC_ZenSat_Chassis`, `/ZendirAssetsSpace/Blueprints/Spacecraft/MRO/BP_Z_SC_MRO_Chassis`, `/ZendirAssetsSpace/Blueprints/Spacecraft/GatewayCore/BP_Z_SC_GatewayCore_Chassis`. |
| `scale` | `number` | `1.0` | Visual scale factor of the mesh. Has no physics effect. |
| `offset` | `number[3]` (m) | `[0,0,0]` | Visual offset of the mesh from the spacecraft origin. Use to centre the rendered chassis. |
| `hide` | `bool` | `false` | If `true`, the spacecraft is hidden from the world view but still simulates fully. Useful for "constructive-agent" rogue spacecraft that should be discovered visually. |

`mesh` is a presentation-only field — telemetry and command semantics are unaffected.

---

## `controller` — per-spacecraft tuning

```json
"controller": {
  "safe_fraction":           0.1,
  "capture_tax":             0.001,
  "downlink_tax":            0.01,
  "ping_interval":           20.0,
  "reset_interval":          60.0,
  "jamming_multiplier":      100.0,
  "enable_rpo_software":              false,
  "enable_intercept": true
}
```

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `safe_fraction` | `number` `0–1` | `0.1` | Battery fraction below which the spacecraft enters `SAFE` mode (autonomous power-conservation behaviour). |
| `capture_tax` | `number` `0–1` | `0.001` | Battery fraction consumed per `capture` command (image capture cost). |
| `downlink_tax` | `number` `0–1` | `0.001` | Battery fraction consumed per `downlink` command. |
| `ping_interval` | `number` (sim s) | `20.0` | Sim seconds between auto-Pings. Affects how quickly teams see command acks. |
| `reset_interval` | `number` (sim s) | `300.0` | Sim seconds the spacecraft is offline after a `reset` (or after [`encryption`](../api-reference/spacecraft-commands.md#encryption), which causes a reboot). Lower this for shorter exercises. |
| `jamming_multiplier` | `number` | `1.0` | Scales the per-watt RF interference produced by the spacecraft's `Jammer` payload. Shipped scenarios commonly use `100.0`. |
| `enable_rpo_software` | `bool` | `false` | `true` installs RPO flight software so the [`rendezvous`](../api-reference/spacecraft-commands.md#rendezvous) command can run. Docking adapters, fuel/power interconnects, and the [`docking`](../api-reference/spacecraft-commands.md#docking) command are independent of this flag — they depend on the relevant components being present on the spacecraft. |
| `enable_intercept` | `bool` | `true` | If `true`, the spacecraft records uplink packets it overhears for SIGINT-style replay (downlinked as [Uplink Intercept](../reference/packet-formats.md#uplink-intercept) records). Set `false` to save memory in scenarios that do not exercise this feature. |

Studio reads **`enable_intercept`** first; when it is omitted, loading falls back to the legacy key **`record_uplink_intercept`** so older scenario JSON keeps working.

The `controller` block is **optional**; defaults work for most exercises. The keys that change most between scenarios are `safe_fraction` (lower for fault-injection scenarios where teams should be forced to manage power), `reset_interval` (lower for fast-paced exercises), and `enable_rpo_software` (only set `true` on spacecraft that need to manoeuvre).

---

## `power` — electrical bus

Every spacecraft has an on-board **power bus**. The optional `power` block defines how **solar panels** (and other power sources), **batteries**, **bus components** (switches, fuses, diodes, limiters, regulators, sinks), **payloads** wired as loads, and the **jammer** (if present) are connected when the scenario starts. Component classes and `data` keys: [components.md — Power bus network components](components.md#power-bus-network-components).

### JSON shape

```json
"power": {
  "bus": [
    {
      "source_component": "Solar Panel +X",
      "source_terminal": "out",
      "target_component": "Battery",
      "target_terminal": "out"
    },
    {
      "source_component": "Battery",
      "source_terminal": "out",
      "target_component": "Jammer",
      "target_terminal": "in"
    }
  ]
}
```

| Key | JSON type | Description |
| --- | --- | --- |
| `bus` | `object[]` | Ordered list of on-board connections. Each object is one directed link on that spacecraft's bus. |

Per-connection fields (names must match component `name` values on **that** spacecraft):

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `source_component` | `string` | — | Source component **name** (resolved via the spacecraft controller's `GetTarget`). |
| `source_terminal` | `string` | `"out"` | Terminal on the source: `"out"` or `"in"` (case-insensitive). |
| `target_component` | `string` | — | Target component **name**. |
| `target_terminal` | `string` | `"out"` | Terminal on the target: `"out"` or `"in"`. |

If either component name cannot be found, Studio logs a warning and **skips** that connection; other connections still apply.

Author `power` as a nested object on each spacecraft entry. Studio reads `power.bus` as an ordered list of on-board connections. Cross-spacecraft power links are declared separately in the top-level [`docking`](#docking-start-the-scenario-already-docked) block (see [Power interconnects](#power-interconnects)).

### Default behaviour when `bus` is empty or omitted

If `power` is missing, `{}`, or `"bus": []`, Studio **auto-wires** the bus:

1. **More than one battery** — connect batteries **in series** along the bus (**first battery `out` → next battery `in`**, and so on).
2. **At least one battery** — connect every solar panel (and other power source) to the **first battery** with **both terminals set to `out`** (`out` → `out`).
3. **Jammer present** — if there is at least one battery, connect the **last battery** to the jammer (**battery `out` → jammer `in`**).

Spacecraft with **no batteries and no power sources** still get a power bus, but auto-wiring creates **no connections** (for example a jammer-only rogue hull with no solar panel or battery).

Explicit `bus` entries **replace** auto-wiring entirely — they do not merge with defaults. If you define `bus`, you must list every connection you need.

### Typical explicit patterns (match shipped scenarios)

**Dual solar panels + single battery** (defender `Microsat`):

```json
"power": {
  "bus": [
    { "source_component": "Solar Panel +X", "source_terminal": "out", "target_component": "Battery", "target_terminal": "out" },
    { "source_component": "Solar Panel -X", "source_terminal": "out", "target_component": "Battery", "target_terminal": "out" }
  ]
}
```

**Single solar panel + battery + jammer** (rogue `SC_ROGUE` / `Recon` with panel):

```json
"power": {
  "bus": [
    { "source_component": "Solar Panel", "source_terminal": "out", "target_component": "Battery", "target_terminal": "out" },
    { "source_component": "Battery", "source_terminal": "out", "target_component": "Jammer", "target_terminal": "in" }
  ]
}
```

**No storage or generation** — omit `power` or use `"bus": []` and rely on auto-wiring (no-op when there are no batteries/sources).

Jamming still draws from the battery when wired; `controller.jamming_multiplier` scales RF interference power consumption in the spacecraft controller.

## `fuel` — propellant bus

Every spacecraft has an on-board **fuel bus** when fuel components are present. The optional `fuel` block defines how **fuel sources** (tanks), **valves**, **pumps**, **thrusters**, and **fuel interconnects** are connected when the scenario starts. Component classes and `data` keys: [components.md — Fuel network components](components.md#fuel-network-components).

### JSON shape

Uses the same connection field names as `power` (`source_component`, `source_terminal`, `target_component`, `target_terminal`). Terminals are `"in"` or `"out"` (case-insensitive). Studio maps those to the correct fuel port on each component type (for example valve `in` → inlet, thruster `in` → intake, tank `out` → tank port).

```json
"fuel": {
  "bus": [
    {
      "source_component": "Main Tank",
      "source_terminal": "out",
      "target_component": "Main Valve",
      "target_terminal": "in"
    },
    {
      "source_component": "Main Valve",
      "source_terminal": "out",
      "target_component": "Thruster +X",
      "target_terminal": "in"
    }
  ]
}
```

| Key | JSON type | Description |
| --- | --- | --- |
| `bus` | `object[]` | Ordered list of on-board fuel connections. Each object is one directed link on that spacecraft's fuel bus. |

Per-connection fields (names must match component `name` values on **that** spacecraft):

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `source_component` | `string` | — | Source component **name**. |
| `source_terminal` | `string` | `"out"` | Terminal on the source: `"out"` or `"in"`. |
| `target_component` | `string` | — | Target component **name**. |
| `target_terminal` | `string` | `"in"` | Terminal on the target: `"out"` or `"in"`. |

If either component name cannot be found, Studio logs a warning and **skips** that connection.

**Fuel pumps** also draw electrical power when enabled — wire the pump on `power.bus[]` separately (same `in` / `out` terminals as other loads). Runtime valve/pump state is changed via [`fuel_bus`](../api-reference/spacecraft-commands.md#fuel_bus) and read back with [`get_configuration`](../api-reference/spacecraft-commands.md#get_configuration) (`scope: "fuel_bus"`).

### Default behaviour when `bus` is empty or omitted

If `fuel` is missing, `{}`, or `"bus": []`, Studio **auto-wires** every **fuel source** to every **thruster** with a direct `out` → `in` link. Spacecraft with no fuel sources or no thrusters get a fuel bus but no connections.

Explicit `bus` entries **replace** auto-wiring entirely — they do not merge with defaults.

### Worked example

See `Testing/test_fuel_scenario.json` — two tanks, three valves, one pump, three thrusters on an explicit manifold.

### Fuel interconnects

A **Fuel Interconnect** bridges two spacecraft **fuel buses** so propellant can be transferred across a **docked** interface (for example a tanker or station topping up a client). Like [power interconnects](#power-interconnects), fuel links are declared in the top-level [`docking`](#docking-start-the-scenario-already-docked) block, not per-spacecraft: each interconnect is bonded to a local fuel object on its own `fuel.bus`, and the cross-spacecraft pairing is declared **once** in `docking` as a fuel-interconnect connection.

#### Component on each spacecraft

Add a `Fuel Interconnect` to **`components[]`** on every hull that should share fuel:

```json
{ "class": "Fuel Interconnect", "name": "Fuel Interconnect" }
```

See [Fuel Interconnect](components.md#fuel-interconnect) for the `data` keys (`Is Bidirectional`, `Vent To Space When Unconnected`, etc.). On a hub, add **one interconnect per client** (e.g. `Fuel Interconnect A`…`E`).

#### Bond each interconnect to a local fuel object

Wire each interconnect into its own `fuel.bus` so it has a local fuel object (a `Fuel Source`, `Fuel Valve`, or `Fuel Pump`) to draw from or feed into. Putting a **valve next to the interconnect** lets flow be opened/closed locally (or set `Vent To Space When Unconnected: false` and drop the valve):

```json
"fuel": {
  "bus": [
    { "source_component": "Depot Tank", "source_terminal": "out", "target_component": "Transfer Valve", "target_terminal": "in" },
    { "source_component": "Transfer Valve", "source_terminal": "out", "target_component": "Fuel Interconnect", "target_terminal": "in" }
  ]
}
```

The interconnect maps to a single `Local` fuel port, so wiring it on the bus bonds it to its neighbour automatically; no operator action is needed beyond opening the valves on each side.

#### Link the interconnects in the `docking` block

Declare the cross-spacecraft link in the top-level [`docking`](#docking-start-the-scenario-already-docked) array as a **fuel-interconnect connection** — both endpoints name a `Fuel Interconnect`, so Studio **links** them (rather than docking them) when the scenario is built:

```json
"docking": [
  { "from_team": 111111, "from_target": "Fuel Interconnect", "to_asset": "SC_HUB", "to_target": "Fuel Interconnect A" }
]
```

Each endpoint names a component plus the spacecraft carrying it — addressed **by team** (`from_team`/`to_team`) for per-team craft or **by asset** (`from_asset`/`to_asset`) for a specific/neutral craft such as a shared hub. See the [`docking`](#docking-start-the-scenario-already-docked) section for the full field reference and addressing rules.

#### Requirements and restrictions

| Rule | Detail |
| --- | --- |
| **Interconnect on each side** | Both endpoints named in the connection must be `Fuel Interconnect` components. |
| **Local bond** | Each interconnect must be wired on its own `fuel.bus` (to a valve/pump/tank). |
| **Linked, not derived** | The pairing is **explicit** in the `docking` block; it is not inferred from docking adapters. Fuel still only flows once the hulls are docked, so pair the fuel link with a docking-adapter connection (or a runtime dock). |
| **Tank flow rates must be set** | Fuel only moves if the **supply** tank has `Amount > 0` and the **receiving** tank has spare `Capacity` and a **positive `Desired Ingoing Flow Rate`** (it defaults to `0.0` — an unset receiver draws nothing). See [Fuel Source](components.md#fuel-source). |
| **Cross-team / neutral OK** | A neutral hub (addressed by `to_asset`) and clients on different teams link fine (the RPO hub is exactly this). |

#### Worked example (two hulls)

`Testing/test_fuel_scenario` ships a minimal demo: a **Tanker** (depot tank → transfer valve → interconnect) starts docked to a **Microsat** (interconnect → fill valve → main tank). Both craft belong to one team, so the `docking` block uses `from_asset`/`to_asset` to disambiguate them — one docking-adapter entry to dock the hulls and one fuel-interconnect entry to link the interconnects:

```json
"docking": [
  { "from_team": 111111, "from_asset": "SC_FUEL_TANKER", "from_target": "Docking Adapter",  "to_team": 111111, "to_asset": "SC_FUEL_TEST", "to_target": "Docking Adapter" },
  { "from_team": 111111, "from_asset": "SC_FUEL_TANKER", "from_target": "Fuel Interconnect", "to_team": 111111, "to_asset": "SC_FUEL_TEST", "to_target": "Fuel Interconnect" }
]
```

#### Recipe: one hub, many clients (multi-port station)

To feed several clients from a **single station tank** (the RPO scenario: five teams docked to a neutral hub):

1. **Station (`SC_002`, neutral):** one `Fuel Source` (the depot tank), then **one `Fuel Interconnect` per client** (`Fuel Interconnect A`…`E`). Wire the tank into each interconnect on `fuel.bus` (optionally through a per-client `Fuel Valve`).
2. **Each client (`SC_001`):** one `Fuel Interconnect` bonded to a fill valve/tank, plus its single `Docking Adapter`. Because the client definition is shared across teams, **no per-team wiring is needed**.
3. **`docking` block:** one docking-adapter entry **and** one fuel-interconnect entry per team, sending each team's client to a distinct hub port and interconnect (the neutral hub is addressed by `to_asset`):

```json
"docking": [
  { "from_team": 111111, "from_target": "Docking Adapter",  "to_asset": "SC_002", "to_target": "Docking A" },
  { "from_team": 111111, "from_target": "Fuel Interconnect", "to_asset": "SC_002", "to_target": "Fuel Interconnect A" }
]
```

`Vent To Space When Unconnected: false` on the station interconnects means an idle port simply stops flow instead of venting (and lets you drop the per-client valves). See `scenarios/RPO/rpo.json` for the full five-port build.

### Power interconnects

A **Power Interconnect** bridges two spacecraft **power buses** so they share one electrical network across a docked interface (for example a hub charging a docked client). It is the power analogue of the [Fuel interconnect](#fuel-interconnects): each interconnect is wired onto its local `power.bus`, and the cross-spacecraft pairing is declared **once** in the top-level [`docking`](#docking-start-the-scenario-already-docked) block as a power-interconnect connection.

A `Power Interconnect` is itself a switch (it extends `Power Switch`), so it can be opened to break the bridge.

#### Component on each spacecraft

Add a `Power Interconnect` to **`components[]`** on every hull that should share power:

```json
{ "class": "Power Interconnect", "name": "Interconnect" }
```

On a hub, add **one interconnect per client** (e.g. `Interconnect A`…`E`).

#### Wire each interconnect onto its local bus

Each interconnect must be part of that spacecraft's `power.bus`, typically fed from a battery. Put a `Power Switch` in front of it if you want the link gated locally (the RPO client does this so each team chooses when to charge):

```json
"power": {
  "bus": [
    { "source_component": "Solar Panel +X", "source_terminal": "out", "target_component": "Battery", "target_terminal": "out" },
    { "source_component": "Solar Panel -X", "source_terminal": "out", "target_component": "Battery", "target_terminal": "out" },
    { "source_component": "Battery", "source_terminal": "out", "target_component": "Charge Switch", "target_terminal": "in" },
    { "source_component": "Charge Switch", "source_terminal": "out", "target_component": "Interconnect", "target_terminal": "in" }
  ]
}
```

If the interconnect is not wired on its local bus first, the cross-spacecraft link is skipped with a warning.

#### Link the interconnects in the `docking` block

Declare the cross-spacecraft link in the top-level [`docking`](#docking-start-the-scenario-already-docked) array as a **power-interconnect connection** — both endpoints name a `Power Interconnect`, so Studio **links** them (rather than docking them) when the scenario is built:

```json
"docking": [
  { "from_team": 111111, "from_target": "Interconnect", "to_asset": "SC_HUB", "to_target": "Interconnect A" }
]
```

Address each craft **by team** (`from_team`/`to_team`) or **by asset** (`from_asset`/`to_asset`, e.g. a neutral hub) — same rules as the [`docking`](#docking-start-the-scenario-already-docked) section.

#### Requirements and restrictions

| Rule | Detail |
| --- | --- |
| **Interconnect on each side** | Both endpoints named in the connection must be `Power Interconnect` components. |
| **Local bus wiring** | Each interconnect must already appear on its own `power.bus` before the link is applied. |
| **Linked, not derived** | The pairing is **explicit** in the `docking` block; it is not inferred from docking adapters. |
| **Cross-team / neutral OK** | A neutral hub (addressed by `to_asset`) and clients on different teams link fine (the RPO hub charges all five teams this way). |

#### Recipe: hub charges many clients

The RPO scenario starts each team's client battery low (`Charge Fraction: 0.2`) and lets it top up from the neutral hub's large battery:

1. **Hub (`SC_002`, neutral):** one large `Battery`, then **one `Power Interconnect` per client** (`Interconnect A`…`E`), each fed from the battery on `power.bus`.
2. **Each client (`SC_001`):** `Battery` → `Charge Switch` (a `Power Switch` that **starts open**, `Is Open: true`) → `Interconnect`. With the switch open no current flows; the team **closes** it (`Is Open: false`) to charge from the hub.
3. **`docking` block:** one power-interconnect entry per team, each addressing the neutral hub by `to_asset`:

```json
"docking": [
  { "from_team": 111111, "from_target": "Interconnect", "to_asset": "SC_002", "to_target": "Interconnect A" }
]
```

See `scenarios/RPO/rpo.json` for the full five-client build.

---

## `components[]` — on-board hardware

This is the largest part of a scenario. Each entry instantiates one piece of hardware. The full per-class reference is in [components.md](components.md). At a glance:

```json
{
  "class":    "Camera",
  "name":     "Camera",
  "mesh":     "None",
  "enabled":  true,
  "position": [0.0, -0.36, -0.16],
  "rotation": [90.0, 0.0, 0.0],
  "scale":    1.0,
  "data":     { "Mass": 5.0 }
}
```

| Key | JSON type | Required? | Description |
| --- | --- | --- | --- |
| `class` | `string` | yes | Component class. See [components.md#class-table](components.md#class-table) for the full set. Common values: `Solar Panel`, `Battery`, `Reaction Wheels`, `Computer`, `Camera`, `Receiver`, `Transmitter`, `Storage`, `GPS Sensor`, `EM Sensor`, `Jammer`, `Magnetometer`, `Gyroscope`, `Laser Range Finder`, `External Force Torque`, `Thruster`, `Docking Adapter`, `Text`. |
| `name` | `string` | recommended | Friendly name. **Must be unique** within a spacecraft. Teams reference it via `target` in commands. Case-insensitive at runtime. If omitted, defaults to `class`. |
| `mesh` | `string` | no | Unreal mesh path, or `"None"` to use the class default. |
| `enabled` | `bool` | no (default `true`) | If `false`, the component is loaded but inactive (good for failure events that flip it on later). |
| `position` | `number[3]` (m) | no | Local-position offset from the chassis origin. |
| `rotation` | `number[3]` (deg) | no | Local rotation as Euler angles `[X, Y, Z]` (Tait–Bryan, applied in 1‑2‑3 order). |
| `scale` | `number` | no (default `1.0`) | Visual scale factor. |
| `data` | `object` | no | Class-specific tuning. `Mass` is universal (kg). See [components.md](components.md) for per-class keys. |

**`name` must be unique within a spacecraft.** Two components with the same name on the same spacecraft cannot both be addressed by uplink commands — the second will shadow the first.

---

## `collections`

`assets.collections[]` is the lookup table that maps each team's `collection` string to the spacecraft IDs that team controls.

```json
"collections": [
  { "id": "Main",  "space_assets": ["SC_001"] },
  { "id": "Rogue", "space_assets": ["SC_002"] }
]
```

| Key | JSON type | Description |
| --- | --- | --- |
| `id` | `string` | Identifier referenced by a team's `collection` field. |
| `space_assets` | `string[]` | List of spacecraft `id` values in this collection. |

A team can have multiple spacecraft (just list them all). A spacecraft can belong to multiple collections only if you genuinely want multiple teams to share it — usually you don't, so keep collections one-to-one.

The order of entries in `space_assets` determines the order spacecraft appear in [`list_assets`](../api-reference/ground-requests.md#list_assets) for that team.

---

## `neutral` (team-less shared craft)

`assets.neutral[]` is an optional top-level list of spacecraft `id` values (from `assets.space[]`) that are spawned as **neutral** craft: a single shared instance each, owned by no team.

```json
"assets": {
  "space": [
    { "id": "SC_001", "name": "Microsat", ... },
    { "id": "SC_HUB", "name": "Station",  ... }
  ],
  "collections": [
    { "id": "Main", "space_assets": ["SC_001"] }
  ],
  "neutral": ["SC_HUB"]
}
```

A neutral craft:

- **Is spawned exactly once**, regardless of how many teams are in play (unlike a `collection` asset, which spawns a separate copy per team).
- **Cannot be controlled by any team.** It has no ground controller, so no team can uplink commands to it, change its telemetry, or read its telemetry/configuration. Attempts to fetch its telemetry return an explicit error.
- **Can be referenced as a target by every team.** It appears in each team's [`list_assets`](../api-reference/ground-requests.md#list_assets) flagged `"neutral": true` / `"controllable": false`, and its public component list (names + classes) is available via [`list_entity`](../api-reference/ground-requests.md#list_entity) to any team. This makes it a valid target for [relative pointing](../api-reference/spacecraft-commands.md), [rendezvous](../api-reference/spacecraft-commands.md), and [docking](../api-reference/spacecraft-commands.md) — for example a central station with one docking port per team to latch onto.
- **Has a deterministic `asset_id`** derived from its scenario `id`, so it is stable across runs. It can be referenced either by that `asset_id` or directly by its scenario `id` string (e.g. `"SC_HUB"`) in the `spacecraft`/`target` argument of pointing, rendezvous and docking commands.

Admin tooling retains full visibility of neutral craft (telemetry, components) for monitoring and debugging.

| Key | JSON type | Description |
| --- | --- | --- |
| `neutral` | `string[]` | List of spacecraft `id` values (from `assets.space[]`) to spawn as single, shared, uncontrollable craft. Optional; omit or leave empty for none. |

---

## `docking` (start the scenario already docked)

`docking[]` is an optional **top-level** array (a sibling of `teams` and `assets`, not nested inside `assets`) that establishes connections between spacecraft components at the moment the scenario is built. Each entry is **generic**: it joins a component on one craft (`from`) to a component on another (`to`), and Studio acts on the **type** of the two components:

- **Two docking adapters** → the `from` craft is physically placed so its adapter mates with the `to` port, then the two are **docked**.
- **Two fuel interconnects** → the two interconnects are **linked** so fuel can transfer across the interface (see [Fuel interconnects](#fuel-interconnects)).
- **Two power interconnects** → the two interconnects are **linked** so the power buses bridge across the interface (see [Power interconnects](#power-interconnects)).

The classic use is a central neutral hub with one port per team, where every team begins latched on (and optionally plumbed for fuel and power).

```json
"docking": [
  { "from_team": 111111, "from_target": "Docking Adapter",  "to_asset": "SC_HUB", "to_target": "Docking A" },
  { "from_team": 111111, "from_target": "Fuel Interconnect", "to_asset": "SC_HUB", "to_target": "Fuel Interconnect A" },
  { "from_team": 111111, "from_target": "Interconnect",      "to_asset": "SC_HUB", "to_target": "Interconnect A" }
]
```

#### Addressing each endpoint

Each endpoint (`from` and `to`) names a **component** plus the spacecraft that carries it. The spacecraft is addressed in one of two ways — Studio **prefers the team** when its key is present, and falls back to the asset id otherwise:

- **By team** (`from_team` / `to_team`, an `int`): the craft in that team that owns the named component is used. This is required for a definition that is **instanced per team** (e.g. a shared client `SC_001` that exists once per team). Add `from_asset` / `to_asset` alongside it only to disambiguate when a single team owns more than one matching craft.
- **By asset** (`from_asset` / `to_asset`, a `string`): a **specific** spacecraft is resolved directly by its scenario `id` (e.g. `"SC_HUB"`) or runtime `asset_id`. This is how you address a **neutral, team-less** craft such as a shared hub, and it stays unambiguous even when several neutral assets exist because each id is unique.

So a typical hub setup uses `from_team` for each team's client and `to_asset` for the neutral hub (as above).

For a docking-adapter pair Studio finds the `from` craft, **physically places it** so its adapter mates with the `to` port (coincident position, adapter facing the port), matches the target's velocity, and then docks the two. Because docking freezes the relative pose at the instant of capture, the placement is what makes the craft start cleanly attached rather than welded together at the wrong offset.

Notes:

- For docking, **both** endpoints must be `Docking Adapter` components on spacecraft that each carry a docking adapter. The chaser only needs a `Docking Adapter` component — `enable_rpo_software` is **not** required for docking. For fuel links, **both** endpoints must be `Fuel Interconnect` components; for power links, **both** must be `Power Interconnect` components. A mismatched pair (e.g. an adapter and an interconnect) logs a warning and is skipped.
- The placement runs **once**, during scenario construction. Reloading a saved simulation restores the existing docked hierarchy instead of re-placing, so docking entries are skipped for craft that are already docked.
- A docked pair becomes a single rigid body, with the heavier craft acting as the hub. Teams can later separate using the normal undock command.

| Key | JSON type | Required | Description |
| --- | --- | --- | --- |
| `from_team` | `int` | one of team/asset | Team id of the `from` endpoint. Preferred when present. |
| `from_asset` | `string` | one of team/asset | Scenario `id` / runtime `asset_id` of the `from` craft. Used when `from_team` is absent, or as a disambiguator within a team. |
| `from_target` | `string` | yes | Name of the component (`Docking Adapter`, `Fuel Interconnect`, or `Power Interconnect`) on the `from` craft. |
| `to_team` | `int` | one of team/asset | Team id of the `to` endpoint. Preferred when present. |
| `to_asset` | `string` | one of team/asset | Scenario `id` / runtime `asset_id` of the `to` craft (e.g. a neutral hub). Used when `to_team` is absent, or as a disambiguator within a team. |
| `to_target` | `string` | yes | Name of the component (`Docking Adapter`, `Fuel Interconnect`, or `Power Interconnect`) on the `to` craft. |
| `capture_distance` | `number` | no | [m] Capture distance used when establishing a dock (docking-adapter entries only). Default `0.5`. |
| `capture_angle` | `number` | no | [deg] Capture angle used when establishing a dock (docking-adapter entries only). Default `5.0`. |

---

## Worked example

A small but complete spacecraft definition — enough to copy/paste as a starting point:

```json
{
  "id":   "SC_001",
  "name": "Microsat",
  "orbit": {
    "planet": "Earth",
    "values": [7000.0, 0.0, 51.6, 0.0, 0.0, 0.0],
    "offset": [0.0,    0.0, 0.0,  0.0, 0.0, 0.001]
  },
  "physics": {
    "override_mass":  true,
    "mass":           100.0,
    "center_of_mass": [0.0, 0.0, 0.0],
    "inertia_tensor": [[10,0,0],[0,10,0],[0,0,10]]
  },
  "visualization": {
    "mesh":   "/ZendirAssetsSpace/Blueprints/Spacecraft/ZenSat/BP_Z_SC_ZenSat_Chassis",
    "scale":  1.0,
    "offset": [0.0, 0.0, 0.12]
  },
  "controller": {
    "safe_fraction":  0.1,
    "capture_tax":    0.001,
    "downlink_tax":   0.005,
    "ping_interval":  20.0,
    "reset_interval": 60.0,
    "enable_rpo_software":     false
  },
  "power": {
    "bus": [
      { "source_component": "Solar Panel +X", "source_terminal": "out", "target_component": "Battery", "target_terminal": "out" },
      { "source_component": "Solar Panel -X", "source_terminal": "out", "target_component": "Battery", "target_terminal": "out" }
    ]
  },
  "components": [
    { "class": "Solar Panel",     "name": "Solar Panel +X", "position": [ 0.8, 0.276313, -0.2], "rotation": [35.0, 0.0, 0.0], "data": { "Area": 0.3, "Efficiency": 0.4, "Mass": 10.0 } },
    { "class": "Solar Panel",     "name": "Solar Panel -X", "position": [-0.8, 0.276313, -0.2], "rotation": [35.0, 0.0, 0.0], "data": { "Area": 0.3, "Efficiency": 0.4, "Mass": 10.0 } },
    { "class": "Reaction Wheels", "name": "Reaction Wheels", "data": { "Mass": 9.0 } },
    { "class": "Computer",        "name": "Computer",        "data": { "Mass": 2.0 } },
    { "class": "Battery",         "name": "Battery",         "data": { "Nominal Capacity": 80.0, "Charge Fraction": 0.5, "Mass": 5.0 } },
    { "class": "Camera",          "name": "Camera",          "position": [0.0, -0.36, -0.16], "rotation": [90.0, 0.0, 0.0], "data": { "Mass": 5.0 } },
    { "class": "GPS Sensor",      "name": "GPS Sensor",      "data": { "Mass": 2.0 } },
    { "class": "Receiver",        "name": "Receiver",        "data": { "Antenna Gain": 3.0, "Mass": 2.0 } },
    { "class": "Transmitter",     "name": "Transmitter",     "data": { "Mass": 1.0 } },
    { "class": "Storage",         "name": "Storage",         "data": { "Mass": 4.0 } }
  ]
}
```
