# Reading Intent in Orbit — Video Script

Capability: **Custody Under Threat**. Scenario: ICEYE-X36 against a five-vehicle Cosmos approach.

Target duration: **4:00** cutting on the short end of every shot, **4:45** if you take the long end throughout.

Every shot below owns exactly one narration paragraph, and its duration is set by how long that paragraph takes to speak plus about two seconds of air. Verify with `python scripts/check_timing.py` after editing either the narration or the durations.

This is the primary spoken and visual script. Record each section separately using `config/section_1.json` through `config/section_5.json`.

The story is:

> Five spacecraft begin quietly changing their orbits toward one commercial satellite. When does ordinary activity become a coordinated threat, and what can an operator still do by the time the pattern is clear?



## Recording style

- Use **Studio** for orbital geometry, spacecraft motion, labels, trails, time compression and cinematic views.
- Use **Operator** for mission activity, payload tasking, telemetry, sensor commands, downlink and decisions.
- Keep Operator shots short. Show the command being issued, then cut to the resulting telemetry or Studio view.
- Record clean Studio views both with and without labels.
- Do not film mouse travel, loading screens or scenario setup.
- Each section JSON is a clean retake point. Reload the section rather than manually rebuilding the state.



### Narration timing

- **Every shot owns exactly one narration paragraph.** No paragraph is split across shots and no shot runs silent.
- Shot durations are **edited screen time**, derived from the paragraph at roughly **150 words per minute** plus about two seconds of air. A 30-word paragraph needs about 14 seconds, not 6.
- Record the narration first. Let the delivery set the final cut length.
- Capture 2–3 seconds of clean handles before and after every take so the editor can extend a shot without freezing the image.
- After changing any narration or duration, run `python scripts/check_timing.py`. It fails if a shot lost its beat or is too short to speak it.

---



# Spoken narration

Read this in order. Record each section as its own take. About 480 words; at 150 words per minute that is roughly 3:15 of voice, and the remaining 45 seconds is breathing room for commands, chart changes, slews and disclosures.

Each paragraph below is one shot. The per-section entries repeat the same paragraph beside the shot it belongs to.

## Optional cold open

Use only if the edit needs 3–5 seconds before Section 1.

A close approach may be the final alert. The intent to create it can be visible days earlier.

## Section 1 — Nominal Operations

ICEYE-X36 is a commercial synthetic-aperture radar satellite operating in a near-polar orbit. Its mission is routine: revisit a target, collect imagery and return that information to customers on the ground.

Through the Zendir Space Range Operator interface, the team controls the spacecraft's pointing and payload tasking.

Here it images an Arctic maritime area, stores the product on board, and downlinks it on the next ground-station pass.

At this point, everything is nominal. One spacecraft, one stable orbital plane and one predictable operating rhythm.

## Section 2 — The Pattern Emerges

Five recently launched Cosmos spacecraft are operating near ICEYE-X36. On its own, that is not unusual. But three of them are no longer in the plane they launched into.

The orbital record shows how that happened. On the fourteenth of May, one spacecraft changes inclination. For a newly launched vehicle, that could still be explained as routine commissioning. The important indication is not the first change — it is the second spacecraft moving in the same direction, followed by a third.

Meanwhile, ICEYE-X36 carries on with routine tasking. Nothing in its own telemetry says anything has changed.

What looked like isolated activity is becoming a coordinated pattern — and all of it points toward one destination plane.

## Section 3 — Coercive Proximity

Across the group, the orbital record contains eleven selected inclination steps. The reconstructed cost is approximately 108 to 117 metres per second for each spacecraft.

That is not passive drift. It is a large and deliberate fleet-level commitment.

Once the destination plane is accessible, phasing can turn that access into sustained proximity: inspection, shadowing and the ability to repeatedly approach the asset.

The close grouping shown here is an illustrative continuation. The evidence underneath it is the coordinated inclination campaign.

At inspection range, proximity also enables narrow-field optical collection. Here, Cosmos 2614 is shown holding ICEYE-X36 in its field of view — an illustrative capability, not a reconstructed observation.

## Section 4 — Blue Tightens Custody

ICEYE-X36 cannot simply outrun five spacecraft that have already demonstrated this level of commitment. Every metre per second spent by the commercial asset is mission life it cannot recover.

