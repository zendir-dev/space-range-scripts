# Troubleshooting & FAQ

A field manual for the things that go wrong. Each section is structured the same way: **symptom → likely causes (in order of probability) → diagnostic step → fix**.

If your problem isn't here, the canonical investigation order is:

1. Is the simulation actually running? ([`admin_get_simulation`](../api-reference/admin-requests.md#admin_get_simulation) or watch the session clock.)
2. Are you on the right topic? (Game name, team ID, controller name — see [MQTT topics](../api-reference/mqtt-topics.md).)
3. Are you using the right password? (Team password vs admin password — see [Encryption](../concepts/encryption.md).)
4. Are XOR + Caesar applied in the right order? (See [Decoding telemetry](decoding-telemetry.md).)

90% of issues fall out of those four checks.

---

## Connection

### "I subscribed but nothing is arriving."

**Likely causes** (in order):

1. Wrong broker host / port.
2. Wrong topic — typo in `<GAME>` or `<TEAM_ID>`.
3. Studio is not running, or the scenario hasn't been started.
4. The session topic *is* arriving but it's unencrypted — you're applying XOR and getting garbage, then your JSON parser silently drops it.

**Diagnostic.** Subscribe to the unencrypted session topic:

```text
Zendir/SpaceRange/<GAME>/Session
```

If you receive a JSON tick at ~3 Hz, the broker and game name are correct. Move on to checking team-scoped topics. If you receive nothing, the broker host or game name is wrong.

**Fix.** Confirm `GAME` matches Studio's configured game name *exactly*, including spaces and case. The Operator UI auto-uppercases the game name; do the same in custom clients.

### "I get connected but published commands have no effect."

**Likely causes**:

1. You're publishing to a topic with a typo (e.g. `Uplinks` instead of `Uplink`). MQTT brokers happily accept publishes to topics nobody listens to.
2. You're encrypting with the wrong password — Studio decrypts your bytes into garbage, fails to parse JSON, and silently drops the message.
3. You're publishing on the wrong team's topic (not your own).

**Diagnostic.** Subscribe to your team's `Response` topic and send a request — if you get back any reply (even an error), the topic + password are correct and you can move on to debugging the command itself.

**Fix.** Re-derive your topic strings from a known-good template. Compare your XOR output against the Operator UI's output for the same payload (its dev tools log XOR'd payloads in debug mode).

### "Connection drops every minute."

**Likely cause.** Your MQTT keepalive isn't being honoured by your client. Most paho-mqtt and `mqtt.js` defaults are fine; if you're hand-rolling MQTT, check that you're sending PINGREQ within the keepalive window.

**Fix.** Set `keepalive=60` (or your library's equivalent) and make sure your event loop is running between publishes.

---

## Encryption & decoding

### "XOR-decoded payload looks like garbage."

**Likely causes**:

1. Wrong team password.
2. You're trying to XOR the unencrypted Session topic.
3. Your password contains whitespace or padding that Studio doesn't have.

**Diagnostic.**

```python
decoded = xor_crypt(PASSWORD, mqtt_payload)
print(decoded[:64])  # human-eyeball check
```

A correctly-XOR'd JSON payload starts with `{` (`0x7B`). If yours starts with anything else, the password is wrong (or it's a downlink frame whose first byte is the format byte — see next).

**Fix.** Confirm the password against `admin_list_team` (instructors), or against the credential URL the instructor sent you.

### "I XOR'd the Downlink and the bytes still look weird."

**Likely cause.** You forgot the 5-byte frame header + Caesar layer. Downlink is *triple*-wrapped: XOR (outer), 5-byte header, then Caesar.

**Diagnostic.**

```python
decoded = xor_crypt(PASSWORD, mqtt_payload)
fmt     = decoded[0]
team_id = int.from_bytes(decoded[1:5], "little")
print(f"format={fmt}, team_id={team_id}")
```

If `team_id` matches yours and `fmt` is in `{0,1,2,3}`, the XOR layer is correct — you just need to Caesar-decode `decoded[5:]`.

**Fix.** Apply `caesar_decrypt(KEY, decoded[5:])`. Your CCSDS Space Packet (or media / intercept body) is in there.

### "Pings stopped arriving after I rotated the Caesar key."

**Likely causes** (in order):

1. The spacecraft is rebooting (normal — wait one `reset_interval`).
2. Your client's local Caesar key is still on the old value.
3. Your ground-station receiver is still on the old key (you didn't run `set_telemetry`).
4. The rotation never reached the spacecraft (jammed / out of view); the spacecraft is still on the old key.

**Diagnostic.** Cycle your client between the old and new Caesar keys for the next two Pings. Whichever decodes is the actual spacecraft state.

**Fix.** See the [Encryption walkthrough → Recovering from a desync](encryption-walkthrough.md#recovering-from-a-desync).

### "JSON parse error on a decoded payload."

**Likely causes**:

1. Wrong password (most common).
2. Double-stringified JSON. Studio sometimes wraps payloads in an extra `json.dumps` layer; the result is a valid JSON *string* whose contents are valid JSON.
3. Embedded JSON-in-string fields (e.g. `Commands` field on Pings, `args` field on responses).

**Diagnostic.** Look at the first character. `{` → real JSON object. `"` → double-stringified.

**Fix.** Use `space_range_scripts.utils.decode_payload` or copy its logic — it handles both Studio anomalies. The relevant pattern:

```python
parsed = json.loads(text)
if isinstance(parsed, str):
    parsed = json.loads(parsed)   # unwrap
```

---

## Commands

### "I sent a command and got nothing back."

There's no acknowledgement on the wire when a command is *accepted* — that's by design (commands are fire-and-forget on the uplink topic). You only see acks in the **next Ping** as part of its `Commands` field.

**Diagnostic.** Wait for the next Ping (default cadence ~20 sim s). Look at `ping["Commands"]`. The most recent uplink should appear with `Success: true` or `Success: false`.

If it doesn't appear at all:

1. Your XOR password is wrong (Studio rejected the parse silently). Verify by [sending a request](#i-get-connected-but-published-commands-have-no-effect).
2. The command was scheduled in the future and hasn't fired yet.
3. The command violated the schema (e.g. unknown command name) and was dropped.

### "Schema mismatch on a command."

**Likely cause.** You're using lowercase JSON keys (`asset`, `command`, `time`, `args`). Uplink commands require **PascalCase** (`Asset`, `Command`, `Time`, `Args`).

**Fix.** See [Spacecraft commands → Envelope](../api-reference/spacecraft-commands.md#envelope). Note that *requests* (on the `Request` topic to the ground/admin controllers) use **lowercase** keys. The two envelopes have different conventions.

### "Time field doesn't seem to do anything."

**Likely cause.** You're setting `Time` in real seconds, not simulation seconds. Or you're setting it relative to `t=0` and the simulation is well past that.

**Fix.** `Time` is **simulation time, absolute** (sim seconds since `t=0`). To schedule "in 60 seconds", read the current sim time from the Session topic, add 60, and use that.

```python
session = latest_session_message  # {"time": 742.18, "instance": ...}
cmd["Time"] = session["time"] + 60.0
```

### "An update_command request was rejected."

**Likely causes**:

1. The command has already executed (you can only update *pending* commands).
2. The `ID` in `Args` doesn't match any pending command (it may have executed already, or the ID is stale).

**Fix.** Re-fetch the schedule with [`get_schedule`](../api-reference/spacecraft-commands.md#get_schedule) and use the spacecraft-assigned `ID` from the freshly returned report (or correlate by `TargetTime` / `TargetCommand` as documented for [`update_command`](../api-reference/spacecraft-commands.md#update_command)).

---

## Telemetry

### "The link budget shows nominal but no Pings arrive."

**Likely causes**:

1. Caesar / frequency mismatch (most common).
2. The spacecraft is in `SAFE` or `REBOOTING` state and not transmitting.
3. Storage is full and pings are being dropped before transmit.

**Diagnostic.** Have an instructor run `admin_query_data` against your spacecraft and compare its outgoing `frequency` and `key` to your client's. Or `set_telemetry` on the ground side to your spacecraft's likely values and see if you start decoding.

**Fix.** Reconcile the keys. If you can't, request a scenario reset.

### "Pings arrive but `Commands` is missing."

**Likely cause.** You haven't unwrapped the JSON-in-string field. The XTCE field `Commands` is a *string* whose contents are JSON.

**Fix.**

```python
ping["Commands"] = json.loads(ping["Commands"])
```

If that throws, check whether `Commands` is the literal string `"[]"` (empty list — no recent commands) and handle it.

### "Plot view goes flat after a while."

**Likely cause.** The spacecraft fell into eclipse / lost station view / entered SAFE mode. Pings stop, plots stop updating.

**Diagnostic.** Open the Map view to see if you're in view of any station. Check the most recent Ping's `State` field.

**Fix.** Wait for the next pass, or send a `downlink` with `ping=true` if you're in view but suspect storage backed up.

### "Captured imagery is corrupted / won't decode."

**Likely cause.** Imagery is corrupted *probabilistically* by design — see [Telemetry → Format = Media](../concepts/telemetry.md#format--media-imagery-and-files). Sometimes a JPEG is too damaged to decode but the bytes are intact.

**Fix.** Save the raw bytes anyway (the Operator UI's **Download** button does this). For analysis, treat partial / corrupted imagery as evidence — exactly the case real operators face.

---

## Scenarios & instructors

### "A team isn't appearing in the Operator UI / `admin_list_entities`."

**Likely cause.** The team's `enabled` field in the scenario JSON is `false`, or the JSON failed to parse.

**Diagnostic.** Tail Studio's log on scenario load — parse errors are logged.

**Fix.** Set `enabled: true` and re-load the scenario. After fixing, do a `Stopped` → `Running` cycle so Studio re-instantiates.

### "A spacecraft has `asset_id: null`."

**Likely cause.** The spacecraft definition has an invalid component (unknown class, missing required `data`, malformed mesh path) and Studio failed to instantiate it. The team and the spacecraft entry exist, but the runtime asset doesn't.

**Diagnostic.** Look at the `components[]` for that spacecraft in the scenario JSON. Check class names against the table in [Scenario configuration → components[]](scenario-config.md#components).

**Fix.** Correct the component definition; reload the scenario.

### "A scripted event didn't fire."

**Likely causes**:

1. `Enabled: false` on the event.
2. Trigger time hasn't been reached. Pausing extends real time but not simulation time — check the actual sim clock.
3. The `Target` string doesn't match any component / error model in the loaded build.

**Diagnostic.** Run [`admin_get_scenario_events`](../api-reference/admin-requests.md#admin_get_scenario_events). The response lists every parsed event; if your event is missing, the JSON failed to parse it.

**Fix.** Compare `Target` strings against the working examples in `orbital_sentinel.json`. Use exact spelling.

### "I changed the scenario JSON but Studio is still using the old one."

Studio caches the scenario at load time. Edits to the JSON file are ignored by the running simulation.

**Fix.** `admin_set_simulation` → `Stopped`, then either re-load the scenario from Studio's UI or restart Studio. There is no zero-downtime hot reload.

---

## Performance

### "The Operator UI is slow / dropping frames."

**Likely causes**:

1. The Plot view has too many series selected. Each Ping triggers a re-render.
2. The Data view has accumulated thousands of packets without trimming.
3. Browser tab is throttled in the background.

**Fix.**

- Trim Plot fields to ≤ 8 series.
- Open Settings → Advanced and reduce log retention.
- Keep the tab in the foreground during active sessions.

### "My Python client is missing telemetry."

**Likely causes**:

1. Your `on_message` handler is doing slow work (writing to disk, calling external APIs) in the same callback.
2. You're not running the MQTT client's network loop.

**Fix.**

- Push expensive work into a queue / worker thread; keep the handler short.
- Confirm you're calling `client.loop_forever()` or `client.loop_start()`.
- Check your broker QoS — Space Range publishes at QoS 0, so subscribers that block too long will silently miss messages.

### "The simulation slows down when I add more clients."

Studio is mostly indifferent to client count, but the broker is not. If you have 20+ subscribers on each downlink topic, the broker's outbound throughput becomes the bottleneck.

**Fix.** Use a broker scaled for the load (Mosquitto with `max_connections` raised, or a hosted broker). Avoid running every subscriber on the same machine as Studio.

---

## Quick FAQ

**Q. What's the relationship between `team_id` and `asset_id`?**
A team has one `id` (numeric). Each team has zero or more spacecraft, each with an 8-character hex `asset_id` derived at runtime. Topics use `team_id`; commands use `asset_id`. See [Teams and assets](../concepts/teams-and-assets.md).

**Q. Can I have two operators on the same team?**
Yes — both connect with the team password. Studio doesn't track "sessions"; both clients receive the same telemetry and either can send commands. Coordinate out of band.

**Q. Can two teams share a spacecraft?**
Configurationally yes (list the same `id` in two collections), but it's almost always a mistake. Both teams will see the spacecraft and both can command it; conflicts resolve in last-write-wins.

**Q. What happens when storage fills up?**
New telemetry is dropped at capture time until storage is `downlink`'d. The spacecraft enters `FULL STORAGE` state in its Pings. Send a `downlink` to flush.

**Q. How do I clear the spacecraft's command queue?**
Send `remove_command` for each pending entry, or send `reset` on the Computer component to wipe the queue (the Computer is what holds the schedule).

**Q. Does the simulation persist across restarts?**
The event database persists. Live state (positions, velocities, queued commands, in-flight RF) does not — restarts behave like an `admin_set_simulation` Stopped.

**Q. How do I find my spacecraft's `asset_id`?**
Call [`list_assets`](../api-reference/ground-requests.md#list_assets) on the ground controller. Or in the Operator UI, the asset selector in the top bar shows them.

**Q. Why does the session clock sometimes jump backwards?**
You missed an `instance` change — somebody (instructor) reset the simulation. Re-fetch your assets and XTCE schemas; your previous `(asset_id, schemas)` are stale.

**Q. Are passwords case-sensitive?**
Yes. Both team and admin passwords are case-sensitive 6-character alphanumeric strings.

**Q. Can I use TLS / wss?**
Yes. The Operator UI auto-upgrades to wss when the host page is https. Custom clients should use port 8883 / wss-equivalent for their broker library.

**Q. How do I integrate with a third-party SOC tool?**
Have your SOC consume the unsolicited admin push (`admin_event_triggered`) — it's a stream of structured events ideal for forwarding. See [Admin requests → admin_event_triggered](../api-reference/admin-requests.md#admin_event_triggered).

---

## Where to ask for help

If a problem isn't covered here:

1. Capture a minimal reproduction (one MQTT payload, one command, one decoded result).
2. Note the scenario name, the game name, your team ID (not password!), and the simulation `instance`.
3. Reach out via your usual support channel with that information.

Specific, reproducible reports are massively faster to debug than "telemetry isn't working".
