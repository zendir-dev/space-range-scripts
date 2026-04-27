# Operator UI Quick Start

The **Operator UI** is the bundled React web app under `space-range-operator/`. It is the reference operator client — anything it can do is also doable from a custom client over MQTT. Use it when you want a turnkey experience, when you're learning Space Range for the first time, or when you want to validate a scenario configuration without writing any code.

This page covers the absolute minimum to get connected and active. The deeper feature tour is in [Guides → Operator UI guide](../guides/operator-ui-guide.md).

---

## Running the UI

You have two options:

### Option A — Use a hosted build

If your scenario operator hosts the UI for you, just open the URL they provide in any modern browser (Chrome, Edge, Firefox, Safari). No installation needed.

### Option B — Run it locally

From the `space-range-operator/` directory:

```bash
npm install
npm start
```

The dev server starts on [http://localhost:3000](http://localhost:3000) and reloads on file changes. For a production build:

```bash
npm run build
# serve the build/ folder with any static-file server
```

The UI is a pure client — it talks to the broker directly over MQTT-over-WebSockets and does not need its own backend.

---

## Connecting

Open the UI and go to **Settings → Connection**. You'll see four fields:

| Field | What goes in it | Notes |
| --- | --- | --- |
| **Server Address** | The broker host (e.g. `mqtt.zendir.io`) | Default: `mqtt.zendir.io`. Plain hostname; the UI handles the WebSocket scheme. |
| **Game Name** | The game name configured in Studio | Auto-uppercased. Default: `SPACE RANGE`. |
| **Team ID** | Your numeric team ID | 0–999999. |
| **Password** | Your 6-character team password | Pin-style input; auto-connects when full. |

Click **Connect**. You should immediately see:

- Session clock ticking in the top bar (`t = X.XX s`).
- Your assets populating in the asset selector.
- A green/active indicator next to the connection icon.

If the clock doesn't tick, the simulation isn't running. If your assets never appear, the team ID or password is wrong (you'll typically see no error — the UI just stays empty).

### Sharable URLs

The UI persists everything you type into cookies, and also accepts query-string parameters so you can share preconfigured links:

```text
https://your-host/?server=mqtt.zendir.io&game=SPACE%20RANGE&team=111111&password=AAAAAA
```

The clipboard icon next to **Connection Settings** copies the current configuration as one of these URLs. Useful for sending team-specific links to operators.

> **Treat these URLs like passwords.** They include the team password in clear text. Don't paste them into shared chat channels or commit them to public repos.

---

## The main views

Once connected, the left-hand sidebar exposes the major work surfaces. You don't need all of them every session — pick the ones that match your scenario.

| View | What it's for |
| --- | --- |
| **Map** | World map showing each spacecraft's ground track and your ground stations. The "where am I, where are they?" view. |
| **Telemetry** | Link-budget readouts, current frequency / Caesar key, raw-bytes transmit panel, and inbound RF data feed. |
| **Control** | Forms for every spacecraft command (guidance, thrust, camera, jammer, RPO, docking, …). The fastest way to issue a single command. |
| **Schedule** | Pending commands queue. Add, edit (`update_command`), and remove (`remove_command`) future commands. |
| **Plot** | Time-series plots of selected telemetry fields. Useful for trend monitoring during long scenarios. |
| **Image** | Captured imagery downlinked from cameras. Includes both full captures and 32×32 sample previews. |
| **Data** | Inbound Space Packet feed — every CCSDS packet you've received, decoded against the active XTCE schema. |
| **Log** | Session log: connect/disconnect events, executed commands, errors. |
| **Timeline** | Scenario events (success/failure milestones) in chronological order. |
| **Repair** | Component-reset shortcut for failed subsystems. |
| **Questions** | Scenario Q&A — answers count toward scoring. |
| **Uplink Intercept** | Captured foreign uplinks, ready for SIGINT analysis or replay. |
| **Limit** | Configured operating limits / alerts on telemetry channels. |
| **Settings** | Connection, theme, and per-view preferences. |

Switching assets (when your team has more than one) is done from the asset selector at the top of the screen. All asset-scoped views update instantly.

---

## A 5-minute self-test

A quick sanity sequence to confirm everything works end-to-end:

1. **Connect** with your team credentials.
2. Open **Map**. You should see at least one spacecraft icon moving.
3. Open **Telemetry**. You should see a recent Link Budget update and the team frequency / key match what you were given.
4. Open **Control** → select your asset → choose **Guidance**.
5. Set pointing to **Sun**, alignment to **+z**, and target a solar panel component. Click **Send**.
6. Switch to **Schedule** — the command shouldn't appear here because it was immediate (`Time = 0`). It will, however, show up in **Log** under "Sent" within a second.
7. Switch to **Data** and watch the Space Packet feed. Within ~20 simulation seconds you should see a **Ping** packet whose `Commands` field contains a `guidance` entry with `Success: true`.

If any step fails, jump to the matching section of the [Troubleshooting guide](../guides/troubleshooting.md). The most common failure is a wrong Caesar key on **Telemetry** — fix it via the **Set Telemetry** controls there, or by uplinking an `encryption` command to rotate both spacecraft and ground.

---

## Where to go from here

- For a complete view-by-view walkthrough, see the [Operator UI guide](../guides/operator-ui-guide.md).
- For the same flow in code rather than UI, see [Your first command](first-command.md).
- For the wire formats behind every form in the UI, the relevant [API reference](../api-reference/mqtt-topics.md) section is the canonical answer — the UI is a thin layer over those messages.
