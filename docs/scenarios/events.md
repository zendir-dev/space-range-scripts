# `events[]` — scheduled scenario events

The `events[]` array is the timeline of "things that happen" once the simulation starts. Each entry is an `FScenarioEvent` (`studio/Plugins/SpaceRange/Source/SpaceRange/Public/Structs/ScenarioEvent.h`) parsed by `FScenarioEvent::LoadFromJson` and dispatched by `USpaceRangeSubsystem` once `simulation.time` reaches the event's `Time`.

Two event types exist:

| `Type` | Purpose |
| --- | --- |
| `Spacecraft` | Inject a fault, mode change or property change on one or more spacecraft components. |
| `GPS` | Add/remove a GPS spoofing region or jamming source on the global GPS subsystem. |

There is no `Ground` or `Scenario` event type — older docs may mention them, but the current `EScenarioEventType` enum (`studio/.../Enums/ScenarioEventType.h`) only lists `Spacecraft` and `GPS`. Anything else falls back to `Spacecraft` with a warning.

## Common fields

Every event uses the same outer shape. Field names parse case-insensitively (`UJSONLibrary` is case-insensitive), but the canonical examples in `Plugins/SpaceRange/Resources/Events/*.json` use PascalCase, so prefer that for consistency:

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `Enabled` | `boolean` | `true` | Disabled events are loaded but never fire. Useful while authoring. |
| `Name` | `string` | `"Event"` | Human-readable label. Surfaced in admin tools and logs. Must be unique within the scenario for clean log output. |
| `Time` | `number` (s) | `0.0` | Simulation seconds (since epoch) at which the event fires. |
| `Repeat` | `boolean` | `false` | If `true`, the event fires again every `Interval` seconds. |
| `Interval` | `number` (s) | `1.0` | Repeat period when `Repeat: true`. Ignored otherwise. |
| `Type` | `string` | `"Spacecraft"` | One of `Spacecraft`, `GPS` (case-insensitive). The string `"failure"` is also accepted as an alias for `Spacecraft`. |
| `Assets` | `string[]` | `[]` | Asset IDs the event applies to (matches `assets.space[].id`). Empty `[]` means **all** spacecraft. Only relevant for `Spacecraft` events; ignored for `GPS`. |
| `Target` | `string` | `""` | (Spacecraft only) Component to act on, optionally with an error model. See [Target syntax](#spacecraft-event-target-syntax). |
| `Data` | `object` | `{}` | A flat map of keys to string-or-number values. Schema depends on `Type` — see sections below. |

> The runtime stores `Data` as a `TMap<FString, FString>`. Internally, `.` in keys is rewritten to `$.` to prevent `UJSONLibrary` from interpreting them as nested lookups. Keep your JSON keys flat — do not nest objects inside `Data`.

## Spacecraft events

A `Spacecraft` event injects state into one or more components on the spacecraft.

### Pipeline

When the event fires (`USpacecraftController::ExecuteEvent`):

1. Split `Target` on the first `-` into `<component>` and `<error_model>`.
2. Resolve `<component>` to physical objects on the spacecraft. Match is **case-insensitive** by either:
   - Component **name** (the `name` field on the component asset), or
   - Component **class alias** (`Battery`, `Solar Panel`, `Reaction Wheels`, …) resolved via `USpaceRangeLibrary::GetPhysicalObjectClass`. See [`components.md`](./components.md) for the full alias table.
3. Strip spaces from each `Data` key (so `"Bit Rate"` becomes `BitRate`).
4. Pass the data map and `<error_model>` (may be empty) to the matching `UBaseExtension::Failure(...)` on every resolved component.

If `<error_model>` is empty, the extension treats keys as **direct property names** on the component (or its base extension) and assigns each value via `UVariableLibrary`. Common targets: `Capacity`, `Bit Rate`, `Stuck Index`, `Fault State`, etc.

If `<error_model>` is non-empty, the extension finds (or creates) the named `UErrorModelBase` subobject on the component and assigns properties on it instead.

### Spacecraft event Target syntax

```text
<ComponentNameOrClass>[-<ErrorModelClassName>]
```

Examples:

| `Target` | What gets touched |
| --- | --- |
| `"Storage"` | The `Storage` extension on every storage component. Sets direct properties (e.g. `Capacity`). |
| `"Battery-IntermittentConnectionErrorModel"` | The `IntermittentConnectionErrorModel` on every battery. |
| `"Solar Panel-SolarPanelDegradationErrorModel"` | Spaces in the class alias are fine — they are matched in `GetPhysicalObjectClass`. |
| `"GPS Sensor"` | The GPS sensor component (matched on its class alias). |
| `"chassis_panel_a"` | The component whose `name` is `chassis_panel_a` (whatever class it happens to be). |

Restrict the impact to specific spacecraft via `Assets`:

```json
"Assets": ["alpha", "bravo"]
```

> If `Assets` is omitted or empty, the event runs on **every** spacecraft in the scenario. Use this for global anomalies (e.g. solar flare); use a single-element array for per-team faults.

### Spacecraft event `Data`

`Data` is a flat string-or-number map. Keys correspond to `UPROPERTY` names on either the targeted component, its `UBaseExtension`, or its `UErrorModelBase` subobject — with spaces stripped before matching. `bool`, `int`, `float`, `double`, `FString` and `enum` properties are all accepted; `UVariableLibrary::CreateVariantFromString` does the conversion.

### Canonical Spacecraft event recipes

These are taken verbatim from `Plugins/SpaceRange/Resources/Events/Spacecraft.json` and represent the supported templates. Use them as-is or adjust the numbers.

#### Storage — fill the disk to force a downlink

```json
{
  "Enabled": true, "Name": "Storage Full", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "Storage", "Assets": [],
  "Data": { "Capacity": 100000 }
}
```

`Capacity` is in **bytes** (the partitioned storage extension reads it as the new max capacity).

#### Storage — corrupt stored data

```json
{
  "Enabled": true, "Name": "Storage Corruption", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "Storage", "Assets": [],
  "Data": { "Corruption Fraction": 0.1, "Corruption Intensity": 0.2 }
}
```

#### Transmitter — drop the bit-rate

```json
{
  "Enabled": true, "Name": "Low Bit Rate", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "Transmitter", "Assets": [],
  "Data": { "Bit Rate": 500.0 }
}
```

`Bit Rate` is in bits/sec.

#### Transmitter — packet corruption (error model)

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

#### Solar Panel — degradation

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

#### Battery — intermittent connection (power spikes)

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

#### Battery — leak

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

#### Computer — guidance noise

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

#### Sensors — fault states

`Magnetometer`, `GPS Sensor`, `EM Sensor` (and any other `ASensorBase` subclass) use a `Fault State` integer that maps to an `EFaultState` enum on the sensor (`0 = Healthy`, other values depend on the sensor — typical mappings include stuck-at, biased, noisy, dead).

##### Faulty GPS Sensor

```json
{
  "Enabled": true, "Name": "Faulty GPS", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "GPS Sensor",
  "Data": { "Fault State": 4 }
}
```

##### Faulty Magnetometer

```json
{
  "Enabled": true, "Name": "Faulty Magnetometer", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "Magnetometer", "Assets": [],
  "Data": { "Fault State": 3 }
}
```

##### Faulty EM Sensor

```json
{
  "Enabled": true, "Name": "Faulty EM Sensor", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "EM Sensor", "Assets": [],
  "Data": { "Fault State": 3 }
}
```

`Gyroscope` accepts the same `Fault State` parameter — substitute the `Target` and you have a faulty-gyro recipe.

#### Reaction Wheels — stuck index

```json
{
  "Enabled": true, "Name": "Reaction Wheel Stuck", "Time": 100.0,
  "Repeat": false, "Interval": 1.0,
  "Type": "Spacecraft", "Target": "Reaction Wheels", "Assets": [],
  "Data": { "Stuck Index": 0 }
}
```

`Stuck Index` is `0`, `1`, `2`, or `3` (which wheel jams).

> Newer error models added to `Plugins/SpaceRange/Source/SpaceRange/Private/Extensions/*ErrorModel*.cpp` will accept whatever properties they declare. The reliable rule is: a key in `Data` is the property name on the target with spaces stripped. Open the matching `*Extension.cpp` to see what properties are declared.

## GPS events

`GPS` events configure spoofing regions and jamming sources on the global `UGlobalPositioningSystem`. They ignore `Target` and `Assets` — the only relevant fields are `Time`, `Repeat`, `Interval` and `Data`. The dispatch logic lives in `USpaceRangeSubsystem::ExecuteGPSEvent`.

`Data.Type` selects the sub-mode and is **required**:

| `Data.Type` | Effect |
| --- | --- |
| `Spoofing` | Configure (or clear) a single global spoofing region. |
| `Jamming` | `add`, `update` or `remove` a jamming source on the GPS environment. |

### Spoofing

Spoofing replaces the apparent receiver position whenever the receiver is inside a sphere centred on `Origin`, returning a fix at `Spoof` instead. Position can be supplied either in PCI Cartesian coordinates (`Origin X/Y/Z`, `Spoof X/Y/Z`) or geodetic (`Origin Latitude/Longitude/Altitude`, `Spoof Latitude/Longitude/Altitude`). If any geodetic field is non-zero it overrides the Cartesian values.

| `Data` key | Type | Default | Description |
| --- | --- | --- | --- |
| `Type` | `"Spoofing"` | _(required)_ | Selects spoofing mode. |
| `Enabled` | `boolean` | `true` | Set to `false` to clear all spoofing. When `false`, all other keys are ignored. |
| `Origin X` / `Origin Y` / `Origin Z` | `number` (m, PCI) | `0` | Centre of the spoofing region in PCI (planet-centred inertial) metres. |
| `Origin Latitude` / `Origin Longitude` / `Origin Altitude` | `number` (deg, deg, m) | `0` | Geodetic centre. Overrides Cartesian if any of the three is non-zero. |
| `Radius` | `number` (m) | `100000.0` | Radius of the spoofing region around `Origin`. |
| `Spoof X` / `Spoof Y` / `Spoof Z` | `number` (m, PCI) | `0` | The PCI position the receiver will report. |
| `Spoof Latitude` / `Spoof Longitude` / `Spoof Altitude` | `number` (deg, deg, m) | `0` | Geodetic spoofed position. Overrides Cartesian if any is non-zero. |

##### Spoofing — Cartesian (PCI)

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

##### Spoofing — geodetic

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

#### Add an ECI jammer at GEO

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

#### Add a ground jammer (geodetic)

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

#### Update a jammer (move it, change ERP)

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

> `Index` is parsed as a string in the canonical templates because `Data` values round-trip through `TMap<FString, FString>`. Either `"0"` or `0` works in JSON.

#### Disable a jammer without removing it

```json
{
  "Enabled": true, "Name": "Jam Off", "Time": 600.0,
  "Type": "GPS",
  "Data": { "Type": "Jamming", "Action": "update", "Index": "0", "Enabled": "false" }
}
```

#### Remove a jammer

```json
{
  "Enabled": true, "Name": "Jam Cleanup", "Time": 700.0,
  "Type": "GPS",
  "Data": { "Type": "Jamming", "Action": "remove", "Index": "0" }
}
```

## Authoring tips

- **Order events in the array by `Time`** for readability. The runtime sorts them internally, but it's much easier to spot mistakes when the JSON is in chronological order.
- **Disable, don't delete.** When iterating, set `"Enabled": false` rather than removing an event — that way the data stays alongside related events for context.
- **Pair every fault with a recovery, where it matters.** A spoofing region that never clears or a jammer that never disables is fine for an exam, but in a training scenario you almost always want a follow-up event that reverts state.
- **Use `Repeat` sparingly.** It's most useful for slow-running stochastic faults (e.g. random packet corruption pulses every 60 s). For a one-shot fault, leave `Repeat: false`.
- **Validate your `Target` strings.** Open the spacecraft's `components[]` and confirm the component name or class alias actually exists. A typo silently no-ops because `GetTargets` returns an empty list.
- **Keep `Data` values JSON-typed where possible** (`true`/`false`, numbers) rather than stringified — both work, but typed values document intent better. The runtime stringifies everything internally.

## See also

- [`questions.md`](./questions.md) — define what teams have to figure out about your events.
- [`components.md`](./components.md) — class-alias table for `Target` strings.
- `studio/Plugins/SpaceRange/Resources/Events/Spacecraft.json` — canonical Spacecraft event templates (also surfaced in admin UI).
- `studio/Plugins/SpaceRange/Resources/Events/GPS.json` — canonical GPS event templates.
