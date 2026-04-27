# Instructor & Admin Guide

The **admin** role in Space Range is the instructor / exercise controller — the person responsible for running a scenario, monitoring all teams, intervening when needed, and grading the result. This guide is a working playbook for that role.

It assumes:

- You have the **admin password** for the game (a 6-character alphanumeric string, distinct from any team password).
- Studio is running with a scenario loaded.
- You can reach the broker.

If any of those are not true, start at [Getting started → Prerequisites](../getting-started/prerequisites.md).

---

## What admin actually controls

Admin is **not** "team zero". The admin password unlocks a separate API on its own MQTT topic pair:

```text
Zendir/SpaceRange/<GAME>/Admin/Request
Zendir/SpaceRange/<GAME>/Admin/Response
```

Both XOR-encrypted with the admin password. The full request set is documented in [API reference → Admin requests](../api-reference/admin-requests.md).

| Capability | How |
| --- | --- |
| See every team's roster, assets, components | [`admin_list_entities`](../api-reference/admin-requests.md#admin_list_entities), [`admin_list_team`](../api-reference/admin-requests.md#admin_list_team) |
| Read any team's historical telemetry from the database | [`admin_query_data`](../api-reference/admin-requests.md#admin_query_data) |
| Inspect the event log (every team's actions) | [`admin_query_events`](../api-reference/admin-requests.md#admin_query_events) and the `admin_event_triggered` push |
| Pause, play, stop, and change speed of the simulation | [`admin_set_simulation`](../api-reference/admin-requests.md#admin_set_simulation) |
| List the scripted scenario events | [`admin_get_scenario_events`](../api-reference/admin-requests.md#admin_get_scenario_events) |

What admin **cannot** do directly:

- Send a spacecraft command on behalf of a team. To do that, you need that team's password (XOR layer is per-team) and you'd publish on the team's own `Uplink` topic.
- Read a team's encrypted `Downlink` payload contents without the team's password and Caesar key. (You can see the topic name and the message size, but not parse the body.)
- Edit the loaded scenario at runtime. Scenario changes require editing the JSON and re-loading in Studio.

In other words: **admin gives you visibility and timeline control, not impersonation.** This is the right model for instructors who must remain neutral.

---

## Connecting as admin

You have the same two options as a team operator:

### Option A — The bundled Operator UI

The Operator UI ships an **admin mode**, accessed by URL parameter:

```text
https://your-host/?server=mqtt.zendir.io&game=SPACE%20RANGE&password=ADMINP&admin=1
```

The `admin=1` flag tells the UI to skip the team selection and connect to the admin topic pair instead. Settings → Connection → "Admin Mode" exposes the same toggle in the UI.

In admin mode the views shift:

| View | What you see |
| --- | --- |
| **Map** | Every team's spacecraft and ground tracks, colour-coded by team. |
| **Teams** | Roster of all teams, current scores, asset state. |
| **Telemetry** | Per-asset link summaries across teams. |
| **Plots** | Plot any field of any asset across teams. |
| **Power** | Per-spacecraft power state across teams. |
| **Events** | Live + historical event log across teams. |
| **Timeline** | Scenario events with countdown timers. |
| **Settings** | Connection, theme, simulation control (play/pause/speed). |

### Option B — Custom client

A custom admin client connects exactly like a team client, with two changes: the topic root drops the team ID, and the password is the admin password. A minimal Python client:

```python
import json
import paho.mqtt.client as mqtt
from secrets import xor_crypt   # from the encryption walkthrough

GAME = "SPACE RANGE"
ADMIN_PASSWORD = "ADMINP"

REQ_TOPIC  = f"Zendir/SpaceRange/{GAME}/Admin/Request"
RESP_TOPIC = f"Zendir/SpaceRange/{GAME}/Admin/Response"

def admin_request(client, type_, args=None, req_id=0):
    payload = {"type": type_, "req_id": req_id}
    if args is not None:
        payload["args"] = args
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    client.publish(REQ_TOPIC, xor_crypt(ADMIN_PASSWORD, body))

def on_message(_c, _u, msg):
    if msg.topic != RESP_TOPIC:
        return
    decoded = xor_crypt(ADMIN_PASSWORD, msg.payload).decode("utf-8")
    print(json.loads(decoded))

client = mqtt.Client()
client.on_message = on_message
client.connect("broker.local", 1883)
client.subscribe(RESP_TOPIC)
admin_request(client, "admin_get_simulation")
client.loop_forever()
```

The `space-range-scripts` package wraps this in an `AdminClient` helper; see `space-range-scripts/src/admin_client.py` for the reference implementation.

---

## A pre-flight checklist

Before kicking off an exercise, walk through this checklist. It takes ~5 minutes and prevents most "we restarted three times" sessions.

1. **Studio is running and the right scenario is loaded.** Verify by calling `admin_get_simulation` and checking the broker has the topics for every expected team.
2. **Every team is in the roster.** Run `admin_list_entities` and confirm the names and IDs match what you'll hand out. If a team is missing, the team's `enabled` flag in the scenario JSON is `false` or its config has a parse error — fix and reload.
3. **Every spacecraft is alive.** For each team, fetch `admin_list_team` and check that `spacecraft[].asset_id` is set (not `null`). A `null` asset_id means the spacecraft definition failed to instantiate.
4. **Scenario events are visible.** Run `admin_get_scenario_events` and confirm the count matches the JSON. Note the trigger times; they're sim seconds from `t=0`, so plan your real-time launch around them.
5. **Simulation is paused at `t = 0`.** Check `admin_get_simulation`; if `state != "Paused"` or `current_time > 0`, [stop and reset](#stopping-and-resetting-the-simulation) before handing the keys to the operators.
6. **Operator credentials are distributed.** Each team needs its team ID + password. The Operator UI's clipboard-copy on Settings → Connection generates a one-link-per-team URL to share.
7. **Your own admin client is connected and stable.** You don't want to be debugging broker connectivity once the exercise starts.

A scripted version of the checklist (Python) — useful to drop into a cold-start procedure:

```python
sim = admin.request("admin_get_simulation")["args"]
assert sim["state"] == "Paused" and sim["time"] == 0.0, sim

teams = admin.request("admin_list_entities")["args"]["teams"]
print(f"{len(teams)} teams loaded")

for t in teams:
    info = admin.request("admin_list_team", {"team_id": t["id"]})["args"]
    for sc in info["spacecraft"]:
        assert sc.get("asset_id"), f"{t['name']} / {sc['name']} not instantiated"

events = admin.request("admin_get_scenario_events")["args"]["events"]
print(f"{len(events)} scripted events on the timeline")
```

If anything fails the assertions, fix it before you start.

---

## Running the simulation

The simulation has three states, controlled by [`admin_set_simulation`](../api-reference/admin-requests.md#admin_set_simulation):

| State | Meaning |
| --- | --- |
| `Running` | Time is advancing at `speed × real-time`. |
| `Paused` | Time is frozen. Commands sent during a pause queue normally and execute by `Time` once running again. |
| `Stopped` | **Simulation is reset.** All asset state is wiped, the clock returns to `t=0`, and the [instance ID](../concepts/simulation-clock.md#instance-id-and-resets) increments. |

### Starting

```python
admin.request("admin_set_simulation", {"state": "Running", "speed": 1.0})
```

### Pausing & resuming

```python
admin.request("admin_set_simulation", {"state": "Paused"})  # freeze
# do whatever you need
admin.request("admin_set_simulation", {"state": "Running"}) # resume
```

Pausing is non-destructive: pending commands, telemetry buffers, and component state are all preserved.

### Changing the simulation speed

```python
admin.request("admin_set_simulation", {"speed": 4.0})
```

`speed` is sim-seconds per real-second. Allowed values vary slightly by build, but `0.25, 0.5, 1.0, 2.0, 4.0` are universally supported. Operators should be told before you change speed mid-exercise — fast forward changes the cadence of telemetry they're watching.

### Stopping and resetting the simulation

> **`Stopped` is destructive. Use only when you mean it.** It triggers a full reset: all asset state, schedules, queued telemetry, and tracked events are wiped, and the `instance` ID increments. Operators must re-fetch their assets and XTCE schemas after a reset.

```python
admin.request("admin_set_simulation", {"state": "Stopped"})
```

The simulation lands at `t=0, state=Paused, instance=<new>`. From there, set `Running` to restart, or send another `Stopped` to fully discard a corrupted state.

A clean reset in three calls:

```python
admin.request("admin_set_simulation", {"state": "Stopped"})       # reset
admin.request("admin_set_simulation", {"state": "Running",
                                       "speed": 1.0})              # start at 1×
```

Operators will see a session-clock discontinuity (sometimes a small backwards step into the new instance), then their UIs will repopulate against the fresh state.

### Scripted events vs. live commands

Scenario events fire on the simulation timeline regardless of pause/resume — they're scheduled in **simulation time**, not wall time. So pausing for ten real minutes does *not* delay the next scripted event.

If the next scripted event isn't due for an hour of sim time and you don't want to wait, increase `speed` until you reach the trigger time, then drop back to `1.0`.

---

## Watching what's happening

The `Admin/Response` topic is a firehose. There are three things on it you should keep an eye on:

### 1. Live event push: `admin_event_triggered`

Every time **any** team triggers a tracked event (sent a command, executed a command, captured an image, jammed something, …), Studio pushes one of these to `Admin/Response`:

```json
{
  "type":    "admin_event_triggered",
  "args":    {
    "team_id":   111111,
    "asset_id":  "A3F2C014",
    "type":      "command_executed",
    "time":      "2026-04-15T08:30:12Z",
    "sim_time":  742.18,
    "data":      { "command": "guidance", "success": true }
  }
}
```

Use it as the primary feed for your "what's going on" view. The Operator UI's admin **Events** view binds directly to this push.

`type` values you'll see (non-exhaustive):

- `command_sent`, `command_executed`, `command_failed`
- `capture_taken`, `downlink_sent`, `downlink_received`
- `jamming_started`, `jamming_stopped`
- `link_lost`, `link_restored`
- `safe_entered`, `safe_exited`, `rebooted`
- `question_answered`

### 2. Per-team scoring

If the scenario defines `questions[]`, each correct submission triggers a scoring update. The Operator UI's admin **Teams** view shows the running totals; programmatically, you can poll [`admin_query_events`](../api-reference/admin-requests.md#admin_query_events) with `type: "question_answered"`.

### 3. Historical drill-down

For "what did Red Team do an hour ago?" investigations, query the database directly:

```python
admin.request("admin_query_events", {
    "team_id": 111111,
    "since":   "2026-04-15T07:30:00Z",
    "until":   "2026-04-15T08:30:00Z",
})
```

```python
admin.request("admin_query_data", {
    "asset_id":  "A3F2C014",
    "since":     "2026-04-15T07:30:00Z",
    "fields":    ["battery", "memory", "frequency"],
})
```

Both return Studio's persisted records, not just what's currently in memory — useful for after-action reports.

---

## Common interventions

### A team's spacecraft is bricked

Symptoms: no Pings, no link, no command acks, regardless of `downlink` retries.

Most likely a desynced Caesar key or frequency after a botched `encryption` rotation, or a stuck component error after a scripted event.

Without impersonating the team, your options are:

- **Wait it out.** The `reset_interval` after an `encryption` command is finite; the spacecraft will reboot.
- **Trigger a scenario event** that flips the failed component back via Studio's event mechanism (if your scenario includes such recovery events).
- **Reset the simulation.** Nuclear option; only when one team's recovery is worth disrupting everyone else.
- **Hand the team their own escape hatch.** Tell them to use [`set_telemetry`](../api-reference/ground-requests.md#set_telemetry) on the ground side to walk through plausible `(key, frequency)` combinations until they recover.

### A team is jamming everyone unintentionally

A misfired `jammer` command can take out the entire shared band. Diagnose with `admin_list_entities`'s asset listing (the team's spacecraft will report `jammer.is_active = true`) and either:

- Tell the team to send `jammer` with `state: "stop"`.
- Wait for the timer-bound jamming to expire.
- Pause the simulation while you sort it out.

### A scripted event needs to be skipped

You cannot delete or reorder a scripted event at runtime. You can:

- **Speed-run past it** by raising `speed` until you've cleared the trigger time, then dropping back.
- **Pause around it.** Pausing freezes the sim clock; the event still fires on the next tick after resume.
- **Edit the JSON and reset.** Toggle `Enabled: false` for the event, save, reload, hit `Stopped → Running`. Disruptive; use only when planning the next round.

### Mid-session reload

To swap scenarios mid-session, you must:

1. `admin_set_simulation` → `Stopped`.
2. Stop Studio, edit the loaded scenario file pointer (Studio config), restart Studio.
3. Push the new credentials to the operators (different scenarios usually have different team passwords).

There is no zero-downtime scenario hotswap.

---

## Distributing credentials

A practical pattern for handing out team credentials:

1. From the Operator UI, connect once to each team (in admin mode you can switch to a team's view if you also have its password — typically you'll have all of them as the instructor).
2. Click the clipboard icon next to **Connection Settings**. The UI copies a URL of the form `?server=...&game=...&team=...&password=...`.
3. Send each URL via the team's chosen channel (private chat, individual emails, in-room handout). **Don't** post these in shared channels — anyone with the URL can play as that team.

If you're running an exercise with strict secrecy, distribute team passwords on paper and let operators type them in by hand; never round-trip them through email or shared chat.

For larger competitions, generate the URLs programmatically:

```python
from urllib.parse import quote_plus

teams = admin.request("admin_list_entities")["args"]["teams"]
for t in teams:
    cfg = admin.request("admin_list_team", {"team_id": t["id"]})["args"]
    pw  = cfg["password"]
    url = (
        f"https://operator.zendir.io/"
        f"?server=mqtt.zendir.io"
        f"&game={quote_plus(GAME)}"
        f"&team={t['id']}"
        f"&password={pw}"
    )
    print(t["name"], "→", url)
```

---

## After-action: extracting results

When the exercise is over, what you usually want is:

1. **Final score per team** — call `admin_query_events` filtered by `type: "question_answered"` and aggregate.
2. **Command history** — `admin_query_events` for each team filtered by command-related types.
3. **Telemetry over time** — `admin_query_data` per asset, full time range, all fields.
4. **Captured imagery** — these aren't in the structured database; they'll be in your team operators' clients (the Operator UI's **Image** view) or in any custom storage you configured. Make sure operators export imagery before disconnecting if you need it for review.

Bundle all of those into a per-team report; your scenario authors will thank you for the feedback when designing the next iteration.

---

## Next

- [Operator UI guide](operator-ui-guide.md) — the views your operators see and the workflow you'll observe them following.
- [Scenario configuration](scenario-config.md) — the JSON file backing every exercise.
- [API reference → Admin requests](../api-reference/admin-requests.md) — the full set of admin calls.
- [Troubleshooting & FAQ](troubleshooting.md) — diagnostic playbooks for common issues.
