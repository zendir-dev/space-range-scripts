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
| `Charge Coupled Device` | `CCD` | Low-level imaging sensor (more often used as a `Camera` model). |
| `Docking Adapter` | `Docking` | RPO end-effector. Both vehicles need one to exchange a docking handshake. |
| `Power Interconnect` | — | Cross-bus connector; pairs two spacecraft power networks at load. See [Power Interconnect](#power-interconnect). |
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

**Runtime operator state** (switch open/closed, fuse threshold, limiter set-point, etc.) is not static scenario `data` — it changes during the exercise via the spacecraft [`power`](../api-reference/spacecraft-commands.md#power) command. Clients pull the current snapshot with [`get_configuration`](../api-reference/spacecraft-commands.md#get_configuration) (`scope: "power"`); the Operator UI does this automatically for the Power panel. Static keys in the tables below are authored at load time; session-mutable fields are listed in the [`get_configuration`](../api-reference/spacecraft-commands.md#get_configuration) power-field table.

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

`Is Fuse Blown` is runtime state (read-only), not normally set in scenario JSON. Operators read it via [`get_configuration`](../api-reference/spacecraft-commands.md#get_configuration) and clear a blown fuse with [`power`](../api-reference/spacecraft-commands.md#power) `action: "reset"` (or wait for auto-reset when `Reset Duration` &gt; 0 and branch current is below threshold).

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

## Power Interconnect

A **Power Interconnect** is a power-bus connector that can **link to another interconnect on a different spacecraft**, merging the two buses into one electrical network when the scenario starts.

```json
{
  "class": "Power Interconnect",
  "name": "Interconnect"
}
```

No class-specific `data` keys are required for typical scenarios.

### Terminal usage (same spacecraft)

| Terminal | Wiring |
| --- | --- |
| **`in`** | Upstream components on **this** bus connect **to** the interconnect here (e.g. `Battery` `out` → `Interconnect` `in`). Required before a cross-spacecraft link. |
| **`out`** | Used for downstream loads on the same bus (series continuation). The cross-spacecraft bridge to the partner bus is created by `power.interconnects[]`, not by an extra `bus[]` row to the other hull. |

Wire upstream feeds into **`in`**; use **`out`** for downstream loads on the same bus and for the partner link declared in `interconnects`.

### Cross-spacecraft link (scenario JSON)

Configure in the owning spacecraft's `power.interconnects[]` (not in `components[]`). Full rules, team matching, and a worked example: [spacecraft.md — Power interconnects](spacecraft.md#power-interconnects-powerinterconnects).

**Suggested use:** docking / depot scenarios where two hulls should **start** with a shared power network (e.g. `Docking_Procedure`) before or alongside RPO commands.

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
