# Encryption Walkthrough

This guide walks through Space Range's two encryption layers in code, end-to-end. By the end you will have:

- A working pair of `encrypt`/`decrypt` helpers in Python and JavaScript.
- A round-trip test that proves your implementation is byte-identical with Studio's.
- A complete teardown of one real downlink frame from raw bytes to a parsed CCSDS Space Packet.
- A worked example of rotating the team's Caesar key + frequency at runtime without losing the link.

For background on **why** there are two layers and what each protects, read [Concepts → Encryption](../concepts/encryption.md) first.

---

## Layer recap

| Layer | Cipher | Key | Where applied |
| --- | --- | --- | --- |
| Transport (MQTT) | XOR (cyclic) | Team password (or admin password) | Every payload on `Uplink`, `Downlink`, `Request`, `Response`, `Admin/*` |
| RF (telemetry) | Caesar (additive mod 256) | Team Caesar key (`0–255`) | Inside the `Downlink` payload, after the 5-byte frame header |

Memorise this rule and you'll never get confused about which layer applies where:

- **Uplink, Request, Response, Admin/Request, Admin/Response** → XOR only.
- **Downlink** → XOR on the outside, Caesar on the inside (around the CCSDS payload).
- **Session** → no encryption.

---

## Reference implementations

### Python

```python
def xor_crypt(password: str, data: bytes) -> bytes:
    """Encrypts AND decrypts (XOR is involutive)."""
    if not data:
        return data
    key = password.encode("utf-8")
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def caesar_encrypt(key: int, data: bytes) -> bytes:
    return bytes((b + key) & 0xFF for b in data)


def caesar_decrypt(key: int, data: bytes) -> bytes:
    return bytes((b - key) & 0xFF for b in data)
```

### JavaScript / TypeScript

```javascript
function xorCrypt(password, data) {
  if (!data?.length) return data;
  const key = new TextEncoder().encode(password);
  const out = new Uint8Array(data.length);
  for (let i = 0; i < data.length; i++) {
    out[i] = data[i] ^ key[i % key.length];
  }
  return out;
}

function caesarEncrypt(key, data) {
  const out = new Uint8Array(data.length);
  for (let i = 0; i < data.length; i++) out[i] = (data[i] + key) & 0xff;
  return out;
}

function caesarDecrypt(key, data) {
  const out = new Uint8Array(data.length);
  for (let i = 0; i < data.length; i++) out[i] = (data[i] - key) & 0xff;
  return out;
}
```

A few small things that catch people out:

- The XOR password is **UTF-8 encoded**. In practice it's always 6 alphanumeric ASCII characters, so this rarely matters — but if you ever feed it a non-ASCII password, encode as UTF-8 (not Latin-1 or UTF-16).
- The Caesar key is an **integer in [0, 255]**. Negative values and values ≥ 256 are not legal; use `& 0xFF` to be defensive in case a 16-bit integer slips through.
- Both ciphers are **length-preserving**. There is no IV, no padding, and no length prefix. If your output length differs from the input, something is wrong.
- An **empty payload** is returned unchanged by Studio. Don't `xor_crypt("PASSWD", b"")` and expect anything other than `b""`.

---

## Round-trip self-test

Before you use these functions in anger, prove they're symmetric:

### Python

```python
import json

password = "AB12CD"   # team password
caesar_key = 17       # team Caesar key

cmd = {
    "Asset":   "A3F2C014",
    "Command": "guidance",
    "Time":    0,
    "Args":    {"pointing": "sun", "target": "Solar Panel", "alignment": "+z"},
}
plaintext = json.dumps(cmd, separators=(",", ":")).encode("utf-8")

ciphertext  = xor_crypt(password, plaintext)
recovered   = xor_crypt(password, ciphertext)
assert recovered == plaintext, "XOR layer failed self-test"

caesar_ct  = caesar_encrypt(caesar_key, plaintext)
caesar_pt  = caesar_decrypt(caesar_key, caesar_ct)
assert caesar_pt == plaintext, "Caesar layer failed self-test"
print("OK")
```

### JavaScript

