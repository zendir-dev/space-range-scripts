**Scenario:** Thruster-Based Docking
**Epoch:** 2026-01-25 09:00:00 UTC
**Simulation speed:** 2x real time
**Session length:** 30 minutes simulation time
**Ground stations:** Madrid, Singapore, Canberra

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
6. Monitor APID 403 and propellant telemetry to verify that translation is produced by the cold-gas thrusters.

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

The layout provides thrust in all six body directions. The docking axis uses symmetric lateral pairs and the remaining axes use single on-axis nozzles, so a translation command produces no net attitude torque. Reaction wheels handle attitude, so the reduced thruster set is used purely for translation.

### Client

| Item | Configuration |
| --- | --- |
| Mass | 20 kg |
| Attitude | Pre-aligned inertial hold with reaction wheels (automatic at T+1) |
| Docking | Docking Adapter |
| Commandable | No receiver; cannot be commanded |

---

## Thruster Layout

Thrusters are named for the direction of thrust they produce, not the face they sit on.

| Thrust direction | Thrusters | Mount position |
| --- | --- | --- |
| -X | 1 | (0.20, 0, 0) |
| +X | 2 | (-0.20, 0, 0) |
| -Y | 3, 4 | (±0.16, 0.36, 0), either side of the docking adapter |
| +Y | 5, 6 | (±0.16, -0.36, 0), aft face |
| -Z | 7 | (0, 0, 0.18) |
| +Z | 8 | (0, 0, -0.18) |

Each thruster has a maximum thrust of 1 N and a 0.25 s spool-up time. The docking axis (±Y) carries a lateral pair at each end, giving 2 N for approach and braking against 1 N for lateral corrections, and keeping the docking adapter, camera, and laser range finder mounting line clear.

Two geometry rules keep the force allocation solvable, and breaking either one makes the mapping matrix singular so the solver commands zero thrust on every thruster:

1. Directions served by a **single** thruster (±X and ±Z here) must sit exactly on their own thrust axis, so the thrust line passes through the centre of mass. Offsetting one of these makes its torque row a multiple of its force row.
2. Directions served by a **pair** may be offset laterally, but the pair must be symmetric about the axis so that firing both together produces no net couple.

All mount positions are relative to the centre of mass. The Servicer's mesh offset is zero so authored component positions are also the physical moment arms; a non-zero mesh offset shifts every component off the centre of mass and breaks the allocation.

---

## Operator sequence

Select the **Servicer**. The simulation must be running to uplink.

1. **Pointing — align the adapters.** Guidance → Pointing Mode **Dock** → spacecraft **Client** → clocking **0** → Apply. Done when the Servicer docking axis tracks the Client adapter and range is still ~10 m.
2. **Perch — hold off the docking adapter.** Rendezvous → Active **on** → Target **Client** → Aim Component **Docking Adapter** → Standoff **5** m → Apply. Done when LRF settles near 5 m and closing rate is ~0. Hold as long as you want.
3. **Dock — approach and capture.** Docking → Target **Client** → Component **Docking Adapter** → **Dock**. Done when range decreases toward 0 (after gates) and the adapters latch at ≤ 0.05 m / ≤ 5° / ≤ 5°.

To abort translation: Rendezvous Active **off**, Apply, and confirm closing speed falls.

## Before You Begin

1. Log in with the team credentials.
2. Confirm both spacecraft are visible on the Map.
3. Verify Servicer telemetry and an initial range near 10 m.
4. Confirm eight thrusters are available.
5. Open the Guidance, Rendezvous, Docking, and Telemetry panels.
