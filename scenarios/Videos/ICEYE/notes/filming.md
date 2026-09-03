# Reading Intent in Orbit — filming notes

Capability: **Custody Under Threat**. Scenario: ICEYE-X36 against a five-vehicle Cosmos approach.

Internal filming kit for a 3–4 minute video. Load and film each section separately; do not try to record one uninterrupted simulation.

## The line the video must leave behind

> If five spacecraft quietly begin converging on one of yours, when do you notice, when do you call it hostile, and what can you actually do about it by then?

Target runtime: **4:00** cutting short throughout, **4:45** cutting long.

- Section 1 — 0:41–0:49, 4 shots
- Section 2 — 0:55–1:04, 4 shots
- Section 3 — 0:54–1:05, 5 shots
- Section 4 — 0:52–1:01, 4 shots
- Section 5 — 0:38–0:46, 4 shots

Every shot owns exactly one narration paragraph, and its length is set by how long that paragraph takes to speak at roughly 150 words per minute plus about two seconds of air. `narrative.md` holds the authoritative shot-by-shot narration; do not re-derive timings here. Record 2–3 seconds of clean handles around every take, and run `python scripts/check_timing.py` after changing narration or durations.

## Generate and load

From the repository root:

```powershell
python "scenarios/Videos/ICEYE/scripts/generate_scenarios.py"
python "scenarios/Videos/ICEYE/scripts/generate_scenarios.py" --check
```

Copy or load `config/section_1.json` through `config/section_5.json` in Studio. Every file is a clean retake point. If a take goes wrong, stop and reload that section instead of trying to recover the timeline.

Blue login:

- Team: `Blue`
- Team ID: `591036`
- Password: `X36SDA`

The five Cosmos spacecraft are neutral: Blue can select and point at them, but cannot command them or read their internal telemetry. That is intentional.

## Preflight before every take

1. Load the required section JSON and confirm the title is `Intent in Orbit - Stage N`.
2. In Studio, enable labels and assign cyan to the ICEYE trail and red/orange to the five Cosmos trails if the current Studio build exposes overlay colors. Spacecraft JSON does not set per-asset colors.
3. Confirm only ICEYE-X36 and, in Sections 4–5, `SDA Overwatch` are controllable by Blue.
4. Open the Operator UI in advance and select the required Blue spacecraft.
5. Open only the panels needed for the take. Hide unrelated telemetry.
6. Set Studio orbit trails/plane overlays and labels before recording.
7. Pause at a clean frame. Start the screen recording, then resume.
8. Keep the evidence-boundary wording visible or in narration whenever filming Section 3 or the Overwatch asset.

## Simulation speed — why nothing runs faster than 8×

All five sections use the **Euler** integrator at a **0.1 s step**, which caps usable simulation speed at **8×**. Raising the step size would buy more speed, but it coarsens attitude integration enough that reaction-wheel slews stop looking smooth, and every section either films a pointing command or depends on the orbit geometry holding.

Sections 2, 3, and 5 previously ran at 30–60×. They are now all 8×. Section 3 was the worst case: at 60× the step size needed is 0.75 s, and forward Euler at that step drifts **148 km in altitude and 1,637 km in position** over the section's 12,793 s. The illustrative close phasing uses along-track offsets of 0.18–0.70°, roughly 20–80 km, so that error does not just degrade the shot, it erases the formation entirely. At 8× the same run drifts about 20 km, and the first few minutes are essentially exact.

**Speed long stretches up in the edit, not in the simulator.** Real recording time per section at these settings:

| Section | Sim time | Speed | Real recording time |
| --- | --- | --- | --- |
| 1 | 900 s | 8× | 1 min 52 s |
| 2 | 1800 s | 8× | 3 min 45 s |
| 3 | 12793 s | 8× | 26 min 39 s (see note) |
| 4 | 1200 s | 5× | 4 min 00 s |
| 5 | 1800 s | 8× | 3 min 45 s |

Section 3's `end_time` is a safety net, not a shot length. Stage 3 loads with the close geometry already in place, so film the first minute or two and stop — you do not need to sit through the full run.