Blue's immediate advantage is custody. The operator tasks an additional surveillance asset and points its optical and ranging payloads toward Cosmos 2614.

Independent observations begin to accumulate: imagery, range and range-rate, collected and downlinked without touching ICEYE.

Increased revisit, improved ranging and additional imagery sharpen the orbital picture. This gives the team better information for protection, attribution and the next operational decision — without immediately spending ICEYE's limited fuel.

## Section 5 — Debrief and Replay

During debrief, the scenario can be reset to the moment the pattern first became visible.

The warning existed well before the close geometry. It was written in cumulative behaviour and in the amount of propellant the fleet was prepared to spend.

The useful decision point was Days 2 to 3 — when the evidence was still incomplete, but low-cost responses were still available.

If this were your spacecraft, when would you call the pattern hostile?

## Optional product close

Use only after the final question if a product close is required.

Zendir enables operators to replay these decisions against realistic spacecraft systems and orbital behaviour — before the same pattern appears around a real asset.

## End-card text

On-screen only; do not speak this unless the edit needs a voiced attribution.

Initial conditions and inclination changes derived from public catalogue history. Exercise timing and close phasing are illustrative. Spaceflux supplied optical observations for Cosmos 2610, 2612, 2613 and 2614. ICEYE-X36 and Cosmos 2611 use catalogue data only.

---



# Section 1 — Nominal Operations

Load: `config/section_1.json`

Duration: **41–49 seconds** across 4 shots

## What happens

ICEYE-X36 begins in a nominal near-polar orbit conducting an illustrative commercial maritime imaging task. The five Cosmos spacecraft are not loaded in this section at all, so the opening view has exactly one spacecraft in it.

This section establishes three things:

1. ICEYE-X36 is a commercial Earth-observation asset.
2. Its operations are routine and predictable.
3. Nothing currently appears abnormal to the operator.

Do not introduce the Cosmos spacecraft yet.

## What to prepare



### Studio

1. Load `config/section_1.json`.
2. Pause the simulation.
3. Select ICEYE-X36 and enable its orbit trail.
4. Frame Earth and the spacecraft from a wide orbital view.
5. Prepare a second view following ICEYE-X36 over the Arctic maritime task area.



### Operator

1. Log in as Blue and select `ICEYE-X36`.
2. Open:
  - Guidance
  - Camera
  - GPS or position telemetry
  - Storage
  - Downlink
3. Select `SAR-X36 X-Band Imaging Payload`.
4. Prepare a guidance command that points the payload at `GO_MARITIME_01` rather than at nadir. Target pointing keeps the vessels centred for the whole T+0–405 s window; nadir only frames them for a few seconds around T+120 s.
5. Configure the payload to approximately 12° field of view.

The payload uses the simulator's Camera component to demonstrate the imaging workflow. The rendered result is not intended to reproduce SAR phenomenology.

**Timing constraint:** the pass starts over the pole with no ground station in view. Anchorage acquires at T+185 s and Vancouver at T+290 s. Shoot the capture early (T+100–150 s, when the vessels are overhead) and the downlink after T+185 s.

## What to record



### Shot 1 — Establish the mission

Use **14–16 seconds**; record at least 18 seconds in Studio.

- Wide Earth view.
- ICEYE-X36 moving along its near-polar orbit.
- Orbit trail visible.
- Spacecraft label visible for at least part of the shot.

Narration for this shot:

> ICEYE-X36 is a commercial synthetic-aperture radar satellite operating in a near-polar orbit. Its mission is routine: revisit a target, collect imagery and return that information to customers on the ground.

Purpose: establish the asset and its normal operating environment immediately.

### Shot 2 — Show the operator in control

Use **8–10 seconds**; record at least 12 seconds in Operator.

- ICEYE-X36 selected.
- Guidance command issued to point `SAR-X36 X-Band Imaging Payload` at the maritime target.
- Cut once the command is accepted and the slew has visibly started.

Narration for this shot:

> Through the Zendir Space Range Operator interface, the team controls the spacecraft's pointing and payload tasking.

Purpose: show that this is an operational simulation, not just an orbital animation.

### Shot 3 — Conduct the imaging task

Use **10–12 seconds** across Operator and Studio.

