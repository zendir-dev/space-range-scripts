# Cyber Defender — Scenario Specification

> **Status**: design draft — pre-implementation.
> **Audience**: scenario author (JSON), Python-script author (rogue agent), instructor.
> **Sibling references**: `scenarios/Orbital Sentinel/orbital_sentinel.json` & `orbital_sentinel.py` for the closest existing template; this scenario reuses that shape (multiple blue teams sharing one collection + scripted Red team).

---

## 1. One-line pitch

A small fleet of **blue teams** share one defender spacecraft over a busy maritime corridor while the **environment** (scenario events) and a **co-orbital rogue spacecraft** (scripted Python) progressively introduce a curated catalogue of cyber effects. Teams must detect, attribute, and (where possible) mitigate each effect — then answer forensic questions for scoring.

---

## 2. Learning objectives

By the end of the workshop, an operator should be able to:

1. **Recognise** the telemetry signatures of: GPS spoofing, GPS jamming, uplink jamming, downlink jamming, command injection (telemetry tamper), replay attack, sensor fault, storage corruption.
2. **Distinguish** an *environmental* effect (everyone sees it) from a *targeted* effect aimed at one team's RF identity (only that team sees it).
3. **Pick** the right mitigation per attack — frequency hop, key rotation, component reset, ephemeris rollback, ignore-and-wait.
4. **Attribute** effects to a candidate adversary using an EM sensor + camera (the Rogue is visually identifiable, like in *Orbital Sentinel*).

---

## 3. Time budget

| Quantity | Value |
| --- | --- |
| Wall-clock duration | **60 minutes** |
| Sim speed | **5×** (`simulation.speed: 5.0`) |
| Sim seconds elapsed | **18 000 s** ≈ **5 sim hours** |
| Useful active window | **~16 500 s** (drop first ~750 s for connect/intro and last ~750 s for debrief) |

### Phase plan (sim-time anchored)

| Phase | Wall | Sim time | Theme |
| --- | --- | --- | --- |
| **0 — Familiarisation** | 00:00 – 00:05 | `0 – 1 500 s` | Connect, baseline ops, image a target, see the rogue on map. |
| **1 — Passive cyber** | 00:05 – 00:20 | `1 500 – 6 000 s` | Environment-driven effects: GPS spoof/jam, sensor fault, storage corruption. |
| **2a — Rogue capture** | 00:20 – 00:30 | `6 000 – 9 000 s` | Rogue cycles through every blue team's frequency, recording foreign uplinks. |
| **2b — Rogue replay & jam** | 00:30 – 00:50 | `9 000 – 15 000 s` | Replay captured commands across all blue freqs at random; **light pulsed** uplink jam on one team; **broadcast** downlink jam centred on each AOI overhead pass. |
| **3 — Compound** | 00:50 – 00:55 | `15 000 – 16 500 s` | Cyber telemetry tampering on live components + sustained jam + component faults. |
| **4 — Wind-down** | 00:55 – 01:00 | `16 500 – 18 000 s` | Attacks stop. Teams finalise answers. |

> Phases 1 and 2 deliberately **overlap visually but separate causally**: Phase 1 is global (everyone is affected); Phase 2 is targeted by the rogue spacecraft. Asking teams to attribute who-caused-what is the core of the assessment. Phase 2 is split into a **listen-only first half** and a **broadcast second half** so capture has time to populate before replay.

---

## 4. Universe & orbit

### 4.1 Orbit choice — MEO, slightly elliptical

```text
SMA           = 10 000 km   (alt ~3 622 km, classified MEO)
Eccentricity  = 0.015
Inclination   = 37.5°
RAAN          = 242°
ArgPerigee    = 0°
TrueAnomaly   = 0° (defender) / 0.01° (rogue — co-located so PHANTOM is in-frame next to Watchtower)
```

| Property | Value | Rationale |
| --- | --- | --- |
| Orbital period | **~2.77 h** | `T = 2π√(a³/μ)` with `a = 10 000 km` ≈ 9 952 s. |
| Orbits per workshop | **~1.8** | 5 sim h / 2.77 h. Enough to see ~3 ground passes per station, not so few that the orbit is a curiosity. |
| Inclination | 37.5° | Tuned (with RAAN = 242°) so the ground track passes Madrid → Doha → Singapore → Perth → Auckland → Miami within visibility, while still crossing directly over the Hormuz / Arabian Sea AOI on the orbit-1 descending leg. |
| RAAN | 242° | Phase-aligns the ground track with the chosen ground-station chain so coverage is ~100% throughout the workshop. |
| Eccentricity | 0.015 | Light variation in altitude makes apoapsis/periapsis a worthwhile telemetry question without distorting the timeline. |
| Rogue placement | `ν₀ = 0.01°` | Same-orbit, essentially co-located with the defender — keeps PHANTOM visible in the same camera/3D viewport so teams can answer the call-sign question and watch the rogue's behaviour live. |

> **Why not LEO?** Three orbits in 5 sim hours is fine for a flight-ops scenario, but cyber effects (replay capture, jamming windows) want **longer dwell** over the AOI. MEO gives ~12-minute uninterrupted contacts versus ~5-minute LEO passes — much friendlier for scripted multi-step attacks.