The generator enforces this: `base_scenario` raises if any section asks for more than 8×, and `--check` asserts the integrator, step size, and speed cap on all five files.

## Ground station network

All sections use `Anchorage`, `Vancouver`, `Reykjavik` at a 5° elevation mask. This is a deliberately northern network, which is what a real near-polar SAR operator uses, and it gives roughly 20% contact over each 95-minute orbit.

Every section starts at the same epoch, with ICEYE-X36 at 81.6°N, 72.1°W descending over Arctic Canada. **There is no station contact for the first 185 s of sim time.** Anchorage acquires at T+185 s and Vancouver at T+290 s. Reykjavik only comes into view later in the orbit (T+5110 s), so it matters for Section 3's long run but not for the short sections.

If you need a downlink on camera, film it after T+185 s. Attempting it during the polar opening is the failure the network cannot fix — no preset station in the Studio library sees that part of the track.

## Evidence boundary — do not improvise these claims

Safe to say:

- Five Cosmos spacecraft moved from roughly 96.96° inclination toward ICEYE-X36 near 97.84°.
- The supplied reconstruction contains 11 inclination steps.
- Reconstructed total Delta-V is approximately 108–117 m/s per Cosmos.
- Spaceflux supplied optical observations for Cosmos 2610, 2612, 2613, and 2614.
- A repeated fleet-level pattern becomes more meaningful than any individual manoeuvre.

Always qualify:

- Exact burn times are illustrative. Catalogue history only bounds each change.
- Exercise timing is compressed.
- Section 3's close grouping is an **illustrative phasing continuation** after inclination matching, flown by RPO flight software. Its Delta-V is a simulator artefact and is unrelated to the reconstructed 108–117 m/s.
- `SDA Overwatch` is a **fictional Blue orbital sensor** used to demonstrate Operator tasking.
- The Camera-class `SAR-X36 X-Band Imaging Payload` is a visual stand-in for imaging command flow; it does not model SAR phenomenology.

Do not say:

- That the scenario reconstructs a historical 13 km approach.
- That Spaceflux measured ICEYE-X36 or Cosmos 2611 in this delivery.
- That Spaceflux operates the fictional Overwatch spacecraft.
- That matching inclination alone means the full orbital planes or spacecraft positions coincide.
- That the on-screen maritime target was a real ICEYE collection.

## Section 1 — nominal operations

Load: `config/section_1.json`

Purpose: establish ICEYE-X36 as useful civil infrastructure with a stable, ordinary routine.

### Setup

1. Keep the simulation paused.
2. In Studio, frame Earth with the labelled ICEYE-X36 orbit and hide broad catalogue clutter.
3. The five Cosmos are not in `config/section_1.json` at all, so there is nothing to hide and no label to leak. They first appear in Stage 2.
4. In Operator, select `ICEYE-X36`.
5. Open Guidance, Camera, GPS/position telemetry, Storage, and Downlink.
6. The two vessels in Viscount Melville Sound (Northwest Passage) are illustrative neutral maritime targets.
7. `SAR-X36 X-Band Imaging Payload` uses the simulator's Camera component. Film it as a product workflow, not as a claim that the rendered image is physics-true SAR.

### Pass geometry — read this before the take

The section is 900 s of sim time at 8× speed, so about 112 s of real recording. Timings below are sim time.

| Sim time | Sub-satellite point | What is available |
| --- | --- | --- |
| T+0 s | 81.6°N, 72.1°W | Over the Arctic north of Ellesmere Island. **No ground station in view.** |
| T+120 s | 76.8°N, 104.9°W | Vessels pass **directly overhead** (90° elevation). Best capture moment. |
| T+185 s | 73.5°N, 113.2°W | **Anchorage acquires.** First downlink opportunity. |
| T+290–820 s | Arctic Canada into the eastern Pacific | **Vancouver in view**, peaking at 32°. Strongest link for the downlink shot. |
| T+405 s | 62.0°N, 125.5°W | Vessels drop below 5° elevation. Capture window closes. |

The polar start has no coverage from any preset station — Reykjavik is the closest and sits at 1.3°, below the horizon mask. Do not try to downlink before T+185 s; it will fail. Use the pre-AOS stretch as the "quiet routine" establishing shot and let Anchorage acquisition be the beat that starts the tasking sequence.

