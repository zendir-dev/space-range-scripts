**Scenario:** Thruster-Based Docking
**Epoch:** 2026-01-25 09:00:00 UTC
**Simulation speed:** 2x real time
**Session length:** 30 minutes simulation time
**Ground stations:** Canberra, Hobart, Cairns, Darwin, Davao, Osaka, Seoul, Ulaanbaatar

---

## Overview

The Servicer begins approximately 10 metres along-track from an uncooperative Client spacecraft. The Client cannot be commanded and simply keeps the pre-aligned attitude it spawns with; the scenario contains no automatic events. The operator flies the Servicer from Commands: Dock pointing, a 5 m port-relative perch, then Dock to close and capture. An eight-thruster cold-gas system provides translation.

This is a clean, general docking demonstration. It contains no injected propulsion failures or participant questions.

## Mission Goals

1. Confirm the initial range is approximately 10 m with the Laser Range Finder.
2. Command Dock pointing so the Servicer adapters face the Client.
3. Command a 5 m port-relative perch on the Client docking adapter and hold.
4. Command Dock to close after the axis, roll, and corridor gates are satisfied.
5. Confirm capture at a separation of 0.05 m and an alignment error below 5°.
6. **Undock** when you want to separate: Docking → **Undock**. Confirm. The adapters release with a 10 N / 1 s push along the docking axis.
7. Optional: fire individual cold-gas nozzles from **Thruster** (select a named thruster, set duration, Start Firing). Use this after undock, or to abort a hold.
8. Monitor APID 403 and propellant telemetry to verify that translation is produced by the cold-gas thrusters.

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
| Docking | Docking Adapter |
| RPO software | Enabled |

The layout is two squares of four thrusters, one at each Y-end of the Servicer. Each nozzle is canted 45° outward toward its corner, so a single firing produces a Y component plus X and Z. Opposite ends reverse the Y component. Firing a matched set of four produces pure ±X, ±Y, or ±Z with no residual couple. Reaction wheels handle attitude.

### Client

| Item | Configuration |
| --- | --- |
| Mass | 20 kg |
| Attitude | Pre-aligned inertial hold with reaction wheels (automatic at T+1) |
| Docking | Docking Adapter |
| Commandable | No receiver; cannot be commanded |

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

Select the **Servicer**. The simulation must be running to uplink.

1. **Pointing — align the adapters.** Guidance → Pointing Mode **Dock** → spacecraft **Client** → clocking **0** → Apply. Done when the Servicer docking axis tracks the Client adapter and range is still ~10 m.
2. **Perch — hold off the docking adapter.** Rendezvous → Active **on** → Target **Client** → Aim Component **Docking Adapter** → Standoff **5** m → Apply. Done when LRF settles near 5 m and closing rate is ~0. Hold as long as you want.
3. **Dock — approach and capture.** Docking → Target **Client** → Component **Docking Adapter** → **Dock**. Done when range decreases toward 0 (after gates) and the adapters latch at ≤ 0.05 m / ≤ 5° / ≤ 5°.

4. **Undock — separate.** Docking → **Undock** → confirm. Done when the Docking panel shows undocked and range starts increasing.

5. **Optional manual thrust.** Thruster → pick a named nozzle → duration → Thruster On → **Start Firing**. Do not select a Thruster Array. Done when APID 403 shows force on that nozzle.

To abort translation: Rendezvous Active **off**, Apply, and confirm closing speed falls. You can also fire a selected nozzle from **Thruster**.

## Before You Begin

1. Log in with the team credentials.
2. Confirm both spacecraft are visible on the Map.
3. Verify Servicer telemetry and an initial range near 10 m.
4. Confirm eight thrusters are available.
5. Open the Guidance, Rendezvous, Docking, Thruster, and Telemetry panels.