```javascript
const password = "AB12CD";
const caesarKey = 17;

const cmd = {
  Asset: "A3F2C014", Command: "guidance", Time: 0,
  Args: { pointing: "sun", target: "Solar Panel", alignment: "+z" },
};
const plaintext = new TextEncoder().encode(JSON.stringify(cmd));

const ciphertext = xorCrypt(password, plaintext);
const recovered  = xorCrypt(password, ciphertext);
console.assert(plaintext.every((b, i) => b === recovered[i]), "XOR self-test failed");

const caesarCt = caesarEncrypt(caesarKey, plaintext);
const caesarPt = caesarDecrypt(caesarKey, caesarCt);
console.assert(plaintext.every((b, i) => b === caesarPt[i]), "Caesar self-test failed");
console.log("OK");
```

If either assertion fails, you have a bug — fix it before continuing.

---

## End-to-end: decoding one downlink frame

Suppose you've subscribed to:

```text
Zendir/SpaceRange/SPACE RANGE/111111/Downlink
```

with the team password `"AB12CD"` and Caesar key `17`. You receive a 312-byte payload. Here is what the layers look like, in order, as you peel them.

### Step 1 — XOR-decrypt with the team password

```python
xor_decoded = xor_crypt("AB12CD", msg.payload)
# len(xor_decoded) == 312
```

After this the bytes are still a black box, but they're **layered** correctly.

### Step 2 — Read the 5-byte frame header

```python
fmt     = xor_decoded[0]                                   # 1 = Message
team_id = int.from_bytes(xor_decoded[1:5], "little")       # e.g. 111111
body    = xor_decoded[5:]                                  # the Caesar-encoded body
```

The format byte tells you what's inside:

- `0` (None) — empty frame, ignore.
- `1` (Message) — CCSDS Space Packet (Ping or Schedule Report).
- `2` (Media) — file payload (image with 50-byte name header).
- `3` (Uplink Intercept) — captured uplink (32-byte header + raw on-air bytes).

### Step 3 — Caesar-decrypt the body

```python
inner = caesar_decrypt(17, body)
```

`inner` is now the actual Space Packet (or media file, or intercept record).

### Step 4 — Parse according to the format

For `fmt = 1`, parse `inner` as a CCSDS Space Packet using your XTCE schema. See [Decoding telemetry](decoding-telemetry.md) for the full walkthrough and code.

### Putting it all together

```python
import json
import paho.mqtt.client as mqtt

GAME = "SPACE RANGE"
TEAM_ID = 111111
PASSWORD = "AB12CD"
CAESAR_KEY = 17

def on_message(client, userdata, msg):
    xor_decoded = xor_crypt(PASSWORD, msg.payload)
    if len(xor_decoded) < 5:
        return

    fmt = xor_decoded[0]
    team_id = int.from_bytes(xor_decoded[1:5], "little")
    body = caesar_decrypt(CAESAR_KEY, xor_decoded[5:])

    if team_id != TEAM_ID:
        # Cross-wire — somebody else's data, ignore.
        return

    if fmt == 1:
        handle_space_packet(body)
    elif fmt == 2:
        handle_media(body)
    elif fmt == 3:
        handle_uplink_intercept(body)
    # fmt == 0: ignore

client = mqtt.Client()
client.on_message = on_message
client.connect("broker.local", 1883)
client.subscribe(f"Zendir/SpaceRange/{GAME}/{TEAM_ID}/Downlink")
client.loop_forever()
```

---

## Encoding an uplink command

Uplinks are the easy direction — there's no Caesar layer, just XOR on top of JSON:

### Python

```python
def send_uplink(client, password, game, team_id, command):
    payload = json.dumps(command, separators=(",", ":")).encode("utf-8")
    encrypted = xor_crypt(password, payload)
    topic = f"Zendir/SpaceRange/{game}/{team_id}/Uplink"
    client.publish(topic, encrypted)

send_uplink(client, "AB12CD", "SPACE RANGE", 111111, {
    "Asset":   "A3F2C014",
    "Command": "guidance",
    "Time":    0,
    "Args":    {"pointing": "sun", "target": "Solar Panel", "alignment": "+z"},
})
```

### JavaScript

```javascript
function sendUplink(client, password, game, teamId, command) {
  const payload = new TextEncoder().encode(JSON.stringify(command));
  const encrypted = xorCrypt(password, payload);
  client.publish(`Zendir/SpaceRange/${game}/${teamId}/Uplink`, encrypted);
}
```

