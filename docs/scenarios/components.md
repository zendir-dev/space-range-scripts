# Components reference

Every entry in a spacecraft's `components[]` array becomes one `APhysicalObject` actor on that spacecraft. The `class` field selects which simulation module is constructed — see the table below for the full list of accepted classes and their aliases.

The `data` object is **class-specific** tuning. `Mass` is the only universal key (every component has mass). Other keys map directly to C++ properties on the underlying class, with whitespace ignored when matching (`"Antenna Gain"` matches the `AntennaGain` property).

This page documents the data fields used by every shipped scenario plus every class-specific extension override surfaced through `Setup_Impl` (initial-load) and `Failure_Impl` (event-driven mutation).

---

## Class table

The `class` field is matched case-insensitive after spaces are stripped. The shipped scenarios spell classes with spaces (`"Solar Panel"`); shorter aliases also work.

Source: `USpaceRangeLibrary::GetPhysicalObjectClass` in `studio/Plugins/SpaceRange/Source/SpaceRange/Private/Libraries/SpaceRangeLibrary.cpp`.

| Class (canonical) | Aliases | Underlying C++ class | Notes |
| --- | --- | --- | --- |
| `Solar Panel` | — | `ASolarPanel` | Power source. |
| `Battery` | — | `ABattery` | Power store. Required for any spacecraft that does not run on solar alone. |
| `Computer` | `Guidance Computer` | `AGuidanceComputer` | Brain — handles software modes (navigation, pointing, controller). |
| `Reaction Wheels` | `RW` | `AReactionWheelArray` | Attitude actuator. Implies an attitude-control mapping is set up automatically by the computer. |
| `External Force Torque` | `External Force` | `AExternalForceTorque` | Generic force/torque actuator (used as an idealised stand-in for thrusters or RWs). |
| `Cold Gas Thruster` | `Thruster` | `AColdGasThruster` | Discrete-pulse thruster. |
| `Ion Thruster` | — | `AIonThruster` | Continuous low-thrust electric propulsion. |
| `Receiver` | — | `AReceiver` | RF downlink/uplink receiver. |
| `Transmitter` | — | `ATransmitter` | RF transmitter. |
| `Jammer` | `Jamming Transmitter` | `AJammingTransmitter` | Hostile RF emitter. |
| `Storage` | `Partitioned Data Storage` | `APartitionedDataStorage` | Onboard data buffer. |
| `Camera` | `Optical Camera`, `Event Camera` | `ACamera` | Visible-light camera. |
| `Heatmap Camera` | `Infrared Camera` | `AHeatmapCamera` | Thermal-imagery camera. |
| `EM Sensor` | `Electromagnetic Sensor` | `AElectromagneticSensor` | RF-spectrum sensor (lets teams see radio sources). |
| `GPS Sensor` | `GPS` | `AGPSSensor` | Position/velocity from the constellation. |
| `Magnetometer` | — | `AMagnetometer` | Magnetic-field measurement. |
| `Gyroscope` | `IMU` | `AGyroscope` | Body-rate measurement. |
| `Charge Coupled Device` | `CCD` | `AChargeCoupledDevice` | Low-level imaging sensor (more often used as a `Camera` model). |
| `Docking Adapter` | `Docking` | `ADockingAdapter` | RPO end-effector. Both vehicles need one to exchange a docking handshake. |
| `Text` | `Physical Text` | `APhysicalText` | Pure-visual label (e.g. callsign written across the chassis). |

You can also reference any other `APhysicalObject` subclass by its short C++ name as a fallback. If the class isn't recognised, Studio logs a warning and instantiates the base `APhysicalObject` (which is just a placeholder).

---

## Universal `data` keys

Every component accepts these keys in its `data` object. Internally each one corresponds to a `UVariableLibrary` property on the component; spaces in the JSON key are stripped before matching.

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `Mass` | `number` (kg) | depends on class | Component mass. Summed into the spacecraft total when `physics.override_mass` is `false`. |

Many components also expose direct properties such as `Sample Rate`, `Bit Rate`, `Antenna Gain`, etc. — these are listed per class below. The general rule is: any `Bool`, `Int`, `Float`, or `Enum` UPROPERTY on the C++ class is settable from `data`. Arrays, strings, and complex types are not (unless explicitly handled by `Setup_Impl`).

---

## Solar Panel