### Operator actions to film

1. Guidance → point `SAR-X36 X-Band Imaging Payload` at the ground target. Prefer **target pointing at `GO_MARITIME_01`** over nadir; it holds the vessels centred across the whole T+0–405 s window instead of only the few seconds around T+120 s.
2. Camera → configure `SAR-X36 X-Band Imaging Payload` to a moderate field of view, approximately 12°.
3. Capture → name the image `Nominal_Maritime_Task`. Aim for T+100–150 s if you want the overhead look.
4. Downlink the capture once Anchorage or Vancouver is in view (T+185 s onward).

Allow time between guidance and capture for the spacecraft to slew. If the image misses the vessels, keep the Operator action shot and use a separate Studio beauty shot of the ground target.

### Studio shots

- Wide Earth view: one labelled orbital plane and one predictable spacecraft.
- Medium tracking shot following ICEYE-X36 over the Arctic.
- Brief cut to the two maritime vessels in the Northwest Passage, or the image result.
- Optional GPS telemetry close-up showing a stable near-polar orbit.

### Talk track

“ICEYE-X36 is a small commercial radar-imaging satellite. It spends each orbit doing ordinary, useful work: revisiting targets, collecting imagery and downlinking it to customers. This is civil infrastructure that defence users also depend on. At first, the picture is simple—one asset, one stable plane, one predictable routine.”

### Exit frame

End on the clean ICEYE orbit. Cut before introducing the Cosmos tracks.

## Section 2 — the pattern emerges

Load: `config/section_2.json`

Purpose: show why one change is ambiguous and several related changes are a warning.

This section is a staged decision-point view fixed at **16 May 2026**, a real moment in the catalogue chronology. Cosmos 2613, 2610, and 2612 have each finished their entire inclination campaign and now sit on ICEYE's plane. Cosmos 2611 and 2614 have not moved at all and will not until 20–21 May.

| Spacecraft | Inclination here | State |
| --- | --- | --- |
| ICEYE-X36 | 97.838° | never manoeuvres |
| COSMOS 2612 | 97.851° | campaign complete |
| COSMOS 2610 | 97.796° | campaign complete |
| COSMOS 2613 | 97.780° | campaign complete |
| COSMOS 2614 | 96.960° | untouched |
| COSMOS 2611 | 96.951° | untouched |

### Read this before planning shots

**Nothing manoeuvres during this section, and no camera work can hide that.** The simulator has no scheduled-impulse event — spacecraft events cover component faults, thruster firing, and RPO only — so inclination cannot evolve on the clock. The planes are frozen at their 16 May values before the clock starts.

This matters because Section 2's content is a **time series**: eleven inclination steps spread over eight days. A 3D orbit view can only ever render one instant of that. This is why multiple Studio angles of this scene all look identical — they are the same frozen picture with different annotations, and stacking three of them will read as dead air.

So Studio is demoted to a single establishing shot here, and **an animated inclination-versus-date chart carries the section**. The chart is the only representation that can show the change, and it is a direct plot of `data/e2_range_burns_catalog_timing.csv`, which makes it the most defensible frame in the video.

Three of five is the point. Do not imply the whole fleet has committed yet; that is Stage 3.

### What actually moves in this file

The complete list, so you plan against it rather than around it:

- The six spacecraft advancing along their orbits at 8×.
- ICEYE's commanded attitude slew, roughly 5–15 s of real recording.
- Earth rolling beneath the `SAR-X36 X-Band Imaging Payload` camera — the only sustained dynamic footage in the section.
- The Operator panel updating ICEYE's own telemetry.

### Two constraints that shape the shots

**Use short comet-tail trails, not full orbit rings.** Full rings are fixed in inertial space, so the frame is genuinely frozen and the spacecraft are lost against their own tracks. Short tails give you six visibly moving objects whose displacement out of ICEYE's plane grows and shrinks as they travel. Run live at 8× rather than paused, and speed the footage up in the edit.

