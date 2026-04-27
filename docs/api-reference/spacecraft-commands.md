# Spacecraft Commands

Every spacecraft action in Space Range is driven by a single uplink JSON message. This page documents every command the spacecraft controller accepts: the envelope, the `Args` for each `Command` value, and the most common gotchas.

For background — how commands flow through the system, how scheduling works, why the keys are PascalCase — see [Concepts → Commands and scheduling](../concepts/commands-and-scheduling.md).

---

## Envelope

All uplink commands publish to:

```text
Zendir/SpaceRange/<GAME>/<TEAM>/Uplink     (XOR-encrypted with the team password)
```

with the payload:

```json
{
  "Asset":   "A3F2C014",
  "Command": "guidance",
  "Time":    0,
  "Args":    { "...": "..." }
}
```

| Field | Type | Description |
| --- | --- | --- |
| `Asset` | `string` | 8-character hex ID of the target spacecraft. Case-insensitive on the wire (Studio uppercases internally). The same uplink topic serves every spacecraft on the team — only the spacecraft whose ID matches will execute. |
| `Command` | `string` | One of the command names listed below (case-insensitive: `guidance`, `Guidance`, `GUIDANCE` are equivalent). |
| `Time` | `number` | Simulation seconds at which to execute. `0` (or any value `≤ current sim time`) means "execute immediately". A future value schedules the command. |
| `Args` | `object` | Command-specific arguments. Keys are case-insensitive. Missing keys fall back to documented defaults. |

### Notes about the envelope

