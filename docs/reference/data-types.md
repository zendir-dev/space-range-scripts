# Data Types

A flat reference for every type, unit, and convention used across the Space Range API. If you've wondered "should this latitude be in degrees or radians?" or "is this frequency in Hz or MHz?" — this is the page.

For wire layouts, see [Packet formats](packet-formats.md). For the higher-level treatment of where these types come from, the relevant [Concepts](../concepts/teams-and-assets.md) page is usually the right entry point.

---

## Primitive types

These are the building blocks of every JSON payload and CCSDS packet.

| Logical type | JSON form | Wire form (binary) | Notes |
| --- | --- | --- | --- |
| **Boolean** | `true` / `false` | 1 byte (`0` / `1`) | Lowercase in JSON. |
| **Integer** | bare number, no decimal point | 32-bit signed, two's complement, big-endian | Range: `−2,147,483,648 .. 2,147,483,647`. |
| **Float** | bare number, optional decimal | 32-bit IEEE-754, big-endian | C++ `double` fields are downcast to `float32` on the XTCE wire. |
| **String** | `"…"` | 16-bit BE length prefix + UTF-8 bytes | Max practical length ~64 KiB; in practice strings are ≤ 256 bytes. |
| **Bytes** | usually base64-encoded string | raw bytes | Used inside [`transmit_bytes`](../api-reference/ground-requests.md#transmit_bytes) and `Uplink Intercept` payloads. |
| **DateTime** | ISO-8601 UTC string (`"2026-04-15T08:30:12Z"`) | 64-bit signed integer of Unreal `Ticks` (100 ns), big-endian | JSON wire uses ISO-8601; binary wire uses ticks. |
| **Vector2** | JSON array of 2 numbers `[x, y]` | two `float64` BE | Studio always serialises as 64-bit on the wire even though JSON shows them as plain numbers. |
| **Vector3** | JSON array of 3 numbers `[x, y, z]` | three `float64` BE | |
| **Vector4** | JSON array of 4 numbers `[x, y, z, w]` | four `float64` BE | |

JSON numbers are always sent as decimal literals (no hex, no scientific notation in practice — though the spec allows both). When in doubt, prefer integer JSON for integer fields (`"Time": 0`, not `"Time": 0.0`) — it round-trips cleanly through every parser.

---

## Identifiers

Every entity in Space Range has at least one identifier. They have specific shapes and you should pick the right one for each API surface.

| Identifier | Shape | Example | Used by |
| --- | --- | --- | --- |
| **Game name** | non-empty string, often uppercase | `"SPACE RANGE"` | MQTT topic `<GAME>` segment. Case-sensitive — Studio's configured value wins. |
| **Team ID** | integer, 6 digits in shipped scenarios | `111111` | MQTT topic `<TEAM>` segment, `team_id` field in admin responses. Must be unique within a scenario. |
| **Team password** | 6-character ASCII alphanumeric | `"AB12CD"` | XOR key for team-scoped topics. Case-sensitive. |
| **Admin password** | 6-character ASCII alphanumeric | `"ADMINP"` | XOR key for `Admin/*` topics. Distinct from any team password. |
| **Asset ID** | 8-character lowercase / mixed-case hex | `"A3F2C014"` | `asset_id` field in commands and ground responses, `Asset` field in command envelopes. |
| **Spacecraft scenario ID** | snake_case string from the scenario JSON | `"SC_001"` | Internal to scenario authoring; resolved to `Asset ID` at runtime. |
| **Component name** | string, case-insensitive at runtime | `"Camera"`, `"Solar Panel +X"` | `target` field of commands. Must match what's listed in [`list_entity`](../api-reference/ground-requests.md#list_entity). |
| **Ground station name** | string, exact match | `"Madrid"`, `"Easter Island"` | Returned by [`list_stations`](../api-reference/ground-requests.md#list_stations); referenced in scenario JSON. |
| **Caesar key** | integer `0–255` | `17` | RF-layer cipher key. Per team. |
| **Frequency** | float MHz | `500.0`, `2230.5` | `frequency` field across commands and requests. |
| **Command ID** | integer | `123456` | Spacecraft-assigned; `ID` in Ping/Schedule Report `Commands` arrays and in `Args` for [`update_command`](../api-reference/spacecraft-commands.md#update_command) / [`remove_command`](../api-reference/spacecraft-commands.md#remove_command); matches `command_executed` events. |
| **Intercept enabled** | boolean | `true` / `false` | Scenario/controller flag `enable_intercept`. Surfaced in API responses as `intercept_enabled` on [`list_assets`](../api-reference/ground-requests.md#list_assets), [`admin_list_team`](../api-reference/admin-requests.md#admin_list_team), [`admin_query_data`](../api-reference/admin-requests.md#admin_query_data), and (when filtering by asset) [`admin_query_events`](../api-reference/admin-requests.md#admin_query_events). When `true`, the spacecraft retains raw uplink intercept records for SIGINT / replay. |
| **Request ID** | integer (echoed) | `42` | `req_id` field. Free for the client to use to correlate requests with responses. |
| **Instance** | integer, monotonic | `3` | `instance` field of Session topic; increments on simulation reset. |

### Asset ID derivation

Asset IDs are an opaque 8-character hex code derived at runtime from the scenario asset definition. Don't try to construct them — read them from [`list_assets`](../api-reference/ground-requests.md#list_assets) once per session and cache.

### Team ID conventions

In shipped scenarios:

- Tutorial / testing: `111111`, `222222`, … (memorable, easy to type).
- Competition: 6-digit pseudo-random IDs (`584203`, `917462`, …) so muscle memory doesn't lead operators to the wrong team.

Either convention is legal. The only hard rules are uniqueness per scenario and that they fit in `int32`.

---

## Time

Three time bases coexist; they are **not** interchangeable.

| Type | Unit | Origin | Where you see it |
| --- | --- | --- | --- |
| **Simulation time** | seconds since `t = 0` of the current instance | Studio's clock | `time` field of session, `Time` field of commands, `SimulationTime` in CCSDS secondary header, `sim_time` in admin events. |
| **UTC** | ISO-8601 datetime | wall clock | `utc` field of session, secondary-header `CoarseTime + FineTime`, `time` field of `admin_query_*` responses. |
| **Real time** | seconds since wall-clock epoch (varies) | client only | Internal to your client code. **Never** appears on the wire. |

### Conversion

The session topic is the bridge — every Session message gives you both:

```python
sim_time   = msg["time"]    # 742.18
utc_time   = msg["utc"]     # "2026-04-15T08:30:12Z"
instance   = msg["instance"]
```

Use `sim_time` for everything that needs to interoperate with command schedules, telemetry timestamps, and link-budget calculations. Use `utc_time` only for human-readable logs or correlation with external systems.

### Speed

The simulation can run faster or slower than wall-clock. The current speed is exposed by [`admin_get_simulation`](../api-reference/admin-requests.md#admin_get_simulation):

```json
{ "state": "Running", "speed": 4.0, "time": 742.18 }
```

`speed = 4.0` means 4 sim-seconds elapse per real-second. **All scheduled `Time` values remain in simulation seconds**, regardless of speed; speed only changes how fast the clock advances toward them.

---

## Coordinates and units

Default conventions, used unless a specific endpoint says otherwise.

### Geographic

| Field | Unit | Range | Notes |
| --- | --- | --- | --- |
| `latitude` | degrees | `−90 .. +90` | Positive = North. WGS84. |
| `longitude` | degrees | `−180 .. +180` | Positive = East. WGS84. |
| `altitude` | metres | depends | Altitude above the surface in metres unless stated otherwise. |
| `heading` | degrees | `0 .. 360` | Compass heading. `0` = North, `90` = East. |

### Orbital

The `orbit.values` array in scenario JSON is a 6-element classical Keplerian set:

| Index | Element | Symbol | Unit | Notes |
| --- | --- | --- | --- | --- |
| 0 | Semi-major axis | `a` | km | Relative to the central body's center. |
| 1 | Eccentricity | `e` | unitless | `0 = circular`. |
| 2 | Inclination | `i` | degrees | `0 = equatorial`. |
| 3 | Right ascension of ascending node | `Ω` | degrees | |
| 4 | Argument of periapsis | `ω` | degrees | |
| 5 | True anomaly | `ν` | degrees | Initial position along the orbit. |

`orbit.offset` is the same shape but interpreted as small per-element perturbations to break degeneracies between co-located twin spacecraft.

### Spacecraft body frame

| Axis | Convention | Visual |
| --- | --- | --- |
| `+x`, `-x` | along the spacecraft's primary roll axis | typically along the bus length |
| `+y`, `-y` | the secondary axis | perpendicular to roll, in the orbital plane |
| `+z`, `-z` | the third axis | nominally nadir / zenith |

Component `position` is in **metres** in the spacecraft body frame; `rotation` is in **degrees** as Euler angles (Yaw, Pitch, Roll). These follow Unreal Engine conventions internally but are exposed in standard SI units at the API surface.

### Forces & dynamics

| Field | Unit | Notes |
| --- | --- | --- |
| `mass` | kg | |
| `inertia_tensor` | kg·m² | 3×3 symmetric matrix in the body frame. |
| `force` | N | Linear thrust. |
| `torque` | N·m | Body-frame torque. |
| `delta_v` | m/s | Burn magnitudes for [`thrust`](../api-reference/spacecraft-commands.md#thrust). |
| `angular_velocity` | rad/s | Body-frame spin rate components. |
| `attitude` | quaternion `[x, y, z, w]` | Unit quaternion, scalar-last. |

### Power

| Field | Unit | Range | Notes |
| --- | --- | --- | --- |
| `Battery` (Ping) | fraction | `0.0–1.0` | State of charge. |
| `Memory` (Ping) | fraction | `0.0–1.0` | Storage fill. |
| `Nominal Capacity` (config) | Wh | `> 0` | Battery capacity. |
| `Charge Fraction` (config) | fraction | `0.0–1.0` | Initial charge. |
| `Power` (Jammer) | watts | `≥ 0` | Transmit power. |
| `Antenna Gain` (Receiver / Transmitter / Jammer) | dB | `≥ 0` | RF antenna gain. |
| `Efficiency` (Solar Panel) | fraction | `0.0–1.0` | Conversion efficiency. |
| `Area` (Solar Panel) | m² | `> 0` | Active panel area. |

### RF

| Field | Unit | Range | Notes |
| --- | --- | --- | --- |
| `frequency` | MHz | `0–10000` (typical `100–10000`) | Carrier frequency on commands and `set_telemetry`. |
| `bandwidth` | Hz | `> 0` | Channel bandwidth. |
| `snr_db` | dB | any | Signal-to-noise ratio in link budgets. |
| `link_margin_db` | dB | any | Margin above closure threshold. |
| `range_km` | km | `≥ 0` | Spacecraft-station slant range. |

### Camera

| Field | Unit | Range | Notes |
| --- | --- | --- | --- |
| `fov` | degrees | `0.1–90` | Half- or full-angle depending on camera config — check the [`camera`](../api-reference/spacecraft-commands.md#camera) reference. |
| `aperture` | f-stop | `0.7–22` | Optical aperture. |
| `iso` | unitless | `100–25600` | Sensor sensitivity. |
| `shutter` | seconds | `1e-6 .. 1.0` | Exposure time. |

---

## Enumerations

The string values that show up as enums on the wire.

### Spacecraft state (`Ping.State`)

| Value | Meaning |
| --- | --- |
| `NOMINAL` | Healthy, operating normally. |
| `LOW` | Battery in the low-power band. Component duty cycles reduced. |
| `SAFE` | Safe mode. Most components disabled. |
| `TRANSMIT` | Currently bursting telemetry on the link. Brief and transient. |
| `FULL STORAGE` | Storage at capacity; new data is being dropped. |
| `REBOOTING` | Just executed a `reset` or `encryption` rotation; offline for the configured `reset_interval`. |

### Frame format (`EDataFormatType`)

| Value | Symbol | Meaning |
| --- | --- | --- |
| `0` | `None` | Empty / sentinel. |
| `1` | `Message` | CCSDS Space Packet (Ping, Schedule Report, …). |
| `2` | `Media` | 50-byte name header + file bytes. |
| `3` | `UplinkIntercept` | 32-byte intercept header + raw on-air bytes. |

### Simulation state (`admin_get_simulation` / `admin_set_simulation`)

| Value | Meaning |
| --- | --- |
| `Running` | Time advancing at `speed × real-time`. |
| `Paused` | Time frozen. State preserved. |
| `Stopped` | **Reset.** All state wiped, `t = 0`, `instance` increments. |

### Pointing modes (`guidance` command)

| Value | Meaning |
| --- | --- |
| `idle` | No active pointing. Default for unrecognised modes. |
| `sun` | Track the Sun. |
| `nadir` | Track the planet centre below. |
| `ground` | Track the named ground station. |
| `relative` | Track another spacecraft's position. Requires `spacecraft` argument. |

### Command outcome (`Ping.Commands[].Success`)

A boolean — `true` if execution succeeded, `false` otherwise. The reason for failure is **not** in the Ping; check Studio's logs (admin) or correlate against the `command_failed` admin event.

### Question types (`scenario.questions[].type`)

| Value | Answer JSON shape | Notes |
| --- | --- | --- |
| `text` | `{ "value": "…" }` | Case-insensitive match. |
| `number` | `{ "value": 7, "tolerance": 0 }` | `tolerance` ≥ 0. |
| `select` | `{ "options": ["…"], "value": <index> }` | `value` is the **index** of the correct option. |
| `checkbox` | `{ "options": ["…"], "value": [<indices>] }` | `value` is an array of correct indices (any order). |

### Uplink-intercept flags

| Bit | Mask | Name |
| --- | --- | --- |
| 0 | `0x01` | `Truncated` |
| 1 | `0x02` | `DecodeOk` |
| 2 | `0x04` | `ParseOk` |
| 3 | `0x08` | `AddressedToUs` |

### Common admin event types

The most-seen `type` values in [`admin_event_triggered`](../api-reference/admin-requests.md#admin_event_triggered) and [`admin_query_events`](../api-reference/admin-requests.md#admin_query_events). The list grows over time; treat it as non-exhaustive.

| Type | Trigger |
| --- | --- |
| `command_sent` | Operator published an uplink. |
| `command_executed` | Spacecraft executed a queued command. |
| `command_failed` | Spacecraft attempted a command and failed. |
| `capture_taken` | Camera captured an image. |
| `downlink_sent` | Spacecraft transmitted bytes. |
| `downlink_received` | Ground station received bytes. |
| `jamming_started` | Jammer was activated. |
| `jamming_stopped` | Jammer was deactivated. |
| `link_lost` | Link budget closed → open transition. |
| `link_restored` | Link budget open → closed transition. |
| `safe_entered` | Spacecraft entered SAFE mode. |
| `safe_exited` | Spacecraft exited SAFE mode. |
| `rebooted` | Spacecraft rebooted (after `reset` or `encryption`). |
| `question_answered` | Team submitted an answer to a scenario question. |
| `scenario_event_triggered` | A scripted scenario event fired. |

---

## JSON conventions

### Casing

Two conventions are used, depending on the API:

| API surface | JSON key style | Examples |
| --- | --- | --- |
| **Spacecraft uplink commands** (`<TEAM>/Uplink`) | **PascalCase** | `Asset`, `Command`, `Time`, `Args` |
| **Ground / Admin requests + responses** | **lowercase** (snake_case for multi-word) | `type`, `req_id`, `args`, `asset_id` |
| **Telemetry payloads** (CCSDS user data) | **PascalCase** | `State`, `Battery`, `Commands`, `UplinkInterceptDataBytes` |
| **Scenario JSON** | **lowercase** (snake_case), except `events[]` which uses **PascalCase** | `teams`, `assets`, `space_assets` ; `Enabled`, `Time`, `Repeat` |

> **The most common bug** when integrating Space Range from a custom client is sending lowercase keys to the spacecraft uplink (which Studio rejects). Double-check your envelope casing against [Spacecraft commands → Envelope](../api-reference/spacecraft-commands.md#envelope) before debugging anything else.

### Optional fields

Optional fields default in one of two ways:

- **Type-default** (`""`, `0`, `false`, `[]`) when omitted.
- **Endpoint-specific default** noted in the API reference for that endpoint.

A missing optional field is **never** an error; an unrecognised key is silently ignored. There is no "extra keys" warning. If you typoed a key, Studio happily executes the command without it.

### Strings inside strings

Several telemetry fields carry JSON-encoded strings as their value:

| Field | Where | Notes |
| --- | --- | --- |
| `Commands` (Ping) | telemetry | `json.loads(ping["Commands"])` to recover the array. |
| `Commands` (Schedule Report) | telemetry | same |
| `Args` (inside `Commands` entries) | nested | `json.loads(entry["Args"])` to recover the args object. |
| Some response `args` fields | Ground/Admin responses | Check `space_range_scripts.utils.decode_payload` for the unwrap heuristic. |

This is intentional — XTCE wants fixed-shape fields, and a JSON-string-of-array is the simplest way to carry variable-length data inside a typed schema. Always remember to apply the second-stage unwrap.

### Sensitive-key redaction

Inside `Commands` arrays in telemetry, the `Args` field has its `password` (and any future credential keys) **redacted** before transmission. You'll see something like:

```json
{
  "Command": "encryption",
  "Args":    "{\"password\":\"***\",\"frequency\":478.0,\"key\":233}"
}
```

The redaction is applied server-side; clients never see the plaintext password in any telemetry stream.

---

## Encoding for `transmit_bytes`

The [`transmit_bytes`](../api-reference/ground-requests.md#transmit_bytes) request lets a ground station emit arbitrary bytes on a frequency. The `data` field can be in any of these encodings, selected by `encoding`:

| `encoding` | `data` form | Notes |
| --- | --- | --- |
| `base64` (or `b64`) | RFC 4648 base64 string | Most reliable for arbitrary binary. |
| `hex` | continuous hex string, optional spaces | Case-insensitive. |
| `utf8` | plain UTF-8 string | Bytes are the UTF-8 encoding of the input. |
| `ascii` | plain ASCII string | High bits stripped if present. |

The maximum payload size is bounded by the frame format on the air — frames longer than ~1 KB are truncated when intercepted, but the transmit path itself accepts longer payloads.

---

## Constants worth knowing

| Constant | Value | Meaning |
| --- | --- | --- |
| `Session` cadence | ~3 Hz | Heartbeat rate of the unencrypted Session topic. |
| Default `ping_interval` | `20.0` sim s | Ping cadence per spacecraft, scenario-configurable. |
| Default `reset_interval` | `60.0` sim s | Time spacecraft stays offline after a `reset`. |
| Default secondary header | 24 bytes | Sized in [Packet formats → Secondary Header](packet-formats.md#secondary-header-default-24-bytes). |
| Uplink Intercept `MaxRawPayloadBytes` | `1024` | Bytes captured from a frame; tail is dropped. |
| Uplink Intercept `Magic` | `0x5055495A` | "ZIUP" little-endian. |
| Uplink Intercept current `FormatVersion` | `2` | Older `1` records (no `ReceiverFrequency`) are still parseable. |
| 50 | `Media` name field width | Bytes; longer names truncated. |
| 6 | XOR password length | UTF-8 bytes (always ASCII alphanumeric in practice). |
| 8 | Asset ID length | Hex characters. |

---

## Next

- [Packet formats](packet-formats.md) — the byte layouts that consume these types.
- [Spacecraft commands](../api-reference/spacecraft-commands.md) — every endpoint's expected types in context.
- [Concepts → Teams and assets](../concepts/teams-and-assets.md) — the runtime view of the identifiers documented here.