- Configure the imaging payload.
- Capture an image named `Nominal_Maritime_Task`.
- Briefly show storage or payload telemetry responding.
- Downlink the capture once Anchorage or Vancouver is in view (T+185 s onward).

Narration for this shot:

> Here it images an Arctic maritime area, stores the product on board, and downlinks it on the next ground-station pass.

Let the capture, storage and downlink visuals land on the words that name them. If the rendered image does not clearly show the vessels, retain the command and telemetry footage and use a separate Studio shot of the maritime area.

### Shot 4 — Re-establish normality

Use **9–11 seconds** in Studio.

- Return to the wide orbital view.
- Show one predictable spacecraft and one stable orbital plane.
- End on a clean frame suitable for revealing the Cosmos tracks in Section 2.

Narration for this shot:

> At this point, everything is nominal. One spacecraft, one stable orbital plane and one predictable operating rhythm.



## Spoken script

Read as one continuous take; the shot boundaries above fall between paragraphs.

> ICEYE-X36 is a commercial synthetic-aperture radar satellite operating in a near-polar orbit. Its mission is routine: revisit a target, collect imagery and return that information to customers on the ground.
>
> Through the Zendir Space Range Operator interface, the team controls the spacecraft's pointing and payload tasking.
>
> Here it images an Arctic maritime area, stores the product on board, and downlinks it on the next ground-station pass.
>
> At this point, everything is nominal. One spacecraft, one stable orbital plane and one predictable operating rhythm.



## On-screen text

Use only brief callouts:

- `ICEYE-X36`
- `Commercial Earth Observation`
- `Nominal Maritime Task`
- `Inclination: 97.84°`



## Transition to Section 2

End on the wide ICEYE orbit.

Begin Section 2 from a similar Studio camera angle, then reveal the five Cosmos orbital tracks. The matching camera position should make the change in the environment feel immediate.

---



# Section 2 — The Pattern Emerges

Load: `config/section_2.json`

Duration: **55–64 seconds** across 4 shots

## What happens

Five recently launched Cosmos spacecraft are shown in a nearby but noticeably different orbital plane. Three have completed inclination changes toward the ICEYE-X36 inclination; two have not moved at all.

The first change is deliberately ambiguous. The threat only becomes meaningful when related spacecraft repeat the same behaviour.

This section should not declare the activity hostile. It should establish the decision problem.

## How this section is built

`config/section_2.json` is a frozen snapshot of 16 May 2026. **Nothing manoeuvres.** The simulator has no scheduled-impulse event, so inclination cannot change on the clock, and no camera angle will disguise that.

The content of this section is a time series — eleven inclination steps across eight days — and a 3D orbit view can only show one instant of it. So Studio gets **one** establishing shot, and an **animated inclination-versus-date chart is the centrepiece**. See `filming.md` for the full chart data spec; it is a direct plot of `data/e2_range_burns_catalog_timing.csv`.

Do not shoot multiple Studio angles of this scene. They are the same frozen frame with different labels and will read as dead air.

## What to prepare



### Studio

1. Match the final camera angle from Section 1.
2. Enable labels for all six spacecraft.
3. Use **short comet-tail trails, not full orbit rings.** Full rings are fixed in space and freeze the frame; short tails give you six visibly moving objects.
4. Assign distinct trail colors in Studio if available:
  - ICEYE-X36: cyan or blue
  - Cosmos group: red or orange
5. Run live at 8× rather than paused, and speed the footage up in the edit.
6. Frame near **maximum latitude**, never near the equator — the plane separation collapses to zero at the node crossings. At T+0 ICEYE is already at 81.6°N, near its 82.2° maximum, so the opening moment is the best one.



### Operator

1. Select ICEYE-X36.

Operator is **ICEYE-only** in this section. Neutral craft expose no telemetry, so there is no Cosmos readout to show. All cross-craft inclination comparisons are chart or overlay work.

## What to record

Four distinct textures, about 48 seconds in the edit. Only shots 3 and 4 need the simulation running.

### Shot 1 — Establish the geometry

Use **14–16 seconds** in the edit; record at least 20 seconds in Studio.

