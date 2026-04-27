# Packet Formats

Byte-level reference for every binary format on the Space Range wire. This page is the canonical answer to "what byte goes where?" — if you're building a custom decoder and need to know the exact layout, this is the page to keep open.

For a working code walkthrough, see [Decoding telemetry](../guides/decoding-telemetry.md). For the higher-level conceptual treatment, see [Concepts → Telemetry](../concepts/telemetry.md).

---

## Endianness conventions

Two conventions co-exist on the wire. The relevant one depends on which layer you're decoding:

| Layer | Endianness | Source |
| --- | --- | --- |
| MQTT XOR ciphertext | byte-stream (no order) | n/a — XOR is per-byte |
| Downlink frame header (5 bytes) | **little-endian** | Studio writes the team ID with `IntToBytes(..., LittleEndian)` |
| Uplink Intercept header (32 bytes) | **little-endian** | The intercept record is a packed C++ struct, naturally LE on x86 / Unreal |
| CCSDS Space Packet primary header (6 bytes) | **big-endian** (network byte order) | CCSDS 133.0-B-2 §4.1.3 |
| CCSDS Space Packet secondary header | **big-endian** | Studio's `MakeIntegerType` defaults to `mostSignificantByteFirst` |
| CCSDS user-data fields (XTCE-defined) | **big-endian** | Studio writes every numeric field with `WriteBigEndian*()` |
| Media name header & body | byte-stream | name is plain ASCII bytes, file body is the file format's own |

If you're getting numeric values that look like swapped bytes (e.g. `0x0100_0000` instead of `1`), 95% of the time you've used the wrong endianness for the layer.

---

## The downlink envelope (overview)

Every byte that arrives on `Zendir/SpaceRange/<GAME>/<TEAM>/Downlink` has the same layered shape:

```text
+---------------------------------------------------+
|  XOR ciphertext (team password, no length change) |
+---------------------------------------------------+
                    │ peel XOR
                    ▼
+---+--------+----------------------------------+
| F |  Tid   |   Caesar-encoded inner payload   |
+---+--------+----------------------------------+
  1B   4B LE   variable length
                    │ peel Caesar
                    ▼
+---------------------------------------------------+
|        Inner payload (depends on F)               |
|        F=1: CCSDS Space Packet                    |
|        F=2: Media (50B name + file)               |
|        F=3: Uplink Intercept (32B + raw)          |
+---------------------------------------------------+
```

The 5-byte frame header is documented next, then each `F` value is detailed in turn.

---

## 5-byte downlink frame header

After XOR-decryption, **before** Caesar decryption, the first 5 bytes describe the inner payload.

| Offset | Size | Field | Type | Meaning |
| --- | --- | --- | --- | --- |
| 0 | 1 | `Format` | `uint8` | `EDataFormatType` enum: see below. |
| 1 | 4 | `TeamID` | `int32` LE | Numeric team ID that owns the spacecraft that emitted this packet. |
| 5 | … | `Payload` | bytes | Caesar-encoded inner payload. Variable length. |

`Format` values:

| Value | Symbol | Inner payload |
| --- | --- | --- |
| `0` | `None` | Empty / sentinel. Discard. |
| `1` | `Message` | CCSDS Space Packet (Ping, Schedule Report, or any other XTCE-defined message). |
| `2` | `Media` | 50-byte name header + file bytes. |
| `3` | `UplinkIntercept` | 32-byte intercept header + raw on-air bytes. |

Quick decode (Python):

```python
fmt = decoded[0]
team_id = int.from_bytes(decoded[1:5], "little", signed=False)
inner   = caesar_decrypt(team_key, decoded[5:])
```

The `TeamID` field is always little-endian regardless of platform — Studio explicitly serialises it that way when assembling the frame.

---

## CCSDS Space Packet (`Format = 1`)

Studio's "Message" frames are CCSDS 133.0-B-2 Space Packets with the optional Secondary Header **always enabled** for telemetry.

```text
+---------------------+----------------------+-----------------------+
|  Primary Header     |  Secondary Header    |  User Data Field      |
|       6 bytes       |     24 bytes (1)     |   variable length     |
+---------------------+----------------------+-----------------------+
```

