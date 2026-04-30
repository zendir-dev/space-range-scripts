# Cyber Defender — instructor brief

A one-hour workshop that walks operators through eight different cyber effects against a single MEO defender. Two duty-crew teams (Blue Alpha, Blue Bravo) share the spacecraft *Watchtower*; a scripted rogue (*PHANTOM*) flies in the same orbit and drives every active attack from `cyber_defender.py`.

The full design rationale lives in [`cyber_defender.spec.md`](cyber_defender.spec.md). This README is the launch checklist.

## Mission narrative (one paragraph)

The **Maritime Cyber Watch** programme operates *Watchtower*, an MEO imagery / SIGINT bird, over the Hormuz / Arabian Sea shipping corridor. Multiple shifts (one duty-crew per blue team) command the same spacecraft from their own consoles. Sister-state intelligence has flagged a co-orbital satellite, callsign **PHANTOM**, as a potential cyber threat. Each duty crew must keep the link healthy from their own console, recognise each cyber effect as it appears, choose the right mitigation, and submit a forensic after-action report.

## Phase plan

| Phase | Wall | Sim time | Theme |
| --- | --- | --- | --- |
| 0 — Familiarisation | 00:00 – 00:05 | `0 – 1 500 s` | Connect, baseline ops, image Hormuz, see PHANTOM on map. |
| 1 — Passive cyber | 00:05 – 00:20 | `1 500 – 6 000 s` | GPS spoof, GPS jam, storage corruption, GPS sensor hard fault. |
| 2a — Rogue capture | 00:20 – 00:30 | `6 000 – 9 000 s` | PHANTOM cycles every blue team's frequency, recording foreign uplinks (silent — no defender-visible signature). |
| 2b — Rogue replay & jam | 00:30 – 00:50 | `9 000 – 15 000 s` | Random replay bursts; **light pulsed** uplink jam on the last enemy team in config order (Blue Bravo by default); **broadcast** downlink jam over both AOI overhead passes. |
| 3 — Compound | 00:50 – 00:55 | `15 000 – 16 500 s` | Cyber telemetry tampering (Ping `State`, GPS position) + reaction-wheel stuck + battery power spikes. |
| 4 — Wind-down | 00:55 – 01:00 | `16 500 – 18 000 s` | Attacks stop. Teams finalise answers. |

Run the simulation at `simulation.speed: 5.0` (already set in `cyber_defender.json`) — this gives ~1.8 orbits in the hour.

## Launch sequence

1. **Open** `cyber_defender.json` in Studio (or load via the admin tooling). Verify `simulation.speed = 5.0`, `universe.gps = true`, and that the six ground stations (Madrid, Doha, Singapore, Perth, Auckland, Miami) are present.
2. **Start the rogue agent** from the project root:

   ```powershell
   python "scenarios/Cyber Defender/cyber_defender.py"
   ```

   It will prompt for the game name and admin password (saved between runs in `.space-range-defaults`). Connect each blue team's Operator UI separately (Blue Alpha, Blue Bravo).

3. **Start the simulation** in Studio. The script blocks in `loop_forever` and ticks the capture / replay state machines on every Session message it receives.

