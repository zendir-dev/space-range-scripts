# `events[]`: Scheduled Scenario Events

The `events[]` array is the timeline of "things that happen" once the simulation starts. Each entry fires when simulated time reaches its `Time` (and repeats on `Interval` when `Repeat` is true).

Three event types exist:

| `Type` | Purpose |
| --- | --- |
| `Spacecraft` | Inject a fault, mode change or property change on one or more spacecraft components. |
| `GPS` | Add/remove a GPS spoofing region or jamming source on the global GPS subsystem. |
| `Cyber` | Apply packet-level telemetry tampering overlays (APID-targeted byte patching in CCSDS user data). |

There is no `Ground` or `Scenario` event type: older docs may mention them. Only `Spacecraft`, `GPS`, and `Cyber` are supported; other `Type` values fall back to `Spacecraft` with a warning.

## Common Fields

Every event uses the same outer shape. Field names are case-insensitive when loaded; the Studio **Add Event** templates use PascalCase, so prefer that for consistency:

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `Enabled` | `boolean` | `true` | Disabled events are loaded but never fire. Useful while authoring. |
| `Name` | `string` | `"Event"` | Human-readable label. Surfaced in admin tools and logs. Must be unique within the scenario for clean log output. |
| `Time` | `number` (s) | `0.0` | Simulation seconds (since epoch) at which the event fires. |
| `Repeat` | `boolean` | `false` | If `true`, the event fires again every `Interval` seconds. |
| `Interval` | `number` (s) | `1.0` | Repeat period when `Repeat: true`. Ignored otherwise. |
| `Type` | `string` | `"Spacecraft"` | One of `Spacecraft`, `GPS`, `Cyber` (case-insensitive). The string `"failure"` is also accepted as an alias for `Spacecraft`. |
| `Assets` | `string[]` | `[]` | Asset IDs the event applies to (matches `assets.space[].id`). Empty `[]` means **all** spacecraft. Used by `Spacecraft` and `Cyber`; ignored by `GPS`. |
| `Target` | `string` | `""` | `Spacecraft`: component/error-model target. `Cyber`: currently must be `Spacecraft` (case-insensitive). `GPS`: ignored. |
| `Data` | `object` | `{}` | A flat map of keys to string-or-number values. Schema depends on `Type`: see sections below. |

Keep `Data` keys **flat**: do not nest objects inside `Data`. Avoid `.` in key names unless you intend a dotted lookup (unusual for events).

---

## Spacecraft Events

A `Spacecraft` event injects state into one or more components on the spacecraft.

### How Targeting Works

When a `Spacecraft` event fires:

1. Studio first tries `Target` as a full **component name** (`components[].name`). Names that contain a hyphen: `"Thruster 4 (-X)"`, `"Solar Panel -X"`: match that one component and are not split.
2. If the full string does not resolve, Studio splits `Target` on the first `-` into **component** and optional **error model**, then resolves the left side by name or **class alias** (`Battery`, `Solar Panel`, `Reaction Wheels`, …). See [`components.md`](./components.md) for aliases.
3. Spaces are stripped from each `Data` key before matching (`"Bit Rate"` → `BitRate`).
4. Values are applied to every matching component on every spacecraft listed in `Assets` (or all spacecraft if `Assets` is empty). Unknown `Target` strings do not fall through to every component.

If there is **no** error-model suffix, `Data` keys set **direct properties** on the component (e.g. `Capacity`, `Bit Rate`, `Stuck Index`, `Fault State`).

If an error-model suffix is present (e.g. `Battery-IntermittentConnectionErrorModel`), `Data` keys set properties on that **error model** attached to the component.

### Spacecraft Event Target Syntax

```text
<ComponentNameOrClass>[-<ErrorModelClassName>]
```

Examples:

| `Target` | What gets touched |
| --- | --- |
| `"Storage"` | The `Storage` extension on every storage component. Sets direct properties (e.g. `Capacity`). |
| `"Battery-IntermittentConnectionErrorModel"` | The `IntermittentConnectionErrorModel` on every battery. |
| `"Solar Panel-SolarPanelDegradationErrorModel"` | Spaces in the class alias are fine: they are matched in `GetPhysicalObjectClass`. |
| `"GPS Sensor"` | The GPS sensor component (matched on its class alias). |
| `"chassis_panel_a"` | The component whose `name` is `chassis_panel_a` (whatever class it happens to be). |
| `"Thruster 4 (-X)"` | The thruster whose `name` is `Thruster 4 (-X)`. The hyphen is part of the name, not an error-model separator. |

