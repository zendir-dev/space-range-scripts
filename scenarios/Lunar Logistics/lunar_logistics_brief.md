**Scenario:** Lunar Logistics  
**Epoch:** 2026-02-14 00:00:00 UTC  
**Duration:** 60 minutes  
**Ground Segment:** Canberra Deep Space Network (DSN)

---

## Overview

You are the operator of a logistics microsatellite in lunar orbit, currently **docked** to the **Lunar Gateway Hub**. Your spacecraft shares the cis-lunar environment with the hub and a co-orbital debris object. Each team operates an identical microsat from a separate docking port.

Questions and scoring are delivered in the **Tasks** section. Use this brief for mission context, spacecraft configuration, and communications constraints.

---

## Mission Goals

### Phase 1 - Docked Logistics

While attached to the Lunar Gateway:

1. **Assess Spacecraft State:**  Review power, fuel, and subsystem telemetry before commanding transfers.
2. **Support Hub Propellant Resupply:** Your microsat carries a full onboard fuel supply. Configure the fuel path and transfer propellant into the hub port tank through the fuel interconnect until the hub stops accepting fuel or your procedure is complete.
3. **Manage Power Sharing:** Your power interconnect is available for bidirectional energy exchange with the hub. Monitor battery charge and hub power while docked; low starting charge fraction means solar recharge and power routing matter during early operations. Ensure your battery does not go below 10% charge.
4. **Execute Fuel Transfer Safely:** The fuel path includes a pump, valves, and redundant power feeds. Watch fuel and power telemetry throughout the transfer; anomalies can interrupt flow and must be diagnosed from subsystem data.

### Phase 2 - Communications Blackout

At some point between **10** and **20** minutes into the operation, it is expected that your spacecraft will lose access to the Deep Space Network (DSN) as the spacecraft is eclipsed by the moon. Ensure the following:

1. **Suspend Operations:** Ensure that before the blackout occurs, operations are suspended to ensure that systems do not fail during the process.
2. **Run Diagnostics:** Once the blackout has ended and communications resumes with the DSN, run a full diagnostics check on all systems, validating that no issues occurred during the time.
3. **Resume Operations:** Once validated, resume standard operations.

### Phase 3 - Undocking & Inspection

After logistics tasks are complete, and **once the blackout has finished**, perform the following actions:

1. **Undock from the Lunar Gateway:** Command separation through your docking adapter. There is **no** RPO guidance software and **no** onboard thrusters. After undock, you drift under the separation impulse only.
2. **Characterize Relative Motion:** Three body-fixed laser range finders (LRF 0, LRF 120, LRF 240) are already sighted on the hub at undock. Use them to measure range, range rate, and any sensor disagreement after separation.
3. **Inspect Co-Orbital Debris:** A rocket body (R/B) orbits near the hub. Determine its range, spin rate, and identity markings using your optical camera and laser range finders.
4. **Conduct Lunar Observation:** Use the main optical camera to survey the lunar surface and locate features of interest on the far side.

> Once undocked, your spacecraft will not be able to re-dock with the Lunar Gateway again. Make sure once your team undocks from the hub, all docking tasks have been completed.


### Operational Constraints

| Constraint | Detail |
| --- | --- |
| Propulsion | No thrusters installed |
| Attitude Control | Reaction wheels present but **disabled** while docked |
| RPO Software | **Not available** - no automated rendezvous/proximity guidance |
| Post-Undock Manoeuvring | Separation impulse only; no return-to-hub manoeuvre |
| Starting Fuel | 80 kg capacity, tank **full** at session start |
| Starting Battery | 40 Wh capacity, **15% charge** at session start |
| Interconnect Valve | **Closed** (0%) at start - must be commanded open for fuel transfer |

---

## Microsat Configuration

Each team operates one identical **Microsat**. Each team will be given a designated docking port on the hub, which the spacecraft will begin docked from.

### Platform Summary

| Item | Configuration |
| --- | --- |
| Mass | 100 kg |
| Orbit | Lunar orbit
| Docking | Single docking adapter |
| Power storage | Battery, 40 Wh nominal capacity |
| Propellant | Fuel tank, 80 kg capacity |
| Sensors | GPS; three laser range finders; main optical camera; docking camera |
| Comms | Receiver and transmitter |
| Propulsion / ACDS | No thrusters, three reaction wheels |

### Payload and sensors

- **Main Camera:** Nadir/survey imaging; 1024×1024, variable field of view (1°–15°).
- **Docking Camera:** Berthing aid; 256×256, wide field of view (30°–60°).
- **Laser Range Finders:** LRF 0, LRF 120, and LRF 240; body-fixed on the +Y face, 10 km operating range. All three are aligned on the hub sightline while docked.
- **GPS Sensor:** nabled for position/navigation context.

