# Encryption

Space Range applies **two layers of encryption** to most of the traffic on the broker. The two layers solve different problems and operate independently:

| Layer | Cipher | Where applied | Key |
| --- | --- | --- | --- |
| **Transport** | XOR (cyclic) | All team and admin MQTT payloads | Team password (or admin password), 6-character alphanumeric |
| **RF** | Caesar (additive mod-256) | Telemetry packets *inside* downlink payloads | Numeric Caesar key, 0–255, per team |

This page describes each layer, why both exist, what is and isn't encrypted, and how to implement them in client code.

> **Threat model.** Space Range encryption is designed to **segregate teams** during exercises and to model the operational burden of managing encryption keys. It is **not** intended as production-grade cryptography. The XOR layer is trivially breakable given any known-plaintext, and the Caesar layer offers ~8 bits of secrecy. Treat both as in-game obfuscation, not security.

---

## The XOR transport layer

### What it protects

Every JSON payload published on a team's `Uplink`, `Downlink`, `Request`, or `Response` topic is XOR-encrypted with the team's **password**. The same applies to admin payloads on `Admin/Request` and `Admin/Response` using the **admin password**.

The **session topic** is *not* encrypted — it carries no team-specific information.

### How it works

The cipher is byte-cyclic XOR:

1. Encode the password as UTF-8 bytes.
2. For each byte of the plaintext at index `i`, XOR it with the password byte at `i mod len(password)`.
3. Output the result.

Because XOR is involutive, **encryption and decryption are the same operation** with the same key. There is no IV, no padding, and no length prefix — the ciphertext has exactly the same length as the plaintext.

In pseudocode:

```text
encrypt(key, data):
    key_bytes = utf8(key)
    for i in 0 .. len(data) - 1:
        out[i] = data[i] XOR key_bytes[i mod len(key_bytes)]
    return out

decrypt(key, data) = encrypt(key, data)
```

### Implementation

**Python:**

```python
def xor_crypt(password: str, data: bytes) -> bytes:
    key = password.encode("utf-8")
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
```

**JavaScript (browser or Node):**

```javascript
function xorCrypt(password, data) {
  const key = new TextEncoder().encode(password);
  const out = new Uint8Array(data.length);
  for (let i = 0; i < data.length; i++) {
    out[i] = data[i] ^ key[i % key.length];
  }
  return out;
}
```

The same function encrypts when given plaintext and decrypts when given ciphertext.

### Pitfalls

- **Empty payloads** are returned unchanged in the C++ reference. Don't try to publish an empty body — it carries no information either way.
- **Wrong password** produces garbage that JSON parsing will reject. Treat parse failures as a sign you're using the wrong password (or the wrong topic).
- **Extra whitespace in the password** counts. Passwords are exactly 6 alphanumeric characters; do not pad.

---

## The Caesar RF layer

### What it protects

Telemetry packets that travel over the simulated RF link are **additionally** Caesar-encoded *before* they are XOR-wrapped for MQTT. Inside a team's `Downlink` topic payload, the bytes you recover after XOR-decryption are still Caesar-shifted; you must apply the inverse Caesar shift to get the actual CCSDS Space Packet.

This layer models the burden of managing radio encryption keys in real spacecraft operations and supports the **encryption rotation** mechanic (see below).

### How it works

The cipher is a per-byte additive shift modulo 256:

- **Encrypt:** `c[i] = (p[i] + key) mod 256`
- **Decrypt:** `p[i] = (c[i] - key) mod 256`

`key` is an integer 0–255. `key = 0` means no shift.

### Implementation

**Python:**

```python
def caesar_decrypt(key: int, data: bytes) -> bytes:
    return bytes((b - key) % 256 for b in data)

def caesar_encrypt(key: int, data: bytes) -> bytes:
    return bytes((b + key) % 256 for b in data)
```

**JavaScript:**

```javascript
function caesarDecrypt(key, data) {
  const out = new Uint8Array(data.length);
  for (let i = 0; i < data.length; i++) out[i] = (data[i] - key) & 0xff;
  return out;
}
function caesarEncrypt(key, data) {
  const out = new Uint8Array(data.length);
  for (let i = 0; i < data.length; i++) out[i] = (data[i] + key) & 0xff;
  return out;
}
```

---

## Putting both layers together

