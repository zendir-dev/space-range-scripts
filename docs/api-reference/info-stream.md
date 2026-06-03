# Info Stream

The **Info** topic publishes scenario metadata and live team scores. Use it for scoreboards, instructor dashboards, and lobby displays — without polling [`admin_list_team`](admin-requests.md#admin_list_team) on every score change.

Like [Session](session-stream.md), this topic is **not** encrypted.

---

## Topic

```text
Zendir/SpaceRange/<GAME>/Info
```

| Property | Value |
| --- | --- |
| Direction | Studio → all clients |
| Encryption | None — plain ASCII JSON |
| Cadence | **Event-driven** — a new message is published only when something changes (see below) |
| QoS | 0; the **latest** payload remains available on the topic for new subscribers |

`<GAME>` is the game name configured in Studio (case-significant), same as for Session and team topics.

---

## When messages are published

Studio publishes a fresh Info payload when any of these change:

- **Game metadata** — e.g. display `name`, `description`, or `duration`
- **Team roster** — teams added or removed
- **Scores** — any team's `correct` or `incorrect` point totals change (after a graded question submission)

Between those events, **no repeat publishes** are sent. If you subscribe after traffic has already started, read the **most recent** message on the topic to get current game and score state.

---

## Payload

```json
{
  "game": {
    "timestamp": 1780458776,
    "id": "MRX",
    "name": "Cyber Defender",
    "description": "No description provided.",
    "duration": 3600.0
  },
  "teams": [
    {
      "id": 473829,
      "name": "Team Blue",
      "color": "0098FFFF",
      "score": {
        "correct": 10,
        "incorrect": 5
      }
    },
    {
      "id": 200733,
      "name": "Team Red",
      "color": "FF558DFF",
      "score": {
        "correct": 23,
        "incorrect": 1
      }
    }
  ]
}
```

### `game` object

| Field | Type | Description |
| --- | --- | --- |
| `timestamp` | `number` | Real-time **UNIX** epoch seconds when this snapshot was published (wall clock, not simulation time). |
| `id` | `string` | Short game / scenario identifier (e.g. `MRX`). Distinct from the MQTT `<GAME>` topic segment when they differ. |
| `name` | `string` | Human-readable scenario or exercise title. |
| `description` | `string` | Longer description text; may be a placeholder if none was configured. |
| `duration` | `number` (seconds) | Planned or configured exercise duration in **seconds** (e.g. `3600.0` = one hour). |

### `teams[]` entries

| Field | Type | Description |
| --- | --- | --- |
| `id` | `integer` | Team numeric ID — matches `teams[].id` in scenario JSON and `<TEAM>` in MQTT team topics. |
| `name` | `string` | Display name (e.g. `Team Blue`, `Rogue`). |
| `color` | `string` | Team colour as **8 hex digits** `AARRGGBB` (alpha, red, green, blue), no `#` prefix. Example: `0098FFFF`. |
| `score` | `string` | JSON **string** (escaped) encoding point totals — parse it as JSON (see below). |

### `score` string

The `score` field is a string containing JSON, not a nested object. After parsing:

| Key | Type | Meaning |
| --- | --- | --- |
| `correct` | `number` (int) | **Points earned** from fully correct question submissions. |
| `incorrect` | `number` (int) | **Points lost** from wrong or partial submissions (penalties), not a count of wrong answers unless scoring is 1 point per miss. |

Example: `"score": {"correct": 10, "incorrect": 5}"` → 10 points on the board, 5 points deducted for incorrect/partial answers. Net display is often `correct - incorrect` but the wire format keeps both fields separate.

Scoring rules come from scenario [`questions[]`](../scenarios/questions.md) (`answer.score` and evaluation logic); Info only reflects the running totals.

---

## Examples

### Python

```python
import json
import paho.mqtt.client as mqtt

GAME = "SPACE RANGE"

def on_info(client, userdata, msg):
    info = json.loads(msg.payload.decode("ascii"))
    g = info["game"]
    print(f"{g['name']} ({g['id']}) — duration {g['duration']}s")

    for team in info["teams"]:
        pts = json.loads(team["score"])
        net = pts["correct"] - pts["incorrect"]
        print(f"  {team['name']:12}  +{pts['correct']} / -{pts['incorrect']}  (net {net})")

client = mqtt.Client()
client.on_message = on_info
client.connect("broker.local", 1883)
client.subscribe(f"Zendir/SpaceRange/{GAME}/Info")
client.loop_forever()
```

### JavaScript

```js
import mqtt from "mqtt";

const GAME = "SPACE RANGE";
const client = mqtt.connect("ws://broker.local:9001");

client.subscribe(`Zendir/SpaceRange/${GAME}/Info`);
client.on("message", (topic, payload) => {
  if (!topic.endsWith("/Info")) return;

  const info = JSON.parse(payload.toString("ascii"));
  for (const team of info.teams) {
    const pts = JSON.parse(team.score);
    console.log(
      `${team.name}: +${pts.correct} / -${pts.incorrect}`
    );
  }
});
```

---

## Common pitfalls

- **Treating `score` as an object.** It is a string — `JSON.parse(team.score)` (or equivalent) is required.
- **Expecting a steady heartbeat.** Unlike Session (~0.3 s), Info is quiet until something changes. Build UI around the last message received, not periodic ticks.
- **Confusing `game.id` and `<GAME>`.** The MQTT path uses the Studio game name; `game.id` is an internal short code.
- **XOR-decrypting Info.** It is plain JSON — same as Session.
- **Using simulation time.** `game.timestamp` is real-time UNIX only; use [Session](session-stream.md) `time` for command scheduling.

---

## Next

- [MQTT topics](mqtt-topics.md) — full topic map.
- [Session stream](session-stream.md) — simulation clock (complementary unencrypted topic).
- [Questions](../scenarios/questions.md) — how scenario questions define scoring.
- [Ground requests → submit_answer](ground-requests.md#submit_answer) — how teams submit answers that update scores.