Restrict the impact to specific spacecraft via `Assets`:

```json
"Assets": ["alpha", "bravo"]
```

If `Assets` is omitted or empty, the event runs on **every** spacecraft in the scenario. Use this for global anomalies (e.g. solar flare); use a single-element array for per-team faults.

### Spacecraft Event `Data`

`Data` is a flat string-or-number map. Keys must match the property names the component or error model expects, with spaces stripped before matching. Booleans, integers, floats, and strings are all accepted in JSON.

### Canonical Spacecraft Event Recipes

These match the Studio **Add Event → Spacecraft** templates. Use them as-is or adjust the numbers.

### Storage: Fill the Disk to Force a Downlink

```json
{
  "Enabled": true, "Name": "Storage Full", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "Storage", "Assets": [],
  "Data": { "Capacity": 100000 }
}
```

`Capacity` is in **bytes** (the partitioned storage extension reads it as the new max capacity).

### Storage: Corrupt Stored Data

```json
{
  "Enabled": true, "Name": "Storage Corruption", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "Storage", "Assets": [],
  "Data": { "Corruption Fraction": 0.1, "Corruption Intensity": 0.2 }
}
```

### Transmitter: Drop the Bit-Rate

```json
{
  "Enabled": true, "Name": "Low Bit Rate", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "Transmitter", "Assets": [],
  "Data": { "Bit Rate": 500.0 }
}
```

`Bit Rate` is in bits/sec.

### Transmitter: Packet Corruption (Error Model)

```json
{
  "Enabled": true, "Name": "Packet Corruption", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft",
  "Target": "Transmitter-TransmitterPacketCorruptionErrorModel",
  "Assets": [],
  "Data": { "Packet Corruption Fraction": 0.2 }
}
```

### Solar Panel: Degradation

```json
{
  "Enabled": true, "Name": "Faulty Solar Panel", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft",
  "Target": "SolarPanel-SolarPanelDegradationErrorModel",
  "Assets": [],
  "Data": { "Degradation Rate": 100000.0 }
}
```

### Battery: Intermittent Connection (Power Spikes)

```json
{
  "Enabled": true, "Name": "Battery Power Spikes", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft",
  "Target": "Battery-IntermittentConnectionErrorModel",
  "Assets": [],
  "Data": { "Intermittent Mean": 1, "Intermittent Std": 2 }
}
```

### Battery: Leak

```json
{
  "Enabled": true, "Name": "Battery Leak", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft",
  "Target": "Battery-BatteryLeakageErrorModel",
  "Assets": [],
  "Data": { "Power Leakage Rate": 0.001 }
}
```

`Power Leakage Rate` is fraction-of-stored-energy per second.

### Computer: Guidance Noise

```json
{
  "Enabled": true, "Name": "Pointing Error", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft",
  "Target": "Computer-GuidanceComputerNoiseErrorModel",
  "Assets": [],
  "Data": { "Noise Factor": 0.005, "Randomize": true }
}
```

### Sensor Fault States

`Magnetometer`, `GPS Sensor`, `EM Sensor` (and any other `ASensorBase` subclass) use a `Fault State` integer that maps to an `EFaultState` enum on the sensor (`0 = Healthy`, other values depend on the sensor: typical mappings include stuck-at, biased, noisy, dead).

### Faulty GPS Sensor

```json
{
  "Enabled": true, "Name": "Faulty GPS", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "GPS Sensor",
  "Data": { "Fault State": 4 }
}
```

### Faulty Magnetometer

```json
{
  "Enabled": true, "Name": "Faulty Magnetometer", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "Magnetometer", "Assets": [],
  "Data": { "Fault State": 3 }
}
```

### Faulty EM Sensor

```json
{
  "Enabled": true, "Name": "Faulty EM Sensor", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "EM Sensor", "Assets": [],
  "Data": { "Fault State": 3 }
}
```

`Gyroscope` accepts the same `Fault State` parameter: substitute the `Target` and you have a faulty-gyro recipe.

### Reaction Wheels: Stuck Index