- Open overhead at the pole, where all six orbits look concentric and the difference is invisible.
- Move slowly to edge-on down the line of nodes, near RAAN 271.5°, until the planes separate.
- The picture resolves into one tight bundle — ICEYE with Cosmos 2612, 2610 and 2613 all within 7 km of its plane — plus two clear strays, Cosmos 2611 and 2614, about 106 km off.
- Cosmos 2613 and 2614 are both near ICEYE's latitude at T+0, one on-plane and one off, so a single polar frame carries the contrast.
- Use the callout `16 MAY 2026`.

Narration for this shot:

> Five recently launched Cosmos spacecraft are operating near ICEYE-X36. On its own, that is not unusual. But three of them are no longer in the plane they launched into.

Note the three completed craft cannot be told apart geometrically at 7 km separation. Identifying which moved first is the chart's job, not this shot's.

### Shot 2 — The chart

Use **23–26 seconds** in the edit. The rendered source is 13.0 seconds, so retime it to approximately 55%, or extend the final hold. Use `videos/media/2-chart.mp4`, or import `videos/chart_frames/` as an image sequence at 20 fps. Regenerate with `python scripts/make_chart.py` if you want different timing.

- Inclination against date, 14 to 21 May, with ICEYE flat at 97.838° labelled `DESTINATION PLANE`.
- Cosmos lines step upward one after another as a playhead sweeps to 16 May 12:00.
- 2613 climbs alone first, then 2610 follows the same path, then 2612. Two lines stay flat at the bottom.
- Everything from 20 May onward stays right of the playhead and unrevealed. Those are Section 3's steps.
- A `COMPLETED n of 5` counter in the top right ticks 1, 2, 3 as they land.
- Add the callouts `FIRST: 2613 — AMBIGUOUS`, then `2610`, `2612`, then `THREE OF FIVE`.

The final three seconds are a static hold, so the cut out of this shot can land anywhere in that tail.

Narration for this shot — the longest single block in the video, which is why the chart is retimed to carry it:

> The orbital record shows how that happened. On the fourteenth of May, one spacecraft changes inclination. For a newly launched vehicle, that could still be explained as routine commissioning. The important indication is not the first change — it is the second spacecraft moving in the same direction, followed by a third.

Time the first inclination step to “On the fourteenth of May,” and let the second and third steps land as they are spoken.

### Shot 3 — ICEYE carries on

Use **8–10 seconds** in Operator, running at 8×.

- Select ICEYE-X36 and command a nadir imaging slew.
- Show the command going out and the attitude and reaction-wheel telemetry responding.
- This is the only live-motion shot in the section, roughly 5–15 seconds of real time.
- Use the callout `ICEYE-X36 — ROUTINE TASKING`.

Narration for this shot:

> Meanwhile, ICEYE-X36 carries on with routine tasking. Nothing in its own telemetry says anything has changed.

The beat is that ICEYE is doing routine work while the pattern assembles around it. The audience sees something the operator does not yet.

### Shot 4 — Payload view

Use **10–12 seconds** in Studio, running at 8×.

- Cut to the `SAR-X36 X-Band Imaging Payload` camera view.
- Earth through the sensor is a completely different image and breaks up the orbit-view monotony.

Narration for this shot:

> What looked like isolated activity is becoming a coordinated pattern — and all of it points toward one destination plane.

A calm sensor image under the section's most pointed line is the intended contrast. Hold two seconds after the last word before cutting.

### Do not have the Cosmos point at ICEYE

It is technically possible now, but the supplied data contains no attitude information, so it would invent the most incriminating detail in the video. It would also resolve the ambiguity this section exists to establish, and spend Section 4's material early.

## Spoken script

One paragraph per shot, in order: establishing shot, chart, Operator, payload view.

> Five recently launched Cosmos spacecraft are operating near ICEYE-X36. On its own, that is not unusual. But three of them are no longer in the plane they launched into.
>
> The orbital record shows how that happened. On the fourteenth of May, one spacecraft changes inclination. For a newly launched vehicle, that could still be explained as routine commissioning. The important indication is not the first change — it is the second spacecraft moving in the same direction, followed by a third.
>
> Meanwhile, ICEYE-X36 carries on with routine tasking. Nothing in its own telemetry says anything has changed.
>
> What looked like isolated activity is becoming a coordinated pattern — and all of it points toward one destination plane.



## On-screen text

- `Cosmos 2610–2614`
- `Initial Inclination: ~96.96°`
- `ICEYE-X36: 97.84°`
- `First Change: Ambiguous`
- `Repeated Direction: Pattern`
- `Exact Burn Timing: Illustrative`



