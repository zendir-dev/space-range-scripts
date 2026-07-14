# Session Stream

The session topic carries the scenario clock, simulation state, and instance ID. Every Space Range client should subscribe to it — use it to drive UI clocks, know whether the sim is advancing, and detect resets.

This is the only public topic that is **not** encrypted: it contains no team-specific information.

---

## Topic

```text
Zendir/SpaceRange/<GAME>/Session
```

| Property | Value |
| --- | --- |
| Direction | Studio → all clients |
| Encryption | None — plain ASCII JSON |
| Cadence | ~3.3 Hz (one message every **~0.3 s** of real time) while Studio is connected |
| QoS | 0, not retained |

Messages continue at this cadence across all simulation states; use the **`state`** field (not silence on the topic) to tell whether time is advancing.

---

## Payload

```json
{
  "timestamp": 1780458776,
  "time":      321.3,
  "utc":       "2024/05/23 12:01:32",
  "instance":  12345678,
  "state":     "running"
}
```

| Field | Type | Description |
| --- | --- | --- |
| `timestamp` | `number` | **Real-time** UNIX epoch seconds (wall clock when the message was published). Not simulation time — use for client-side latency, staleness checks, or correlating with external logs. |
| `time` | `number` (seconds) | **Simulation** time since `t = 0` for the current `instance`. Used for command `Time` fields and telemetry scheduling. May advance faster, slower, or backwards (on scrub) relative to real time. |
| `utc` | `string` | **Simulation** UTC at this `time`, formatted `YYYY/MM/DD HH:MM:SS` (epoch from the scenario plus `time`). For display and orbital plots — do not treat as wall-clock UTC. |
| `instance` | `integer` | Unique ID for this run of the scenario. **Changes when the game resets** (new scenario load or instructor `Stopped`). Clients should clear cached assets, schemas, and telemetry when `instance` changes. |
| `state` | `string` | High-level simulation state. One of `running`, `standby`, `paused`, `ended` (see [Simulation states](#simulation-states)). |

### Deprecated: `running`

Older builds also sent a boolean `running`. **Do not use it** in new clients — it will be removed in a future release. Use **`state`** instead:

| Legacy `running` | Use `state` |
| --- | --- |
| implied active | `"running"` |
| implied inactive | `"paused"`, `"standby"`, or `"ended"` as appropriate |

---

## Simulation states

| `state` | Typical meaning |
| --- | --- |
| `running` | Simulation clock is advancing (subject to `speed` from [`admin_set_simulation`](admin-requests.md#admin_set_simulation)). |
| `standby` | Scenario loaded; clock not advancing (e.g. before start or between runs). |
| `paused` | Time frozen; queued commands retain their scheduled `Time` values. |
| `ended` | Run finished or scenario torn down; do not schedule new work against this `instance`. |

Only treat **`state == "running"`** as “sim time is moving.” When paused or in standby, `time` may stay flat between ticks even though messages still arrive every ~0.3 s.

Admin [`admin_set_simulation`](admin-requests.md#admin_set_simulation) uses `Running` / `Paused` / `Stopped` (PascalCase) on the request API; the Session topic mirrors that lifecycle with the lowercase `state` strings above. A `Stopped` admin action resets the sim and bumps `instance`.

---

## Detecting resets

Cache the most recent `instance` value. On every message:

- `instance` unchanged → normal tick (still check `state` for UI).
- `instance` changed → scenario reset. Discard cached state (asset lists, telemetry, schedules) and re-query everything you need.

Without this check, your client will keep showing data from the previous run after the instructor restarts the scenario.

---

## Examples

### Python

```python
import json
import paho.mqtt.client as mqtt

GAME = "SPACE RANGE"

last_instance = None

def on_message(client, userdata, msg):
    global last_instance
    s = json.loads(msg.payload.decode("ascii"))

    if last_instance is not None and s["instance"] != last_instance:
        print(f"[reset] new instance {s['instance']}, clearing local state")
        # ... clear caches, re-query list_assets, get_packet_schemas, ...

    last_instance = s["instance"]

    if s.get("state") != "running":
        print(f"[{s['state']}] t={s['time']:.2f}s — sim not advancing")
        return

    print(
        f"t={s['time']:8.2f}s  utc={s['utc']}  "
        f"instance={s['instance']}  wall={s['timestamp']:.0f}"
    )

client = mqtt.Client()
client.on_message = on_message
client.connect("broker.local", 1883)
client.subscribe(f"Zendir/SpaceRange/{GAME}/Session")
client.loop_forever()
```

### JavaScript

```js
import mqtt from "mqtt";

const GAME = "SPACE RANGE";
let lastInstance = null;

const client = mqtt.connect("ws://broker.local:9001");
client.on("connect", () => {
  client.subscribe(`Zendir/SpaceRange/${GAME}/Session`);
});

client.on("message", (_, payload) => {
  const s = JSON.parse(payload.toString("ascii"));

  if (lastInstance !== null && s.instance !== lastInstance) {
    console.log(`[reset] new instance ${s.instance}, clearing local state`);
    // ... clear caches, re-query ...
  }
  lastInstance = s.instance;

  if (s.state !== "running") {
    console.log(`[${s.state}] t=${s.time.toFixed(2)}s — sim not advancing`);
    return;
  }

  console.log(
    `t=${s.time.toFixed(2)} s  utc=${s.utc}  instance=${s.instance}`
  );
});
```

---

## Driving timestamps from the session clock

Spacecraft commands carry a `Time` field which is **simulation seconds** (`time`), not `timestamp` and not wall clock. The session topic is the right source for scheduling.

```python
# schedule a command 30 sim-seconds in the future (only when state == "running")
fire_at = last_sim_time + 30.0
uplink({
    "Asset":   "A3F2C014",
    "Command": "guidance",
    "Time":    fire_at,
    "Args":    {"mode": "sun"},
})
```

If you compute `fire_at` from `time.time()` or from `timestamp`, the command will fire at the wrong sim instant. Always anchor command times to the most recent session **`time`**.

---

## Common pitfalls

- **Subscribing to the wrong topic.** If `<GAME>` doesn't match exactly (case, spaces), you'll get nothing. Copy the value from the scenario's connection settings.
- **Using deprecated `running`.** Prefer `state`.
- **Assuming silence means paused.** The topic keeps publishing at ~0.3 s; read `state` instead.
- **Assuming sim time advances at 1× real time.** Watch `time` deltas between ticks when `state` is `running`, not your wall clock.
- **Confusing `timestamp` and `time`.** `timestamp` is real-time UNIX; `time` is simulation seconds.
- **Persisting telemetry across instances.** When `instance` changes, re-query assets and XTCE schemas.
- **Treating the topic as encrypted.** Parse plain ASCII JSON — XOR with a team password produces garbage.

---

## Next

- [MQTT topics](mqtt-topics.md) — the full topic map.
- [Concepts → Simulation clock](../concepts/simulation-clock.md) — deeper background on simulation time and instances.
- [Spacecraft commands](spacecraft-commands.md) — uses `time` for scheduling.
