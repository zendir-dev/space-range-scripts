# Message Queuing Telemetry Transport (MQTT) Topics

Every public Space Range interaction uses a small set of MQTT topics under `Zendir/SpaceRange/<GAME>/`. This page identifies each topic, its publishers and subscribers, its payload shape, and its encryption layer.

All topics are rooted at `Zendir/SpaceRange/<GAME>/...` where `<GAME>` is the game name configured in Studio (case-significant; copy it exactly as the instructor gave it).

---

## Quick Reference

| Topic | Direction | Payload | Encryption |
| --- | --- | --- | --- |
| `Zendir/SpaceRange/<GAME>/Session` | Studio → all | JSON (ASCII) | **none** |
| `Zendir/SpaceRange/<GAME>/Info` | Studio → all | JSON (ASCII) | **none** |
| `Zendir/SpaceRange/<GAME>/<TEAM>/Uplink` | Client → Studio | JSON command envelope | XOR(team password) |
| `Zendir/SpaceRange/<GAME>/<TEAM>/Downlink` | Studio → client | 5-byte header + Caesar-encoded body | XOR(team password): Caesar layer inside |
| `Zendir/SpaceRange/<GAME>/<TEAM>/Request` | Client → Studio | JSON request envelope | XOR(team password) |
| `Zendir/SpaceRange/<GAME>/<TEAM>/Response` | Studio → client | JSON response envelope | XOR(team password) |
| `Zendir/SpaceRange/<GAME>/Admin/Request` | Admin client → Studio | JSON request envelope | XOR(admin password) |
| `Zendir/SpaceRange/<GAME>/Admin/Response` | Studio → admin client | JSON response envelope | XOR(admin password) |

Placeholders:

- `<GAME>`: the game name string (e.g. `SPACE RANGE`).
- `<TEAM>`: the team's numeric ID (e.g. `111111`).

There is no QoS or retained-message contract: Studio publishes at QoS 0 and does not retain. Subscribe before traffic starts to be sure of seeing it.

---

## Session

```text
Zendir/SpaceRange/<GAME>/Session
```

- **Direction:** Studio → all.
- **Encryption:** None.
- **Cadence:** ~every 0.3 s of real time (~3.3 Hz) while Studio is connected.
- **Payload:** Plain ASCII JSON (`timestamp`, `time`, `utc`, `instance`, `state`).

The simulation clock, state (`running` / `standby` / `paused` / `ended`), and instance ID. The only public topic that is **not** encrypted. Clients use `time` for scheduling, `state` to know whether the sim is advancing, and `instance` to detect resets. The legacy `running` boolean is deprecated: use `state`.

→ Full reference: [Session stream](session-stream.md).

---

## Info

```text
Zendir/SpaceRange/<GAME>/Info
```

- **Direction:** Studio → all.
- **Encryption:** None.
- **Cadence:** Event-driven (game metadata, roster, or score changes only).
- **Payload:** Plain ASCII JSON (`game`, `teams[]` with stringified score objects).

Scenario title, duration, team colors, and live **correct** / **incorrect** point totals for scoreboards. The latest message stays on the topic for late subscribers.

→ Full reference: [Info stream](info-stream.md).

---

## Per-Team Topics

Each team has four topics under the team's numeric ID. Commands, ground-state queries, and telemetry flow through these topics. All four are XOR-encrypted with the team password.

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

`req_id` is a caller-assigned number. The matching response carries the same value for correlation. `0` is sufficient when only one request is in flight.

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

Replies to `Request` publishes. The `success` flag indicates whether the request succeeded; on failure, `error` is populated and `args` is typically empty or partial.

This topic is **also** used for unsolicited push notifications:

- **`event_triggered`**: fires whenever the team's spacecraft or ground controller does something noteworthy (commands sent, telemetry settings changed, and similar events).
- **`chat_response`**: fires when the AI chat assistant has produced a reply to a previous `chat_query`.

Treat the `Response` topic as a multiplexed channel and dispatch by `type` rather than assuming every message is a direct reply.

---

## Admin Topics

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

- **`admin_event_triggered`**: fires whenever **any** team's spacecraft or ground controller emits an event. The admin sees every team's traffic, not just one.

---

## What Is *Not* a Public Topic

Studio uses a few additional internal topics, most notably `<GAME>/<FREQUENCY>/Telemetry`, the simulated RF medium between spacecraft and ground stations. These are implementation details and are not part of the client API. Clients should not subscribe to them directly; relevant post-RF and post-encryption content arrives on `<TEAM>/Downlink`.

---

## Subscribing Pattern

For a single team operator, the minimum viable subscription set is:

```text
Zendir/SpaceRange/<GAME>/Session
Zendir/SpaceRange/<GAME>/Info
Zendir/SpaceRange/<GAME>/<TEAM>/Downlink
Zendir/SpaceRange/<GAME>/<TEAM>/Response
```

The two outbound topics (`Uplink`, `Request`) are publish-only for clients.

For an admin client:

```text
Zendir/SpaceRange/<GAME>/Session
Zendir/SpaceRange/<GAME>/Info
Zendir/SpaceRange/<GAME>/Admin/Response
```

Monitoring a particular team's traffic in admin mode requires that team's password and additional subscriptions to its team-scoped topics.

---

## Topic-Level Wildcards

The standard MQTT wildcards work, but Space Range does not depend on them. Some patterns that may be useful while developing:

```text
Zendir/SpaceRange/<GAME>/+/Session         # one-segment wildcard (rarely useful here)
Zendir/SpaceRange/<GAME>/#                 # everything for one game: admin debugging only
```

In production, keep subscriptions narrow: broker traffic is per-subscription and broad wildcards make troubleshooting harder.

---

## Next

- [Session stream](session-stream.md): the unencrypted clock topic in detail.
- [Info stream](info-stream.md): game metadata and team scores.
- [Spacecraft commands](spacecraft-commands.md): every uplink command type.
- [Ground requests](ground-requests.md): every team request type.
- [Admin requests](admin-requests.md): every admin request type.
