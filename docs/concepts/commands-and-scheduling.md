# Commands and Scheduling

A **command** is a JSON object that a client publishes on a team's `Uplink` topic to drive a single spacecraft. Commands range from immediate one-shots (e.g. "take a picture now") to time-tagged future actions (e.g. "fire RCS at T+ 1200 s") to pure metadata operations (e.g. "remove a queued command").

This page describes the full lifecycle: how a command is built, encrypted, validated, scheduled, executed, and reported. It deliberately avoids per-command argument detail — for that, see [API Reference → Spacecraft commands](../api-reference/spacecraft-commands.md).

---

## The command envelope

Every uplink command — whatever its type — uses the same outer JSON shape:

```json
{
  "Asset": "A3F2C014",
  "Command": "guidance",
  "Time": 0.0,
  "Args": {
    "pointing": "nadir",
    "alignment": "+z"
  }
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `Asset` | string (8 hex chars) | yes | The asset ID of the target spacecraft. Case-insensitive. Studio rejects the command if this doesn't match a live asset on the receiving team. |
| `Command` | string | yes | The command type (e.g. `guidance`, `thrust`, `camera`). Case-insensitive. |
| `Time` | number (seconds) | no (default `0.0`) | Simulation time at which to execute. `≤ 0` means "as soon as possible". A future value queues the command. |
| `Args` | object | no | Command-specific arguments. Empty `{}` if the command takes no arguments. |

The uplink envelope does **not** include a command `ID`. **`Asset`** is the only targeting field the operator sets — it selects which spacecraft on the team should accept the command. After acceptance, the spacecraft controller assigns a unique integer **`ID`** to that queued command (see [Validation](#3-validation)); that ID is what appears in Ping executed-command lists, Schedule Reports, and in `Args` for [`remove_command`](../api-reference/spacecraft-commands.md#remove_command) / [`update_command`](../api-reference/spacecraft-commands.md#update_command).

> **Heads up on capitalisation.** The envelope keys are **PascalCase** (`Asset`, `Command`, `Time`, `Args`). The keys *inside* `Args` and the keys used in **ground requests** are typically **lowercase** (e.g. `pointing`, `alignment`, `asset_id`, `req_id`). Earlier versions of the schemas used lowercase outer keys; current Studio uses PascalCase and that is what these docs reflect.

---

## Lifecycle

```text
client                      broker                       Studio
  │                            │                            │
  │  build JSON envelope        │                            │
  │  XOR-encrypt with password │                            │
  ├───────► publish on Uplink  │                            │
  │                            ├──────► deliver to listener │
  │                            │                            │
  │                            │      decrypt + parse JSON  │
  │                            │      ┌────────────────────┤
  │                            │      │ valid Asset?        │  no  → record
  │                            │      │                    │       intercept,
  │                            │      └─Yes─┐               │       drop.
  │                            │            ▼               │
  │                            │      assign command ID      │
  │                            │      append to schedule     │
  │                            │      sort by Time           │
  │                            │                            │
  │                            │   when sim time ≥ Time:     │
  │                            │       execute handler       │
  │                            │       redact sensitive args │
  │                            │       append to "executed"  │
  │                            │       trigger event log     │
  │                            │                            │
  │                            │  side-effects emit telemetry│
  │  ◄──── eventually receive  │                            │
  │       telemetry/Ping       │                            │
