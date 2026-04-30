# Recipes & agent checklist

This page is a working catalogue of complete scenario patterns derived from the shipped examples. Each recipe is annotated, so you can copy a pattern and adapt it. A short **agent checklist** at the bottom captures the rules an automated author should follow.

---

## When to copy from which scenario

| Goal | Start from | Why |
| --- | --- | --- |
| Imagery / detection exercise on Earth | `Maritime_Surveillance.json` | Many ground vessels (`objects.ground[]`), two teams sharing one collection. |
| Telemetry-loss / packet-corruption exercise | `Telemetry_Drop.json` | Single transmitter packet-corruption event with paired recovery context. |
| Unresponsive-spacecraft / command-rejection exercise | `Unresponsive_Satellite.json`, `Command_Rejection.json` | Show how to use `enable_rpo`, `enable_intercept` and computer fault models. |
| Docking / RPO exercise | `Docking_Procedure.json` | Two spacecraft with `Docking Adapter` components; `enable_rpo: true` on the controller. |
| Pointing / attitude error | `Payload_Misalignment.json` | Reaction-wheel `Stuck Index` event and guidance noise model. |
| GPS denial | (see GPS event recipes in [`events.md`](./events.md)) | No shipped scenario uses GPS jamming end-to-end yet — combine the events template with a `Maritime_Surveillance` shell. |
| Multi-section assessment with full Q&A | `Orbital Sentinel/orbital_sentinel.json` | Long `questions[]`, multiple ground objects, multiple events, multi-team. |

The agent-friendly summary: **`Orbital Sentinel` is the most complete reference**. Anything else is a simpler variant.

---

## Recipe 1 — Single-team imagery detection

Use when the brief is *"give a team some imagery and ask them to count things"*. Spawn one team with one spacecraft carrying a `Camera`, populate `objects.ground[]` with vessels at distinct lat/lons, and ask `number` questions.

```json
{
  "simulation":      { "epoch": "2026/04/27 12:00:00", "speed": 1.0,
                       "step_size": 0.1, "integrator": "Euler", "end_time": 0.0 },
  "universe":        { "atmosphere": false, "magnetosphere": false, "gps": true,
                       "cloud_opacity": 0.7, "cloud_contrast": 2.5, "ambient_light": 0.25 },
  "ground_stations": { "locations": ["Madrid", "Singapore"],
                       "min_elevation": 0, "max_range": 0 },
  "teams": [
    { "enabled": true, "id": 100001, "password": "BLUE01", "name": "Blue Team",
      "key": 6, "frequency": 473, "collection": "Main", "color": "#00AAFF" }
  ],
  "assets": {
    "space": [
      {
        "id": "SC_001", "name": "Microsat",
        "orbit": { "planet": "Earth",
                   "values": [7000.0, 0.0, 51.6, 0.0, 0.0, 0.0],
                   "offset": [0,0,0,0,0,0.001] },
        "components": [
          { "class": "Solar Panel", "name": "Solar Panel", "data": { "Area": 0.3, "Efficiency": 0.4, "Mass": 10.0 } },
          { "class": "Battery",     "name": "Battery",     "data": { "Nominal Capacity": 80.0, "Charge Fraction": 0.5, "Mass": 5.0 } },
          { "class": "Computer",    "name": "Computer",    "data": { "Mass": 2.0 } },
          { "class": "Receiver",    "name": "Receiver",    "data": { "Antenna Gain": 3.0, "Mass": 2.0 } },
          { "class": "Transmitter", "name": "Transmitter", "data": { "Mass": 1.0 } },
          { "class": "Storage",     "name": "Storage",     "data": { "Mass": 4.0 } },
          { "class": "Camera",      "name": "Camera",      "data": { "Resolution": 1024, "Field of View": 5.0, "Mass": 3.0 } },
          { "class": "Reaction Wheels", "name": "Reaction Wheels", "data": { "Mass": 1.5 } }
        ]
      }
    ],
    "collections": [
      { "id": "Main", "space_assets": ["SC_001"] }
    ]
  },
  "objects": {
    "ground": [
      { "id": "GO_001", "type": "vessel", "name": "EG01", "planet": "Earth",
        "latitude": 12.1, "longitude": 44.2, "altitude": 1,
        "scale": 120, "color": "#00FF00",
        "data": { "heading": 76.0, "speed": 10.0 } },
      { "id": "GO_002", "type": "vessel", "name": "EG02", "planet": "Earth",
        "latitude": 11.5, "longitude": 44.2, "altitude": 1,
        "scale": 120, "color": "#00FF00",
        "data": { "heading": 86.0, "speed": 0.0 } }
    ]
  },
  "questions": [
    {
      "section": "Counter-Piracy",
      "title":   "How many vessels can you count in the strait?",
      "description": "Use the camera to count green commercial vessels.",
      "type":    "number",
      "answer":  { "value": 2, "tolerance": 0, "reason": "Two green vessels.", "score": 5 }
    }
  ]
}
```

