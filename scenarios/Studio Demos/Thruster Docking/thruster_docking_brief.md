**Scenario:** Thruster-Based Docking
**Epoch:** 2026-01-25 09:00:00 UTC
**Simulation speed:** 2x real time
**Session length:** 30 minutes simulation time
**Ground stations:** Canberra, Hobart, Cairns, Darwin, Davao, Osaka, Seoul, Ulaanbaatar

---

## Overview

The Servicer begins approximately 10 metres along-track from the Client. The **Gold** team owns both spacecraft. Fly the Servicer: Dock pointing, a 5 m port-relative perch, then Dock to close and capture. An eight-thruster cold-gas system provides translation.

This scenario is inspired by the thruster failures on Astroscale's ELSA-d (End-of-Life Services by Astroscale-demonstration) mission, which showed how unexpected firings and lost nozzles complicate proximity operations.

## Scheduled anomalies

Studio injects two timed events on the Servicer. Watch **APID 403** (Thruster) and propellant mass — with a 2 s ping interval you should see each event within a couple of seconds of sim time.

| Sim time | Event | What you should see | How to accommodate |
| --- | --- | --- | --- |
| **T+300 s** (5 min) | **+Y** thrusters **1** and **4** fire without a command (`Duration` 1800 s) | APID 403 shows thrust on the diagonal +Y pair only. Asymmetric burn (~1.4 N) with X/Z couple — not a matched quad. Propellant mass falls steadily. The burn runs until sim end (session ends at T+1800 s, so ~25 min of remaining sim time). | Cancel Rendezvous if active (Active **off**, Apply). Re-command Dock pointing if attitude drifts. Do not press **Dock** until range and rate are stable again. |
| **T+350 s** | Thrusters **1**, **4**, and **6** fail off permanently (`Dispersed Factor` = 1) | Both firing nozzles (1 and 4) stop delivering force even though APID 403 may still show a fire request. Thruster 6 never produces thrust when commanded. Only thrusters **2**, **3**, **5**, **7**, and **8** remain effective. | RPO software drops failed nozzles from the Thruster Array on the next step — no operator action required for allocation. Pure +Y translation uses 2 and 3 only. Pure −Y loses one corner (6 gone; 5, 7, 8 remain). Re-perch or re-point before resuming closure. |

Failed thrusters still accept fire commands but deliver zero force. A `reset` does **not** restore them.

## Mission Goals

1. Confirm the initial range is approximately 10 m with the Laser Range Finder.
2. Command Dock pointing so the Servicer adapters face the Client.
3. Command a 5 m port-relative perch on the Client docking adapter and hold.
4. Command Dock to close after the axis, roll, and corridor gates are satisfied.
5. Confirm capture at a separation of 0.05 m and an alignment error below 5°.
6. **Undock** when you want to separate: Docking → **Undock**. Confirm. The adapters release with a 10 N / 1 s push along the docking axis.
7. Optional: fire one or several cold-gas nozzles from **Thruster** (check nozzles or **Select all**, set duration, Start Firing, or schedule with the clock). Use this after undock, or to abort a hold.
8. Monitor APID 403 and propellant telemetry. Use the **Scheduled anomalies** table above to confirm each event fired and to recover before continuing the approach.

---

## Spacecraft

### Servicer

| Item | Configuration |
| --- | --- |
| Orbit | Sun-synchronous LEO, approximately 550 km altitude |
| Mass | 180 kg |
| Translation | 8 x 1 N cold-gas thrusters |
| Propellant | Single tank, 25 kg initial load |
| Attitude | Dock pointing with reaction wheels (operator-commanded) |
| Sensors | Camera, Laser Range Finder, GPS |
| Docking | Docking Adapter on the **+Y** end at `(0, 0.35, 0)`, rotation `(−90, 0, 0)` |
| RPO software | Enabled |