### Decoding a downlink

Given a payload received on `Zendir/SpaceRange/<GAME>/<TEAM>/Downlink`:

```python
encrypted_bytes = msg.payload                     # raw MQTT payload
xor_decoded     = xor_crypt(team.password, encrypted_bytes)  # peel XOR layer

frame_format    = xor_decoded[0]                  # see "downlink frame format" below
team_id         = int.from_bytes(xor_decoded[1:5], "little")
caesar_payload  = xor_decoded[5:]                 # CCSDS Space Packet (Caesar-encoded)

space_packet    = caesar_decrypt(team.key, caesar_payload)
# → parse with the team's XTCE schema
```

### Encoding an uplink

Uplinks do **not** use the Caesar layer. The plaintext is just the JSON command:

```python
plaintext  = json.dumps(command).encode("utf-8")
ciphertext = xor_crypt(team.password, plaintext)
client.publish(f"Zendir/SpaceRange/{game}/{team.id}/Uplink", ciphertext)
```

The asymmetry exists because the RF model only fires on downlink (telemetry from spacecraft → ground). Uplink commands are delivered to Studio "out-of-band" by the simulation and only need the transport layer.

### Downlink frame format

The 5-byte header that precedes every downlink payload (after XOR decoding) is:

| Byte(s) | Field | Description |
| --- | --- | --- |
| 0 | `Format` | `EDataFormatType` enum: `0` = None, `1` = Message, `2` = Media, `3` = Uplink Intercept. |
| 1–4 | `Team ID` | Little-endian 32-bit integer. The team that owns the spacecraft that emitted this packet. |
| 5+ | `Payload` | The Caesar-encoded payload, format depending on `Format`. |

For `Format = Message`, the payload is a CCSDS Space Packet. For `Format = Media`, the payload starts with a 50-byte name header followed by the file bytes. For `Format = Uplink Intercept`, the payload is the [Uplink Intercept record](../reference/packet-formats.md#uplink-intercept).

The full frame layout is documented in [Reference → Packet formats](../reference/packet-formats.md).

---

## Key rotation

The team password is **fixed** for a scenario — there is no API to change it at runtime, and there is no automatic rotation.

The Caesar key and the team's downlink frequency, however, **can be rotated** at runtime by uplinking the [`encryption`](../api-reference/spacecraft-commands.md#encryption) command. Rotating happens in three phases:

1. The operator uplinks `encryption` with new `key` and `frequency` values.
2. The spacecraft validates the password (which must match the team ID — see the command reference) and updates its outgoing transmitter accordingly.
3. The spacecraft **shuts down briefly** (a reset interval) and reboots with the new RF settings. Telemetry pauses during the shutdown.

The team must also update its **ground-side** view of `(key, frequency)` so it can decode the new downlinks. There are two ways to do that:

- Use [`set_telemetry`](../api-reference/ground-requests.md#set_telemetry) on the ground controller to apply the new key/frequency on the receive side.
- Or query [`get_telemetry`](../api-reference/ground-requests.md#get_telemetry) to read the current values and confirm the rotation took effect.

If the spacecraft and ground go out of sync — different keys, or different frequencies — telemetry decoding will produce garbage, the link budget may report no link, and the team is effectively locked out of its own spacecraft until the keys are reconciled.

A walkthrough of a clean rotation is in [Guides → Encryption walkthrough](../guides/encryption-walkthrough.md).

---

## What is *not* encrypted

For completeness, here is what travels in the clear:

- The **session topic** (`<GAME>/Session`) — simulation time, UTC, instance ID.
- **MQTT topic strings themselves** — anyone watching the broker can see which teams are active and how often each is publishing. Topic-level metadata is part of the threat model.
- **Message timing** — even with valid encryption, the timing of publishes leaks information (e.g., "the red team just sent a command").

If you are integrating Space Range into a setting where these leaks matter, place the broker behind an authenticated TLS endpoint and rely on broker-level access control as well as the in-game cryptography.

---

## Next

- [Commands and scheduling](commands-and-scheduling.md) — how to actually use these encrypted channels.
- [Telemetry](telemetry.md) — what comes back over the encrypted RF layer.
- [Guides → Encryption walkthrough](../guides/encryption-walkthrough.md) — runnable Python and JavaScript examples for both layers.
