# Decoding Telemetry

Every byte your client receives on `Downlink` is wrapped in three layers: an MQTT XOR cipher, a 5-byte frame header, and a Caesar-encoded payload (the actual data). This guide takes you all the way from a raw MQTT message to a typed Python/JavaScript object you can plot, log, or feed into the rest of your stack.

You should already be comfortable with [Encryption walkthrough](encryption-walkthrough.md). The XOR/Caesar helpers from that guide are reused throughout.

---

## What you can decode

| Format byte | Payload | What it carries |
| --- | --- | --- |
| `0` (`None`) | empty | Heartbeat / sentinel. Ignore. |
| `1` (`Message`) | CCSDS Space Packet | **Ping** (periodic spacecraft status) and **Schedule Report** (queued commands), described by the team's XTCE schemas. |
| `2` (`Media`) | 50-byte name + file bytes | Imagery and other binary payloads. |
| `3` (`Uplink Intercept`) | 32-byte header + raw RF bytes | Frames captured off the air, used for SIGINT exercises. |

Each section below decodes one of these formats end-to-end.

---

## The unified entry point

Every downlink starts the same way. Wrap this in your MQTT message handler:

### Python

```python
def handle_downlink(payload: bytes, team_password: str, caesar_key: int):
    if not payload:
        return None

    decrypted = xor_crypt(team_password, payload)
    if len(decrypted) < 5:
        return None

    fmt     = decrypted[0]
    team_id = int.from_bytes(decrypted[1:5], "little")
    body    = caesar_decrypt(caesar_key, decrypted[5:])

    return {"format": fmt, "team_id": team_id, "body": body}
```

### JavaScript

```javascript
function handleDownlink(payload, teamPassword, caesarKey) {
  if (!payload?.length) return null;
  const decrypted = xorCrypt(teamPassword, payload);
  if (decrypted.length < 5) return null;

  const fmt = decrypted[0];
  const teamId =
    decrypted[1] | (decrypted[2] << 8) | (decrypted[3] << 16) | (decrypted[4] << 24);
  const body = caesarDecrypt(caesarKey, decrypted.slice(5));
  return { format: fmt, teamId, body };
}
```

After this, dispatch on `format`. Everything below works on the `body` bytes.

---

## Format `1` — CCSDS Space Packet (Ping & Schedule Report)

The body is a single **CCSDS Space Packet** per CCSDS 133.0-B-2:

```text
+-----------------------+-----------------------+--------------------+
|  Primary Header (6B)  | Secondary Header (NB) | Data Field (M B)   |
+-----------------------+-----------------------+--------------------+
```

You can parse it three ways:

