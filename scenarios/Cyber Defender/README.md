# Cyber Defender — instructor brief

A one-hour workshop that walks operators through eight different cyber effects against a single MEO defender. Two duty-crew teams (Blue Alpha, Blue Bravo) share the spacecraft *Watchtower*; a scripted rogue (*PHANTOM*) flies in the same orbit and drives every active attack from `cyber_defender.py`.

The full design rationale lives in [`cyber_defender.spec.md`](cyber_defender.spec.md). This README is the launch checklist.

## Mission narrative (one paragraph)

The **Maritime Cyber Watch** programme operates *Watchtower*, an MEO imagery / SIGINT bird, over the Hormuz / Arabian Sea shipping corridor. Multiple shifts (one duty-crew per blue team) command the same spacecraft from their own consoles. Sister-state intelligence has flagged a co-orbital satellite, callsign **PHANTOM**, as a potential cyber threat. Each duty crew must keep the link healthy from their own console, recognise each cyber effect as it appears, choose the right mitigation, and submit a forensic after-action report.

## Phase plan

Sim speed is **1×** — wall-clock minutes match simulation seconds. With **ν = −90°** and times shifted **−9 min** from the old ν=−110° schedule, most scripted threats finish by **~36 min**; the rest of the hour is wind-down and scoring. **Re-validate** pass times on your first dry-run.

Epoch **`2026/02/02 08:00 UTC`** — Dubai / Hormuz phasing is **~9 min earlier** than the prior orbit block; **run a trace** to confirm. Visibility (indicative): Paris **0–2 000 s**, Dubai **370–3 340 s**, Singapore **2 000–4 900 s**.

| Phase | Wall | Sim time | Theme |
| --- | --- | --- | --- |
| 0 — Familiarisation | 00:00 – ~00:02 | `0 – ~120 s` | Paris pass; connect. **~30 s** GPS spoofing OFF (bootstrap). **~2 min** **solar-array degradation**. |
| 1 — Passive cyber | ~00:02 – ~00:24 | `~120 – ~1 440 s` | Hormuz GPS spoof/jam/fault from ~**18 min**; AOI jam `T_AOI_1 ≈ 1 260 s`; storage ~**24 min**. Capture **`60 – 1 260 s`**. |
| 2a — Rogue capture | ~00:01 – ~00:21 | `~60 – ~1 260 s` | **First half** — PHANTOM cycles every blue team's frequency (silent intercept pool). |
| 2b — Rogue replay & jam | ~00:21 – ~00:34 | `~1 280 – ~2 060 s` | **Second half** — random replay of captured wires; pulsed uplink jam; second AOI jam `T_AOI_2 ≈ 2 010 s`. |
| 3 — Compound | ~00:34 – ~00:36 | `~2 045 – ~2 160 s` | Cyber tamper + reaction wheel + battery pile-on. |
| 4 — Wind-down | ~00:36 – 01:00 | `~2 160 – 3 600 s` | Attacks stop. Teams finalise answers. `simulation.end_time` stops the hour at **3 600 s**. |

At **1×**, less than one full orbit elapses in an hour — pacing prioritises cyber teaching over electro-optical framing.

## Launch sequence

1. **Open** `cyber_defender.json` in Studio (or load via the admin tooling). Verify `simulation.speed = 1.0`, `simulation.end_time = 3600`, `simulation.epoch` matches **`2026/02/02 08:00:00`**, `universe.gps = true`, and that the six ground stations (**Paris, Dubai, Singapore, Sydney, Easter Island, Miami**) are present in that order.
2. **Start the rogue agent** from the project root:

   ```powershell
   python "scenarios/Cyber Defender/cyber_defender.py"
   ```

   It will prompt for the game name and admin password (saved between runs in `.space-range-defaults`). Connect each blue team's Operator UI separately (Blue Alpha, Blue Bravo).

3. **Start the simulation** in Studio. The script blocks in `loop_forever` and ticks the capture / replay state machines on every Session message it receives.

4. **Watch for these log markers** in the rogue's terminal — they confirm each phase started (team names below are taken straight from the config — they update automatically if you rename or add teams):

   - `cyber: defender asset resolved → 'SC_OPS' (Watchtower)`
   - `A7: uplink-jam target picked dynamically → 'Blue Bravo' (team_id=…, config_freq=… MHz)`
   - `capture: started — 2 blue team(s), dwell=…s, quota=2/team, window=[60, 1260]s`
   - `capture: stored intercept for '<team>' (1/2, rx=… MHz, t≈…s)` — repeats per intercept.
   - `capture: complete — 4 intercept(s) across 2 team(s)` (or window-expiry if the quota wasn't met).
   - `replay: armed 8 burst(s) between t=1820s and t=2600s — times=[…]`
   - `replay: t=…s burst 1/8 → '<team>' @ … MHz (sha1=…)` — repeats per burst.
   - `jamming: scheduled … pulse pair(s) for 'Uplink Pulse Jam (<team>)' …`
   - `Downlink Jam ON (AOI Pass 1)` / `OFF` — fires once per AOI pass.

5. **Forensic artefacts** are saved next to the script when each phase finalises:

   - `cyber_defender_captures.json` — every captured wire, indexed by team.
   - `cyber_defender_replays.json` — every replay attempt (sim time, target team, sha1 of payload, success flag).

   Use these to mark the Phase-2 questions ("how many distinct teams were replayed against?", "roughly what proportion of Blue Bravo's commands failed?").

## Sanity checklist before going live

- [ ] `python -c "import json; json.load(open(r'scenarios/Cyber Defender/cyber_defender.json'))"` returns no error.
- [ ] `admin_get_scenario_events` lists **12** events (8 GPS/Spacecraft for Phase 1, 4 Cyber/Spacecraft for Phase 3).
- [ ] Both blue teams' MQTT clients receive their first Ping within ~30 sim s of start.
- [ ] `SC_ROGUE` has `visualization.hide: true` (rogue not on default map — EM sensor for attribution).
- [ ] GPS spoof region enables at **`t ≈ 1 080 s`** (ν=−90° schedule; ~**18 min**); jam **`~1 110–1 380 s`**, hard fault **`~1 220 s`**. **`T_AOI_1 ≈ 1 260 s`** — imagery downlink jam overlaps the environmental GPS attack window by design (**dry-run** to confirm).

## Tunables to lock from a dry-run

These constants live at the top of `cyber_defender.py` and need to be tuned on the first dry-run (see spec § 12):

| Constant | Default | Action |
| --- | --- | --- |
| `T_AOI_1` | `1 260 s` | Hormuz-centred broadcast jam — patch from GPS trace if your integrator differs. |
| `T_AOI_2` | `2 010 s` | Second AOI jam (Dubai + Singapore overlap region) — patch from trace. |
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
