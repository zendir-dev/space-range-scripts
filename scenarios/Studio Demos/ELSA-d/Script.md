# ELSA-d Thruster Failures - Instructor Script

This document provides a talk-track for instructors running the ELSA-d Thruster Failures demonstration.

---

## Pre-Session Setup

1. Load `elsa_d_thruster_failures.json` in Studio.
2. Verify both spacecraft spawn correctly (Servicer and Client visible, approximately 30 m apart, docking adapters facing each other).
3. Confirm the Servicer shows 24 thrusters in telemetry.
4. Check that events are loaded (Admin > Events should show Align Docking Adapters at T+1 s and Automatic Docking Approach at T+60 s). Thruster-fault events should be disabled.
5. Set simulation speed to 5x unless the audience prefers real-time.

Translation uses the Servicer's 24 × 0.25 N cold-gas thrusters (four per face, not an unbounded External Force Torque). A full face is 1 N on a 180 kg vehicle. Relative pointing holds the docking port on the Client so translation does not tumble an idle ADCS. This reference run has the anomaly events disabled so the pair can complete a clean dock from 30 m.

---

## Session Timeline

| Sim Time | Wall Time (5x) | Event | Instructor Action |
| --- | --- | --- | --- |
| 0:00 | 0:00 | Session start | Introduce scenario, distribute credentials |
| 0:01 (1s) | 0:00 | **Align docking adapters** | Confirm relative pointing is active and range is ~30 m |
| 1:00 (60s) | 0:12 | **Automatic docking approach** | Confirm the Servicer starts closing onto the Client docking adapter |
| 1:00–5:00 | 0:12–1:00 | Capture | Watch LRF range drop; docking should complete once adapters are inside capture distance |
| ~20:00 | ~4 min | Wrap-up | Debrief. Re-enable fault events for a later degraded-propulsion run |

---

## Key Teaching Points

### 1. Anomaly Detection

When the unplanned thruster fire occurs at T+180s:

- Thruster 1 (+X) fires for 15 seconds without operator command
- Participants should see:
  - APID 403 telemetry showing non-zero ThrustForce_B on Thruster 1
  - Range to Client increasing (unplanned delta-V pushing Servicer away)
  - Possible attitude disturbance

**If participants miss it:** "Check your thruster telemetry. Is anything firing that you didn't command?"

### 2. Abort Procedure

The correct response is:

1. Stop the firing thruster (Thruster panel > Stop Firing)
2. Cancel rendezvous (Rendezvous panel > Active off)
3. Verify separation is increasing via LRF

**Common mistake:** Trying to compensate with another thruster instead of aborting. Emphasise that during RPO, uncertain propulsion behaviour demands separation first.

### 3. Diagnosing Failures

After T+210s, three thrusters are non-functional:
- Thruster 1 (+X)
- Thruster 2 (+X)
- Thruster 3 (+X)

After T+300s, a fourth fails:
- Thruster 4 (+X)

**Teaching point:** The four-thruster loss is geometrically clustered (the entire +X face). This creates asymmetric control authority: +X translation is gone while the other five faces remain intact.

To diagnose: Have participants fire each thruster briefly (1-2 seconds) and observe APID 403 ThrustForce_B. Failed thrusters will show ~0 N.

### 4. Redundancy vs Controllability

This is the core lesson from ELSA-d:

> "Propulsion redundancy must be evaluated at the level of controllability and manoeuvre authority, not simply by component count."

Twenty-four thrusters sounds redundant. But:
- Losing 4 of 24 is only ~17% by count
- The loss of the entire +X face means no thrust in one direction
- Coupled translation/rotation effects emerge once a face is no longer a balanced rectangle

**Discussion prompt:** "If you could choose which 4 thrusters to lose, which would you pick to preserve the most control authority?" (Answer: lose one from each of four different faces, not a whole face)

### 5. Recovery Operations

With 20 remaining thrusters (faces -X, +Y, -Y, +Z, -Z intact), participants can still translate in five directions. They cannot directly thrust in +X. Approach must be planned accordingly.

The rendezvous command may still work but will be slower on the +X axis and may produce more attitude coupling once that face is gone.

**Target:** Get within ~150 m of the Client. Exact distance is less important than demonstrating successful degraded-mode operations.

---

## Common Questions

**Q: What actually caused the ELSA-d failures?**  
A: Public sources do not establish a definitive root cause. Three thrusters were affected by a "system issue" and a fourth failed for an unresolved reason. The scenario models loss of thrust authority without claiming a specific mechanism.

**Q: Why didn't we model the valve/feed system?**  
A: The scenario focuses on the operational response to loss of control authority, not propulsion system internals. Adding valve failures would increase complexity without changing the core lesson.

**Q: Can participants reset the thrusters?**  
A: In this scenario, the `reset` command does not restore failed thrusters. The DispersedFactor is set by the scenario event and is not cleared on reset. This matches ELSA-d, where the thruster losses were permanent.

**Q: What if someone fires the wrong thruster during the anomaly?**  
A: This can make the situation worse. Use it as a teaching moment about the importance of the abort-first philosophy.

---

## Debrief Talking Points

1. **The abort decision was correct.** Continuing capture operations with uncertain propulsion risked collision.

2. **Detection matters.** The faster the anomaly is detected, the less unplanned delta-V accumulates.

3. **Diagnosis is systematic.** Test each thruster, record which work and which don't.

4. **Controllability is not count.** Twenty thrusters can still provide 5-axis translation after one face is lost. Four thrusters on one face provide no authority on the opposite axis.

5. **Real ELSA-d recovered.** Despite losing half its thrusters, ELSA-d demonstrated navigation from ~1,600 km to 159 m using degraded propulsion plus environmental forces (drag). The mission was not a failure, it was a demonstration of resilience.

---

## Answer Key

| Question | Answer | Score |
| --- | --- | --- |
| What should you do FIRST when you detect an unexpected thruster firing during RPO? | Option 2 of 4: "Abort: stop the thruster fire and cancel the rendezvous" | 15 |
| How many servicer thrusters remain usable after the full anomaly sequence? | 20 (exact) | 10 |
| Approximate the closest approach distance (in metres) you achieved during the recovery phase | 150 m, tolerance 100 (50-250 accepted) | 15 |
| Why did the loss of four thrusters have a disproportionate impact? | Option 2 of 4: "The lost thrusters were on one side, creating asymmetric thrust capability and coupling between translation and attitude" | 10 |

**Total possible:** 50 points