**Operator cannot show Cosmos data.** Neutral craft deliberately expose no telemetry — `GroundController` rejects the request with "is neutral and does not expose telemetry." Operator here is **ICEYE-only**. Every cross-craft inclination comparison must be a Studio label or an edit overlay.

### Geometry: where and when to point the camera

At **T+0 the geometry is already optimal.** ICEYE starts at 81.6°N against a maximum reachable latitude of 82.2°, so the scene opens at the pole where the planes are at maximum separation. Cosmos 2613 (79.9°N) and Cosmos 2614 (80.4°N) are up there with it — 2613 has completed its campaign, 2614 has not moved — so a single polar frame at T+0 holds the entire thesis.

Maximum out-of-plane distance from ICEYE, which is what the camera is actually showing:

| Spacecraft | Δi vs ICEYE | Max cross-track |
| --- | --- | --- |
| COSMOS 2612 | 0.013° | 1.6 km |
| COSMOS 2610 | 0.041° | 5.0 km |
| COSMOS 2613 | 0.058° | 7.0 km |
| COSMOS 2614 | 0.877° | 105.9 km |
| COSMOS 2611 | 0.887° | 107.0 km |

Two consequences. First, **frame near maximum latitude, never near the equator** — separation collapses to zero at the node crossings and the section's whole point vanishes. Second, the three completed craft sit within 7 km of ICEYE's plane and read as a **single bundle**; you cannot tell them apart geometrically. The picture is binary — one bundle, two strays at ~106 km — and the "which one moved first" detail must come from the chart, not the orbit view.

The best angle is edge-on down the line of nodes, near RAAN 271.5°, where both planes collapse to lines and the difference appears directly as the angle between them. From overhead the same difference is nearly invisible, so a move from overhead to edge-on works as a reveal in itself.

Note the spacecraft are **not** clustered in this section; the along-track grouping applies only to Sections 3–5. At T+0 they sit at arguments of latitude of roughly 6°, 18°, 54°, 84° and 97°.

### The chart (section centrepiece — already rendered)

**This is built and ready. You do not need to make a graphic.**

```
python "scenarios/Videos/ICEYE/scripts/make_chart.py"           # Section 2 Shot 2, playhead stops 16 May
python "scenarios/Videos/ICEYE/scripts/make_chart.py" --full    # Section 3 Shot 1, resumes 16 -> 21 May
```

Ready-to-use MP4s are in `videos/media/2-chart.mp4` and `videos/media/3-chart.mp4`. The numbered 1920×1080 PNG sequences are in `videos/chart_frames/` and `videos/chart_frames_full/`. Import a PNG folder as an **image sequence at 20 fps** only if you prefer the lossless source — 260 frames, 13.0 seconds. Trim it to whatever the narration needs; the last three seconds are a static hold on the final state, so it cuts anywhere in that tail.

The timing is 2 s hold on 14 May, an 8 s sweep, then a 3 s hold. Adjust `HOLD_IN_S`, `SWEEP_S` and `HOLD_OUT_S` at the top of the script and re-run if you want a different shape. Colours, fonts and the dark background are set to sit against Studio footage.

The `--full` variant is **Section 3 Shot 1**, where the remaining two craft complete. It resumes at the 16 May stop rather than replaying from 14 May, so its first frame is pixel-identical to the Section 2 render's last frame — hold on that frame at the end of Section 2 and the cut into Section 3 is invisible. Both variants share a colour per spacecraft, so lines already converged stay put. Pass `--from-start` if you ever want the full 14 May replay instead.

How it is built, for reference:

- **X axis:** 14 May to 21 May 2026.
- **Y axis:** 96.9° to 98.0° inclination.
- **ICEYE-X36:** flat cyan reference line at 97.838°, labelled `DESTINATION PLANE`.
- **Five Cosmos:** step functions, one colour each, dimmed until they move.
- **Playhead:** sweeps left to right, halting at **16 May 12:00** — the moment `config/section_2.json` depicts.
- **Counter:** `COMPLETED n of 5` in the top right, which is the three-of-five beat in a single number.

Starting inclinations: 2610 96.958°, 2611 96.951°, 2612 96.964°, 2613 96.965°, 2614 96.960°.

