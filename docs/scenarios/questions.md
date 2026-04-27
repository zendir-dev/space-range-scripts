# `questions[]` — scenario Q&A

The `questions[]` array holds the assessment that operators submit answers against during the run. Each entry is parsed into `FSpaceRangeScenarioQuestion` (`studio/Plugins/SpaceRange/Source/SpaceRange/Public/Structs/SpaceRangeScenarioQuestion.h`) by `LoadFromScenarioDefinitionJson`, scored by `EvaluateSubmission`, and surfaced to clients via `ToClientListEntryJson`.

Question IDs are **assigned automatically** in load order (1, 2, 3, …). Authors do not write `id` into the JSON.

```json
"questions": [
  { "section": "...", "title": "...", "description": "...", "type": "...", "answer": { ... } }
]
```

The full structure of a question depends on its `type`. All the question types follow the same outer shape — only the `answer` block differs.

## Common fields

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `section` | `string` | `""` | Display group. Questions that share a `section` are grouped together in the operator UI. Use a short title (`"Red Sea (Counter-Piracy)"`, `"Orbital Operations"`, …). |
| `title` | `string` | `""` | One-line question prompt. |
| `description` | `string` | `""` | Longer body shown beneath the title. Supports plain text only — no HTML or markdown. |
| `type` | `string` | _(required)_ | One of `text`, `number` (alias `numeric`), `select`, `checkbox`. **Lowercase**. A missing or unrecognised `type` causes the question to be skipped entirely with no error in the scenario load log. |
| `answer` | `object` _or_ implicit (see below) | _(required)_ | Type-specific correctness data plus `score`. |
| `answer.score` | `number` (int) | `0` | Points awarded for a fully correct submission. Rounded to nearest integer. Set this on every question — `0` is loadable but useless. |

> The `type` string is one of the few values in the scenario JSON that is **case-sensitive in practice**: it is lower-cased before parsing, but the canonical form everywhere in the codebase is lowercase. Stick to lowercase to avoid confusion with elsewhere in the schema where casing is flexible.

### Two ways to express `answer`

The parser supports two equivalent shapes — pick one and stay consistent within a scenario file:

**Embedded object (recommended, used by every shipped scenario):**

```json
{
  "type": "number",
  "answer": { "value": 7, "tolerance": 0.5, "unit": "deg", "score": 4 }
}
```

**Dotted notation:**

```json
{
  "type": "number",
  "answer.value": 7,
  "answer.tolerance": 0.5,
  "answer.unit": "deg",
  "answer.score": 4
}
```

Both parse identically because of the `K()` lambda in `LoadFromScenarioDefinitionJson` — when `answer` is an object string starting with `{`, it is read directly; otherwise the parser falls back to dotted lookups on the outer object.

## Question types

### `type: "text"`

Free-text answer. Compared to `answer.value` after **trimming whitespace and lower-casing both sides**. There is no fuzzy matching: spelling matters.

| `answer` field | Type | Default | Description |
| --- | --- | --- | --- |
| `value` | `string` | `""` | The expected answer. |
| `reason` | `string` | `""` | Explanation shown when the team submits any incorrect text. |
| `score` | `number` | `0` | Points awarded for an exact (case-insensitive) match. |

```json
{
  "section": "Rogue Spacecraft",
  "title": "Identify the Rogue Spacecraft's identity.",
  "description": "Hint: Look for any text or markings on the spacecraft that can provide clues to its identity.",
  "type": "text",
  "answer": {
    "value": "RECON",
    "reason": "This word can be spotted on the solar panels of the rogue spacecraft.",
    "score": 4
  }
}
```

> Authoring tip: keep `value` short and unambiguous. There is no support for multiple correct answers — if a question has two valid synonyms, pick the most likely answer and add the alternative to `description` (`"... answer with the call sign, not the registration code"`).

### `type: "number"` (alias `numeric`)

Numeric answer with a tolerance band. Correct iff `|submitted - value| <= tolerance + epsilon`.

| `answer` field | Type | Default | Description |
| --- | --- | --- | --- |
| `value` | `number` | _(required)_ | The expected answer. **A question with no `value` key fails to load.** |
| `tolerance` | `number` | `0.0` | Acceptable absolute deviation. `0` requires an exact match (rarely what you want for floats). |
| `unit` | `string` | `""` | Unit label shown next to the input box (e.g. `"km"`, `"deg"`, `"MHz"`, `"dB"`). Cosmetic only — submissions are not unit-converted. |
| `reason` | `string` | `""` | Explanation shown when the team is wrong. |
| `score` | `number` | `0` | Points for a correct answer (binary — partial credit is not awarded for "close" numbers). |

```json
{
  "section": "South China Sea (Island Construction)",
  "title": "New Island Latitude",
  "description": "Give the location of the newest island to the nearest 1 degree in latitude.",
  "type": "number",
  "answer": {
    "unit": "deg",
    "value": 16.1,
    "tolerance": 0.7,
    "reason": "This can be found in the Paracel Island group.",
    "score": 7
  }
}
```

> Pick `tolerance` so that the question is unambiguous but rewards real measurement, not guessing. For "to the nearest km" use `0.5`; for "to the nearest 100 km" use `50`.

### `type: "select"`

Single-choice from a list. The submission is the **zero-based index** of the chosen option, and the question is correct iff it matches `answer.value`.

