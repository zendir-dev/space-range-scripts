# Operator UI Guide

The **Operator UI** (`space-range-operator/`) is the bundled React web app for running a Space Range exercise. It's a thin client over the same MQTT API documented elsewhere in these docs — anything the UI does, you can do from a custom client. But for most operators most of the time, the UI is the right tool.

This guide is a complete view-by-view walkthrough. For getting connected for the first time, see [Getting started → Operator UI Quick Start](../getting-started/operator-ui.md).

---

## Layout & navigation

After login the screen is:

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Top bar:  game name · session clock · asset selector · status icons  │
├────────┬─────────────────────────────────────────────────────────────┤
│  Side  │                                                             │
│  Nav   │                       Main view                             │
│        │                                                             │
└────────┴─────────────────────────────────────────────────────────────┘
```

- **Top bar.** Always visible. The session clock (`t = X.XX s · UTC ...`) confirms the simulation is alive. The asset selector to the right switches the working spacecraft when your team has more than one. Status icons at the far right indicate broker connectivity, current sim speed, and active alerts.
- **Side nav.** All the major views, listed below. Collapses to a tablet bar below 1024px wide.
- **Main view.** Whichever view is currently selected.

The UI persists everything you set into cookies, so most settings (theme, panel sizes, plot selections) survive a page reload.

---

## Map

The "where am I, where are they?" view.

- **Globe** with each spacecraft's current position and recent ground track, colour-coded by team (admin) or your team's colour (operator).
- **Ground stations** for the scenario, marked at their lat/lon.
- **In-view indicator** showing which station(s) currently see your spacecraft.
- **Click a spacecraft** to centre and select it.

When to use it:

- **At connect** — confirm your spacecraft is where you expected.
- **Before a `capture`** — verify you're over the target ground footprint.
- **Before an `encryption` rotation** — confirm you're in view of a station so the new key can be confirmed quickly via the next Ping.

The view doesn't issue commands itself; it's a situational awareness layer. For control, jump to **Control**.

---

## Telemetry

The radio status board.

Three panes:

- **Link Budget.** Latest uplink and downlink budget snapshots — SNR (dB), link margin (dB), bandwidth, range. Pulled from `get_telemetry` on a slow poll and refreshed whenever a new Ping arrives.
- **Frequency & Caesar key.** The current `(frequency, key)` pair the **ground side** is configured for. Two important things to know:
  - This is what your **receiver** is listening for, not necessarily what your spacecraft is transmitting on. A mismatch between these two is the most common cause of "I stopped getting Pings".
  - Use the **Set Telemetry** button to push the values you want to use — it sends a `set_telemetry` request that updates the ground state immediately.
- **Transmit Bytes.** A raw-bytes injector for the team's uplink. You pick an encoding (`base64`, `hex`, `utf8`, `ascii`, `b64`), paste your payload, set a frequency, and hit **Transmit**. Used for replaying captured frames or testing nonstandard payloads — see [Decoding telemetry](decoding-telemetry.md#what-to-do-with-intercepts) for the typical workflow.
- **Inbound RF Feed.** A live tail of the most recent decoded RF events.

When to use it:

- **Diagnosing a dead link.** Compare the spacecraft's broadcast `(frequency, key)` (in the Ping) against the ground side's `(frequency, key)` here. If they disagree, fix the side that's wrong.
- **Replaying an intercept.** Drop the bytes from the **Uplink Intercept** view into Transmit Bytes.
- **Verifying an `encryption` rotation succeeded.** After a rotate, watch this view for the next link-budget update with the new frequency.

---

## Control

The fastest way to issue a single command. The view shows one form per supported command type, conditionally — forms only appear when the selected spacecraft has the relevant hardware.

Forms surfaced (one panel each):

| Panel | Maps to | Notes |
| --- | --- | --- |
| **Guidance** | [`guidance`](../api-reference/spacecraft-commands.md#guidance) | Pointing mode, target component, alignment axis. |
| **Camera** | [`camera`](../api-reference/spacecraft-commands.md#camera) + [`capture`](../api-reference/spacecraft-commands.md#capture) | Configure FOV/aperture, then capture. Only shown if an imager component exists. |
| **Downlink** | [`downlink`](../api-reference/spacecraft-commands.md#downlink) | Optional `ping` flag to force a status push. |
| **Jammer** | [`jammer`](../api-reference/spacecraft-commands.md#jammer) | Frequencies + power. Only shown if a jammer is present. |
| **Thruster** | [`thrust`](../api-reference/spacecraft-commands.md#thrust) | Burn config. Only shown if a thruster is present. |
| **Rendezvous** | [`rendezvous`](../api-reference/spacecraft-commands.md#rendezvous) | Target asset selection. Only shown if RPO is enabled and ≥2 assets exist. |
| **Docking** | [`docking`](../api-reference/spacecraft-commands.md#docking) | Phases of docking. Requires a docking adapter and RPO. |

Every form has the same submit pattern:

1. Fill the fields. The form validates inline; invalid values are caught before the request goes out.
2. Optionally set a **Time** field — leave at `0` for "execute immediately", set a positive value to enqueue.
3. Click **Send**. The command is XOR-encoded and published on `Uplink`.
4. Watch the response in **Log** ("Sent" entry) and the next Ping in **Data** for the execution result.

Forms only show fields the API supports; if you can't find a knob in the UI, it's because the wire API doesn't accept it. Drop to a custom client if you need something niche.

---

## Schedule

Visualises and manages the spacecraft's pending command queue.

- **Top half** — table of currently-scheduled commands (`Time`, `Command`, `Args` digest). Refreshes whenever a Schedule Report arrives.
- **Bottom half** — controls to:
  - **Refresh** — sends [`get_schedule`](../api-reference/spacecraft-commands.md#get_schedule) and updates the table.
  - **Edit** — sends [`update_command`](../api-reference/spacecraft-commands.md#update_command). Pick a row, change the time and/or arguments, send.
  - **Remove** — sends [`remove_command`](../api-reference/spacecraft-commands.md#remove_command).
  - **Add** — opens an embedded mini Control view that lets you queue a future command without leaving the schedule.

When to use it:

- **Planning a pass.** Queue several commands ahead of an upcoming station overflight.
- **Cleaning up after a misfire.** Find the bad command in the queue, remove it.
- **Adjusting timing.** A scheduled `capture` slipped a few seconds — edit it rather than removing and re-adding.

The view shows pending commands only. Commands that have already executed appear in the **Log** (and in the most recent Ping's `Commands` field).

---

## Plot

Time-series plots of selected telemetry fields. Most useful in long scenarios.

- **Left rail** — pick fields to plot. Fields are categorised by component (Battery, Reaction Wheels, Receiver, …) and supports multi-select. Up to 8 series at once is comfortable.
- **Centre** — chart with shared time axis. Auto-scrolls during live play; freeze with the pause button to inspect history.
- **Right rail** — per-series legend with current value, min/max within visible window, and unit.

The Plot view binds directly to inbound Pings — the more frequent your `ping_interval`, the higher-resolution your plots. To increase cadence beyond the configured rate, send `downlink` with `ping=true` whenever you want a fresh point.

When to use it:

- **Power management.** Track Battery over an orbit to see when you'll be in eclipse.
- **Storage planning.** Watch Memory rise during sustained captures to predict when you must `downlink`.
- **Link diagnostics.** Plot SNR alongside Battery to correlate transmit power with budget margins.

---

## Image

Displays imagery downlinked from cameras.

- **Gallery** of full captures and 32×32 sample previews, ordered by capture time.
- **Selected image pane** with metadata: capture sim time, camera component, file name, raw size in bytes.
- **Download** button to save the original bytes.

Images come in over the same `Downlink` topic as Pings, with `Format = Media`. The UI parses the 50-byte name header and either decodes the JPEG/PNG or shows the raw bytes if the file is corrupt. (Imagery is corrupted probabilistically — see [Telemetry → Format = Media](../concepts/telemetry.md#format--media-imagery-and-files).)

When to use it:

- **After a `capture`.** Verify the camera was pointed at the right thing.
- **For Q&A.** Many `questions[]` in scoring scenarios require visual identification — this is where you check.

---

## Data

The raw inbound Space Packet feed.

- **Live list** of every Space Packet you've received (Pings, Schedule Reports, custom packet types if the scenario defines any).
- **Per-packet detail** showing parsed XTCE fields. The `Commands` field on Pings is auto-decoded from JSON-string to JSON-array for readability.
- **Filter** by APID/name and by time window.

This is the closest the UI gets to "raw mode" — it's what you watch when you're debugging a telemetry pipeline or want to confirm a specific field arrived. For everything else, the higher-level views (Plot, Telemetry) are easier.

---

## Log

A chronological feed of session-level events:

- Connection state changes (connected, disconnected, reconnect attempts).
- Outbound commands ("Sent: guidance to A3F2C014 at t=0").
- Inbound command acks ("Executed: guidance — success").
- Errors (parse failures, broker errors, request rejections).

Use the Log as the primary "what just happened?" view. When something goes wrong elsewhere, the Log usually has the answer first.

---

## Timeline

Scenario events on a chronological strip.

- **Past events** are styled "completed" and show their actual trigger time.
- **Future events** are styled "upcoming" and show countdowns in sim seconds.
- **Tooltips** include the event description.

The Timeline is most useful when the instructor has shared the scenario brief — you can correlate "expect a Battery anomaly at t=6000s" with the timeline's countdown so you're not surprised.

This view is read-only; events are scheduled in the scenario JSON and triggered by Studio.

---

## Repair

A shortcut for component-level resets.

- **List** of components on the selected spacecraft, with their current health/status.
- **Reset** buttons next to components in a failed/intermittent state.

Under the hood, **Repair** issues a `reset` command targeted at the component. The action is destructive in the sense that the component reboots and any in-flight operation it had is lost — but it's the supported recovery path for a component that's stuck in an error state from a scripted scenario event.

---

## Questions

Scenario Q&A. Only present if the loaded scenario defines `questions[]`.

- **Top bar** — running score, "answered N of M" progress.
- **Question list** — grouped by `section`. Locked questions are shown but greyed.
- **Question detail** — title, description, type-appropriate input (text box, number input, single-select dropdown, multi-select checkbox group).
- **Submit** button.

After submission:

- The UI shows the configured `reason` text (correct or incorrect, depending on your answer).
- Your team's score updates if you got it right.
- The question is locked — you cannot resubmit.

Behind the scenes the UI calls [`list_questions`](../api-reference/ground-requests.md#list_questions) and [`submit_answer`](../api-reference/ground-requests.md#submit_answer); see those endpoints for the wire format.

---

## Uplink Intercept

The SIGINT view. Lists every uplink the spacecraft has captured off-air, decoded as far as the receiver could.

Per-row, you see:

- **Kind badge** — `Our command` (addressed to us), `Other command` (parsed JSON for someone else), `Readable text` (UTF-8 but not command JSON), or `Raw capture` (undecoded ciphertext).
- **Length** — `wire → stored` bytes (different when truncated).
- **Frequency** — receiver frequency at capture time.
- **Sim time** — when the capture occurred.

Clicking a row opens a detail panel with:

- The full 32-byte header decoded.
- Hex + ASCII view of the stored payload.
- A **Replay via Transmit Bytes** button that prefills the **Telemetry → Transmit Bytes** form with the capture's bytes and frequency.

Filters at the top let you toggle "All / For us / Not for us" — useful in a busy session.

When to use it:

- **Counter-intelligence.** What is the other team about to do?
- **Replay exercises.** Re-broadcast a captured `Other command` to see whether your transmitter can spoof its target. Almost always blocked by encryption mismatch — that's the lesson.
- **Forensic.** After a confusing event, scroll through intercepts to see what was on the air at the time.

The full record format is in [Telemetry → Format = Uplink Intercept](../concepts/telemetry.md#format--uplink-intercept).

---

## Limit

User-defined operating limits on telemetry channels.

- **Add limit** — pick a channel (any field that arrives in a Ping or other Space Packet), set a min, max, or both, and choose a severity (`info`, `warn`, `critical`).
- **Active limits** — table of currently-configured limits, each with their last evaluation against the most recent telemetry sample.
- **Alerts** — when a limit is violated, the side nav shows a badge and the Log records the breach.

Limits are **client-side only** — they're not pushed to Studio and don't trigger any spacecraft action. Their value is operator attention: "wake me up when battery drops below 0.2".

---

## Settings

Configuration for the UI itself.

- **Connection.** Server, game, team ID, password (`pin` style). Includes the clipboard-copy that emits a sharable URL.
- **Theme.** Light / dark / accent colour.
- **Layout.** Per-view density, default panels, sidebar collapsed state.
- **Advanced.** Polling intervals, log retention size, debug toggles.

Settings are stored in browser cookies. To wipe them, clear cookies for the UI's domain.

---

## Switching assets

When your team has more than one spacecraft, the **asset selector** in the top bar swaps between them. Switching:

- Reloads asset-scoped views (Telemetry, Control, Schedule, Plot, Image, Data, Repair, Limit) for the new asset.
- **Does not** reset connection state — you stay subscribed to your team's `Downlink` and continue to receive packets from all assets.
- Persists per-view UI state (selected fields in Plot, filters in Data, etc.) per asset.

Multi-asset workflows tend to look like: drive A while watching B's status from the side, then swap, then swap back.

---

## A typical operator session

A pattern that fits most exercises:

1. Open Settings → Connection. Connect with your team credentials.
2. Verify life-signs in **Map** (you see your spacecraft) and **Telemetry** (link budget recent).
3. Open **Timeline** to see what scripted events are upcoming.
4. Open **Schedule** in a side tab. Plan your near-term commands and queue them.
5. During passes, watch **Plot** for power & memory, and **Map** for ground-track.
6. After a `capture`, switch to **Image** to confirm what you got.
7. When the simulation surprises you, dive into **Log** + **Data** to reconstruct what happened.
8. If the scenario has a Q&A, periodically check **Questions** for unanswered items as you discover the relevant facts.

Most missed objectives in our experience trace back to operators forgetting to issue a `downlink` after a sequence of captures. **The downlink is what flushes onboard storage** — without it, you have great imagery the rest of the world will never see.

---

## Going beyond the UI

The UI deliberately does **not** expose every API endpoint. If you find yourself wanting:

- **Bulk schedule manipulation** (more than a handful of commands at once);
- **Programmatic Q&A** (auto-answering after analysis);
- **Custom telemetry alerting** (paging, webhook integration);
- **Historical analysis** (data warehouse queries, plotting weeks of telemetry);

…drop to a custom client. The same UI workflow can be replicated on top of the [API reference](../api-reference/mqtt-topics.md) endpoints; that's how the UI itself is built.

For instructors, see the [Instructor & admin guide](instructor-admin.md). The UI also has an admin mode that exposes the cross-team views.

---

## Next

- [First command](../getting-started/first-command.md) — the same flow without the UI.
- [Decoding telemetry](decoding-telemetry.md) — what's behind the **Data**, **Image**, and **Uplink Intercept** views.
- [Troubleshooting & FAQ](troubleshooting.md) — when something in the UI doesn't behave the way this guide says it should.