```json
{
  "class": "Solar Panel",
  "name":  "Solar Panel +X",
  "position": [0.8, 0.276313, -0.2],
  "rotation": [35.0, 0.0, 0.0],
  "data": {
    "Area":       0.3,
    "Efficiency": 0.4,
    "Mass":       10.0
  }
}
```

| `data` key | Type | Description |
| --- | --- | --- |
| `Area` | `number` (m²) | Active panel area. |
| `Efficiency` | `number` `0–1` | Conversion efficiency. `0.4` is a realistic modern value. |
| `Mass` | `number` (kg) | Panel mass. |

Power generated is roughly `Area × Efficiency × solar_flux × cos(sun_angle)`, gated by line-of-sight to the Sun.

The `Solar Panel-SolarPanelDegradationErrorModel` event injects permanent efficiency loss; see [events.md#canonical-spacecraft-event-recipes](events.md#canonical-spacecraft-event-recipes).

---

## Battery

```json
{
  "class": "Battery",
  "name":  "Battery",
  "data": {
    "Nominal Capacity": 80.0,
    "Charge Fraction":  0.5,
    "Mass":             5.0
  }
}
```

| `data` key | Type | Description |
| --- | --- | --- |
| `Nominal Capacity` | `number` (Wh) | Maximum stored energy. |
| `Charge Fraction` | `number` `0–1` | Initial state of charge. `0.5` starts the spacecraft with a half-full battery. |
| `Mass` | `number` (kg) | Battery mass. |

Battery error-model events: `Battery-IntermittentConnectionErrorModel` (power spikes), `Battery-BatteryLeakageErrorModel` (slow drain). See [events.md#canonical-spacecraft-event-recipes](events.md#canonical-spacecraft-event-recipes).

---

## Computer (Guidance Computer)

```json
{
  "class": "Computer",
  "name":  "Computer",
  "data":  { "Mass": 2.0 }
}
```

The computer has no other authoring-time `data` keys. Its software modes (navigation, pointing, controller) are configured in code at startup (see `UGuidanceComputerExtension::Setup_Impl`):

- `NavigationMode = Simple`
- `PointingMode = Inertial`
- `ControllerMode = Idle`
- `MappingMode = ReactionWheels` if the spacecraft has reaction wheels, else `ExternalTorque`.

Teams change pointing and controller modes at runtime via the [`guidance`](../api-reference/spacecraft-commands.md#guidance) command (which selects pointing mode and target attitude in one go).

The `Computer-GuidanceComputerNoiseErrorModel` event injects pointing noise; see [events.md#canonical-spacecraft-event-recipes](events.md#canonical-spacecraft-event-recipes).

---

## Reaction Wheels

```json
{
  "class": "Reaction Wheels",
  "name":  "Reaction Wheels",
  "data":  { "Mass": 9.0 }
}
```

The default reaction-wheel array has four wheels in a tetrahedral configuration. There are no authoring-time tuning keys beyond `Mass`. Wheel-level torque limits and inertia are baked into the class.

The `Reaction Wheels` failure event accepts `Stuck Index` to lock one wheel; see [events.md#canonical-spacecraft-event-recipes](events.md#canonical-spacecraft-event-recipes).

---

## External Force Torque

```json
{
  "class": "External Force Torque",
  "name":  "External Force Torque",
  "data": {
    "Max Force":  5000,
    "Max Torque": 2000,
    "Mass":       2.0
  }
}
```

| `data` key | Type | Description |
| --- | --- | --- |
| `Max Force` | `number` (N) | Saturation force. |
| `Max Torque` | `number` (N·m) | Saturation torque. |

Useful as an idealised actuator on tutorial / instructor spacecraft (the `Recon` rogue in `Orbital Sentinel` and the `Microsat` in `Docking_Procedure` use it instead of reaction wheels for simpler dynamics).

---

## Cold Gas Thruster / Ion Thruster

```json
{
  "class": "Cold Gas Thruster",
  "name":  "Thruster +Z",
  "position": [0.0, 0.0, -0.5],
  "rotation": [0.0, 0.0, 0.0],
  "data":  { "Mass": 1.5 }
}
```

Authoring-time keys are limited to `Mass`. Thrust magnitude and Isp are class defaults. For more nuanced thruster behaviour, use multiple thruster components placed around the spacecraft.

---

## Receiver

```json
{
  "class": "Receiver",
  "name":  "Receiver",
  "rotation": [90.0, 0.0, 0.0],
  "data": {
    "Antenna Gain": 3.0,
    "Mass":         2.0
  }
}
```

| `data` key | Type | Description |
| --- | --- | --- |
| `Antenna Gain` | `number` (dBi) | Receive-antenna gain. |
| `Mass` | `number` (kg) | Component mass. |

`Frequency` and `Bandwidth` are excluded from generic data parsing (`UReceiverExtension::GetIgnoredVariables` returns `{ "Frequency", "Bandwidth" }`) — they are set by the spacecraft controller from team config and runtime commands instead.

---

## Transmitter

```json
{
  "class": "Transmitter",
  "name":  "Transmitter",
  "rotation": [90.0, 0.0, 0.0],
  "data":  {
    "Antenna Gain": 3.0,
    "Bit Rate":     20000.0,
    "Mass":         1.0
  }
}
```

| `data` key | Type | Description |
| --- | --- | --- |
| `Antenna Gain` | `number` (dBi) | Transmit-antenna gain. |
| `Bit Rate` | `number` (bits/s) | Downlink bit rate. Affects how quickly the storage drain during downlink. |
| `Mass` | `number` (kg) | Component mass. |
| `Lookup` | `string` | Optional CSV lookup file name to configure the EM antenna pattern. Loaded by `UTransmitterExtension::Setup_Impl`. Most scenarios omit this. |

`Frequency` is excluded from generic parsing — set by the team config (`teams[].frequency`) and rotated at runtime via [`telemetry`](../api-reference/spacecraft-commands.md#telemetry) (from ground) or [`encryption`](../api-reference/spacecraft-commands.md#encryption) (from the spacecraft).

The `Transmitter-TransmitterPacketCorruptionErrorModel` event injects per-packet corruption; the bare `Transmitter` target with `Bit Rate` cuts throughput. See [events.md#canonical-spacecraft-event-recipes](events.md#canonical-spacecraft-event-recipes).

---

## Jammer (Jamming Transmitter)

```json
{
  "class": "Jammer",
  "name":  "Jammer",
  "rotation": [90.0, 90.0, 0.0],
  "data": {
    "Power":        100.0,
    "Antenna Gain": 15.0,
    "Lookup":       "RFPattern.csv",
    "Mass":         1.5
  }
}
```

| `data` key | Type | Description |
| --- | --- | --- |
| `Power` | `number` (W) | Output power. |
| `Antenna Gain` | `number` (dBi) | Antenna gain. |
| `Lookup` | `string` | CSV lookup file describing the EM emission pattern, loaded by `UJammerExtension::Setup_Impl`. The shipped scenarios use `"RFPattern.csv"`. |
| `Mass` | `number` (kg) | Component mass. |

`Frequency` is excluded from generic parsing — set at runtime by the [`jammer`](../api-reference/spacecraft-commands.md#jammer) command (`Mode: start`/`stop` with one or more frequencies).

---

## Storage (Partitioned Data Storage)

```json
{
  "class": "Storage",
  "name":  "Storage",
  "data":  { "Mass": 4.0 }
}
```

| `data` key | Type | Description |
| --- | --- | --- |
| `Mass` | `number` (kg) | Component mass. |

Storage capacity, corruption fraction, and corruption intensity are tracked on the **spacecraft controller** (not the component), and are mutated at runtime by `Storage` failure events:

| Event `Data` key | Type | Effect |
| --- | --- | --- |
| `Capacity` | `int` (bytes) | Force a new total capacity. Use with `Target: "Storage"` to fill the buffer. |
| `Corruption Fraction` | `number` `0–1` | Fraction of stored bytes randomly corrupted. |
| `Corruption Intensity` | `number` `0–1` | How aggressive each corruption event is. |

See [events.md#canonical-spacecraft-event-recipes](events.md#canonical-spacecraft-event-recipes).

---

## Camera (Optical Camera) / Heatmap Camera (Infrared)

```json
{
  "class": "Camera",
  "name":  "Camera",
  "position": [0.0, -0.36, -0.16],
  "rotation": [90.0, 0.0, 0.0],
  "data": {
    "Sample Rate": 10.0,
    "Mass":        5.0
  }
}
```

| `data` key | Type | Description |
| --- | --- | --- |
| `Sample Rate` | `number` (Hz) | Frame rate of the camera. |
| `Mass` | `number` (kg) | Component mass. |

Optical settings (FOV, aperture, exposure) come from the [`camera`](../api-reference/spacecraft-commands.md#camera) command at runtime, **not** from `data`. Heatmap Camera and Optical Camera share the same `data` schema.

---

## GPS Sensor

```json
{
  "class": "GPS Sensor",
  "name":  "GPS Sensor",
  "data":  { "Mass": 2.0 }
}
```

The `GPS Sensor` failure event accepts `Fault State` to put the sensor into a degraded mode; see [events.md#canonical-spacecraft-event-recipes](events.md#canonical-spacecraft-event-recipes). Whole-constellation effects (spoofing, jamming) are scenario-level GPS events instead — see [events.md#gps-events](events.md#gps-events).

---

## Magnetometer / Gyroscope / Electromagnetic Sensor / Charge Coupled Device

These four sensor classes all share the same minimal `data` schema:

```json
{ "class": "Magnetometer", "name": "Magnetometer", "data": { "Mass": 2.0 } }
{ "class": "Gyroscope",    "name": "Gyroscope",    "data": { "Mass": 1.0 } }
{ "class": "EM Sensor",    "name": "EM Sensor",    "data": { "Mass": 2.0 } }
```

| `data` key | Type | Description |
| --- | --- | --- |
| `Mass` | `number` (kg) | Component mass. |

Each accepts a `Fault State` event to inject sensor faults at runtime (see [events.md#canonical-spacecraft-event-recipes](events.md#canonical-spacecraft-event-recipes)).

The `Electromagnetic Sensor` is started disabled with a `Nominal` fault state — teams must explicitly enable it through their guidance computer to use it. This is by design (`UElectromagneticSensorExtension::Setup_Impl`).

---

## Docking Adapter

```json
{
  "class": "Docking Adapter",
  "name":  "Docking Adapter",
  "position": [0.0, 0.36, -0.015],
  "rotation": [-90.0, 0.0, 0.0],
  "data": {
    "Capture Distance": 0.05,
    "Capture Angle":    20.0,
    "Mass":             5.0
  }
}
```

| `data` key | Type | Description |
| --- | --- | --- |
| `Capture Distance` | `number` (m) | Maximum face-to-face distance at which capture succeeds. |
| `Capture Angle` | `number` (deg) | Maximum half-cone alignment angle for a successful capture. |
| `Mass` | `number` (kg) | Component mass. |

Both the chaser and the target need a `Docking Adapter` component, and both spacecraft need `enable_rpo: true` in their `controller`. See [recipes.md](recipes.md) — Recipe 4.

---

## Text (Physical Text)

```json
{
  "class": "Text",
  "name":  "Text Front",
  "enabled": true,
  "position": [13.418, 40.162, -8.064],
  "rotation": [-1.4, 77.7, -97.2],
  "data": {
    "Text":  "RECON",
    "Color": "#FFFF0D",
    "Scale": 50.0
  }
}
```

| `data` key | Type | Description |
| --- | --- | --- |
| `Text` | `string` | The text to render on the spacecraft. |
| `Color` | `string` (hex) | Text color. Accepts `#RRGGBB`. |
| `Scale` | `number` | Text scale factor. |

Pure visual / labelling — the text has no simulation effect, but teams can read it from a Camera image. This is the trick used by `Orbital Sentinel`'s rogue spacecraft, where the answer to one of the questions is the word painted on its solar panels.

`Text` data fields are parsed by `UPhysicalTextExtension::Setup_Impl` and bypass the generic property loader, so the keys must be exact (case-insensitive but no aliases): `Text`, `Color`, `Scale`.

---

## Authoring tips

- **Always include `Mass`** on every component. Power, propellant, and inertia calculations rely on a non-zero spacecraft mass.
- **Place components physically** (`position`, `rotation`) when they affect geometry-aware physics: cameras, antennas, jammers, docking adapters, solar panels. For "anywhere on the bus" components (computer, battery, storage), the position is purely cosmetic.
- **Pick standardised names** within a fleet. If every spacecraft has a `Camera`, name it `Camera` everywhere; teams can then write commands that target `Camera` without knowing which spacecraft they're addressing.
- **Disable components with `enabled: false`** when an event is going to enable them later — for example, a `Jammer` that should only come online mid-scenario.
- **Use a `Text` label** on rogue/constructive-agent spacecraft so teams have a way to identify them visually.

For runtime exploration of any spacecraft's component graph, use [`list_entity`](../api-reference/ground-requests.md#list_entity) with the spacecraft's asset ID.
