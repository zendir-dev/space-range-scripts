# MQTT Topics

Every public Space Range interaction is one of seven MQTT topics. This page is the canonical map: what each topic is for, who publishes/subscribes, the payload shape, and the encryption layer applied.

All topics are rooted at `Zendir/SpaceRange/<GAME>/...` where `<GAME>` is the game name configured in Studio (case-significant; copy it exactly as the instructor gave it).

---

## Quick reference

| Topic | Direction | Payload | Encryption |
| --- | --- | --- | --- |
| `Zendir/SpaceRange/<GAME>/Session` | Studio → all | JSON (ASCII) | **none** |
| `Zendir/SpaceRange/<GAME>/<TEAM>/Uplink` | Client → Studio | JSON command envelope | XOR(team password) |
| `Zendir/SpaceRange/<GAME>/<TEAM>/Downlink` | Studio → client | 5-byte header + Caesar-encoded body | XOR(team password) — Caesar layer inside |
| `Zendir/SpaceRange/<GAME>/<TEAM>/Request` | Client → Studio | JSON request envelope | XOR(team password) |
| `Zendir/SpaceRange/<GAME>/<TEAM>/Response` | Studio → client | JSON response envelope | XOR(team password) |
| `Zendir/SpaceRange/<GAME>/Admin/Request` | Admin client → Studio | JSON request envelope | XOR(admin password) |
| `Zendir/SpaceRange/<GAME>/Admin/Response` | Studio → admin client | JSON response envelope | XOR(admin password) |

Placeholders:

- `<GAME>` — the game name string (e.g. `SPACE RANGE`).
- `<TEAM>` — the team's numeric ID (e.g. `111111`).

There is no QoS or retained-message contract — Studio publishes at QoS 0 and does not retain. Subscribe before traffic starts to be sure of seeing it.

---

## Session

```text
Zendir/SpaceRange/<GAME>/Session
```

- **Direction:** Studio → all.
- **Encryption:** None.
- **Cadence:** ~3 Hz while the simulation is running.
- **Payload:** Plain ASCII JSON.

The simulation clock and instance ID. The only public topic that is **not** encrypted, because it carries no team-specific information. Used by every client to drive its own clock and to detect scenario resets via the `instance` field.

→ Full reference: [Session stream](session-stream.md).

---

## Per-team topics

Each team has four topics, namespaced by the team's numeric ID. Anything you do for a team — sending commands, querying ground state, receiving telemetry — flows through these four. All four are XOR-encrypted with the team password.

### `<TEAM>/Uplink`

```text
Zendir/SpaceRange/<GAME>/<TEAM>/Uplink
```

- **Direction:** Client → Studio.
- **Encryption:** XOR(team password).
- **Payload:** JSON command envelope (PascalCase keys).

```json
{
  "Asset":   "A3F2C014",
  "Command": "guidance",
  "Time":    0,
  "Args":    { "...": "..." }
}
```

Spacecraft commands. The envelope and lifecycle are described in [Concepts → Commands and scheduling](../concepts/commands-and-scheduling.md); each command type and its `Args` are in [Spacecraft commands](spacecraft-commands.md).

Studio dispatches every uplink to **every** spacecraft owned by the team; each spacecraft's controller checks the `Asset` field and accepts only its own. Ill-addressed uplinks are dropped silently.

### `<TEAM>/Downlink`

```text
Zendir/SpaceRange/<GAME>/<TEAM>/Downlink
```

- **Direction:** Studio → client.
- **Encryption:** XOR(team password) **plus** Caesar(team key) on the inner payload.
- **Payload:** 5-byte frame header + Caesar-encoded body.

Telemetry from spacecraft. After XOR-decryption the payload begins with:

| Bytes | Field | Meaning |
| --- | --- | --- |
| 0 | `Format` | `EDataFormatType` enum: `0` = None, `1` = Message (CCSDS Space Packet), `2` = Media (file/image), `3` = Uplink Intercept. |
| 1–4 | `TeamID` | Little-endian int32. The team that owns the emitting spacecraft. |
| 5+ | Payload | Caesar-encoded body, format depending on `Format`. |

Decode the body with `caesar_decrypt(team.key, body)` to get the actual CCSDS Space Packet, media frame, or Uplink Intercept record.

→ Frame layouts: [Reference → Packet formats](../reference/packet-formats.md).
→ Decoding walkthrough: [Guides → Decoding telemetry](../guides/decoding-telemetry.md).

### `<TEAM>/Request`