## Transition to Section 3

Hold on the chart with three lines converged on the ICEYE reference and two still flat at the bottom.

Cut straight into Section 3's Shot 1, which is the same chart resuming from that exact frame. The two renders are frame-matched at 16 May 12:00, so the join reads as the playhead starting to move again rather than as a cut. What follows is the remainder of the fleet-level campaign — the 20–21 May steps that sat greyed out to the right of the playhead.

---



# Section 3 — Coercive Proximity

Load: `config/section_3.json`

Duration: **54–65 seconds** across 5 shots

## What happens

All five Cosmos spacecraft have completed the reconstructed inclination changes. Their final inclinations are close to the ICEYE-X36 inclination.

The section then shows an illustrative phasing continuation in which the spacecraft occupy sustained close geometry around ICEYE-X36.

The inclination changes and reconstructed Delta-V totals come from the supplied data. The close grouping does not reconstruct the reported 29 May close approach.

## What to prepare



### Studio

Shot 1 is the pre-rendered chart and needs nothing from Studio. Everything below is for Shots 2 to 5.

1. Enable orbit trails and labels for all six spacecraft.
2. Prepare:
  - a wide view of the near-matched planes;
  - a medium view showing the five Cosmos spacecraft around ICEYE-X36;
  - a close cinematic tracking view.
3. Run at 8× for orbital movement, then pause for close formation shots. Speed it up in the edit rather than in the simulator; a larger step size breaks the formation geometry.
4. Ensure the illustrative-phasing disclaimer can be added in the edit.
5. At T+60 s the five Cosmos begin an RPO approach and close from 22–85 km onto stations 2.9–8.1 km from ICEYE. Film the closure; it is the strongest visual in the piece.
6. Cosmos 2614 then repeats the approach: in to 1.0 km at T+3000 s, back out to 6.0 km at T+4800 s. That is about 10 minutes of real recording at 8×, so plan to speed it up heavily in the edit.
7. At T+3000 s, the same event beat automatically slews Cosmos 2614's `OCS-410 Narrow-Field Inspection Camera` toward ICEYE-X36. The 0.5° field of view is deliberately tight. Allow the reaction wheels to settle before opening the camera view.



### Operator

No Operator interaction is required in this section. The fleet Delta-V commitment and the evidence boundary are carried by narration and on-screen text.

## What to record



### Shot 1 — Complete the plane-change story

Use **12–14 seconds** in the edit. **Not filmed** — this is the second chart render. Use `videos/media/3-chart.mp4`, or import `videos/chart_frames_full/` as an image sequence at 20 fps. The source is 13.0 seconds, so it already fits without retiming.

- Chart-to-chart match cut straight out of Section 2's closing hold. The Section 3 render resumes at the 16 May stop, so its first frame is identical to the Section 2 render's last frame — the cut is invisible and the playhead simply starts moving again.
- The sweep runs 16 to 21 May. Cosmos 2611 steps up on 20 May, then 2614 on 21 May, and the field goes flat against the `DESTINATION PLANE` reference.
- The `COMPLETED n of 5` counter ticks to 4 and then 5. Let it reach `5 of 5` before cutting.
- Both renders share a colour per spacecraft, so the three lines already converged stay exactly where the audience left them.

This shot carries the eleven-steps and delta-V claim, which is why it is the chart rather than Studio: a 3D orbit view cannot show eleven discrete steps or a per-spacecraft cost. Studio's converged geometry arrives in Shot 3.

Narration for this shot:

> Across the group, the orbital record contains eleven selected inclination steps. The reconstructed cost is approximately 108 to 117 metres per second for each spacecraft.

Time "eleven selected inclination steps" to the last two lines completing.

Regenerate with `python scripts/make_chart.py --full`. Add `--from-start` if you ever want the full 14 May replay instead of the resume.

### Shot 2 — Show the scale of commitment

Use **7–9 seconds** using Studio with graphic overlays.

- `11 SELECTED INCLINATION STEPS`
- `~108–117 m/s PER SPACECRAFT`
- `FIVE-VEHICLE COMMITMENT`

Narration for this shot:

> That is not passive drift. It is a large and deliberate fleet-level commitment.