Step schedule, in catalogue order:

| Node (UTC) | Spacecraft | Δi | Result |
| --- | --- | ---: | ---: |
| 2026-05-14T04:24 | COSMOS 2613 | +0.3362° | 97.301° |
| 2026-05-14T11:34 | COSMOS 2613 | +0.4145° | 97.716° |
| 2026-05-14T23:31 | COSMOS 2613 | +0.0640° | **97.780° complete** |
| 2026-05-15T08:36 | COSMOS 2610 | +0.7678° | 97.725° |
| 2026-05-15T22:46 | COSMOS 2612 | +0.2897° | 97.254° |
| 2026-05-15T23:44 | COSMOS 2610 | +0.0711° | **97.796° complete** |
| 2026-05-16T10:43 | COSMOS 2612 | +0.5968° | **97.851° complete** |
| 2026-05-20T05:03 | COSMOS 2611 | +0.3316° | 97.282° |
| 2026-05-20T16:13 | COSMOS 2611 | +0.5194° | 97.802° |
| 2026-05-21T02:48 | COSMOS 2614 | +0.3355° | 97.296° |
| 2026-05-21T14:46 | COSMOS 2614 | +0.4820° | 97.778° |

Everything from 20 May onward sits to the **right of the playhead** — greyed, dashed or hidden. Those steps are Section 3's material; revealing them here collapses the ambiguity this section exists to establish.

The dramatic beat is the shape: 2613 climbs alone, then 2610 follows on the same trajectory, then 2612. Three converging lines and two flat ones. Hold on that.

### Shots

Roughly 55–64 s in the edit across four distinct textures. Only the last two need the simulation running. One narration paragraph per shot; see `narrative.md` for the exact wording.

1. **Studio establishing shot, 14–16 s.** Short comet-tail trails, labels on all six. Open overhead at the pole where the orbits look concentric, then move to edge-on down the line of nodes until the bundle and the two strays separate. Callout `16 MAY 2026`. Resist adding a second angle.
2. **Chart, 23–26 s.** The rendered source is 13.0 s, so retime it to approximately 55% or extend its final hold. This is the longest narration block in the video. Callouts `FIRST: 2613 — AMBIGUOUS`, then `2610`, `2612`, then `THREE OF FIVE`.
3. **Operator, 8–10 s, running at 8×.** Select `ICEYE-X36` and command a nadir imaging slew. Show the command going out and attitude and reaction-wheel telemetry responding. ICEYE is carrying on with routine work while the pattern assembles around it. Callout `ICEYE-X36 — ROUTINE TASKING`.
4. **Payload view, 10–12 s, running at 8×.** Cut to the `SAR-X36 X-Band Imaging Payload` camera. Earth through the sensor is a completely different image and is what breaks the rings-on-black monotony. The section's sharpest line lands over this calm image, so do not cut it short.

Do not have the Cosmos point at or track ICEYE in **Section 2**. It would destroy the ambiguity this section is built on. Reserve that explicitly illustrative escalation for Cosmos 2614 at inspection range in Section 3.

### Talk track

Use the exact Section 2 spoken script in `narrative.md`. It is four paragraphs, one per shot above, in order.

### On-screen callouts

- First burn: **ambiguous**
- Repeated direction: **pattern**
- Destination plane: **ICEYE-X36 inclination**
- Exact impulse timing: **illustrative**

### Exit frame

Hold on the chart with three lines converged and two still flat, under the unanswered question: “When is this enough to act?” Match-cut from there into Section 3's completed geometry.

## Section 3 — coercive proximity

Load: `config/section_3.json`

Purpose: show the completed fleet commitment and the threat of repeatable access, without inventing a kinetic attack.

The final inclination values are evidence-backed by the supplied reconstruction. The close along-track grouping is not; it is a labelled illustrative continuation.

### The approach is flown live by RPO

Unlike every other section, something actually manoeuvres here. All five Cosmos have `enable_rpo_software: true` and rendezvous events fly them in.

`rendezvous` engages a **station-keeping hold**, not a one-shot transfer: the craft flies to the offset and stays there until released. Each later phase is the same command re-issued with a new offset. Axes are X radial, Y along-track, Z orbit-normal.

