# 🛰️ Space Range Scripts

A Python scripting framework for automating spacecraft operations in **Space Range** — a simulated space operations environment used for training spacecraft operators. Scripts con## 🖨️ Coloured Output (`printer`)ect## 📖 Command Referenceto the Space Range MQTT broker, listen to the simulation clock, and fire pre-scheduled commands at precise simulation times.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Writing a Scenario Script](#writing-a-scenario-script)
  - [Configuration](#configuration)
  - [Scheduling Commands](#scheduling-commands)
  - [Ground Requests](#ground-requests)
  - [Running a Script](#running-a-script)
- [Coloured Output (`printer`)](#️-coloured-output-printer)
- [Command Reference](#command-reference)
- [Schemas](#schemas)

---

## 🔭 Overview

> **⚠️ Prerequisites — A Space Range game must be actively running for any script in this repository to function.** This library acts as a spacecraft controller client — it connects to the Space Range MQTT broker, authenticates as a specific team, and autonomously sends commands to control an assigned space asset within the live simulation. Without an active Space Range game instance broadcasting session data on the configured broker, scripts will connect successfully but receive no session clock and no commands will ever be dispatched.

Each Space Range scenario runs a live simulation that broadcasts a session clock over MQTT. Operator scripts connect to the broker, listen to that clock, and automatically send encrypted commands to a spacecraft at the right simulation time.

```
Session Clock (MQTT)
      │
      ▼
 SpaceRangeClient
      │
      ├──► EventScheduler ──► send_command() ──► Uplink topic (XOR encrypted)
      │
      └──► Ground Requests ──► Request topic  ──► Response topic (blocking)
```

Key behaviours:

- ⏱️ **Time-driven execution** — commands fire when the simulation clock passes their trigger time, not wall-clock time.
- 🔄 **Simulation reset detection** — if the simulation restarts mid-session (new `instance` ID), all scheduled events are automatically reset and will re-execute.
- 🔐 **Encrypted uplink** — every command is XOR-encrypted with the team's unique password before being published.
- 📡 **Blocking ground requests** — query the ground controller synchronously (e.g. list assets, get telemetry) with a configurable timeout; returns `None` if no response arrives in time.

---

## 📁 Project Structure

```
space-range-scripts/
│
├── scenarios/                  # One script + one JSON config per scenario
│   ├── orbit_sentinel.py       # Example scenario script
│   └── orbit_sentinel.json     # Scenario configuration (simulation, teams, assets)
│
├── src/                        # Reusable framework library
│   ├── __init__.py
│   ├── config.py               # Scenario JSON loader & typed config dataclasses
│   ├── commands.py             # Command builder helpers (guidance, camera, jammer…)
│   ├── event_scheduler.py      # Time-based event queue (asset name → live ID resolution)
│   ├── scheduled_event.py      # ScheduledEvent dataclass
│   ├── mqtt_client.py          # SpaceRangeClient — MQTT connection & routing
│   ├── ground_client.py        # GroundRequestClient — blocking request/response calls
│   └── printer.py              # Coloured terminal output helpers (ANSI)
│
├── schemas/                    # Reference documentation for all data structures
│   ├── Command_Schema.md       # Uplink command packet format & all command types
│   ├── Ground_Schema.md        # Ground controller request/response API
│   ├── Session_Schema.md       # Session clock message format
│   └── Teams_Schema.md         # Team & collection configuration structure
│
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Configure your scenario**

Each scenario has a paired `.json` file (e.g. `scenarios/orbit_sentinel.json`) that defines the simulation parameters, teams, assets, and ground stations. Update the team IDs, passwords, frequencies, and asset IDs to match your Space Range instance.

**3. Run a scenario script**

```bash
python scenarios/orbit_sentinel.py
```

On startup you will be prompted for the game/instance name:

```
Game name [ZENDIR]:
```

Press **Enter** to use the default (`ZENDIR`), or type the name of your specific game instance. This name is used to construct the MQTT topic paths.

---

## ✍️ Writing a Scenario Script

### ⚙️ Configuration

`load_config()` automatically finds the scenario JSON by matching the calling script's filename. No path argument is needed:

```python
from src import load_config, prompt_game_name

game   = prompt_game_name()          # prompts operator at runtime
config = load_config(game=game)      # auto-loads scenarios/<script_name>.json

red_team   = config.get_team("RED")
red_assets = config.get_assets_for_team(red_team)
ASSET_NAME = red_assets[0].name      # e.g. "Recon" — matched live against ground controller data
```

Asset IDs in Space Range are 8-character hex strings assigned at runtime by the simulation. The framework automatically resolves the live ID from the ground controller's `list_assets` response by matching against the asset's **name** — you never need to hard-code an ID.

You can also pass an explicit path if needed:

```python
config = load_config(path="scenarios/my_scenario.json", game="MYGAME")
```

### 🗓️ Scheduling Commands

Build an `EventScheduler` with your asset's **name** and add events using the `commands` helpers. The live asset ID is resolved automatically at runtime — you never need to look it up yourself:

```python
from src import EventScheduler
from src import commands

scheduler = EventScheduler(asset_name=ASSET_NAME)   # name matched live against ground controller

scheduler.add_event("Sun Pointing",       trigger_time=100.0,  **commands.guidance_sun("Solar Panel"))
scheduler.add_event("Nadir Pointing",     trigger_time=300.0,  **commands.guidance_nadir("Camera"))
scheduler.add_event("Point Jammer",       trigger_time=600.0,  **commands.guidance_ground("Jammer", station="Dubai"))
scheduler.add_event("Start Jamming",      trigger_time=700.0,  **commands.jammer_start([blue_team.frequency], power=3.0))
scheduler.add_event("Stop Jamming",       trigger_time=800.0,  **commands.jammer_stop())
```

Events are always executed in trigger-time order regardless of the order they are added.

### 📡 Ground Requests

`SpaceRangeClient` exposes blocking ground request methods inherited from `GroundRequestClient`. Each call publishes an encrypted request and waits for a matching response (matched by a random `req_id`). Returns `None` if no response arrives within the timeout.

```python
# List all assets assigned to your team
assets = client.list_assets()
if assets:
    for a in assets["space"]:
        print(a["asset_id"], a["name"])

# Inspect components on a specific asset
entity = client.list_entity(ASSET_ID)

# Check link budget
telem = client.get_telemetry(ASSET_ID, timeout=5.0)

# Update frequency and key
client.set_telemetry(frequency=510.0, key=42)

# List available ground stations
stations = client.list_stations()

# Ask the AI assistant (initial ack is immediate; answer arrives via on_event)
client.chat_query(ASSET_ID, "What is the current battery state?")
```

**Unsolicited notifications** (e.g. `event_triggered`, `chat_response`) are routed to an optional callback:

```python
def handle_event(evt: dict):
    print(f"Notification: {evt['type']} — {evt['args'].get('name', '')}")

client = SpaceRangeClient(..., on_event=handle_event)
```

### ▶️ Running a Script

Pass the client a config, team, and scheduler, then call `connect_and_run()`. There is no `asset_id` argument — the live ID is resolved automatically from the ground controller using the asset name set on the scheduler:

```python
from src import SpaceRangeClient

client = SpaceRangeClient(
    config=config,
    team=red_team,
    scheduler=scheduler,
    on_event=handle_event,   # optional
)

client.print_banner()
scheduler.print_schedule()
client.connect_and_run()    # blocks until Ctrl+C
```

---

## �️ Coloured Output (`printer`)

The `src.printer` module provides coloured ANSI terminal output helpers used throughout the framework. You can use the same helpers in your own scenario scripts for consistent, readable output. Colours are automatically disabled when the output stream is not a TTY (e.g. when piping to a file or running in CI), and the `NO_COLOR` environment variable is respected.

```python
from src import printer

printer.banner("SPACE RANGE — Orbital Sentinel")   # bold white banner
printer.info("Connecting to broker…")            # cyan  — connection / instance events
printer.success("Asset ID resolved: 2D708E04")  # green — resolved IDs, commands sent OK
printer.warn("Retrying asset resolution…")      # yellow — non-fatal issues
printer.error("Unexpected response format")     # red   — failures needing attention
printer.log("t=100.0s | UTC: 2025/04/15")       # grey  — periodic heartbeat lines
printer.sent("guidance", asset="2D708E04",      # magenta — uplink command details
             args={"pointing": "sun"})
printer.event(sim_time=500.0,                   # blue  — event trigger notifications
              name="Point Jammer to Madrid")
printer.divider()                               # grey separator line
```

| Helper | Colour | Typical use |
|---|---|---|
| `banner(title, width, subtitle)` | Bold white | Startup header |
| `info(msg)` | Cyan | Connection, subscription, instance tracking |
| `success(msg)` | Green | Asset ID resolved, command dispatched |
| `warn(msg)` | Yellow | Non-fatal issues, skipped events, resets |
| `error(msg)` | Red | Connection failures, bad responses |
| `log(msg)` | Grey | Periodic session-clock heartbeat lines |
| `sent(command, asset, args)` | Magenta | Uplink command just published |
| `event(sim_time, name, description)` | Blue | Scheduled event firing |
| `complete(name)` | Green | Event execution confirmed |
| `request(request_type, req_id)` | Cyan | Outgoing ground request |
| `resolve(msg)` | Cyan | Asset name→ID resolution status |
| `divider(width)` | Grey | Section separator |

---

## �📖 Command Reference

All command helpers live in `src/commands.py` and return a dict that unpacks directly into `scheduler.add_event()`.

### 🧭 Guidance & Pointing

Controls the spacecraft's ADCS (Attitude Determination and Control System) to orient a named component in a particular direction. The `target` is the component name (e.g. `"Camera"`, `"Solar Panel"`, `"Jammer"`) and `alignment` is the component axis to point (default `+z`).

| Function | Description |
|---|---|
| `guidance_sun(target, alignment)` | Points the target component's axis toward the Sun. Commonly used to maximise solar power generation by aligning solar panels face-on. |
| `guidance_nadir(target, alignment, planet)` | Points the target component down toward the surface of a planet (nadir direction). Ideal for Earth observation — align the camera downward before a capture. |
| `guidance_velocity(target, alignment)` | Aligns the target component's axis with the spacecraft's velocity vector. Useful for ram-facing sensors or aerodynamic attitude modes. |
| `guidance_inertial(target, alignment, pitch, roll, yaw)` | Holds a fixed inertial attitude defined by pitch, roll, and yaw angles. Useful for star tracking, deep-space imaging, or holding a known orientation. |
| `guidance_ground(target, alignment, station)` | Points the target component toward a named ground station. Use this to pre-point a directional antenna or jammer at a specific station before operating. |
| `guidance_location(target, lat, lon, alt, alignment, planet)` | Points the target component toward an arbitrary latitude, longitude, and altitude on a planet's surface. Useful for imaging specific ground targets or objects of interest. |
| `guidance_spacecraft(target, spacecraft_id, alignment)` | Points the target component toward another spacecraft identified by its asset ID. Required for RPO (Rendezvous and Proximity Operations) and inter-spacecraft imaging. |
| `guidance_idle()` | Stops all ADCS torque output — the reaction wheels cease commanding and the spacecraft drifts. Saves power when attitude control is not required. |

### 📻 Jammer

Controls the on-board RF jamming transmitter. The jammer outputs interference on one or more frequencies to disrupt another team's uplink or downlink channel. Higher power increases jamming effectiveness but drains the battery faster.

| Function | Description |
|---|---|
| `jammer_start(frequencies, power)` | Activates the jammer on the specified list of frequencies (MHz) at the given power level (W). Supports multi-band barrage jamming by supplying multiple frequencies. The spacecraft must first be pointed toward the target using a guidance command. |
| `jammer_stop()` | Deactivates the jammer immediately, ceasing all RF interference output and stopping the associated power draw. |

### 📥 Downlink

Manages the transfer of stored sensor data and images from the spacecraft's on-board storage down to the ground station network via the telecommunication system.

| Function | Description |
|---|---|
| `downlink(ping)` | Triggers an immediate downlink of all data currently cached in on-board storage. Set `ping=True` to also enable automatic downlink on every subsequent spacecraft ping (approximately every 20 simulation seconds). |
| `downlink_ping_on()` | Enables automatic downlink on every ping cycle. Keeps the storage cache clear and data continuously flowing to the ground, at the cost of increased transmitter power usage. |
| `downlink_ping_off()` | Disables automatic ping-triggered downlinks. Data will only be sent when a manual downlink command is issued. |

### 📷 Camera

Configures and operates the on-board imaging system. Camera configuration should be performed before capture to ensure the correct field of view, resolution, and focus settings are applied.

| Function | Description |
|---|---|
| `camera_configure(target, fov, resolution, focal_length, aperture, monochromatic, sample, focusing_distance, pixel_pitch, coc)` | Configures all optical and sensor parameters for the named camera component. Key parameters include `fov` (field of view in degrees), `resolution` (image size in pixels, square), `focal_length` (mm), `aperture` (mm), and `focusing_distance` (m) for close-range targets. Set `sample=True` to downlink a 32×32 preview on the next ping. Set `monochromatic=True` to reduce downlink data size at the cost of colour information. |
| `camera_capture(target, name)` | Captures a full-resolution image from the named camera and stores it in on-board storage with the given name. The image is not transmitted until a downlink command is issued. The name is stored in the first 50 bytes of the image data. |

### 📶 Telemetry

Updates the communication parameters of the spacecraft and ground station network. This affects the frequency and encryption key used on the RF link between the spacecraft and the ground station — not the MQTT broker connection.

| Function | Description |
|---|---|
| `telemetry_configure(frequency, key)` | Sets the uplink and downlink frequency (MHz) and Caesar cipher key (0–255) for the spacecraft's communication channel. Use this to change frequency if another team is interfering, or to rotate the encryption key if it may have been compromised. Both the spacecraft receiver/transmitter and the ground station network are updated together. |

### 🔥 Thruster

Commands the spacecraft's propulsion system to perform orbital manoeuvres. Thrust is applied in the spacecraft body frame, so attitude should be set correctly before firing.

| Function | Description |
|---|---|
| `thruster_fire(target, duration)` | Fires the named thruster for the specified duration in seconds. Used for delta-V manoeuvres such as orbit raising, lowering, or plane changes. Ensure the spacecraft is correctly pointed before firing to achieve the desired orbital effect. |
| `thruster_stop(target)` | Immediately cuts thrust from the named thruster, regardless of any remaining scheduled burn duration. |

### 🤝 Rendezvous

Commands the spacecraft to autonomously navigate to and hold position relative to another space asset using RPO (Rendezvous and Proximity Operations) guidance. The offset is specified in the target's LVLH (Local Vertical Local Horizontal) frame: X = radial, Y = along-track, Z = cross-track.

| Function | Description |
|---|---|
| `rendezvous_start(target_id, offset_x, offset_y, offset_z)` | Initiates autonomous rendezvous with the spacecraft identified by `target_id`, manoeuvring to and holding at the specified LVLH offset (metres). Used for inspection, formation flying, or pre-docking proximity holds. Requires `enable_rpo: true` in the spacecraft controller configuration. |
| `rendezvous_stop(target_id)` | Cancels the active rendezvous manoeuvre with the specified target, halting autonomous proximity navigation. The spacecraft will retain its current attitude and velocity at the time of cancellation. |

### 🔗 Docking

Commands the spacecraft to physically dock with or undock from a component on another spacecraft. The spacecraft must be in close proximity (typically via a rendezvous hold) before docking can succeed.

| Function | Description |
|---|---|
| `docking_dock(target_id, component)` | Commands the spacecraft to dock with the named component (e.g. a docking adapter) on the target spacecraft. Once docked, the two spacecraft move as a single rigid body. |
| `docking_undock(target_id, component)` | Commands the spacecraft to release from the named docking component on the target spacecraft, separating the two vehicles. |

### 🔁 Component Reset

| Function | Description |
|---|---|
| `component_reset(target)` | Reboots the named component on the spacecraft. If a component has become corrupted or non-functional (due to an error model or scenario event), a reset may restore it to an operational state. Note that resetting certain components (e.g. the computer) will cause the entire spacecraft to reboot, which may take up to a minute of simulation time before commands can be received again. |

---

## 📚 Schemas

Detailed reference documentation for all data structures used in Space Range:

| Schema | Description |
|---|---|
| [Command Schema](schemas/Command_Schema.md) | Full specification for uplink command packets — all commands, arguments, ranges, and units |
| [Ground Schema](schemas/Ground_Schema.md) | Ground controller request/response API — all request types, response formats, and unsolicited notifications |
| [Session Schema](schemas/Session_Schema.md) | Session clock message format broadcast by the simulation |
| [Teams Schema](schemas/Teams_Schema.md) | Team and collection configuration structure within the scenario JSON |