| `answer` field | Type | Default | Description |
| --- | --- | --- | --- |
| `options` | `string[]` | `[]` | Choices in display order. |
| `value` | `integer` | _(required)_ | Zero-based index of the correct option. **Missing `value` causes the question to fail to load.** |
| `reason` | `string[]` | `[]` | Per-option explanation shown when the team picks that option (only shown for the wrong picks; ignored for the correct one). One entry per option, in the same order as `options`. Provide a sensible message for every wrong option, otherwise the UI falls back to `"The value is wrong."` |
| `score` | `number` | `0` | Points for picking the right index. |

```json
{
  "section": "Red Sea (Counter-Piracy)",
  "title": "Identify the destructive vessel",
  "description": "Which non-green colored ship do you suspect to be a bad actor?",
  "type": "select",
  "answer": {
    "options": ["Blue", "Red", "White", "Yellow"],
    "value": 3,
    "reason": [
      "It's Yellow — only ship hovering near the damaged ships.",
      "It's Yellow — only ship hovering near the damaged ships.",
      "It's Yellow — only ship hovering near the damaged ships.",
      "It's Yellow — only ship hovering near the damaged ships."
    ],
    "score": 8
  }
}
```

> The `reason` array can be shorter than `options` (e.g. a single entry covering the most likely misclick). The UI uses `reasons[index]` only if it exists and is non-empty; otherwise it defaults to `"The value is wrong."`.

### `type: "checkbox"`

Multi-select from a list. The submission is an array of zero-based indices.

#### Scoring rules — read carefully

The scoring is **strict-then-partial**:

1. Build the set of correct indices `C` from `answer.value` (de-duplicated and sorted internally).
2. If the submission contains **any** index that is **not** in `C`, the score is **zero**, regardless of how many correct boxes were also ticked. The reason is `"Incorrect selection (one or more invalid or wrong options chosen)."`.
3. Otherwise, count the number of correct hits `Hits` and award `round(score * Hits / |C|)`. Selecting all correct options and no incorrect options gives the full `score`. Selecting some correct options and no incorrect options gives partial credit, with `"Partial credit."` as the reason.

| `answer` field | Type | Default | Description |
| --- | --- | --- | --- |
| `options` | `string[]` | `[]` | Choices in display order. |
| `value` | `integer[]` | `[]` | Zero-based indices of all correct options. Order doesn't matter; duplicates are dropped. An empty array makes the question unscoreable (`"Question has no correct options defined."`). |
| `reason` | `string[]` | `[]` | Per-option rationale. Currently used for log/UI hints — there is no per-option penalty model. One overall message is fine. |
| `score` | `number` | `0` | Maximum points (awarded only when **all** correct options are selected and **no** incorrect ones). |

```json
{
  "section": "Rogue Spacecraft",
  "title": "What location(s) were affected by the interference anomaly?",
  "description": "Above which ground station(s) did the interference occur?",
  "type": "checkbox",
  "answer": {
    "options": [
      "Auckland", "Dubai", "Easter Island", "Madrid",
      "Miami", "Salvador", "Singapore"
    ],
    "value": [1, 2],
    "reason": [
      "Downlink jamming occurred over the Dubai and Easter Island ground stations."
    ],
    "score": 4
  }
}
```

> Because partial credit collapses to zero on **any** incorrect tick, checkbox questions effectively reward conservatism. If you want to penalise wrong picks more gently, prefer `select` (single-choice) or split the checkbox into multiple binary questions.

## Putting it together

A complete `questions` block from a real scenario:

```json
"questions": [
  {
    "section": "Orbital Operations",
    "title": "What is the Semi Major Axis (km) of your spacecraft's orbit?",
    "description": "Use the GPS telemetry to compute the average orbital radius.",
    "type": "number",
    "answer": { "unit": "km", "value": 8200.0, "tolerance": 100.0,
                "reason": "Computed from average altitude + Earth radius.",
                "score": 5 }
  },
  {
    "section": "Orbital Operations",
    "title": "During operations a component failure occurred. What component failed?",
    "description": "Use the telemetry data to identify the failed component.",
    "type": "select",
    "answer": {
      "options": [
        "Battery", "Computer", "GPS Sensor", "Reaction Wheels",
        "Reciever", "Solar Panel", "Storage", "Transmitter"
      ],
      "value": 0,
      "reason": [
        "The battery produced power spikes mid-mission — fixable with a reset."
      ],
      "score": 5
    }
  }
]
```

## Authoring checklist

- Group related questions with `section` so the UI groups them.
- Always set `score`. Total scenario score is the sum across questions; aim for a round number (50, 100).
- For `number`, set `tolerance` deliberately and include a `unit`.
- For `select`/`checkbox`, double-check the zero-based indices in `answer.value` against `answer.options`. Off-by-one is the most common bug.
- For `text`, trim whitespace mentally and pick a single canonical wording.
- Avoid trick questions whose correct answer depends on UI rounding — both submission parsing and the answer field round-trip through `double`.
- Re-load the scenario after every edit to confirm questions load (a missing `type` or `value` silently drops a question).

## See also

- [`events.md`](./events.md) — design fault events that questions can probe.
- [`README.md`](./README.md) — note about question IDs being auto-assigned.
- `studio/Plugins/SpaceRange/Source/SpaceRange/Private/Structs/SpaceRangeScenarioQuestion.cpp` — exact scoring code.