1. **By hand** using the XTCE schema fetched from [`get_packet_schemas`](../api-reference/ground-requests.md#get_packet_schemas).
2. **With a CCSDS / XTCE library** (`ccsdspy`, `space-packet-parser`, etc.).
3. **Using the bundled XTCE-aware parser** in `space-range-scripts`.

For most users, #3 is the right choice while learning, then #1 or #2 if you build a custom client.

### The Primary Header (6 bytes, big-endian)

| Bits | Field | Meaning |
| --- | --- | --- |
| 0–2 | Version | Always `0`. |
| 3 | Type | `0` = telemetry (downlink), `1` = telecommand. |
| 4 | Sec hdr flag | `1` if a Secondary Header is present. |
| 5–15 | **APID** | Application Process Identifier. Identifies the message type. |
| 16–17 | Seq flags | `11` (`0b11`) for unsegmented. |
| 18–31 | Seq count | Wraparound counter. |
| 32–47 | **Data length** | Bytes in (Secondary Header + Data Field) **minus 1**. |

The two fields you really care about are **APID** and **Data length**.

Decoding the APID in Python:

```python
def parse_primary_header(buf: bytes):
    if len(buf) < 6:
        raise ValueError("Buffer too short for CCSDS primary header")
    word0  = int.from_bytes(buf[0:2], "big")
    word1  = int.from_bytes(buf[2:4], "big")
    word2  = int.from_bytes(buf[4:6], "big")
    apid       = word0 & 0x07FF
    sec_hdr    = (word0 >> 11) & 0x1
    pkt_type   = (word0 >> 12) & 0x1
    seq_count  = word1 & 0x3FFF
    data_len   = word2 + 1   # CCSDS stores length-1
    return {
        "apid": apid, "sec_hdr": sec_hdr, "type": pkt_type,
        "seq_count": seq_count, "data_len": data_len,
    }
```

### Routing by APID

The team's XTCE schemas assign each packet type a specific APID. The Studio defaults are organised by category (numbers may vary if the scenario customises them):

| Range | Category | Examples |
| --- | --- | --- |
| 100–199 | System | Ping, Schedule Report |
| 200–299 | Power System | Battery, Power Source, Power Node |
| 300–399 | Sensors | Magnetometer, GPS, EM Sensor, CCD, Gyroscope |
| 400–499 | ADCS | Computer, Reaction Wheels, Dynamics, Thruster, Formation Flying |
| 500–599 | Telemetry / Comms | Receiver, Transmitter, Jammer, Storage |

Always treat the APID-to-message mapping as **dynamic** and re-derive it from the XTCE schemas each scenario load (the `instance` field changes when the scenario resets — re-fetch then).

### Loading XTCE schemas

```python
schemas_xml = ground.request("get_packet_schemas")["args"]["telemetry"]  # list[str]
# Each entry is a complete XTCE document. Save to disk or feed to your XTCE parser.
```

### The Ping payload

Ping (one of the system-category APIDs) is the workhorse telemetry message. After parsing the primary header, the data field contains:

| Field | Type | Meaning |
| --- | --- | --- |
| `State` | string (enum) | `NOMINAL`, `LOW`, `SAFE`, `TRANSMIT`, `FULL STORAGE`, `REBOOTING`. |
| `Station` | string | Nearest ground station, or `None`. |
| `Memory` | float (`0–1`) | Storage fill fraction. |
| `Battery` | float (`0–1`) | Battery charge fraction. |
| `Commands` | string (JSON) | JSON array of recently-executed commands. |
| `UplinkInterceptDataBytes` | int | Bytes of intercepted uplinks waiting in the on-board ring buffer. |

**The `Commands` field is a JSON-encoded *string*, not a JSON array.** This is intentional — XTCE wants fixed-shape fields and the executed command list is variable-size. Always remember to:

```python
ping["Commands"] = json.loads(ping["Commands"])  # now a list[dict]
```

Each entry has `ID`, `Command`, `Time`, `Success`, `Args` (with `password` redacted). This is how you confirm a command actually ran.

### The Schedule Report payload

Schedule Report is the response to [`get_schedule`](../api-reference/spacecraft-commands.md#get_schedule):

| Field | Type | Meaning |
| --- | --- | --- |
| `Count` | int | Number of pending commands. |
| `Commands` | string (JSON) | JSON array of pending commands; each has `Asset`, `ID`, `Index`, `Time`, `Command`, `Args` (redacted). |

Same JSON-string-of-array trick. Same `json.loads` after parse.

### Worked example with the bundled parser

```python
import json
from space_range_scripts import GroundClient

ground = GroundClient(game="SPACE RANGE", team_id=111111, password="AB12CD")
ground.connect()

# Cache schemas once at startup.
schemas = ground.fetch_packet_schemas()

@ground.on_downlink
def on_downlink(record):
    if record.format != 1:    # not a Space Packet
        return
    pkt = record.parse_space_packet(schemas)   # APID-routed XTCE parse
    if pkt.name == "Ping":
        ping = pkt.fields
        ping["Commands"] = json.loads(ping["Commands"])
        for c in ping["Commands"]:
            print(f"  executed t={c['Time']:.1f}s {c['Command']} → success={c['Success']}")
    elif pkt.name == "ScheduleReport":
        sched = pkt.fields
        sched["Commands"] = json.loads(sched["Commands"])
        print(f"queue depth = {sched['Count']}, next at t={sched['Commands'][0]['Time']:.1f}s")

ground.run_forever()
```

The same flow is implemented inside the Operator UI's `DataView` — every Space Packet that arrives is routed by APID, parsed against the cached XTCE document, and rendered into the live feed.

### Worked example without a library (Python + struct)

If you don't want to depend on the script package, you can still get the same result with `struct` and a small XTCE walker. The wire encoding for every field is **big-endian** (CCSDS network byte order):

| XTCE type | Wire encoding |
| --- | --- |
| `Bool` | 1 byte (`0` or `1`) |
| `Int` | 32-bit signed two's complement, big-endian |
| `Float` | 32-bit IEEE-754, big-endian |
| `String` | 16-bit big-endian length prefix, then UTF-8 bytes |
| `DateTime` | 64-bit signed integer (ticks), big-endian |
| `Vector2/3/4` | each component is a 64-bit IEEE-754 double, big-endian, expanded to `_X`/`_Y`/`_Z`/`_W` parameters |

A trimmed-down skeleton for Ping using those rules:

```python
import struct, json

def read_string_be(data: bytes, off: int) -> tuple[str, int]:
    (length,) = struct.unpack_from(">H", data, off)
    off += 2
    return data[off:off + length].decode("utf-8"), off + length

def parse_ping_user_data(data: bytes) -> dict:
    """
    Hand-coded for clarity. Real XTCE parsing should follow the schema
    rather than hardcoded offsets — fields can move between scenarios.
    All multi-byte fields are big-endian.
    """
    off = 0
    state,   off = read_string_be(data, off)
    station, off = read_string_be(data, off)
    memory,  = struct.unpack_from(">f", data, off);  off += 4
    battery, = struct.unpack_from(">f", data, off);  off += 4
    commands_json, off = read_string_be(data, off)
    intercept_bytes, = struct.unpack_from(">i", data, off); off += 4

    return {
        "State": state, "Station": station,
        "Memory": memory, "Battery": battery,
        "Commands": json.loads(commands_json),
        "UplinkInterceptDataBytes": intercept_bytes,
    }
```

This is illustrative only — **prefer XTCE-driven parsing** (manual or library) so your decoder doesn't break when the scenario adds or reorders fields. The full byte-level layout is in [Reference → Packet formats](../reference/packet-formats.md).

### Common pitfalls

- **Trying to parse format-0 packets.** They're empty by design.
- **Forgetting to `json.loads(packet.Commands)`.** Field arrives as a string; until you load it, you can't iterate over it.
- **Hardcoding APIDs.** They're stable within one scenario but free to change across builds. Always look them up in the XTCE.
- **Reusing schemas across `instance` resets.** Re-fetch on instance change.

---

## Format `2` — Media (imagery & files)

The body of a media frame is fixed-format: a 50-byte name header followed by raw file bytes (typically JPEG or PNG).

| Offset | Size | Field |
| --- | --- | --- |
| 0 | 50 bytes | File name, ASCII / UTF-8, padded with `\0`. |
| 50 | … | File body. |

### Python

```python
def parse_media(body: bytes) -> dict:
    if len(body) < 50:
        raise ValueError("Media body too short for name header")
    name_raw = body[:50]
    name = name_raw.split(b"\x00", 1)[0].decode("utf-8", errors="replace")
    file_bytes = body[50:]
    return {"name": name, "bytes": file_bytes}
```

### JavaScript

```javascript
function parseMedia(body) {
  if (body.length < 50) throw new Error("Media body too short");
  let nameEnd = 0;
  while (nameEnd < 50 && body[nameEnd] !== 0) nameEnd++;
  const name = new TextDecoder("utf-8").decode(body.slice(0, nameEnd));
  const fileBytes = body.slice(50);
  return { name, bytes: fileBytes };
}
```

To save an image to disk:

```python
media = parse_media(record.body)
with open(f"images/{media['name']}.jpg", "wb") as f:
    f.write(media["bytes"])
```

### Pitfalls

- **Names longer than 50 bytes are truncated** at capture time, before they ever reach you. Allow for that when correlating with the original `capture` command.
- **Imagery is corrupted probabilistically** to model real-world data integrity. Some bytes will be flipped at random — don't assume every JPEG decodes cleanly. Failed decodes are still useful as evidence; archive the raw bytes.

---

## Format `3` — Uplink Intercept

When a spacecraft has uplink-intercept recording enabled, the receiver captures every uplink frame on its frequency — including foreign uplinks intended for other teams — and emits them on downlink as 32-byte-headered records. Use these for SIGINT analysis or replay exercises.

### Header layout (little-endian, 32 bytes)

| Offset | Size | Field | Meaning |
| --- | --- | --- | --- |
| 0 | 4 | `Magic` | `0x5055495A` ("ZIUP" — Zendir/Uplink/Intercept/Payload). Reject if mismatched. |
| 4 | 1 | `Version` | Wire-format version (currently `2`; v1 also accepted, lacks frequency). |
| 5 | 3 | _padding_ | Zero. |
| 8 | 8 | `SimTimeSeconds` | `double`, simulation time when the frame was dequeued. |
| 16 | 4 | `WireLengthBytes` | Original on-air length. |
| 20 | 4 | `StoredLengthBytes` | Bytes actually stored = `min(WireLengthBytes, 1024)`. |
| 24 | 1 | `Flags` | Bitmask, see below. |
| 25 | 3 | _padding_ | Zero. |
| 28 | 4 | `ReceiverFrequencyMHz` | `float32`, the receiver frequency at capture time. |
| 32 | … | Payload | Up to 1024 bytes of raw on-air ciphertext. |

### Flags

| Bit | Name | Meaning |
| --- | --- | --- |
| 0 | `Truncated` | Stored bytes are only a prefix of the on-air frame. |
| 1 | `DecodeOk` | Stored payload decoded as UTF-8 text. |
| 2 | `ParseOk` | The decoded text was valid JSON. |
| 3 | `AddressedToUs` | Parsed JSON's `Asset` field matches *our* spacecraft (so our computer would have executed it). |

### Python parser

```python
import struct

ZIUP = 0x5055495A
HEADER_SIZE = 32

class InterceptFlags:
    Truncated     = 1 << 0
    DecodeOk      = 1 << 1
    ParseOk       = 1 << 2
    AddressedToUs = 1 << 3

def parse_uplink_intercept(body: bytes):
    if len(body) < HEADER_SIZE:
        raise ValueError("Buffer too short for intercept header")

    magic, version = struct.unpack_from("<iB", body, 0)
    if magic != ZIUP:
        raise ValueError(f"Bad intercept magic 0x{magic:08x}")
    if version not in (1, 2):
        raise ValueError(f"Unknown intercept version {version}")

    sim_time     = struct.unpack_from("<d", body, 8)[0]
    wire_len     = struct.unpack_from("<i", body, 16)[0]
    stored_len   = struct.unpack_from("<i", body, 20)[0]
    flags        = body[24]
    rx_freq_mhz  = struct.unpack_from("<f", body, 28)[0] if version >= 2 else None

    payload = body[HEADER_SIZE:HEADER_SIZE + stored_len]

    return {
        "version": version,
        "sim_time": sim_time,
        "wire_length": wire_len,
        "stored_length": stored_len,
        "flags": flags,
        "rx_frequency_mhz": rx_freq_mhz,
        "addressed_to_us": bool(flags & InterceptFlags.AddressedToUs),
        "decode_ok":       bool(flags & InterceptFlags.DecodeOk),
        "parse_ok":        bool(flags & InterceptFlags.ParseOk),
        "truncated":       bool(flags & InterceptFlags.Truncated),
        "payload": payload,
    }
```

### JavaScript parser

The Operator UI ships a reference implementation at `space-range-operator/src/user/helpers/uplinkInterceptParse.js` — `parseUplinkInterceptRecord(rawBytes)` returns the same shape. Use it as a drop-in if you're building a JS client.

### What to do with intercepts

There are two common workflows.

**SIGINT classification.** For each record, look at the flag combination:

| Pattern | What it means | What to do |
| --- | --- | --- |
| `AddressedToUs` set | Our own command, just observed | Confirm against our log; ignore. |
| `ParseOk` set, not `AddressedToUs` | Foreign command JSON | Inspect — what was the other team trying to do? |
| `DecodeOk` set, `ParseOk` not | UTF-8 but not command JSON | Probably noise or partial frame. Worth a closer look in hex. |
| Neither | Raw ciphertext | Ciphertext for an unknown key, or random RF noise. Keep for replay. |

**Replay exercises.** The stored payload is the **on-air ciphertext** — i.e. it's already encoded with whatever Caesar key the original target was on. To replay it, transmit it from your own ground station via [`transmit_bytes`](../api-reference/ground-requests.md#transmit_bytes) on the same frequency the intercept reports. If your target is on a different key, the replay will be garbage to them — which is the same problem the original sender faced.

```python
intercept = parse_uplink_intercept(record.body)

# Re-broadcast it, base64-encoded, on the same frequency we captured it on.
import base64
ground.request("transmit_bytes", {
    "frequency": intercept["rx_frequency_mhz"],
    "encoding":  "base64",
    "data":      base64.b64encode(intercept["payload"]).decode("ascii"),
})
```

---

## Putting it all together

A complete decoder, in Python, that handles every format and dispatches into per-type handlers:

```python
import json
import struct
import paho.mqtt.client as mqtt

GAME, TEAM_ID, PASSWORD, CAESAR_KEY = "SPACE RANGE", 111111, "AB12CD", 17
SCHEMAS = []  # Fetched once via ground.request("get_packet_schemas")

def on_message(client, _userdata, msg):
    rec = handle_downlink(msg.payload, PASSWORD, CAESAR_KEY)
    if not rec or rec["team_id"] != TEAM_ID:
        return

    fmt, body = rec["format"], rec["body"]
    if fmt == 1:
        pkt = parse_space_packet(body, SCHEMAS)
        if pkt and pkt["name"] == "Ping":
            handle_ping(pkt["fields"])
        elif pkt and pkt["name"] == "ScheduleReport":
            handle_schedule_report(pkt["fields"])
    elif fmt == 2:
        media = parse_media(body)
        save_image(media["name"], media["bytes"])
    elif fmt == 3:
        intercept = parse_uplink_intercept(body)
        log_intercept(intercept)
    # fmt == 0: ignore

def handle_ping(fields):
    fields["Commands"] = json.loads(fields["Commands"])
    print(f"State={fields['State']} Battery={fields['Battery']:.0%} "
          f"Memory={fields['Memory']:.0%} Station={fields['Station']}")
    for c in fields["Commands"]:
        print(f"  ↳ {c['Command']} t={c['Time']:.1f}s success={c['Success']}")

def handle_schedule_report(fields):
    fields["Commands"] = json.loads(fields["Commands"])
    print(f"queue depth = {fields['Count']}")

client = mqtt.Client()
client.on_message = on_message
client.connect("broker.local", 1883)
client.subscribe(f"Zendir/SpaceRange/{GAME}/{TEAM_ID}/Downlink")
client.loop_forever()
```

Substitute `parse_space_packet` for the XTCE library you choose to use — the rest of the pipeline is invariant.

---

## Validating your decoder against the Operator UI

A useful smoke test: subscribe both your custom client and the Operator UI to the same team, send a short uplink sequence (e.g. a Sun-pointing `guidance`), and confirm that:

1. Your custom client and the UI's **Data** view both register the same Ping at roughly the same simulation time.
2. The `Commands` arrays match.
3. If you capture an image, the **Image** view in the UI shows the same name + bytes you save to disk.

Discrepancies almost always trace back to:

- A mismatched team password (XOR layer fails — payload looks like noise).
- A mismatched Caesar key (XOR succeeds, frame header looks plausible, body is gibberish).
- Stale XTCE schemas after an `instance` reset (Space Packet headers parse, fields don't).

---

## Next

- [Reference → Packet formats](../reference/packet-formats.md) — the precise binary layouts that complement this guide.
- [Operator UI guide](operator-ui-guide.md) — how the same packets show up in the bundled UI.
- [Troubleshooting & FAQ](troubleshooting.md) — common decode failures and what they mean.