- Uplink keys are **PascalCase** (`Asset`, `Command`, `Time`, `Args`). The keys *inside* `Args` are typically lowercase. The historical schema used lowercase top-level keys; that form is no longer accepted by the current backend — use the PascalCase form documented here.
- An incorrect `Asset` ID is **not an error** — Studio simply has no spacecraft to deliver the command to and the uplink is dropped silently. Verify your ID via [`list_assets`](ground-requests.md#list_assets) if commands appear to be ignored.
- An unrecognised `Command` name is a no-op. The spacecraft does not return a "command rejected" message; you'll see no Ping field changes and no scheduled entry. Double-check the spelling.
- Once accepted, scheduled commands appear in the Schedule Report (request via the [`get_schedule`](#get_schedule) command). Use that to confirm what the spacecraft has queued.

---

## Command index

ADCS / pointing
: [`guidance`](#guidance) — set the spacecraft's pointing mode.

Imaging
: [`camera`](#camera) — configure a camera.
: [`capture`](#capture) — capture an image with a configured camera.

Communications
: [`telemetry`](#telemetry) — change RF link parameters (frequency, key, bandwidth) via ground.
: [`encryption`](#encryption) — rotate the team's RF key/frequency directly from the spacecraft.
: [`downlink`](#downlink) — flush the on-board cache to the ground station.
: [`jammer`](#jammer) — activate / deactivate the jammer payload.

Maintenance
: [`reset`](#reset) — reboot a malfunctioning component.

Propulsion
: [`thrust`](#thrust) — fire a thruster for a duration.

RPO
: [`rendezvous`](#rendezvous) — hold a relative position in another spacecraft's LVLH frame.
: [`docking`](#docking) — initiate or release a docking with another spacecraft.

Schedule management
: [`get_schedule`](#get_schedule) — request the on-board command queue.
: [`remove_command`](#remove_command) — cancel a scheduled command.
: [`update_command`](#update_command) — modify a scheduled command's time or args.

---

## `guidance`

Sets the spacecraft's pointing mode through the on-board ADCS. Each `pointing` value uses a different subset of `Args`; only the relevant keys are read.

```json
{
  "Asset": "A3F2C014",
  "Command": "guidance",
  "Time": 0,
  "Args": {
    "pointing": "sun",
    "target": "Solar Panel",
    "alignment": "+z"
  }
}
```

### Args (common)

| Argument | Default | Range / Values | Unit | Description |
| --- | --- | --- | --- | --- |
| `pointing` | `inertial` | `inertial`, `velocity`, `sun`, `nadir`, `ground`, `location`, `relative`, `idle` | — | Pointing law to engage. `idle` disables the controller and stops drawing reaction-wheel torque. Any unrecognised value also falls through to `idle`. |
| `target` | _(spacecraft body)_ | component name | — | Component on the spacecraft whose face should align with the pointing direction. Case-insensitive match against the spacecraft's component list (see [`list_entity`](ground-requests.md#list_entity)). If omitted, the alignment is interpreted in the spacecraft body frame. |
| `alignment` | `+z` | `+x`, `-x`, `+y`, `-y`, `+z`, `-z` | — | Which axis of the `target` to point along the pointing direction. Most components (cameras, panels, antennas) have their working face on `+z`. |

### Args by `pointing` mode

**`inertial`** — hold a fixed attitude in the inertial frame.

| Argument | Default | Range | Unit | Description |
| --- | --- | --- | --- | --- |
| `pitch` | `0.0` | `-90 … 90` | deg | Pitch component of the target attitude. |
| `roll` | `0.0` | `-180 … 180` | deg | Roll component of the target attitude. |
| `yaw` | `0.0` | `-180 … 180` | deg | Yaw component of the target attitude. |

**`velocity`**, **`sun`** — no extra arguments. Aligns `target`/`alignment` with the velocity vector or the Sun direction respectively.

**`nadir`** — point at the centre of a celestial body.

| Argument | Default | Values | Description |
| --- | --- | --- | --- |
| `planet` | `earth` | `sun`, `earth`, `moon`, `mars` | Body to point at. |

**`ground`** — point at a named ground station from the scenario.

| Argument | Default | Description |
| --- | --- | --- |
| `station` | `singapore` | Name of a ground station (case-insensitive). Available names come from [`list_stations`](ground-requests.md#list_stations). |

**`location`** — point at a fixed lat/lon/alt on a celestial body.

| Argument | Default | Range | Unit | Description |
| --- | --- | --- | --- | --- |
| `latitude` | `0.0` | `-90 … 90` | deg | Latitude on `planet`. |
| `longitude` | `0.0` | `-180 … 180` | deg | Longitude on `planet`. |
| `altitude` | `0.0` | `0 … 100000` | m | Altitude above the surface. |
| `planet` | `earth` | `sun`, `earth`, `moon`, `mars` | — | Body the lat/lon is on. |

**`relative`** — point at another spacecraft (RPO).

| Argument | Default | Description |
| --- | --- | --- |
| `spacecraft` | _(none)_ | Asset ID of another spacecraft in the simulation. If the ID does not resolve, the controller engages but holds its current target. |

### Notes

- After `idle`, the spacecraft will drift; nothing will resist disturbance torques. Re-issue a non-idle `guidance` command to take control again.
- Switching modes is instantaneous in the controller, but the spacecraft physically slews under the dynamics of its reaction wheels and inertia. Allow time before issuing a [`capture`](#capture).

---

## `downlink`

Flushes telemetry, imagery, and other cached data from the spacecraft to its ground station, or arms the spacecraft to auto-downlink on every Ping.

```json
{
  "Asset": "A3F2C014",
  "Command": "downlink",
  "Time": 0,
  "Args": { "downlink": true, "ping": false }
}
```

| Argument | Default | Values | Description |
| --- | --- | --- | --- |
| `downlink` | `true` | `true`, `false` | Whether to perform a one-shot downlink now. `false` makes the command a no-op for the immediate flush — useful if you only want to change the `ping` flag. |
| `ping` | `false` | `true`, `false` | If `true`, the spacecraft auto-downlinks every Ping (~20 sim s). Keeps caches drained but consumes more transmitter power. |

### Notes

- Downlink only succeeds while the link budget allows it. If the spacecraft is below the horizon or jammed, the data stays in the cache and will be flushed on the next successful pass.
- Imagery is large. With `ping = true` and an active camera, expect the downlink frequency to be saturated by image traffic.

---

## `camera`

Configures a camera on the spacecraft. This does **not** capture an image (unless `sample = true`); it sets up the optics so a subsequent [`capture`](#capture) produces the image you expect.

```json
{
  "Asset": "A3F2C014",
  "Command": "camera",
  "Time": 0,
  "Args": {
    "target": "Camera",
    "resolution": 512,
    "fov": 45.0,
    "monochromatic": false
  }
}
```

| Argument | Default | Range | Unit | Description |
| --- | --- | --- | --- | --- |
| `target` | _(none)_ | component name | — | Camera component to configure (case-insensitive). `Camera` matches the default sensor on most scenarios. |
| `monochromatic` | `false` | `true`, `false` | — | Capture in greyscale. Saves downlink budget at the cost of colour resolution. |
| `resolution` | `512` | `128 … 1024` | px | Image side length in pixels. Cameras are square: total pixels = `resolution²`. |
| `coc` | `0.03` | `0.0 … 1.0` | mm | Circle of confusion — acceptable blur on the sensor for depth-of-field calculations. |
| `pixel_pitch` | `0.012` | `0.0 … 1.0` | mm | Distance between adjacent pixel centres. Smaller pitch + smaller resolution → smaller sensor → tighter crop. |
| `focusing_distance` | `4.0` | `0.0 … 1000000.0` | m | Distance to the in-focus plane. Use the approximate range to your imaging target. |
| `aperture` | `1.0` | `0.0 … 1000.0` | mm | Lens diameter. Larger = brighter image and wider FOV. |
| `focal_length` | `100.0` | `0.0 … 1000.0` | mm | Distance from nodal point to sensor. Longer = narrower FOV. |
| `fov` | `60.0` | `0.01 … 150.0` | deg | Field of view, used together with focal length and aperture for the projected image. |
| `sample` | `false` | `true`, `false` | — | Capture and downlink a 32×32 preview on the next Ping. Useful for confirming the optics without committing to a full image. |

### Notes

- The configuration sticks until the next `camera` command — multiple `capture` calls can share the same setup.
- An imager with `monochromatic = true` followed by a colour `capture` returns greyscale; the capture command does not override imaging mode.

---

## `capture`

Captures a still image with a previously configured camera and stores it in the on-board cache for the next downlink.

```json
{
  "Asset": "A3F2C014",
  "Command": "capture",
  "Time": 0,
  "Args": { "target": "Camera", "name": "Earth_pass_1" }
}
```

| Argument | Default | Description |
| --- | --- | --- |
| `target` | _(none)_ | Camera component to capture from (case-insensitive). Must be the same kind of imager as configured by [`camera`](#camera). |
| `name` | `image` | Image label. Stored in the **first 50 bytes** of the image data as ASCII; longer names are truncated, shorter names are padded. The remaining bytes are the JPEG payload. |

### Notes

- The image is not downlinked automatically. Send a [`downlink`](#downlink) (or pre-arm with `ping = true`) to get it to the ground.
- If the spacecraft is not pointed correctly, the resulting image will be of empty space. Use a [`guidance`](#guidance) ahead of the capture and allow time for the slew.

---

## `telemetry`

Changes the **link parameters** of the spacecraft's communication system through a normal uplink: frequency, RF encryption key (Caesar), and ground-side bandwidth. The change is propagated to the ground station so both ends stay in sync.

```json
{
  "Asset": "A3F2C014",
  "Command": "telemetry",
  "Time": 0,
  "Args": { "frequency": 475.0, "key": 17, "bandwidth": 1.0 }
}
```

| Argument | Default | Range | Unit | Description |
| --- | --- | --- | --- | --- |
| `frequency` | `0` | `0 … 10000` | MHz | New uplink/downlink carrier frequency. |
| `key` | `0` | `0 … 255` | — | New Caesar key for the RF link. |
| `bandwidth` | _(unchanged)_ | — | MHz | New ground-receiver bandwidth. Optional — omit to leave the bandwidth alone. |

### Notes

- The change is **brokered through the ground controller**. The spacecraft is told the new settings over the *current* link, then both ends switch. If the new settings are unreachable from the spacecraft (out of range, jammed), the spacecraft may end up on the new key/frequency while the ground stays on the old one — recover with another `telemetry` command from ground or with [`encryption`](#encryption) from the spacecraft.
- See also [`set_telemetry`](ground-requests.md#set_telemetry), the request you usually invoke from a client. It produces this command internally.

---

## `encryption`

Rotates the team's password, RF Caesar key, and frequency directly from the spacecraft side. Unlike `telemetry`, this command **requires the team password** in `Args` as a credential — it must come from someone who already knows the team secret, not from a relayed RF message.

```json
{
  "Asset": "A3F2C014",
  "Command": "encryption",
  "Time": 0,
  "Args": {
    "password": "AB12CD",
    "frequency": 480.0,
    "key": 42
  }
}
```

| Argument | Default | Range | Unit | Description |
| --- | --- | --- | --- | --- |
| `password` | _(required)_ | 6-char alphanumeric | — | The team's current XOR password. The spacecraft rejects the command if this does not match. |
| `frequency` | _(required)_ | `0 … 10000` | MHz | New RF frequency. |
| `key` | _(required)_ | `0 … 255` | — | New Caesar key. |

### Notes

- Triggers a spacecraft **reboot** while the new settings come up. Expect a brief telemetry blackout.
- The password in `Args` is **redacted** from any internal command-execution logs to avoid accidental disclosure.
- Use this when you suspect the team password or RF key has leaked. Coordinate with the ground side to expect the new key, or you'll fail to decode subsequent downlinks.

---

## `jammer`

Activates or deactivates the jammer payload. The jammer outputs noise on one or more frequencies, drains battery, and disrupts other teams' RF — but only while the spacecraft has line of sight.

```json
{
  "Asset": "A3F2C014",
  "Command": "jammer",
  "Time": 0,
  "Args": {
    "active": true,
    "frequencies": [474.0, 480.0],
    "power": 25.0
  }
}
```

| Argument | Default | Range | Unit | Description |
| --- | --- | --- | --- | --- |
| `active` | `false` | `true`, `false` | — | Master switch. Set `false` to stop the jammer immediately. |
| `frequencies` | `[]` | `0 … 10000` per entry | MHz | Array of frequencies to broadcast on. Multiple entries → multi-band jamming. |
| `power` | `0` | `0 … 10000` | W | Transmit power per frequency. Higher power = wider effective range, faster battery drain. |

### Notes

- If the spacecraft has no jammer component, the command is a no-op.
- Jamming yourself is possible — if `frequencies` overlaps your own RF link, your downlinks will degrade.

---

## `reset`

Power-cycles a single component. Use this when telemetry shows a component is malfunctioning or has been disabled by a scenario event.

```json
{
  "Asset": "A3F2C014",
  "Command": "reset",
  "Time": 0,
  "Args": { "target": "Battery" }
}
```

| Argument | Default | Description |
| --- | --- | --- |
| `target` | _(none)_ | Name of the component to reset (case-insensitive). Match against [`list_entity`](ground-requests.md#list_entity). |

### Notes

- A reset usually triggers a **spacecraft reboot**, which can take ~60 sim s before the spacecraft is responsive again.
- Resetting a healthy component is safe but wasteful — you'll lose telemetry for the duration of the reboot.

---

## `thrust`

Fires a thruster at its rated force for a fixed duration. Direction is determined by the thruster's mounting; this command cannot gimbal it.

```json
{
  "Asset": "A3F2C014",
  "Command": "thrust",
  "Time": 0,
  "Args": { "target": "Thruster +X", "active": true, "duration": 5.0 }
}
```

| Argument | Default | Unit | Description |
| --- | --- | --- | --- |
| `target` | _(none)_ | — | Thruster component name. Required if the spacecraft has more than one. |
| `active` | `false` | — | `true` to start firing, `false` to stop early (overrides `duration`). |
| `duration` | `0` | s | Time to fire, in simulation seconds. After this elapses the thruster shuts off automatically. |

### Notes

- Thrust consumes fuel from the spacecraft's tank model. Out of fuel = no thrust regardless of command.
- For larger maneuvers, plan a sequence of `thrust` commands at different sim times rather than one long burn — the dynamics may evolve mid-burn.

---

## `rendezvous`

Engages a perch-mode hold relative to another spacecraft. The chaser holds a fixed offset in the **target's LVLH frame**:

- `X` = radial (away from the central body)
- `Y` = along the velocity vector
- `Z` = orbit-normal (radial × velocity)

```json
{
  "Asset": "A3F2C014",
  "Command": "rendezvous",
  "Time": 0,
  "Args": {
    "target": "B7E9D210",
    "active": true,
    "offset": [0, -100, 0]
  }
}
```

| Argument | Default | Range | Unit | Description |
| --- | --- | --- | --- | --- |
| `target` | _(none)_ | asset ID | — | The spacecraft to perch relative to. The LVLH frame is anchored on this target. |
| `active` | `false` | `true`, `false` | — | `true` engages the controller; `false` releases it. |
| `offset` | `[0, 0, 0]` | `[-10000, 10000]` per axis | m | Desired `[X, Y, Z]` offset in the target's LVLH frame. |

### Notes

- The spacecraft must have RPO enabled in the scenario. If `rpo_enabled` is `false` in [`list_assets`](ground-requests.md#list_assets), the command is silently ignored.
- The maneuver uses the spacecraft's existing thrusters/control authority — bring fuel.

---

## `docking`

Initiates or releases a docking with another team's spacecraft. The current spacecraft must have at least one Docking Adapter component and RPO must be enabled. Docking only completes once the two spacecraft are physically close enough — the command sets the target; the simulation does the connection.

```json
{
  "Asset": "A3F2C014",
  "Command": "docking",
  "Time": 0,
  "Args": {
    "target": "B7E9D210",
    "component": "Docking Port +Z",
    "dock": true
  }
}
```

| Argument | Default | Description |
| --- | --- | --- |
| `target` | _(none)_ | Asset ID of the spacecraft to dock with / undock from. |
| `component` | _(none)_ | **Name** of the docking adapter on the target (not its component ID). Match to the `name` (or `class` if `name` is absent) in the target's [`list_entity`](ground-requests.md#list_entity) component list. |
| `dock` | _(none)_ | `true` to dock, `false` to undock. |

### Notes

- Plan your approach with [`rendezvous`](#rendezvous) first. The docking command sets intent; physics handles capture.
- Once docked, both spacecraft become rigidly attached until an explicit `dock = false` is issued.

---

## `get_schedule`

Asks the spacecraft to report all currently queued (scheduled, not-yet-executed) commands. The spacecraft replies with a **Schedule Report** telemetry message; see [Concepts → Telemetry](../concepts/telemetry.md#schedule-report) for the wire format.

```json
{
  "Asset": "A3F2C014",
  "Command": "get_schedule",
  "Time": 0,
  "Args": {}
}
```

No arguments are read.

### Notes

- The reply is delivered via the normal Downlink path, so it's subject to RF availability. If you don't see one, you may need to wait for a pass or downlink window.
- Sensitive `Args` (passwords, etc.) are redacted in the report.

---

## `remove_command`

Removes a previously scheduled command from the on-board queue.

```json
{
  "Asset": "A3F2C014",
  "Command": "remove_command",
  "Time": 0,
  "Args": { "id": "c0a8b39e-..." }
}
```

You may identify the command in one of two ways:

| Argument | Description |
| --- | --- |
| `id` | The unique ID of the scheduled command, as reported in the Schedule Report. **Preferred** — unambiguous. |
| `time` + `command` | Fallback. The spacecraft removes the **first** queued command whose `Time` and `Command` name both match. If multiple match, only one is removed (subsequent calls remove the next). |

If neither identifier matches a queued command, the request is a silent no-op. Issue [`get_schedule`](#get_schedule) afterwards to confirm.

---

## `update_command`

Modifies the `Time` and/or `Args` of a previously scheduled command without removing/re-adding it.

```json
{
  "Asset": "A3F2C014",
  "Command": "update_command",
  "Time": 0,
  "Args": {
    "id": "c0a8b39e-...",
    "time": 1200.0,
    "args": { "pointing": "nadir" }
  }
}
```

| Argument | Description |
| --- | --- |
| `id` | Scheduled command's unique ID (from the Schedule Report). |
| `time` | _(optional)_ New execution time, in simulation seconds. **Must be in the future** relative to the current sim time, or the update is rejected. |
| `args` | _(optional)_ Replacement `Args` object. Replaces the whole `Args`, not merged. |

### Notes

- Updating an `id` that doesn't exist is a no-op.
- Updating a `time` to a value that is already in the past is rejected; the command is left untouched.

---

## Worked example: a small uplink sequence

A typical "image Earth on the next pass" sequence:

```json
{ "Asset": "A3F2C014", "Command": "guidance", "Time": 0,
  "Args": { "pointing": "nadir", "target": "Camera", "alignment": "+z", "planet": "earth" } }
```

```json
{ "Asset": "A3F2C014", "Command": "camera", "Time": 0,
  "Args": { "target": "Camera", "resolution": 1024, "fov": 30.0 } }
```

```json
{ "Asset": "A3F2C014", "Command": "capture", "Time": 600.0,
  "Args": { "target": "Camera", "name": "Earth_t600" } }
```

```json
{ "Asset": "A3F2C014", "Command": "downlink", "Time": 700.0,
  "Args": { "downlink": true } }
```

The first two run immediately (slew to nadir, set up optics). The capture is scheduled for `t = 600 s`, after which the downlink at `t = 700 s` flushes the JPEG to the ground station.

---

## Next

- [Concepts → Commands and scheduling](../concepts/commands-and-scheduling.md) — lifecycle and validation rules.
- [Ground requests](ground-requests.md) — how to discover asset IDs, component names, and station names referenced above.
- [Guides → Decoding telemetry](../guides/decoding-telemetry.md) — how to read the Ping / Schedule Report messages that confirm command execution.