```json
{
  "Enabled": true, "Name": "Reaction Wheel Stuck", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "Reaction Wheels", "Assets": [],
  "Data": { "Stuck Index": 0 }
}
```

`Stuck Index` is `0`, `1`, `2`, or `3` (which wheel jams).

### Reaction Wheels: Restore a Stuck Wheel

The Studio **Add Event → Spacecraft** menu also includes a recovery event. Set `Nominal Index` to the same wheel index to return that wheel to nominal operation:

```json
{
  "Enabled": true, "Name": "Reaction Wheel Nominal", "Time": 200.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "Reaction Wheels", "Assets": [],
  "Data": { "Nominal Index": 0 }
}
```

Use separate events for separate wheel indices. Pairing a stuck event with a later nominal event is useful in training scenarios where operators are expected to diagnose the fault before recovery.

### Thruster: Unexpected Fire

Triggers a thruster to fire without an operator command. Useful for simulating propulsion anomalies during proximity operations.

```json
{
  "Enabled": true, "Name": "Unexpected Thruster Fire", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "Thruster 1 (+X)", "Assets": [],
  "Data": { "Active": true, "Duration": 30.0 }
}
```

| `Data` key | Type | Description |
| --- | --- | --- |
| `Active` | `boolean` | `true` starts the fire, `false` stops it. Default `true` if `Duration` > 0. |
| `Duration` | `number` (s) | How long the thruster should fire. |

To stop an unexpected fire early, use a follow-up event with `Active: false` or `Duration: 0`.

### Thruster: Failed Off (Dispersed Factor)

Sets a thruster's `Dispersed Factor` to 1.0, causing it to produce no thrust when commanded. The command is accepted but the delivered force is zero.

```json
{
  "Enabled": true, "Name": "Thruster Failed Off", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "Thruster 1 (+X)", "Assets": [],
  "Data": { "Dispersed Factor": 1.0 }
}
```

| `Data` key | Type | Description |
| --- | --- | --- |
| `Dispersed Factor` | `number` (0–1) | Fraction of thrust lost. `1.0` = complete loss. `0.5` = half thrust. |

This models permanent thruster failure. The `reset` command does not restore thruster performance.

### Rendezvous: Automatic Approach

Routes a timed spacecraft event through the same rendezvous and proximity operations (RPO) handler used by operator commands. This is useful for automatically beginning a proximity or docking approach after the simulation starts.

```json
{
  "Enabled": true, "Name": "Automatic Docking Approach", "Time": 5.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "Rendezvous",
  "Assets": ["SC_SERVICER"],
  "Data": {
    "Target": "SC_CLIENT",
    "Active": true,
    "Component": "Docking Adapter",
    "Dock": true,
    "Offset X": 0.0,
    "Offset Y": 0.0,
    "Offset Z": 0.0
  }
}
```

| `Data` key | Type | Description |
| --- | --- | --- |
| `Target` | `string` | Scenario asset id of the target spacecraft. It is resolved to the matching runtime asset within each team. |
| `Active` | `boolean` | `true` starts the perch maneuver; `false` cancels it. |
| `Component` | `string` | Optional component name on both spacecraft, normally `Docking Adapter`. Anchors the perch so those components close, not the spacecraft origins. |
| `Dock` | `boolean` | When present, routes through the docking handler too. `true` calls `SetDockingTarget` and arms both adapters bidirectionally, and points the chaser docking port at the target (`relative` guidance) so capture-angle checks can succeed. `false` undocks. |
| `Offset X/Y/Z` | `number` (m) | Desired local vertical/local horizontal (LVLH) perch offset relative to the target. |

The chaser must have `enable_rpo_software: true`. If that spacecraft also has thrusters, the perch is flown through a `Thruster Array`; otherwise SpaceRange uses a dedicated `External Force Torque`. Use `Assets` to target only the chaser definition; otherwise every RPO-enabled spacecraft will attempt the maneuver.

### Guidance: Automatic Pointing

Routes a timed spacecraft event through the same guidance handler used by operator commands. Use this to slew a chaser onto a docking port before translation starts, so reaction wheels are already holding alignment.

```json
{
  "Enabled": true, "Name": "Align Docking Adapters", "Time": 1.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "Guidance",
  "Assets": ["SC_SERVICER"],
  "Data": {
    "Pointing": "relative",
    "Target": "Docking Adapter",
    "Alignment": "+z",
    "Spacecraft": "SC_CLIENT",
    "Component": "Docking Adapter"
  }
}
```

