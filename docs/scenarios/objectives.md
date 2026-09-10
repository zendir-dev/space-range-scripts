# `objectives[]`: Parameter-Triggered Scoring

The `objectives[]` array is how a scenario awards points for something a team *achieves* on their spacecraft. Each entry watches one variable on one kind of component and pays the owning team when the value satisfies a condition.

An objective is the inverse of an [event](./events.md). An event runs on the clock and changes the spacecraft; an objective watches the spacecraft and changes the score.

| | Trigger | Effect |
| --- | --- | --- |
| `events[]` | Simulation time reaches `Time` | Write values onto components |
| `objectives[]` | A component variable satisfies a condition | Award points to the owning team |

Objectives and [`questions[]`](./questions.md) both feed the same per-team score. Questions score what a team *knows*; objectives score what a team *does*. A scenario can use either, both, or neither.

---

## Minimal Example

Charge the battery back above 80% and the team earns 25 points:

```json
"objectives": [
  {
    "enabled": true,
    "name": "Battery Recovered",
    "type": "spacecraft",
    "assets": [],
    "target": "Battery",
    "target name": "",
    "variable": "Charge Fraction",
    "operation": ">=",
    "value": "0.8",
    "award": {
      "points": 25.0,
      "reason": "Restored the battery to a safe state of charge.",
      "repeatable": false
    }
  }
]
```

---

## Fields