| Sim time | Real time at 8× | Spacecraft | Goes to | Speed | Beat |
| --- | --- | --- | --- | --- | --- |
| T+60 s | 0:08 | all five | 2.9–8.1 km | 40 m/s | the fleet closes in |
| T+3000 s | 6:15 | 2614 | 1.0 km | 2 m/s | tightens to inspection range |
| T+3000 s | 6:15 | 2614 | points optical camera at ICEYE | reaction wheels | begins inspection |
| T+4800 s | 10:00 | 2614 | 6.0 km | 8 m/s | withdraws to standoff |

Starting distances are 22 km (2610), 34 km (2611), 51 km (2612), 66 km (2613), 85 km (2614). Closure stations are `[0, -8000, 1500]`, `[1500, 6500, -2000]`, `[-2000, -5000, -2500]`, `[2500, 4000, 2000]` and `[-1000, -2500, 1000]` respectively. 2614 is held closest because Stage 4 uses it as the custody target.

The 2614 sequence exists to earn the narration line about the ability to approach **repeatedly**. A single closure only shows arrival. Close, hold, tighten, withdraw shows access at will, which is the actual threat being described.

At T+3000 s, a Guidance event also points COSMOS 2614's `OCS-410 Narrow-Field Inspection Camera` at ICEYE-X36. It uses relative pointing with the camera's `+z` working face and a 0.5° field of view. Let the final approach and reaction-wheel slew settle before opening the camera feed; the best image is near the 1 km hold, not at the initial 2.9 km station.

This camera and its attitude are invented for the film. The supplied data contains no payload manifest or attitude history for Cosmos 2614. Keep `ILLUSTRATIVE OPTICAL INSPECTION — NO ATTITUDE OR PAYLOAD DATA` visible for the entire optical view.

**These events require a patched build.** As originally shipped, the rendezvous event resolved its target only within the chaser's own team (`SpacecraftController.cpp`, `ExecuteEvent`). The Cosmos are neutral and therefore sit on the sentinel team `-1`, while ICEYE-X36 belongs to Blue, so every event logged `could not resolve target asset 'SC_ICEYE_X36' for team -1` and returned without moving anything. The resolver now falls back to neutral craft and then to a globally unique match, via `USpacecraftController::ResolveEventTargetAsset`. If the Cosmos sit still and you see that warning in the log, you are on an unpatched binary.

`Max Speed` and `Approach Acceleration` are absent from the documented event `Data` table, but the handler does read them — key lookup strips spaces and ignores case, so `"Max Speed"` reaches the command as `max_speed`. The trapezoidal ramp is live.

**Expect one tuning pass in Studio; these speeds are unverified against a live run.** If the transit reads as a missile rather than a manoeuvre, drop `RPO_TRANSIT_MAX_SPEED_M_S`. If it drags, raise it.

Each LVLH axis is clamped to ±10 km by the command, so stations cannot sit further out than that. This is why RPO works here as a final closure and could not have staged the whole week of phasing.

Two honesty notes for this section. The closure's ΔV is whatever the controller spends — **not** the reconstructed 108–117 m/s, so never put both numbers in the same frame. And because these Cosmos carry no thrusters, SpaceRange flies them with an `External Force Torque`, meaning the approach and the hold cost no propellant and look perfectly steady. That is a simulator convenience, not a real capability, which is another reason the illustrative caption stays on screen throughout.

### Setup

1. Confirm the scenario brief contains the evidence warning.
2. Run at 8× and compress in the edit; the section cannot run faster without breaking the formation.
3. Frame the orbital planes from far enough away to show they have nearly converged.
4. Let the approach run, then move to a close formation view around ICEYE-X36.
5. Keep the Cosmos labels visible in at least one shot so the audience sees five distinct vehicles.

### Shots

