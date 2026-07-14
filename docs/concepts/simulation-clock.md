# Simulation Clock

Space Range runs on **simulation time** — a virtual clock that starts at `0.0` when a scenario begins and advances independently of wall-clock time. Every command schedule, every telemetry timestamp, and every scenario event is expressed in simulation seconds. The session topic also carries a **real-time** `timestamp` and a simulation `utc` string for display.

This page covers how the clock is exposed, how clients should consume it, and how the **instance ID** lets clients detect resets.

---

## The session topic

Studio publishes session status continuously on a single, **unencrypted** topic:

```text
Zendir/SpaceRange/<GAME>/Session
```

Updates arrive at **~3.3 Hz** (about every **0.3 s** of real time) whenever Studio is connected. The topic is QoS 0 and not retained — subscribe early to see the next tick.

### Packet format

```json
{
  "timestamp": 213214214121.0,
  "time":      321.3,
  "utc":       "2024/05/23 12:01:32",
  "instance":  12345678,
  "state":     "running"
}
```

| Field | Type | Description |
| --- | --- | --- |
| `timestamp` | number | Real-time UNIX epoch seconds when this message was sent. **Not** simulation time. |
| `time` | number (seconds) | Simulation time since `t = 0` for the current `instance`. |
| `utc` | string | Simulation UTC at this `time`: `YYYY/MM/DD HH:MM:SS`. Derived from the scenario epoch plus `time`. |
| `instance` | integer | Scenario instance ID. Changes on reset or reload — clients must clear cached state when it changes. |
| `state` | string | `running`, `standby`, `paused`, or `ended`. Use this to know whether the clock is advancing. |

The packet is plain ASCII JSON — no XOR, no Caesar cipher.

**Deprecated:** older builds included `"running": true/false`. Do not use it in new code; use `state` instead (the boolean will be removed in a future release).

### Simulation states

| `state` | Meaning for clients |
| --- | --- |
| `running` | Sim time is advancing (at `speed` from admin settings). |
| `standby` | Loaded but not advancing — e.g. before start. |
| `paused` | Frozen — `time` may repeat between ticks. |
| `ended` | Run over — do not assume further sim progress on this `instance`. |

Messages still arrive every ~0.3 s in non-`running` states; do not infer pause from a silent topic. See [Session stream](../api-reference/session-stream.md) for full field reference.

---

## Simulation time

Treat session **`time`** as the canonical clock for everything else in Space Range:

- **Command scheduling** — the `Time` field in spacecraft commands is in simulation seconds.
- **Telemetry timestamps** — CCSDS secondary headers and schedule reports use the same clock.
- **Scenario events** — admin event queries use sim-time where applicable.

Simulation time may not run at 1× wall-clock rate. Use **`state == "running"`** and deltas in **`time`** between session ticks — not `timestamp` and not `time.time()`.

### A simple session listener

```python
import json
import paho.mqtt.client as mqtt

def on_session(client, userdata, msg):
    pkt = json.loads(msg.payload.decode("utf-8"))
    print(
        f"state={pkt['state']}  t={pkt['time']:.2f}s  "
        f"utc={pkt['utc']}  instance={pkt['instance']}"
    )

client = mqtt.Client()
client.on_message = on_session
client.connect("broker.local", 1883)
client.subscribe("Zendir/SpaceRange/MyGame/Session")
client.loop_forever()
```

```javascript
// JavaScript (mqtt.js)
import mqtt from "mqtt";

const client = mqtt.connect("mqtt://broker.local:1883");
client.subscribe("Zendir/SpaceRange/MyGame/Session");
client.on("message", (_topic, payload) => {
  const pkt = JSON.parse(payload.toString("utf-8"));
  console.log(
    `state=${pkt.state}  t=${pkt.time.toFixed(2)}s  ` +
    `utc=${pkt.utc}  instance=${pkt.instance}`
  );
});
```

---

## Instance ID and resets

The `instance` field changes whenever the simulation is **reset** (instructor `Stopped`, scenario reload, or Studio restart). Clients must treat a change as “all cached data is stale.”

When `instance` changes:

1. **Drop all cached state** — asset lists, telemetry buffers, schedules, link budgets.
2. **Re-fetch XTCE schemas** via [`get_packet_schemas`](../api-reference/ground-requests.md#get_packet_schemas).
3. **Re-list assets** via [`list_assets`](../api-reference/ground-requests.md#list_assets).
4. **Re-apply telemetry configuration** if your client sets modes at startup.

The Operator UI does this automatically. Custom clients should compare `instance` on every session message.

### Time can go backwards

On reset, `time` typically returns to `0` and `instance` increments. On **scrub** (within the same instance), `time` may jump backwards while `instance` stays the same. Always pair **`(instance, time)`** when comparing two moments.

---

## Choosing how often to react

The ~0.3 s session feed is the natural heartbeat for UI clock displays. Use `state` to disable controls when not `running`. For coarser updates (e.g. once per simulated minute), check whether `floor(time / 60)` changed since the last tick.

---

## Next

- [Encryption](encryption.md) — XOR password and Caesar cipher.
- [Commands and scheduling](commands-and-scheduling.md) — using `Time` to schedule future commands.
- [API Reference → Session stream](../api-reference/session-stream.md) — wire format reference.
