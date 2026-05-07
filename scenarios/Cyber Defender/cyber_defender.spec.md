# Cyber Defender — Scenario Specification

> **Status**: implemented baseline — keep synced with JSON/script edits.
> **Audience**: scenario author (JSON), Python-script author (rogue agent), instructor.
> **Sibling references**: `scenarios/Orbital Sentinel/orbital_sentinel.json` & `orbital_sentinel.py` for the closest existing template; this scenario reuses that shape (multiple blue teams sharing one collection + scripted Red team).

---

## 1. One-line pitch

A small fleet of **blue teams** share one defender spacecraft over a busy maritime corridor while the **environment** (scenario events) and a **co-orbital rogue spacecraft** (scripted Python) progressively introduce a curated catalogue of cyber effects. Teams must detect, attribute, and (where possible) mitigate each effect — then answer forensic questions for scoring.

---

## 2. Learning objectives

By the end of the workshop, an operator should be able to:

1. **Recognise** the telemetry signatures of: GPS spoofing, GPS jamming, uplink jamming, downlink jamming, command injection (telemetry tamper), replay attack, storage capacity fault, reaction-wheel fault, and **solar-array degradation**.
2. **Distinguish** an *environmental* effect (everyone sees it) from a *targeted* effect aimed at one team's RF identity (only that team sees it).
3. **Pick** the right mitigation per attack — frequency hop, key rotation, component reset, ephemeris rollback, ignore-and-wait.
4. **Attribute** effects to a candidate adversary using **EM spectrum** (rogue mesh hidden by default; optional camera only if `visualization.hide` is cleared).

---

## 3. Time budget

| Quantity | Value |
| --- | --- |
| Wall-clock duration | **60 minutes** |
| Sim speed | **1×** (`simulation.speed: 1.0`) — wall-clock seconds match simulation seconds; pacing matches real operator tempo (electro-optical collection is not the learning objective). |
| Sim seconds elapsed | **3 600 s** (one hour); `simulation.end_time` stops the session at the hour mark. |
| Threat-heavy arc | **`0 → ~3 000 s`** (~first **50 minutes**) — passive GPS/fault/inject events plus rogue replay/jam windows complete by **3 000 s**, leaving final minutes for debrief and scoring. |

### Phase plan (sim-time anchored)

Epoch **`2026/02/02 08:00 UTC`**, orbit §4.1 — **ν = −90°** pulls SOH phasing ~**9 min earlier** than ν=−110°; **re-validate** Dubai/Hormuz visibility on first trace. Indicative: Dubai overlap **~370 s** (shift with dry-run); Hormuz GPS cluster ~**18 min**; nearest-GS routing **~8 min** (dry-run your link policy).

| Phase | Wall | Sim time | Theme |
| --- | --- | --- | --- |
| **0 — Familiarisation** | 00:00 – ~00:12 | `0 – ~720 s` | Paris visibility; connect, baseline ops. **~6:40 min** first GPS spoof region and **~10 min** solar-array degradation. Optional vessel-count question. |
| **1 — Passive cyber** | ~00:07 – ~00:33 | `~400 – ~2 000 s` | Multi-step GPS spoof sequence (5 region updates + remove), storage/reaction-wheel faults, GPS jamming on/off, and two cyber inject events. |
| **2a — Rogue capture** | ~00:00 – ~00:15 | `0 – 900 s` | MQTT uplink capture only (all blue teams subscribed concurrently). |
| **2b — Rogue replay & jam** | ~00:25 – ~00:50 | `~1 500 – ~3 000 s` envelope | Replay bursts **`1 500 – 1 980`**, **continuous uplink jam `1 980 – 2 280`** (all blue MHz), Singapore downlink barrage **`2 400 – 3 000`**. |
| **3 — Compound** | ~00:26 – ~00:33 | `~1 560 – ~2 000 s` | Storage + reaction-wheel fault, GPS jamming, and the second cyber inject overlap this arc. |
| **4 — Wind-down** | ~00:50 – 01:00 | `~3 000 – 3 600 s` | No new scripted attacks. Teams finalise answers and forensic notes. |

> Phases 1 and 2 deliberately **overlap visually but separate causally**: Phase 1 is global (everyone is affected); Phase 2 is targeted by the rogue spacecraft. Asking teams to attribute who-caused-what is the core of the assessment. Phase 2 is split into a **listen-only first half** and a **broadcast second half** so capture has time to populate before replay.

