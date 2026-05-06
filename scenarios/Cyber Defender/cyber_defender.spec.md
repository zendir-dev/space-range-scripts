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

1. **Recognise** the telemetry signatures of: GPS spoofing, GPS jamming, uplink jamming, downlink jamming, command injection (telemetry tamper), replay attack, sensor fault, storage corruption, **solar-array degradation** (early-session warm-up).
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
| Threat-heavy arc | **`0 → ~2 160 s`** (~first **36 minutes**, ν=−90° schedule) — passive GPS/storage/GPS-fault events, rogue capture/replay/jam windows, broadcast AOI downlink jams, and compound cyber tail finish by **~2 160 s**, leaving the rest of the hour for debrief and question wrap-up. |

### Phase plan (sim-time anchored)

Epoch **`2026/02/02 08:00 UTC`**, orbit §4.1 — **ν = −90°** pulls SOH phasing ~**9 min earlier** than ν=−110°; **re-validate** Dubai/Hormuz visibility on first trace. Indicative: Dubai overlap **~370 s** (shift with dry-run); Hormuz GPS cluster ~**18 min**; nearest-GS routing **~8 min** (dry-run your link policy).

| Phase | Wall | Sim time | Theme |
| --- | --- | --- | --- |
| **0 — Familiarisation** | 00:00 – ~00:02 | `0 – ~120 s` | Paris visibility; connect, baseline ops. **~30 s** bootstrap **GPS spoofing OFF**. **~2 min** **solar-array degradation** warm-up. Optional vessel-count question. |
| **1 — Passive cyber** | ~00:02 – ~00:24 | `~120 – ~1 440 s` | Hormuz **GPS spoof → jam → fault → jam remove** (from ~**18 min**); **storage ~23–24 min**. **Rogue capture** `60 → 1 260 s`. |
| **2a — Rogue capture** | ~00:01 – ~00:21 | `~60 – ~1 260 s` | **First half of session** — cycle every blue frequency; silent per-team capture pools. |
| **2b — Rogue replay & jam** | ~00:21 – ~00:34 | `~1 280 – ~2 060 s` | **Second half** — random re-transmit of captured uplink bytes; pulsed uplink jam; **second AOI downlink jam** (`T_AOI_2 ≈ 2 010 s`). |
| **3 — Compound** | ~00:34 – ~00:36 | `~2 045 – ~2 160 s` | Cyber telemetry tamper + reaction wheel + battery pile-on. |
| **4 — Wind-down** | ~00:36 – 01:00 | `~2 160 – 3 600 s` | No new scripted attacks. Teams finalise answers and forensic notes. |

> **`T_AOI_1`** (**~1 260 s**, ~**21 min**) fires during Phase 1 — broadcast downlink jam overlaps the Hormuz GPS attack cluster by design.

> Phases 1 and 2 deliberately **overlap visually but separate causally**: Phase 1 is global (everyone is affected); Phase 2 is targeted by the rogue spacecraft. Asking teams to attribute who-caused-what is the core of the assessment. Phase 2 is split into a **listen-only first half** and a **broadcast second half** so capture has time to populate before replay.

### 3.1 Master event timeline (validation)

Single checklist for dry-runs at **1×** (`wall seconds == sim seconds`). Values come from `cyber_defender.json` and `cyber_defender.py`; **keep this subsection in sync** when you edit either.

**Continuous windows** (not single instants)

| Item | Sim interval (s) | Definition |
| --- | --- | --- |
| Multi-team **uplink capture** | **60 → 1 260** | `CAPTURE_START` / `CAPTURE_END` |
| **Replay** envelope | **1 280 → 2 060** | `REPLAY_START` / `REPLAY_END`; eight bursts drawn inside (`seed` below) |
| **A7** pulsed uplink jam | **1 560 → 1 660** | **8 s ON / 40 s period** — pulses ON **1 560**, **1 600**, **1 640**; OFF **1 568**, **1 608**, **1 648** |
| **AOI broadcast downlink jam** | Pass **1**: **1 170 → 1 350**; Pass **2**: **1 920 → 2 100** | Centres **`T_AOI_1 = 1 260`**, **`T_AOI_2 = 2 010`**; half-width **90 s** each (`±90` from centre) |