```

### 1. Build

The client builds the envelope as a normal JSON object, populating `Args` with the type-specific fields documented in the command reference.

For a one-shot command, set `Time: 0` (or omit it). For a scheduled command, set `Time` to the desired simulation time. There is no "absolute UTC" form — all times are simulation seconds.

### 2. Encrypt

XOR-encrypt the JSON bytes with the team password and publish on:

```text
Zendir/SpaceRange/<GAME>/<TEAM>/Uplink
```

(See [Encryption](encryption.md) for the full algorithm.)

### 3. Validation

Studio's per-team listener decrypts the payload and dispatches it to **every** spacecraft owned by that team. Each spacecraft's `SpacecraftController` independently checks whether `Asset` matches its own ID:

- If the `Asset` field is empty, the command is dropped silently.
- If the `Asset` is non-empty but does not match this controller's ID, the command is dropped at this controller (a different controller on the team may still accept it).
- If `Asset` matches, the controller accepts the command and assigns a unique integer **command ID**. The ID comes from an internal counter (`CommandBufferID`): each new command initially uses the current counter value; if that ID is already present in the buffer (a rare collision guard), the counter is advanced until the ID is free. The command is then appended and the counter increments so the next uplink gets a fresh ID. After a scenario reset the counter returns to **1** with an empty buffer. An `UplinkIntercept` flag bit records successful parse and addressing.

This check happens *before* any argument validation. An ill-formed `Args` will not be detected until the command is actually executed; at that point the corresponding handler simply returns failure and the command is logged as "executed with success=false".

### 4. Scheduling

Every accepted command is stored in the controller's command buffer along with its target `Time` and the assigned command `ID`. The buffer is kept **sorted by `Time` ascending**, with ties broken by **`ID` ascending** so that two commands queued for the same simulation time execute in the order they were accepted (successive IDs reflect arrival order).

A command with `Time ≤ current sim time` is eligible to run on the next tick.

### 5. Execution

On each simulation tick:

1. The controller pops every command whose `Time` is now in the past.
2. It dispatches each one to the appropriate handler (`HandleGuidanceCommand`, `HandleCameraCommand`, etc.), which validates arguments, performs the action, and returns `success`.
3. The controller records an "executed" entry containing `ID`, `Command`, `Time`, `Success`, and `Args` (with sensitive keys redacted — see below).
4. The controller emits a **tracking event** to the simulation, which the admin can query via [`admin_query_events`](../api-reference/admin-requests.md#admin_query_events).
5. Side effects (e.g. an ADCS slew, a thruster burn, a captured image) are produced by the spacecraft's normal subsystems and any resulting telemetry follows the standard downlink path.

### 6. Reporting

The controller does **not** push a per-command success/failure response on the team's `Response` topic — that channel is reserved for ground-controller queries. Instead, executed and pending commands surface in two places:

- **Ping** telemetry messages list recently executed commands (with redacted args). See [Reference → Packet formats → Ping](../reference/packet-formats.md#ping).
- **[`get_schedule`](../api-reference/spacecraft-commands.md#get_schedule)** is itself a command that, when executed, emits a [Schedule Report](../reference/packet-formats.md#schedule-report) telemetry message listing every pending command currently in the buffer.

If you need to know whether a particular command succeeded, the typical approach is:

1. Learn the spacecraft-assigned **`ID`** from a Schedule Report ([`get_schedule`](../api-reference/spacecraft-commands.md#get_schedule)) or from an earlier Ping — you cannot set this field on uplink; it exists only after the command is accepted.
2. Watch incoming Pings for an executed-commands entry matching that **`ID`**, or fall back to correlating by **`(Time, Command)`** if you never captured the ID.
3. Examine the `Success` flag.

---

## Scheduling (`Time > 0`)

Setting `Time` in the future puts the command in the controller's pending queue. Schedules are durable for the lifetime of the simulation instance — they survive normal ticks but **not** scenario resets. (After a reset, the instance ID changes; see [Simulation clock](simulation-clock.md#instance-id-and-resets).)

Two side-effects to be aware of:

- **No conflict checking.** You can queue ten contradictory `guidance` commands for the same time, and Studio will execute all of them in order — typically with the last winning. It is the operator's responsibility to design their schedule sensibly.
- **Sensitive args are redacted on read-back.** When the schedule is reported back via [`get_schedule`](../api-reference/spacecraft-commands.md#get_schedule), any `password` field inside `Args` is stripped. This keeps the `encryption` rotation password from leaking via telemetry.

### Listing scheduled commands

```python
ground.uplink({
    "Asset": "A3F2C014",
    "Command": "get_schedule",
    "Time": 0,
    "Args": {}
})
# Wait for the next Schedule Report telemetry message on Downlink.
```

### Removing a scheduled command

Two ways to identify the command to remove:

- **By schedule `ID`** — preferred when you have it (Ping reports include the `ID`).
- **By `(Time, Command)` fallback** — used when the ID is unknown or stale. Removes the *first* pending command with that exact time and command type.

```json
{
  "Asset": "A3F2C014",
  "Command": "remove_command",
  "Args": { "ID": 123456789 }
}
```

```json
{
  "Asset": "A3F2C014",
  "Command": "remove_command",
  "Args": { "Time": 1200.0, "Command": "thrust" }
}
```

If neither match succeeds, the command is logged as failed and nothing is removed.

### Updating a scheduled command

[`update_command`](../api-reference/spacecraft-commands.md#update_command) lets you change the `Time` and/or `Args` of a pending command. The command type itself cannot be changed — to switch types, remove the old entry and add a new one.

```json
{
  "Asset": "A3F2C014",
  "Command": "update_command",
  "Args": {
    "ID": 123456789,
    "Time": 1500.0,
    "Args": "{\"thrust\": 1.0, \"duration\": 30.0}"
  }
}
```

The new `Time` **must be in the future**; updates that would land in the past are rejected.

---

## Validation, redaction, and security

A few non-obvious behaviours are worth knowing:

- **Asset matching is case-insensitive.** `a3f2c014` works. Internal storage is uppercase.
- **Lowercase command names are accepted.** Studio lowercases the `Command` field before dispatch. `Guidance`, `GUIDANCE`, and `guidance` all behave identically.
- **Unknown commands are logged at error level** but do not affect the simulation. The command is still recorded as "executed with success=false" in the executed-commands log.
- **`password` keys inside `Args` are stripped** before the command is exposed via Ping or Schedule Report. This is enforced server-side; you cannot bypass it.
- **Ground-side rejections** (e.g. asset belongs to a different team) result in *no* downlink reply — the failed command appears nowhere from the team's perspective. This is by design: there is no oracle that tells one team about another team's spacecraft.
- **Other teams' uplinks** that happen to be received by your spacecraft may appear as [Uplink Intercept](../reference/packet-formats.md#uplink-intercept) records if the spacecraft is configured to record them (`bRecordUplinkIntercept`). The bytes are re-encrypted with the receiver's key model so a SIGINT operator must work to decode them.

---

## Choosing immediate vs. scheduled

| When… | Use |
| --- | --- |
| The action depends on operator decisions made in the moment | `Time = 0` (immediate). |
| You have a precomputed plan (a maneuver sequence, an imaging campaign, a docking timeline) | Schedule each step at its target time. |
| You want a "fail-safe" — execute in N seconds unless cancelled | Schedule at `current_sim_time + N`, then `remove_command` to abort. |
| You need to pre-stage encryption rotation | Schedule the `encryption` command — but remember the spacecraft will be unreachable during the reboot interval. |

Scheduling does not consume any resources on the spacecraft itself (it's a Studio-side data structure), so feel free to queue dozens of commands per asset.

---

## Worked example

A two-step "image on next pass" plan:

```python
# t = 0 — set up the imager
ground.uplink({
    "Asset": "A3F2C014",
    "Command": "camera",
    "Time": 0,
    "Args": {"camera": "Camera A", "exposure": 0.02},
})

# t = 1200 — orient toward the target
ground.uplink({
    "Asset": "A3F2C014",
    "Command": "guidance",
    "Time": 1200,
    "Args": {
        "pointing": "location",
        "alignment": "+z",
        "target": "Camera A",
        "latitude": 35.6,
        "longitude": 139.7,
    },
})

# t = 1230 — capture
ground.uplink({
    "Asset": "A3F2C014",
    "Command": "capture",
    "Time": 1230,
    "Args": {"camera": "Camera A"},
})

# t = 1300 — downlink everything captured
ground.uplink({
    "Asset": "A3F2C014",
    "Command": "downlink",
    "Time": 1300,
    "Args": {"downlink": True, "ping": True},
})
```

Five seconds later you call `get_schedule` and see all four commands queued. Around `t = 1230` you start receiving image telemetry; around `t = 1300` you receive a Ping containing the executed-commands log entries for each of the four steps.

---

## Next

- [Telemetry](telemetry.md) — what comes back when a command runs (or fails).
- [API Reference → Spacecraft commands](../api-reference/spacecraft-commands.md) — every command type with its `Args`.
- [Reference → Packet formats](../reference/packet-formats.md) — Ping and Schedule Report layouts.