> (1) The default Studio config is 24 bytes. The exact size is determined by the [Secondary Header config](#secondary-header-default-24-bytes); the XTCE schema you fetch via [`get_packet_schemas`](../api-reference/ground-requests.md#get_packet_schemas) is the authoritative description for the running scenario.

### Primary Header (6 bytes, big-endian)

Three 16-bit words. Bit positions are MSB-first within each word.

```text
 Word 0 (bytes 0-1):
  ┌──────┬─────┬─────────────┬─────────────────────────────┐
  │ Ver  │ Typ │ SecHdr Flag │           APID              │
  │ 3 b  │ 1 b │     1 b     │           11 b              │
  └──────┴─────┴─────────────┴─────────────────────────────┘

 Word 1 (bytes 2-3):
  ┌──────────────────┬───────────────────────────────────────┐
  │  Sequence Flags  │       Sequence Count                  │
  │       2 b        │           14 b                        │
  └──────────────────┴───────────────────────────────────────┘

 Word 2 (bytes 4-5):
  ┌─────────────────────────────────────────────────────────┐
  │           Packet Data Length minus 1                     │
  │                  16 b (uint16)                           │
  └─────────────────────────────────────────────────────────┘
```

| Field | Size | Allowed values | Meaning |
| --- | --- | --- | --- |
| `Version` | 3 b | `0` | CCSDS packet version. Always `0` for the current spec. |
| `Type` | 1 b | `0`, `1` | `0` = Telemetry (downlink), `1` = Telecommand. Studio emits only `0`. |
| `SecHdrFlag` | 1 b | `0`, `1` | `1` if a Secondary Header follows. Studio always sets `1`. |
| `APID` | 11 b | `0–2047` | Application Process Identifier. Identifies the message class. |
| `SeqFlags` | 2 b | `0–3` | `3` = unsegmented, `1` = first segment, `0` = continuation, `2` = last. Studio emits `3`. |
| `SeqCount` | 14 b | `0–16383` | Per-APID counter. Wraps. Reset on `admin_set_simulation` `Stopped`. |
| `Packet Data Length` | 16 b | `0–65535` | `(SecondaryHeaderLength + UserDataLength) − 1`. Add 1 to get the byte count of everything after the primary header. |

A worked decoder:

```python
def parse_primary_header(buf: bytes) -> dict:
    if len(buf) < 6:
        raise ValueError("Buffer too short for CCSDS primary header")
    w0, w1, w2 = struct.unpack(">HHH", buf[:6])
    return {
        "version":     (w0 >> 13) & 0x07,
        "type":        (w0 >> 12) & 0x01,
        "sec_hdr":     (w0 >> 11) & 0x01,
        "apid":         w0        & 0x07FF,
        "seq_flags":   (w1 >> 14) & 0x03,
        "seq_count":    w1        & 0x3FFF,
        "data_length":  w2 + 1,
    }
```

### Secondary Header (default 24 bytes)

Space Range uses CUC time format with all optional fields enabled except packet sub-type, which **is** enabled. Layout:

| Offset | Size | Field | Type | Meaning |
| --- | --- | --- | --- | --- |
| 0 | 1 | `PField` | `uint8` | Time-code identification byte. CUC P-field. |
| 1 | 4 | `CoarseTime` | `uint32` BE | Whole seconds since the UTC epoch. |
| 5 | 2 | `FineTime` | `uint16` BE | Fractional seconds (~15 µs / LSB). |
| 7 | 8 | `SpacecraftID` | ASCII, fixed-length | 8-character spacecraft asset ID, null-padded. |
| 15 | 1 | `PacketSubType` | `uint8` | Optional sub-classification within an APID (`0` if unused). |
| 16 | 8 | `SimulationTime` | `float64` BE (IEEE-754) | Seconds since simulation start (`t = 0`). |
| **24** | | | | **End of secondary header.** |

Notes:

- **`SpacecraftID`** is the same 8-character hex `asset_id` that you see in the team-side API (`A3F2C014`-style). Use it to demultiplex packets when subscribing on behalf of a team that has multiple spacecraft.
- **`SimulationTime`** is the most reliable timestamp for plotting — it's monotonic across leap seconds and matches the `Session` topic's `time` field exactly.
- **`CoarseTime + FineTime`** give the wall-clock UTC. If you're correlating with external systems, prefer this; if you're plotting against the simulation timeline, use `SimulationTime`.

If a scenario customises the secondary header config, the XTCE schema you fetch will reflect the new layout — always trust the schema over this table.

### User Data Field (XTCE-defined)

The user data field's bytes follow the order and types declared in the XTCE schema for the matching APID. Encoding rules are uniform:

| XTCE type | Wire encoding |
| --- | --- |
| `Bool` | 1 byte: `0` or `1`. |
| `Int` | 32-bit signed two's complement, **big-endian**. |
| `Float` | 32-bit IEEE-754, **big-endian** (note: `double` C++ fields are *down-converted* to 32-bit on the wire). |
| `DateTime` | 64-bit signed integer (Unreal `Ticks`, 100-ns units), big-endian. |
| `String` | **16-bit big-endian** length prefix (byte count, not codepoints), then UTF-8 bytes. |
| `Vector2` | Two big-endian `float64`s, in order `X, Y`. |
| `Vector3` | Three big-endian `float64`s, `X, Y, Z`. |
| `Vector4` | Four big-endian `float64`s, `X, Y, Z, W`. |

These rules are uniform across every XTCE-defined message — once you can parse one, you can parse all of them.

---

## Ping packet (`APID` = system, e.g. 100)

The most common message. Periodic snapshot of the spacecraft's state.

### XTCE field order (in encoded order)

| # | Field | XTCE type | Range / unit | Description |
| --- | --- | --- | --- | --- |
| 1 | `State` | String | enum below | Current operational state. |
| 2 | `Station` | String | — | Nearest ground station name, or `"None"`. |
| 3 | `Memory` | Float (32) | `0.0–1.0` | On-board storage usage as a fraction of capacity. |
| 4 | `Battery` | Float (32) | `0.0–1.0` | Battery charge as a fraction of capacity. |
| 5 | `Commands` | String | JSON array | Commands executed since the previous Ping. |
| 6 | `UplinkInterceptDataBytes` | Int (32) | `≥ 0`, `B` | Bytes of pre-decode intercepted uplinks queued on-board. |

`State` enum values:

| String | Meaning |
| --- | --- |
| `NOMINAL` | Normal operations. |
| `LOW` | Battery below the configured threshold but above safe-mode. Reduced operations. |
| `SAFE` | Safe mode. Most components disabled. |
| `TRANSMIT` | Currently transmitting via downlink (briefly held during burst). |
| `FULL STORAGE` | On-board storage is full; new captures are being dropped. |
| `REBOOTING` | Just executed a `reset` (or `encryption` rotation) and is offline for the configured `reset_interval`. |

### Wire layout (concrete byte view)

For an example Ping with `State="NOMINAL"`, `Station="Madrid"`, `Memory=0.42`, `Battery=0.81`, `Commands="[]"`, `UplinkInterceptDataBytes=0`:

```text
Offset  Bytes                                                Field
------  --------------------------------------------------   ----------------------
0       00 07                                                len(State) = 7
2       4E 4F 4D 49 4E 41 4C                                 "NOMINAL"
9       00 06                                                len(Station) = 6
11      4D 61 64 72 69 64                                    "Madrid"
17      3E D7 0A 3D                                          Memory   = 0.42 (BE float32)
21      3F 4F 5C 29                                          Battery  = 0.81 (BE float32)
25      00 02                                                len(Commands) = 2
27      5B 5D                                                "[]"
29      00 00 00 00                                          UplinkInterceptDataBytes (BE int32)
```

The total user-data length depends entirely on the actual string contents, so the primary header's `Data Length` field is your authoritative measure of where the packet ends.

### `Commands` JSON shape

After parsing the user-data field, `Commands` is a UTF-8 string whose contents are a JSON array. Each entry:

```json
{
  "ID":      123456,
  "Command": "guidance",
  "Time":    742.18,
  "Success": true,
  "Args":    "{\"pointing\":\"sun\",\"target\":\"Solar Panel\",\"alignment\":\"+z\"}"
}
```

| Field | Type | Description |
| --- | --- | --- |
| `ID` | int | Unique command identifier (matches the ID echoed in `command_executed` events). |
| `Command` | string | Command type (one of the [spacecraft commands](../api-reference/spacecraft-commands.md)). |
| `Time` | float | Simulation time at which it was scheduled to execute. |
| `Success` | bool | Whether execution succeeded. |
| `Args` | string (JSON) | The command's arguments as a JSON-encoded string with sensitive keys (e.g. `password`) redacted. |

`Args` is itself a JSON string — `json.loads(entry["Args"])` to recover the arguments object.

---

## Schedule Report packet

Sent only in response to [`get_schedule`](../api-reference/spacecraft-commands.md#get_schedule).

### XTCE field order

| # | Field | XTCE type | Range / unit | Description |
| --- | --- | --- | --- | --- |
| 1 | `Count` | Int (32) | `≥ 0` | Number of pending commands. |
| 2 | `Commands` | String | JSON array | Pending command queue. |

### `Commands` JSON shape

Each entry:

```json
{
  "Asset":   "A3F2C014",
  "ID":      123456,
  "Index":   3,
  "Time":    825.0,
  "Command": "capture",
  "Args":    "{\"target\":\"Camera\"}"
}
```

| Field | Type | Description |
| --- | --- | --- |
| `Asset` | string | Asset ID the command targets. |
| `ID` | int | Unique command identifier. |
| `Index` | int | Insertion index within the queue (used as a tie-breaker). Pass this to [`update_command`](../api-reference/spacecraft-commands.md#update_command) and [`remove_command`](../api-reference/spacecraft-commands.md#remove_command). |
| `Time` | float | Simulation time at which it will execute. |
| `Command` | string | Command type. |
| `Args` | string (JSON) | Arguments, redacted of sensitive keys. |

The same JSON-string-of-array trick as Ping — `json.loads(report["Commands"])` to access the list.

---

## Media frame (`Format = 2`)

Inside the Caesar-decoded body of a `Format = 2` frame:

| Offset | Size | Field | Type | Meaning |
| --- | --- | --- | --- | --- |
| 0 | 50 | `Name` | `char[50]` | File name, UTF-8, **null-padded** to 50 bytes. Names longer than 50 bytes are truncated at capture time. |
| 50 | … | `FileBytes` | bytes | The complete file body. Almost always JPEG or PNG. |

The 50-byte name field is fixed-width — extract bytes `[0, 50)`, strip trailing nulls, decode as UTF-8. Everything from byte 50 onward is the raw file.

```python
name_raw  = body[:50]
name      = name_raw.split(b"\x00", 1)[0].decode("utf-8", errors="replace")
file_data = body[50:]
```

> Imagery is corrupted **probabilistically** to simulate real-world data integrity issues. A small fraction of bytes are randomly bit-flipped before transmission. This means JPEG decoders will sometimes fail, and you should always preserve the raw bytes alongside any decoded preview.

---

## Uplink Intercept frame (`Format = 3`)

A captured uplink frame, as recorded **before** any decode or team-ID validation. Layout:

```text
+----------------------------+--------------------------------+
|  FUplinkInterceptHeader    |  Raw on-air bytes (prefix)     |
|         32 bytes           |     0..1024 bytes              |
+----------------------------+--------------------------------+
```

### Header layout (32 bytes, **little-endian**)

| Offset | Size | Field | Type | Meaning |
| --- | --- | --- | --- | --- |
| 0 | 4 | `Magic` | `int32` LE | `0x5055495A` ("ZIUP" — Zendir Uplink Intercept Payload). |
| 4 | 1 | `Version` | `uint8` | `2` currently; `1` also accepted (no frequency field). |
| 5 | 1 | `Padding0` | `uint8` | Reserved, zero. |
| 6 | 1 | `Padding1` | `uint8` | Reserved, zero. |
| 7 | 1 | `Padding2` | `uint8` | Reserved, zero. |
| 8 | 8 | `SimTimeSeconds` | `float64` LE | Simulation time when the frame was dequeued. |
| 16 | 4 | `WireLengthBytes` | `int32` LE | Original on-air length, before truncation. |
| 20 | 4 | `StoredLengthBytes` | `int32` LE | `min(WireLengthBytes, 1024)`. Bytes actually present after the header. |
| 24 | 1 | `Flags` | `uint8` | Bitmask, see below. |
| 25 | 1 | `FlagsPadding0` | `uint8` | Reserved, zero. |
| 26 | 1 | `FlagsPadding1` | `uint8` | Reserved, zero. |
| 27 | 1 | `FlagsPadding2` | `uint8` | Reserved, zero. |
| 28 | 4 | `ReceiverFrequency` | `float32` LE | Receiver tune in MHz at dequeue. v2+ only; in v1 these bytes are zero. |
| **32** | | | | **End of header.** |

Total header size is invariant at 32 bytes — there's a `static_assert` in the C++ source guaranteeing it.

### Flags (`uint8` bitmask)

| Bit | Mask | Name | Meaning |
| --- | --- | --- | --- |
| 0 | `0x01` | `Truncated` | Stored bytes are only a prefix of the on-air frame. |
| 1 | `0x02` | `DecodeOk` | Stored payload decoded as UTF-8 text successfully. |
| 2 | `0x04` | `ParseOk` | Decoded text parsed as a valid command JSON. |
| 3 | `0x08` | `AddressedToUs` | Parsed JSON's `Asset` field matches the receiver's spacecraft. |
| 4–7 | — | reserved | Set to zero. |

### Payload

After the 32-byte header, `StoredLengthBytes` raw bytes follow. These are the **on-air ciphertext** as captured — i.e. they're already encoded with whatever Caesar key the original target was on. The bytes are byte-identical to what was transmitted, suitable for replay via [`transmit_bytes`](../api-reference/ground-requests.md#transmit_bytes).

If `Truncated` is set, you have only the start of the original frame; the tail was dropped at capture.

A reference parser is shipped in the Operator UI at `space-range-operator/src/user/helpers/uplinkInterceptParse.js` — `parseUplinkInterceptRecord(rawBytes)` returns the parsed header + payload.

---

## XOR cipher specification

The transport-layer cipher used on every team-scoped MQTT topic.

### Algorithm

Cyclic byte-wise XOR. Encryption and decryption are the **same operation**.

```text
key_bytes = utf8(password)
for i in 0 .. len(data) - 1:
    out[i] = data[i] XOR key_bytes[i mod len(key_bytes)]
```

| Property | Value |
| --- | --- |
| Block size | 1 byte |
| Key length | exactly 6 UTF-8 bytes for team / admin passwords |
| IV / nonce | none |
| Padding | none |
| Output length | identical to input length |
| Empty input | returned unchanged |

### Topics that use it

Every team-scoped or admin-scoped topic except `Session`. See [MQTT topics](../api-reference/mqtt-topics.md) for the full list.

---

## Caesar cipher specification

The "RF-layer" cipher, applied to telemetry payloads inside the downlink frame.

### Algorithm

Per-byte additive shift modulo 256.

```text
encrypt: c[i] = (p[i] + key) mod 256
decrypt: p[i] = (c[i] - key) mod 256
```

| Property | Value |
| --- | --- |
| Block size | 1 byte |
| Key | integer `0–255` |
| IV / nonce | none |
| Output length | identical to input length |

### Where it's applied

Only on the **inner payload** of `Downlink` frames (`bytes[5:]` of the XOR-decrypted message). Uplinks, requests, responses, and the session topic do **not** use Caesar.

The team's current Caesar key can be fetched at runtime via [`get_telemetry`](../api-reference/ground-requests.md#get_telemetry) and rotated via the [`encryption`](../api-reference/spacecraft-commands.md#encryption) command.

---

## Session topic payload

The unencrypted heartbeat on `Zendir/SpaceRange/<GAME>/Session` is a UTF-8 JSON object, ~80–110 bytes:

```json
{
  "time":     742.18,
  "utc":      "2026-04-15T08:30:12Z",
  "instance": 3
}
```

| Field | Type | Description |
| --- | --- | --- |
| `time` | `float64` | Seconds since `t = 0` for the current scenario instance. |
| `utc` | `string` | ISO-8601 UTC time of the same moment. |
| `instance` | `int32` | Monotonic counter; increments on every `admin_set_simulation` `Stopped`. |

Cadence is ~3 Hz. See [Session stream](../api-reference/session-stream.md) for the consumer-side details.

---

## Quick decode cheat sheet

The full pipeline, expressed as one Python function:

```python
def decode_downlink(payload: bytes,
                    team_password: str,
                    caesar_key: int,
                    xtce_schemas: dict) -> dict | None:
    if not payload or len(payload) < 5:
        return None

    decrypted = xor_crypt(team_password, payload)

    fmt     = decrypted[0]
    team_id = int.from_bytes(decrypted[1:5], "little")
    inner   = caesar_decrypt(caesar_key, decrypted[5:])

    if fmt == 0:
        return None
    if fmt == 1:
        return parse_space_packet(inner, xtce_schemas)   # APID-routed
    if fmt == 2:
        return parse_media(inner)                        # 50B name + bytes
    if fmt == 3:
        return parse_uplink_intercept(inner)             # 32B header + bytes
    raise ValueError(f"Unknown frame format {fmt}")
```

Hold this picture in your head and every wire-level decision in Space Range becomes obvious.

---

## Next

- [Data types](data-types.md) — units, ranges, and conventions for every value that travels over these formats.
- [Decoding telemetry](../guides/decoding-telemetry.md) — runnable code that uses every layout on this page.
- [Concepts → Telemetry](../concepts/telemetry.md) — why these formats look the way they do.
