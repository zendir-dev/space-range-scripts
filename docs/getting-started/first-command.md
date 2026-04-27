# Your First Command

This page builds on [Connecting](connecting.md) — once you can read the session clock and round-trip a ground request, you're ready to actually drive a spacecraft.

We will:

1. Resolve a live spacecraft asset ID via `list_assets`.
2. Uplink a single `guidance` command to point the spacecraft at the Sun.
3. Confirm execution by watching for the matching entry in the next Ping.

The full code listing at the bottom is around 80 lines of Python, with a JavaScript equivalent.

---

## Step 1 — Resolve your asset ID

Asset IDs are 8-character hex strings assigned by Studio at scenario load. Fetch them dynamically rather than hard-coding:

```python
def list_assets(client):
    pending = {}

    def on_resp(_c, _u, msg):
        body = json.loads(xor_crypt(TEAM_PWD, msg.payload).decode("utf-8"))
        if body.get("type") == "list_assets":
            pending["space"] = body["args"]["space"]

    client.message_callback_add(RESPONSE, on_resp)
    client.publish(REQUEST, xor_crypt(TEAM_PWD, json.dumps({
        "type": "list_assets", "req_id": 1, "args": {}
    }).encode("utf-8")))

    # Spin until response arrives or timeout
    for _ in range(50):
        if "space" in pending:
            return pending["space"]
        time.sleep(0.1)
    raise TimeoutError("list_assets timed out")

assets = list_assets(client)
asset_id = assets[0]["asset_id"]
print(f"Targeting asset {asset_id} ({assets[0]['name']}).")
```

```javascript
async function listAssets() {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("timeout")), 5000);
    const handler = (topic, payload) => {
      if (topic !== RESPONSE_TOPIC) return;
      const body = JSON.parse(new TextDecoder().decode(xorCrypt(TEAM_PWD, payload)));
      if (body.type === "list_assets") {
        clearTimeout(timer);
        client.off("message", handler);
        resolve(body.args.space);
      }
    };
    client.on("message", handler);
    const req = new TextEncoder().encode(JSON.stringify({
      type: "list_assets", req_id: 1, args: {},
    }));
    client.publish(REQUEST_TOPIC, Buffer.from(xorCrypt(TEAM_PWD, req)));
  });
}

const assets = await listAssets();
const assetId = assets[0].asset_id;
console.log(`Targeting asset ${assetId} (${assets[0].name}).`);
```

> **Tip.** `list_assets` is also a good reachability check during normal operation. If it stops responding, the simulation has paused or your credentials have changed.

---

## Step 2 — Build and uplink a `guidance` command

The command envelope is the same for every command type:

```json
{
  "Asset":   "<your asset id>",
  "Command": "guidance",
  "Time":    0,
  "Args": {
    "pointing":  "sun",
    "alignment": "+z",
    "target":    "Solar Panel"
  }
}
```