1. **Shot 1 is the second chart render, not Studio footage.** Use `videos/media/3-chart.mp4`. It resumes at the 16 May stop, so its first frame is identical to the Section 2 chart's last frame and the two cut together invisibly; the sweep then runs 16 to 21 May and 2611 and 2614 finally step up to `5 of 5`. This is the shot that carries the eleven-steps and delta-V claim, because Studio cannot show either.
2. Wide Studio shot before T+60 s: all five near the ICEYE inclination but still tens of km out. Overlay or title: `11 selected inclination steps`.
3. Overlay or title: `~108–117 m/s per spacecraft`.
4. Let the RPO approach run and film the five closing in. This is the section's money shot.
5. Cover the 2614 repeat sequence: it tightens to 1 km at T+3000 s, then withdraws to 6 km at T+4800 s. Cut these together tightly so the "we can come back whenever we like" point lands.
6. After the slew settles near the 1 km hold, show an exterior angle of 2614 tracking ICEYE and then cut to the `OCS-410 Narrow-Field Inspection Camera` feed for **14–17 s in the edit**. Record at least 20 s so both narration sentences and the disclosure have room.
7. Put `ILLUSTRATIVE PHASING — NOT A RECONSTRUCTED CLOSE APPROACH` on screen throughout the approach and grouping.
8. During the optical feed, replace it with `ILLUSTRATIVE OPTICAL INSPECTION — NO ATTITUDE OR PAYLOAD DATA`.
9. Hold a closing caption that separates the two: `INCLINATION CAMPAIGN: RECONSTRUCTED · CLOSE PHASING: ILLUSTRATIVE`. Never let the grouping shot run without one of these on screen.

The eleven inclination burns are still **not** executed here; the section loads with them already applied. Show that convergence with a match cut from Stage 2. What runs live is only the final proximity closure.

### Talk track

“Across the group, the changes add up to eleven selected inclination steps and roughly 108 to 117 metres per second per spacecraft. That is not accidental drift. It is a large, deliberate commitment. Once the planes are accessible, phasing can turn access into persistent proximity: inspection, shadowing and the message that the asset can be reached again at will. At inspection range, narrow-field optical collection becomes possible; the view shown here is illustrative, not a reconstructed observation.”

Optional final sentence:

“This close grouping is an illustrative continuation; the defensible fact underneath it is the fleet-wide inclination commitment.”

### Do not add

- No jamming, dazzling, collision, or kinetic effect.
- No 13 km caption.
- No Spaceflux logo over ICEYE or Cosmos 2611 data.

### Exit frame

End with ICEYE visually surrounded but still operating. The threat is coercive proximity, not destruction.

## Section 4 — Blue tightens custody

Load: `config/section_4.json`

Purpose: show an operator doing something realistic and useful without pretending ICEYE can outrun five committed vehicles.

### Setup

Section 4 is a staged continuation, not a replay of Section 3's approach:

- Epoch: `2026/05/14 22:00:00`, 22 hours after the other sections so Earth and the ground track begin in a visibly different orientation.
- Cosmos 2614 starts about **1 km from ICEYE-X36**.
- Cosmos 2610–2613 start at separate illustrative stations roughly **4–8 km from ICEYE-X36**.
- SDA Overwatch starts about **5 km radially outside Cosmos 2614**, close enough for optical and radar custody at T+0.
- These positions are illustrative and do not reconstruct historical phasing.

1. In Operator, select `SDA Overwatch`.
2. Open Guidance, Camera, Radar/range telemetry, Capture, and Downlink.
3. Choose `COSMOS 2614` for the main take.
4. Keep simulation speed at 5× or lower while interacting.
5. In Studio, use split shots: Overwatch-to-target line of sight, then the seven-object geometry.
6. ICEYE-X36 has no camera in this section and is already slewed to nadir at T+0. Do not open an ICEYE or Cosmos camera view.

### Operator actions to film

1. Guidance → relative pointing.
2. Target component: `SBR-900 Space Surveillance Radar`, `OTC-450 Optical Tracking Camera` or `EVS-450 Neuromorphic Event Camera`.
3. Target spacecraft: `COSMOS 2614`.
4. Apply guidance and wait for the slew.
5. Capture with `OTC-450 Optical Tracking Camera` (monochromatic) or `EVS-450 Neuromorphic Event Camera` (monochromatic, event mode), name it `COSMOS_2614_Custody`.
6. Hold `SBR-900 Space Surveillance Radar`/`LRP-1550 Laser Ranging Payload` on the target long enough to show range updates.
7. Downlink the observation.