Do not display exact historical burn times.

### Shot 3 — Reveal the coercive geometry

Use **12–14 seconds** in Studio.

- Move from the wide plane view into the close grouping.
- Keep ICEYE-X36 visually central.
- Show multiple Cosmos spacecraft in the same shot where possible.
- Maintain visible orbital motion to avoid making the scene look static.

Narration for this shot:

> Once the destination plane is accessible, phasing can turn that access into sustained proximity: inspection, shadowing and the ability to repeatedly approach the asset.

Display throughout this shot:

`ILLUSTRATIVE PHASING — NOT A RECONSTRUCTED CLOSE APPROACH`

### Shot 4 — Confirm the evidence boundary

Use **9–11 seconds** in Studio.

- Hold on the converged planes with the full-frame caption `INCLINATION CAMPAIGN: RECONSTRUCTED · CLOSE PHASING: ILLUSTRATIVE`.
- This disclosure is mandatory and must be legible; it is the only thing separating the evidence from the dramatisation.

Narration for this shot:

> The close grouping shown here is an illustrative continuation. The evidence underneath it is the coordinated inclination campaign.



### Shot 5 — Optical inspection from COSMOS 2614

Use **14–17 seconds** in the edit after the T+3000 s event and after the attitude slew settles; record at least 20 seconds.

- Select the `OCS-410 Narrow-Field Inspection Camera` on COSMOS 2614.
- Open its camera view and frame ICEYE-X36 in the 0.5° field of view.
- Prefer the period near the 1 km inspection hold; the target will be much more readable than at the initial 2.9 km station.
- Begin with the exterior view showing COSMOS 2614 pointed at ICEYE, then cut to the optical camera feed.
- Keep this caption visible for the full camera shot:

`ILLUSTRATIVE OPTICAL INSPECTION — NO ATTITUDE OR PAYLOAD DATA`

Narration for this shot:

> At inspection range, proximity also enables narrow-field optical collection. Here, Cosmos 2614 is shown holding ICEYE-X36 in its field of view — an illustrative capability, not a reconstructed observation.

Hold the exterior angle for the first sentence, then cut to the optical feed for the qualification.

This image is not evidence that Cosmos 2614 carried this camera or imaged ICEYE-X36. It demonstrates what close-range optical access could enable.

## Spoken script

One paragraph per shot, in order.

> Across the group, the orbital record contains eleven selected inclination steps. The reconstructed cost is approximately 108 to 117 metres per second for each spacecraft.
>
> That is not passive drift. It is a large and deliberate fleet-level commitment.
>
> Once the destination plane is accessible, phasing can turn that access into sustained proximity: inspection, shadowing and the ability to repeatedly approach the asset.
>
> The close grouping shown here is an illustrative continuation. The evidence underneath it is the coordinated inclination campaign.
>
> At inspection range, proximity also enables narrow-field optical collection. Here, Cosmos 2614 is shown holding ICEYE-X36 in its field of view — an illustrative capability, not a reconstructed observation.



## On-screen text

- `11 Inclination Steps`
- `~108–117 m/s Each`
- `Coordinated Fleet Behaviour`
- `Illustrative Phasing`
- `Illustrative Optical Inspection`
- `No Kinetic Effect`

Do not show:

- A 13 km distance claim
- Jamming or dazzling
- A collision
- A kinetic attack
- Exact burn times



## Transition to Section 4

End with ICEYE-X36 surrounded by the five labelled Cosmos spacecraft.

Cut to the Operator interface with the question: what can Blue still do without sacrificing the asset's remaining mission life?

---



# Section 4 — Blue Tightens Custody

Load: `config/section_4.json`

Duration: **52–61 seconds** across 4 shots

## What happens

Section 4 opens **22 hours later** than the other scenario files, giving the Earth and ground track a visibly different starting orientation. It begins at the close-state consequence of Section 3 rather than replaying the approach: Cosmos 2614 is already about **1 km from ICEYE-X36**, and the other four Cosmos spacecraft are staged roughly **4–8 km away**.

SDA Overwatch begins roughly **5 km radially outside Cosmos 2614**, already close enough for a readable optical and radar custody shot. There is no RPO approach to wait for in this section; the live action is the Overwatch payload slew, radar/ranging collection, camera capture and downlink.

