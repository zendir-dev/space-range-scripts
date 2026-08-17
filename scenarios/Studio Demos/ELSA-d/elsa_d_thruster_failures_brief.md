**Scenario:** ELSA-d Thruster Failures  
**Epoch:** 2026-01-25 09:00:00 UTC  
**Simulation speed:** 2x real time  
**Session length:** 30 minutes (simulation time; 15 minutes wall time)  
**Ground stations:** Madrid, Singapore, Canberra

---

## Overview

This demonstration is inspired by the **ELSA-d** (End-of-Life Services by Astroscale demonstration) mission anomaly of January 2022. During autonomous proximity operations approximately 30 metres from a client spacecraft, the servicer experienced a propulsion anomaly that produced an unplanned velocity change. The mission team aborted the capture attempt and established safe separation. Investigation revealed that three thrusters had become non-functional due to a system issue, and a fourth thruster subsequently failed independently.

You will operate a **Servicer** spacecraft starting approximately **10 metres** along-track from a **Client**. The Client holds its pre-aligned inertial attitude with reaction wheels while Dock pointing commands only the Servicer, avoiding a mutual pointing loop. After ten simulation seconds the Servicer flies a port-relative approach to a 5 m standoff along the Client port axis, then a slower alignment-gated closure captures the Client. Thruster-fault events are present in the scenario but **disabled**, so this run is a clean docking reference. Re-enable those events when you want the anomaly sequence.

> **Note:** Public sources do not establish a definitive physical root cause for the ELSA-d thruster failures. When the fault events are enabled, this scenario models the loss of thrust authority without claiming a specific mechanism.

## Mission Goals

1. **Confirm the 10 m start** - Servicer and Client should be about 10 m apart. Monitor range with the Laser Range Finder. The Client port starts facing the Servicer, whose Dock pointing should maintain anti-parallel adapter Up vectors.
2. **Watch the port-relative standoff** - At T+10 s the Servicer begins closing along the Client port axis to a 5 m standoff at 5 cm/s.
3. **Watch alignment-gated closure** - At T+180 s the Servicer closes at 1 cm/s only after axis, clocking, and corridor gates are met. Confirm capture.
4. **Optional: re-enable the anomaly** - The unplanned ΔV and thruster-failure events are disabled. Turn them on when you want the degraded-propulsion exercise.
5. **Complete the tasks** - Answer the scored questions in the Tasks section.

---

## Your Spacecraft

### Servicer

The Servicer is your primary asset. It carries twenty-four cold-gas thrusters (four per face) for translation, plus sensors for relative navigation.

| Item | Configuration |
| --- | --- |
| Orbit | Sun-synchronous LEO, ~550 km altitude |
| Mass | 180 kg |
| Thrusters | 24 x 0.25 N cold-gas (4 per face, Thrusters 1-24) |
| Propellant | Single tank, 25 kg initial load |
| Power | Two solar panels, 60 Wh battery |
| Attitude | Inertial hold + reaction wheels (Client) / Dock pointing + thrusters (Servicer) |
| Sensors | Camera, Laser Range Finder, GPS |
| Docking | Docking Adapter |
| Comms | Receiver, Transmitter |

The Servicer has **RPO software enabled**, so you can use the Rendezvous command to hold an offset position relative to the Client. Rendezvous force is allocated onto the twenty-four cold-gas thrusters; watch propellant mass and APID 403 fire commands, not an External Force Torque. Each face fires as a balanced rectangle so translation does not dump torque into attitude.

### Client

The Client is an uncooperative target spacecraft. It has no receiver and cannot be commanded.

| Item | Configuration |
| --- | --- |
| Mass | 20 kg |
| Attitude | Inertial hold keeps the initially aligned Client port fixed using reaction wheels |
| Docking | Docking Adapter |
| Commandable | No (no receiver) |

---

## Thruster Layout

The Servicer's twenty-four thrusters sit in a 2-by-2 rectangle on each of the six body faces (four nozzles per face). Each unit is 0.25 N with a 0.25 s spool-up, so a full face provides 1 N of translation with the couples cancelling.

| Face | Thrusters | Layout |
| --- | --- | --- |
| +X | 1-4 | Rectangle on the +X face |
| -X | 5-8 | Rectangle on the -X face |
| +Y | 9-12 | Rectangle on the +Y face |
| -Y | 13-16 | Rectangle on the -Y face |
| +Z | 17-20 | Rectangle on the +Z face |
| -Z | 21-24 | Rectangle on the -Z face |

> **Key lesson:** Losing thrusters that are geometrically clustered (the entire +X face) affects specific control axes disproportionately. Thruster count alone is not a measure of control authority.

---

## Using the Operator Terminal

| View | What it is for |
| --- | --- |
| **Map** | See your orbit, the Client position, and ground station coverage. |
| **Control** | Command pointing with **Guidance**, fire thrusters with **Thruster**, and set rendezvous holds with **Rendezvous**. |
| **Telemetry** | Read Laser Range Finder distance, thruster telemetry (APID 403), and fuel levels. |
| **Tasks** | Read and submit answers to the scored questions. |

### Abort procedure

When an anomaly is detected during proximity operations:

1. **Stop the thruster** - In Control > Thruster, select the firing thruster and click Stop Firing.
2. **Cancel the rendezvous hold** - In Control > Rendezvous, toggle Active off.
3. **Verify separation** - Watch the LRF range in Telemetry to confirm distance is increasing.
4. **Diagnose** - Test each thruster individually. A failed thruster will accept the command but produce zero or near-zero thrust in telemetry.

---

## What to Expect

The session proceeds in three phases while the fault events are disabled:

1. **Phase 1: Attitude acquisition** - From T+1 s the Client holds inertially and only the Servicer commands Dock pointing. Range should stay near 10 m.
2. **Phase 2: Port-relative standoff** - At T+10 s the Servicer closes along the Client port axis to a 5 m standoff.
3. **Phase 3: Alignment-gated closure** - At T+180 s the Servicer closes to capture once axis, clocking, and corridor gates are satisfied.

Re-enable the anomaly events when you want the unplanned ΔV and thruster-loss sequence after a successful reference dock.

---

## Operational Constraints

| Constraint | Value |
| --- | --- |
| RPO Software | Available on Servicer |
| Thruster commands | Available (fault events are disabled on this reference run) |
| Docking | Available after a safe, stable close approach; both spacecraft carry adapters |
| Client commands | Not possible (no receiver on Client) |

---

## Learning Focuses

- Detecting anomalous spacecraft behaviour during proximity operations
- Executing abort procedures to establish safe separation
- Diagnosing partial propulsion system failures
- Operating with degraded control authority
- Understanding that redundancy must be evaluated at the level of controllability, not component count

---

## Before You Begin

1. Log in to the operator terminal with your team credentials.
2. Confirm you can see both Servicer and Client on the Map.
3. Verify the Servicer has telemetry (check Ping in Telemetry view).
4. Confirm the starting range is approximately 10 m using the Laser Range Finder.
5. Familiarise yourself with the Thruster, Rendezvous, and Docking panels in Control. Client inertial hold and Servicer Dock pointing start at T+1 s; the port-relative standoff starts at T+10 s; alignment-gated closure starts at T+180 s.

Good luck. Remember: when in doubt during RPO, abort first and investigate second.
