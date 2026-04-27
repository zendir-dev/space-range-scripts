# Session Stream

The session topic carries the scenario clock and instance ID. Every Space Range client should subscribe to it — it is the only reliable signal that the simulation is running, what time it thinks it is, and whether a reset has happened.

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
| Cadence | ~3 Hz (every ~0.3 s of real time) while the simulation is running |
| QoS | 0, not retained |
| Quiet behaviour | No publishes when the simulation is paused or stopped |

If you stop receiving session messages for more than ~1 s, treat the simulation as paused or disconnected. Do not try to drive your own clock forward in that case — wait for it to resume.

---

## Payload

```json
{
  "time": 32.5,
  "utc": "2026/01/26 13:23:13",
  "instance": 10234141
}
```

| Field | Type | Description |
| --- | --- | --- |
| `time` | `number` (seconds) | Simulation time since `t = 0`. Driven by the scenario, not the wall clock. May advance faster, slower, or backwards (on scrubbing) relative to real time. |
| `utc` | `string` | Simulation UTC, formatted `YYYY/MM/DD HH:MM:SS`. Computed from the scenario epoch plus `time`; useful for orbital mechanics and ground-track plots. |
| `instance` | `integer` | A unique ID for this run of the scenario. Changes whenever the scenario is reset or reloaded. |

The clock can change non-monotonically. If the simulation is **scrubbed** (rewound through history), `time` will jump backwards while `instance` stays the same. If the simulation is **reset**, `time` returns to `0` and `instance` changes.

---

## Detecting resets

Cache the most recent `instance` value. On every message, compare:

- `instance` unchanged → normal tick.
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
    sim_time = s["time"]
    sim_utc  = s["utc"]
    instance = s["instance"]

    if last_instance is not None and instance != last_instance:
        print(f"[reset] new instance {instance}, clearing local state")
        # ... clear caches, resubscribe, re-query ...

    last_instance = instance
    print(f"t = {sim_time:8.2f} s   utc = {sim_utc}   instance = {instance}")

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
    // ... clear caches, resubscribe, re-query ...
  }
  lastInstance = s.instance;
  console.log(`t = ${s.time.toFixed(2)} s   utc = ${s.utc}   instance = ${s.instance}`);
});
```

---

## Driving timestamps from the session clock

Spacecraft commands carry a `Time` field which is **simulation seconds**, not wall-clock time. The session clock is the right source for that value.

```python
# scheduling a command 30 s in the future
fire_at = last_sim_time + 30.0
uplink({
    "Asset":   "A3F2C014",
    "Command": "guidance",
    "Time":    fire_at,
    "Args":    {"mode": "sun"},
})
```

If you compute `fire_at` from `time.time()` (wall clock), the command will either fire immediately (if the sim runs faster than real-time) or never (if it runs slower). Always anchor command times to the most recent `time` from the session topic.

---

## Common pitfalls

- **Subscribing to the wrong topic.** If `<GAME>` doesn't match exactly (case, spaces), you'll get nothing. Copy the value from the scenario's connection settings.
- **Assuming sim time advances at 1× real time.** It doesn't, by default. The instructor may be running at 5×, 10×, paused, or scrubbing — watch the session deltas, not your wall clock.
- **Persisting telemetry across instances.** When `instance` changes, the asset IDs, encryption keys, and frequencies may all be different in the new scenario. Re-query everything.
- **Treating it as encrypted.** It isn't. If you XOR-decrypt the session payload with a team password, you'll get garbage. Parse it as plain ASCII JSON.

---

## Next

- [MQTT topics](mqtt-topics.md) — the full topic map.
- [Concepts → Simulation clock](../concepts/simulation-clock.md) — deeper background on simulation time and instances.
- [Spacecraft commands](spacecraft-commands.md) — uses `time` for scheduling.
