# Components reference

Every entry in a spacecraft's `components[]` array adds one piece of on-board hardware. The `class` field selects which component type is created — see the table below for accepted classes and aliases.

The `data` object is **class-specific** tuning. `Mass` is the only universal key (every component has mass). Other keys set component parameters at load time. **Prefer spaced names** in JSON (`"Is Open"`, `"Nominal Capacity"`); Studio ignores spaces when matching, so `"IsOpen"` also works.

This page documents the `data` fields used in shipped scenarios and the keys that scripted `events[]` entries can change at runtime.

---

## Class table

The `class` field is matched case-insensitive after spaces are stripped. The shipped scenarios spell classes with spaces (`"Solar Panel"`); shorter aliases also work.

| Class (canonical) | Aliases | Notes |
| --- | --- | --- |
| `Solar Panel` | — | Power source. |
| `Battery` | — | Power store. Required for any spacecraft that does not run on solar alone. |
| `Power Switch` | — | On-bus switch; open/closed. |
| `Power Fuse` | — | Over-current protection with optional auto-reset. |
| `Power Current Limiter` | — | Limits branch current above a threshold. |
| `Power Diode` | — | One-way conduction on the bus. |
| `Power Sink` | — | Configurable load (watts / voltage drop). |
| `Power Voltage Regulator` | — | Regulates downstream voltage. |
| `Computer` | `Guidance Computer` | Brain — handles software modes (navigation, pointing, controller). |
| `Reaction Wheels` | `RW` | Attitude actuator. |
| `External Force Torque` | `External Force` | Generic force/torque actuator (stand-in for thrusters or RWs). |
| `Cold Gas Thruster` | `Thruster` | Discrete-pulse thruster. |
| `Ion Thruster` | — | Continuous low-thrust electric propulsion. |
| `Receiver` | — | RF downlink/uplink receiver. |
| `Transmitter` | — | RF transmitter. |
| `Jammer` | `Jamming Transmitter` | Hostile RF emitter. |
| `Storage` | `Partitioned Data Storage` | Onboard data buffer. |
| `Camera` | `Optical Camera`, `Event Camera` | Visible-light camera. |
| `Heatmap Camera` | `Infrared Camera` | Thermal-imagery camera. |
| `EM Sensor` | `Electromagnetic Sensor` | RF-spectrum sensor (lets teams see radio sources). |
| `GPS Sensor` | `GPS` | Position/velocity from the constellation. |
| `Magnetometer` | — | Magnetic-field measurement. |
| `Gyroscope` | `IMU` | Body-rate measurement. |
| `Charge Coupled Device` | `CCD` | Configurable imaging sensor (resolution, exposure time, FOV). Captures like a `Camera`. See [Charge Coupled Device (CCD)](#charge-coupled-device-ccd). |
| `Laser Range Finder` | `LRF` | Range-finder for determining distance to objects nearby. |
| `Docking Adapter` | `Docking` | RPO end-effector. Both vehicles need one to exchange a docking handshake. |
| `Power Interconnect` | — | Cross-bus connector; pairs two spacecraft power networks at load. See [Power Interconnect](#power-interconnect). |
| `Fuel Source` | — | Propellant tank. |
| `Fuel Valve` | — | Gated flow path between fuel components. |
| `Fuel Pump` | — | Powered pump between fuel nodes; also needs `power.bus[]` wiring. |
| `Fuel Interconnect` | — | Cross-bus fuel connector; pairs two spacecraft fuel networks at load. |
| `Text` | `Physical Text` | Pure-visual label (e.g. callsign written across the chassis). |

If the `class` value is not recognised, Studio logs a warning and the component may not behave as intended.

---

## Universal `data` keys

Every component accepts these keys in its `data` object. Spaces in the JSON key are stripped before matching.

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `Mass` | `number` (kg) | depends on class | Component mass. Summed into the spacecraft total when `physics.override_mass` is `false`. |

Many components also expose tuning keys such as `Sample Rate`, `Bit Rate`, `Antenna Gain`, etc. — these are listed per class below. Keys not documented for a class are usually ignored at load time.

---

## Component `models`

Each entry in `components[]` may include an optional `models` array. Models are **Universe Models** — extra simulation behaviour attached to the component (error models, power-node models, radiation models, etc.). They have no `name`, `mesh`, or transform; only a class, enable flag, and parameter data.

```json
{
  "class": "Solar Panel",
  "name": "Solar Panel +X",
  "position": [0.8, 0.276313, -0.2],
  "rotation": [35.0, 0.0, 0.0],
  "data": {
    "Area": 0.3,
    "Efficiency": 0.4,
    "Mass": 10.0
  },
  "models": [
    {
      "class": "Solar Panel Degradation Error Model",
      "enabled": true,
      "data": {
        "Degradation Rate": 10.0
      }
    }
  ]
}
```

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `class` | `string` | — | Model class name (matched case-insensitively against the formatted Mono class name, e.g. `"Solar Panel Degradation Error Model"`). The model must be supported on the parent component type. |
| `enabled` | `bool` | `true` | When `false`, the model is attached but does not simulate. Legacy key `enable` is also accepted. |
| `data` | `object` | `{}` | Model-specific parameters, using the same spaced-name rules as component `data`. |

If the model class is unknown or not supported on that component, Studio logs a warning and skips that entry. Multiple models may be listed when the component supports more than one.

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

## Power bus network components

These components attach to the spacecraft **power bus** and are wired with `power.bus[]` on the spacecraft entry (see [spacecraft.md — power](spacecraft.md#power--electrical-bus)). Each has **`in`** and **`out`** terminals unless noted. Chain them in series from the battery (or solar) toward loads; use a **`Power Diode`** when current must only flow one way.

**Generation and storage** (`Solar Panel`, `Battery`) are documented above. **Cross-spacecraft links** use `Power Interconnect` ([below](#power-interconnect)).

**Runtime operator state** (switch open/closed, fuse threshold, limiter set-point, valve/pump state, guidance pointing modes, imager settings, etc.) is not static scenario `data` — it changes during the exercise via spacecraft [`power_bus`](../api-reference/spacecraft-commands.md#power_bus), [`fuel_bus`](../api-reference/spacecraft-commands.md#fuel_bus), [`guidance`](../api-reference/spacecraft-commands.md#guidance), and [`camera`](../api-reference/spacecraft-commands.md#camera) / [`capture`](../api-reference/spacecraft-commands.md#capture) commands. Clients pull the current snapshot with [`get_configuration`](../api-reference/spacecraft-commands.md#get_configuration) (omit `scope` for all sections, or filter by `scope`). Static keys in the tables below are authored at load time; session-mutable fields are in the [`get_configuration`](../api-reference/spacecraft-commands.md#get_configuration) report shape (`power_bus`, `fuel_bus`, `computer`, `camera`).

Payload hardware (`Camera`, `Transmitter`, sensors, etc.) can also be listed on `power.bus[]` when those types participate in the electrical model — same `source_component` / `target_component` rules as switches and sinks.

### Power Switch

User-operable (or scenario-initialised) switch on the bus. When **open**, the branch is disconnected; when **closed**, current can flow.

```json
{
  "class": "Power Switch",
  "name": "EPS Switch",
  "data": {
    "Is Open":    false,
    "Resistance": 1.0,
    "Mass":       0.5
  }
}
```

| `data` key | Type | Default | Description |
| --- | --- | --- | --- |
| `Is Open` | `bool` | `false` | `true` = open (no conduction); `false` = closed. |
| `Resistance` | `number` (Ω) | `1.0` | Series resistance when closed. |
| `Mass` | `number` (kg) | — | Component mass. |

`Power Interconnect` is a specialised switch used for cross-spacecraft pairing; see [Power Interconnect](#power-interconnect).

### Power Fuse

Opens the circuit when branch current exceeds a threshold for long enough. Optional timed reset after a blow.

```json
{
  "class": "Power Fuse",
  "name": "EPS Fuse",
  "data": {
    "Current Threshold":   2.0,
    "Threshold Duration":  5.0,
    "Reset Duration":      60.0,
    "Resistance":          1.0,
    "Mass":                0.5
  }
}
```

| `data` key | Type | Default | Description |
| --- | --- | --- | --- |
| `Current Threshold` | `number` (A) | `0.0` | Current above which the fuse may blow. |
| `Threshold Duration` | `number` (s) | `0.0` | Time the threshold must be exceeded before blowing. |
| `Reset Duration` | `number` (s) | `0.0` | Time after a blow before auto-reset; `0` = no auto-reset. |
| `Resistance` | `number` (Ω) | `1.0` | Resistance while closed. |
| `Mass` | `number` (kg) | — | Component mass. |

`Is Fuse Blown` is runtime state (read-only), not normally set in scenario JSON. Operators read it via [`get_configuration`](../api-reference/spacecraft-commands.md#get_configuration) and clear a blown fuse with [`power_bus`](../api-reference/spacecraft-commands.md#power_bus) `action: "reset"` (or wait for auto-reset when `Reset Duration` &gt; 0 and branch current is below threshold).

### Power Current Limiter

Reduces or blocks current when the branch exceeds `Current Limit`.

```json
{
  "class": "Power Current Limiter",
  "name": "Bus Limiter",
  "data": {
    "Current Limit": 5.0,
    "Resistance":    1.0,
    "Mass":          0.5
  }
}
```

| `data` key | Type | Default | Description |
| --- | --- | --- | --- |
| `Current Limit` | `number` (A) | `0.0` | Limit above which limiting engages. |
| `Resistance` | `number` (Ω) | `1.0` | Series resistance. |
| `Mass` | `number` (kg) | — | Component mass. |

### Power Diode

One-way valve: forward current flows **`in` → `out`**; reverse current is blocked (within model limits). Use for OR-ing sources, blocking back-feed, or protecting branches.

```json
{
  "class": "Power Diode",
  "name": "Bus Diode",
  "data": {
    "Resistance": 1.0,
    "Mass":       0.5
  }
}
```

| `data` key | Type | Default | Description |
| --- | --- | --- | --- |
| `Resistance` | `number` (Ω) | `1.0` | Small-signal / parasitic resistance. |
| `Saturation Current` | `number` (A) | `2.52e-9` | Diode saturation current (IS). |
| `Emission Coefficient` | `number` | `1.984` | Emission coefficient (N). |
| `Junction Capacitance` | `number` (F) | `35e-12` | Zero-bias junction capacitance (CJO). |
| `Junction Potential` | `number` (V) | `0.75` | Junction potential (VJ). |
| `Grading Coefficient` | `number` | `0.333` | Grading coefficient (M). |
| `Bandgap Voltage` | `number` (V) | `1.11` | Bandgap voltage (EG). |
| `Breakdown Voltage` | `number` (V) | `400.0` | Reverse breakdown voltage (BV). |
| `Breakdown Current` | `number` (A) | `1e-6` | Current at breakdown (IBV). |
| `Transit Time` | `number` (s) | `2.52e-7` | Transit time (TT); advanced. |
| `Flicker Noise Coefficient` | `number` | `0.0` | Flicker noise coefficient (KF); advanced. |
| `Flicker Noise Exponent` | `number` | `1.0` | Flicker noise exponent (AF); advanced. |
| `Forward Bias Depletion Cap Coeff` | `number` | `0.5` | Forward-bias depletion capacitance coefficient (FC); advanced. |
| `Mass` | `number` (kg) | — | Component mass. |

Only `Resistance` and `Mass` are needed for most scenarios; omit the diode model keys to keep defaults (1N4004-like).

Wire with upstream on **`in`** and downstream on **`out`** so forward power flows toward the load.

### Power Sink

Fixed or commanded electrical load on the bus (heaters, avionics blocks, or stand-ins for payload draw).

```json
{
  "class": "Power Sink",
  "name": "Camera Load",
  "data": {
    "Is Active":              true,
    "Nominal Voltage Drop":   12.0,
    "Nominal Power":          8.0,
    "Resistance":             1.0,
    "Mass":                   0.5
  }
}
```

| `data` key | Type | Default | Description |
| --- | --- | --- | --- |
| `Is Active` | `bool` | `true` | When `false`, nominal draw is zero. |
| `Nominal Voltage Drop` | `number` (V) | `12.0` | Target voltage drop across the sink. |
| `Nominal Power` | `number` (W) | `0.0` | Target power consumption when active. |
| `Resistance` | `number` (Ω) | `1.0` | Series resistance. |
| `Mass` | `number` (kg) | — | Component mass. |

### Power Voltage Regulator

Holds downstream voltage near `Regulation Voltage` when input is high enough; otherwise output follows input minus resistive drop. Efficiency is derived at runtime (not authored).

```json
{
  "class": "Power Voltage Regulator",
  "name": "Bus Regulator",
  "data": {
    "Regulation Voltage": 28.0,
    "Resistance":         1.0,
    "Mass":               0.5
  }
}
```

| `data` key | Type | Default | Description |
| --- | --- | --- | --- |
| `Regulation Voltage` | `number` (V) | `0.0` | Regulation set-point. |
| `Resistance` | `number` (Ω) | `1.0` | Series resistance. |
| `Mass` | `number` (kg) | — | Component mass. |

---

## Computer (Guidance Computer)

```json
{
  "class": "Computer",
  "name":  "Computer",
  "data":  { 
    "Mass": 2.0 
  }
}
```

The computer has no other authoring-time `data` keys. Its software modes (navigation, pointing, controller) are configured at scenario load:

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
  "data":  { 
    "Mass": 9.0 
  }
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

Useful as an idealised actuator on tutorial / instructor spacecraft (the `Recon` rogue in `Orbital Intel` and the `Microsat` in `Docking_Procedure` use it instead of reaction wheels for simpler dynamics).

---

## Cold Gas Thruster / Ion Thruster

```json
{
  "class": "Cold Gas Thruster",
  "name":  "Thruster +Z",
  "position": [0.0, 0.0, -0.5],
  "rotation": [0.0, 0.0, 0.0],
  "data":  { 
    "Mass": 1.5 
  }
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
| `Lookup` | `string` | Optional CSV lookup file name to configure the EM antenna pattern. Most scenarios omit this. |

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
| `Lookup` | `string` | CSV lookup file describing the EM emission pattern. The shipped scenarios use `"RFPattern.csv"`. |
| `Mass` | `number` (kg) | Component mass. |

`Frequency` is excluded from generic parsing — set at runtime by the [`jammer`](../api-reference/spacecraft-commands.md#jammer) command (`Mode: start`/`stop` with one or more frequencies).

---

## Storage (Partitioned Data Storage)

```json
{
  "class": "Storage",
  "name":  "Storage",
  "data":  { 
    "Mass": 4.0 
  }
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
  "class": "Optical Camera",
  "name":  "Main Camera",
  "position": [0.0, -0.36, -0.16],
  "rotation": [90.0, 0.0, 0.0],
  "data": {
    "Sample Rate": 10.0,
    "Mass": 3.0,
    "Aperture": 20.0,
    "Min Field Of View": 1.0,
    "Field Of View": 10.0,
    "Max Field Of View": 15.0,
    "Resolution": [1024, 1024]
  }
}
```

| `data` key | Type | Description |
| --- | --- | --- |
| `Sample Rate` | `number` (Hz) | Frame rate of the camera. |
| `Mass` | `number` (kg) | Component mass. |
| `Min Field Of View` | `number` (deg) | **Hardware limit** — narrowest FOV operators may command. Default `0`. Must be ≤ `Field Of View` ≤ `Max Field Of View`. |
| `Field Of View` | `number` (deg) | **Initial FOV** at scenario load (before any [`camera`](../api-reference/spacecraft-commands.md#camera) command). Clamped into `[Min Field Of View, Max Field Of View]`. Default `60` on the class if omitted. |
| `Max Field Of View` | `number` (deg) | **Hardware limit** — widest FOV operators may command. Default `180`. |
| `Aperture` | `number` (mm) | Lens diameter at load. Operators can change aperture at runtime via `camera` / `capture`. |
| `Focal Length` | `number` (mm) | Lens focal length at load. |
| `Focusing Distance` | `number` (m) | In-focus distance at load. |
| `Pixel Pitch` | `number` (mm) | Sensor pixel pitch at load. |
| `Circle Of Confusion` | `number` (mm) | Depth-of-field blur tolerance at load. |
| `Resolution` | `[w, h]` (px) | Sensor resolution at load as a two-element array (e.g. `[1024, 1024]`). Default `256×256`. |

### Field of view limits

Each `Optical Camera` / `Camera` can define a **per-unit FOV envelope** in `data`:

- **`Min Field Of View`** and **`Max Field Of View`** are set by the scenario author and define what operators are allowed to request in the [`camera`](../api-reference/spacecraft-commands.md#camera) / [`capture`](../api-reference/spacecraft-commands.md#capture) `fov` argument.
- **`Field Of View`** is the starting value inside that envelope when the simulation spawns the craft.
- If `fov` is outside the envelope, the command is **rejected** (Studio) and the Operator UI disables capture for that value.

Use tight envelopes for mission-specific optics — for example a narrow science camera (`1° … 15°`) and a wide docking camera (`30° … 60°`) on the same spacecraft. See [Lunar Logistics](../scenarios/Lunar%20Logistics/lunar_logistics.json) (`Main Camera` and `Docking Camera`).

At runtime, operator-chosen settings (`fov`, `resolution`, `aperture`, …) are stored in the Configuration Report `camera[]` section and **sync across the team** after each `camera` / `capture` command (same pattern as Guidance). The report also includes `min_field_of_view` and `max_field_of_view` so every operator UI shows the correct slider range.

Heatmap Camera and Optical Camera share the same `data` schema. `Charge Coupled Device` imagers capture using the same command/sync pipeline but expose a smaller set of settings — see [Charge Coupled Device (CCD)](#charge-coupled-device-ccd) below.

---

## Charge Coupled Device (CCD)

A low-noise imaging sensor that captures via the same [`capture`](../api-reference/spacecraft-commands.md#capture) / [`camera`](../api-reference/spacecraft-commands.md#camera) pipeline as a `Camera`, but with a smaller, imager-specific setting set. Unlike the `Camera`, its `Resolution` is a **single integer** (a square sensor grid), and it adds an `Exposure Time`.

```json
{
  "class": "Charge Coupled Device",
  "name":  "Charge Coupled Device",
  "position": [0.0, -0.36, -0.16],
  "rotation": [90.0, 0.0, 180.0],
  "data": {
    "Resolution": 64,
    "Exposure Time": 0.01,
    "Capture On Tick": false
  }
}
```

| `data` key | Type | Description |
| --- | --- | --- |
| `Resolution` | `number` (px) | Sensor grid size as a **single integer** — the frame is `Resolution × Resolution`. Class default `16`. The Operator UI caps operator-set values to `16 … 64`. |
| `Exposure Time` | `number` (s) | How long the sensor integrates light per capture. Class default `0.1`. The Operator UI caps operator-set values to `0.001 … 1.0`. |
| `Field Of View` | `number` (deg) | Starting FOV. Class default `60`. The CCD uses a fixed `1° … 90°` envelope (there are no `Min/Max Field Of View` properties on this class). |
| `Capture On Tick` | `bool` | Whether the sensor captures automatically every simulation tick. Class default `true`; set `false` to capture only on command. |
| `Maximum ADU` | `number` (ADU) | Full-well digitisation ceiling per pixel. Class default `65535`. |
| `Mass` | `number` (kg) | Component mass. |

Radiometric / noise parameters (`Area`, `Efficiency`, `Spectral Wavelength`, `Atmosphere Absorption`, `Point Spread Factor`, `Thermal Noise`, `Readout Noise`, `Quantization Noise`, `Dark Current Noise`, `Bias`) can also be set in `data`; they default to sensible values on the class and are only needed for detailed sensor-modelling exercises.

At runtime, operator-chosen `resolution`, `fov`, and `exposure_time` are stored in the Configuration Report `camera[]` section and **sync across the team** after each `camera` / `capture` command — the same pattern as a `Camera`. The Operator UI shows only Camera Unit, Field of View, Resolution, and Exposure Time for a CCD.

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

## Magnetometer / Gyroscope / Electromagnetic Sensor

These three sensor classes all share the same minimal `data` schema:

```json
{
  "class": "Magnetometer",
  "name": "Magnetometer",
  "data": { "Mass": 2.0 }
}
```

```json
{
  "class": "Gyroscope",
  "name": "Gyroscope",
  "data": { "Mass": 1.0 }
}
```

```json
{
  "class": "EM Sensor",
  "name": "EM Sensor",
  "data": { "Mass": 2.0 }
}
```

| `data` key | Type | Description |
| --- | --- | --- |
| `Mass` | `number` (kg) | Component mass. |

Each accepts a `Fault State` event to inject sensor faults at runtime (see [events.md#canonical-spacecraft-event-recipes](events.md#canonical-spacecraft-event-recipes)).

The `Electromagnetic Sensor` is started disabled with a `Nominal` fault state — teams must explicitly enable it through their guidance computer to use it.

---

## Laser Range Finder

The laser range finder uses the following schema:

```json
{
  "class": "Laser Range Finder",
  "name": "LRF",
  "data": { 
    "Operating Range": 1000.0,
    "Range Accuracy Constant": 0.01
  }
}
```

| `data` key | Type | Description |
| --- | --- | --- |
| `Operating Range` | `number` (m) | Maximum operating range for the sensor. |
| `Range Accuracy Constant` | The accuracy (towards 0) in which the value is correct. |

This also accepts a `Fault State` event to inject sensor faults at runtime (see [events.md#canonical-spacecraft-event-recipes](events.md#canonical-spacecraft-event-recipes)).

---

## Docking Adapter

```json
{
  "class": "Docking Adapter",
  "name":  "Docking Adapter",
  "position": [0.0, 0.36, -0.015],
  "rotation": [-90.0, 0.0, 0.0],
  "data": {
    "Capture Distance":    0.05,
    "Capture Angle":       20.0,
    "Separation Force":    100.0,
    "Separation Duration": 1.0,
    "Mass":                5.0
  }
}
```

| `data` key | Type | Description |
| --- | --- | --- |
| `Capture Distance` | `number` (m) | Maximum face-to-face distance at which capture succeeds. |
| `Capture Angle` | `number` (deg) | Maximum half-cone alignment angle for a successful capture. |
| `Separation Force` | `number` (N) | Impulse force applied along the docking axis when undocking, to push the craft apart. Default `100`. |
| `Separation Duration` | `number` (s) | Duration over which the separation force is applied when undocking. Default `0.5`. |
| `Mass` | `number` (kg) | Component mass. |

Both the chaser and the target need a `Docking Adapter` component. The chaser does **not** need `enable_rpo_software` — only a rendezvous manoeuvre requires that flag. Undocking via the [`docking`](../api-reference/spacecraft-commands.md#docking) command applies the separation impulse defined here. See [recipes.md](recipes.md) — Recipe 4.

---

## Fuel network components

Static topology is authored in each spacecraft's `fuel.bus[]` (see [spacecraft.md — fuel](spacecraft.md#fuel--propellant-bus)). Runtime valve/pump state changes via [`fuel_bus`](../api-reference/spacecraft-commands.md#fuel_bus) and [`get_configuration`](../api-reference/spacecraft-commands.md#get_configuration) (`scope: "fuel_bus"`). Set initial state in `data` where noted.

### Fuel Source

```json
{
  "class": "Fuel Source",
  "name": "Main Tank",
  "data": {
    "Capacity": 50.0,
    "Amount": 45.0,
    "Dry Mass": 8.0,
    "Maximum Outgoing Flow Rate": 2.0,
    "Desired Ingoing Flow Rate": 0.0,
    "Mass": 8.0
  }
}
```

| `data` key | Type | Default | Description |
| --- | --- | --- | --- |
| `Capacity` | `number` (kg) | `1.0` | Maximum propellant the tank can hold. **Always set this** — the `1.0` default is tiny and will cap fill/transfer immediately. |
| `Amount` | `number` (kg) | `0.0` | Propellant loaded at scenario start. **Defaults to empty (`0.0`)**, so a supply/source tank must set it; a receiving tank typically starts at `0.0` (or partial). |
| `Initial Fuel Mass` | `number` (kg) | `0.0` | Alias for `Amount` (either key works). |
| `Dry Mass` | `number` (kg) | `0.0` | Tank hardware mass without propellant. |
| `Maximum Outgoing Flow Rate` | `number` (kg/s) | `2.0` | Outflow limit **from** the tank (how fast it can supply downstream). |
| `Desired Ingoing Flow Rate` | `number` (kg/s) | `0.0` | Rate at which the tank actively **draws fuel in**. **Defaults to `0.0`, meaning the tank pulls nothing** — a receiving tank (e.g. the client end of a fuel interconnect) must set this **positive** or no fuel transfers in, even with valves open. |
| `Mass` | `number` (kg) | — | Component mass (summed into spacecraft total). |

> **Fuel transfer needs both ends configured.** For propellant to move across a [`Fuel Interconnect`](#fuel-interconnect), the **supply** tank needs `Amount > 0` and an adequate `Maximum Outgoing Flow Rate`, and the **receiving** tank needs spare `Capacity` and a positive `Desired Ingoing Flow Rate` (it is `0.0` by default, so an unset receiver silently accepts nothing). The transfer rate is limited by the smallest of those plus any valve `Max Flow Rate` in between.

### Fuel Valve

```json
{
  "class": "Fuel Valve",
  "name": "Main Valve",
  "data": {
    "Commanded Percent Open": 1.0,
    "Max Flow Rate": 2.0,
    "Mass": 0.5
  }
}
```

| `data` key | Type | Default | Description |
| --- | --- | --- | --- |
| `Commanded Percent Open` | `number` `0–1` | `1.0` | Target openness at load (`0` = closed, `1` = fully open). |
| `Max Flow Rate` | `number` (kg/s) | unlimited | Flow cap when open. |
| `Max Actuation Angular Velocity` | `number` (rad/s) | `π/2` | How fast the valve moves toward the commanded position. |
| `Mass` | `number` (kg) | — | Component mass. |

Wire on `fuel.bus[]` with `in` / `out` terminals (maps to inlet / outlet).

### Fuel Pump

```json
{
  "class": "Fuel Pump",
  "name": "Feed Pump",
  "data": {
    "Max Flow Rate": 1.0,
    "Efficiency": 0.9,
    "Is Pump Enabled": false,
    "Mass": 1.5
  }
}
```

| `data` key | Type | Default | Description |
| --- | --- | --- | --- |
| `Max Flow Rate` | `number` (kg/s) | `1.0` | Rated flow at full motor speed. |
| `Efficiency` | `number` `0–1` | `1.0` | Mechanical efficiency factor. |
| `Is Pump Enabled` | `bool` | `false` | Whether the pump starts enabled. |
| `Allow Flow When Disabled` | `bool` | `false` | Passive pass-through when disabled. |
| `Mass` | `number` (kg) | — | Component mass. |

Also connect the pump on `power.bus[]` (`battery` `out` → pump `in`) so the motor can run.

### Fuel Interconnect

A **Fuel Interconnect** is a passive fuel node that bonds to **one local fuel object** (a `Fuel Source`, `Fuel Valve`, or `Fuel Pump`) and **links to a matching interconnect on another spacecraft** to form a fuel-transfer bridge. Fuel only crosses the link while the two spacecraft are **docked** (and the bonded valve on each side is open), so it is the fuel analogue of [`Power Interconnect`](#power-interconnect).

```json
{
  "class": "Fuel Interconnect",
  "name": "Fuel Interconnect",
  "data": {
    "Mass": 0.5,
    "Is Bidirectional": true,
    "Vent To Space When Unconnected": false
  }
}
```

| `data` key | Type | Default | Description |
| --- | --- | --- | --- |
| `Is Bidirectional` | `bool` | `false` | When `true`, fuel may flow either direction through the link. |
| `Vent To Space When Unconnected` | `bool` | `true` | When `true`, fuel vents to space (producing a small thrust) if the interconnect is unlinked, or cross-docked but **not** currently docked. Set `false` to simply stop flow. |
| `Specific Impulse` | `number` (s) | `50.0` | Isp used to convert vent mass-flow to thrust when venting. `0` removes mass without thrust. |
| `Require Positive Pressure Differential` | `bool` | `false` | When `true`, transfer requires the supply ullage pressure to exceed the receiver's (both sides need a `Fuel Source Thermal Model`). |
| `Mass` | `number` (kg) | — | Component mass. |

**Bond it locally first.** On `fuel.bus[]`, wire a valve/pump/tank into the interconnect so it has a local fuel object to draw from or feed into (the interconnect maps to a single `Local` port):

```json
{ "source_component": "Transfer Valve", "source_terminal": "out", "target_component": "Fuel Interconnect", "target_terminal": "in" }
```

**Then link it to its partner** in the top-level [`docking`](spacecraft.md#docking-start-the-scenario-already-docked) block as a fuel-interconnect connection — `{ "from_team": 111111, "from_asset": "SC_001", "from_target": "Fuel Interconnect", "to_asset": "SC_HUB", "to_target": "Fuel Interconnect A" }`. Both endpoints name a `Fuel Interconnect`, so Studio links (rather than docks) them; address each craft by team (`from_team`/`to_team`, which also requires `from_asset`/`to_asset`) or by asset (`from_asset`/`to_asset`, e.g. a neutral hub). Full rules and a multi-port hub recipe: [spacecraft.md — Fuel interconnects](spacecraft.md#fuel-interconnects).

**Suggested use:** servicer/depot scenarios where a tanker tops up a client across a docked interface (see `Testing/test_fuel_scenario`).

---

## Power Interconnect

A **Power Interconnect** is a power-bus connector that can **link to another interconnect on a different spacecraft**, merging the two buses into one electrical network. It extends `Power Switch`, so it is itself a switch (`Is Open`) that can break the bridge. It is the power analogue of the [Fuel Interconnect](#fuel-interconnect).

```json
{
  "class": "Power Interconnect",
  "name": "Interconnect"
}
```

No class-specific `data` keys are required for typical scenarios (it inherits `Is Open`, `Resistance`, etc. from [Power Switch](#power-switch)).

### Terminal usage (same spacecraft)

| Terminal | Wiring |
| --- | --- |
| **`in`** | Upstream components on **this** bus connect **to** the interconnect here (e.g. `Battery` `out` → `Interconnect` `in`). Required before a cross-spacecraft link. |
| **`out`** | Used for downstream loads on the same bus (series continuation). The cross-spacecraft bridge to the partner bus is created by the `docking` link, not by an extra `bus[]` row to the other hull. |

### Cross-spacecraft link (scenario JSON)

Link two interconnects in the top-level [`docking`](spacecraft.md#docking-start-the-scenario-already-docked) block as a power-interconnect connection — `{ "from_team": 111111, "from_asset": "SC_001", "from_target": "Interconnect", "to_asset": "SC_HUB", "to_target": "Interconnect A" }`. Both endpoints name a `Power Interconnect`, so Studio links (rather than docks) them; address each craft by team (`from_team`/`to_team`, which also requires `from_asset`/`to_asset`) or asset (`from_asset`/`to_asset`, e.g. a neutral hub). Full rules and a hub recipe: [spacecraft.md — Power interconnects](spacecraft.md#power-interconnects).

**Suggested use:** docking / depot scenarios where two hulls should **start** with a shared power network — e.g. the RPO hub charging docked clients.

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

Pure visual / labelling — the text has no simulation effect, but teams can read it from a Camera image. This is the trick used by `Orbital Intel`'s rogue spacecraft, where the answer to one of the questions is the word painted on its solar panels.

`Text` uses dedicated keys only (case-insensitive, no aliases): `Text`, `Color`, `Scale`.

---

## Authoring tips

- **Always include `Mass`** on every component. Power, propellant, and inertia calculations rely on a non-zero spacecraft mass.
- **Place components physically** (`position`, `rotation`) when they affect geometry-aware physics: cameras, antennas, jammers, docking adapters, solar panels. For "anywhere on the bus" components (computer, battery, storage), the position is purely cosmetic.
- **Pick standardised names** within a fleet. If every spacecraft has a `Camera`, name it `Camera` everywhere; teams can then write commands that target `Camera` without knowing which spacecraft they're addressing.
- **Disable components with `enabled: false`** when an event is going to enable them later — for example, a `Jammer` that should only come online mid-scenario.
- **Use a `Text` label** on rogue/constructive-agent spacecraft so teams have a way to identify them visually.

For runtime exploration of any spacecraft's component graph, use [`list_entity`](../api-reference/ground-requests.md#list_entity) with the spacecraft's asset ID.
