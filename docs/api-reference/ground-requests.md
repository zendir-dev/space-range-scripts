# Ground Requests

The ground controller exposes a request/response API for everything that isn't a spacecraft uplink: discovering assets, querying link budgets, transmitting raw bytes, talking to the AI assistant, and submitting scenario answers. This page documents every request type the team-side ground controller accepts.

For the topic plumbing, see [MQTT topics](mqtt-topics.md). For the underlying simulation concepts, see [Concepts → Teams and assets](../concepts/teams-and-assets.md).

---

## Topics

```text
Zendir/SpaceRange/<GAME>/<TEAM>/Request     (client → Studio)
Zendir/SpaceRange/<GAME>/<TEAM>/Response    (Studio → client)
```

Both topics are XOR-encrypted with the team password.

The `Response` topic also receives **unsolicited** push messages — `event_triggered` and `chat_response`. Dispatch by the `type` field, not by request order.

---

## Request envelope

```json
{
  "type":   "list_assets",
  "req_id": 0,
  "args":   { "...": "..." }
}
```

| Field | Type | Description |
| --- | --- | --- |
| `type` | `string` | The request type. See the index below. Case-insensitive on the wire. |
| `req_id` | `integer` | Caller-assigned correlation ID. The matching response carries the same value. Use `0` if you don't need to correlate; reuse is allowed. |
| `args` | `object` | Type-specific arguments. Omit the field if a request takes no arguments. |

## Response envelope

```json
{
  "type":    "list_assets",
  "req_id":  0,
  "args":    { "...": "..." },
  "success": true,
  "error":   ""
}
```

| Field | Type | Description |
| --- | --- | --- |
| `type` | `string` | Echoes the request `type` (or the unsolicited push name). |
| `req_id` | `integer` | Echoes the request `req_id`. |
| `args` | `object` | Type-specific response data. May be empty. |
| `success` | `boolean` | `true` if the request succeeded; `false` if it failed. |
| `error` | `string` | Populated only on failure. Empty string or omitted on success. |

If you publish a malformed request (missing `type`, unknown `type`, ill-formed JSON), Studio may not respond at all. Always set a sensible response timeout client-side rather than waiting indefinitely.

---

## Request index