**Replay round times** — `MultiTeamReplaySequence(..., seed=20260202)`, uniform on **`[1280, 2060]`** (recompute if seed or bounds change): **1 321.7**, **1 485.0**, **1 510.7**, **1 693.8**, **1 726.8**, **1 769.2**, **1 866.2**, **2 021.4**. At **each** instant the rogue issues **one transmit per blue team** (each picks a random wire from **that** team's capture pool).

**Point & edge triggers** — sorted by **simulation time** (`ν = −90°` / **−89.99°** rogue; absolute times **−540 s** vs former ν=−110° schedule)

| Sim (s) | Wall | Src | Event |
| ---: | ---: | :--- | :--- |
| 30 | 00:30 | JSON | GPS Spoof Region — Hormuz OFF **(bootstrap)** |
| 60 | 01:00 | Py | `Initial Sun Point` |
| 120 | 02:00 | JSON | Solar Panel Degradation **(early warm-up)** |
| 1 080 | 18:00 | JSON | GPS Spoof Region — Hormuz ON |
| 1 110 | 18:30 | JSON | GPS Jammer Add — Hormuz |
| 1 160 | 19:20 | Py | Point jammer (AOI Pass **1** prep) |
| 1 170 | 19:30 | Py | Downlink Jam **ON** (AOI Pass **1**) |
| 1 220 | 20:20 | JSON | GPS Sensor Hard Fault |
| 1 321.7 | 22:02 | Py | Replay burst **#1** |
| 1 350 | 22:30 | Py | Downlink Jam **OFF** (AOI Pass **1**) |
| 1 380 | 23:00 | JSON | GPS Jammer Remove — Hormuz |
| 1 390 | 23:10 | JSON | GPS Spoof Region — Hormuz OFF **(post-cluster)** |
| 1 420 | 23:40 | JSON | Storage Corruption |
| 1 485.0 | 24:45 | Py | Replay burst **#2** |
| 1 510.7 | 25:11 | Py | Replay burst **#3** |
| 1 550 | 25:50 | Py | Point jammer (A7 uplink jam prep) |
| 1 560 | 26:00 | Py | A7 jammer **ON** #1 |
| 1 568 | 26:08 | Py | A7 jammer **OFF** #1 |
| 1 600 | 26:40 | Py | A7 jammer **ON** #2 |
| 1 608 | 26:48 | Py | A7 jammer **OFF** #2 |
| 1 640 | 27:20 | Py | A7 jammer **ON** #3 |
| 1 648 | 27:28 | Py | A7 jammer **OFF** #3 |
| 1 693.8 | 28:14 | Py | Replay burst **#4** |
| 1 726.8 | 28:47 | Py | Replay burst **#5** |
| 1 769.2 | 29:29 | Py | Replay burst **#6** |
| 1 866.2 | 31:06 | Py | Replay burst **#7** |
| 1 910 | 31:50 | Py | Point jammer (AOI Pass **2** prep) |
| 1 920 | 32:00 | Py | Downlink Jam **ON** (AOI Pass **2**) |
| 2 021.4 | 33:41 | Py | Replay burst **#8** |
| 2 045 | 34:05 | JSON | Reaction Wheel Stuck |
| 2 080 | 34:40 | JSON | Tamper Ping State (Cyber) |
| 2 100 | 35:00 | Py | Downlink Jam **OFF** (AOI Pass **2**) |
| 2 110 | 35:10 | JSON | Tamper GPS Position (Cyber) |
| 2 160 | 36:00 | JSON | Battery Power Spikes |
| 2 760 | 46:00 | Py | `Final Sun Point` |

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

The scripted threats place **Hormuz-region GPS attacks and the first AOI downlink jam ~21 min** into the pass on the current ν=−90° / −540 s clock (Dubai link primary), with **nearest-GS routing to Dubai ~8–12 min** — align fine timing on your range if link logic differs. **Re-validate after any orbit or epoch change.**

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
- **Window**: fires once at **`120 s`** (~2 min); persists until mitigated via component logic.
- **Mechanism**: `Data: { "Degradation Rate": 100000.0 }` on **`SC_OPS`** (see `docs/scenarios/events.md`).
- **Signature**: solar / power telemetry trends away from nominal — **orthogonal** to RF cyber, easy to attribute to **hardware / environment**.
- **Mitigation**: component `reset` / ops procedure per platform.
- **Pedagogy**: gives operators **something to chase before the Hormuz GPS cluster** without stacking ambiguous imagery faults.

#### A1. GPS Spoofing — Hormuz region

- **Type**: passive (`Type: "GPS"`, `Data.Type: "Spoofing"`).
- **Window**: **bootstrap OFF** at **`30 s`**, **ON** at **`1 080 s`**, **post-cluster OFF** at **`1 390 s`** (brackets the Hormuz pass; ends before storage corruption at **1 420 s**).
- **Mechanism**: spoof a ~200 km-radius volume centred on `lat 26.5°, lon 56.5°, alt 4 000 km` — when the defender's GPS receiver is inside the sphere, position is reported at `lat -26.5°, lon -123.5°` (mirror point in the South Pacific).
- **Signature**: GPS lat/lon "jumps" while velocity vector and B-field are unchanged. APID 301 (`GPS`) reports drift, APID 300 (`Magnetometer`) doesn't.
- **Mitigation**: ephemeris rollback (or trust last good fix until exit).

#### A2. GPS Jamming — ground source over AOI

- **Type**: passive (`Type: "GPS"`, `Data.Type: "Jamming"`, `Action: "add"`).
- **Window**: `1 110 s → 1 380 s` (paired add/remove with `Index: "0"`).
- **Mechanism**: ground jammer at `lat 26°, lon 56°, alt 50 km`, `ERP: 250 000 W`.
- **Signature**: GPS solutions go unhealthy / no-fix when over the AOI.
- **Mitigation**: dead-reckon; cross-check with magnetometer (still healthy).

#### A3. Storage corruption

- **Type**: passive (`Type: "Spacecraft"`, `Target: "Storage"`).
- **Window**: fires once at **`1 420 s`** (after the Hormuz GPS jammer is removed); corruption persists until mitigated.
- **Mechanism**: `Data: { "Corruption Fraction": 0.1, "Corruption Intensity": 0.2 }`.
- **Signature**: downlinked imagery starts containing scrambled bytes; APID 503 (`Storage`) reports degradation.
- **Mitigation**: `reset` the Storage component.
- **Pedagogy**: scheduled **after** the A1/A2/A4 GPS sequence so operators separate **environmental RF/GPS denial** from **payload-layer storage** faults.

#### A4. GPS Sensor fault (sustained / hard fault)

- **Type**: passive (`Type: "Spacecraft"`, `Target: "GPS Sensor"`).
- **Window**: fires at **`1 760 s`**; cleared by `reset` from operator.
- **Mechanism**: `Data: { "Fault State": 4 }`.
- **Signature**: APID 301 stops emitting fresh fixes / sticks at last value with `fault_state != 0`.
- **Mitigation**: `reset` the `GPS Sensor` component. Distinguishes a hardware fault from A1/A2 environmental denial.

### Phase 2a — Listen across every blue team (Python rogue script)

#### A5. Multi-team replay capture

- **Type**: active (extends `InterceptReplaySequence` from `src/cyber_replay.py`).
- **Window**: `60 s → 1 260 s` (first half of the hour; overlaps passive GPS on purpose).
- **Mechanism** (script-level — *new* helper required, see § 11.2):
  1. Resolve **every** blue team's RF via `rf_catalog.get_all_frequencies(admin)` — gives one snapshot per team.
  2. **Cycle** through them on a fixed dwell derived from the capture window length and team count so each team is visited twice before the window closes (at 1× speed the dwell is tens of seconds per sweep for a two-team roster). With more teams, shorten dwell proportionally.
  3. For each dwell, `tune_ground` to that team's `(freq, key, bandwidth)` and keep a **per-team capture pool** indexed by `team_id`.
  4. Stop the cycle once **every blue team has at least `X = 2` foreign intercepts** captured (or the window expires). Save the pools as JSON for forensics.
- **Signature**: nothing visible to the defender — captures are silent.
- **Defender training point**: this only succeeds because uplinks are unauthenticated ciphertext. Operators who rotate `encryption` mid-window invalidate any captured ciphertext for *their* team going forward.

> Implementation detail: the existing `InterceptReplaySequence.begin_capture(listen_rf, foreign_count)` is a single-frequency capture. Extend with a thin wrapper `MultiTeamCaptureSequence` that owns a `dict[team_id, list[CapturedWire]]` plus a tuner-cycle loop driven from `tick(sim_time)`. Reuse `decode_downlink_mqtt_payload` + `parse_uplink_intercept_record`.

### Phase 2b — Replay & jam across every blue team (Python rogue script)

#### A6. Random multi-team replay

- **Type**: active (re-broadcast captured wire bytes from A5 — **no mutation**; each transmit draws a **random** wire from **that team's** pool — commands that were sent *to the defender* and overheard while listening as that blue RF identity).
- **Window**: `1 280 s → 2 060 s` (second half; starts just after first-half capture ends).
- **Mechanism**:
  1. Schedule **N replay rounds** (`burst_count`, default **8**) at **random** sim-times across the window.
  2. At **each round time**, for **every** blue team **in order**, pick a **random** capture from **that team's pool only**, tune the rogue ground TX to that team's frequency, and `replay_transmit_bytes` the **verbatim** on-air bytes. If a team's pool is empty, skip that team for that round (logged).
  3. Whether the bus **accepts** a replay (state change) or **rejects** it (counter / envelope) is **not** prescribed — both are valid teaching outcomes; questions should allow either.
  4. Log **every** transmit for forensics (`burst_round`, team, sha1).
- **Signature**: spurious uplink-traffic spike on EM sensor at a blue team's RX frequency without a matching ground-station transmission; possible duplicate `command_received` events.
- **Mitigation**: rotate Caesar key (`encryption`) — invalidates captured ciphertext for that team.

> Implementation detail: a second helper `MultiTeamReplaySequence` schedules replay events through the existing `EventScheduler`. Replay events arm at creation but **fire on `tick(sim_time)`**, identical to the single-team `schedule_replay_at` pattern — just iterated. Every replay event resolves the **current** team frequency live via `live_enemy_frequencies`-style lookup (key may have been rotated mid-window, in which case the replay simply fails to decode on-board, which is itself observable behaviour).

#### A7. Light pulsed uplink jamming (one blue team)

- **Type**: active (`commands.jammer_start` / `jammer_stop` pulsed against one blue team's freq).
- **Window**: `1 560 s → 1 660 s` (inside replay + second AOI window).
- **Design intent**: **light** — we want a *fraction* of the targeted team's commands to fail, not all of them. The pulse + low-power combination lands ~15-25% of the team's commands inside an ON window where the jammer drowns the uplink, while the rest pass normally. This produces a much more realistic "intermittent comms" symptom than continuous jamming and gives operators something to *measure* (success rate) rather than just notice.
- **Mechanism**: a Python helper `schedule_jammer_pulses(...)` (see § 11.2) emits an alternating sequence of `jammer_start` / `jammer_stop` events at low power across the window:

  ```python
  scheduler.add_event("Point Jammer to Watchtower",
      trigger_time=2_090.0,
      **commands.guidance_spacecraft("Jammer", "SC_OPS"))
  schedule_jammer_pulses(scheduler,
      name="Uplink Pulse Jam (<target team>)",
      start=2_100.0, end=2_200.0,
      on_seconds=8.0, period_seconds=40.0,    # 20% duty cycle
      frequencies_resolver=lambda: [scenario.team_frequency("<target team>")],
      power=0.8)                              # well below A8/A11's level
  ```

  Frequencies are resolved live (per pulse) so a key/freq rotation by Blue Bravo mid-window changes the target without rewriting the schedule. The script picks **one team** to single out so the question "which team was uplink-jammed?" has a concrete answer.
- **Signature**: that team's ping payloads start showing **gaps** in the `Commands` list (some sent commands never appear as executed). Success rate during the window is roughly `1 − duty_cycle` ≈ 75-85%. Other blue teams continue normally.
- **Mitigation**: `telemetry` frequency hop (from ground) **or** `encryption` rotate (from spacecraft) — both move the team off the jammed channel for subsequent commands.
- **Forensic question target**: "Roughly what proportion of Blue Bravo's commands failed during the jam window?" — design tolerance ±10 pp.

#### A8. Downlink jamming over AOI imaging Pass #1

- **Type**: active (broadcast jammer across all blue freqs, fired during an AOI overhead pass).
- **Window**: **`T_AOI_1 ± 90 s`** (~180 s total) — default `T_AOI_1 ≈ 1 260 s` (ν=−90° schedule); **patch from GPS lat/lon if your epoch/geodesy differs**.
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

> **Locking AOI pass times**: **`T_AOI_1`** keys off the dry-run Hormuz crossing (~**1 260 s**). **`T_AOI_2`** sits in the Dubai + Singapore overlap (~**2 010 s**) alongside replay/uplink jam — adjust both after GPS trace validation if your integration timestep or station masks differ.

#### A11. Downlink jamming over AOI imaging Pass #2

- **Type**: active (same mechanism as A8, second AOI overhead).
- **Window**: **`T_AOI_2 ± 90 s`** — default `T_AOI_2 ≈ 2 010 s`, again **lock from dry-run**.
- **Design intent**: a second broadcast jam on the lat-band imaging timeline minutes after the first — same mechanism, different pass geometry / station depending on ground track. Lets teams realise the jam is **band-locked, not station-locked**, and that frequency-hopping after Pass #1 pays off if they did it.
- **Mechanism**: identical to A8 — `T_AOI_2 ± 90 s`, all blue freqs, `power=3.0 W`.
- **Signature**: same as A8 but on a different ground station's pass. Teams who hopped frequency after Pass #1 should see either reduced impact (rogue is jamming the *old* freq) or none (rogue is jamming a freq nobody listens on any more).
- **Mitigation**: confirms the A8 mitigation worked. Otherwise: hop now.
- **Forensic question target**: pairs with A8's question — "Was the second imaging pass also disrupted? At what ground station?"

### Phase 3 — Compound (Cyber events + script)

> **Payload safety**: the scenario JSON loader does not handle `{`, `}`, or `"` inside Cyber-event ASCII payloads (a bug in the JSON-to-internal-string round trip). All ASCII payloads below avoid those characters. For obvious "FLAG" signatures, use `FLAG-<word>` rather than `FLAG{<word>}`. Hex payloads are fine because they're matched character-class.

#### A9. Telemetry tamper — Ping `State` field (APID 100)

- **Type**: passive (`Type: "Cyber"`, `Target: "Spacecraft"`, `Assets: ["SC_OPS"]`).
- **Window**: trigger at `2 080 s`, `Expiry Seconds: 600.0`.
- **Mechanism**:

  ```json
  { "Enabled": true, "Name": "Tamper Ping State", "Time": 2080.0,
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
- **Window**: trigger at `2 110 s`, `Expiry Seconds: 600.0`.
- **Mechanism**:

  ```json
  { "Enabled": true, "Name": "Tamper GPS Position", "Time": 2110.0,
    "Type": "Cyber", "Target": "Spacecraft", "Assets": ["SC_OPS"],
    "Data": {
      "APID": 301, "SubType": -1, "Offset Bytes": 0,
      "Payload": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00",
      "Encoding": "hex",
      "Expiry Seconds": 600.0, "Clear On Reset": true
    }
  }
  ```

  The logical field order of the on-board GPS solution is defined in `api-classes/Zendir.Classes/Messages/Custom/GPSDataMessage.cs`: `IsActive`, `NumActive`, `CorrectedPseudoRange`, `TimeOfWeek`, `ECI` (`Vector3`), `ECEF` (`Vector3`), `Latitude`, `Longitude`, `Altitude`. The **wire layout** of APID 301 user-data (packing, array encoding, and whether a binary header precedes the first `Vector3`) must still be taken from the **XTCE / `get_packet_schemas` dry-run** — the C# class gives semantic order, not byte offsets. The stock event uses a 24-byte hex zero wipe aligned with the assumed start of the packed position block; shift `Offset Bytes` if your schema places `ECI`/`ECEF` later.
- **Signature**: live GPS plot snaps to implausible coordinates; magnetometer is unchanged so the team can detect the inconsistency.
- **Mitigation**: `reset` Computer (via `Clear On Reset: true`).
- **Confirm before shipping**: lock **`Offset Bytes`** from a live schema pull if the first 24 B do not line up with the first position `Vector3` in the packetized stream.

#### A12. Reaction-wheel stuck (component fault)

- **Type**: passive (`Type: "Spacecraft"`, `Target: "Reaction Wheels"`).
- **Window**: `2 045 s`.
- **Mechanism**: `Data: { "Stuck Index": 0 }`. Pointing degrades while teams are mitigating telemetry tamper.
- **Signature**: APID 401 (`Reaction Wheels`) reports a stuck axis; pointing drifts.
- **Mitigation**: `reset` `Reaction Wheels`.

#### A13. Battery intermittent connection

- **Type**: passive (`Type: "Spacecraft"`, `Target: "Battery-IntermittentConnectionErrorModel"`).
- **Window**: `2 160 s`.
- **Mechanism**: `Data: { "Intermittent Mean": 1, "Intermittent Std": 2 }` (verbatim from *Orbital Sentinel*).
- **Signature**: APID 200 (`Battery`) state-of-charge reports become noisy / spike.
- **Mitigation**: `reset` `Battery`.

### Phase 4 — Wind-down

From **`~2 160 s` onwards**: **no new effects fire**. Operator focus shifts to answering questions and reviewing EM-sensor / console artefacts until `end_time` at **3 600 s**.

---

## 10. Question framework

Aim for **~16-18 questions**, total score `100`, distributed across these sections (mirrors *Orbital Sentinel*'s breakdown style):

| Section | Approx weight | Sample question titles |
| --- | --- | --- |
| Orbital Operations (sanity) | 10 pts | "What is the SC_OPS semi-major axis?", "What is the orbital period?" |
| Environmental Cyber (Phase 1) | 25 pts | "Which AOI was GPS-spoofed?", "Where was the GPS jammer located?", "Which sensor returned a hard fault and at roughly what time?" |
| Adversary Attribution | 25 pts | "What is the rogue spacecraft's call-sign?" (brief / EM), "What frequency does PHANTOM transmit on?" (EM sensor), "Which ground stations saw downlink jamming?" |
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
                                     window=(1_280.0, 2_060.0))

# Phase 2a — capture (illustrative — real script uses tick()-driven windows)
scheduler.add_event("Capture: cycle blue teams", trigger_time=60.0,
                    pre_trigger=lambda a: capture.start_cycle(),
                    command="noop", args={}, description="...")
scheduler.add_event("Capture: stop", trigger_time=1_260.0,
                    pre_trigger=lambda a: capture.stop_cycle(),
                    command="noop", args={}, description="...")

# Phase 2b — replay across teams (random sim-times within window)
scheduler.add_event("Replay: arm bursts", trigger_time=1_280.0,
                    pre_trigger=lambda a: replay_seq.arm_random_bursts(),
                    command="noop", args={}, description="...")

# A7 / A8 / A11 — jammer events use commands.jammer_start
# with live_enemy_frequencies, identical to orbital_sentinel.py.
```

`Scenario.run` already drives `on_session` → `seq.tick(session["time"])` forwarding; the new helpers expose a matching `tick(sim_time)`.

> **New code additions to `src/cyber_replay.py`**:
>
> - `MultiTeamCaptureSequence` — owns `dict[team_id, list[CapturedWire]]`, cycles `tune_ground` across each team's RF with a configurable dwell.
> - `MultiTeamReplaySequence` — given a capture pool and a `(start, end)` sim window, schedules `N` random **round times**; at each time, **loops every blue team**, picks a random capture from **that** team's pool, and calls `replay_transmit_bytes` on the live team frequency.

> **New code addition to `src/commands.py` (or a small `src/jamming.py`)**:
>
> - `schedule_jammer_pulses(scheduler, *, name, start, end, on_seconds, period_seconds, frequencies_resolver, power)` — emits an alternating `jammer_start` / `jammer_stop` event sequence to produce a duty-cycle pulse over `[start, end]`. `frequencies_resolver` is called per ON pulse so live frequency rotations are picked up without rewriting the schedule. Used by A7 (light uplink jam) and is generally useful for any future "intermittent denial" pattern.

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
4. **A10 GPS logical field order** — Documented from `GPSDataMessage.cs` (§A10); **packed byte offsets** still confirmed via XTCE / dry-run.
5. **Capture / replay cadence** — **First half** of session: multi-team **capture** only. **Second half**: **random replay bursts** (plus jams). Per-team quota **`X = 2`** if `len(enemy_teams) ≤ 2`, else **`X = 3`** (`cyber_defender.py`).
6. **`T_AOI_1` / `T_AOI_2`** — Instructor to validate against GPS trace (**ongoing**).
7. **A7 uplink-jam duty** — **20%** design target; **tune after more testing** if observed ack-rate does not match.

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