### 3.1 Master event timeline (validation)

Single checklist for dry-runs at **1×** (`wall seconds == sim seconds`). Values come from `cyber_defender.json` and `cyber_defender.py`; **keep this subsection in sync** when you edit either.

**Continuous windows** (not single instants)

| Item | Sim interval (s) | Definition |
| --- | --- | --- |
| Multi-team **uplink capture** | **0 → 900** | `CAPTURE_START` / `CAPTURE_END` |
| **Replay** envelope | **1 500 → 1 980** | `REPLAY_START` / `REPLAY_END`; eight bursts drawn inside (`seed` below) |
| **A7** uplink jam | **1 980 → 2 280** | Continuous; **~0.08 W** on **all** blue MHz (`UPLINK_JAM_POWER`); bore-sight defender via `guidance_spacecraft` |
| **Broadcast downlink jam** | **900 → 1 500** (Dubai bore-sight) and **2 400 → 3 000** (Singapore bore-sight) | Prep events **10 s** before each **ON**; jammer aimed with `guidance_ground("Jammer", "<station>")`, not at the defender bus |

**Replay round times** — `MultiTeamReplaySequence(..., seed=20260202)`, uniform on **`[1500, 1980]`** (recompute if seed or bounds change): **1 525.7**, **1 626.2**, **1 642.0**, **1 754.6**, **1 775.0**, **1 801.0**, **1 860.7**, **1 956.2** s.

**Point & edge triggers** — sorted by **simulation time** (`ν = −90°` / **−89.99°** rogue; absolute times **−540 s** vs former ν=−110° schedule)

| Sim (s) | Wall | Src | Event |
| ---: | ---: | :--- | :--- |
| 0 | 00:00 | Py | `Initial Sun Point` |
| 400 | 06:40 | JSON | GPS Spoof Region 1 |
| 600 | 10:00 | JSON | Solar Panel Degradation (**150000** degradation rate) |
| 600 | 10:00 | JSON | GPS Spoof Region 2 |
| 800 | 13:20 | JSON | GPS Spoof Region 3 |
| 840 | 14:00 | JSON | Cyber Inject 1 (`STAR INJECT`, APID **300**) |
| 870 | 14:30 | JSON | GPS Spoof Region 4 |
| 890 | 14:50 | Py | Point jammer at **Dubai** (downlink barrage prep) |
| 900 | 15:00 | Py | Downlink Jam **ON** (Dubai segment) |
| 980 | 16:20 | JSON | GPS Spoof Region 5 |
| 1 100 | 18:20 | JSON | GPS Spoof Off (remove index 0) |
| 1 500 | 25:00 | Py | Downlink Jam **OFF** (Dubai segment) |
| 1 525.7 | 25:26 | Py | Replay burst **#1** |
| 1 560 | 26:00 | JSON | Storage Full |
| 1 620 | 27:00 | JSON | Reaction Wheel Stuck |
| 1 626.2 | 27:06 | Py | Replay burst **#2** |
| 1 642.0 | 27:22 | Py | Replay burst **#3** |
| 1 754.6 | 29:15 | Py | Replay burst **#4** |
| 1 775.0 | 29:35 | Py | Replay burst **#5** |
| 1 800 | 30:00 | JSON | Reaction Wheel Nominal |
| 1 801.0 | 30:01 | Py | Replay burst **#6** |
| 1 850 | 30:50 | JSON | GPS Jamming On |
| 1 860.7 | 31:01 | Py | Replay burst **#7** |
| 1 920 | 32:00 | JSON | Cyber Inject 2 (`ECHO VIRUS`, APID **302**) |
| 1 956.2 | 32:36 | Py | Replay burst **#8** |
| 1 970 | 32:50 | Py | Point jammer at defender bus (uplink jam prep) |
| 1 980 | 33:00 | Py | **Uplink Jam ON** (all blue MHz, low power) |
| 2 000 | 33:20 | JSON | GPS Jamming Off |
| 2 280 | 38:00 | Py | **Uplink Jam OFF** |
| 2 390 | 39:50 | Py | Point jammer at **Singapore** (downlink barrage prep) |
| 2 400 | 40:00 | Py | Downlink Jam **ON** (Singapore segment) |
| 3 000 | 50:00 | Py | Downlink Jam **OFF** (Singapore segment) |
| 3 060 | 51:00 | Py | `Final Sun Point` |