**What to vary per brief**: `objects.ground[]` (vessel layout), `questions[]` (matching counts/IDs), `orbit.values` (so the camera actually flies over the area).

---

## Recipe 2 — Telemetry drop / packet corruption

Use when the brief is *"the radio is degraded, can the team detect it?"*. Add a single Spacecraft event targeting a transmitter error model.

Add the following to a base scenario (built from Recipe 1 or the minimal scenario in [`README.md`](./README.md)):

```json
"events": [
  {
    "Enabled": true, "Name": "Packet Corruption",
    "Time": 7200.0, "Repeat": false, "Interval": 1.0,
    "Type": "Spacecraft",
    "Target": "Transmitter-TransmitterPacketCorruptionErrorModel",
    "Assets": [],
    "Data": { "Packet Corruption Fraction": 0.2 }
  }
]
```

And a question to match:

```json
"questions": [
  {
    "section": "Comms",
    "title":   "What was the packet-corruption fraction observed during downlink?",
    "description": "Use the telemetry data to estimate the corrupted-fraction during the affected pass.",
    "type":    "number",
    "answer":  { "unit": "%", "value": 20, "tolerance": 5,
                  "reason": "Corruption fraction of 0.2 = 20% applied at T+2h.",
                  "score": 6 }
  }
]
```

> Pair the event time with `simulation.end_time`: `Time: 7200` only fires if the simulation runs at least 7200s of sim time. With `speed: 100`, that's 72s wall-clock — usually fine.

---

## Recipe 3 — Component fault assessment

Use when the brief is *"a component fails partway through; the team needs to identify which one and react"*.

```json
"events": [
  {
    "Enabled": true, "Name": "Battery Power Spikes",
    "Time": 6000.0, "Repeat": false, "Interval": 1.0,
    "Type": "Spacecraft",
    "Target": "Battery-IntermittentConnectionErrorModel",
    "Assets": [],
    "Data": { "Intermittent Mean": 1, "Intermittent Std": 2 }
  }
],
"questions": [
  {
    "section": "Orbital Operations",
    "title":   "What component failed during operations?",
    "description": "Identify the failed component from the telemetry data.",
    "type":    "select",
    "answer":  {
      "options": ["Battery", "Computer", "GPS Sensor", "Reaction Wheels",
                  "Receiver", "Solar Panel", "Storage", "Transmitter"],
      "value": 0,
      "reason": ["The battery showed power spikes mid-mission. A reset clears them."],
      "score": 5
    }
  }
]
```

