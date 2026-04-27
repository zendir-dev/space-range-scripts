# Connecting

This page walks through the minimum steps to connect a custom client to a Space Range scenario, confirm the simulation is running, and start receiving traffic for your team. We deliberately keep it small — no commands yet, just enough to prove every layer is wired up correctly.

By the end you will have:

1. Connected to the broker.
2. Subscribed to the **session topic** and seen the simulation clock advance.
3. Subscribed to your team's **downlink** and **response** topics, ready to receive traffic.
4. Verified your **XOR password** by decoding a downlink payload.

For the actual first command, see [Your first command](first-command.md).

---

## Prerequisites

Make sure you have the items listed in [Prerequisites](prerequisites.md):

- Broker host/port (e.g. `mqtt.zendir.io:1883`).
- Game name, e.g. `SPACE RANGE`.
- Team ID and team password.
- A Space Range scenario actually running (no Studio = no traffic, no matter how correctly your client is configured).

The examples below use Python with `paho-mqtt` and JavaScript with `mqtt.js`. Translate freely to your language of choice — every step is just publish/subscribe + JSON.

```bash
# Python
pip install paho-mqtt

# JavaScript (Node)
npm install mqtt
```

---

## Step 1 — Connect to the broker

Just open the connection. No authentication required at the broker level for hosted Space Range:

```python
import paho.mqtt.client as mqtt

BROKER_HOST = "mqtt.zendir.io"
BROKER_PORT = 1883
GAME        = "SPACE RANGE"
TEAM_ID     = 111111
TEAM_PWD    = "AAAAAA"

client = mqtt.Client()
client.connect(BROKER_HOST, BROKER_PORT)
client.loop_start()
print("Connected to broker.")
```

```javascript
import mqtt from "mqtt";

const BROKER  = "mqtt://mqtt.zendir.io:1883";
const GAME    = "SPACE RANGE";
const TEAM_ID = 111111;
const TEAM_PWD = "AAAAAA";

const client = mqtt.connect(BROKER);
client.on("connect", () => console.log("Connected to broker."));
```

If `connect()` raises or never fires `on("connect")`, you have a network or broker problem — see [Troubleshooting](../guides/troubleshooting.md). Until that resolves, no Space Range layer above will work.

---

## Step 2 — Subscribe to the session topic

The simulation clock is published in the clear on:

```text
Zendir/SpaceRange/<GAME>/Session
```

If a scenario is running, you will see one packet every ~0.33 seconds. If you see nothing for more than a couple of seconds, the simulation isn't running (or you have the wrong game name).

```python
import json

SESSION_TOPIC = f"Zendir/SpaceRange/{GAME}/Session"

def on_session(client, userdata, msg):
    pkt = json.loads(msg.payload.decode("utf-8"))
    print(f"t={pkt['time']:.2f}s  utc={pkt['utc']}  instance={pkt['instance']}")

client.message_callback_add(SESSION_TOPIC, on_session)
client.subscribe(SESSION_TOPIC)
```

```javascript
const SESSION_TOPIC = `Zendir/SpaceRange/${GAME}/Session`;

client.subscribe(SESSION_TOPIC);
client.on("message", (topic, payload) => {
  if (topic === SESSION_TOPIC) {
    const pkt = JSON.parse(payload.toString("utf-8"));
    console.log(`t=${pkt.time.toFixed(2)}s  utc=${pkt.utc}  instance=${pkt.instance}`);
  }
});
```

You should see lines like:

```text
t=14.33s  utc=2026/01/26 13:23:13  instance=10234141
t=14.66s  utc=2026/01/26 13:23:13  instance=10234141
t=14.99s  utc=2026/01/26 13:23:13  instance=10234141
```