**Wall** column is **mm:ss** from session start at 1×. **Src**: **JSON** = `events[]` in `cyber_defender.json`; **Py** = `cyber_defender.py` scheduler / replay module.

---

## 4. Universe & orbit

### 4.1 Orbit choice — MEO, slightly elliptical

```text
SMA           = 10 000 km   (alt ~3 622 km, classified MEO)
Eccentricity  = 0.015
Inclination   = −37°
RAAN          = 350°
ArgPerigee    = 0°
TrueAnomaly   = −90° (defender) / −89.99° (rogue — co-located)
```

| Property | Value | Rationale |
| --- | --- | --- |
| Orbital period | **~2.77 h** | `T = 2π√(a³/μ)` with `a = 10 000 km` ≈ 9 952 s. |
| Orbits per workshop | **Fraction of one orbit** at 1× / h | One wall-clock hour spans less than one orbital period — pacing prioritises cyber timelines over repeating ground-track passes. |
| Inclination | −37° | Signed inclination as authored in JSON; GPS \|latitude\| peaks near 37°. |
| RAAN | 350° | Phases the ground track with the workshop epoch so Hormuz / Dubai handoff lands mid-session (dry-run validated). |
| Eccentricity | 0.015 | Light variation in altitude makes apoapsis/periapsis a worthwhile telemetry question without distorting the timeline. |
| Rogue placement | `ν ≈ −90°` | Same orbit as defender with negligible separation; **`visualization.hide: true`** removes the default 3D cue — teams rely on RF attribution. **~20°** advance in ν vs −110° ≈ **~9 min** along-track for `T ≈ 9 952 s` — scenario **event times are shifted −540 s** to stay aligned with the Hormuz pass. |

> **Why not LEO?** A flight-ops course may want many short passes; this workshop wants **longer dwell** for scripted capture/replay and jamming. MEO gives longer contacts per pass than a typical LEO bus — still time-bounded (unlike GEO) so effects can be tied to *when* a pass occurs.

> **Why not GEO?** GEO is *too* easy: continuous visibility, no pass timing, events become dimensionless in time. We want some pass-cadence so teams notice "the jamming happens **only** over Dubai".

### 4.2 Universe block

```json
"universe": {
  "atmosphere": false,
  "magnetosphere": true,
  "gps": true,
  "cloud_opacity": 0.85,
  "cloud_contrast": 2.5,
  "ambient_light": 0.07
}
```

- `gps: true` is **mandatory** — GPS spoofing and GPS jamming events both rely on the global GPS subsystem (see `docs/scenarios/events.md` § GPS events).

### 4.3 Ground stations

Order matters for operator UX when multiple sites are in view — full city catalog: `docs/scenarios/ground-stations.md`.

```json
"ground_stations": {
  "locations": [
    "Paris", "Dubai", "Singapore", "Sydney",
    "Easter Island", "Miami"
  ],
  "min_elevation": 5,
  "max_range": 0,
  "scale": 100
}
```

Why this set (`min_elevation: 5°` adds a realistic horizon mask so passes feel finite — important for jamming windows that bracket a single contact):

| Station | Role |
| --- | --- |
| **Paris** | European anchor — first solid pass at workshop open for this epoch/orbit. |
| **Dubai** | CENTCOM-aligned Gulf anchor; nearest-GS handoff from Paris into Hormuz imaging **~18–25 min** on the ν=−90° schedule (dry-run). |
| **Singapore** | Indo-Pacific mid-pass overlap with Dubai for the second AOI jam window. |
| **Sydney** | Entering range late in the hour — continuity into the next orbit for instructors who overrun slightly. |
| **Easter Island** | Pacific gap filler between Americas and APAC arcs. |
| **Miami** | Western hemisphere anchor. |

#### 4.3.1 Coverage check (dry-run reference)

For the **`2026/02/02 08:00 UTC`** epoch and the six-element set in §4.1, a simulation pass reports **in-range** intervals (approximate sim-seconds, `min_elevation = 5°`):

```text
Paris          0 – 2 000
Dubai          370 – 3 340
Singapore      2 000 – 4 900
Sydney         3 600 – 6 670
```

The scripted threats place the first broadcast downlink barrage over the Dubai-linked segment (**900–1500 s**) and the second over the Singapore-linked segment (**2400–3000 s**). Re-validate pass ownership if your ground-routing policy differs.

#### 4.3.2 Cities deliberately not used

