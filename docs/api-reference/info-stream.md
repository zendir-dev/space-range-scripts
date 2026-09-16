# Info Stream

The **Info** topic publishes scenario metadata and live team scores. Use it for scoreboards, instructor dashboards, and lobby displays: without polling [`admin_list_team`](admin-requests.md#admin_list_team) on every score change.

Like [Session](session-stream.md), this topic is **not** encrypted.

---

## Topic

```text
Zendir/SpaceRange/<GAME>/Info
```

| Property | Value |
| --- | --- |
| Direction | Studio → all clients |
| Encryption | None: plain ASCII JSON |
| Cadence | **Event-driven**: a new message is published only when something changes (see below) |
| QoS | 0; the **latest** payload remains available on the topic for new subscribers |

`<GAME>` is the game name configured in Studio (case-significant), same as for Session and team topics.

---

## When Messages Are Published

Studio publishes a fresh Info payload when any of these change:

- **Game metadata**: e.g. display `name`, `description`, or `duration`
- **Team roster**: teams added or removed
- **Scores**: a question is graded, an objective reward or penalty fires, or a run resets

Between those events, **no repeat publishes** are sent. Clients that subscribe after traffic starts should read the **most recent** message on the topic for current game and score state.

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
        "incorrect": 5,
        "rank": 1,
        "questions": { "earned": 10, "missed": 5, "penalty": 0, "net": 10 },
        "objectives": { "earned": 25, "penalty": 0, "penalty_count": 0, "net": 25 },
        "operations": { "earned": 0, "penalty": 0, "penalty_count": 0, "net": 0 },
        "total": { "earned": 35, "penalty": 0, "penalty_count": 0, "net": 35 }
      }
    },
    {
      "id": 200733,
      "name": "Team Red",
      "color": "FF558DFF",
      "score": {
        "correct": 23,
        "incorrect": 1,
        "rank": 2,
        "questions": { "earned": 23, "missed": 1, "penalty": 0, "net": 23 },
        "objectives": { "earned": 20, "penalty": 10, "penalty_count": 1, "net": 10 },
        "operations": { "earned": 0, "penalty": 0, "penalty_count": 0, "net": 0 },
        "total": { "earned": 43, "penalty": 10, "penalty_count": 1, "net": 33 }
      }
    }
  ]
}
```

### `game` Object

| Field | Type | Description |
| --- | --- | --- |
| `timestamp` | `number` | Real-time **UNIX** epoch seconds when this snapshot was published (wall clock, not simulation time). |
| `id` | `string` | Short game / scenario identifier (e.g. `MRX`). Distinct from the MQTT `<GAME>` topic segment when they differ. |
| `name` | `string` | Human-readable scenario or exercise title. |
| `description` | `string` | Longer description text; may be a placeholder if none was configured. |
| `duration` | `number` (seconds) | Planned or configured exercise duration in **seconds** (e.g. `3600.0` = one hour). |

### `teams[]` Entries

| Field | Type | Description |
| --- | --- | --- |
| `id` | `integer` | Team numeric ID: matches `teams[].id` in scenario JSON and `<TEAM>` in MQTT team topics. |
| `name` | `string` | Display name (e.g. `Team Blue`, `Rogue`). |
| `color` | `string` | Team color as **8 hex digits** `AARRGGBB` (alpha, red, green, blue), no `#` prefix. Example: `0098FFFF`. |
| `score` | `object` | Live question, objective, operation, penalty, net, and rank totals. |

### `score` Object

The `score` field is a nested JSON object containing score information.

| Key | Type | Meaning |
| --- | --- | --- |
| `correct` | `number` | Legacy alias for `questions.earned`. |
| `incorrect` | `number` | Legacy alias for `questions.missed`. These are points not earned, not a deduction from `total.net`. |
| `rank` | `integer` | Current leaderboard rank, starting at 1. |
| `questions.earned` | `number` | Points actually earned from question submissions. |
| `questions.missed` | `number` | Available question points missed through wrong or partial answers. |
| `questions.penalty` | `number` | Magnitude of any actual negative question awards. Normally zero. |
| `questions.net` | `number` | Question rewards minus actual question penalties. |
| `objectives.earned` | `number` | Positive points earned from objectives. |
| `objectives.penalty` | `number` | Positive magnitude of negative objective awards. |
| `objectives.penalty_count` | `integer` | Number of negative objective awards triggered. |
| `objectives.net` | `number` | Objective rewards minus objective penalties. |
| `operations.*` | object | The same earned/penalty/net breakdown for other score actions. |
| `total.earned` | `number` | All positive awards in the score ledger. |
| `total.penalty` | `number` | Positive magnitude of all negative awards. |
| `total.penalty_count` | `integer` | Number of negative awards. |
| `total.net` | `number` | The leaderboard score: `total.earned - total.penalty`. |

Teams rank by `total.net` descending. Ties prefer lower `total.penalty`, then higher
`total.earned`, then lower team ID. This rewards a clean run when two teams finish on the same net
score without allowing penalty avoidance to outweigh a genuinely higher score.

Scoring rules come from scenario [`questions[]`](../scenarios/questions.md) and
[`objectives[]`](../scenarios/objectives.md). A negative objective is a real penalty and reduces
`total.net`; an incorrect question records missed points but does not create a negative award.

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
    print(f"{g['name']} ({g['id']}): duration {g['duration']}s")

    for team in info["teams"]:
        pts = team["score"]
        print(
            f"  #{pts['rank']} {team['name']:12}  "
            f"+{pts['total']['earned']} / -{pts['total']['penalty']}  "
            f"(net {pts['total']['net']})"
        )

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
    const pts = team.score;
    console.log(
      `#${pts.rank} ${team.name}: ` +
      `+${pts.total.earned} / -${pts.total.penalty} (net ${pts.total.net})`
    );
  }
});
```

---

## Common Pitfalls

- **Expecting a steady heartbeat.** Unlike Session (~0.3 s), Info is quiet until something changes. Build UI around the last message received, not periodic ticks.
- **Confusing `game.id` and `<GAME>`.** The MQTT path uses the Studio game name; `game.id` is an internal short code.
- **XOR-decrypting Info.** It is plain JSON: same as Session.
- **Using simulation time.** `game.timestamp` is real-time UNIX only; use [Session](session-stream.md) `time` for command scheduling.

---

## Next

- [MQTT topics](mqtt-topics.md): full topic map.
- [Session stream](session-stream.md): simulation clock (complementary unencrypted topic).
- [Questions](../scenarios/questions.md): how scenario questions define scoring.
- [Ground requests → submit_answer](ground-requests.md#submit_answer): how teams submit answers that update scores.
