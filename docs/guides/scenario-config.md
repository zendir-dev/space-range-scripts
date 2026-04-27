# Scenario Configuration

A Space Range **scenario** is a single JSON file describing everything Studio needs to spin up an exercise: simulation parameters, the universe, ground stations, teams and their credentials, spacecraft and their components, ground objects (vessels, decals, text), scripted failure events, and (optionally) Q&A questions for scoring.

This guide is the **narrative tour** of that file — short enough to read end-to-end, focused on the parts authors edit most often. For the **complete field-by-field specification** (every component class, every event-`Data` key, every question scoring rule, recipes, and an agent checklist), see the [Scenario authoring reference](../scenarios/README.md).

The shipped reference scenario at `space-range-scripts/scenarios/orbital_sentinel.json` is a good starting point; quote it freely.

---

## File location & layout

Scenario JSONs live in Studio's `Scenarios` directory (the location varies by build — check your Studio install). Filenames are usually short snake-case identifiers (`orbital_sentinel.json`). The matching scripted-scenario Python file (e.g. `orbital_sentinel.py`) sits alongside it; see [The scripted-scenario companion](#the-scripted-scenario-companion) at the end.

The top-level shape of every scenario is:

```json
{
  "simulation":      { ... },
  "universe":        { ... },
  "ground_stations": { ... },
  "teams":           [ ... ],
  "assets": {
    "space":         [ ... ],
    "collections":   [ ... ]
  },
  "objects": {
    "ground":        [ ... ]
  },
  "events":          [ ... ],
  "questions":       [ ... ]
}
```

Every section is optional except `teams` and `assets` — without those the scenario can be loaded but no team can do anything. A minimal scenario is ~50 lines; a competition-grade scenario like `orbital_sentinel.json` is ~1300 lines.

---

## `simulation` — global timeline & solver

Controls how the simulation clock advances and what dynamics integrator is used.

```json
"simulation": {
  "epoch":      "2026/04/15 07:30:00",
  "speed":      5.0,
  "step_size":  0.12,
  "integrator": "Euler",
  "end_time":   0.0
}
```

