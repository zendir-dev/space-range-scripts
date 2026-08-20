# Thruster-Based Docking — Instructor Script

This talk-track supports a two-team eight-thruster docking demonstration. The **Servicer** team flies the servicing vehicle; the **Client** team owns the target. If nobody logs in as Client, the Client stays the same uncooperative target.

## Pre-Session Setup

1. Load `thruster_docking.json` in Studio.
2. Verify the Servicer and Client spawn approximately 10 m apart.
3. Confirm the Servicer exposes eight cold-gas thrusters and reaction-wheel telemetry.
4. Confirm the **Servicer** team owns the servicing vehicle and the **Client** team owns the target. If nobody is on the Client team, the Client keeps its current uncooperative config (no receiver, no thrusters, RPO off) and simply holds the spawn attitude.
5. Confirm the scenario has **no events** — every action in this demo is an operator command.
6. Set simulation speed to 2x.
7. Open Operator Commands: Guidance, Rendezvous, Docking, Thruster, and Telemetry. The Servicer team selects the Servicer.

The Servicer uses reaction wheels for Dock pointing and eight 1 N cold-gas thrusters for translation. The thrusters sit in two squares of four, one at each Y-end, each nozzle canted 45° outward so X, Y, and Z force can be synthesised from the same eight units.

## Session Timeline

| Step | Action | Instructor talk |
| --- | --- | --- |
| Setup | Play. Range stays ~10 m until the Servicer team commands. | Introduce the Servicer and Client teams. If the Client team is empty, the Client sits still. |
| 1. Pointing | Guidance → **Dock** → Client → clocking 0 → Apply | Confirm the Servicer docking axis tracks the Client adapter. Wheel torque is non-zero. |
| 2. Perch | Rendezvous → Active on → Client → Docking Adapter → standoff 5 m → Apply | Watch the Servicer close along the Client port axis and hold at 5 m. |
| 3. Dock | Docking → Client → Docking Adapter → **Dock** | Closure starts only after the alignment and corridor gates are met. Then capture. |
| 4. Undock | Docking → **Undock** → confirm | Adapters release with a 10 N / 1 s push. Range increases. |
| 5. Optional | Thruster → one or multiple nozzles → Start Firing (or schedule) | Manual translation after undock, or an abort burn. APID 403 should show force. |

Keep the simulation **Running** when sending commands. Pause between steps to talk.

## Teaching Points

### Reduced thruster architecture

- Thrusters 1–4 sit at the four corners of the +Y (docking) end; 5–8 sit at the matching −Y (aft) square.
- Each nozzle is canted 45° outward toward its XZ corner, so it contributes a Y component plus X and Z.
- A pure ±Y burn fires all four nozzles on one end (~2.8 N). A pure ±X or ±Z burn fires the four nozzles that share that sign (~2.0 N).
- Matched sets are symmetric about the centre of mass, so those burns produce no residual couple.
- Reaction wheels provide all attitude control. This layout has no torque authority about Y, so pointing must stay on the wheels.

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

Log in as the **Servicer** team with the Servicer selected. Client team credentials are available if a second operator will fly the Client.

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

**Next:** Undock, or stop here.

### 4. Undock — separate

**When:** Docked. Docking panel shows **Undock** enabled.

**Do:** Docking → **Undock** → confirm.

**Done when:** Range increases. Panel shows undocked. Rendezvous perch is stopped.

**Next:** Optional manual thrust, or reload to repeat.

### 5. Optional — manual thruster firing

**When:** After undock, or to abort a hold without using Rendezvous Active off.

**Do:** Thruster → **One thruster** or **Multiple** → select nozzle(s) (not **Thruster Array**) → Duration → Thruster On → **Start Firing**. Use the clock to schedule the same command.

**Done when:** APID 403 shows force on the selected nozzle(s). Propellant mass decreases.

## Debrief

1. Translation was generated by a finite eight-thruster layout rather than an External Force Torque.
2. Reaction wheels maintained docking attitude independently of translation allocation.
3. Port-relative guidance produced a controlled standoff before final closure.
4. Alignment and corridor gates prevented closure until the adapters were ready to capture.
5. APID 403 and propellant telemetry provide direct evidence of the commanded control effort.