`Time: 0` means "execute as soon as possible". The `Args` for `guidance` are documented in [API Reference → Spacecraft commands → guidance](../api-reference/spacecraft-commands.md#guidance); for now, this combination tells ADCS to align the `+z` face of the spacecraft's `Solar Panel` component with the Sun.

XOR-encrypt the JSON and publish on the `Uplink` topic:

```python
UPLINK = f"Zendir/SpaceRange/{GAME}/{TEAM_ID}/Uplink"

cmd = {
    "Asset":   asset_id,
    "Command": "guidance",
    "Time":    0,
    "Args": {
        "pointing":  "sun",
        "alignment": "+z",
        "target":    "Solar Panel",
    },
}

payload = xor_crypt(TEAM_PWD, json.dumps(cmd).encode("utf-8"))
client.publish(UPLINK, payload)
print("Uplinked guidance command.")
```

```javascript
const UPLINK_TOPIC = `Zendir/SpaceRange/${GAME}/${TEAM_ID}/Uplink`;

const cmd = {
  Asset:   assetId,
  Command: "guidance",
  Time:    0,
  Args: {
    pointing:  "sun",
    alignment: "+z",
    target:    "Solar Panel",
  },
};

const payload = Buffer.from(xorCrypt(TEAM_PWD,
  new TextEncoder().encode(JSON.stringify(cmd))));
client.publish(UPLINK_TOPIC, payload);
console.log("Uplinked guidance command.");
```

You will *not* receive a direct response on the `Response` topic — uplink commands are reported via telemetry, not via the request/response channel. (See [Concepts → Commands and scheduling → Reporting](../concepts/commands-and-scheduling.md#6-reporting).)

---

## Step 3 — Confirm execution via Ping

The spacecraft emits **Ping** telemetry on a periodic cadence (and on demand). Each Ping includes a `Commands` field listing commands executed since the previous Ping. Watch for an entry matching your `Command` and `Time`.

For this minimal example we'll skip XTCE-aware parsing and just look at the **decoded payload bytes** for the substring `"guidance"` after both decryption layers. That's enough to confirm round-trip; full structured parsing is in [Guides → Decoding telemetry](../guides/decoding-telemetry.md).

```python
TEAM_KEY = 6   # the team's Caesar key, from scenario config

def caesar_decrypt(key, data):
    return bytes((b - key) % 256 for b in data)

def on_downlink(_c, _u, msg):
    xor_decoded = xor_crypt(TEAM_PWD, msg.payload)
    if len(xor_decoded) < 5:
        return
    fmt = xor_decoded[0]               # 1 = Message, 2 = Media, 3 = UplinkIntercept
    payload = caesar_decrypt(TEAM_KEY, xor_decoded[5:])
    if fmt == 1 and b"guidance" in payload:
        print("Saw guidance entry in Ping payload — command executed.")
        # In a real client, parse the Space Packet and read the JSON Commands field.

client.message_callback_add(DOWNLINK, on_downlink)
```

```javascript
const TEAM_KEY = 6;

function caesarDecrypt(key, data) {
  const out = new Uint8Array(data.length);
  for (let i = 0; i < data.length; i++) out[i] = (data[i] - key) & 0xff;
  return out;
}

client.on("message", (topic, payload) => {
  if (topic !== DOWNLINK_TOPIC) return;
  const xorDecoded = xorCrypt(TEAM_PWD, payload);
  if (xorDecoded.length < 5) return;
  const fmt = xorDecoded[0];
  const body = caesarDecrypt(TEAM_KEY, xorDecoded.slice(5));
  if (fmt === 1 && Buffer.from(body).includes("guidance")) {
    console.log("Saw guidance entry in Ping payload — command executed.");
  }
});
```

If you don't see a Ping within ~30 seconds, force one by uplinking a `downlink` command with `ping: true`:

```python
ping_cmd = {
    "Asset": asset_id,
    "Command": "downlink",
    "Time": 0,
    "Args": {"downlink": True, "ping": True},
}
client.publish(UPLINK,
    xor_crypt(TEAM_PWD, json.dumps(ping_cmd).encode("utf-8")))
```

When the Ping arrives and the substring shows up, you've completed a full round trip:

- Issued a command from the client.
- Studio decrypted, validated, scheduled, and executed it.
- The spacecraft reported the executed command in telemetry.
- Your client decrypted both layers and read the result.

---

## Full Python listing

```python
import json
import time
import paho.mqtt.client as mqtt

BROKER_HOST, BROKER_PORT = "mqtt.zendir.io", 1883
GAME      = "SPACE RANGE"
TEAM_ID   = 111111
TEAM_PWD  = "AAAAAA"
TEAM_KEY  = 6

SESSION  = f"Zendir/SpaceRange/{GAME}/Session"
UPLINK   = f"Zendir/SpaceRange/{GAME}/{TEAM_ID}/Uplink"
DOWNLINK = f"Zendir/SpaceRange/{GAME}/{TEAM_ID}/Downlink"
REQUEST  = f"Zendir/SpaceRange/{GAME}/{TEAM_ID}/Request"
RESPONSE = f"Zendir/SpaceRange/{GAME}/{TEAM_ID}/Response"

def xor_crypt(password, data):
    key = password.encode("utf-8")
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

def caesar_decrypt(key, data):
    return bytes((b - key) % 256 for b in data)

pending_response = {}

def on_response(_c, _u, msg):
    body = json.loads(xor_crypt(TEAM_PWD, msg.payload).decode("utf-8"))
    pending_response[body.get("type")] = body

def on_downlink(_c, _u, msg):
    decoded = xor_crypt(TEAM_PWD, msg.payload)
    if len(decoded) < 5:
        return
    fmt = decoded[0]
    body = caesar_decrypt(TEAM_KEY, decoded[5:])
    if fmt == 1 and b"guidance" in body:
        print(">>> Saw guidance entry in Ping payload.")

c = mqtt.Client()
c.message_callback_add(RESPONSE, on_response)
c.message_callback_add(DOWNLINK, on_downlink)
c.connect(BROKER_HOST, BROKER_PORT)
c.subscribe([(DOWNLINK, 0), (RESPONSE, 0)])
c.loop_start()

c.publish(REQUEST, xor_crypt(TEAM_PWD,
    json.dumps({"type": "list_assets", "req_id": 1, "args": {}}).encode("utf-8")))

for _ in range(50):
    if "list_assets" in pending_response:
        break
    time.sleep(0.1)

asset_id = pending_response["list_assets"]["args"]["space"][0]["asset_id"]
print(f"Targeting {asset_id}.")

c.publish(UPLINK, xor_crypt(TEAM_PWD, json.dumps({
    "Asset": asset_id, "Command": "guidance", "Time": 0,
    "Args": {"pointing": "sun", "alignment": "+z", "target": "Solar Panel"},
}).encode("utf-8")))

c.publish(UPLINK, xor_crypt(TEAM_PWD, json.dumps({
    "Asset": asset_id, "Command": "downlink", "Time": 0,
    "Args": {"downlink": True, "ping": True},
}).encode("utf-8")))

print("Watching for confirmation; Ctrl+C to stop.")
c.loop_forever()
```

---

## Where to go next

You now have the full pattern any client follows: connect → resolve assets → build envelope → encrypt → publish → watch telemetry. To go further:

- **More commands:** [API Reference → Spacecraft commands](../api-reference/spacecraft-commands.md) covers every command type and its `Args`.
- **Structured telemetry:** [Guides → Decoding telemetry](../guides/decoding-telemetry.md) shows how to parse Space Packets via XTCE so you can pull out individual fields rather than substring-matching.
- **Scheduling and editing the queue:** [Concepts → Commands and scheduling](../concepts/commands-and-scheduling.md) for `Time > 0`, `get_schedule`, `remove_command`, and `update_command`.
- **Don't want to write a client?** Use the bundled [Operator UI](operator-ui.md) instead.