4. **Watch for these log markers** in the rogue's terminal — they confirm each phase started (team names below are taken straight from the config — they update automatically if you rename or add teams):

   - `cyber: defender asset resolved → 'SC_OPS' (Watchtower)`
   - `A7: uplink-jam target picked dynamically → 'Blue Bravo' (team_id=…, config_freq=… MHz)`
   - `capture: started — 2 blue team(s), dwell=750s, quota=2/team, window=[6000, 9000]s`
   - `capture: stored intercept for '<team>' (1/2, rx=… MHz, t≈…s)` — repeats per intercept.
   - `capture: complete — 4 intercept(s) across 2 team(s)` (or window-expiry if the quota wasn't met).
   - `replay: armed 8 burst(s) between t=9500s and t=14500s — times=[…]`
   - `replay: t=…s burst 1/8 → '<team>' @ … MHz (sha1=…)` — repeats per burst.
   - `jamming: scheduled 15 pulse(s) for 'Uplink Pulse Jam (<team>)' …`
   - `Downlink Jam ON (AOI Pass 1)` / `OFF` — fires once per AOI pass.

5. **Forensic artefacts** are saved next to the script when each phase finalises:

   - `cyber_defender_captures.json` — every captured wire, indexed by team.
   - `cyber_defender_replays.json` — every replay attempt (sim time, target team, sha1 of payload, success flag).

   Use these to mark the Phase-2 questions ("how many distinct teams were replayed against?", "roughly what proportion of Blue Bravo's commands failed?").

## Sanity checklist before going live

- [ ] `python -c "import json; json.load(open(r'scenarios/Cyber Defender/cyber_defender.json'))"` returns no error.
- [ ] `admin_get_scenario_events` lists **10** events (6 GPS/Spacecraft for Phase 1, 4 Cyber/Spacecraft for Phase 3).
- [ ] Both blue teams' MQTT clients receive their first Ping within ~30 sim s of start.
- [ ] PHANTOM is visible on the map view from `t=0` (no `visualization.hide`).
- [ ] At `t=1 800 s`, the GPS spoof event fires — operator's GPS lat/lon snaps to the antipode. The defender's orbit-1 descending Hormuz pass (`t ≈ 3 730 s, lat ≈ 26.5° N, lon ≈ 54° E`) lands inside the spoof + jam windows, so the baseline imagery operators take of the AOI is geo-tagged with bogus coordinates if they trust GPS naively.

## Tunables to lock from a dry-run

These constants live at the top of `cyber_defender.py` and need to be tuned on the first dry-run (see spec § 12):

| Constant | Default | Action |
| --- | --- | --- |
| `T_AOI_1` | `11 200 s` | First phase-2b lat-26.5°N pass (≈ orbit-2 ascending, Caribbean / Miami arc). Find the actual sim-time from the GPS trace; patch in. |
| `T_AOI_2` | `13 700 s` | Second phase-2b lat-26.5°N pass (≈ orbit-2 descending, Mediterranean / Madrid arc). Patch from the GPS trace. |
| `UPLINK_JAM_ON` | `8.0 s` | Tune up if the observed Blue Bravo command-success rate during the jam window is too high (>85 %). |
| `UPLINK_JAM_PERIOD` | `40.0 s` | Adjust to keep the duty cycle ≈ 20 % unless dry-run shows a different fraction works better. |

The two GPS Cyber-event payloads (`A9` Ping `State`, `A10` GPS position) both avoid `{`, `}`, `"` to dodge the JSON-parsing bug; do not edit those payloads without re-checking the constraint.

## Extending to 8 blue teams

Add the extra entries to `teams[]` in the JSON (use the *Orbital Sentinel* roster as a template — the colours and frequencies are spread far enough apart to keep the EM-sensor view legible). **No Python changes are required.** `cyber_defender.py` discovers everything from the config + admin API:

- `scenario.enemy_teams` enumerates blue teams from the JSON.
- `scenario.live_enemy_frequencies_by_team()` admin-queries each team's live frequency at fire-time.
- The per-team capture quota auto-bumps from 2 → 3 once `len(enemy_teams) > 2`.
- The pulsed uplink-jam target is `scenario.enemy_teams[-1]` — the last enemy team in config order. Edit the index in `cyber_defender.py` if you want a different team singled out.

If you reorder or rename teams, the script logs the picked target on startup (`A7: uplink-jam target picked dynamically → '…'`) so you can confirm the choice before the simulation kicks off. **Update the matching question answer in `cyber_defender.json` to reflect the picked team** — the Phase-2 "Which blue team was singled out?" question currently encodes the answer as the last team's name.

## See also

- [`cyber_defender.spec.md`](cyber_defender.spec.md) — full scenario design (orbit choice, ground-station coverage, attack rationale, question framework).
- [`docs/scenarios/events.md`](../../docs/scenarios/events.md) — `Spacecraft`, `GPS`, `Cyber` event reference.
- [`docs/scenarios/ground-stations.md`](../../docs/scenarios/ground-stations.md) — full ground-station catalog.
- [`docs/reference/packet-formats.md`](../../docs/reference/packet-formats.md) — APID catalog (used by the Cyber tamper events).
- [`src/cyber_replay.py`](../../src/cyber_replay.py) — `MultiTeamCaptureSequence`, `MultiTeamReplaySequence`.
- [`src/jamming.py`](../../src/jamming.py) — `schedule_jammer_pulses`.