| City | Reason omitted |
| --- | --- |
| Karachi | Pakistan's strategic posture has drifted toward CPEC/BRI; awkward optics for a US/EU-framed exercise. |
| Colombo | Hambantota lease and Sri Lanka's tilt toward BRI. |
| Cape Town | South Africa is a BRICS member and has hosted Russia/China naval drills. |
| Doha | Geographically close to Dubai — this scenario standardises on **Dubai** as the Gulf anchor. |

Instructors who want to swap any of these back in can do so — the city catalog in `docs/scenarios/ground-stations.md` lists every available city. **Re-run a coverage pass** if you change the chain.

---

## 5. Mission narrative

> The **Maritime Cyber Watch** programme operates a single MEO defender, *Watchtower*, providing imagery and SIGINT across the Hormuz / Arabian Sea shipping corridor. Operations are split across **multiple shifts** — each blue team is a duty crew with its own RF identity (frequency, key, password) commanding the same shared spacecraft. Sister-state intelligence has flagged a co-orbital satellite, callsign **PHANTOM**, as a potential cyber threat. The exercise begins with nominal ops; over the workshop, both the Earth-side environment and PHANTOM escalate hostile activity. Each duty crew must keep the link healthy from their own console and file a forensic after-action report.

This narrative drives:

- One clear AOI for imagery in Phase 0.
- A reason to keep the EM sensor on (used for Phase 2 attribution).
- A reason to use **EM-sensor / spectrum** on the rogue carrier during replay (call-sign reinforced by mission brief; mesh hidden in stock JSON).
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
| `GPS Sensor` | Source of APID 301 telemetry used to observe spoofing/jamming effects. | 301 |
| `Magnetometer` | Cross-check GPS spoof against B-field. | 300 |
| `Reaction Wheels` | Pointing for camera/EM. | 401 |

The APID column matters for Phase 3 telemetry overlays (§ 9, A9-A10 — Magnetometer and EM Sensor injects) — only APIDs whose underlying components exist on `SC_OPS` will actually be emitted and therefore be patchable.

`controller`:

