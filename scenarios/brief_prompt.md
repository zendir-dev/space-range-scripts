# Prompt: Generate a Scenario Brief from a Space Range Scenario JSON

Use this prompt to turn any Space Range scenario JSON file into a participant-facing mission brief
(`<scenario_snake>_brief.md`) that matches the house style used across
`space-range-scripts/scenarios/*/*_brief.md`.

Reference briefs:

- `Lunar Logistics/lunar_logistics_brief.md` for a full, multi-phase scenario.
- `Tutorial/tutorial_brief.md` for a minimal scenario.
- `Studio Demos/Maritime/maritime_surveillance_brief.md` for a mid-sized scenario.

## Inputs

- One scenario JSON path (provided at run time). Read the whole file before writing anything.
- Write the output to `<same folder as the JSON>/<scenario_name_snake_case>_brief.md`.

## Golden rules

1. Use only what is in the JSON. Do not invent components, values, orbits, stations, or events.
   If a detail is not in the file, leave it out rather than guess.
2. Never reveal answers. The `questions[]` array tells you which topics and skills to cover, but the
   brief must not include any `answer.value`, `answer.tolerance`, which option is correct, or
   `answer.reason` text. Turn questions into goals and context, not solutions.
3. Write for the participant. Use second person ("you", "your team"), present tense, and a concise
   operational tone. Do not describe the JSON or the process of writing the brief.
4. Only emit a section if the JSON supports it. Scale the brief to the scenario: a simple scenario
   may need only the header, overview, mission goals, operator terminal, spacecraft, before you
   begin, and learning focuses.
5. Use tables for specifications and blockquotes (`>`) for tips and warnings, matching the existing
   briefs.
6. Treat images as placeholders. Insert the S3 placeholder links described below wherever a
   schematic, diagram, or map would help the reader. Do not claim an image exists beyond the
   placeholder.

## Writing style

The brief should read like it was written by an experienced mission author, not generated. Keep the
prose plain and direct.

- Do not use em dashes (`-`, `\u2014`) or en dashes (`\u2013`) as sentence punctuation. Use a plain
  hyphen with spaces, a comma, a colon, or split the sentence in two. The one exception is numeric
  ranges inside spec tables (for example a field-of-view range), where the existing briefs use an en
  dash; match whatever the sibling briefs already do.
- Keep the rest of the text ASCII. The degree symbol and the multiplication sign in resolutions
  (for example 1024 x 1024) are fine because the existing briefs use them.
- Avoid filler and cliches. Skip phrases like "in today's world", "it is important to note",
  "seamless", "robust", "leverage", "delve", and "not just X but Y" constructions.
- Do not over-bold. Bold a term when it first matters, then use it plainly.
- Vary sentence length. Prefer short, concrete instructions over long qualified ones.
- Be specific. Name the actual components, stations, and values from the JSON instead of writing in
  the abstract.

## JSON to brief mapping

| JSON source | Brief use |
| --- | --- |
| `metadata.name` | Header `**Scenario:**` and title context |
| `metadata.description` | Basis for the Overview, rewritten in participant voice |
| `simulation.epoch` | Header `**Epoch:**`, formatted `YYYY-MM-DD HH:MM:SS UTC` |
| `simulation.end_time`, `simulation.speed` | Header `**Duration:**`. Sim minutes = `end_time / 60`. Wall-clock minutes = `end_time / (60 * speed)`. If `end_time` is 0, write "Open-ended (instructor-controlled)". If speed is not 1, state the sim time and the speed. |
| `ground_stations.locations` | Header ground segment line and the Communications section |
| `teams[]` | Team count, the Team Frequencies note, and a short Teams table when there are two or more. Never print passwords or keys. |
| `assets.space[]` (team craft) | Spacecraft Configuration: mass from `physics.mass`, orbit from `orbit.planet` and regime, plus component-derived rows |
| `assets.neutral[]` and neutral craft | Overview and an Environment or Other Participants note (hub, debris, rogue, and so on) |
| `Optical Camera` / `Camera` components | Cameras section: resolution, field of view, aperture, focusing distance. Infer opposite-facing boresights from `position` and `rotation` when two cameras exist. |
| Sensor components (LRF, GPS Sensor, EM Sensor) | Other sensors list |
| `power.bus` and power components | Power Network description and a component starting-states table, using `Is Open`, `Charge Fraction`, `Nominal Capacity`, and `enabled` |
| `fuel.bus` and fuel components | Fuel Network description, starting states, and transfer notes |
| `controller.enable_rpo_software`, `enable_intercept` | Operational Constraints (for example "RPO Software: Not available") |
| Components with `enabled: false` (for example Reaction Wheels), no `Thruster` present | Operational Constraints (disabled attitude control, no thrusters) |
| `docking[]` | Docked-start narrative, per-team port assignment, interconnect coupling |
| `events[]` | Timeline and anomaly context for Mission Goals and Communications, described as expectations rather than spoilers |
| Unique `questions[].section` values | Drives the Mission Goals phases and the Learning focuses themes, topic only |
| `objects.ground[]` (vessels, text, markers) | Observation or collection sections and an optional reference-map placeholder |

