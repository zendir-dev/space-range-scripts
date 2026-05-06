# Orbital Sentinel - Scenario Specification

> **Status**: design documentation for the implemented scenario.
> **Audience**: scenario author, instructor, Python-script maintainer.
> **Source of truth**: `orbital_sentinel.json` and `orbital_sentinel.py`.

---

## 1. One-line Pitch

Orbital Sentinel is a maritime surveillance exercise where multiple blue teams operate a shared imaging / sensing spacecraft, inspect three geographically separated maritime tasking areas, and then identify and mitigate interference from a co-orbital rogue spacecraft.

---

## 2. Learning Objectives

By the end of the scenario, an operator should be able to:

1. Use camera imagery and ground-object context to identify commercial, suspicious, and damaged vessels.
2. Compare current imagery against a reference brief to detect new construction near the Paracel Islands.
3. Cross-check visible vessel position, heading, speed, and identity against provided AIS data.
4. Diagnose a spacecraft component fault from telemetry.
5. Identify a rogue spacecraft using imagery and EM-sensor evidence.
6. Mitigate downlink jamming with frequency hopping.

---

## 3. Scenario Shape

| Quantity | Value |
| --- | --- |
| Epoch | `2025/04/15 07:30:00` |
| Sim speed | `5.0` |
| Step size | `0.12` |
| End time | `0.0` (open-ended; instructor controls session end) |
| Blue teams | 8 enabled teams in the `Main` collection |
| Rogue team | `Rogue`, controlling `SC_002` / `Recon` |
| Defender spacecraft | `SC_001` / `Microsat` |
| Rogue spacecraft | `SC_002` / `Recon`, hidden by default |

### Task Orders

| Task Order | Operational Theme | Primary Evidence | Question Section |
| --- | --- | --- | --- |
| 1. Red Sea Piracy | Identify suspicious / damaged vessels in the Bab el-Mandeb Strait. | Ground-object imagery and vessel colour / motion. | `Red Sea (Counter-Piracy)` |
| 2. South China Sea Island Construction | Locate new island construction and count nearby construction vessels. | Camera imagery near the Paracel Islands. | `South China Sea (Island Construction)` |
| 3. Coast of Venezuela AIS Verification | Identify vessels lying through AIS mismatch or AIS silence. | Visible vessel state vs mission-brief AIS data. | `Coast of Venezuela (AIS Verification)` |
| 4. Rogue Spacecraft | Diagnose downlink jamming, identify the rogue, and mitigate interference. | SNR drop, EM sensor, camera image of hidden rogue if acquired. | `Rogue Spacecraft` |

---

## 4. Orbit, Spacecraft, and Teams

### 4.1 Defender Orbit

```text
SMA           = 8 200 km
Eccentricity  = 0.02
Inclination   = 17.3 deg
RAAN          = 283 deg
ArgPerigee    = 0 deg
TrueAnomaly   = 360 deg
```

The orbit supports repeated maritime collection windows across low-latitude regions: the Red Sea / Bab el-Mandeb, South China Sea, and Caribbean / Venezuela operating areas. The orbital operations questions use this telemetry directly:

| Question | Answer |
| --- | --- |
| Semi-major axis | `8 200 km` |
| Eccentricity | `0.02` |
| Inclination | `17.3 deg` |

### 4.2 Rogue Orbit

```text
SMA           = 8 200 km
Eccentricity  = 0.0199
Inclination   = 17.3 deg
RAAN          = 283 deg
ArgPerigee    = 0 deg
TrueAnomaly   = 0.004 deg
```

`SC_002` (`Recon`) is near the defender and is configured with:

- `visualization.hide: true`, so the rogue is not presented as an obvious map target.
- `enable_rpo: true`, supporting proximity-operations style behaviour if extended later.
- A high-gain receiver, transmitter, and jammer.
- Text labels reading `RECON`, used by the rogue-identification question if teams image it.

### 4.3 Team Roster

The scenario has one rogue team and eight enabled blue teams:

| Team | Frequency (MHz) | Key | Collection |
| --- | ---: | ---: | --- |
| Rogue | 500 | 1 | `Rogue` |
| Team Blue | 612 | 42 | `Main` |
| Team Green | 745 | 87 | `Main` |
| Team Yellow | 889 | 154 | `Main` |
| Team Violet | 523 | 201 | `Main` |
| Team Cyan | 468 | 12 | `Main` |
| Team Pink | 901 | 233 | `Main` |
| Team Orange | 777 | 99 | `Main` |
| Team White | 655 | 176 | `Main` |

The Python script resolves all blue-team frequencies live just before jamming, so frequency hopping remains meaningful during the rogue phase.

---

## 5. Ground Stations

Configured ground stations:

```json
["Madrid", "Dubai", "Singapore", "Auckland", "Easter Island", "Salvador", "Miami"]
```

`min_elevation` is `0`, making this a broad-access training scenario rather than a strict horizon-mask exercise. The jamming questions focus on ground-station SNR during rogue activity, especially Singapore in the current script schedule.

---