The Guidance command rotates the selected Overwatch payload; it does not translate the spacecraft. Do not wait for an approach manoeuvre—Overwatch and Cosmos 2614 already begin approximately 5 km apart.

If radar telemetry is not visually useful in the current build, film the pointing/capture command and use Studio range/track overlays for the custody result. Do not substitute a fake Spaceflux spacecraft label.

### Talk track

“Evasion is not the attractive answer. Every metre per second ICEYE spends is mission life it never gets back, and all five vehicles have already shown they will pay to follow. Blue’s immediate lever is custody: task another sensor, increase revisit, sharpen the orbit solution and preserve the evidence needed for attribution.”

Optional second sentence:

“A small phasing adjustment may complicate one pass, but it does not break contact with a committed five-vehicle group.”

### Required disclosure

Show once, either as a lower third or narration:

`SDA Overwatch is a fictional orbital sensor used to demonstrate tasking.`

Then separately:

`Spaceflux observations cover Cosmos 2610, 2612, 2613 and 2614.`

### Exit frame

End on improving track/range updates, not on a Blue manoeuvre.

## Section 5 — debrief and replay

Load: `config/section_5.json`

Purpose: return to the point where action was still cheap and evidence was still incomplete.

### Setup

1. Start with the partially converged state.
2. Run at 8× briefly, then pause at the staged pattern. Speed the stretch up in the edit if it needs to feel faster.
3. If useful, intercut one second each from Sections 1, 2, 3, and 4.
4. The decision-window point is made in narration and on-screen text, not by an in-sim Task.

### Shots

1. Select `Days 2–3, when the repeated pattern emerges`.
2. Show a rapid before/after:
   - sparse custody / wait;
   - additional sensor tasked.
3. Reset or reload once on camera to establish replayability.
4. End on the partially converged plane view, not the final surround.

### Talk track

“The warning was visible before the close geometry—written in cumulative behaviour and propellant. By the time all five had committed, Blue was reacting. The useful decision point was earlier, when the evidence was weakest but the options were still cheapest.”

Final line:

“If this were your spacecraft, when would you call the pattern hostile?”

## Suggested edit rhythm

- Use Studio for orbital-scale truth: planes, trails, labels, relative geometry and time compression.
- Use Operator for agency: guidance, sensor selection, capture, range and downlink.
- Do not leave any form open long enough to become a software tutorial.
- Cut on completed actions, not on mouse travel.
- Prefer one clean command per Operator shot.
- Record clean plates of every Studio view without labels in case text is added in post.
- Record each evidence disclaimer as both a visible lower third and a clean narration take.

## Source notes

The generator transcribes the scenario inputs needed for filming from:

- `e2_range_initial_conditions.csv`
- `e2_range_burns.csv`
- `e2_range_burns_catalog_timing.csv`
- `e2_range_ics.json`
- `e2_space_range_brief.md`

The two `layer1_59103_ICEYE-X36*.csv` files are not used. Their Time 0 position does not match the supplied May 14 TEME initial condition, and the CSV does not carry an epoch or frame.

## Fast troubleshooting

- Missing spacecraft: check the Studio load log for a partial JSON parse.
- Cosmos controllable by Blue: verify they remain listed in `assets.neutral`.
- Cosmos absent in Section 1: expected; they are not in that file.
- Cosmos labels visible when the craft are not: you are on an older `config/section_1.json`. Regenerate — hidden assets still draw Studio labels, which is why Section 1 now omits them outright.
- Camera capture is empty: reapply guidance, wait for slew, widen FOV, and capture again.
- No useful range result: slow the simulation, use Cosmos 2614, and verify the tracking sensor is pointed at the spacecraft centre.
- Orbit planes do not read on camera: exaggerate the visual camera angle, not the orbital data.
- Section 3 looks like a historical reconstruction: add the illustrative-phasing lower third before using the shot.
- Retake is drifting: reload the section JSON rather than rewinding manually.