The layout is two squares of four thrusters, one at each Y-end of the Servicer. Each nozzle is canted 45° outward toward its corner, so a single firing produces a Y component plus X and Z. Opposite ends reverse the Y component. Firing a matched set of four produces pure ±X, ±Y, or ±Z with no residual couple. Reaction wheels handle attitude.

### Client

| Item | Configuration |
| --- | --- |
| Mass | 20 kg |
| Mesh | Landsat-8 bus (`BP_Z_SC_Landsat8_Chassis`, scale 0.2) |
| Attitude | Same Euler attitude as the Servicer at spawn; reaction wheels present; rate zero. No scripted guidance event |
| Docking | Docking Adapter on the **−Y** end at `(0, −0.42, 0)`, rotation `(90, 0, 0)` so the port faces outward along −Y (toward the Servicer after spawn attitude) |
| Commandable | On the Gold team with the Servicer. Holds spawn attitude as the docking target |

---

## Thruster Layout

Thrusters are named for the Y-end and XZ corner they sit on. Each is canted 45° outward from that end, so it contributes to Y translation and to the X/Z axes of its corner.

| Thruster | End | Corner | Mount position |
| --- | --- | --- | --- |
| 1 | +Y | +X +Z | (0.16, 0.36, 0.16) |
| 2 | +Y | +X −Z | (0.16, 0.36, −0.16) |
| 3 | +Y | −X +Z | (−0.16, 0.36, 0.16) |
| 4 | +Y | −X −Z | (−0.16, 0.36, −0.16) |
| 5 | −Y | +X +Z | (0.16, −0.36, 0.16) |
| 6 | −Y | +X −Z | (0.16, −0.36, −0.16) |
| 7 | −Y | −X +Z | (−0.16, −0.36, 0.16) |
| 8 | −Y | −X −Z | (−0.16, −0.36, −0.16) |

Each thruster has a maximum thrust of 1 N and a 0.25 s spool-up time. The docking-adapter, camera, and laser-range-finder centre line stays clear. A pure docking-axis burn uses all four nozzles on one Y-end (~2.8 N). A pure ±X or ±Z burn uses the four nozzles that share that sign (~2.0 N).

The squares are symmetric about the centre of mass, so equal firing of a matched set produces translation without a residual couple. Reaction wheels still provide attitude. This layout cannot produce torque about Y; that is intentional and is why pointing stays on the wheels.

All mount positions are relative to the centre of mass. The Servicer's mesh offset is zero so authored component positions are also the physical moment arms.

---

## Operator sequence

Log in as the **Gold** team and select the Servicer. The simulation must be running to uplink.

1. **Pointing — align the adapters.** Guidance → Pointing Mode **Dock** → spacecraft **Client** → clocking **0** → Apply. Done when the Servicer docking axis tracks the Client adapter and range is still ~10 m.
2. **Perch — hold off the docking adapter.** Rendezvous → Active **on** → Target **Client** → Aim Component **Docking Adapter** → Standoff **5** m → Apply. Done when LRF settles near 5 m and closing rate is ~0. Hold as long as you want.
3. **Dock — approach and capture.** Docking → Target **Client** → Component **Docking Adapter** → **Dock**. Done when range decreases toward 0 (after gates) and the adapters latch at ≤ 0.05 m / ≤ 5° / ≤ 5°.

4. **Undock — separate.** Docking → **Undock** → confirm. Done when the Docking panel shows undocked and range starts increasing.

5. **Optional manual thrust.** Thruster → check nozzle(s) or **Select all** → duration → Thruster On → **Start Firing** (or schedule). Thruster Array components are omitted from the list. Done when APID 403 shows force on the selected nozzle(s).

To abort translation: Rendezvous Active **off**, Apply, and confirm closing speed falls. You can also fire a selected nozzle from **Thruster**.

## Before You Begin

1. Log in as the **Gold** team and select the Servicer.
2. Confirm both spacecraft are visible on the Map.
3. Verify Servicer telemetry and an initial range near 10 m.
4. Confirm eight thrusters are available.
5. Open the Guidance, Rendezvous, Docking, Thruster, and Telemetry panels.