```json
{
  "safe_fraction": 0.1,
  "capture_tax": 0.001,
  "downlink_tax": 0.005,
  "ping_interval": 3.0,
  "reset_interval": 20.0,
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
| `Text` (`"PHANTOM"`) | Chassis ID if `hide` is cleared; otherwise answer from brief / EM context. |

`controller`:

```json
{
  "safe_fraction": 0.05,
  "capture_tax": 0.001,
  "downlink_tax": 0.005,
  "ping_interval": 3.0,
  "reset_interval": 20.0,
  "jamming_multiplier": 100.0,
  "enable_rpo": false,
  "enable_intercept": true
}
```

> `enable_intercept: true` is **required** for the Python intercept-capture sequence to receive Format 3 records (see `src/cyber_replay.py`).

### 7.3 Visual concealment

`visualization.hide: true` on `SC_ROGUE` (same pattern as *Orbital Sentinel*'s stock rogue) — the mesh is **not** shown on the default map / 3D pass. Discovery is **EM-sensor and spectrum** during replay/jam, plus mission context for the call-sign question. The `MRO` chassis and `Text` "PHANTOM" components remain in the asset for custom builds that clear `hide`.

---

## 8. Ground objects (AOI dressing)

**Why ships exist:** they give *Watchtower*’s maritime/SIGINT framing something **concrete in the map layer** — imagery tasking, AIS-like density, and (during spoofing) a **visual mismatch** between “where GPS says we are” versus where the Hormuz hulls actually live. They are **not** there for a ship-counting WEGO exercise unless you choose to score it.

**Authoring today:** **five** green traffic hulls at the Hormuz grid (**Lead, Trail, Flank, Picket, Tender** — `GO_001`–`GO_005`), plus **two** yellow **Spoof Decoy** hulls offset southeast (`GO_006`, `GO_007`) so the deceptive GPS fix story has a **wrong-ocean** cluster to reference.

**Optional assessment:** the question bank includes a **primary Hormuz cluster count** (= **5**, excluding decoys). Skip it if you want zero overlap with counter-piracy tropes.

Earlier guidance still applies: **fewer** vessels than *Orbital Sentinel* because cyber signatures are the focus.

---

## 9. Attack catalogue

> Format: each attack lists **type** (passive event vs. active script), **sim-time window**, **mechanism** (the JSON event or Python call), and the **observable signature** the defender should recognise.

### Phase 1 — Passive (events JSON)

#### A0. Solar panel degradation (early warm-up)

- **Type**: passive (`Type: "Spacecraft"`, `Target: "SolarPanel-SolarPanelDegradationErrorModel"`).
- **Window**: fires once at **`600 s`** (**~10 min** simulation time); persists until mitigated via component logic.
- **Mechanism**: `Data: { "Degradation Rate": 150000.0 }` (**1.5×** the stock **100000** recipe) on **`SC_OPS`** (see `docs/scenarios/events.md`).
- **Signature**: solar / power telemetry trends away from nominal — **orthogonal** to RF cyber, easy to attribute to **hardware / environment**.
- **Mitigation**: component `reset` / ops procedure per platform.
- **Pedagogy**: gives operators **something to chase before the Hormuz GPS cluster** without stacking ambiguous imagery faults.
- **Assessment** (question bank): fault type = **Solar Panel Degradation**; panels keyed as **Both** (+X and −X); event time **~10 min** (±3 min tolerance).

#### A1. GPS Spoofing sequence — Regions 1 to 5

- **Type**: passive (`Type: "GPS"`, `Data.Type: "Spoofing"`).
- **Window**: **`400 s → 1 100 s`**.
- **Mechanism**: five authored spoof-region updates (`GPS Spoof Region 1..5`) progressively move the spoofed location, then `GPS Spoof Off` removes index `0`.
- **Signature**: APID 301 (`GPS`) position/altitude track jumps across implausible regions while APID 300 (`Magnetometer`) remains physically coherent.
- **Mitigation**: cross-check with non-GPS sensors, dead-reckon, or roll back to last trusted navigation state.

#### A2. GPS Jamming — ground source

- **Type**: passive (`Type: "GPS"`, `Data.Type: "Jamming"`, `Action: "add"`).
- **Window**: **`1 850 s → 2 000 s`** (paired add/remove with `Index: "0"`).
- **Mechanism**: `GPS Jamming On` adds jammer at `lat 26°, lon 56°, alt 500 km`, `ERP: 25 000 000 W`, `Path Loss Exponent: 1.0`; `GPS Jamming Off` removes it.
- **Signature**: GPS solutions go unhealthy / no-fix when over the AOI.
- **Mitigation**: dead-reckon; cross-check with magnetometer (still healthy).

#### A3. Storage Full (capacity stress)

- **Type**: passive (`Type: "Spacecraft"`, `Target: "Storage"`) — stock recipe **`Storage Full`** from `studio/Plugins/SpaceRange/Resources/Events/Spacecraft.json`.
- **Window**: fires once at **`1 560 s`** (**26 min** simulation time).
- **Mechanism**: `Data: { "Capacity": 100000 }` on **`SC_OPS`** — clamps usable capacity so operators perceive **reduced storage headroom** (not bit-rot).
- **Signature**: storage fullness / capacity telemetry diverges from nominal; imagery retention planning is affected.
- **Mitigation**: ops procedures per platform — archive, delete, or `reset` Storage if your lesson plan allows.
- **Pedagogy**: separates **storage sizing / capacity** stress from GPS-layer attacks.
- **Assessment** (question bank): keyed outcome **“Storage Capacity was Decreased”** (interpretation of capacity clamp); event time **26 min** (±3 min tolerance).

### Phase 2a — Listen across every blue team (Python rogue script)

#### A5. Multi-team replay capture

- **Type**: active (extends `InterceptReplaySequence` from `src/cyber_replay.py`).
- **Window**: **`0 s → 900 s`**.
- **Mechanism**: rogue enables MQTT foreign-uplink capture for **all** blue teams at once, storing valid decrypted JSON commands into per-team pools (`max_per_team` cap).
- **Signature**: nothing visible to the defender — captures are silent.
- **Defender training point**: this only succeeds because uplinks are unauthenticated ciphertext. Operators who rotate `encryption` mid-window invalidate any captured ciphertext for *their* team going forward.

> Implementation detail: implemented as `MqttUplinkCaptureSequence` (multi-team MQTT capture), which stores valid JSON uplinks per team across `0 → 900 s` without RF dwell-cycling.

### Phase 2b — Replay & jam across every blue team (Python rogue script)

#### A6. Random multi-team replay

- **Type**: active (re-broadcast captured wire bytes from A5 — **no mutation**; each transmit draws a **random** wire from **that team's** pool — commands that were sent *to the defender* and overheard while listening as that blue RF identity).
- **Window**: **`1 500 s → 1 980 s`**.
- **Mechanism**:
  1. Schedule **N replay rounds** (`burst_count`, default **8**) at **random** sim-times across the window.
  2. At **each round time**, for **every** blue team **in order**, pick a **random** capture from **that team's pool only**, tune the rogue ground TX to that team's frequency, and `replay_transmit_bytes` the **verbatim** on-air bytes. If a team's pool is empty, skip that team for that round (logged).
  3. Whether the bus **accepts** a replay (state change) or **rejects** it (counter / envelope) is **not** prescribed — both are valid teaching outcomes; questions should allow either.
  4. Log **every** transmit for forensics (`burst_round`, team, sha1).
- **Signature**: spurious uplink-traffic spike on EM sensor at a blue team's RX frequency without a matching ground-station transmission; possible duplicate `command_received` events.
- **Mitigation**: rotate Caesar key (`encryption`) — invalidates captured ciphertext for that team.

> Implementation detail: a second helper `MultiTeamReplaySequence` schedules replay events through the existing `EventScheduler`. Replay events arm at creation but **fire on `tick(sim_time)`**, identical to the single-team `schedule_replay_at` pattern — just iterated. Every replay event resolves the **current** team frequency live via `live_enemy_frequencies`-style lookup (key may have been rotated mid-window, in which case the replay simply fails to decode on-board, which is itself observable behaviour).

#### A7. Continuous uplink jam (shared defender bore-sight, all blue MHz, low power)

- **Type**: active — one **`jammer_start`** and one **`jammer_stop`**.
- **Window**: **`1 980 → 2 280` s** (Mumbai keyed pass narrative).
- **Design intent**: the rogue bore-sights the **defender spacecraft** (`guidance_spacecraft("Jammer", <first-blue-asset>)`) — not a ground antenna — while hitting **every** blue team's MHz in one list. **Very low wattage** (default **~0.08 W** vs **3 W** downlink barrage) keeps the effect pedagogical rather than wiping all uplinks at once; no pulses and no scripted per-team hopping.
- **Mechanism**:

  ```python
  scheduler.add_event(..., trigger_time=UPLINK_JAM_START - 10.0,
      **guidance_spacecraft("Jammer", DEFENDER_ASSET_ID))
  scheduler.add_event("Uplink Jam ON", trigger_time=UPLINK_JAM_START,
      pre_trigger=live_jammer_args_all,
      **jammer_start(fallback=enemies_mhz_list, power=UPLINK_JAM_POWER))
  scheduler.add_event("Uplink Jam OFF", trigger_time=UPLINK_JAM_END,
      **jammer_stop())
  ```

- **Signature**: all blue crews may see **weaker / sporadic uplink degradation** concurrently during the Mumbai window depending on simulator link budget — far gentler than the downlink AOI barrage.
- **Mitigation**: `telemetry` frequency hop and/or encryption rotate remains valid coursework.

#### A8. Broadcast downlink jam — Dubai segment

- **Type**: active (rogue spacecraft jammer, all blue-team downlink MHz).
- **Window**: **`900 → 1 500` s** (simulation time).
- **Design intent**: operators are **keyed through Dubai** (~9–25 min scripted visibility); bore-sighting the **Dubai ground site** jams the contested downlink geography without pointing the rogue at the defender bus.
- **Mechanism**:

  ```python
  scheduler.add_event("Point Jammer at Dubai (...)",
      trigger_time=890.0, **commands.guidance_ground("Jammer", "Dubai"))
  scheduler.add_event("Downlink Jam ON (Dubai segment)",
      trigger_time=900.0, pre_trigger=live_jammer_args_all,
      **commands.jammer_start(enemy_fallback_freqs, power=3.0))
  scheduler.add_event("Downlink Jam OFF (Dubai segment)",
      trigger_time=1500.0, **commands.jammer_stop())
  ```

  Frequency list = **every** blue team's frequency (`live_jammer_args_all`). Power `3.0 W`.

#### A11. Broadcast downlink jam — Singapore segment

- **Type**: active (same as A8).
- **Window**: **`2 400 → 3 000` s**.
- **Design intent**: second barrage **keyed through Singapore** (~38+ min scripted visibility); jammer bore-sighted with `guidance_ground("Jammer", "Singapore")`.
- **Mechanism**: Same pattern as A8 with prep at **`2 390` s**, **ON** at **`2 400`**, **OFF** at **`3 000`**, `power=3.0 W`.
- **Mitigation**: frequency hop (`telemetry`) so the next pass can close on an unjammed channel.

### Phase 3 — Compound (Cyber events + script)

> **Payload safety**: the scenario JSON loader does not handle `{`, `}`, or `"` inside Cyber-event ASCII payloads (a bug in the JSON-to-internal-string round trip). The A9 and A10 ASCII payloads (`STAR INJECT`, `ECHO VIRUS`) avoid those characters.