## Section order

Include the sections that apply, in this order.

1. Header block. Bold key and value lines (`**Scenario:**`, `**Epoch:**`, `**Duration:**`, and a
   ground segment or ground stations line), followed by `---`. End each header line with two spaces
   so they render on separate lines.
2. Overview. One or two short paragraphs from `metadata.description` plus the asset roles. Close
   with a blockquote that points participants to the in-terminal Tasks section and states the brief
   is context, not an answer key.
3. Mission Goals. Derive from the question sections, events, and asset configuration. For a complex
   scenario, break into `### Phase N - <Name>` with numbered, bolded action items. For a simple
   scenario, use a single numbered list. Add blockquote warnings for irreversible actions such as
   undocking.
4. Operational Constraints, when any exist. A two-column table.
5. Spacecraft Configuration. An intro line, an optional `### Schematic` image placeholder, and a
   `### Platform Summary` table (mass, orbit, power storage, propellant, sensors, comms, propulsion,
   attitude control).
6. Cameras, when optical cameras exist. An opposite-face table when there are two cameras, then a
   subsection per camera with a purpose line and a spec table, plus a short recommendation
   blockquote. Follow with an `### Other sensors` list.
7. Power Network, when `power.bus` is non-trivial. Description, diagram placeholder, and a
   starting-states table.
8. Fuel Network, when `fuel.bus` exists. Description, diagram placeholder, starting-states table,
   and a `### Fuel transfer notes` list.
9. Communications, when it matters. A ground station table, a Link Budget note, an
   `### Expected Contact Profile` table when a blackout or geometry constraint applies (derive the
   window from events or narrative, and soften to "approximately" when it is not explicitly timed),
   and a `### Team Frequencies` note.
10. Observation or Collection, when `objects.ground[]` is present. Operating area, target
    description (color, count, motion) without the scored answer, and an optional reference-map
    placeholder with usage bullets.
11. Suggested Team Roles. The standard four roles, adjusted to the subsystems this scenario uses.
    - Mission Lead: assigns roles, answers questions, monitors key information, makes go/no-go calls.
    - Satellite Operator: telemetry, guidance pointing, health, power and fuel transfer.
    - Payload Operator: camera and sensor data capture relevant to this scenario.
    - Communications Specialist: link budgets, GPS, contact windows, and blackout timing when it
      applies.
12. Before You Begin. Three or four numbered setup steps: log in, confirm map and telemetry, read
    the Tasks, split roles.
13. Learning focuses. One `### Heading` and a one-sentence outcome per major theme, drawn from the
    question sections and the scenario skills. Usually three or four.

## Image placeholders

Use this URL pattern, with the scenario name in snake_case:

```
https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/<scenario_snake>/<image>.png
```

Common images: `schematic.png`, `power_network_diagram.png`, `fuel_network_diagram.png`, and any
scenario-specific reference map such as `lunar_map.png`. Embed with `![Alt text](URL)`. Only add an
image where it helps the reader.

## Formatting details

- Separate major sections with `---`.
- Put the readable value in tables, not the raw JSON key.
- Do not include team passwords, Caesar keys, `answer` blocks, or `reason` text.
- Use numbered lists for procedures, bullets for enumerations, and blockquotes for tips and
  warnings.

## Output

Produce only the finished Markdown brief, ready to save as `<scenario_snake>_brief.md` in the
scenario folder. Before finishing, check two things: every fact in the brief traces back to the
JSON, and no scored answer is revealed.