| Field | Type | Description |
| --- | --- | --- |
| `epoch` | `string` | UTC start of simulated time, `YYYY/MM/DD HH:MM:SS`. Drives sun position, ground tracks, etc. |
| `speed` | `number` | Default `simulation_speed` (sim seconds per real second). Instructors can change this at runtime via [`admin_set_simulation`](../api-reference/admin-requests.md#admin_set_simulation). |
| `step_size` | `number` | Integrator step in sim seconds. Smaller = more accurate dynamics, more CPU. `0.1–0.2` is typical. |
| `integrator` | `string` | One of `Euler`, `RK4`. `Euler` is fine for most exercises; switch to `RK4` for long propagation accuracy. |
| `end_time` | `number` | Hard stop in sim seconds. `0.0` means "run forever / until reset". |

---

## `universe` — environment switches

Toggles for the simulated environment that the spacecraft react to.

```json
"universe": {
  "atmosphere":     false,
  "magnetosphere":  true,
  "gps":            true,
  "cloud_opacity":  0.9,
  "cloud_contrast": 2.5,
  "ambient_light":  0.25
}
```

| Field | Type | Description |
| --- | --- | --- |
| `atmosphere` | `bool` | If `true`, atmospheric drag and visual scattering apply. Off by default at typical operating altitudes. |
| `magnetosphere` | `bool` | If `true`, Earth's magnetic field is modelled (relevant to magnetometer telemetry and magnetorquer-style components). |
| `gps` | `bool` | If `true`, the GPS sensor returns valid fixes. Set `false` to model a GPS-denied scenario. |
| `cloud_opacity`, `cloud_contrast` | `number` | Visual settings for the rendered Earth — they affect how bright and how cloudy imagery from the camera looks. `0–1` opacity, contrast around `1.0–3.0`. |
| `ambient_light` | `number` | Scene ambient light. Higher values brighten dark sides for visualisation; doesn't affect physics. |

These values change the *experience* of the scenario — they do not change command/telemetry semantics.

---

## `ground_stations` — receiving network

The pool of ground stations available to teams.

```json
"ground_stations": {
  "locations": [
    "Madrid", "Dubai", "Singapore", "Auckland",
    "Easter Island", "Salvador", "Miami"
  ],
  "min_elevation": 0,
  "max_range":     0,
  "scale":         100
}
```

| Field | Type | Description |
| --- | --- | --- |
| `locations` | `string[]` | Names of the cities to instantiate ground stations at. Each name matches an entry in Studio's built-in city table. |
| `min_elevation` | `number` (deg) | Minimum elevation above the horizon for a station to be considered "in view". `0` means at-the-horizon counts. |
| `max_range` | `number` (km) | Maximum range over which the station can close a link. `0` means unlimited (link budget alone gates it). |
| `scale` | `number` | Visual scale factor for ground-station markers in the world view. |

Every ground station defined here is shared by every team — there is no per-team ground network. To restrict which station a team uses, control it operationally (e.g. let the team choose one with [`guidance` mode `ground`](../api-reference/spacecraft-commands.md#guidance)) rather than configurationally.

---

## `teams` — the units of identity

Every team in the scenario gets one entry. The order doesn't matter; the IDs do.

```json
"teams": [
  {
    "enabled":    true,
    "id":         111111,
    "password":   "AB12CD",
    "name":       "Red Team",
    "key":        17,
    "frequency":  500,
    "collection": "RED",
    "color":      "#FF366A"
  }
]
```

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `enabled` | `bool` | `true` | If `false`, the team is parsed but not instantiated. Useful for keeping inactive teams in the file for documentation. |
| `id` | `integer` | _(required)_ | Numeric team ID. Used in MQTT topic paths (`<GAME>/<ID>/...`) and in the `team_id` field of every event. **Must be unique** within the scenario. |
| `password` | `string` | _(required)_ | 6-character alphanumeric XOR password. **Must be unique** per team. |
| `name` | `string` | _(required)_ | Display name (`"Red Team"`, `"Team Blue"`). Used by the Operator UI and admin tools. |
| `key` | `integer` | `0` | Initial Caesar key (`0–255`). Teams can rotate this at runtime via [`encryption`](../api-reference/spacecraft-commands.md#encryption). |
| `frequency` | `integer` (MHz) | `0` | Initial RF carrier frequency. Pick distinct values per team to avoid cross-talk. |
| `collection` | `string` | `""` | Name of an entry in `assets.collections` listing the spacecraft this team controls. Empty = no spacecraft. |
| `color` | `string` | `"#FFFFFF"` | Hex RGB. Used for ground tracks, asset markers, plot colours. |

**Picking team values, in practice:**

- Use random alphanumeric passwords (no patterns, no shared substrings between teams). The XOR layer is weak; defence in depth is to make passwords un-guessable.
- Spread frequencies across the band (`468–901 MHz` is the typical range used by `orbital_sentinel.json`). Closer-spaced frequencies make jamming exercises more interesting; widely-spaced frequencies make accidents less likely.
- Caesar keys can collide between teams without consequence — they're scoped per-team. But keep them random anyway.
- Reserve small IDs (e.g. `111111`, `222222`) for tutorial/testing scenarios; production scenarios should use larger random IDs to avoid muscle-memory mistakes.

---

## `assets` — spacecraft and their hardware

Two arrays: `space` (the spacecraft definitions) and `collections` (the lookup tables that map team `collection` strings to spacecraft IDs).

### `assets.space[]` — spacecraft

Each spacecraft is the most complex object in the scenario. The shape:

```json
{
  "id":   "SC_001",
  "name": "Microsat",
  "orbit": { ... },
  "physics": { ... },
  "visualization": { ... },
  "controller": { ... },
  "components": [ ... ]
}
```

| Block | Purpose |
| --- | --- |
| `id` | Unique string referenced by `assets.collections[].space_assets`. The 8-character hex `asset_id` you see at runtime is **derived** from this. |
| `name` | Display name. The Operator UI and ground-controller responses strip the team name prefix from this for cleanliness. |
| `orbit` | Initial orbit (Keplerian). `values` is `[a (km), e, i (deg), Ω (deg), ω (deg), ν (deg)]`; `offset` is a small per-axis perturbation to avoid identical co-located twins. |
| `physics` | Mass, centre-of-mass offset, and 3×3 inertia tensor. Drives attitude dynamics. |
| `visualization` | The Unreal mesh path and scale used to render the spacecraft. `hide: true` hides it visually but keeps it simulating. |
| `controller` | Per-spacecraft tuning (see below). |
| `components` | The on-board hardware list. |

#### `controller`

```json
"controller": {
  "safe_fraction":      0.1,
  "capture_tax":        0.001,
  "downlink_tax":       0.01,
  "ping_interval":      20.0,
  "reset_interval":     60.0,
  "jamming_multiplier": 100.0,
  "enable_rpo":         false
}
```

| Field | Description |
| --- | --- |
| `safe_fraction` | Battery fraction below which the spacecraft enters `SAFE` mode. |
| `capture_tax` | Battery fraction consumed per `capture` command. |
| `downlink_tax` | Battery fraction consumed per `downlink` command. |
| `ping_interval` | Sim seconds between auto-Pings. Affects how quickly teams see command acks. |
| `reset_interval` | Sim seconds the spacecraft is offline after a `reset` (or after [`encryption`](../api-reference/spacecraft-commands.md#encryption) which causes a reboot). |
| `jamming_multiplier` | Scales the per-watt RF interference produced by the spacecraft's jammer payload. |
| `enable_rpo` | `true` enables [`rendezvous`](../api-reference/spacecraft-commands.md#rendezvous) and [`docking`](../api-reference/spacecraft-commands.md#docking). |

#### `components[]`

Each entry instantiates one piece of on-board hardware. The `class` decides which simulation module is constructed; the `name` is what teams use in the `target` field of commands.

```json
{
  "class":    "Camera",
  "name":     "Camera",
  "mesh":     "None",
  "enabled":  true,
  "position": [0.0, -0.36, -0.16],
  "rotation": [90.0, 0.0, 0.0],
  "data":     { "Mass": 5.0 }
}
```

| Field | Type | Description |
| --- | --- | --- |
| `class` | `string` | Simulation class. Common values: `Solar Panel`, `Battery`, `Reaction Wheels`, `Computer`, `Camera`, `Receiver`, `Transmitter`, `Storage`, `GPS Sensor`, `EM Sensor`, `Jammer`, `Magnetometer`, `Gyroscope`, `External Force Torque`, `Thruster`, `Docking Adapter`, `Text`. |
| `name` | `string` | Friendly name. **Must be unique** within a spacecraft. Teams reference it via `target` in commands. Case-insensitive at runtime. |
| `mesh` | `string` | Unreal mesh path, or `"None"` to use the class default. |
| `enabled` | `bool` | If `false`, the component is loaded but inactive (good for failure events that flip it on later). |
| `position`, `rotation` | `number[3]` | Local placement. `position` in metres relative to spacecraft origin; `rotation` in degrees (Yaw/Pitch/Roll). |
| `data` | `object` | Class-specific tuning. `Mass` is universal (kg). Class-specific keys are documented in Studio's component reference. |

**Most-used component classes and what's in their `data`:**

| Class | Common `data` fields |
| --- | --- |
| `Solar Panel` | `Area` (m²), `Efficiency` (`0–1`), `Mass` |
| `Battery` | `Nominal Capacity` (Wh), `Charge Fraction` (`0–1`), `Mass` |
| `Reaction Wheels` | `Mass` (and class-specific torque limits in some builds) |
| `Camera` | `Mass`. Optical settings (`fov`, `aperture`, etc.) come from the `camera` command, not config. |
| `Receiver` / `Transmitter` | `Antenna Gain` (dB), `Mass` |
| `Storage` | `Mass` (capacity scales with mass in default builds) |
| `Jammer` | `Power` (W), `Antenna Gain` (dB), `Lookup` (RF pattern CSV file) |
| `Computer`, `GPS Sensor`, `EM Sensor`, `Magnetometer`, `Gyroscope`, `External Force Torque` | `Mass` |
| `Docking Adapter` | `Mass`, `Half Cone Angle` (deg) |
| `Text` | `Text` (string), `Color` (hex), `Scale`. Pure visual/labelling component. |

### `assets.collections[]` — team-to-asset lookup

```json
"collections": [
  { "id": "Main", "space_assets": ["SC_001"] },
  { "id": "RED",  "space_assets": ["SC_002"] }
]
```

| Field | Description |
| --- | --- |
| `id` | The string referenced by a team's `collection` field. |
| `space_assets[]` | Spacecraft `id`s in this collection. The team controls every spacecraft listed here. |

A team can have multiple spacecraft (just list them all). A spacecraft can belong to multiple collections only if you genuinely want multiple teams to share it — usually you don't, so keep collections one-to-one.

---

## `objects.ground[]` — ground decorations

Visual ground objects: vessels, text labels, anything that needs to appear at a lat/lon.

```json
{
  "id":        "GO_001",
  "type":      "vessel",
  "name":      "EG01",
  "planet":    "Earth",
  "latitude":  12.1,
  "longitude": 44.2,
  "altitude":  1,
  "scale":     120,
  "color":     "#00FF00",
  "data":      { "heading": 76.0, "speed": 10.0 }
}
```

| Field | Description |
| --- | --- |
| `id` | Unique identifier. |
| `type` | `vessel`, `text`, or any other supported ground-object class. |
| `name` | Display name. |
| `planet` | Body the object sits on (`Earth`, `Moon`, `Mars`). |
| `latitude`, `longitude`, `altitude` | Position. Altitude in metres above the surface. |
| `scale` | Visual size factor. |
| `color` | Hex RGB. For `vessel`, this is the ship's hull colour. |
| `data` | Type-specific values: `heading` (deg) and `speed` (m/s) for vessels; `text` (string) for `type: text`. |

Ground objects are **passive** — they don't generate telemetry, can't be commanded, and aren't part of the team configuration. They exist to give imagery exercises something realistic to find.

---

## `events[]` — scripted failures and anomalies

Studio fires these on the simulation timeline. They're how an instructor injects scripted hardware failures or environmental events without having to be at the controls.

```json
"events": [
  {
    "Enabled":  true,
    "Name":     "Battery Power Spikes",
    "Time":     6000.0,
    "Repeat":   false,
    "Interval": 1.0,
    "Type":     "Spacecraft",
    "Target":   "Battery-IntermittentConnectionErrorModel",
    "Assets":   [],
    "Data":     { "Intermittent Mean": 1, "Intermittent Std": 2 }
  }
]
```

| Field | Type | Description |
| --- | --- | --- |
| `Enabled` | `bool` | Set `false` to keep the event in the file but inactive. |
| `Name` | `string` | Display name surfaced by [`admin_get_scenario_events`](../api-reference/admin-requests.md#admin_get_scenario_events) and the admin UI. |
| `Time` | `number` (sim s) | First trigger time. |
| `Repeat` | `bool` | If `true`, fires every `Interval` seconds after the first trigger. |
| `Interval` | `number` (sim s) | Repeat period. Ignored when `Repeat` is `false`. |
| `Type` | `string` | `Spacecraft` or `GPS` (case-insensitive; `failure` is accepted as an alias for `Spacecraft`). Selects the action handler. |
| `Target` | `string` | (Spacecraft only.) Component / error-model the event acts on. The form is `"<ComponentName>-<ErrorModel>"`, or just `"<ComponentName>"` to set properties directly. Ignored by `GPS` events. |
| `Assets` | `string[]` | (Spacecraft only.) Spacecraft IDs to target. Empty array = "every spacecraft". |
| `Data` | `object` | Type/target-specific parameters. For `Spacecraft` events, keys are property names on the component or its error model (with whitespace stripped). For `GPS` events, `Data.Type` selects `Spoofing` vs `Jamming`, and `Data.Action` selects `add`/`update`/`remove` for jamming. |

The most useful Spacecraft `Target` forms:

| `Target` form | Effect |
| --- | --- |
| `<Component>` | Set direct properties on the component (e.g. `Capacity`, `Bit Rate`, `Stuck Index`). |
| `<Component>-IntermittentConnectionErrorModel` | Component intermittently disconnects (`Intermittent Mean`, `Intermittent Std`). |
| `Solar Panel-SolarPanelDegradationErrorModel` | Permanent efficiency loss (`Degradation Rate`). |
| `Battery-BatteryLeakageErrorModel` | Battery leak (`Power Leakage Rate`). |
| `Transmitter-TransmitterPacketCorruptionErrorModel` | Packet corruption (`Packet Corruption Fraction`). |
| `Computer-GuidanceComputerNoiseErrorModel` | Pointing error (`Noise Factor`, `Randomize`). |

GPS events configure spoofing regions and jamming sources on the global GPS subsystem; see [Scenario reference → events](../scenarios/events.md#gps-events) for the full schema.

When you're authoring events, fire one at a time during testing — failure cascades are easy to write and hard to debug. To list every event in the loaded scenario at runtime, an admin can call [`admin_get_scenario_events`](../api-reference/admin-requests.md#admin_get_scenario_events).

---

## `questions[]` — Q&A scoring

Optional. If present, scenarios become "graded" — teams can answer questions via [`list_questions`](../api-reference/ground-requests.md#list_questions) / [`submit_answer`](../api-reference/ground-requests.md#submit_answer), and per-team scores are tracked.

```json
{
  "section":     "Red Sea (Counter‑Piracy)",
  "title":       "How many commercial vessels in the Strait?",
  "description": "Count the large green ships in the Bab el-Mandeb Strait.",
  "type":        "number",
  "answer": {
    "value":     7,
    "tolerance": 0,
    "reason":    "There are 7 large green ships in the strait.",
    "score":     4
  }
}
```

| Field | Type | Description |
| --- | --- | --- |
| `section` | `string` | Logical grouping (UI uses it to bucket questions). |
| `title` | `string` | Short prompt. |
| `description` | `string` | Long-form explanation shown to the team. |
| `type` | `string` | `text`, `number`, `select`, or `checkbox`. Selects how `answer` is interpreted. |
| `answer` | `object` | The grading config — see below per-type. |

### `answer` by `type`

#### `number`

```json
"answer": { "value": 7, "tolerance": 0, "unit": "deg", "reason": "...", "score": 4 }
```

| Field | Description |
| --- | --- |
| `value` | Correct numeric value. |
| `tolerance` | Acceptable deviation. `0` means exact match; positive values widen the band. |
| `unit` | Optional. Display string only. |
| `reason` | Feedback shown to the team after submission. |
| `score` | Points awarded for a correct answer. |

#### `text`

```json
"answer": { "value": "Caesar cipher", "score": 5, "reason": "..." }
```

`value` is matched case-insensitively against `submit_answer`'s `value` field.

#### `select`

```json
"answer": {
  "options": ["Blue", "Red", "White", "Yellow"],
  "value":   3,
  "reason":  ["...for option 0", "...for option 1", "...for option 2", "...for option 3"],
  "score":   8
}
```

`options[]` is the list shown to the team. `value` is the **index** of the correct option. `reason` is an array of the same length so each option can have its own feedback string.

#### `checkbox`

Like `select`, but `value` is an **array of indices** representing the correct combination. Submissions with the same set of indices (in any order) score.

```json
"answer": {
  "options": ["A", "B", "C", "D"],
  "value":   [0, 2],
  "reason":  ["A and C are correct because..."],
  "score":   6
}
```

Each team can answer each question once. Re-submission attempts are rejected (see [`submit_answer`](../api-reference/ground-requests.md#submit_answer)).

---

## The scripted-scenario companion

Many scenarios pair the JSON with a Python script (`<scenario>.py`) that schedules commands on behalf of a team — typically a "rogue" or "constructive agent" team that the live operators are reacting to. The script:

- Loads its config from the **same JSON** by matching scenario name.
- Connects via the bundled `space-range-scripts` framework using the team password from the JSON.
- Schedules commands on the simulation timeline using `scheduler.add_event(...)`.

A trimmed example (from `orbital_sentinel.py`):

```python
from src import Scenario, commands

scenario = Scenario(team_name="Rogue")
scheduler = scenario.scheduler

scheduler.add_event(
    name="Point Nadir",
    trigger_time=100.0,
    **commands.guidance_nadir("Jammer"),
)
scheduler.add_event(
    name="Start Jamming All Enemy Teams",
    trigger_time=2620.0,
    **commands.jammer_start(frequencies=scenario.enemy_fallback_freqs, power=3.0),
)

scenario.run()
```

The script is **optional** — you can run a scenario from the JSON alone and have all teams be human-operated. The script is the right answer when you want a deterministic adversary that runs every time you start the scenario.

A full description of the framework is intentionally out of scope here; see `space-range-scripts/README.md` for its API.

---

## Iterating on a scenario

A practical workflow when authoring or editing a scenario:

1. Start from `orbital_sentinel.json`. Strip what you don't need; keep what you do.
2. Edit `simulation`, `universe`, `ground_stations` to set the world. These rarely change once set.
3. Build out `teams` and `assets`. Get one team flying with one spacecraft first.
4. Add `objects.ground[]` decorations as the scenario narrative requires.
5. Add `events[]` last — they're the easiest to break things with. Test each event individually by setting a small `Time` and watching the admin event stream.
6. Add `questions[]` only after the rest of the scenario is stable.
7. Lint your JSON. Studio's parser is strict; trailing commas and bare keys will fail to load.

To verify a scenario will load cleanly, run it once in Studio against a single test client (the Operator UI is fastest). Watch for:

- Every team listed in `teams` shows up in [`admin_list_entities`](../api-reference/admin-requests.md#admin_list_entities).
- Every spacecraft listed in `assets.space[]` shows up in [`list_assets`](../api-reference/ground-requests.md#list_assets) for its team.
- Every component name on a spacecraft is reachable via [`list_entity`](../api-reference/ground-requests.md#list_entity).
- Every scripted event appears in [`admin_get_scenario_events`](../api-reference/admin-requests.md#admin_get_scenario_events).

If any of those don't match, the JSON did not load fully; fix the scenario file before continuing.

---

## Next

- [Scenario authoring reference](../scenarios/README.md) — the deep, per-section specification, with full component tables, event recipes, question-scoring rules, and an agent checklist.
- [Instructor & admin guide](instructor-admin.md) — running a scenario you've authored, with admin tools.
- [API reference → Admin requests](../api-reference/admin-requests.md) — programmatic access to the same controls.
- [Concepts → Teams and assets](../concepts/teams-and-assets.md) — the runtime view of what you configure here.
