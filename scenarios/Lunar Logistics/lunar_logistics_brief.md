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
3. **Inspect co-orbital debris** — A rocket body (R/B) orbits near the hub. Determine its range, spin rate, and identity markings using your optical camera and laser range finders.
4. **Conduct lunar observation** — Use the main optical camera to survey the lunar surface and locate features of interest on the far side.

### Phase 3 — Communications awareness

Throughout the hour:

1. **Maintain DSN contact where possible** — Your downlink and uplink run through Canberra. Monitor the Link Budget panel and connection telemetry.
2. **Plan around the blackout** — Lunar geometry will cause a **telecommunications blackout** with the DSN **sometime between 10 and 20 minutes** into the simulation. Use the healthy link period before blackout to complete time-critical commanding and downloads; after contact returns, verify hub and spacecraft state and recover any deferred operations.

### Operational constraints (important)

| Constraint | Detail |
| --- | --- |
| Propulsion | No thrusters installed |
| Attitude control | Reaction wheels present but **disabled** at start |
| RPO software | **Not available** — no automated rendezvous/proximity guidance |
| Post-undock manoeuvring | Separation impulse only; no return-to-hub manoeuvre |
| Starting fuel | 80 kg capacity, tank **full** at session start |
| Starting battery | 40 Wh capacity, **15% charge** at session start |
| Interconnect valve | **Closed** (0%) at start — must be commanded open for hub transfer |

---

## Your Spacecraft — Microsat Configuration

Each team operates one **Microsat** (`SC_001` class). Red Team berths on **Docking Port D**; Blue Team on **Docking Port E**. Configurations are identical; only the hub attachment differs.

### Platform summary

| Item | Configuration |
| --- | --- |
| Mass | 100 kg |
| Orbit | Lunar orbit (distinct from hub ephemeris while docked; rigidly attached via docking adapter) |
| Docking | Single docking adapter (+Y); separation force 3 N for 1 s |
| Power storage | Battery, 40 Wh nominal capacity |
| Propellant | Fuel tank, 80 kg capacity |
| Sensors | GPS; three laser range finders; main optical camera; docking camera |
| Comms | Receiver and transmitter (team-assigned frequency) |
| Propulsion / ACS | No thrusters; reaction wheels disabled |

### Payload and sensors

- **Main Camera** — nadir/survey imaging; 1024×1024, variable field of view (1°–15°).
- **Docking Camera** — berthing aid; 256×256, wide field of view (30°–60°).
- **Laser Range Finders** — LRF 0, LRF 120, and LRF 240; body-fixed on the +Y face, 10 km operating range. All three are aligned on the hub sightline while docked.
- **GPS Sensor** — enabled for position/navigation context.

---

## Power Network

Electrical power is generated by two body-mounted solar panels, stored in a single battery, and distributed to spacecraft loads and the hub interconnect. The fuel pump has **primary and backup power feeds** (each with switch, fuse, and controller).

### Power network diagram

![Microsat power network](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/lunar_logistics/power_network_diagram.png)
---

### Component starting states

| Component | Start state |
| --- | --- |
| Solar Panel +X / -X | Enabled |
| Battery | 15% charge fraction |
| Power Interconnect | **Open** (connected to hub while docked) |
| Fuel Pump Switch | **Closed** |
| Backup Fuel Pump Switch | **Open** |
| Fuel Pump Controller | Active (primary path) |
| Backup Fuel Pump Controller | Active (redundant path) |

## Fuel Network

Propellant flows from your onboard tank through a pump and valve to the **bidirectional fuel interconnect** at the docking interface. While docked, the interconnect couples to the hub port fuel line (Port D or E).

### Fuel network diagram

![Microsat fuel network](https://zendir-public-media-bucket.s3.ap-southeast-2.amazonaws.com/space_range/scenarios/lunar_logistics/fuel_network_diagram.png)


### Component starting states

| Component | Start state |
| --- | --- |
| Fuel Tank | 80 kg / 80 kg (full) |
| Fuel Pump | Enabled; max flow 0.2 kg/s |
| Interconnect Valve | **Closed** (0% open) |
| Fuel Interconnect | Connected to hub while docked |
### Fuel transfer notes

- Open the **Interconnect Valve** and energize the **fuel pump** power path before expecting flow into the hub.
- The hub port tanks accept ingoing propellant at a configured desired rate; monitor both spacecraft and hub tank telemetry during transfer.
- If flow stops unexpectedly, inspect **fuel and power subsystems together** — pump power is routed through switched, fused controller paths.

---

## Communications — Time Window and Blackout

### Ground station

| Station | Role |
| --- | --- |
| **Canberra (DSN)** | Sole ground station for uplink and downlink |

Minimum elevation mask is 0° (broad access). Use the **Link Budget** panel in the operator terminal for predicted contact intervals, signal-to-noise ratio, and pass geometry.

### Expected contact profile

| Period | Expectation |
| --- | --- |
| **0 – ~10 min** | Nominal DSN contact at session start under typical lunar pass geometry. Downlink should be healthy — use this window for baseline link metrics and early commanding. |
| **~10 – ~20 min** | **Blackout zone.** The Lunar Gateway (and your spacecraft, when using the same ground link) will **lose DSN access** for a interval within this window due to lunar occlusion and orbit geometry. **Do not assume continuous contact** through this period. |
| **After blackout** | Contact is restored for the remainder of the hour. Re-establish telemetry checks and complete deferred tasks. |

> **Planning tip:** Before the blackout, prioritize commands and data collection that require ground confirmation. After contact returns, verify fuel transfer status, hub state, and any procedures interrupted during the gap.

### Team frequencies

| Team | Frequency (MHz) |
| --- | ---: |
| Red Team | 473 |
| Blue Team | 475 |

Each team commands only its own microsat. The Lunar Gateway and debris object are **neutral** assets (not team-owned).

---

## Environment and Other Participants

| Asset | Role |
| --- | --- |
| **Lunar Gateway (hub)** | Neutral logistics hub; dual berthing (Ports D and E); fuel and power interconnects per port |
| **Debris rocket body** | Neutral co-orbital object near the hub — characterize as part of proximity awareness |
| **Red / Blue microsats** | Your team spacecraft; identical design, separate hub ports |

The Moon includes a marked surface feature (star-shaped crater) on the far side for optical navigation exercises.

---

## Suggested Team Roles

Split responsibilities early:

- **Propulsion / fluids** — Fuel valve, pump power paths, tank levels, hub top-off procedure
- **Power / EPS** — Battery charge, solar panels, interconnect status, pump circuit health
- **Guidance / navigation** — Dock/undock sequencing, LRF telemetry, GPS
- **Payload / imaging** — Cameras, debris inspection, lunar surface search
- **Comms** — Link Budget monitoring, blackout timing, ground pass planning
- **Mission lead** — Timeline, cross-check telemetry, coordinate undock decision

---

## Before You Begin

1. Log in to the operator terminal with your team credentials.
2. Confirm docked state, subsystem telemetry, and Link Budget at **T+0**.
3. Read the in-simulation questions to understand scored tasks — prioritize by team expertise.
4. Replace the S3 placeholder URLs in this document (or in your distributed copy) if your instructor provides network diagrams.

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