---

## Power Network

Electrical power is generated by two body-mounted solar panels, stored in a single battery, and distributed to spacecraft loads and the hub interconnect. The fuel pump has **primary and backup power feeds** (each with switch, fuse, and controller).

### Power Network Diagram

![Microsat power network](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/lunar_logistics/power_network_diagram.png)
---

### Component starting states

| Component | Start State |
| --- | --- |
| Solar Panel +X / -X | Enabled |
| Battery | 15% charge fraction |
| Power Interconnect | **Open** (connected to hub while docked) |
| Fuel Pump Switch | **Closed** |
| Backup Fuel Pump Switch | **Open** |
| Fuel Pump Controller | Active (primary path) |
| Backup Fuel Pump Controller | Active (redundant path) |

---

## Fuel Network

Propellant flows from the onboard tank through a pump and valve to the **fuel interconnect** at the docking interface. While docked, the interconnect couples to the hub port fuel line.

### Fuel Network Diagram

![Microsat fuel network](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/lunar_logistics/fuel_network_diagram.png)


### Component starting states

| Component | Start State |
| --- | --- |
| Fuel Tank | 80 kg / 80 kg (full) |
| Fuel Pump | Enabled |
| Interconnect Valve | **Closed** (0% open) |
| Fuel Interconnect | Connected to hub while docked |

### Fuel transfer notes

- Open the **Interconnect Valve** and energize the **Fuel Pump** power path before expecting flow into the hub.
- The hub port tanks accept ingoing propellant at a configured desired rate; monitor spacecraft tank telemetry during transfer.
- If flow stops unexpectedly, inspect **fuel and power subsystems together** - pump power is routed through switched, fused controller paths.

---

## Communications - Time Window and Blackout

### Ground station

| Station | Role |
| --- | --- |
| **Canberra (DSN)** | Sole ground station for uplink and downlink |

Use the **Link Budget** panels in the operator terminal for predicted contact intervals, signal-to-noise ratio, and pass geometry.

### Expected Contact Profile

| Period | Expectation |
| --- | --- |
| **0 – 10 min** | Nominal DSN contact at session start under typical lunar pass geometry. Downlink should be healthy - use this window for baseline link metrics and early commanding. |
| **10 – 20 min** | **Blackout zone.** The Lunar Gateway will **lose DSN access** for a interval within this window due to lunar occlusion and orbit geometry. **Do not assume continuous contact** through this period. |
| **After Blackout** | Contact is restored for the remainder of the hour. Re-establish telemetry checks and complete deferred tasks. |

> **Planning Tip:** Before the blackout, prioritize commands and data collection that require ground confirmation. After contact returns, verify fuel transfer status, hub state, and any procedures interrupted during the gap.

### Team Frequencies

Each team commands only its own microsat. The Lunar Gateway and debris object are **neutral** assets and are not controllable. Your team will be assigned a communications frequency that is unique at the start of the scenario, that will be pre-configured. This frequency will be the same on the downlink and uplink communications link.

---

## Suggested Team Roles

Split responsibilities early. The Mission Lead should assign these roles at the start of the exercise:

- **Mission Lead:** Tasked with designating roles, answering questions, monitoring key information, and making go/no-go decisions.
- **Satellite Operator:** Tasked with managing telemetry, guidance pointing, key health telemetry, and power / fuel transfer.
- **Payload Operator:** Tasked with capturing payload and sensor data, including camera imagery, laser range finder measurements, and debris or surface observations.
- **Communications Specialist:** Tasked with monitoring link budgets, GPS locations, ground-station contact windows, and blackout timing.

---

## Before You Begin

1. Log in to the operator terminal with your team credentials.
2. Confirm docked state, subsystem telemetry, and Link Budget at **T+0**.
3. Read the in-simulation questions to understand scored tasks - prioritize by team expertise.

---

## Learning focuses

### Docked Logistics

Configure fuel and power paths through the docking interconnects, execute a hub propellant resupply, and monitor tank levels and battery state while berthed at the Lunar Gateway.

### Subsystem Diagnosis

Read coupled fuel and power telemetry to detect transfer interruptions, trace faults through switched pump power paths, and restore or work around anomalies during logistics operations.

### Proximity Awareness

Command undock under manual constraints (no RPO software, no thrusters), use body-fixed laser range finders to measure separation dynamics and sensor calibration, and characterize co-orbital debris with optical and ranging sensors.

### Communications Planning

Use the Link Budget panel and Canberra DSN visibility to establish a healthy baseline link, anticipate the mid-simulation blackout window, and prioritize commanding and data collection around ground contact gaps.