#### A9. Cyber inject — Magnetometer (APID 300)

- **Type**: passive (`Type: "Cyber"`, `Target: "Spacecraft"`, `Assets: ["SC_OPS"]`).
- **Window**: trigger at `840 s` (~14 min), `Expiry Seconds: 300.0` (5 min overlay).
- **Mechanism**: full-message ASCII overlay at offset `0`, payload `STAR INJECT`, `Encoding: "ascii"`, `Clear On Reset: true`.
- **Signature**: Magnetometer user data shows the injected string for the overlay window.
- **Mitigation**: `reset` the `Computer` (overlay clears because of `Clear On Reset: true`).

#### A10. Cyber inject — EM Sensor (APID 302)

- **Type**: passive (same Cyber schema as A9).
- **Window**: trigger at `1 920 s` (~32 min), `Expiry Seconds: 300.0` (5 min overlay).
- **Mechanism**: full-message ASCII overlay at offset `0`, payload `ECHO VIRUS`, `Encoding: "ascii"`, `Clear On Reset: true`.
- **Signature**: EM Sensor user data shows the injected string for the overlay window.
- **Mitigation**: `reset` the `Computer` (same as A9).

#### A12. Reaction-wheel stuck (component fault)

- **Type**: passive (`Type: "Spacecraft"`, `Target: "Reaction Wheels"`).
- **Stuck at**: **`1 620 s`** (**27 min** simulation time).
- **Mechanism**: `Data: { "Stuck Index": 0 }` → **Wheel 1** stuck (zero-based index).
- **Signature**: APID 401 (`Reaction Wheels`) reports a stuck axis; pointing drifts.
- **Mitigation**: `reset` `Reaction Wheels`, or wait for the scripted **nominal** event below.

