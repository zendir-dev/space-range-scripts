# Thruster-Based Docking — Instructor Script

This talk-track supports a general eight-thruster docking demonstration flown from Operator Commands.

## Pre-Session Setup

1. Load `thruster_docking.json` in Studio.
2. Verify the Servicer and Client spawn approximately 10 m apart.
3. Confirm the Servicer exposes eight cold-gas thrusters and reaction-wheel telemetry.
4. Confirm the scenario has **no events at all** — every action in this demo is an operator command. The Client spawns pre-aligned with zero body rates and its guidance controller idle, so it keeps that attitude; it has no receiver, so the team cannot command it either.
5. Set simulation speed to 2x.
6. Open Operator Commands: Guidance, Rendezvous, Docking, and Telemetry. Select the Servicer.

The Servicer uses reaction wheels for Dock pointing and eight 1 N cold-gas thrusters for translation. Separating attitude and translation control keeps the reduced thruster layout suitable for a stable reference docking run.

## Session Timeline

| Step | Action | Instructor talk |
| --- | --- | --- |
| Setup | Play. Nothing happens on its own. | Introduce the two spacecraft and the docking objective. Range should stay ~10 m and the Client should sit still. |
| 1. Pointing | Guidance → **Dock** → Client → clocking 0 → Apply | Confirm the Servicer docking axis tracks the Client adapter. Wheel torque is non-zero. |
| 2. Perch | Rendezvous → Active on → Client → Docking Adapter → standoff 5 m → Apply | Watch the Servicer close along the Client port axis and hold at 5 m. |
| 3. Dock | Docking → Client → Docking Adapter → **Dock** | Closure starts only after the alignment and corridor gates are met. Then capture. |

Keep the simulation **Running** when sending commands. Pause between steps to talk.

## Teaching Points

### Reduced thruster architecture

- Thrusters are named for the thrust direction they produce: 1 gives -X, 2 gives +X, 3 and 4 give -Y, 5 and 6 give +Y, 7 gives -Z, 8 gives +Z.
- The docking axis carries a symmetric lateral pair at each end, so approach and braking have 2 N against 1 N for lateral corrections, and nothing is mounted on the docking adapter centre line.
- The pairs are symmetric about the docking axis and the single nozzles sit on their own thrust axes, so a translation command produces no net torque.
- Reaction wheels provide all attitude control; the thrusters provide only translation.
- Eight unidirectional thrusters cannot provide balanced authority in all six force directions and all three torque axes at once. Twelve would be the minimum for that, which is why attitude is delegated to the wheels here.

### Port-relative approach

After Dock pointing is stable, the operator commands a 5 m standoff along the Client docking-port axis. The Servicer should close at no more than 5 cm/s and settle inside the corridor. Nothing closes further until **Dock** is pressed.

Monitor:

- Laser Range Finder range
- Requested and achieved body force
- APID 403 thruster activity
- Propellant mass
- Docking-axis and roll alignment

### Alignment-gated closure

**Dock** arms the adapters and enables final closure at up to 1 cm/s. Closure waits until the axis and roll errors are within 8° and the Servicer is inside the 0.5 m corridor.

Capture requires:

- Separation at or below 0.05 m
- Docking-axis error at or below 5°
- Roll error at or below 5°

### Operational safety

If the approach becomes unstable:

1. Disable the active Rendezvous command (Active off, Apply).
2. Verify that closing speed decreases.
3. Command a safe separation only after confirming available thrust direction and clearance.
4. Stop and reload the scenario before repeating the demonstration.

## Operator procedure

Team Blue, **Servicer** selected.

### 1. Pointing — align the adapters

**When:** After T+1 (Client is holding). Range still ~10 m. Do this before perching.

**Do:** Guidance → Pointing Mode **Dock** → spacecraft **Client** → clocking **0** → **Apply Guidance**.

**Done when:** Servicer docking axis tracks the Client adapter. Reaction-wheel torque is non-zero. Range is still ~10 m.

**If it did not bind** (right at spawn): Apply once more after ~1 s.

**Next:** Perch. Do not Dock yet.

### 2. Perch — hold off the docking adapter

**When:** Dock pointing is stable.

**Do:** Rendezvous → Active **on** → Target **Client** → Aim Component **Docking Adapter** → Standoff **5** m → **Apply Rendezvous**.

**Done when:** LRF settles near **5 m** and closing rate ~0. Thrusters (APID 403) fired on the way in, then quiet in the hold. Wheel torque still non-zero. Hold as long as you want; nothing closes until Dock.

**Abort:** Active **off**, Apply. Confirm closing speed drops.

**Next:** Dock when axis/roll look aligned (within ~8°) and you are inside the ~0.5 m corridor.

### 3. Dock — approach and capture

**When:** Stable 5 m perch, adapters aligned enough to pass the gates.

**Do:** Docking → Target **Client** → Component **Docking Adapter** → **Dock**.

This arms capture and starts the slow close from the perch.

**Done when (approach):** After a short hold, range decreases toward 0 at about 1 cm/s. If range does not drop, the alignment/corridor gate is holding — improve Dock pointing, stay perched, press Dock again.

**Done when (capture):** Adapters latch at ≤ **0.05 m**, axis ≤ **5°**, roll ≤ **5°**. Docking panel shows docked to Client.

## Debrief

1. Translation was generated by a finite eight-thruster layout rather than an External Force Torque.
2. Reaction wheels maintained docking attitude independently of translation allocation.
3. Port-relative guidance produced a controlled standoff before final closure.
4. Alignment and corridor gates prevented closure until the adapters were ready to capture.
5. APID 403 and propellant telemetry provide direct evidence of the commanded control effort.