If you see them, everything below the team layer is fine. **Note the instance ID** — when it changes, the scenario has been reset; see [Concepts → Simulation clock](../concepts/simulation-clock.md#instance-id-and-resets).

---

## Step 3 — Subscribe to your team's topics

Your team has four topics:

```text
Zendir/SpaceRange/<GAME>/<TEAM>/Uplink     ← you publish here (commands)
Zendir/SpaceRange/<GAME>/<TEAM>/Downlink   ← you receive here (telemetry)
Zendir/SpaceRange/<GAME>/<TEAM>/Request    ← you publish here (queries)
Zendir/SpaceRange/<GAME>/<TEAM>/Response   ← you receive here (replies)
```

Subscribe to the two **inbound** topics:

```python
DOWNLINK_TOPIC = f"Zendir/SpaceRange/{GAME}/{TEAM_ID}/Downlink"
RESPONSE_TOPIC = f"Zendir/SpaceRange/{GAME}/{TEAM_ID}/Response"

client.subscribe(DOWNLINK_TOPIC)
client.subscribe(RESPONSE_TOPIC)
```

```javascript
const DOWNLINK_TOPIC = `Zendir/SpaceRange/${GAME}/${TEAM_ID}/Downlink`;
const RESPONSE_TOPIC = `Zendir/SpaceRange/${GAME}/${TEAM_ID}/Response`;

client.subscribe([DOWNLINK_TOPIC, RESPONSE_TOPIC]);
```

These topics carry **XOR-encrypted bytes** — never plain JSON. If you log raw payloads at this point, expect to see binary garbage.

---

## Step 4 — Decrypt incoming traffic with your password

Both `Downlink` and `Response` are encrypted with your team password. The Caesar layer applies *only* inside the Downlink payload (after the 5-byte frame header) — Responses are plain JSON once XOR-decoded.

A reusable XOR helper:

```python
def xor_crypt(password: str, data: bytes) -> bytes:
    key = password.encode("utf-8")
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
```

```javascript
function xorCrypt(password, data) {
  const key = new TextEncoder().encode(password);
  const out = new Uint8Array(data.length);
  for (let i = 0; i < data.length; i++) out[i] = data[i] ^ key[i % key.length];
  return out;
}
```

To prove your password is correct, send a single ground request — `list_assets` is a safe one because it's read-only and always responds:

```python
REQUEST_TOPIC = f"Zendir/SpaceRange/{GAME}/{TEAM_ID}/Request"

def on_response(client, userdata, msg):
    plaintext = xor_crypt(TEAM_PWD, msg.payload).decode("utf-8")
    print("Response:", plaintext)

client.message_callback_add(RESPONSE_TOPIC, on_response)

req = json.dumps({
    "type":   "list_assets",
    "req_id": 1,
    "args":   {},
}).encode("utf-8")

client.publish(REQUEST_TOPIC, xor_crypt(TEAM_PWD, req))
```

```javascript
const REQUEST_TOPIC = `Zendir/SpaceRange/${GAME}/${TEAM_ID}/Request`;

client.on("message", (topic, payload) => {
  if (topic === RESPONSE_TOPIC) {
    const text = new TextDecoder().decode(xorCrypt(TEAM_PWD, payload));
    console.log("Response:", text);
  }
});

const req = new TextEncoder().encode(JSON.stringify({
  type: "list_assets",
  req_id: 1,
  args: {},
}));
client.publish(REQUEST_TOPIC, Buffer.from(xorCrypt(TEAM_PWD, req)));
```

Within ~1 second you should see a response like:

```json
{
  "type": "list_assets",
  "req_id": 1,
  "args": {
    "space": [
      {"asset_id": "A3F2C014", "name": "Microsat", "rpo_enabled": false}
    ]
  }
}
```

That confirms:

- Broker connectivity ✓
- Game name correct ✓
- Team ID correct ✓
- Team password correct ✓
- Studio is running and your team is enabled ✓

If the response is garbled JSON, your password is wrong. If no response arrives within a few seconds, your team ID is wrong, the team is `enabled: false` in the scenario, or the simulation isn't running.

---

## Putting it together

Below is the smallest end-to-end client that connects, prints the session clock, and confirms the team password by listing assets. Use it as a starting point for your own integration.

```python
import json
import paho.mqtt.client as mqtt

BROKER_HOST, BROKER_PORT = "mqtt.zendir.io", 1883
GAME      = "SPACE RANGE"
TEAM_ID   = 111111
TEAM_PWD  = "AAAAAA"

SESSION  = f"Zendir/SpaceRange/{GAME}/Session"
DOWNLINK = f"Zendir/SpaceRange/{GAME}/{TEAM_ID}/Downlink"
REQUEST  = f"Zendir/SpaceRange/{GAME}/{TEAM_ID}/Request"
RESPONSE = f"Zendir/SpaceRange/{GAME}/{TEAM_ID}/Response"

def xor_crypt(password, data):
    key = password.encode("utf-8")
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

def on_session(_c, _u, msg):
    pkt = json.loads(msg.payload.decode("utf-8"))
    print(f"t={pkt['time']:.2f}s  instance={pkt['instance']}")

def on_response(_c, _u, msg):
    print("Response:", xor_crypt(TEAM_PWD, msg.payload).decode("utf-8"))

c = mqtt.Client()
c.connect(BROKER_HOST, BROKER_PORT)
c.message_callback_add(SESSION, on_session)
c.message_callback_add(RESPONSE, on_response)
c.subscribe([(SESSION, 0), (DOWNLINK, 0), (RESPONSE, 0)])

req = json.dumps({"type": "list_assets", "req_id": 1, "args": {}}).encode("utf-8")
c.publish(REQUEST, xor_crypt(TEAM_PWD, req))

c.loop_forever()
```

---

## Common pitfalls

| Symptom | Likely cause |
| --- | --- |
| `on("connect")` never fires, no error | Wrong host or port; firewall blocking outbound 1883. |
| Session topic is silent | No scenario running; wrong game name; off by case. |
| Garbled JSON on Response | Wrong team password. Confirm 6 chars exactly, and that you're using the team password (not the admin password). |
| No Response after a Request | Wrong team ID; team disabled in scenario; broker dropped the publish (check `client.publish()` return). |
| Downlink payloads decode to garbage | Caesar key or frequency mismatch. Telemetry needs both layers; see [Concepts → Telemetry](../concepts/telemetry.md). |
| Everything works once, then stops | Scenario reset (instance ID changed) — re-list assets, re-fetch schemas, re-subscribe is fine since topics don't change across resets. |

A more comprehensive list is in [Troubleshooting & FAQ](../guides/troubleshooting.md).

---

## Next

- [Your first command](first-command.md) — uplink a `guidance` command and confirm execution via Ping.
- [Operator UI quick start](operator-ui.md) — try the bundled web client first if you'd rather see things visually before writing code.
- [Concepts → Encryption](../concepts/encryption.md) — full algorithm reference for both layers.
