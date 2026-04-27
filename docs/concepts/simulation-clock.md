# Simulation Clock

Space Range runs on **simulation time** — a virtual clock that starts at `0.0` when a scenario begins and advances independently of wall-clock time. Every command schedule, every telemetry timestamp, and every scenario event is expressed in simulation seconds. Wall-clock UTC is broadcast alongside the sim clock for human reference, but is rarely used by clients.

This page covers how the clock is exposed, how clients should consume it, and how the **instance ID** lets clients detect resets.

---

## The session topic

Studio publishes the clock continuously on a single, **unencrypted** topic:

```text
Zendir/SpaceRange/<GAME>/Session
```

Updates are emitted at **3 Hz** while the simulation is running (one packet every ~0.33 s of real time). The topic is QoS 0 and not retained — clients must subscribe before the next tick to see the next update.

### Packet format

```json
{
  "time": 32.5,
  "utc": "2026/01/26 13:23:13",
  "instance": 10234141
}
```

| Field | Type | Description |
| --- | --- | --- |
| `time` | number (seconds) | Current simulation time, measured in seconds since the start of the running scenario instance. |
| `utc` | string | Wall-clock-format UTC string. Derived from the simulation epoch plus `time`. Format: `YYYY/MM/DD HH:MM:SS`. Useful for display only; do not parse it for logic. |
| `instance` | integer | The current scenario instance ID. Changes whenever the scenario is reset or restarted. |

The packet is published as plain ASCII JSON — no XOR layer, no Caesar cipher. That makes it trivial for any client to read time without holding any team credentials.

### When the simulation isn't running

If the simulation is paused, stopped, or the scenario hasn't been started, **no packets are published**. The absence of session traffic for more than ~1 second is a reliable signal that the simulation is not currently advancing. (For pause/resume control, see [Admin requests](../api-reference/admin-requests.md).)

---

## Simulation time

Treat simulation time as the canonical clock for everything else in Space Range:

- **Command scheduling** — the `Time` field in spacecraft commands is in simulation seconds. A command with `Time: 60` runs when the session topic publishes `time: 60` (or shortly thereafter, on the next simulation tick).
- **Telemetry timestamps** — Ping packets, Schedule Reports, and other CCSDS Space Packets carry simulation time fields populated from the same clock.
- **Scenario events** — admin-side queries for events return sim-time timestamps.

Simulation time may not run at 1× wall-clock rate. Studio supports running at fractional or accelerated rates for training; clients should always derive elapsed time from session ticks rather than from `time.time()` or the equivalent.

### A simple session listener

```python
import json
import paho.mqtt.client as mqtt

def on_session(client, userdata, msg):
    pkt = json.loads(msg.payload.decode("utf-8"))
    print(f"t={pkt['time']:.2f}s  utc={pkt['utc']}  instance={pkt['instance']}")

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
  console.log(`t=${pkt.time.toFixed(2)}s  utc=${pkt.utc}  instance=${pkt.instance}`);
});
```

---

## Instance ID and resets

The `instance` field is a monotonically-increasing integer that **changes every time the simulation is reset** — whether by an instructor restarting the scenario, by a scenario completion handler, or by Studio being restarted. It is used by clients to detect that everything they cached is now stale.

When you see the instance change, you should:

1. **Drop all cached state.** Any asset IDs, telemetry buffers, scheduled commands, and link-budget snapshots from the previous instance no longer apply. Asset IDs are typically the same across resets within the same scenario, but you should not assume so.
2. **Re-fetch your XTCE schemas.** A scenario may use different Space Packet definitions across resets. See [`get_packet_schemas`](../api-reference/ground-requests.md#get_packet_schemas).
3. **Re-issue any standing telemetry configuration** (e.g. desired [`telemetry`](../api-reference/spacecraft-commands.md#telemetry) settings).
4. **Re-list assets** with [`list_assets`](../api-reference/ground-requests.md#list_assets).

The Operator UI does this automatically. Custom clients should track the last-seen instance ID and trigger a re-sync on change:

```python
last_instance = None

def on_session(client, userdata, msg):
    global last_instance
    pkt = json.loads(msg.payload.decode("utf-8"))
    if pkt["instance"] != last_instance:
        if last_instance is not None:
            print("Scenario reset detected; resyncing.")
            resync()
        last_instance = pkt["instance"]
```

### Time can go backwards

Across an instance change, simulation time typically resets to `0`. **Do not** assume monotonic time across the boundary — always pair `(instance, time)` if you need to compare two timestamps.

---

## Choosing how often to react

Most clients don't need their own ticker; the 3 Hz session feed is the natural "heartbeat" for periodic UI updates. If you want finer time resolution between session ticks, interpolate from the most recent `time` plus elapsed wall-clock seconds, but be careful: simulation time rate is not guaranteed to match wall-clock rate, so any interpolation is an estimate that will resync at the next session tick.

If you want **coarser** updates (e.g. once per simulated minute), you can simply check whether `floor(time / 60)` has changed since the last tick.

---

## Next

- [Encryption](encryption.md) — XOR password and Caesar cipher.
- [Commands and scheduling](commands-and-scheduling.md) — using `Time` to schedule future commands.
- [API Reference → Session stream](../api-reference/session-stream.md) — the wire format reference.