Discovery
: [`list_assets`](#list_assets) — list this team's spacecraft.
: [`list_entity`](#list_entity) — components & jammer status for one spacecraft.
: [`list_stations`](#list_stations) — ground stations available to this team.
: [`get_packet_schemas`](#get_packet_schemas) — XTCE schemas for every telemetry packet.

Telemetry / RF
: [`get_telemetry`](#get_telemetry) — current frequency, key, bandwidth, and link budgets.
: [`set_telemetry`](#set_telemetry) — change the team's RF link parameters.
: [`transmit_bytes`](#transmit_bytes) — send arbitrary bytes off the ground transmitter at a chosen frequency.

AI assistant (optional, scenario-dependent)
: [`chat_query`](#chat_query) — ask the assistant a question about your spacecraft.
: [`chat_response`](#chat_response) — _(unsolicited)_ delivered when an answer is ready.

Scenario Q&A (optional, scenario-dependent)
: [`list_questions`](#list_questions) — list scenario questions for this team.
: [`submit_answer`](#submit_answer) — submit one or more answers.

Push notifications
: [`event_triggered`](#event_triggered) — _(unsolicited)_ a tracking event happened.

---

## `list_assets`

List the spacecraft owned by this team. The first call you typically make.

**Request**

```json
{ "type": "list_assets", "req_id": 0 }
```

No arguments.

**Response**

```json
{
  "type": "list_assets",
  "req_id": 0,
  "args": {
    "space": [
      { "asset_id": "A3F2C014", "name": "Microsat", "rpo_enabled": true, "intercept_enabled": true }
    ]
  },
  "success": true
}
```

| Field | Description |
| --- | --- |
| `space[]` | Array of space assets controlled by this team. |
| `space[].asset_id` | 8-character hex ID. Use this in the `Asset` field of any uplink command. |
| `space[].name` | Friendly name, with the team prefix stripped. |
| `space[].rpo_enabled` | `true` if rendezvous/proximity-ops is enabled for this asset (required for [`rendezvous`](spacecraft-commands.md#rendezvous) and [`docking`](spacecraft-commands.md#docking)). |
| `space[].intercept_enabled` | `true` if this spacecraft is configured to record raw uplink intercepts (pre-decode RF payloads into on-board storage for SIGINT / replay). Mirrors scenario `enable_intercept` on the controller. When `false`, no new intercept records are retained. |

---

## `list_entity`

Static schematic of one spacecraft: its components and jammer status. This is **not** live telemetry — it doesn't show power, sensor readings, or pointing state. Use telemetry downlinks for that.

**Request**

```json
{ "type": "list_entity", "req_id": 0, "args": { "asset_id": "A3F2C014" } }
```

| Argument | Description |
| --- | --- |
| `asset_id` | Asset ID from [`list_assets`](#list_assets). Must belong to this team or the request fails. |

**Response**

```json
{
  "type": "list_entity",
  "req_id": 0,
  "args": {
    "asset_id": "A3F2C014",
    "components": [
      { "name": "Solar Panel +X", "class": "Solar Panel", "component_id": 5, "is_imager": false },
      { "name": "Camera",         "class": "Camera",       "component_id": 12, "is_imager": true }
    ],
    "jammer": { "is_active": false, "frequency": 0.0, "power": 0.0 }
  },
  "success": true
}
```

| Field | Description |
| --- | --- |
| `asset_id` | Echoes the request. |
| `components[]` | One entry per on-board component. |
| `components[].name` | Friendly name. **Use this for `target` and `component` arguments in spacecraft commands.** Case-insensitive matching. |
| `components[].class` | Component class (e.g. `Camera`, `Solar Panel`, `Battery`). |
| `components[].component_id` | Index used as the **CCSDS APID-like discriminator** in telemetry messages, so you can tell which physical component a packet came from. |
| `components[].is_imager` | `true` for cameras / CCDs — components that can produce imagery. |
| `jammer` | Present only if the spacecraft has a jamming transmitter. |
| `jammer.is_active` | Whether the jammer is currently transmitting. |
| `jammer.frequency` | Active jam frequency in MHz. |
| `jammer.power` | Active jam power in watts. |

Errors: if the `asset_id` doesn't exist or doesn't belong to this team, `success` is `false` and `error` describes which.

---

## `list_stations`

List all ground stations connected to this team's ground controller.

**Request**

```json
{ "type": "list_stations", "req_id": 0 }
```

No arguments.

**Response**

```json
{
  "type": "list_stations",
  "req_id": 0,
  "args": {
    "stations": [
      { "name": "Singapore", "latitude": 1.35, "longitude": 103.82, "altitude": 16.0 }
    ]
  },
  "success": true
}
```

| Field | Description |
| --- | --- |
| `stations[].name` | Ground station name. Use this for `station` in [`guidance` (mode `ground`)](spacecraft-commands.md#guidance). |
| `stations[].latitude` | Geodetic latitude in degrees. |
| `stations[].longitude` | Geodetic longitude in degrees. |
| `stations[].altitude` | Altitude above the ellipsoid in metres. |

---

## `get_telemetry`

Current RF link parameters and link-budget snapshot for one spacecraft.

**Request**

```json
{ "type": "get_telemetry", "req_id": 0, "args": { "asset_id": "A3F2C014" } }
```

| Argument | Description |
| --- | --- |
| `asset_id` | Asset ID. |

**Response**

```json
{
  "type": "get_telemetry",
  "req_id": 0,
  "args": {
    "asset_id": "A3F2C014",
    "frequency": 500.0,
    "key": 10,
    "bandwidth": 1.0,
    "uplink": {
      "IsConnected": true,
      "Frequency": 500.0,
      "Distance": 67032.0,
      "SignalPower": 1.23e-12,
      "InterferencePower": 7e-13,
      "EffectiveSignalToNoise": 3.12,
      "BitErrorRate": 0.001,
      "TransmissionRate": 236782.0
    },
    "downlink": {
      "IsConnected": true,
      "Frequency": 500.0,
      "Distance": 67032.0,
      "SignalPower": 1.23e-12,
      "InterferencePower": 7e-13,
      "EffectiveSignalToNoise": 3.12,
      "BitErrorRate": 0.001,
      "TransmissionRate": 236782.0
    }
  },
  "success": true
}
```

| Field | Description |
| --- | --- |
| `frequency` | Team's nominal RF carrier frequency in MHz. |
| `key` | Team's Caesar key (0–255). The **RF** key, not the MQTT XOR password. |
| `bandwidth` | Receiver bandwidth in MHz. |
| `uplink` / `downlink` | Live link-budget objects (PascalCase keys, taken directly from the simulation's link-budget message). Most-useful fields: `IsConnected` (line of sight + signal above noise), `EffectiveSignalToNoise` (link margin), `BitErrorRate` (link quality), `TransmissionRate` (achievable bit/s). |

Additional fields not shown above may appear in `uplink` / `downlink` depending on the simulation build. Treat both objects as a free-form bag of link-budget telemetry.

---

## `set_telemetry`

Change the team's RF frequency, Caesar key, and ground bandwidth. Internally this dispatches a [`telemetry`](spacecraft-commands.md#telemetry) command to every spacecraft and updates the ground receiver to match.

**Request**

```json
{
  "type": "set_telemetry",
  "req_id": 0,
  "args": { "frequency": 480.0, "key": 17, "bandwidth": 1.0 }
}
```

| Argument | Default | Range | Unit | Description |
| --- | --- | --- | --- | --- |
| `frequency` | _(current)_ | `0 … 10000` | MHz | New RF carrier frequency. |
| `key` | _(current)_ | `0 … 255` | — | New Caesar key. |
| `bandwidth` | _(current)_ | — | MHz | New ground-receiver bandwidth. |

**Response**

```json
{ "type": "set_telemetry", "req_id": 0, "args": {}, "success": true }
```

No arguments on success. On failure, common `error` values:

- `"Already changing telemetry settings. Please wait before making another change."` — a previous `set_telemetry` is still propagating; wait ~1 sim s.
- `"Uplink not available. Cannot change telemetry settings at this time."` — the spacecraft is below the horizon or the link is jammed; try again on the next pass.
- `"No changes made to telemetry settings."` — every requested value matched the current setting.

### Notes

- The change applies to **all** spacecraft on the team. There is no per-asset variant.
- After a successful `set_telemetry`, expect a brief blackout while the spacecraft and ground both retune. Subscribe to the `event_triggered` push to see when the simulation acknowledges the update.

---

## `transmit_bytes`

Transmit arbitrary bytes from the ground transmitter at a chosen frequency, **bypassing** the team's normal RF encryption. Useful for jamming, decoy transmissions, or experimenting with custom waveforms in scenarios that require it.

**Request**

```json
{
  "type": "transmit_bytes",
  "req_id": 0,
  "args": {
    "frequency": 478.0,
    "encoding":  "base64",
    "data":      "SGVsbG8sIHdvcmxkIQ=="
  }
}
```

| Argument | Default | Description |
| --- | --- | --- |
| `frequency` | _(required)_ | Transmit frequency in MHz. Must be `> 0`. |
| `encoding` | `base64` | How the bytes in `data` are encoded. One of: `base64`, `hex`, `utf8`, `ascii`. Whitespace in `hex` is stripped. |
| `data` | `""` | The payload, encoded as specified. |

**Response**

```json
{
  "type": "transmit_bytes",
  "req_id": 0,
  "args": { "bytes_sent": 13 },
  "success": true
}
```

| Field | Description |
| --- | --- |
| `bytes_sent` | Number of bytes queued for transmission. |

Common errors:

- `"Ground transmitter is not available."` — no transmitter configured for this team.
- `"transmit_bytes requires a positive frequency in MHz."` — missing or invalid `frequency`.
- `"Invalid base64 data."` / `"Hex data must have an even number of characters."` / `"Invalid hex digit."` — `data` couldn't be decoded against `encoding`.
- `"Unknown encoding 'X'. Use base64, hex, utf8, or ascii."` — typo in `encoding`.
- `"Already changing telemetry settings. Please wait before transmitting bytes."` — a frequency or encryption change is still in progress.

### Notes

- The transmitter retunes to `frequency` for the duration of the burst, then automatically returns to the team's nominal frequency and Caesar key. While retuned, the team's normal uplink to its own spacecraft is briefly unavailable.
- `transmit_bytes` does **not** apply Caesar encryption — your bytes go on the wire exactly as supplied. If you want to talk to a spacecraft, you must construct the framing yourself.

---

## `get_packet_schemas`

Returns XTCE (XML Telemetric and Command Exchange) definitions for every telemetry packet type the simulation can emit. Use these to decode raw downlink frames without hard-coded knowledge of the wire format.

**Request**

```json
{ "type": "get_packet_schemas", "req_id": 0 }
```

No arguments.

**Response**

```json
{
  "type": "get_packet_schemas",
  "req_id": 0,
  "args": {
    "telemetry": [
      "<?xml version=\"1.0\" ... ?>",
      "<?xml version=\"1.0\" ... ?>"
    ]
  },
  "success": true
}
```

| Field | Description |
| --- | --- |
| `telemetry[]` | Array of XTCE XML strings, one per packet type. Parse with any XTCE-aware library to learn each packet's APID, header layout, parameter types, units, and ranges. |

### Notes

- The schemas are static for a given Studio build, so call this once at startup and cache the result.
- See [Guides → Decoding telemetry](../guides/decoding-telemetry.md) for an end-to-end example using XTCE to decode CCSDS Space Packets received over `Downlink`.

---

## `chat_query`

Sends a question to the AI assistant that has read access to your spacecraft's recent state and the simulation context. Only available in scenarios that explicitly enable the assistant.

**Request**

```json
{
  "type": "chat_query",
  "req_id": 0,
  "args": {
    "asset_id": "A3F2C014",
    "prompt":   "Why is my battery draining so fast?",
    "messages": [ "...most recent decoded telemetry message JSON..." ]
  }
}
```

| Argument | Description |
| --- | --- |
| `asset_id` | The spacecraft the question is about. Must belong to this team. |
| `prompt` | The question, in natural language. |
| `messages[]` | Array of recent telemetry message JSON strings to give the assistant context. Empty array is allowed — the assistant will still see general scenario context. |

**Immediate response**

```json
{ "type": "chat_query", "req_id": 0, "args": {}, "success": true }
```

The immediate response only acknowledges that the query was queued. The actual answer arrives later as an unsolicited [`chat_response`](#chat_response).

If `success` is `false`, common `error` values:

- `"Entity with ID '...' not found."` — bad `asset_id`.
- `"Failed to send chat message."` — the AI subsystem is unavailable in the scenario.

---

## `chat_response` (push)

Unsolicited message published on the team's `Response` topic when the AI assistant has produced an answer. Not in reply to a specific request — match by tracking the `req_id` of your last `chat_query`.

```json
{
  "type": "chat_response",
  "req_id": 0,
  "args": {
    "valid":     true,
    "role":      "assistant",
    "message":   "Your battery is draining faster because...",
    "timestamp": "2026/01/25 13:05:12"
  },
  "success": true
}
```

| Field | Description |
| --- | --- |
| `valid` | `true` once the assistant has finished. `false` indicates the response is still being generated and a follow-up `chat_response` will arrive. |
| `role` | `assistant` (model output) or `user` (echo of your prompt). |
| `message` | The reply text in rich-text style markdown. |
| `timestamp` | Local datetime when the reply was created (`YYYY/MM/DD HH:MM:SS`). |

---

## `list_questions`

Lists the scenario's question set for this team. Scenarios may include questions (e.g. multiple-choice, free text) for evaluation; this endpoint returns the questions and any prior submissions by this team.

**Request**

```json
{ "type": "list_questions", "req_id": 0 }
```

No arguments.

**Response**

```json
{
  "type": "list_questions",
  "req_id": 0,
  "args": {
    "questions": [
      {
        "id":          1,
        "section":     "Telemetry",
        "title":       "Identify the encryption key in use",
        "description": "Inspect the latest downlink to determine the team's Caesar key.",
        "type":        "number",
        "answer":      { "...stub depending on type..." },
        "submission":  {
          "date":    "2026-01-25T13:05:12Z",
          "correct": true,
          "reason":  "Matches expected key.",
          "score":   10,
          "value":   17,
          "answer":  17
        }
      }
    ]
  },
  "success": true
}
```

| Field | Description |
| --- | --- |
| `questions[].id` | Stable integer identifier — pass to `submit_answer`. |
| `questions[].section` | Logical grouping (e.g. `"Telemetry"`, `"Commanding"`). |
| `questions[].title`, `description` | Display strings for a UI. |
| `questions[].type` | `text`, `number`, `select`, or `checkbox`. Determines the shape of `value` in `submit_answer`. |
| `questions[].answer` | Type-dependent stub describing the answer schema (option list, value bounds, etc.). |
| `questions[].submission` | Present only if this team has already submitted an answer. Contains the team's value, the correct value, score awarded, and reason. Once present, the question can no longer be re-answered. |

---

## `submit_answer`

Submits one or more answers to scenario questions in a single call. Each submission is graded independently.

**Request**

```json
{
  "type": "submit_answer",
  "req_id": 0,
  "args": {
    "submissions": [
      { "id": 1, "value": 17 },
      { "id": 4, "value": ["A", "C"] },
      { "id": 7, "value": "We changed the key after the third pass." }
    ]
  }
}
```

| Argument | Description |
| --- | --- |
| `submissions[]` | Array of submission objects. |
| `submissions[].id` | Question ID from [`list_questions`](#list_questions). |
| `submissions[].value` | Type-dependent answer: a string for `text`, a number for `number`, an integer index for `select`, an array of integer indices for `checkbox`. |

**Response**

```json
{
  "type": "submit_answer",
  "req_id": 0,
  "args": {
    "results": [
      { "id": 1, "success": true,  "correct": true,  "score": 10 },
      { "id": 4, "success": false, "error":  "Question already answered." }
    ]
  },
  "success": true
}
```

| Field | Description |
| --- | --- |
| `results[]` | One entry per submission, in the order submitted. |
| `results[].id` | Echoes the submission's question ID. |
| `results[].success` | `true` if the submission was accepted (whether correct or not). |
| `results[].correct` | Present on accepted submissions; whether the answer scored. |
| `results[].score` | Present on accepted submissions; points awarded. |
| `results[].error` | Present on rejected submissions (unknown ID, already answered, missing `value`, etc.). |

The outer `success` is `true` as long as the request itself was well-formed — individual submissions can still be rejected. Inspect each `results[]` entry separately.

---

## `event_triggered` (push)

Unsolicited message that fires every time something noteworthy happens on this team's spacecraft or ground controller — commands sent, telemetry settings changed, components reset, etc. Not in reply to any request.

```json
{
  "type": "event_triggered",
  "req_id": 0,
  "args": {
    "simulation_time": 10.0,
    "simulation_utc":  "2026/01/23 13:23:45",
    "clock_time":      "2026/01/23 25:12:56",
    "trigger":         "Spacecraft",
    "team_id":         10,
    "asset_id":        "A3F2C014",
    "name":            "Spacecraft Reboot",
    "arguments":       { }
  },
  "success": true
}
```

| Field | Description |
| --- | --- |
| `simulation_time` | Sim-seconds when the event occurred. |
| `simulation_utc` | Simulation UTC string. |
| `clock_time` | Wall-clock local time string. |
| `trigger` | Origin of the event: `Scenario`, `Operator`, `Spacecraft`, or `Ground`. |
| `team_id` | Always your team's ID — this push only fires for events scoped to this team. |
| `asset_id` | Asset that triggered the event (may be empty for ground-controller events). |
| `name` | Human-readable event name (`"Spacecraft Reboot"`, `"Telemetry Update"`, `"Command Sent"`, etc.). |
| `arguments` | Free-form key-value bag of extra context. Schema depends on `name`. |

Use this stream to drive a live event log without polling [`admin_query_events`](admin-requests.md#admin_query_events).

---

## Common patterns

### Bootstrap (new client)

1. Subscribe to `Session`, `Downlink`, `Response`.
2. `list_assets` → cache asset IDs.
3. `list_stations` → cache station names.
4. For each asset, `list_entity` → cache component lists.
5. `get_packet_schemas` → cache XTCE definitions.
6. Begin sending uplinks and decoding telemetry.

### Robust request handling

Wrap each request in a request-side timeout (e.g. 5 s), keyed by `req_id`. If you don't get a matching response in time, retry up to N times before surfacing an error. Studio does not guarantee delivery on flaky brokers; the application layer is expected to retry.

### Demultiplexing the Response topic

Don't assume every message on `Response` is the answer to your most recent request. Always switch on `type`:

```python
if msg["type"] in ("event_triggered", "chat_response"):
    handle_push(msg)
else:
    pending = self.pending_requests.pop(msg["req_id"], None)
    if pending:
        pending.set_result(msg)
```

---

## Next

- [Spacecraft commands](spacecraft-commands.md) — what to do once you've discovered an asset.
- [Admin requests](admin-requests.md) — instructor-side request types.
- [Guides → Decoding telemetry](../guides/decoding-telemetry.md) — turning raw `Downlink` bytes into structured data using `get_packet_schemas`.