Keys are case-insensitive when loaded. Studio writes them in lowercase (unlike the PascalCase it uses inside `events[]`), so prefer lowercase here to keep exports and hand-authored files looking the same.

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `enabled` | `boolean` | `true` | A disabled objective still generates its events, so it stays visible and editable on the timeline, but they never fire and it can never pay out. |
| `name` | `string` | `"Objective"` | Human-readable label. Shown on the timeline under each spacecraft, and used as the award `reason` when none is given. |
| `type` | `string` | `"spacecraft"` | Only `spacecraft` does anything today. See [Type](#type) below. |
| `assets` | `string[]` | `[]` | Asset IDs the objective applies to (matches `assets.space[].id`). Empty `[]` means **every** spacecraft. |
| `target` | `string` | `""` | The component to watch, as an instance name or a class alias, optionally with a `-Model` suffix. **Required**: an objective with no target never binds. |
| `target name` | `string` | `""` | Narrows `target` to the components carrying this `components[].name`, ignoring case and spaces. Empty means every component `target` resolves to. |
| `variable` | `string` | `""` | The reflected variable on the target that is compared. **Required.** See [Choosing a Variable](#choosing-a-variable). |
| `operation` | `string` | `">="` | The comparison. Symbols and long names both work: see [Operators](#operators). |
| `value` | `string` | `""` | The value compared against, written as a string. See [Writing the Value](#writing-the-value). |
| `award.points` | `number` | `0.0` | Points added to the owning team's score. Negative values subtract, which is how a penalty is written. |
| `award.reason` | `string` | `""` | Explanation recorded against the award and shown in the score log. Falls back to `name` when empty. |
| `award.repeatable` | `boolean` | `false` | Whether a team can earn the objective more than once in a run. See [Repeatable](#repeatable). |
| `id` | `string` (GUID) | _(generated)_ | Reserved. Studio writes this into its own saved configuration so it can pair the file back up with what it has already built. **Leave it out of hand-authored scenarios**; one is generated on load. |

`award` is a nested object. The flattened form loads identically if you prefer it:

```json
"award.points": 25.0, "award.reason": "...", "award.repeatable": false
```

### Type

`type` accepts the same strings as an event's `Type` (`spacecraft`, `gps`, `cyber`, and `failure` as an alias for `spacecraft`), but only `spacecraft` is implemented. An objective with any other type is loaded, exported and preserved, and never binds to anything, so it can never score. Treat the field as reserved and always write `spacecraft`.

---

## How One Objective Becomes Many Events

This is the part worth understanding before authoring, because it explains almost every surprise.

You author **one** objective. Studio expands it into **one Studio event per component it resolves to**, on every spacecraft it applies to:

```text
objectives[0]  "Battery Recovered"
   │
   ├── Blue Team  / SC_001 / Battery      →  watches this battery,  pays Blue
   ├── Red Team   / SC_001 / Battery      →  watches this battery,  pays Red
   └── Green Team / SC_001 / Battery      →  watches this battery,  pays Green
```

Each generated event carries its own condition and its own scoring action, wired to the team that owns the craft the component sits on. That is why the fan-out is necessary: "has this battery just crossed 80%" is a question about one specific battery, and each team needs their own answer to it.

Consequences that follow from this:

- **You do not write anything per-team.** Teams are discovered from the craft that resolve, so one objective covers a three-team exercise the same way it covers a one-team exercise.
- **A craft with four batteries produces four events for that team.** Any one of them satisfying the condition pays the team. Use `target name` when you mean a specific one.
- **Objectives are scored, not events.** The generated events are the mechanism; the scenario file only ever describes the objective.

### Which Craft Are Skipped

A craft is skipped, silently, when:

- It is not in `assets` (and `assets` is non-empty).
- It is a **neutral** craft. Neutral craft belong to no team, so there is nobody to pay.
- Its team is **hidden** (every craft on the team is hidden). Such a team is not in the score ledger at all, so it has no score to add to.
- The `target` resolves to nothing on it, or the component it resolves to does not have the `variable`.

An objective where *no* craft binds at all is not discarded: Studio keeps the authored intent and retries after the next time the scenario is constructed. This is what makes an objective survive being authored before the spacecraft exist.

### On the Timeline

Generated events appear on the Studio timeline **under the spacecraft that owns the component**, alongside that craft's eclipses and scripted events, labelled with the objective `name`. The team is implied by which craft's row the event sits on, so the name stays the same for every team.

---

## Choosing a Target

`target` resolves exactly the way an event's `Target` does, through the same lookup:

1. An exact **component name** (`components[].name`) is tried first, ignoring case. Names containing a hyphen, such as `"Thruster 4 (-X)"`, match whole and are not split.
2. Failing that, the string is treated as a **class alias** (`Battery`, `Solar Panel`, `Reaction Wheels`, …) and matches every component of that class. See [`components.md`](./components.md) for the alias table.
3. If `target name` is set, the components found so far are narrowed to those carrying that name, ignoring case and spaces.

### Watching a Model

A `-` suffix watches a model attached to the component instead of the component itself:

```json
"target": "Battery-BatteryLeakageErrorModel",
"variable": "Power Leakage Rate"
```

The suffix is split from the **last** hyphen and is only treated as a model when that model class actually exists, which is what lets `"Thruster 4 (-X)"` keep working as a plain name.

One important difference from events: **an objective never brings a model into being.** An event that targets an error model attaches it; an objective only observes, so a component that does not already carry the model is skipped. Watching an error model is therefore only useful once something else — usually a scripted event — has attached it.

### Restricting to One Component

`target name` does for objectives exactly what it does for events, and is documented in full at [Restricting an Event to One Component](./events.md#restricting-an-event-to-one-component). The short version:

| `target` | `target name` | What is watched |
| --- | --- | --- |
| `"Solar Panel"` | `""` | Every solar panel. Any one of them meeting the condition pays the team. |
| `"Solar Panel"` | `"Solar Panel +X"` | Only the panel named `Solar Panel +X`. |
| `"Solar Panel"` | `"Battery A"` | Nothing. The name exists but is not a solar panel, so the objective never binds. |
| `"Thruster 1 (+X)"` | `""` | The one thruster with that name. `target name` adds nothing when `target` is already an instance name. |

This pairs naturally with a single-component fault: fail `Solar Panel +X` with an event that also uses `Target Name`, then write an objective against the same panel so the points depend on the team dealing with that specific one.

---

## Choosing a Variable

`variable` is the **reflected name of a property** on the component or model, not a `Data` key and not a telemetry field.

- The name is matched **ignoring case**, and **any spaces you write are removed** before matching. `"Charge Fraction"`, `"ChargeFraction"` and `"charge fraction"` all reach the same property. Write it spaced out; it reads better and costs nothing.
- Nothing else is normalised. Underscores, punctuation and spelling have to be right.

For a configurable property, the reflected name is the same name the component's `data` block uses, so [`components.md`](./components.md) is a good first place to look. Reflected properties are a **superset** of the configurable ones, though, and the read-only ones are usually the interesting ones to score on: `ChargeFraction` on a battery, `IsDocked` on a docking adapter, `Amount` on a fuel tank, `Allocated` on storage.

Two authoritative sources for a name, in order of convenience:

1. **Studio's objective editor** lists every variable the chosen target exposes, for the build you are actually running.
2. **The class reference** for the component in the Zendir API documentation lists every property with its description and units.

### What Can Be Watched

| Variable type | Watchable | Notes |
| --- | --- | --- |
| `Float` | Yes | The usual case. |
| `Int` | Yes | |
| `Bool` | Yes | Compared as `1` / `0`. |
| `Enum` | Yes | Compared as its integer index. |
| `Vector2` / `Vector3` / `Vector4` | Yes | Reduced to its **magnitude** before comparison. |
| `String`, `Guid`, `DateTime`, object references | No | |
| Arrays of anything | No | |

**Read-only properties are fine.** This is a real difference from events: an event has to write, so it needs a settable property, while an objective only reads. Much of the most interesting state to score on is read-only.

A vector is always compared by magnitude. There is no way to select a single component of a vector from the scenario file, so if you need "altitude above X" rather than "distance from origin above X", find a scalar property that already expresses it.

---

## Writing the Condition

### Operators

`operation` accepts a symbol or a long name, and is trimmed before matching.

| `operation` | Also accepted | Fires while |
| --- | --- | --- |
| `">="` | `larger_equal` | value is at or above the threshold |
| `"<="` | `less_equal` | value is at or below the threshold |
| `">"` | `larger` | value is strictly above the threshold |
| `"<"` | `less` | value is strictly below the threshold |
| `"=="` | `=`, `equal` | value matches, within a tolerance of `1e-6` |
| `"!="` | `<>`, `not_equal` | value differs by more than `1e-6` |
| `"passes"` | | the value **crosses** the threshold in either direction |

Any other operator name parses but never evaluates true, so the objective silently never scores. Stick to the seven above.

**Do not use `==` on a continuously varying quantity.** The tolerance is `1e-6`, so a drifting float will essentially never land inside it. `==` is for discrete values: an enum, a bool, an integer count, a fault-state code. For anything continuous, use `>=` or `<=` and pick the threshold that expresses the intent.

`passes` is the one to reach for when direction does not matter and you want the moment of crossing rather than the state of being past it.

### Writing the Value

`value` is always written as a **string**, and is decoded according to the type of the variable it is compared against.

| Variable type | Write | Example |
| --- | --- | --- |
| `Float` | The number | `"0.8"` |
| `Int` | The integer | `"3"` |
| `Bool` | `"true"` or `"false"` | `"true"` |
| `Enum` | The integer index | `"0"` |
| Vector | A single number, compared against the magnitude | `"250.0"` |

The bool decoding is literal: the only string that means true is the text `true`, in any casing. **Anything else reads as false, including `"1"`.** A bool objective that never scores is almost always this.

### When It Fires

The condition is evaluated every simulation step while the simulation is **running**, and the objective fires on the step the condition **becomes** true:

- Actions run once on entry. Holding the condition for the next ten minutes does not run them again.
- Once the condition stops holding, the objective re-arms. Entering the condition again fires it again.
- A disabled objective, or one whose simulation is paused or stopped, never fires.

So `award.repeatable` controls what happens across *separate entries* into the condition, not what happens while it holds.

---

## The Award

When an objective fires, points go to the team that owns the spacecraft carrying the component.

### Repeatable

| `award.repeatable` | Behaviour |
| --- | --- |
| `false` (default) | The team earns the objective **at most once per run**. The first craft on that team to satisfy the condition claims it, and every later attempt by that team is refused: a second craft, the same craft re-entering the condition, or a different component that resolved from the same objective. |
| `true` | The team earns the points on every entry into the condition, from any of their craft. |

Once-only is scoped to **the team**, not the craft and not the generated event. That is deliberate: an objective that fans out to four batteries on three craft should be worth its points once to that team, not twelve times.

The award history clears when the simulation run is reset, which re-arms every once-only objective for the next run.

### Points and Reason

`award.points` is added to the team's score, and negative values subtract, so a penalty is written as an objective with negative points and a condition describing the thing you do not want:

```json
{
  "name": "Battery Depleted",
  "target": "Battery", "variable": "Charge Fraction",
  "operation": "<=", "value": "0.05",
  "award": { "points": -20.0, "reason": "Allowed the battery to run flat.", "repeatable": false }
}
```

`award.reason` is what appears in the score log next to the points. Write it as a statement of what the team did, since that is what an instructor reads back afterwards. When it is empty the objective `name` is used, which is usually terser than you want.

---

## Recipes

Variable names below are taken from the component class reference. Confirm them against your build in Studio before relying on one.

### Complete a Docking

A bool variable, which is the cleanest kind of objective to write: there is no threshold to argue about.

```json
{
  "enabled": true, "name": "Docked With the Hub",
  "type": "spacecraft", "assets": ["SC_SERVICER"],
  "target": "Docking Adapter",
  "variable": "Is Docked", "operation": "==", "value": "true",
  "award": {
    "points": 100.0,
    "reason": "Completed the docking approach and captured the hub.",
    "repeatable": false
  }
}
```

### Catch a Degraded Solar Panel

Pairs with the single-panel degradation event in [`events.md`](./events.md#restricting-an-event-to-one-component), which eats into `Efficiency` over time. This scores the team for noticing, by asking them to isolate the panel before it drops below a threshold.

```json
{
  "enabled": true, "name": "Degraded Panel Identified",
  "type": "spacecraft", "assets": [],
  "target": "Solar Panel", "target name": "Solar Panel +X",
  "variable": "Efficiency", "operation": "<=", "value": "0.3",
  "award": {
    "points": 30.0,
    "reason": "Panel +X degraded past the reporting threshold.",
    "repeatable": false
  }
}
```

### Complete a Fuel Transfer

```json
{
  "enabled": true, "name": "Tank Refuelled",
  "type": "spacecraft", "assets": ["SC_CLIENT"],
  "target": "Fuel Source", "target name": "Main Tank",
  "variable": "Amount", "operation": ">=", "value": "40.0",
  "award": {
    "points": 50.0,
    "reason": "Transferred propellant to the client tank.",
    "repeatable": false
  }
}
```

Scoping to `SC_CLIENT` matters here: without it, the supply tank on the tanker would also be watched, and it starts already full.

### Clear a Sensor Fault

`Fault State` is an integer where `0` is healthy, so this scores the team for resetting the sensor.

```json
{
  "enabled": true, "name": "GPS Sensor Healthy",
  "type": "spacecraft", "assets": [],
  "target": "GPS Sensor",
  "variable": "Fault State", "operation": "==", "value": "0",
  "award": {
    "points": 20.0,
    "reason": "Cleared the GPS sensor fault.",
    "repeatable": false
  }
}
```

Note that this is true from the start of the scenario unless the sensor begins faulted. An objective whose condition already holds when the run begins is claimed immediately. Pair a recovery objective with the event that causes the fault, and give the event a `Time` early enough that the fault lands before anyone can trip the objective.

### Flush Storage by Downlinking

`Allocated` is the memory currently used across the storage unit, so it drops when a downlink flushes the buffer. Repeatable, so a team is paid for each flush rather than only the first.

```json
{
  "enabled": true, "name": "Storage Flushed",
  "type": "spacecraft", "assets": [],
  "target": "Storage",
  "variable": "Allocated", "operation": "<=", "value": "1000",
  "award": {
    "points": 10.0,
    "reason": "Downlinked the stored imagery.",
    "repeatable": true
  }
}
```

Storage starts empty, so this condition holds at `t=0` and would be claimed immediately. Give the team something to capture first, or raise the threshold to a level only a real downlink reaches.

---

## Authoring Tips

- **Check the variable name in Studio first.** The single most common reason an objective never scores is a variable that does not exist on the target. The objective binds nothing and says nothing about it.
- **Ask whether the condition already holds at `t=0`.** A once-only objective whose condition is true at the start is claimed in the first simulation step, by whichever team gets there first, for doing nothing. Either invert the condition, or make sure an event puts the craft into the state the team has to recover from.
- **Scope with `assets` when craft differ.** An objective across a mixed fleet binds to whatever resolves, which is rarely what you meant when only one craft is supposed to be doing the task.
- **Pair objectives with events.** The strongest scenarios break something, then pay for fixing it. The event and the objective should agree on `target` and `target name` so they refer to the same hardware.
- **Prefer `>=` and `<=` over `>` and `<`.** A threshold that has to be *exceeded* rather than *reached* is usually an accident, and is invisible in review.
- **Keep points on a consistent scale** across objectives and [`questions[]`](./questions.md), since they land in the same score.
- **Disable, don't delete,** while iterating. `"enabled": false` keeps the objective in the file next to its related entries.

---

## When an Objective Never Scores

Work down this list; it is roughly ordered by how often each one is the answer.

1. **The variable name is wrong.** Confirm it against Studio's variable list for that target, remembering that spaces are stripped but nothing else is.
2. **The variable is not a watchable type.** Strings, arrays and object references cannot be watched at all.
3. **The target resolves to nothing.** Check `target` against `components[].name` and the class aliases in [`components.md`](./components.md).
4. **`target name` narrowed it to nothing.** The class resolved, then the name filter removed everything. The match ignores case and spaces but not punctuation.
5. **The model is not attached.** An objective watching `Component-SomeErrorModel` skips any component that does not already carry that model, and never attaches one.
6. **The craft has no team to pay.** Neutral craft and fully hidden teams are skipped.
7. **`assets` does not match.** The IDs must match `assets.space[].id`.
8. **The operator never evaluates.** Only `>=`, `<=`, `>`, `<`, `==`, `!=` and `passes` do anything.
9. **`==` on a float.** The tolerance is `1e-6`. Use a threshold comparison instead.
10. **A bool `value` that is not the text `true`.** `"1"`, `"yes"` and `"True "` with a trailing space all read as false.
11. **It already fired.** With `"repeatable": false` the team gets it once per run. Check the score log for an award that was claimed earlier than you expected, then reset the run.
12. **`"enabled": false`,** or the simulation is not running.

---

## See Also

- [`events.md`](./events.md): the other half of the pairing, and the shared `Target` / `Target Name` rules.
- [`questions.md`](./questions.md): the other input to a team's score.
- [`components.md`](./components.md): class aliases for `target`, and the configurable properties of every component.
- [`teams.md`](./teams.md): how a team comes to own a spacecraft, which is what decides who an objective pays.