#### A12b. Reaction-wheel nominal (unstuck)

- **Type**: passive (same target as A12; stock recipe **Reaction Wheel Nominal** in `studio/Plugins/SpaceRange/Resources/Events/Spacecraft.json`).
- **Fires at**: **`1 800 s`** (**30 min** simulation time).
- **Mechanism**: `Data: { "Nominal Index": 0 }` — clears the stuck state on wheel index **0** (same wheel as A12).
- **Assessment** (question bank): wheel **1** for which wheel stuck; stuck time **27 min** (±3 min tolerance).

> **Hardware faults in this workshop**: only **three** passive spacecraft component events are authored — **A0** solar degradation, **A3** storage full, **A12** reaction-wheel stuck. There is **no** battery intermittent-connection event in `cyber_defender.json`.

### Phase 4 — Wind-down

From **after the last Cyber tamper / telemetry event you author** onwards: operator focus shifts to answering questions and reviewing EM-sensor / console artefacts until `end_time` at **3 600 s**.

---

## 10. Question framework

Current JSON carries **32 questions** across the sections below. Keep this breakdown synced with `cyber_defender.json`:

| Section | Approx weight | Sample question titles |
| --- | --- | --- |
| Orbital Operations (sanity) | ~14 pts | Maritime counts, semi-major axis, inclination |
| Vessel Identification | 10 pts | Green and yellow vessel counts |
| Orbital Operations | 10 pts | Semi-major axis and inclination |
| Solar Panel Fault | 10 pts | fault type, affected panels, time |
| Storage Fault | 8 pts | effect and time |
| Reaction Wheels Fault | 7 pts | affected wheel and time |
| GPS Spoofing | 15 pts | first/last time and spoofed region |
| GPS Jamming | 10 pts | first/last time |
| Cyber Injects | 20 pts | APID selection + hidden payload text |
| Rogue Identification | 15 pts | call-sign + transmitter frequency |
| Downlink Jamming | 20 pts | episodes, affected stations, min SNR, mitigation |
| Uplink Jamming | 20 pts | episodes, station, min SNR, mitigation |
| Replay Attacks | 15 pts | affected station, duration, mitigation |

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
- `events[]`: 14 passive events, including GPS Spoof Region 1..5 and GPS Jamming On/Off, plus the two Cyber Inject events and spacecraft faults; sorted by `Time`.
- `questions[]`: see §10.