ICEYE-X36 has **no imaging payload** in this section and is automatically slewed to nadir at T+0. The Cosmos spacecraft have **no cameras**. Do not try to open an ICEYE or Cosmos camera view here.

Blue does not attempt to outrun five committed vehicles. Instead, the operator tasks an additional fictional space-domain-awareness asset to improve custody, collect range and imagery, and strengthen attribution. All Section 4 proximity is illustrative.

`SDA Overwatch` exists to demonstrate sensor tasking in the Operator interface. It is not a Spaceflux spacecraft.

## What to prepare



### Studio

1. Confirm the scenario epoch reads `2026/05/14 22:00:00`, 22 hours after Sections 1–3.
2. At T+0, confirm Cosmos 2614 is about 1 km from ICEYE-X36, the other Cosmos craft are within roughly 4–8 km, and SDA Overwatch is about 5 km from Cosmos 2614.
3. Frame ICEYE-X36, SDA Overwatch and the selected Cosmos target.
4. Prefer Cosmos 2614 as the primary tracked object.
5. Prepare a line-of-sight view from Overwatch toward Cosmos 2614.
6. Prepare a wide view showing the broader five-vehicle geometry.



### Operator

1. Select `SDA Overwatch`.
2. Open:
  - Guidance
  - Camera
  - Radar or ranging telemetry
  - Capture
  - Downlink
3. Prepare these payloads:
  - `OTC-450 Optical Tracking Camera` (monochromatic)
  - `EVS-450 Neuromorphic Event Camera` (monochromatic, event mode)
  - `SBR-900 Space Surveillance Radar`
  - `LRP-1550 Laser Ranging Payload`



## What to record



### Shot 1 — Task the additional sensor

Use **14–17 seconds** in the edit; record at least 20 seconds in Operator.

- Select `SDA Overwatch`.
- Set relative guidance toward `COSMOS 2614`.
- Use either `SBR-900 Space Surveillance Radar`, `OTC-450 Optical Tracking Camera` or `EVS-450 Neuromorphic Event Camera` as the pointing component.
- Apply guidance.
- Do not wait for a translation manoeuvre: Overwatch and its target begin approximately 5 km apart. This command slews the selected payload; it does not move Overwatch.

Narration for this shot:

> ICEYE-X36 cannot simply outrun five spacecraft that have already demonstrated this level of commitment. Every metre per second spent by the commercial asset is mission life it cannot recover.



### Shot 2 — Show the physical result

Use **11–13 seconds** in Studio.

- Show Overwatch slewing or holding line of sight toward Cosmos 2614.
- Keep ICEYE-X36 visible in the wider geometry if practical.

Narration for this shot:

> Blue's immediate advantage is custody. The operator tasks an additional surveillance asset and points its optical and ranging payloads toward Cosmos 2614.



### Shot 3 — Collect evidence

Use **12–14 seconds** in Operator. This shot has more interface actions than narration, so the extra seconds are deliberate visual time.

- Capture with `OTC-450 Optical Tracking Camera` or `EVS-450 Neuromorphic Event Camera`.
- Name the product `COSMOS_2614_Custody`.
- Show range or range-rate data from the radar or laser ranging payload.
- Downlink the observation.

Narration for this shot:

> Independent observations begin to accumulate: imagery, range and range-rate, collected and downlinked without touching ICEYE.



### Shot 4 — Return to the operational picture

Use **15–17 seconds** in Studio.

- Show the tracked target, ICEYE-X36 and the remaining Cosmos spacecraft.
- Add a visual custody marker or line if Studio supports it.

Narration for this shot:

> Increased revisit, improved ranging and additional imagery sharpen the orbital picture. This gives the team better information for protection, attribution and the next operational decision — without immediately spending ICEYE's limited fuel.

Do not cut away before the fuel-preservation point lands.

## Spoken script

One paragraph per shot, in order.

> ICEYE-X36 cannot simply outrun five spacecraft that have already demonstrated this level of commitment. Every metre per second spent by the commercial asset is mission life it cannot recover.
>
> Blue's immediate advantage is custody. The operator tasks an additional surveillance asset and points its optical and ranging payloads toward Cosmos 2614.
>
> Independent observations begin to accumulate: imagery, range and range-rate, collected and downlinked without touching ICEYE.
>
> Increased revisit, improved ranging and additional imagery sharpen the orbital picture. This gives the team better information for protection, attribution and the next operational decision — without immediately spending ICEYE's limited fuel.