The same pattern applies to `Request` and `Admin/Request` — XOR with the appropriate password, publish, done.

---

## Rotating the Caesar key (and frequency) safely

The Caesar key and frequency can be rotated at runtime via the [`encryption`](../api-reference/spacecraft-commands.md#encryption) command. Done badly, this locks you out of your own spacecraft. Done in this order, it's robust:

### Phase 1 — Pre-flight check

Confirm you're connected and seeing telemetry. Don't rotate while you're already missing Pings, or you won't be able to tell whether the rotation worked.

```python
state = ground.request("get_telemetry", {"asset_id": ASSET})
print(state)  # frequency, key, link budgets — both ends should agree
```

### Phase 2 — Pick new values

- **New frequency** distinct from every other team's. Check `admin_list_entities` (or compare with teammates) to avoid collisions.
- **New key** in `[0, 255]`. Anything goes; `0` is legal but obviously the trivial cipher.

### Phase 3 — Uplink the rotation command

```python
new_freq = 478.0
new_key  = 233

send_uplink(client, PASSWORD, GAME, TEAM_ID, {
    "Asset":   ASSET,
    "Command": "encryption",
    "Time":    0,
    "Args":    {
        "password":  PASSWORD,   # required credential
        "frequency": new_freq,
        "key":       new_key,
    },
})
```

The `password` argument **must** be your current team password. Studio uses it to authenticate the rotation — without it the command is silently rejected (the spacecraft's view is "if you knew my password you'd already be on this channel").

### Phase 4 — Update your client immediately

After the rotation has been *uplinked*, the spacecraft will (a) ack the command on the next Ping, then (b) reboot and come up on the new key/frequency.

Your client must switch to the new Caesar key **before** the next Ping arrives, otherwise the Ping will look like garbage. The simplest pattern:

```python
# Before sending the uplink:
old_key = CAESAR_KEY
new_key = 233

send_uplink(...)

# Optimistically switch local state:
CAESAR_KEY = new_key
```

If the spacecraft never receives the rotation (jammed / out of view), the spacecraft stays on `old_key` and your client now can't decode anything. This is the failure mode you mainly need to plan for; see "Recovering from a desync" below.

### Phase 5 — Tell the ground side too

The spacecraft's RF transmitter is now on `(new_freq, new_key)`. Your **ground station receiver** also needs to be told. Use `set_telemetry`:

```python
ground.request("set_telemetry", {
    "frequency": new_freq,
    "key":       new_key,
})
```

After this, both spacecraft and ground are in sync, and downlinks resume.

### Recovering from a desync

If, after a rotation, you stop receiving Pings, the most likely causes — in order — are:

1. **Spacecraft is rebooting.** Wait one reset interval (typically ~60 sim s). The next Ping should report `State: REBOOTING` and then return to nominal.
2. **Ground side wasn't updated.** Re-run `set_telemetry` with the new values.
3. **Rotation never reached the spacecraft.** The spacecraft is still on the *old* key. Switch your client back to the old key, confirm Pings resume, then retry the rotation.
4. **Frequency clashes with a jammer or another team.** Pick a new frequency and rotate again.

Always preserve your old `(key, frequency)` until you've confirmed the new ones work end-to-end.

---

## What is *not* protected

To set expectations, the encryption layers are **operational**, not cryptographic:

- The XOR layer fails to a known-plaintext attack. Anyone who sees an encrypted payload **and** can guess the JSON structure (which is documented here in full) can recover the password byte-by-byte.
- The Caesar layer offers ~8 bits of secrecy. Brute force is trivial.
- Topic strings, message timing, and message lengths are all visible to anyone watching the broker. Even if your encryption was unbreakable, an observer could still tell that the red team just published 312 bytes on its `Uplink`.

For exercises, this is by design — Space Range is a training tool, not a production C2 system. For deployments where these leaks matter, put the broker behind authenticated TLS and rely on broker-level access control as the real security boundary.

---

## Next

- [Decoding telemetry](decoding-telemetry.md) — once you've peeled the encryption layers, decode the Space Packet inside.
- [Spacecraft commands](../api-reference/spacecraft-commands.md) — what to send up the channel you can now encrypt.
- [Concepts → Encryption](../concepts/encryption.md) — the conceptual treatment if you want to skim before reading code.