| `Data` key | Type | Description |
| --- | --- | --- |
| `Pointing` | `string` | Same values as the [`guidance`](../api-reference/spacecraft-commands.md#guidance) command (`relative`, `nadir`, `velocity`, …). |
| `Target` | `string` | Component on **this** spacecraft whose axis should align (normally `Docking Adapter`). |
| `Alignment` | `string` | Axis of that component (`+z` is the docking-adapter capture axis). |
| `Spacecraft` | `string` | For `relative` pointing: scenario asset id of the other spacecraft, resolved per team. |
| `Component` | `string` | Optional aim point on the other spacecraft (normally `Docking Adapter`). |

For error-model events, each `Data` key must match a property that error model exposes (spaces stripped). If a key is wrong, the event may no-op for that component: test in Studio with a low `Time` first.

---

## GPS Events

`GPS` events configure spoofing regions and jamming sources on the global GPS constellation. They ignore `Target` and `Assets`: the only relevant fields are `Time`, `Repeat`, `Interval`, and `Data`.

`Data.Type` selects the sub-mode and is **required**:

| `Data.Type` | Effect |
| --- | --- |
| `Spoofing` | Configure (or clear) a single global spoofing region. |
| `Jamming` | `add`, `update` or `remove` a jamming source on the GPS environment. |

### Spoofing

Spoofing replaces the apparent receiver position whenever the receiver is inside a sphere centered on `Origin`, returning a fix at `Spoof` instead. Position can be supplied either in planet-centered inertial (PCI) Cartesian coordinates (`Origin X/Y/Z`, `Spoof X/Y/Z`) or geodetic coordinates (`Origin Latitude/Longitude/Altitude`, `Spoof Latitude/Longitude/Altitude`). If any geodetic field is non-zero, it overrides the Cartesian values.

| `Data` key | Type | Default | Description |
| --- | --- | --- | --- |
| `Type` | `"Spoofing"` | _(required)_ | Selects spoofing mode. |
| `Enabled` | `boolean` | `true` | Set to `false` to clear all spoofing. When `false`, all other keys are ignored. |
| `Origin X` / `Origin Y` / `Origin Z` | `number` (m, PCI) | `0` | Center of the spoofing region in PCI (planet-centered inertial) meters. |
| `Origin Latitude` / `Origin Longitude` / `Origin Altitude` | `number` (deg, deg, m) | `0` | Geodetic center. Overrides Cartesian if any of the three is non-zero. |
| `Radius` | `number` (m) | `100000.0` | Radius of the spoofing region around `Origin`. |
| `Spoof X` / `Spoof Y` / `Spoof Z` | `number` (m, PCI) | `0` | The PCI position the receiver will report. |
| `Spoof Latitude` / `Spoof Longitude` / `Spoof Altitude` | `number` (deg, deg, m) | `0` | Geodetic spoofed position. Overrides Cartesian if any is non-zero. |

### Spoofing: Cartesian (PCI)

```json
{
  "Enabled": true, "Name": "GPS Spoof Region", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "GPS",
  "Data": {
    "Type": "Spoofing",
    "Enabled": true,
    "Origin X": 100000.0,
    "Origin Y": 7200000.0,
    "Origin Z": -100000.0,
    "Radius": 50000.0,
    "Spoof X": 200000.0,
    "Spoof Y": -6700000.0,
    "Spoof Z": -50000.0
  }
}
```

### Spoofing: Geodetic

```json
{
  "Enabled": true, "Name": "Spoof San Francisco", "Time": 200.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "GPS",
  "Data": {
    "Type": "Spoofing",
    "Enabled": true,
    "Origin Latitude": 37.7749,
    "Origin Longitude": -122.4194,
    "Origin Altitude": 500000.0,
    "Radius": 50000.0,
    "Spoof Latitude": -37.7749,
    "Spoof Longitude": 122.4194,
    "Spoof Altitude": 20000.0
  }
}
```

To **clear** spoofing later, fire a follow-up event with `Enabled: false`:

```json
{
  "Enabled": true, "Name": "Spoof Off", "Time": 1200.0,
  "Type": "GPS",
  "Data": { "Type": "Spoofing", "Enabled": false }
}
```

### Jamming

Jamming maintains a list of point jammers on the GPS environment message. `Data.Action` selects the operation:

| `Action` | Required | Description |
| --- | --- | --- |
| `add` | jammer position, ERP | Append a new jammer to the list. The new index is `length-1` after the operation. |
| `update` | `Index`, fields to change | Modify an existing jammer in place. Any omitted field keeps its current value. |
| `remove` | `Index` | Delete the jammer at the given index. Subsequent indices shift down. |

Common fields (used by `add` and `update`):

| `Data` key | Type | Default | Description |
| --- | --- | --- | --- |
| `Jammer X` / `Jammer Y` / `Jammer Z` | `number` (m, PCI) | `0` | Cartesian PCI position. |
| `Jammer Latitude` / `Jammer Longitude` / `Jammer Altitude` | `number` (deg, deg, m) | `0` | Geodetic position. Overrides Cartesian if any is non-zero. |
| `ERP` _or_ `Effective Radiated Power` | `number` (W) | `0` | Effective radiated power. Either alias is accepted. |
| `Boresight X` / `Boresight Y` / `Boresight Z` | `number` (unit vector) | `0,0,0` | Direction of the jammer's main lobe. Use `0,0,0` for an isotropic jammer. |
| `Beam Half Angle` | `number` (deg) | `0` | Half-width of the main lobe. `0` = isotropic. |
| `Path Loss Exponent` | `number` | `2.0` | Free-space path-loss exponent (`2.0` = inverse-square). |
| `Index` | `integer` | _(required for `update`/`remove`)_ | Zero-based jammer index. |
| `Enabled` | `boolean` | `true` | (`update` only) Disable a jammer without removing it. |

### Add an ECI Jammer at GEO

```json
{
  "Enabled": true, "Name": "GPS Jamming Add", "Time": 100.0,
  "Type": "GPS",
  "Data": {
    "Type": "Jamming",
    "Action": "add",
    "Jammer X": 12000000.0, "Jammer Y": 0.0, "Jammer Z": 0.0,
    "ERP": 500000.0,
    "Boresight X": 0.0, "Boresight Y": 0.0, "Boresight Z": 0.0,
    "Beam Half Angle": 0.0,
    "Path Loss Exponent": 2.0
  }
}
```

### Add a Ground Jammer (Geodetic)

```json
{
  "Enabled": true, "Name": "Jam Los Angeles", "Time": 100.0,
  "Type": "GPS",
  "Data": {
    "Type": "Jamming",
    "Action": "add",
    "Jammer Latitude": 34.05,
    "Jammer Longitude": -118.25,
    "Jammer Altitude": 500000.0,
    "Effective Radiated Power": 250000.0
  }
}
```

### Update a Jammer (Move It, Change ERP)

```json
{
  "Enabled": true, "Name": "Move Jammer", "Time": 200.0,
  "Type": "GPS",
  "Data": {
    "Type": "Jamming",
    "Action": "update",
    "Index": "0",
    "Jammer X": 13000000.0, "Jammer Y": 100000.0, "Jammer Z": -50000.0,
    "Enabled": "true",
    "ERP": 750000.0
  }
}
```

`Index` is parsed as a string in the canonical templates because `Data` values round-trip through `TMap<FString, FString>`. Either `"0"` or `0` works in JSON.

### Disable a Jammer Without Removing It

```json
{
  "Enabled": true, "Name": "Jam Off", "Time": 600.0,
  "Type": "GPS",
  "Data": { "Type": "Jamming", "Action": "update", "Index": "0", "Enabled": "false" }
}
```

### Remove a Jammer

```json
{
  "Enabled": true, "Name": "Jam Cleanup", "Time": 700.0,
  "Type": "GPS",
  "Data": { "Type": "Jamming", "Action": "remove", "Index": "0" }
}
```

---

## Cyber Events

`Cyber` events apply byte overlays to telemetry payload bytes for selected spacecraft. The patch runs **after** normal packet serialization and **before** downlink encryption/transmit, so packet headers remain valid while user-data contents are tampered.

Current target support:

- `Target: "Spacecraft"` (case-insensitive) is supported.
- Other targets are currently ignored with a warning.

`Assets` works the same way as `Spacecraft` events: empty means all spacecraft, otherwise only listed asset IDs are affected.

### `Cyber` `Data` Keys

| `Data` key | Type | Default | Description |
| --- | --- | --- | --- |
| `APID` | `integer` | _(required)_ | CCSDS APID to match (`0..2047`). |
| `SubType` | `integer` | `-1` | Secondary-header subtype filter. `-1` means "any subtype". |
| `Offset Bytes` | `integer` | `0` | Byte offset from the start of CCSDS **user data** (not packet start). |
| `Payload` | `string` | _(required)_ | Source text to encode/decode into overlay bytes. |
| `Encoding` | `string` | `ascii` | One of `ascii`, `utf8`, `hex`, `base64` (case-insensitive). |
| `Expiry Seconds` | `number` | `0.0` | Lifetime after event trigger. `0` means never expires. |
| `Clear On Reset` | `boolean` | `false` | If true, reset can clear the overlay (see reset behavior below). |

Notes:

- If `Encoding` is unknown, runtime falls back to `ascii` and logs a warning.
- If `hex`/`base64` decoding fails, the event no-ops for that asset and logs a warning.
- If the payload would run past the packet end, bytes are truncated to fit.
- Overlapping overlays resolve by apply order (later overlays win on overlapping bytes).

### Reset Behavior (`Clear On Reset`)

When `Clear On Reset` is `true`:

- Resetting `Computer` clears all resettable cyber overlays on that asset.
- Resetting another component clears only resettable overlays whose `SubType` matches that component subtype.

### Canonical `Cyber` Examples

Templates are available from Studio **Add Event → Cyber**.

### ASCII Patch on Ping (APID 100)

```json
{
  "Enabled": true, "Name": "Ping ASCII", "Time": 100.0,
  "Type": "Cyber", "Target": "Spacecraft", "Assets": [],
  "Data": {
    "APID": 100,
    "SubType": 0,
    "Offset Bytes": 0,
    "Payload": "HELLO",
    "Encoding": "ascii",
    "Expiry Seconds": 120.0,
    "Clear On Reset": true
  }
}
```

### Hex Patch on Ping

```json
{
  "Enabled": true, "Name": "Ping Hex", "Time": 220.0,
  "Type": "Cyber", "Target": "Spacecraft", "Assets": [],
  "Data": {
    "APID": 100,
    "Offset Bytes": 12,
    "Payload": "46 4C 41 47 7B 48 45 58 5F 48 49 4E 54 7D",
    "Encoding": "hex",
    "Expiry Seconds": 0.0,
    "Clear On Reset": false
  }
}
```

### Base64 Patch (Any Subtype)

```json
{
  "Enabled": true, "Name": "Ping Base64", "Time": 340.0,
  "Type": "Cyber", "Target": "Spacecraft", "Assets": [],
  "Data": {
    "APID": 100,
    "SubType": -1,
    "Offset Bytes": 24,
    "Payload": "Q09ERS0xMjM0NQ==",
    "Encoding": "base64",
    "Expiry Seconds": 90.0,
    "Clear On Reset": true
  }
}
```

---

## Authoring Tips

- **Order events in the array by `Time`** for readability. The runtime sorts them internally, but it's much easier to spot mistakes when the JSON is in chronological order.
- **Disable, don't delete.** When iterating, set `"Enabled": false` rather than removing an event: that way the data stays alongside related events for context.
- **Pair every fault with a recovery, where it matters.** A spoofing region that never clears or a jammer that never disables is fine for an exam, but in a training scenario you almost always want a follow-up event that reverts state.
- **Use `Repeat` sparingly.** It's most useful for slow-running stochastic faults (e.g. random packet corruption pulses every 60 s). For a one-shot fault, leave `Repeat: false`.
- **Validate your `Target` strings.** Open the spacecraft's `components[]` and confirm the component name or class alias actually exists. A typo silently no-ops because `GetTargets` returns an empty list.
- **Keep `Data` values JSON-typed where possible** (`true`/`false`, numbers) rather than stringified: both work, but typed values document intent better. The runtime stringifies everything internally.

---

## See Also

- [`questions.md`](./questions.md): define what teams have to figure out about your events.
- [`components.md`](./components.md): class-alias table for `Target` strings.
- Studio **Add Event** menu: canonical Spacecraft, GPS, and Cyber templates to copy from.