The matching `Target` strings for other components follow the table in [`events.md#canonical-spacecraft-event-recipes`](./events.md#canonical-spacecraft-event-recipes). Pick one fault, write the matching `select` question, and you're done.

---

## Recipe 4 — Docking / RPO exercise

Use when the brief is *"two spacecraft must rendezvous and dock"*. Both spacecraft need a `Docking Adapter`, the controller flag `enable_rpo: true`, and orbits chosen so the two paths intersect.

```json
"assets": {
  "space": [
    {
      "id": "ALPHA", "name": "Alpha",
      "orbit": { "planet": "Earth", "values": [7000.0, 0.0, 51.6, 0.0, 0.0, 0.0] },
      "controller": { "enable_rpo": true },
      "components": [
        { "class": "Solar Panel", "name": "Solar Panel", "data": { "Area": 0.5, "Mass": 10.0 } },
        { "class": "Battery",     "name": "Battery",     "data": { "Nominal Capacity": 80.0, "Mass": 5.0 } },
        { "class": "Computer",    "name": "Computer",    "data": { "Mass": 2.0 } },
        { "class": "Receiver",    "name": "Receiver",    "data": { "Mass": 2.0 } },
        { "class": "Transmitter", "name": "Transmitter", "data": { "Mass": 1.0 } },
        { "class": "Storage",     "name": "Storage",     "data": { "Mass": 4.0 } },
        { "class": "Reaction Wheels", "name": "Reaction Wheels", "data": { "Mass": 1.5 } },
        { "class": "Thruster",    "name": "Thruster",    "data": { "Mass": 3.0 } },
        { "class": "Docking Adapter", "name": "Dock", "data": { "Mass": 2.0 } }
      ]
    },
    {
      "id": "BRAVO", "name": "Bravo",
      "orbit": { "planet": "Earth", "values": [7000.0, 0.0, 51.6, 0.0, 5.0, 0.0] },
      "controller": { "enable_rpo": true },
      "components": [
        { "class": "Solar Panel", "name": "Solar Panel", "data": { "Area": 0.5, "Mass": 10.0 } },
        { "class": "Battery",     "name": "Battery",     "data": { "Nominal Capacity": 80.0, "Mass": 5.0 } },
        { "class": "Computer",    "name": "Computer",    "data": { "Mass": 2.0 } },
        { "class": "Receiver",    "name": "Receiver",    "data": { "Mass": 2.0 } },
        { "class": "Transmitter", "name": "Transmitter", "data": { "Mass": 1.0 } },
        { "class": "Storage",     "name": "Storage",     "data": { "Mass": 4.0 } },
        { "class": "Reaction Wheels", "name": "Reaction Wheels", "data": { "Mass": 1.5 } },
        { "class": "Docking Adapter", "name": "Dock", "data": { "Mass": 2.0 } }
      ]
    }
  ],
  "collections": [
    { "id": "Chaser", "space_assets": ["ALPHA"] },
    { "id": "Target", "space_assets": ["BRAVO"] }
  ]
}
```

The two spacecraft share `semi_major_axis` and `inclination` so they're on the same orbital plane; the chaser has a `true_anomaly` offset to give it the rendezvous gap.

---

## Recipe 5 — GPS spoofing region

Use when the brief is *"GPS becomes untrustworthy near a specific city"*. Spoofing is global, so it affects every spacecraft passing through the region.

```json
"events": [
  {
    "Enabled": true, "Name": "Spoof San Francisco",
    "Time": 600.0, "Type": "GPS",
    "Data": {
      "Type": "Spoofing", "Enabled": true,
      "Origin Latitude": 37.7749, "Origin Longitude": -122.4194, "Origin Altitude": 500000.0,
      "Radius": 50000.0,
      "Spoof Latitude": -37.7749, "Spoof Longitude": 122.4194, "Spoof Altitude": 20000.0
    }
  },
  {
    "Enabled": true, "Name": "Spoof Off",
    "Time": 1800.0, "Type": "GPS",
    "Data": { "Type": "Spoofing", "Enabled": false }
  }
]
```

Pair with a `select` question asking *"What region was being spoofed?"* with the cities list.

---

## Recipe 6 — Multi-team assessment with mixed Q&A

`Orbital Sentinel` is the canonical example. Read it end-to-end at `c:\Users\HarrisonVerrios\Downloads\Space Range\Orbital Sentinel\orbital_sentinel.json`. Key features to copy:

- Two enabled teams sharing a collection so they each command the same set of spacecraft.
- ~22 ground vessels arranged into themed clusters (Red Sea, South China Sea, Venezuela).
- One scripted Spacecraft event mid-run (`Battery Power Spikes` at `6000s`).
- Long `questions[]` with all four question types and a clear `section` for each cluster.

Things `Orbital Sentinel` does **not** demonstrate:

- GPS spoofing or jamming (use Recipe 5).
- Docking (use Recipe 4).
- Multiple events on different timelines (use multiple `events[]` entries from the canonical templates in [`events.md`](./events.md)).

---

## Agent checklist

When generating a scenario from a brief, follow this checklist top-to-bottom. Each step is independently testable.

### 1. Plan from the brief

- Extract: number of teams, region(s) of interest, payload required (camera, EM sensor, etc.), failure modes, scoring questions.
- Pick the closest recipe above as the starting shell.
- Decide `simulation.end_time`. Anything above `0.0` is a hard stop; `0.0` means runs forever.

### 2. Skeleton

- Copy `simulation`, `universe`, `ground_stations` from the recipe. **Don't tune yet.**
- Create `teams[]` with **distinct** `id`, `password`, `key`, `frequency`, `color`. Use a deterministic palette.
- Create one `assets.space[]` entry per spacecraft, even if duplicated.
- Create `assets.collections[]` so every spacecraft has at least one team owning it.

### 3. Components

- Always include the canonical 6: `Solar Panel`, `Battery`, `Computer`, `Receiver`, `Transmitter`, `Storage`. Without these, basic ops (`ping`, `capture`, `downlink`) fail.
- Add only the components the brief requires: `Camera` for imagery, `EM Sensor` for SIGINT, `Reaction Wheels` for pointing exercises, `Docking Adapter` for RPO, `Jammer` only if explicitly required.
- Keep `data` minimal — set `Mass` and the one or two parameters relevant to the exercise. Defaults are reasonable for everything else.
- See [`components.md`](./components.md) for the full per-class field list.

### 4. Ground objects

- Place vessels with distinct `latitude` / `longitude`. Avoid stacking vessels at identical coordinates unless the ambiguity is the exercise.
- Use distinct `color` per vessel when they're meant to be referenced by colour in questions.
- Use `text` ground objects to label regions when imagery alone isn't enough.

### 5. Events

- Add **one event at a time** and test in isolation.
- Pull the `Target`/`Data` from the canonical templates in [`events.md`](./events.md) — do not invent new keys.
- For training scenarios, pair every fault with a recovery-prompting follow-up event (or document the recovery in `description`).
- Sort events in the JSON in chronological `Time` order for readability.
- Empty `Assets: []` means *every spacecraft*. Use a single-element list (`["ALPHA"]`) for per-team faults.

### 6. Questions

- Always set `score` per question. Aim for a round total (50, 100).
- Use `number` with a sensible `tolerance` and explicit `unit`.
- Double-check zero-based indices in `select` and `checkbox` against the displayed `options`.
- Group related questions with `section`.
- Avoid checkbox questions where one wrong tick collapses to zero score unless that strictness is intentional. See the scoring rules in [`questions.md`](./questions.md).
- Question IDs are auto-assigned in load order; do not hand-write them.

### 7. Validation pass

- Lint the JSON (no trailing commas, no comments).
- Load the file in Studio and watch the log for parse errors. Studio continues past failed sections — silent partial loads are common.
- Check that:
  - Every team listed in `admin_list_entities`.
  - Every spacecraft listed in `list_assets` for its team.
  - Every component name reachable via `list_entity`.
  - Every event listed in `admin_get_scenario_events`.
  - Every question shows up in `list_questions`.

If something is missing, the most likely culprits (in order) are:

1. A typo in `class`, `name`, or `Target` (case mismatch on names is fine; class aliases must spell-match exactly).
2. A missing `value` on a `number`/`select` question — drops the question silently.
3. An `Assets[]` referencing a spacecraft `id` that doesn't exist — event no-ops.
4. An `events.Data.Type` mismatch (`"Spoofing"` vs `"spoof"`) — event errors out at runtime.
5. A `team.collection` that doesn't exist in `assets.collections[]` — team has no spacecraft.

### 8. Iterate on the timing

- Lower `simulation.speed` (e.g. `100`) for fast iteration; raise for fidelity.
- Lower `events[i].Time` while testing so faults fire early.
- Once the scenario is correct end-to-end, restore production-quality timings (events at realistic sim seconds, `speed: 1.0` if the brief is real-time).

---

## See also

- [`README.md`](./README.md) — the index, with the loading order Studio applies.
- [`events.md`](./events.md) — full event reference.
- [`questions.md`](./questions.md) — full Q&A reference.
- `c:\Users\HarrisonVerrios\Downloads\Space Range\Orbital Sentinel\orbital_sentinel.json` — most complete shipped example.
