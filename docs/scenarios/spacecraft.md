# `assets.space[]` and `assets.collections[]`

The `assets` block is the part most scenario authoring time is spent on. It has two arrays:

- `assets.space[]` — the spacecraft definitions. Each entry instantiates one `ASpacecraft` actor with attached components.
- `assets.collections[]` — the lookup that maps team `collection` strings to spacecraft IDs.

Both are parsed by `SpaceAssetFromJson` / `AssetCollectionFromJson` in `studio/Plugins/SpaceRange/Source/SpaceRange/Private/Libraries/SpaceRangeDefinitionFunctionLibrary.cpp`. Each spacecraft maps to `FSpaceAssetDefinition`.

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
| Mid-LEO, slight eccentricity (used by `Orbital Sentinel`) | `[8200.0, 0.02, 17.3, 283.0, 0.0, 360.0]` |
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
  "enable_rpo":              false,
  "record_uplink_intercept": true
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
| `enable_rpo` | `bool` | `false` | `true` enables [`rendezvous`](../api-reference/spacecraft-commands.md#rendezvous) and [`docking`](../api-reference/spacecraft-commands.md#docking) for this spacecraft. Both commands return errors otherwise. |
| `record_uplink_intercept` | `bool` | `true` | If `true`, the spacecraft records uplink packets it overhears for SIGINT-style replay (downlinked as [Uplink Intercept](../reference/packet-formats.md#uplink-intercept) records). Set `false` to save memory in scenarios that do not exercise this feature. |

The `controller` block is **optional**; defaults work for most exercises. The keys that change most between scenarios are `safe_fraction` (lower for fault-injection scenarios where teams should be forced to manage power), `reset_interval` (lower for fast-paced exercises), and `enable_rpo` (only set `true` on spacecraft that need to manoeuvre).

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
| `class` | `string` | yes | Component class. See [components.md#class-table](components.md#class-table) for the full set. Common values: `Solar Panel`, `Battery`, `Reaction Wheels`, `Computer`, `Camera`, `Receiver`, `Transmitter`, `Storage`, `GPS Sensor`, `EM Sensor`, `Jammer`, `Magnetometer`, `Gyroscope`, `External Force Torque`, `Thruster`, `Docking Adapter`, `Text`. |
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
    "enable_rpo":     false
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
