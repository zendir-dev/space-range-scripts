# Admin Requests

The admin / instructor controller exposes its own request/response API. These endpoints are **not** scoped to a single team — they let an authorized client see every team's data, query historical telemetry from the database, control the simulation timeline, and inspect the scenario's scripted events.

This API uses a separate password (the **admin password**), distinct from any team password. Anyone holding it has full visibility into the simulation.

For the topic plumbing, see [MQTT topics](mqtt-topics.md).

---

## Topics

```text
Zendir/SpaceRange/<GAME>/Admin/Request     (admin client → Studio)
Zendir/SpaceRange/<GAME>/Admin/Response    (Studio → admin client)
```

Both topics are XOR-encrypted with the **admin password**. The team-side topics under `<GAME>/<TEAM>/...` are **not** accessible with the admin password — if you also need to read a team's `Downlink` or `Response`, you must subscribe to those team topics with that team's password.

The `Admin/Response` topic also receives the unsolicited [`admin_event_triggered`](#admin_event_triggered) push.

---

## Envelopes

Both the request and response envelopes are identical to the team-side ones documented in [Ground requests](ground-requests.md#request-envelope). The only difference is which `type` values are accepted: this page lists those.

```json
{ "type": "admin_get_simulation", "req_id": 0, "args": { } }
```

```json
{
  "type":    "admin_get_simulation",
  "req_id":  0,
  "args":    { "state": "Running", "speed": 1.0 },
  "success": true,
  "error":   ""
}
```

Unknown `type` values respond with `success: false` and `error: "Unknown admin request type '...'"`. This is one of the few endpoints that responds explicitly to unknown types — handy when probing the API.

---

## Request index

Discovery
: [`admin_list_entities`](#admin_list_entities) — every team and ground station in the scenario.
: [`admin_list_team`](#admin_list_team) — full configuration of one team (assets, components, password).

Historical data
: [`admin_query_data`](#admin_query_data) — periodic spacecraft data snapshots from the on-disk database.
: [`admin_query_events`](#admin_query_events) — historical tracking events.

Simulation control
: [`admin_get_simulation`](#admin_get_simulation) — current run state & speed.
: [`admin_set_simulation`](#admin_set_simulation) — play / pause / stop / change speed.

Scenario events
: [`admin_get_scenario_events`](#admin_get_scenario_events) — list scripted scenario events.

Push notifications
: [`admin_event_triggered`](#admin_event_triggered) — _(unsolicited)_ a tracking event happened, on **any** team.

---

## `admin_list_entities`

Returns every team and every ground station in the scenario. The result is static for a given scenario load, so cache it.

**Request**

```json
{ "type": "admin_list_entities", "req_id": 0 }
```

No arguments.

**Response**

```json
{
  "type": "admin_list_entities",
  "req_id": 0,
  "args": {
    "teams": [
      { "name": "Red Team",  "id": 10, "password": "AB12CD", "color": "#FF366A" },
      { "name": "Blue Team", "id": 20, "password": "EF34GH", "color": "#3B82F6" }
    ],
    "stations": [
      { "name": "Singapore", "latitude": 1.35, "longitude": 103.82, "altitude": 16.0 }
    ]
  },
  "success": true
}
```

| Field | Description |
| --- | --- |
| `teams[].name` | Display name of the team. |
| `teams[].id` | Numeric team ID. Use this in team-scoped topics (`<GAME>/<TEAM>/...`). |
| `teams[].password` | The team's XOR password — sensitive. Anyone with the admin password can read every team's password. |
| `teams[].color` | Hex RGB color used for UI plotting. |
| `stations[]` | Array of all ground stations in the scenario, each with `name`, `latitude` (deg), `longitude` (deg), `altitude` (m). |

---

## `admin_list_team`

Detailed configuration of a single team: identity, password, and every asset's components.

**Request**

```json
{ "type": "admin_list_team", "req_id": 0, "args": { "team": "Red Team" } }
```

| Argument | Description |
| --- | --- |
| `team` | Team name (case-insensitive). Match against `teams[].name` from [`admin_list_entities`](#admin_list_entities). |

**Response**

```json
{
  "type": "admin_list_team",
  "req_id": 0,
  "args": {
    "name": "Red Team",
    "id": 10,
    "password": "AB12CD",
    "color": "#FF366A",
    "assets": {
      "space": [
        {
          "asset_id": "A3F2C014",
          "name": "Microsat",
          "rpo_enabled": true,
          "intercept_enabled": true,
          "components": [
            { "name": "Solar Panel +X", "class": "Solar Panel", "component_id": 5, "is_imager": false },
            { "name": "Camera",         "class": "Camera",       "component_id": 12, "is_imager": true }
          ]
        }
      ]
    }
  },
  "success": true
}
```

| Field | Description |
| --- | --- |
| `name`, `id`, `password`, `color` | Same as in `admin_list_entities` for this team. |
| `assets.space[]` | Array of space assets owned by the team. |
| `assets.space[].asset_id` | 8-character hex asset ID. |
| `assets.space[].name` | Friendly asset name. |
| `assets.space[].rpo_enabled` | Whether RPO functionality is available on this asset. |
| `assets.space[].intercept_enabled` | Whether this asset records uplink intercepts (`enable_intercept` in scenario JSON). Same semantics as [`list_assets`](ground-requests.md#list_assets) `intercept_enabled`. |
| `assets.space[].components[]` | Component list, identical in shape to the team-side [`list_entity`](ground-requests.md#list_entity) response. |

If `team` doesn't match any team, the response succeeds with mostly-empty data (Studio doesn't currently fail-fast on this). Always validate against the `teams[]` list first.

---

## `admin_query_data`

Pulls historical telemetry snapshots from Studio's on-disk database. The simulation samples every spacecraft's state every ~10 sim s while running; this endpoint replays those samples back. Useful for instructor-side dashboards and post-run analysis.

**Request**

```json
{
  "type": "admin_query_data",
  "req_id": 0,
  "args": {
    "asset_id": "A3F2C014",
    "min_time": 0,
    "max_time": 600,
    "recent": false
  }
}
```

| Argument | Description |
| --- | --- |
| `asset_id` | Asset to query. Must exist in the simulation. |
| `min_time` | _(optional)_ Earliest sim time to include (seconds). Omit for "from the beginning". |
| `max_time` | _(optional)_ Latest sim time to include (seconds). Omit for "up to now". |
| `recent` | _(optional)_ If `true`, return only the most recent sample, ignoring `min_time` and `max_time`. Default `false`. |

**Response**

```json
{
  "type": "admin_query_data",
  "req_id": 0,
  "args": {
    "asset_id": "A3F2C014",
    "team":     "Red Team",
    "intercept_enabled": true,
    "data": [
      {
        "time": 10.7,
        "communications.frequency": 500.0,
        "communications.key": 12,
        "location.latitude": 15.2,
        "power.battery_percent": 45.0,
        "computer.pointing_mode": "Sun",
        "uplink.IsConnected": true,
        "downlink.IsConnected": true,
        "jammer.is_active": false
      }
    ]
  },
  "success": true
}
```

| Field | Description |
| --- | --- |
| `asset_id` | Echo of the queried asset. |
| `team` | Display name of the team that owns the asset. |
| `intercept_enabled` | Whether this spacecraft records uplink intercepts at query time (scenario `enable_intercept`). Included when the asset exists, before `data` is populated. |
| `data[]` | Array of sample objects, ordered by `time`. Each sample is a flat dictionary keyed by `<category>.<property>`. |

The full set of `<category>.<property>` keys available in each sample:

| Category | Sample fields | Notes |
| --- | --- | --- |
| `time` | _(scalar)_ | Sim seconds when the sample was taken. |
| `communications.*` | `frequency`, `key`, `bandwidth` | Team's RF settings at that time. |
| `location.*` | `latitude`, `longitude`, `altitude`, `position_x/y/z`, `velocity_x/y/z`, `station` | Geodetic + ECI position/velocity, plus the nearest ground station. |
| `rotation.*` | `euler_x/y/z`, `attitude_rate_x/y/z` | Attitude in degrees and degrees/s. |
| `power.*` | `battery_percent`, `battery_capacity`, `sunlight_percent`, `power_generated` | Power-system snapshot. |
| `storage.*` | `storage_percent`, `storage_used` | On-board storage utilisation. |
| `computer.*` | `state`, `navigation_mode`, `pointing_mode`, `controller_mode`, `mapping_mode` | ADCS / computer status strings. |
| `uplink.*` / `downlink.*` | `IsConnected`, `Frequency`, `Distance`, `SignalPower`, `InterferencePower`, `EffectiveSignalToNoise`, `BitErrorRate`, `TransmissionRate`, … | Live link-budget snapshots, same shape as `get_telemetry`. |
| `jammer.*` | `is_active`, `frequency`, `power` | Present only if the spacecraft has a jamming transmitter. |

### Notes

- Sampling cadence is fixed by Studio (every ~10 sim s by default). Querying a 1-second window will likely return zero rows.
- The data is **post-RF**: it represents what *actually happened* on board, not what reached any ground station. Use it as ground truth for diagnosing teams' problems.

---

## `admin_query_events`

Returns historical tracking events. Filters can be combined (or both omitted to get everything).

**Request**

```json
{
  "type": "admin_query_events",
  "req_id": 0,
  "args": {
    "asset_id": "A3F2C014",
    "team":     "Red Team"
  }
}
```

| Argument | Description |
| --- | --- |
| `asset_id` | _(optional)_ Filter to events on a specific asset. |
| `team` | _(optional)_ Filter to events for a specific team (by name). |

**Response**

```json
{
  "type": "admin_query_events",
  "req_id": 0,
  "args": {
    "intercept_enabled": true,
    "events": [
      {
        "event_id":        1,
        "simulation_time": 10.0,
        "simulation_utc":  "2026/01/23 13:23:45",
        "clock_time":      "2026/01/23 25:12:56",
        "trigger":         "Spacecraft",
        "team_id":         10,
        "asset_id":        "A3F2C014",
        "name":            "Spacecraft Reboot",
        "arguments":       { }
      }
    ]
  },
  "success": true
}
```

`intercept_enabled` is included **only when** `args.asset_id` is set in the request (filtering events for one spacecraft). It echoes whether that asset currently has uplink intercept recording enabled. Omitted when querying all events or filtering by team name alone.

| Field | Description |
| --- | --- |
| `intercept_enabled` | _(optional)_ Present when `asset_id` was supplied in the request. `true` if that spacecraft records uplink intercepts (scenario `enable_intercept`). |
| `events[].event_id` | Monotonically increasing event index, starting at 0 each scenario run. |
| `events[].simulation_time` | Sim seconds when the event occurred. |
| `events[].simulation_utc` | Simulation UTC time. |
| `events[].clock_time` | Wall-clock local time. |
| `events[].trigger` | Origin: `Scenario`, `Operator`, `Spacecraft`, or `Ground`. |
| `events[].team_id` | Team affected by the event. |
| `events[].asset_id` | Asset affected (may be empty for team- or scenario-level events). |
| `events[].name` | Human-readable event name. |
| `events[].arguments` | Free-form context, schema depends on `name`. |

To stream events live instead of polling, subscribe to [`admin_event_triggered`](#admin_event_triggered).

---

## `admin_get_simulation`

Returns the simulation timeline state and speed. Poll periodically to keep an admin UI in sync with the simulation timeline.

**Request**

```json
{ "type": "admin_get_simulation", "req_id": 0 }
```

No arguments.

**Response**

```json
{
  "type": "admin_get_simulation",
  "req_id": 0,
  "args": { "state": "Running", "speed": 5.0 },
  "success": true
}
```

| Field | Values | Description |
| --- | --- | --- |
| `state` | `Running`, `Paused`, `Stopped`, `Scrubbing` | Current run state. **Stopped** means the simulation has not been started yet (or has been reset). **Scrubbing** means the timeline is being rewound through the database. |
| `speed` | `≥ 0.0` | Sim time advance per real-time second. `1.0` is real-time, `5.0` is 5×, `0.0` is paused (rare — `state: Paused` is the usual signal). |

Common errors:

- `"Simulation subsystem not available."` — Studio is mid-load or unconfigured. Retry shortly.

---

## `admin_set_simulation`

Controls the simulation timeline. Provide `state`, `speed`, or both.

**Request**

```json
{
  "type": "admin_set_simulation",
  "req_id": 0,
  "args": { "state": "Paused", "speed": 2.0 }
}
```

| Argument | Values | Description |
| --- | --- | --- |
| `state` | `Running`, `Paused`, `Stopped` | _(case-insensitive)_ `Running` plays/resumes, `Paused` pauses, `Stopped` resets the simulation to its initial conditions. **Resetting also changes the session `instance` — every subscriber should clear cached state.** |
| `speed` | `≥ 0.0` | New simulation speed factor. |

At least one of the two must be provided. Both are applied atomically when both are present (state first, then speed).

**Response**

```json
{ "type": "admin_set_simulation", "req_id": 0, "args": {}, "success": true }
```

Common errors:

- `"At least one of 'state' or 'speed' must be provided."` — empty `args`.
- `"Invalid state '...'. Must be 'Running', 'Paused' or 'Stopped'."` — unknown state name.
- `"Simulation subsystem not available."` — Studio not ready.

### Notes

- `Stopped` is destructive. Every team's downlinked data, ground events, schedules, and on-board state are wiped. The next session message will arrive with a new `instance` ID.
- Setting `speed` while `state: Stopped` has no observable effect until the simulation is started.

---

## `admin_get_scenario_events`

Returns the **scripted** scenario events configured in the current scenario — failures, anomalies, and other events the instructor pre-loaded. These are distinct from the live tracking events surfaced by `admin_query_events`.

**Request**

```json
{ "type": "admin_get_scenario_events", "req_id": 0 }
```

No arguments.

**Response**

```json
{
  "type": "admin_get_scenario_events",
  "req_id": 0,
  "args": {
    "events": [
      {
        "enabled":  true,
        "name":     "Battery Failure",
        "type":     "Spacecraft",
        "time":     600.0,
        "repeat":   false,
        "interval": 1.0,
        "assets":   ["A3F2C014"],
        "target":   "Battery",
        "data":     { "mode": "disable" }
      }
    ]
  },
  "success": true
}
```

| Field | Description |
| --- | --- |
| `events[].enabled` | Whether the event will fire. Disabled events stay in the list for visibility. |
| `events[].name` | Display name. |
| `events[].type` | Event type, e.g. `Spacecraft`, `GPS`, `Cyber`. Determines how `assets` and `target` are interpreted. |
| `events[].time` | Trigger time in sim seconds. |
| `events[].repeat` | If `true`, fires periodically at `interval` after the first trigger. |
| `events[].interval` | Repeat interval in sim seconds. Ignored when `repeat = false`. |
| `events[].assets` | Asset IDs targeted. Empty / missing means "all assets matching `type`". |
| `events[].target` | Component or sub-system the event acts on (e.g. `Battery`, `Computer`). |
| `events[].data` | Type-specific parameters (e.g. `{"mode": "disable"}`). Schema depends on the event. |

### Notes

- This is read-only. To author or change scenario events, edit the scenario JSON in Studio.
- Common errors: `"Event subsystem not available."` if Studio isn't fully loaded.

---

## `admin_event_triggered` (push)

Unsolicited message published on `Admin/Response` whenever any team triggers a tracking event — commands sent, telemetry changes, reboots, scenario events firing, etc. Same shape as the team-side [`event_triggered`](ground-requests.md#event_triggered) push, but cross-team.

```json
{
  "type": "admin_event_triggered",
  "req_id": 0,
  "args": {
    "event_id":        42,
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
| `event_id` | Monotonic ID matching the one used in `admin_query_events`. |
| `simulation_time`, `simulation_utc`, `clock_time` | Same as on `event_triggered`. |
| `trigger` | `Scenario`, `Operator`, `Spacecraft`, or `Ground`. |
| `team_id` | Affected team (any team — the admin push is not filtered). |
| `asset_id` | Affected asset, may be empty. |
| `name` | Event name. |
| `arguments` | Event-specific context. |

Use this to build a live cross-team event timeline without polling. Combined with `admin_query_events` at startup (to backfill any events you missed), you can build a complete event log.

---

## Common patterns

### Bootstrap (admin client)

1. Subscribe to `Session` (for the clock and `instance`).
2. Subscribe to `Admin/Response` (for replies and pushes).
3. `admin_list_entities` → cache teams + stations.
4. For each team, `admin_list_team` → cache asset/component lists.
5. `admin_get_scenario_events` → display the scripted timeline.
6. `admin_query_events` → backfill any tracking events that fired before you connected.
7. From here, the live `admin_event_triggered` stream keeps you up to date; periodic `admin_query_data` polls drive any per-team telemetry dashboards.

### Pausing for a debrief

```json
{ "type": "admin_set_simulation", "req_id": 0, "args": { "state": "Paused" } }
```

Followed when ready by:

```json
{ "type": "admin_set_simulation", "req_id": 0, "args": { "state": "Running" } }
```

### Restarting the scenario

```json
{ "type": "admin_set_simulation", "req_id": 0, "args": { "state": "Stopped" } }
{ "type": "admin_set_simulation", "req_id": 0, "args": { "state": "Running" } }
```

After this, every client (including yours) should observe a new `instance` on `Session` and clear cached state.

---

## Next

- [Ground requests](ground-requests.md) — team-side counterpart.
- [MQTT topics](mqtt-topics.md) — topic and encryption layout.
- [Concepts → Simulation clock](../concepts/simulation-clock.md) — what `instance` and the timeline mean.
