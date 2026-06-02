# Scenario Authoring Reference

This section is the **complete reference** for authoring Space Range scenarios in JSON. It is structured for both human authors and AI agents that need to generate scenario files from a brief.

If you have not authored a scenario before, read [Scenario configuration](../guides/scenario-config.md) first — it is the narrative tour. This section is the deep specification it references.

---

## What a scenario is

A scenario is a single JSON file Studio loads to set up an exercise: simulation parameters, the universe model, ground stations, teams and their credentials, spacecraft and their components, ground decorations (vessels, text), scripted failure events, and (optionally) Q&A questions for scoring.

Studio loads the JSON and builds the simulation: teams, spacecraft, ground objects, scripted events, and scoring questions.

---

## Top-level shape

Every scenario JSON has this shape. **Every section is optional** except `teams` and `assets` — without those the scenario can be loaded but no team can do anything.

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

| Section | Purpose | Page |
| --- | --- | --- |
| `simulation` | Clock, integrator, simulation speed | [simulation.md](simulation.md) |
| `universe` | Atmosphere, magnetosphere, GPS, lighting toggles | [universe.md](universe.md) |
| `ground_stations` | The pool of receiving sites used by every team | [ground-stations.md](ground-stations.md) |
| `teams` | Team identity (ID, password, key, frequency, color, collection) | [teams.md](teams.md) |
| `assets.space` | Spacecraft definitions (orbit, physics, components, controller, power bus) | [spacecraft.md](spacecraft.md) |
| `assets.collections` | Map of `collection` IDs → spacecraft IDs | [spacecraft.md#collections](spacecraft.md#collections) |
| `objects.ground` | Vessels, text labels, and other passive ground actors | [ground-objects.md](ground-objects.md) |
| `events` | Scripted failures and GPS effects on the simulation timeline | [events.md](events.md) |
| `questions` | Q&A scoring (text, number, select, checkbox) | [questions.md](questions.md) |
| (recipes) | End-to-end annotated patterns for common scenario shapes | [recipes.md](recipes.md) |

---

## Casing, key matching, and whitespace

Studio parses every section when the scenario file is loaded. Two rules to keep in mind:

1. **Keys are case-insensitive.** `enabled`, `Enabled`, and `ENABLED` all match. The shipped templates and example files mix `lowercase` (`simulation`, `teams`, `universe`) and `PascalCase` (`Enabled`, `Name`, `Time`, `Type` inside `events[]`). Both load. **Pick one casing per section and keep it consistent** so JSON diffs stay readable.
2. **Nested keys are reachable via dots.** Internally Studio writes `"orbit.values"`, `"physics.mass"`, `"visualization.mesh"`, etc. — so when authoring you can either nest the JSON normally:

   ```json
   "orbit": { "planet": "Earth", "values": [...] }
   ```

   or flatten with dotted keys:

   ```json
   "orbit.planet": "Earth",
   "orbit.values": [...]
   ```

   Both produce the same parsed result. The example files use nested objects; the round-trip serializer writes dotted keys.

There are two important exceptions to "any casing works":

- The **`questions[]` `type` field** is matched case-insensitively but must be one of `text`, `number` (alias `numeric`), `select`, `checkbox`. See [questions.md](questions.md).
- The **`events[]` `Data` keys** must match the property names the event type expects (whitespace in the key is ignored). `"Stuck Index"` and `"StuckIndex"` both work, but `"stuckindex"` does **not** if the canonical name is `StuckIndex`. See [events.md](events.md).

Trailing commas, comments, and bare keys are **not** allowed — Studio uses a strict JSON parser. Lint your file before loading.

---

## How a scenario loads (so you know what to debug)

When the scenario JSON is loaded (Studio UI scenario picker or admin/scenario API), sections are applied in this order:

1. `simulation` is applied to the clock and integrator.
2. `universe` flags are applied to the world.
3. `ground_stations` instantiates ground stations at the listed cities.
4. `teams[]` creates one ground controller per enabled team and stores its credentials.
5. `assets.space[]` instantiates each spacecraft: orbit → physics → visualization → controller → components.
6. `assets.collections[]` is recorded so that team `collection` strings resolve to spacecraft IDs.
7. `objects.ground[]` instantiates vessels / text actors.
8. `events[]` are registered on the simulation event queue (they fire later, on `Time`).
9. `questions[]` are stored on the subsystem and exposed to teams via [`list_questions`](../api-reference/ground-requests.md#list_questions).

If a section fails to parse, Studio logs the error and continues with the next section. **Always check the Studio log after loading** — silent partial loads are a common authoring trap.

To verify a load programmatically, use the admin API:
- [`admin_list_entities`](../api-reference/admin-requests.md#admin_list_entities) — every team should show up.
- [`list_assets`](../api-reference/ground-requests.md#list_assets) — every spacecraft should show up for its team.
- [`list_entity`](../api-reference/ground-requests.md#list_entity) — every component name on a spacecraft should be reachable.
- [`admin_get_scenario_events`](../api-reference/admin-requests.md#admin_get_scenario_events) — every scripted event should be listed.

---

## Minimal scenario

The smallest scenario that loads and runs:

```json
{
  "simulation":      { "epoch": "2026/04/27 12:00:00", "speed": 1.0, "step_size": 0.1, "integrator": "Euler", "end_time": 0.0 },
  "universe":        { "atmosphere": false, "magnetosphere": false, "gps": true, "cloud_opacity": 0.7, "cloud_contrast": 2.5, "ambient_light": 0.25 },
  "ground_stations": { "locations": ["Madrid"], "min_elevation": 0, "max_range": 0 },
  "teams": [
    { "enabled": true, "id": 111111, "password": "AAAAAA", "name": "Blue Team", "key": 6, "frequency": 473, "collection": "Main", "color": "#00AAFF" }
  ],
  "assets": {
    "space": [
      {
        "id":     "SC_001",
        "name":   "Microsat",
        "orbit":  { "planet": "Earth", "values": [7000.0, 0.0, 51.6, 0.0, 0.0, 0.0], "offset": [0,0,0,0,0,0.001] },
        "components": [
          { "class": "Solar Panel", "name": "Solar Panel", "data": { "Area": 0.3, "Efficiency": 0.4, "Mass": 10.0 } },
          { "class": "Battery",     "name": "Battery",     "data": { "Nominal Capacity": 80.0, "Charge Fraction": 0.5, "Mass": 5.0 } },
          { "class": "Computer",    "name": "Computer",    "data": { "Mass": 2.0 } },
          { "class": "Receiver",    "name": "Receiver",    "data": { "Antenna Gain": 3.0, "Mass": 2.0 } },
          { "class": "Transmitter", "name": "Transmitter", "data": { "Mass": 1.0 } },
          { "class": "Storage",     "name": "Storage",     "data": { "Mass": 4.0 } }
        ]
      }
    ],
    "collections": [
      { "id": "Main", "space_assets": ["SC_001"] }
    ]
  }
}
```

This is enough to give Blue Team one spacecraft they can `ping`, `capture`, `downlink`, etc. Every other section is added on top of this skeleton.

---

## Author / agent quickstart

When generating a scenario from a brief, work in this order. Each step is small and independently testable.

1. **Clock & world** — `simulation`, `universe`, `ground_stations`. These rarely change once set; copy them from a similar shipped scenario.
2. **Teams** — one per side / observer. Pick distinct `id`, `password`, `frequency`, `color`. See [teams.md](teams.md).
3. **One spacecraft** — define `assets.space[0]` end-to-end and add a single-entry `assets.collections[0]` linking it to one team. Get this working before adding more spacecraft. See [spacecraft.md](spacecraft.md).
4. **Components** — start with the canonical 6: `Solar Panel`, `Battery`, `Computer`, `Receiver`, `Transmitter`, `Storage`. Add `Camera`, `GPS Sensor`, `Reaction Wheels`, `Jammer`, `Docking Adapter`, `Power Interconnect`, etc. as the scenario requires. See [components.md](components.md). If two hulls on the **same team** should share power at load, wire each `Power Interconnect` on `power.bus` and add one `power.interconnects` row — [spacecraft.md — Power interconnects](spacecraft.md#power-interconnects-powerinterconnects).
5. **More spacecraft and collections** — duplicate the first spacecraft, vary `id` / `name` / `orbit`, and assign each to a team via collections.
6. **Ground objects** — add vessels, labels, and decorations to support imagery exercises. See [ground-objects.md](ground-objects.md).
7. **Events** — add scripted failures *one at a time*. Test each by lowering its `Time` and watching the admin event stream. See [events.md](events.md).
8. **Questions** — add scoring questions only after the scenario shape is stable; broken JSON in a question hides scoring entirely for that question. See [questions.md](questions.md).

Patterns for whole-scenario shapes (counter-piracy, telemetry-drop, docking, GPS denial) are documented in [recipes.md](recipes.md).

---

## Reference scenarios

The best references for valid JSON shape and field names are the **shipped scenario files** in the Space Range scenarios bundle and the pages in this section (`simulation`, `teams`, `spacecraft`, `components`, `events`, etc.).

Example scenarios to copy from: `Orbital Intel`, `Maritime_Surveillance`, `Unresponsive_Satellite`, `Telemetry_Drop`, `Payload_Misalignment`, `Null_Data`, `Command_Rejection`, `Docking_Procedure`, `Cyber Defender`, `Tutorial`. Power-bus harness: `Testing/test_power_scenario`.

In Studio, the **Add Event** menu lists canonical event templates (Spacecraft, GPS, Cyber) that match the `events[]` shapes documented in [events.md](events.md).