### 11.2 `cyber_defender.py`

Mirrors `orbital_sentinel.py` shape but uses the new multi-team helpers:

```python
from src import Scenario, commands
from src.cyber_replay import MqttUplinkCaptureSequence, MultiTeamReplaySequence

CAPTURE_START, CAPTURE_END = 0.0, 900.0
REPLAY_START, REPLAY_END = 1500.0, 1980.0
UPLINK_JAM_START, UPLINK_JAM_END, UPLINK_JAM_POWER = 1980.0, 2280.0, 0.08

scenario = Scenario(team_name="Rogue", config_path=_config_path)
scheduler = scenario.scheduler

capture = MqttUplinkCaptureSequence(
    scenario.client, scenario.enemy_teams,
    start_at=CAPTURE_START, end_at=CAPTURE_END, max_per_team=512
)
replay_seq = MultiTeamReplaySequence(
    scenario.client, capture,
    start_at=REPLAY_START, end_at=REPLAY_END,
    burst_count=8, seed=20260202,
    frequency_for_team=lambda t: float(scenario.live_enemy_frequency_for(t)),
)

# Uplink jam: single ON/OFF, all blue frequencies, low power
scheduler.add_event("Uplink Jam ON", trigger_time=UPLINK_JAM_START,
                    pre_trigger=live_jammer_args_all,
                    **commands.jammer_start(scenario.enemy_fallback_freqs, UPLINK_JAM_POWER))
scheduler.add_event("Uplink Jam OFF", trigger_time=UPLINK_JAM_END,
                    **commands.jammer_stop())
```

`Scenario.run` already drives `on_session` → `seq.tick(session["time"])` forwarding; the new helpers expose a matching `tick(sim_time)`.

> **Current cyber replay primitives used by this scenario**:
>
> - `MqttUplinkCaptureSequence` — captures valid JSON uplink commands per blue team during `0 → 900 s`.
> - `MultiTeamReplaySequence` — schedules random replay rounds in `1500 → 1980 s`, then replays per-team captures against each team's live frequency.

> **New code addition to `src/commands.py` (or a small `src/jamming.py`)**:
>
> - `schedule_jammer_pulses(...)` — optional helper for *other* scenarios that need duty-cycled jams. **Cyber Defender A7** no longer uses it (single ON/OFF uplink barrage instead).

### 11.3 `README.md` (instructor brief)

Short page (single screen) giving the instructor:

- The mission narrative (§5).
- The phase plan (§3) as a bullet list.
- The launch sequence: load JSON, start `cyber_defender.py`, start sim at **1×** (or your instructor override).
- A sanity checklist (admin `admin_get_scenario_events`, expected event count).

---

## 12. Resolved design decisions

1. **Single RF per team** — **Keep** one `frequency` per team (matches shipped scenarios).
2. **A6 replay semantics** — **Each round** re-sends **one random capture per team** from **each team's** pool (**verbatim** bytes). Do **not** require successful state mutation; wording allows accept/reject on board.
3. **PHANTOM visibility** — **`visualization.hide: true`** on `SC_ROGUE`; discovery via **EM sensor** / spectrum and brief, not default map mesh.
4. **A9 / A10 ASCII Cyber payloads** — `STAR INJECT` and `ECHO VIRUS` avoid `{`, `}`, `"` per the JSON-loader constraint on Cyber ASCII payloads.
5. **Capture / replay cadence** — **First half** of session: multi-team **capture** only. **Second half**: **random replay bursts** (plus jams). Per-team quota **`X = 2`** if `len(enemy_teams) ≤ 2`, else **`X = 3`** (`cyber_defender.py`).
6. **Ground-station ownership during jamming** — confirm Dubai and Singapore pass ownership on your range if routing policy differs.
7. **A7 uplink jam** — **Continuous** barrage at **low power** on **all** blue MHz; **`UPLINK_JAM_POWER`** is the lone scalar to tune after dry-run.

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
- `src/commands.py` — `jammer_start` / `jammer_stop` / `guidance_spacecraft` / `guidance_ground`.
- `docs/guides/instructor-admin.md` — admin checklist and live-event push.