```text
Zendir/SpaceRange/<GAME>/<TEAM>/Request
```

- **Direction:** Client → Studio.
- **Encryption:** XOR(team password).
- **Payload:** JSON request envelope (lowercase keys).

```json
{
  "type":   "list_assets",
  "req_id": 0,
  "args":   { "...": "..." }
}
```

Ground-controller queries: list assets, fetch component details, get/set telemetry settings, transmit raw bytes, ask the AI assistant, list scenario questions, etc. Each request type is documented in [Ground requests](ground-requests.md).

`req_id` is an arbitrary number you choose; the matching response carries the same `req_id` so you can correlate. `0` is fine if you never have more than one request in flight.

### `<TEAM>/Response`

```text
Zendir/SpaceRange/<GAME>/<TEAM>/Response
```

- **Direction:** Studio → client.
- **Encryption:** XOR(team password).
- **Payload:** JSON response envelope.

```json
{
  "type":    "list_assets",
  "req_id":  0,
  "args":    { "...": "..." },
  "success": true,
  "error":   ""
}
```

Replies to your `Request` publishes. The `success` flag indicates whether the request succeeded; on failure, `error` is populated and `args` is typically empty or partial.

This topic is **also** used for unsolicited push notifications:

- **`event_triggered`** — fires whenever your team's spacecraft or ground controller does something noteworthy (commands sent, telemetry settings changed, etc.).
- **`chat_response`** — fires when the AI chat assistant has produced a reply to a previous `chat_query`.

Treat the `Response` topic as a multiplexed channel and dispatch by `type` rather than assuming every message is a direct reply.

---

## Admin topics

The admin / instructor side has its own two-topic pair, namespaced under `Admin/` instead of a numeric team ID. Both are XOR-encrypted with the **admin password** (distinct from any team password).

### `Admin/Request`

```text
Zendir/SpaceRange/<GAME>/Admin/Request
```

- **Direction:** Admin client → Studio.
- **Encryption:** XOR(admin password).
- **Payload:** JSON request envelope.

Same shape as the team request envelope (`type`, `req_id`, `args`), with admin-only request types (e.g. `admin_list_entities`, `admin_query_data`, `admin_set_simulation`). See [Admin requests](admin-requests.md).

### `Admin/Response`

```text
Zendir/SpaceRange/<GAME>/Admin/Response
```

- **Direction:** Studio → admin client.
- **Encryption:** XOR(admin password).
- **Payload:** JSON response envelope.

Same response shape as the team `Response` topic. Also used for unsolicited admin notifications:

- **`admin_event_triggered`** — fires whenever **any** team's spacecraft or ground controller emits an event. The admin sees every team's traffic, not just one.

---

## What is *not* a public topic

Studio uses a few additional internal topics — most notably `<GAME>/<FREQUENCY>/Telemetry`, the simulated RF medium between spacecraft and ground stations. These are implementation details of the simulation and are not part of the client API. Do not subscribe to them directly; the relevant content reaches you, post-RF and post-encryption, on `<TEAM>/Downlink`.

---

## Subscribing pattern

For a single team operator, the minimum viable subscription set is:

```text
Zendir/SpaceRange/<GAME>/Session
Zendir/SpaceRange/<GAME>/<TEAM>/Downlink
Zendir/SpaceRange/<GAME>/<TEAM>/Response
```

The two outbound topics (`Uplink`, `Request`) you publish on but don't subscribe to.

For an admin client:

```text
Zendir/SpaceRange/<GAME>/Session
Zendir/SpaceRange/<GAME>/Admin/Response
```

If you also want to monitor a particular team's traffic in admin mode (for example, to read a team's downlinked telemetry as the instructor), you must hold that team's password and subscribe to its team-scoped topics in addition.

---

## Topic-level wildcards

The standard MQTT wildcards work, but Space Range does not depend on them. Some patterns that may be useful while developing:

```text
Zendir/SpaceRange/<GAME>/+/Session         # one-segment wildcard (rarely useful here)
Zendir/SpaceRange/<GAME>/#                 # everything for one game — admin debugging only
```

In production, keep subscriptions narrow — broker traffic is per-subscription and broad wildcards make troubleshooting harder.

---

## Next

- [Session stream](session-stream.md) — the unencrypted clock topic in detail.
- [Spacecraft commands](spacecraft-commands.md) — every uplink command type.
- [Ground requests](ground-requests.md) — every team request type.
- [Admin requests](admin-requests.md) — every admin request type.
