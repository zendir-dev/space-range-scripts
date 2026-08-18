**Scenario:** Thruster-Based Docking
**Epoch:** 2026-01-25 09:00:00 UTC
**Simulation speed:** 2x real time
**Session length:** 30 minutes simulation time
**Ground stations:** Madrid, Singapore, Canberra

---

## Overview

The Servicer begins approximately 10 metres along-track from an uncooperative Client spacecraft. The Client holds its pre-aligned inertial attitude while the Servicer maintains Dock pointing with reaction wheels. An eight-thruster cold-gas system provides translation throughout a port-relative approach, 5 m standoff, alignment-gated closure, and capture.

This is a clean, general docking demonstration. It contains no injected propulsion failures or participant questions.

## Mission Goals

1. Confirm the initial range is approximately 10 m with the Laser Range Finder.
2. At T+10 s, observe the Servicer approach the Client's docking-port axis and hold at 5 m.
3. At T+180 s, observe the slower final closure after the axis, roll, and corridor gates are satisfied.
4. Confirm capture at a separation of 0.05 m and an alignment error below 5°.
5. Monitor APID 403 and propellant telemetry to verify that translation is produced by the cold-gas thrusters.

---

## Spacecraft

### Servicer

| Item | Configuration |
| --- | --- |
| Orbit | Sun-synchronous LEO, approximately 550 km altitude |
| Mass | 180 kg |
| Translation | 8 x 1 N cold-gas thrusters |
| Propellant | Single tank, 25 kg initial load |
| Attitude | Dock pointing with reaction wheels |
| Sensors | Camera, Laser Range Finder, GPS |
| Docking | Docking Adapter |
| RPO software | Enabled |

The layout provides thrust in all six body directions. The docking axis uses symmetric lateral pairs and the remaining axes use single on-axis nozzles, so a translation command produces no net attitude torque. Reaction wheels handle attitude, so the reduced thruster set is used purely for translation.

### Client

| Item | Configuration |
| --- | --- |
| Mass | 20 kg |
| Attitude | Pre-aligned inertial hold with reaction wheels |
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

## Timeline

1. **T+1 s — Stable attitude split:** The Client starts inertial hold and the Servicer starts Dock pointing.
2. **T+2 s — Dock target refresh:** The active Dock chain binds to the Client adapter.
3. **T+10 s — Port-relative standoff:** The Servicer closes along the Client port axis toward a 5 m standoff at up to 5 cm/s.
4. **T+10.1 s — Attitude actuator restored:** Dock pointing is re-asserted on reaction wheels, because a rendezvous command switches the attitude mapping to thrusters.
5. **T+180 s — Alignment-gated closure:** The Servicer closes at up to 1 cm/s once the docking gates are satisfied.
6. **T+180.1 s — Attitude actuator restored:** Reaction-wheel attitude control is re-asserted after the closure command.
7. **Capture:** The adapters capture at 0.05 m when axis, roll, and corridor conditions are met.

## Before You Begin

1. Log in with the team credentials.
2. Confirm both spacecraft are visible on the Map.
3. Verify Servicer telemetry and an initial range near 10 m.
4. Confirm eight thrusters are available.
5. Open the Guidance, Rendezvous, Docking, and Telemetry panels.