## 6. Maritime Ground Objects

### 6.1 Red Sea / Bab el-Mandeb

Objects `GO_001` through `GO_011` create the Red Sea piracy tableau.

| Group | Objects | Meaning |
| --- | --- | --- |
| Commercial traffic | `EG01` - `EG07` | Seven large green ships in the strait. |
| Suspect / non-commercial vessels | `IR01`, `US01`, `US02`, `US03` | Coloured ships used for bad-actor identification. |

Question answers in `orbital_sentinel.json`:

| Question | Answer |
| --- | --- |
| How many commercial vessels in the strait? | `7` |
| How many vessels are currently damaged / stationary? | `2` |
| Identify the destructive vessel. | Yellow (`IR01`) |

Design intent: this task order is the initial image-interpretation exercise. Operators should learn to use camera pointing, FOV, and object motion before the later cyber / jamming layer appears.

### 6.2 South China Sea / Island Construction

Objects `GO_012` through `GO_016` are small black vessels near the Paracel Island group, plus `TX_01` as a text/map marker.

| Object Range | Location | Meaning |
| --- | --- | --- |
| `SC01` - `SC05` | Around `lat ~16.0-16.2`, `lon ~111.9-112.1` | Construction / support vessels near the new island. |
| `TX_01` | `lat 16.2`, `lon 112` | Visual marker for the island / construction AOI. |

Question answers:

| Question | Answer |
| --- | --- |
| New island latitude | `16.1 deg` |
| New island longitude | `112.0 deg` |
| Construction vessels near the island | `5` |

Design intent: this task order forces narrower camera work and comparison against the mission brief / reference photo. It is about persistent surveillance and change detection, not ship pursuit.

### 6.3 Coast of Venezuela / AIS Verification

Objects `GO_017` through `GO_022` create the AIS anomaly set.

| Object | Colour | Visible State | Question Use |
| --- | --- | --- | --- |
| `Iron Horizon` | Red | `lat 11.932`, `lon -63.547`, heading `85`, speed `4.4` | Normal AIS distractor. |
| `Ocean Tribute` | Violet | `lat 14.471`, `lon -62.871`, heading `120`, speed `6.6` | Normal AIS distractor. |
| `Harbor Sentinel` | Yellow | `lat 13.390`, `lon -60.362`, heading `290`, speed `5.5` | Normal AIS distractor. |
| `Golden Ballast` | Green | `lat 12.793`, `lon -65.922`, heading `185`, speed `3.9` | Lying about heading direction. |
| `Titan Manifest` | Cyan | `lat 15.517`, `lon -57.367`, heading `219`, speed `5.7` | Lying about longitude / position. |
| `Steel Voyager` | White | `lat 16.952`, `lon -67.196`, heading `340`, speed `3.9` | AIS transponder disabled / no matching AIS broadcast. |

Question answers:

| Question | Answer |
| --- | --- |
| Which vessel is lying about position? | Cyan (`Titan Manifest`) |
| Which vessel is lying about heading? | Green (`Golden Ballast`) |
| Which vessel disabled AIS / broadcasts no data? | White (`Steel Voyager`) |

Design intent: this is the main data-fusion task. Teams must not simply trust AIS; they need to compare a live visual / geospatial observation against the external data stream.

---

## 7. Event Timeline

The only JSON scenario event is a spacecraft component fault:

| Sim Time (s) | Event | Target | Training Purpose |
| ---: | --- | --- | --- |
| `6 000` | `Battery Power Spikes` | `Battery-IntermittentConnectionErrorModel` | Introduces a telemetry-diagnosed component fault; mitigation is a battery reset. |

The rogue script adds downlink-jamming windows:

| Sim Time (s) | Script Event | Notes |
| ---: | --- | --- |
| `100` | Point Nadir | Initial attitude setup. |
| `2 610` | Point Jammer to Singapore | Aim rogue jammer for first interference window. |
| `2 620` | Start Jamming All Enemy Teams | Uses live blue-team frequencies. |
| `4 458` | Stop Jamming | End first jamming window. |
| `4 459` | Point Nadir | Stand down / neutral attitude. |
| `10 680` | Point Jammer to Singapore | Aim for second interference window. |
| `10 689` | Start Jamming All Enemy Teams | Uses live blue-team frequencies. |
| `12 530` | Stop Jamming | End second jamming window. |
| `12 532` | Point Nadir | Stand down. |
| `18 846` | Point Jammer to Singapore | Aim for third interference window. |
| `18 847` | Start Jamming All Enemy Teams | Uses live blue-team frequencies. |
| `20 590` | Stop Jamming | End third jamming window. |

At `simulation.speed = 5.0`, these correspond to wall-clock times that are five times shorter than sim seconds. For example, the first jam begins at roughly `8 min 44 s` wall-clock after sim start (`2 620 / 5`).

---

## 8. Rogue Spacecraft Task Order

### 8.1 Interference Signature

The rogue effect is downlink jamming. In the question bank, teams identify:

| Question | Answer |
| --- | --- |
| What interference anomaly occurred? | Downlink jamming |
| Which ground station(s) were affected? | Singapore (`value: [6]` in current option order) |
| What mitigation resolves the anomaly? | Frequency hopping |
| Minimum SNR during anomaly | `15 dB` with `+/-2 dB` tolerance |
| Rogue identity | `RECON` |
| Rogue transmitter frequency | `500 MHz` |

> Note: the question reason text currently says "Dubai and Easter Island", while the answer value selects Singapore. Treat `answer.value` and the script's Singapore-pointing events as the current design intent; update the reason text if you want the explanation to match the implemented answer.

### 8.2 Script Mechanics

`orbital_sentinel.py` runs as the `Rogue` team and:

1. Creates a `Scenario(team_name="Rogue", config_path=...)`.
2. Schedules attitude events for `SC_002`'s `Jammer`.
3. Starts a jammer with `power=3.0`.
4. Uses a `pre_trigger` hook to resolve current enemy frequencies at fire-time:

```python
def live_jammer_args(default_args: dict) -> dict:
    freqs = scenario.live_enemy_frequencies()
    return {**default_args, "frequencies": freqs}
```

This makes frequency hopping relevant: the jammer targets the blue teams' current RF state when each jam starts, but teams can still hop afterward to recover service.

---

## 9. Question Framework

The JSON question bank is organized around the task orders plus orbital operations.

| Section | Score | Questions |
| --- | ---: | --- |
| Red Sea (Counter-Piracy) | `20` | Commercial-vessel count, damaged-vessel count, destructive vessel identification. |
| South China Sea (Island Construction) | `20` | New island latitude, longitude, and construction-vessel count. |
| Coast of Venezuela (AIS Verification) | `20` | Position liar, heading liar, AIS-silent vessel. |
| Rogue Spacecraft | `20` | Interference type, affected station, mitigation, minimum SNR, identity, transmitter frequency. |
| Orbital Operations | `20` | Battery fault, SMA, eccentricity, inclination. |
| **Total** | **100** | Balanced across maritime surveillance, cyber / RF diagnosis, and orbit basics. |

### 9.1 Assessment Notes

- The scenario relies on **colour and named object groups** heavily. Instructor briefs should preserve those mappings.
- AIS questions assume external mission-brief AIS data is available to students. The JSON itself contains the ground truth visible state, not the false AIS broadcast table.
- The rogue identity question assumes students can image the rogue or otherwise reveal the `RECON` text labels. If the workshop prefers EM-only attribution, revise the question to focus on the `500 MHz` carrier and scenario call-sign instead.
- The affected-ground-station question should be dry-run validated, because jamming results depend on link geometry, station visibility, and whether teams frequency-hop before / during the interference window.

---

## 10. Implementation Inventory

### `orbital_sentinel.json`

Contains:

- `simulation`, `universe`, and `ground_stations`.
- One rogue team and eight blue teams.
- Defender spacecraft `SC_001` (`Microsat`) with camera, GPS, EM sensor, comms, storage, and battery.
- Rogue spacecraft `SC_002` (`Recon`) with hidden visualization, high-gain RF components, and jammer.
- Ground objects for Red Sea, South China Sea, and Venezuela AIS task orders.
- One battery fault event at `6 000 s`.
- Full question bank, total score `100`.

### `orbital_sentinel.py`

Contains:

- CLI config override.
- Rogue `Scenario` setup.
- Live frequency resolver for all blue teams.
- Three jamming windows pointed at Singapore.
- No custom `on_session` loop; all active effects are scheduled events.

---

## 11. Dry-run Checklist

- [ ] Load `orbital_sentinel.json` and verify it parses.
- [ ] Confirm all eight blue teams can connect to `SC_001`.
- [ ] Confirm `SC_002` is hidden on the default map but can be imaged / detected through intended sensors.
- [ ] Capture reference screenshots or imagery for all three maritime AOIs.
- [ ] Validate the Red Sea count: seven large green commercial vessels, two stationary / damaged vessels, yellow suspect vessel.
- [ ] Validate the South China Sea count: island near `16.1, 112.0`, five small construction vessels.
- [ ] Validate the Venezuela AIS anomalies against the mission brief: cyan longitude, green heading, white AIS silence.
- [ ] Confirm battery spikes at `t=6 000 s` and that reset clears / mitigates the fault.
- [ ] Confirm jamming windows produce observable downlink SNR drops, with minimum SNR near `15 dB`.
- [ ] Confirm the affected-ground-station answer and reason text match observed telemetry.

---

## 12. Open Items

1. **Affected ground station wording**: current answer selects Singapore, but reason text mentions Dubai and Easter Island. Dry-run and align.
2. **Rogue identification path**: decide whether teams should identify `RECON` by camera imagery, EM sensor / frequency, or both.
3. **AIS brief artifact**: ensure the student-facing AIS table exists and intentionally disagrees with `GO_017` - `GO_022` as described.
4. **Jamming repetition**: three long jamming windows are implemented. Decide whether all three are intended for the workshop or whether later windows are backup opportunities.