## On-screen text

- `Blue Response: Tighten Custody`
- `Additional Sensor Tasked`
- `Optical + Range Observations`
- `Preserve ICEYE Mission Life`
- `SDA Overwatch: Fictional Training Asset`

Spaceflux credit, if shown:

`Spaceflux observations: Cosmos 2610, 2612, 2613 and 2614`

Do not describe SDA Overwatch as Spaceflux hardware.

## Transition to Section 5

End on an improving custody picture.

Cut back to the earlier partial-burn state. The final question is not what Blue can do at close range; it is when Blue should have acted.

---



# Section 5 — Debrief and Replay

Load: `config/section_5.json`

Duration: **38–46 seconds** across 4 shots

## What happens

The scenario returns to the earlier decision point. The debrief focuses on warning time, cumulative behaviour and the cost of waiting for certainty.

The key conclusion is that Days 2–3 were the useful decision window: multiple related spacecraft had begun moving toward one identifiable destination plane, but the full fleet had not yet committed.

## What to prepare



### Studio

1. Return to the partially converged orbital view.
2. Prepare a short before-and-after comparison:
  - the early pattern;
  - the final five-vehicle geometry.
3. Prepare a visible simulation reset or replay action.



### Operator

1. If an after-action-review screen is available in the current build, prepare:
  - event timeline;
  - operator actions;
  - relevant orbital or ranging telemetry.

Do not claim a specific AAR metric unless it is visible in the recorded build.

## What to record



### Shot 1 — Reset to the decision point

Use **8–10 seconds** in Studio or the AAR interface.

- Reset or reload the scenario on camera to establish replayability.
- Land on the partially converged planes.
- If available, show the operator action aligned against the event timeline.

Narration for this shot:

> During debrief, the scenario can be reset to the moment the pattern first became visible.



### Shot 2 — Show the warning was already there

Use **12–14 seconds** in Studio.

- Hold on the partial inclination changes.
- Briefly intercut the final Section 3 geometry as the contrast.

Narration for this shot:

> The warning existed well before the close geometry. It was written in cumulative behaviour and in the amount of propellant the fleet was prepared to spend.



### Shot 3 — Land the timing point

Use **11–13 seconds** in Studio.

- Hold on the partially converged planes while the narration reaches the decision window.
- Use the on-screen callout `DAYS 2–3: PATTERN EMERGING, RESPONSE STILL CHEAP`.

Narration for this shot:

> The useful decision point was Days 2 to 3 — when the evidence was still incomplete, but low-cost responses were still available.



### Shot 4 — Final image

Use **7–9 seconds** in Studio.

- Return to the partially converged planes.
- Leave the audience with the decision, not the final approach.

Narration for this shot:

> If this were your spacecraft, when would you call the pattern hostile?

Hold for at least two seconds after the question.

## Spoken script

One paragraph per shot, in order.

> During debrief, the scenario can be reset to the moment the pattern first became visible.
>
> The warning existed well before the close geometry. It was written in cumulative behaviour and in the amount of propellant the fleet was prepared to spend.
>
> The useful decision point was Days 2 to 3 — when the evidence was still incomplete, but low-cost responses were still available.
>
> If this were your spacecraft, when would you call the pattern hostile?



## On-screen text

- `Day 0: Ambiguous`
- `Days 2–3: Pattern Emerges`
- `Day 7: Fleet Committed`
- `Day 15: Reactive`
- `When Would You Act?`

---



# Optional opening line

Use this only if the edit needs a 3–5 second cold open before Section 1:

> A close approach may be the final alert. The intent to create it can be visible days earlier.



# Optional final Zendir line

Use this after the final question only if a product close is required:

> Zendir enables operators to replay these decisions against realistic spacecraft systems and orbital behaviour—before the same pattern appears around a real asset.



# Evidence and attribution card

Suggested end-card wording:

> Initial conditions and inclination changes derived from public catalogue history. Exercise timing and close phasing are illustrative. Spaceflux supplied optical observations for Cosmos 2610, 2612, 2613 and 2614. ICEYE-X36 and Cosmos 2611 use catalogue data only.