> **Why not GEO?** GEO is *too* easy: continuous visibility, no pass timing, events become dimensionless in time. We want some pass-cadence so teams notice "the jamming happens **only** over Dubai".

### 4.2 Universe block

```json
"universe": {
  "atmosphere": false,
  "magnetosphere": true,
  "gps": true,
  "cloud_opacity": 0.85,
  "cloud_contrast": 2.5,
  "ambient_light": 0.25
}
```

- `gps: true` is **mandatory** — GPS spoofing and GPS jamming events both rely on the global GPS subsystem (see `docs/scenarios/events.md` § GPS events).

### 4.3 Ground stations

A **globally-distributed, US/EU/5-Eyes-aligned set** with near-100% coverage across the orbit. Full city catalog: `docs/scenarios/ground-stations.md`.

```json
"ground_stations": {
  "locations": [
    "Madrid", "Doha", "Singapore", "Perth",
    "Auckland", "Miami"
  ],
  "min_elevation": 5,
  "max_range": 0,
  "scale": 100
}
```

Why this set (`min_elevation: 5°` adds a realistic horizon mask so passes feel finite — important for jamming windows that bracket a single contact):

| Station | Role | Alignment |
| --- | --- | --- |
| **Madrid** | West-Eurasia gateway. Same station as *Orbital Sentinel* — operators familiar with the prior workshop recognise it. | Spain (NATO / EU). |
| **Doha** | AOI primary. Hosts US CENTCOM forward HQ; ideal narrative fit for the Maritime Cyber Watch programme. | Qatar (US partner). |
| **Singapore** | Indo-Pacific equatorial. | US partner; hosts US Navy Logistics Group Western Pacific. |
| **Perth** | Southern hemisphere / Indian Ocean. | Australia (5 Eyes; long-standing US/UK signals-intel cooperation). |
| **Auckland** | SW Pacific + southern leg of the orbit. | New Zealand (5 Eyes). |
| **Miami** | Western Atlantic / Caribbean. **Picks up the orbit-2 ascending lat-26.5° pass** which is one of the AOI-band imaging passes the rogue jams. | US east coast. |

#### 4.3.1 Coverage check

At MEO (`alt ≈ 3 622 km`) with `min_elevation = 5°`, each station's visibility footprint has a central-angle radius of:

```text
Δ = arccos(R / r · cos ε) − ε  ≈  45.4°
```

(`R = 6 378 km`, `r = 10 000 km`, `ε = 5°`). Footprint longitudes (the spacecraft's `±37.5°` latitude range fits inside every station's latitude visibility window):

```text
Madrid    [ -49°,  +37°]
Doha      [  +7°,  +96°]
Singapore [ +59°, +149°]
Perth     [ +71°, +161°]
Auckland  [+130°, -140°]   (wraps the antimeridian)
Miami     [-125°,  -35°]
```

The orbit's RAAN (242°) and inclination (37.5°) are tuned so the ground track threads this chain with no large coverage gaps over the workshop window. Honolulu was originally in the catalogue but the new ground track stays north of its visibility cone for the orbits this scenario covers, so it has been removed. **If you change the orbit, re-check coverage against the catalog in `docs/scenarios/ground-stations.md` before the dry-run.**

#### 4.3.2 Cities deliberately not used

| City | Reason omitted |
| --- | --- |
| Karachi | Pakistan's strategic posture has drifted toward CPEC/BRI; awkward optics for a US/EU-framed exercise. |
| Colombo | Hambantota lease and Sri Lanka's tilt toward BRI. |
| Cape Town | South Africa is a BRICS member and has hosted Russia/China naval drills. |
| Dubai | Geographically redundant with Doha (~4° apart) — Doha is the cleaner CENTCOM-aligned pick. |

Instructors who want to swap any of these back in (e.g. adding Dubai for a narrative reason) can do so without changing coverage materially — the city catalog in `docs/scenarios/ground-stations.md` lists every available city.

---

## 5. Mission narrative

> The **Maritime Cyber Watch** programme operates a single MEO defender, *Watchtower*, providing imagery and SIGINT across the Hormuz / Arabian Sea shipping corridor. Operations are split across **multiple shifts** — each blue team is a duty crew with its own RF identity (frequency, key, password) commanding the same shared spacecraft. Sister-state intelligence has flagged a co-orbital satellite, callsign **PHANTOM**, as a potential cyber threat. The exercise begins with nominal ops; over the workshop, both the Earth-side environment and PHANTOM escalate hostile activity. Each duty crew must keep the link healthy from their own console and file a forensic after-action report.

This narrative drives:

- One clear AOI for imagery in Phase 0.
- A reason to keep the EM sensor on (used for Phase 2 attribution).
- A reason to point the camera at PHANTOM when the rogue gets close (call-sign question, mirroring *Orbital Sentinel*'s `RECON` reveal).
- A reason for **multiple parallel teams** even though they share a spacecraft ("duty crews"), which fits how *Orbital Sentinel* organises its eight blue teams.

> **Naming**: `Watchtower` (defender SC) and `PHANTOM` (rogue SC) replace the earlier "Argus" placeholder used in spec drafts. Final names are at the instructor's discretion — change the `name` field on the assets and the `Text` callsign on the rogue without any other code changes.

---

## 6. Teams

### 6.1 Team structure

Mirroring *Orbital Sentinel*: **N blue duty-crew teams** all share one spacecraft via the same collection ID, plus **one Rogue team** that owns the adversary spacecraft and is driven by the Python script.

We **start with `N = 2` blue teams** to keep the first end-to-end test simple, but the JSON should be structured so growing to 8 (matching *Orbital Sentinel*) is a copy-paste of additional team entries — nothing else has to change.

| Team | Role | Driver | `collection` |
| --- | --- | --- | --- |
| Blue Alpha | Duty crew #1 | Human (Operator UI) | `Main` |
| Blue Bravo | Duty crew #2 | Human (Operator UI) | `Main` |
| _… up to Blue Hotel for 8-team mode_ | | | |
| Rogue | Adversary (`PHANTOM` callsign) | **Scripted** (`cyber_defender.py`) | `Rogue` |

### 6.2 Why all blue teams share the spacecraft

This is the *Orbital Sentinel* pattern verbatim: every entry in `teams[]` whose `collection` is `Main` references the same spacecraft (`SC_OPS`). Each team still gets its own:

- **Frequency** — for uplink/downlink RF identity (the rogue can target each separately).
- **Key** — Caesar key applied to ciphertext (so each team's traffic is distinguishable on-air).
- **Password** — XOR layer on MQTT.

This means the rogue's replay attack has to **target a specific team's frequency** to be useful — a blanket replay across the wrong frequency is ineffective. That's exactly the dynamic we want to teach.

### 6.3 Concrete starting roster (placeholders — finalise on implementation)

```json
"teams": [
  { "enabled": true, "id": 100412, "password": "AL9XQ2", "name": "Blue Alpha",
    "key":  73, "frequency": 612, "collection": "Main", "color": "#1E90FF" },
  { "enabled": true, "id": 100413, "password": "BR4MK7", "name": "Blue Bravo",
    "key": 119, "frequency": 745, "collection": "Main", "color": "#4FC3F7" },
  { "enabled": true, "id": 200733, "password": "PH7K1P", "name": "Rogue",
    "key":  11, "frequency": 905, "collection": "Rogue", "color": "#FF1744" }
]
```

Frequency choices stay **distinct** so jamming/replay targets are unambiguous in EM-sensor telemetry. When extending to 8 blues, pick frequencies spread across the same band to mimic *Orbital Sentinel*.

---

## 7. Spacecraft

### 7.1 `SC_OPS` — *Watchtower* (defender) — components

Mandatory canonical 6 (Solar Panel, Battery, Computer, Receiver, Transmitter, Storage) plus payload:

| Component | Why | Adds APID |
| --- | --- | --- |
| `Camera` | Imagery for AOI questions + visual ID of PHANTOM. | 303 (CCD) |
| `EM Sensor` | Required for Phase 2 attribution (rogue's TX frequency). | 302 |
| `GPS Sensor` | Target of Phase 1 spoofing/jamming/sensor-fault. | 301 |
| `Magnetometer` | Cross-check GPS spoof against B-field. | 300 |
| `Reaction Wheels` | Pointing for camera/EM. | 401 |

The APID column matters for Phase 3 telemetry tampering (§ 9, A9-A10) — only APIDs whose underlying components exist on `SC_OPS` will actually be emitted and therefore be patchable.

`controller`:

```json
{
  "safe_fraction": 0.1,
  "capture_tax": 0.001,
  "downlink_tax": 0.005,
  "ping_interval": 20.0,
  "reset_interval": 60.0,
  "jamming_multiplier": 100.0,
  "enable_rpo": false,
  "enable_intercept": false
}
```

`enable_intercept: false` on the defender — only **PHANTOM** records intercepts. This keeps the defender's downlink free of intercept records and avoids accidental SIGINT-style success from the blue side.

### 7.2 `SC_ROGUE` — *PHANTOM* (rogue) — components

| Component | Why |
| --- | --- |
| `Receiver` (`Antenna Gain: 500`) | Wide-coverage RX so foreign uplink intercepts pile up quickly (matches Orbital Sentinel's Recon). |
| `Transmitter` | For replay-attack on-air re-transmission. |
| `Jammer` (`Power: 100`, `Antenna Gain: 15`, `Lookup: "RFPattern.csv"`) | Uplink/downlink jamming. |
| `Computer`, `External Force Torque`, `Battery`, `Solar Panel` | Standard support. |
| `Text` (`"PHANTOM"`) | Visual ID — the call-sign question's answer. |

`controller`:

```json
{
  "safe_fraction": 0.05,
  "capture_tax": 0.001,
  "downlink_tax": 0.005,
  "ping_interval": 20.0,
  "reset_interval": 60.0,
  "jamming_multiplier": 100.0,
  "enable_rpo": false,
  "enable_intercept": true
}
```

> `enable_intercept: true` is **required** for the Python intercept-capture sequence to receive Format 3 records (see `src/cyber_replay.py`).

### 7.3 Visual concealment

Match *Orbital Sentinel*: `visualization.hide` is **not** set — PHANTOM is visible from the start so teams can train the camera and EM sensor on it. Make the chassis distinct (e.g. `MRO` blueprint, `scale: 10`) and put the `Text` "PHANTOM" on the body so a Camera capture answers the call-sign question.

---

## 8. Ground objects (AOI dressing)

Light, low-effort: enough vessels to make Phase 0 imagery meaningful but **fewer** than *Orbital Sentinel* because cyber effects are the focus, not counting ships. Roughly:

- 4-6 vessels in Hormuz Strait (`lat ≈ 26°, lon ≈ 56°`), distinct colours.
- 2-3 "shadow" vessels offset by a few degrees longitude — used by the GPS-spoofing question (the spoof region puts the apparent position over the wrong cluster).

This is dressing only; the ground-truth questions are about **cyber**, not counter-piracy.

---

## 9. Attack catalogue

> Format: each attack lists **type** (passive event vs. active script), **sim-time window**, **mechanism** (the JSON event or Python call), and the **observable signature** the defender should recognise.

### Phase 1 — Passive (events JSON)

#### A1. GPS Spoofing — Hormuz region

- **Type**: passive (`Type: "GPS"`, `Data.Type: "Spoofing"`).
- **Window**: `1 800 s → 6 200 s` (paired enable/disable events).
- **Mechanism**: spoof a ~200 km-radius volume centred on `lat 26.5°, lon 56.5°, alt 4 000 km` — when the defender's GPS receiver is inside the sphere, position is reported at `lat -26.5°, lon -123.5°` (mirror point in the South Pacific).
- **Signature**: GPS lat/lon "jumps" while velocity vector and B-field are unchanged. APID 301 (`GPS`) reports drift, APID 300 (`Magnetometer`) doesn't.
- **Mitigation**: ephemeris rollback (or trust last good fix until exit).

#### A2. GPS Jamming — ground source over AOI

- **Type**: passive (`Type: "GPS"`, `Data.Type: "Jamming"`, `Action: "add"`).
- **Window**: `2 400 s → 5 800 s` (paired add/remove with `Index: "0"`).
- **Mechanism**: ground jammer at `lat 26°, lon 56°, alt 50 km`, `ERP: 250 000 W`.
- **Signature**: GPS solutions go unhealthy / no-fix when over the AOI.
- **Mitigation**: dead-reckon; cross-check with magnetometer (still healthy).

#### A3. Storage corruption

- **Type**: passive (`Type: "Spacecraft"`, `Target: "Storage"`).
- **Window**: fires once at `4 200 s`; effect persists.
- **Mechanism**: `Data: { "Corruption Fraction": 0.1, "Corruption Intensity": 0.2 }`.
- **Signature**: downlinked imagery starts containing scrambled bytes; APID 503 (`Storage`) reports degradation.
- **Mitigation**: `reset` the Storage component.

#### A4. GPS Sensor fault (sustained / hard fault)

- **Type**: passive (`Type: "Spacecraft"`, `Target: "GPS Sensor"`).
- **Window**: fires at `5 400 s`; cleared by `reset` from operator.
- **Mechanism**: `Data: { "Fault State": 4 }`.
- **Signature**: APID 301 stops emitting fresh fixes / sticks at last value with `fault_state != 0`.
- **Mitigation**: `reset` the `GPS Sensor` component. Distinguishes a hardware fault from A1/A2 environmental denial.

### Phase 2a — Listen across every blue team (Python rogue script)

#### A5. Multi-team replay capture

- **Type**: active (extends `InterceptReplaySequence` from `src/cyber_replay.py`).
- **Window**: `6 000 s → 9 000 s`.
- **Mechanism** (script-level — *new* helper required, see § 11.2):
  1. Resolve **every** blue team's RF via `rf_catalog.get_all_frequencies(admin)` — gives one snapshot per team.
  2. **Cycle** through them on a fixed dwell, e.g. `~600 s` per team (5 sim minutes, ~1 min wall) so a 2-team start covers each twice in the 3 000 s capture window. With 8 teams, drop the dwell to ~360 s.
  3. For each dwell, `tune_ground` to that team's `(freq, key, bandwidth)` and keep a **per-team capture pool** indexed by `team_id`.
  4. Stop the cycle once **every blue team has at least `X = 2` foreign intercepts** captured (or the window expires). Save the pools as JSON for forensics.
- **Signature**: nothing visible to the defender — captures are silent.
- **Defender training point**: this only succeeds because uplinks are unauthenticated ciphertext. Operators who rotate `encryption` mid-window invalidate any captured ciphertext for *their* team going forward.

> Implementation detail: the existing `InterceptReplaySequence.begin_capture(listen_rf, foreign_count)` is a single-frequency capture. Extend with a thin wrapper `MultiTeamCaptureSequence` that owns a `dict[team_id, list[CapturedWire]]` plus a tuner-cycle loop driven from `tick(sim_time)`. Reuse `decode_downlink_mqtt_payload` + `parse_uplink_intercept_record`.

### Phase 2b — Replay & jam across every blue team (Python rogue script)

#### A6. Random multi-team replay

- **Type**: active (re-broadcast captured wire bytes from A5).
- **Window**: `9 500 s → 14 500 s`.
- **Mechanism**:
  1. Build a flat list of `(team_id, captured_wire)` pairs from the per-team pools captured in A5.
  2. Schedule **N replay bursts** (`N ≈ 6-10`) at random sim-times spread across the window.
  3. At each scheduled time, **pick a random capture**, **tune the rogue's ground TX to that team's frequency**, and `replay_transmit_bytes` the stored payload.
  4. Log every replay as `{sim_time, team_id, freq_mhz, payload_sha1}` for the post-exercise forensic question ("how many distinct teams were replayed against?").
- **Signature**: spurious uplink-traffic spike on EM sensor at a blue team's RX frequency without a matching ground-station transmission; possible duplicate `command_received` events.
- **Mitigation**: rotate Caesar key (`encryption`) — invalidates captured ciphertext for that team.

> Implementation detail: a second helper `MultiTeamReplaySequence` schedules replay events through the existing `EventScheduler`. Replay events arm at creation but **fire on `tick(sim_time)`**, identical to the single-team `schedule_replay_at` pattern — just iterated. Every replay event resolves the **current** team frequency live via `live_enemy_frequencies`-style lookup (key may have been rotated mid-window, in which case the replay simply fails to decode on-board, which is itself observable behaviour).

#### A7. Light pulsed uplink jamming (one blue team)

- **Type**: active (`commands.jammer_start` / `jammer_stop` pulsed against one blue team's freq).
- **Window**: `10 200 s → 10 800 s` (~600 s = ~2 wall minutes, covers one ground pass).
- **Design intent**: **light** — we want a *fraction* of the targeted team's commands to fail, not all of them. The pulse + low-power combination lands ~15-25% of the team's commands inside an ON window where the jammer drowns the uplink, while the rest pass normally. This produces a much more realistic "intermittent comms" symptom than continuous jamming and gives operators something to *measure* (success rate) rather than just notice.
- **Mechanism**: a Python helper `schedule_jammer_pulses(...)` (see § 11.2) emits an alternating sequence of `jammer_start` / `jammer_stop` events at low power across the window:

  ```python
  scheduler.add_event("Point Jammer to Watchtower",
      trigger_time=10_190.0,
      **commands.guidance_spacecraft("Jammer", "SC_OPS"))
  schedule_jammer_pulses(scheduler,
      name="Uplink Pulse Jam (Blue Bravo)",
      start=10_200.0, end=10_800.0,
      on_seconds=8.0, period_seconds=40.0,    # 20% duty cycle
      frequencies_resolver=lambda: [scenario.team_frequency("Blue Bravo")],
      power=0.8)                              # well below A8/A11's level
  ```

  Frequencies are resolved live (per pulse) so a key/freq rotation by Blue Bravo mid-window changes the target without rewriting the schedule. The script picks **one team** to single out so the question "which team was uplink-jammed?" has a concrete answer.
- **Signature**: that team's ping payloads start showing **gaps** in the `Commands` list (some sent commands never appear as executed). Success rate during the window is roughly `1 − duty_cycle` ≈ 75-85%. Other blue teams continue normally.
- **Mitigation**: `telemetry` frequency hop (from ground) **or** `encryption` rotate (from spacecraft) — both move the team off the jammed channel for subsequent commands.
- **Forensic question target**: "Roughly what proportion of Blue Bravo's commands failed during the jam window?" — design tolerance ±10 pp.

#### A8. Downlink jamming over AOI imaging Pass #1

- **Type**: active (broadcast jammer across all blue freqs, fired during an AOI overhead pass).
- **Window**: **`T_AOI_1 ± 90 s`** (~180 s total) — placeholder `T_AOI_1 ≈ 11 200 s` (orbit-2 ascending pass through the lat-26.5° band, longitude ≈ Caribbean/Miami arc), **lock the exact value from a dry-run** (see note below).
- **Design intent**: the *narrative* effect — "you can't downlink your imagery from this pass". Teams are most likely to be capturing during AOI overhead, so jamming the downlink at exactly that moment makes the imagery they want most expensive to retrieve. They have to wait for a non-AOI pass over a different ground station, or hop frequency.
- **Mechanism**:

  ```python
  scheduler.add_event("Point Jammer to Watchtower",
      trigger_time=T_AOI_1 - 100.0,
      **commands.guidance_spacecraft("Jammer", "SC_OPS"))
  scheduler.add_event("Downlink Jam ON (AOI Pass 1)",
      trigger_time=T_AOI_1 - 90.0, pre_trigger=live_jammer_args,
      **commands.jammer_start(scenario.enemy_fallback_freqs, power=3.0))
  scheduler.add_event("Downlink Jam OFF",
      trigger_time=T_AOI_1 + 90.0, **commands.jammer_stop())
  ```

  Frequency list = **every** blue team's frequency. Power `3.0 W` (no pulsing — this one *is* meant to be saturating, because we want a clean, attributable failure for the question).
- **Signature**: telemetry stops arriving for **all** blue teams during the pass; ground-station SNR view drops below ~15 dB; the spacecraft itself reports healthy on the next non-AOI pass. Distinguishes a *broadcast* jam (A8) from a *targeted* one (A7).
- **Mitigation**: frequency hop via `telemetry` for each team independently before the next AOI pass.
- **Forensic question target**: "During which imaging pass did downlink fail?" / "Which ground station(s) saw the jammed downlink?" — both answers depend on `T_AOI_1`'s actual value once the orbit is dry-run.

> **Locking AOI pass times**: with `SMA = 10 000 km, e = 0.015, i = 37.5°, RAAN = 242°, ω = 0°, ν₀ = 0°` and the `2026/02/02 12:00 UTC` epoch, the analytic geometry puts the orbit-1 descending lat-26.5° pass at `t ≈ 3 730 s, lon ≈ 54° E` (≈ Hormuz, **phase 1** — landing inside the GPS-spoof / GPS-jam windows so operators take a baseline Hormuz image while their GPS is being attacked), the orbit-2 ascending pass at `t ≈ 11 200 s, lon ≈ -80° E` (Caribbean / Miami arc), and the orbit-2 descending pass at `t ≈ 13 700 s, lon ≈ 13° E` (Mediterranean / Madrid arc). The phase-2b jams (A8/A11) target the two orbit-2 passes — both are in the same lat-26.5° imaging band as Hormuz even though they cross different longitudes. Exact sim-times still depend on integrator drift, so **run the JSON once, watch `admin_query_data` for the spacecraft's GPS lat/lon, and capture the two AOI overhead times.** Patch them into `cyber_defender.py` as `T_AOI_1`, `T_AOI_2` constants. Until then, leave the placeholders (`11 200 s`, `13 700 s`) and treat them as approximate.

#### A11. Downlink jamming over AOI imaging Pass #2

- **Type**: active (same mechanism as A8, second AOI overhead).
- **Window**: **`T_AOI_2 ± 90 s`** — placeholder `T_AOI_2 ≈ 13 700 s` (the orbit-2 descending lat-26.5° pass over the Mediterranean / Madrid arc, ~2 500 s after `T_AOI_1`), again **lock from dry-run**.
- **Design intent**: a second hit on the *same* lat-26.5° imaging band but on the descending leg — and over a different ground station 2 500 s later. Lets teams realise the jam is **band-locked, not station-locked**, and that frequency-hopping after Pass #1 actually pays off if they did it. (Operators have already seen lat-26.5° cleanly during the orbit-1 descending pass over Hormuz at `t ≈ 3 730 s` in phase 1, so they know what an *unjammed* AOI-band downlink should look like.)
- **Mechanism**: identical to A8 — `T_AOI_2 ± 90 s`, all blue freqs, `power=3.0 W`.
- **Signature**: same as A8 but on a different ground station's pass. Teams who hopped frequency after Pass #1 should see either reduced impact (rogue is jamming the *old* freq) or none (rogue is jamming a freq nobody listens on any more).
- **Mitigation**: confirms the A8 mitigation worked. Otherwise: hop now.
- **Forensic question target**: pairs with A8's question — "Was the second imaging pass also disrupted? At what ground station?"

### Phase 3 — Compound (Cyber events + script)

> **Payload safety**: the scenario JSON loader does not handle `{`, `}`, or `"` inside Cyber-event ASCII payloads (a bug in the JSON-to-internal-string round trip). All ASCII payloads below avoid those characters. For obvious "FLAG" signatures, use `FLAG-<word>` rather than `FLAG{<word>}`. Hex payloads are fine because they're matched character-class.

#### A9. Telemetry tamper — Ping `State` field (APID 100)

- **Type**: passive (`Type: "Cyber"`, `Target: "Spacecraft"`, `Assets: ["SC_OPS"]`).
- **Window**: trigger at `15 200 s`, `Expiry Seconds: 600.0`.
- **Mechanism**:

  ```json
  { "Enabled": true, "Name": "Tamper Ping State", "Time": 15200.0,
    "Type": "Cyber", "Target": "Spacecraft", "Assets": ["SC_OPS"],
    "Data": {
      "APID": 100, "SubType": 0, "Offset Bytes": 2,
      "Payload": "FLAG-OWN", "Encoding": "ascii",
      "Expiry Seconds": 600.0, "Clear On Reset": true
    }
  }
  ```

  Per `docs/reference/packet-formats.md` § Ping packet, byte offset `2` of the user data is the start of the `State` string content (after the 2-byte length prefix). Overwriting `"NOMINAL"` (7 bytes) with `"FLAG-OWN"` (8 bytes — truncated to the 7-byte field) is harmless to the packet length but clearly visible in the operator UI's Ping view.
- **Signature**: `state` field shown in operator UI flips from `NOMINAL` to a garbled / signature string. Ping continues to arrive at expected cadence.
- **Mitigation**: `reset` the `Computer` (overlay clears because of `Clear On Reset: true`).

#### A10. Telemetry tamper — GPS position (APID 301)

- **Type**: passive.
- **Window**: trigger at `15 600 s`, `Expiry Seconds: 600.0`.
- **Mechanism**:

  ```json
  { "Enabled": true, "Name": "Tamper GPS Position", "Time": 15600.0,
    "Type": "Cyber", "Target": "Spacecraft", "Assets": ["SC_OPS"],
    "Data": {
      "APID": 301, "SubType": -1, "Offset Bytes": 0,
      "Payload": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00",
      "Encoding": "hex",
      "Expiry Seconds": 600.0, "Clear On Reset": true
    }
  }
  ```

  Hex payload zeroes out the first 24 bytes of GPS user data — i.e. the position triplet (`Vector3` of three big-endian `float64`s = 24 bytes per `docs/reference/packet-formats.md`). Result: GPS reports the centre of the Earth.
- **Signature**: live GPS plot snaps to `(0, 0, 0)`; magnetometer is unchanged so the team can detect the inconsistency.
- **Mitigation**: `reset` Computer (via `Clear On Reset: true`).
- **Confirm before shipping**: APID 301's user-data byte order against the live XTCE schema. If the position vector is preceded by other fields, shift `Offset Bytes` accordingly. Use `get_packet_schemas` from a dry-run to lock the offset.

#### A12. Reaction-wheel stuck (component fault)

- **Type**: passive (`Type: "Spacecraft"`, `Target: "Reaction Wheels"`).
- **Window**: `15 800 s`.
- **Mechanism**: `Data: { "Stuck Index": 0 }`. Pointing degrades while teams are mitigating telemetry tamper.
- **Signature**: APID 401 (`Reaction Wheels`) reports a stuck axis; pointing drifts.
- **Mitigation**: `reset` `Reaction Wheels`.

#### A13. Battery intermittent connection

- **Type**: passive (`Type: "Spacecraft"`, `Target: "Battery-IntermittentConnectionErrorModel"`).
- **Window**: `16 100 s`.
- **Mechanism**: `Data: { "Intermittent Mean": 1, "Intermittent Std": 2 }` (verbatim from *Orbital Sentinel*).
- **Signature**: APID 200 (`Battery`) state-of-charge reports become noisy / spike.
- **Mitigation**: `reset` `Battery`.

### Phase 4 — Wind-down

`16 500 s` onwards: **no new effects fire**. Operator focus shifts to answering questions and reviewing the EM-sensor capture / camera image of PHANTOM.

---

## 10. Question framework

Aim for **~16-18 questions**, total score `100`, distributed across these sections (mirrors *Orbital Sentinel*'s breakdown style):

| Section | Approx weight | Sample question titles |
| --- | --- | --- |
| Orbital Operations (sanity) | 10 pts | "What is the SC_OPS semi-major axis?", "What is the orbital period?" |
| Environmental Cyber (Phase 1) | 25 pts | "Which AOI was GPS-spoofed?", "Where was the GPS jammer located?", "Which sensor returned a hard fault and at roughly what time?" |
| Adversary Attribution | 25 pts | "What is the rogue spacecraft's call-sign?" (camera), "What frequency does PHANTOM transmit on?" (EM sensor), "Which ground stations saw downlink jamming?" |
| Active Attacks (Phase 2) | 25 pts | "Which blue team(s) had captured uplinks replayed against them?", "What was the minimum SNR observed during the downlink jam?", "Which APID(s) showed tampering in Phase 3?" |
| Mitigations | 15 pts | `select` questions on best response per attack — frequency hop, key rotation, component reset, ephemeris rollback. |

> Question *content* (specific values) should be filled in by the JSON-author after a dry-run, since "minimum SNR" / "exact pass affected" are implementation-time observations, not design-time predictions.

---

## 11. Implementation outline

When this spec is approved, three artefacts get produced (all in this folder):

### 11.1 `cyber_defender.json`

- `simulation`, `universe`, `ground_stations` per §3, §4.
- `teams[]`: 2 blue + 1 Rogue (§ 6.3).
- `assets.space[]`: `SC_OPS`, `SC_ROGUE` (§7).
- `assets.collections[]`: `Main: ["SC_OPS"]`, `Rogue: ["SC_ROGUE"]`.
- `objects.ground[]`: minimal Hormuz cluster (§8).
- `events[]`: A1, A2, A3, A4, A9, A10, A12, A13 — sorted by `Time`.
- `questions[]`: see §10.

### 11.2 `cyber_defender.py`

Mirrors `orbital_sentinel.py` shape but uses the new multi-team helpers:

```python
from src import Scenario, commands, replay, rf_catalog
from src.cyber_replay import MultiTeamCaptureSequence, MultiTeamReplaySequence
                             # ↑ NEW helpers — to be added in src/cyber_replay.py

scenario = Scenario(team_name="Rogue", config_path=_config_path)
scheduler = scenario.scheduler

capture = MultiTeamCaptureSequence(scenario.client,
                                   blue_teams=scenario.enemies,
                                   per_team_quota=2)
replay_seq = MultiTeamReplaySequence(scenario.client,
                                     capture=capture,
                                     burst_count=8,
                                     window=(9_500.0, 14_500.0))

# Phase 2a — capture
scheduler.add_event("Capture: cycle blue teams", trigger_time=6_000.0,
                    pre_trigger=lambda a: capture.start_cycle(),
                    command="noop", args={}, description="...")
scheduler.add_event("Capture: stop", trigger_time=9_000.0,
                    pre_trigger=lambda a: capture.stop_cycle(),
                    command="noop", args={}, description="...")

# Phase 2b — replay across teams (random sim-times within window)
scheduler.add_event("Replay: arm bursts", trigger_time=9_500.0,
                    pre_trigger=lambda a: replay_seq.arm_random_bursts(),
                    command="noop", args={}, description="...")

# A7 / A8 / A11 — jammer events use commands.jammer_start
# with live_enemy_frequencies, identical to orbital_sentinel.py.
```

`Scenario.run` already drives `on_session` → `seq.tick(session["time"])` forwarding; the new helpers expose a matching `tick(sim_time)`.

> **New code additions to `src/cyber_replay.py`**:
>
> - `MultiTeamCaptureSequence` — owns `dict[team_id, list[CapturedWire]]`, cycles `tune_ground` across each team's RF with a configurable dwell.
> - `MultiTeamReplaySequence` — given a capture pool and a `(start, end)` sim window, schedules `N` random replay bursts through the existing `EventScheduler`, each calling `replay_transmit_bytes` on a freshly-resolved team frequency.

> **New code addition to `src/commands.py` (or a small `src/jamming.py`)**:
>
> - `schedule_jammer_pulses(scheduler, *, name, start, end, on_seconds, period_seconds, frequencies_resolver, power)` — emits an alternating `jammer_start` / `jammer_stop` event sequence to produce a duty-cycle pulse over `[start, end]`. `frequencies_resolver` is called per ON pulse so live frequency rotations are picked up without rewriting the schedule. Used by A7 (light uplink jam) and is generally useful for any future "intermittent denial" pattern.

### 11.3 `README.md` (instructor brief)

Short page (single screen) giving the instructor:

- The mission narrative (§5).
- The phase plan (§3) as a bullet list.
- The launch sequence: load JSON, start `cyber_defender.py`, start sim at 5×.
- A sanity checklist (admin `admin_get_scenario_events`, expected event count).

---

## 12. Open design questions

These need a quick decision before implementation kicks off:

1. **Single uplink/downlink frequency per team, or split?** Current shipped scenarios use a single `frequency`. Splitting requires a `set_telemetry` shape change. *Recommendation*: single, consistent with shipped scenarios.
2. **Should A6 (replay) actually mutate spacecraft state?** Depends on whether the on-board envelope rejects replayed ciphertext (timestamp / counter checks). If it accepts, the question "did the replay succeed?" gets a yes/no answer; if not, the question becomes "the replay was observable but ineffective — why?". *Recommendation*: leave both possibilities open in question wording.
3. **Hide PHANTOM until first attack?** *Orbital Sentinel* keeps the rogue visible from `t=0`. Hiding it (`visualization.hide: true`) until ~6 000 s would force operators to use the EM sensor for discovery — more authentic but adds workshop friction. *Recommendation*: keep visible.
4. **A10 GPS tamper offset.** Confirm against XTCE that the GPS user-data begins with the position `Vector3`. If preceded by a header field, shift `Offset Bytes`. *Action*: dry-run, fetch schema, lock offset before ship.
5. **Per-team replay quota X.** `X = 2` per team gives 4 captures with 2 blues → small pool, every replay distinguishable. With 8 blues, raise to `X = 3` for ~24-capture pool. *Recommendation*: parameterise on `len(enemies)`.
6. **AOI overhead times `T_AOI_1` / `T_AOI_2`** (used by A8 and A11). Cannot be predicted exactly from JSON alone — depends on `simulation.epoch`, integrator drift, and Earth rotation. The chosen orbit (`i = 37.5°, RAAN = 242°`) and `2026/02/02 12:00 UTC` epoch put the orbit-1 descending Hormuz pass inside the phase-1 GPS-attack windows (`t ≈ 3 730 s`), and the two phase-2b lat-26.5° passes over the Caribbean / Miami arc (`t ≈ 11 200 s`) and Mediterranean / Madrid arc (`t ≈ 13 700 s`). *Action*: dry-run, log GPS lat/lon, find the two phase-2b sim-times where the ground track is in the lat-26.5°N band, patch into `cyber_defender.py`. Until then, placeholder values `11 200 s` / `13 700 s` are good-enough approximations for sequencing checks.
7. **Uplink-jam duty cycle.** `8 s ON / 32 s OFF` (20%) is the design target for A7 and gives the cleanest "~80% success rate" question. If the jammer's effective radius / power means a single ON pulse only damages a smaller fraction of attempts, raise `on_seconds` (e.g. 12/40 = 30%) after the dry-run. *Action*: tune from observed command-success rate.

---

## 13. References

- `scenarios/Orbital Sentinel/orbital_sentinel.json` — closest template.
- `scenarios/Orbital Sentinel/orbital_sentinel.py` — scripted-rogue pattern.
- `docs/scenarios/events.md` — `Spacecraft`, `GPS`, `Cyber` event reference.
- `docs/scenarios/recipes.md` — Recipe 5 (GPS spoof), Recipe 3 (component fault).
- `docs/scenarios/components.md` — Jammer / Receiver / Transmitter `data` keys.
- `docs/scenarios/ground-stations.md` — full city catalog (added alongside this spec).
- `docs/reference/packet-formats.md` § APID catalog — the full APID table; pick Cyber-event APIDs that match components on `SC_OPS`.
- `src/cyber_replay.py`, `src/replay.py`, `src/rf_catalog.py` — Python glue for active phases.
- `src/commands.py` — `jammer_start` / `jammer_stop` / `guidance_spacecraft`.
- `docs/guides/instructor-admin.md` — admin checklist and live-event push.
