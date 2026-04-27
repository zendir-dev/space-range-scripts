# 🛰️ Space Range Scripts

A Python scripting framework for automating spacecraft operations in **Space Range** — a simulated space operations environment used for training spacecraft operators. Scripts connect to the Space Range MQTT broker, listen to the simulation clock, and fire pre-scheduled commands at precise simulation times.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Writing a Scenario Script](#writing-a-scenario-script)
  - [The `Scenario` Class (recommended)](#-the-scenario-class-recommended)
  - [Configuration](#configuration)
  - [Scheduling Commands](#scheduling-commands)
  - [Ground Requests](#ground-requests)
  - [Admin Requests](#admin-requests)
  - [Running a Script](#running-a-script)
- [Coloured Output (`printer`)](#️-coloured-output-printer)
- [Command helpers (`src/commands.py`)](#-command-helpers-srccommandspy)
- [Documentation](#-documentation)

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
      ├──► EventScheduler ──► send_command() ──► Uplink topic     (XOR encrypted, team password)
      │
      ├──► Ground Requests ──► Request topic  ──► Response topic  (blocking, team password)
      │
      └──► Admin Requests  ──► Admin/Request  ──► Admin/Response  (blocking, admin password)
```

Key behaviours:

- ⏱️ **Time-driven execution** — commands fire when the simulation clock passes their trigger time, not wall-clock time.
- 🔄 **Simulation reset detection** — if the simulation restarts mid-session (new `instance` ID), all scheduled events are automatically reset and will re-execute.
- 🔐 **Encrypted uplink** — every command is XOR-encrypted with the team's unique password before being published.
- 📡 **Blocking ground requests** — query the ground controller synchronously (e.g. list assets, get telemetry) with a configurable timeout; returns `None` if no response arrives in time.
- 🕵️ **Admin requests** — constructive agents and instructors can query live telemetry, events, and simulation state for all teams simultaneously via a separate admin channel encrypted with a dedicated admin password.
- 📝 **Automatic session logging** — every line printed to the terminal is also written in plain text to `logs/YYYY-MM-DD_HH-MM-SS_<instance>.log`. A new log file is opened each time a new simulation instance is detected (including resets).

---

## 📁 Project Structure

```
space-range-scripts/
│
├── scenarios/                  # One script + one JSON config per scenario
│   ├── orbital_sentinel.py     # Example scenario script
│   └── orbital_sentinel.json   # Scenario configuration (simulation, teams, assets)
│
├── src/                        # Reusable framework library
│   ├── __init__.py
│   ├── scenario.py             # Scenario — high-level base class for scenario scripts
│   ├── config.py               # Scenario JSON loader & typed config dataclasses
│   ├── commands.py             # Command builder helpers (guidance, camera, jammer…)
│   ├── event_scheduler.py      # Time-based event queue (asset name → live ID resolution)
│   ├── scheduled_event.py      # ScheduledEvent dataclass (supports pre_trigger hooks)
│   ├── mqtt_client.py          # SpaceRangeClient — MQTT connection & routing
│   ├── ground_client.py        # GroundRequestClient — blocking request/response calls
│   ├── admin_client.py         # AdminRequestClient — instructor/agent admin API
│   ├── printer.py              # Coloured terminal output + session log file writer
│   └── utils.py                # decode_payload — robust JSON decoding helpers
│
├── logs/                       # Auto-generated session logs (git-ignored)
│   └── YYYY-MM-DD_HH-MM-SS_<instance>.log
│
├── docs/                       # User documentation (start here)
│   ├── README.md               # Documentation hub
│   ├── introduction/           # Overview, architecture, glossary
│   ├── concepts/               # Teams, simulation clock, encryption, telemetry
│   ├── getting-started/        # Prerequisites, connecting, first command, Operator UI
│   ├── api-reference/          # MQTT topics, commands, ground & admin requests
│   ├── guides/                 # Encryption, decoding telemetry, scenarios, instructor, UI, troubleshooting
│   ├── scenarios/              # Scenario JSON authoring reference (per-block deep dive)
│   └── reference/              # Packet formats, data types
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

Each scenario has a paired `.json` file (e.g. `scenarios/orbital_sentinel.json`) that defines the simulation parameters, teams, assets, and ground stations. Update the team IDs, passwords, frequencies, and asset IDs to match your Space Range instance.

**3. Run a scenario script**

```bash
python scenarios/orbital_sentinel.py
```

On startup you will be prompted for the game/instance name and admin password:

```
Game name [ZENDIR]:
Admin password [      ]:
```

Press **Enter** to accept the saved defaults, or type new values. Both are saved to `.space-range-defaults` at the project root for convenience on subsequent runs — this file is excluded from version control. The game name is used to construct all MQTT topic paths. The admin password unlocks the admin API for querying live telemetry across all teams.

---

## ✍️ Writing a Scenario Script

### 🚀 The `Scenario` Class (recommended)

The `Scenario` class is the fastest way to write a new scenario. It handles every piece of boilerplate automatically — credentials, config loading, team/asset lookup, enemy enumeration, scheduler creation, client setup, and the startup banner — so your script only needs to define the event schedule and any custom logic.

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import Scenario, commands

# All setup in one line: prompts for credentials, loads the JSON config,
# resolves your team and its primary asset, enumerates enemy teams.
scenario = Scenario(team_name="RED")

scheduler = scenario.scheduler
scheduler.add_event("Sun Point", trigger_time=100.0, **commands.guidance_sun("Solar Panel"))
scheduler.add_event("Nadir",     trigger_time=500.0, **commands.guidance_nadir("Camera"))

if __name__ == "__main__":
    scenario.run()   # creates the client, prints the banner, connects and runs
```

That's a complete, working scenario script. The `Scenario` object exposes everything you need:

| Attribute | Type | Description |
|---|---|---|
| `scenario.config` | `ScenarioConfig` | Full parsed scenario configuration |
| `scenario.team` | `TeamConfig` | The controlling team (e.g. RED) |
| `scenario.asset` | `AssetConfig` | Primary asset from the team's collection |
| `scenario.scheduler` | `EventScheduler` | Pre-built scheduler for the asset |
| `scenario.enemy_teams` | `list[TeamConfig]` | All other enabled teams |
| `scenario.enemy_fallback_freqs` | `list[float]` | Their frequencies from config (MHz) |
| `scenario.enemy_asset_ids` | `list[str]` | Live IDs resolved on connect (empty until then) |
| `scenario.client` | `SpaceRangeClient` | Available after `scenario.run()` is called |

#### Live frequency lookups in `pre_trigger` hooks

`scenario.live_enemy_frequencies()` is a ready-made helper for jammer scenarios. It waits for enemy IDs to be resolved on connect, queries each asset's current frequency via the admin API, and falls back to config values if the query fails — all in one call:

```python
def live_jammer_args(default_args: dict) -> dict:
    freqs = scenario.live_enemy_frequencies()   # blocks briefly if IDs not yet ready
    return {**default_args, "frequencies": freqs}

scheduler.add_event(
    name="Start Jamming",
    trigger_time=700.0,
    pre_trigger=live_jammer_args,
    **commands.jammer_start(frequencies=scenario.enemy_fallback_freqs, power=3.0),
)
```

#### Custom `on_connect` work

Enemy asset IDs are resolved automatically on connect. If you need to do additional setup (e.g. extra admin queries) once the connection is live, pass an `on_connect` callback to `run()`. Call `scenario.resolve_enemy_ids()` from within it if you still need live IDs:

```python
def on_connected():
    scenario.resolve_enemy_ids()          # keep built-in ID resolution
    result = scenario.client.admin.get_simulation()
    printer.info(f"Sim speed: {result['args']['speed']}×")

scenario.run(on_connect=on_connected)
```

#### Optional callbacks

All four `SpaceRangeClient` callbacks are forwarded through `scenario.run()`:

```python
scenario.run(
    on_connect=on_connected,         # called once after subscriptions are live
    on_session=handle_session,       # called on every session clock tick
    on_event=handle_event,           # called for unsolicited ground notifications
    on_admin_event=handle_admin,     # called for unsolicited admin push messages
)
```

---

### ⚙️ Configuration

`load_config()` automatically finds the scenario JSON by matching the calling script's filename. Use `prompt_credentials()` to collect both the game name and admin password at startup — previously entered values are offered as defaults:

```python
from src import load_config, prompt_credentials

game, admin_password = prompt_credentials()   # prompts for game name + admin password
config = load_config(game=game)               # auto-loads scenarios/<script_name>.json

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

scheduler.add_event("Sun Pointing",   trigger_time=100.0, **commands.guidance_sun("Solar Panel"))
scheduler.add_event("Nadir Pointing", trigger_time=300.0, **commands.guidance_nadir("Camera"))
scheduler.add_event("Point Jammer",   trigger_time=600.0, **commands.guidance_ground("Jammer", station="Dubai"))
scheduler.add_event("Start Jamming",  trigger_time=700.0, **commands.jammer_start([500.0], power=3.0))
scheduler.add_event("Stop Jamming",   trigger_time=800.0, **commands.jammer_stop())
```

Events are always executed in trigger-time order regardless of the order they are added.

#### ⚡ Live `pre_trigger` hooks

For events where the arguments need to be resolved at the **moment of firing** rather than at schedule-build time, pass a `pre_trigger` callable. It receives the event's default `args` dict and must return the final `args` dict to use:

```python
def live_jammer_args(default_args: dict) -> dict:
    # Called at t=700s, just before the command is sent.
    # Query current enemy frequencies from the admin API.
    live_freqs = client.admin.get_live_frequencies(
        asset_ids=enemy_asset_ids,
        fallback_frequencies=[500.0, 510.0],  # used if a query fails
    )
    return {**default_args, "frequencies": live_freqs}

scheduler.add_event(
    name="Start Jamming",
    trigger_time=700.0,
    pre_trigger=live_jammer_args,   # runs just before the command fires
    **commands.jammer_start(frequencies=[500.0, 510.0], power=3.0),
)
```

If `pre_trigger` raises an exception it is caught, logged, and the event fires with its default args — so the jammer always fires even if the admin query fails.

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

### 🕵️ Admin Requests

`SpaceRangeClient` holds an `AdminRequestClient` instance at `client.admin`. It uses the separate `Admin/Request` and `Admin/Response` MQTT topics, encrypted with the **admin password**, and gives constructive agents read access to live data for every team simultaneously.

> **⚠️ The admin password must not be shared with participant teams** — it provides full read access to all team telemetry, frequencies, and passwords.

```python
# Fetch all team names, IDs, and passwords; and all ground stations
entities = client.admin.list_entities()

# Fetch full details (asset IDs, components) for a specific team
team_info = client.admin.list_team("Blue Team")
asset_ids = [a["asset_id"] for a in team_info["args"]["assets"]["space"]]

# Query the most-recent telemetry data point for a spacecraft
data = client.admin.query_data("fb345a0c", recent=True)
freq = data["args"]["data"][-1]["communications.frequency"]

# Convenience helper — query live frequency for one asset
freq = client.admin.get_live_frequency("fb345a0c")   # returns float MHz or None

# Query live frequencies for multiple enemy assets (with fallbacks)
freqs = client.admin.get_live_frequencies(
    asset_ids=["fb345a0c", "2d708e04"],
    fallback_frequencies=[500.0, 510.0],
)

# Resolve all space asset IDs for a list of enemy team names
# (safe to call once at connect — IDs are stable within a running scenario)
mapping = client.admin.resolve_enemy_asset_ids(["Blue Team", "Green Team"])
# → {"Blue Team": ["fb345a0c"], "Green Team": ["2d708e04"]}

# Query historical events for an asset
events = client.admin.query_events(asset_id="fb345a0c")

# Get current simulation state and speed
sim = client.admin.get_simulation()
# → {"state": "Running", "speed": 5.0}

# Get all predefined scenario events (instructor-configured failures, etc.)
scenario_events = client.admin.get_scenario_events()
```

**Unsolicited `admin_event_triggered` notifications** (fired whenever any team sends a command or a scenario event triggers) arrive on the same `Admin/Response` topic and are routed to an optional callback:

```python
def handle_admin_event(evt: dict):
    args = evt["args"]
    print(f"[ADMIN] t={args['simulation_time']}s  {args['name']}  (team {args['team_id']})")

client = SpaceRangeClient(..., on_admin_event=handle_admin_event)
```

### ▶️ Running a Script

Pass the client a config, team, scheduler, and admin password, then call `connect_and_run()`. The live asset ID is resolved automatically from the ground controller using the asset name set on the scheduler:

```python
from src import SpaceRangeClient

client = SpaceRangeClient(
    config=config,
    team=red_team,
    scheduler=scheduler,
    admin_password=admin_password,   # from prompt_credentials()
    on_event=handle_event,           # optional — ground unsolicited notifications
    on_admin_event=handle_admin_event,  # optional — admin push notifications
)

client.print_banner()
scheduler.print_schedule()
client.connect_and_run()    # blocks until Ctrl+C
```

---

## 🖨️ Coloured Output (`printer`)

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

### 📝 Session log files

Every line printed to the terminal is **also written in plain text** (ANSI codes stripped) to a log file under `logs/`. A new file is opened automatically each time a new simulation instance is detected — including on simulation reset — so each run produces a separate, self-contained log:

```
logs/
└── 2026-03-27_14-32-05_29920346.log   ← real datetime + instance ID
```

The `logs/` directory is excluded from version control. Log files can be opened manually at any time using `printer.open_log(path)`:

```python
from src import printer
printer.open_log("logs/my_custom_run.log")   # all subsequent output also goes here
printer.close_log()                          # flush and close
printer.current_log_path()                  # returns path or None
```

---

## 📖 Command helpers (`src/commands.py`)

Every helper in `src/commands.py` returns a `dict` that unpacks directly into `scheduler.add_event(...)`. They are thin convenience wrappers around the underlying `command_request` MQTT messages — see [API Reference → Spacecraft commands](docs/api-reference/spacecraft-commands.md) for the wire format, every parameter, valid ranges, and units.

| Group | Helpers | Purpose |
|---|---|---|
| Guidance & pointing | `guidance_sun`, `guidance_nadir`, `guidance_velocity`, `guidance_inertial`, `guidance_ground`, `guidance_location`, `guidance_spacecraft`, `guidance_idle` | Orient a named component (camera, antenna, panel, jammer…) toward the Sun, nadir, velocity vector, a fixed inertial attitude, a ground station, an arbitrary lat/lon/alt, or another spacecraft. |
| Jammer | `jammer_start(frequencies, power)`, `jammer_stop()` | Activate / deactivate the on-board RF jammer on one or more frequencies. |
| Downlink | `downlink(ping)`, `downlink_ping_on()`, `downlink_ping_off()` | Trigger an immediate downlink of stored data, or toggle automatic per-ping downlinks. |
| Camera | `camera_configure(...)`, `camera_capture(target, name)` | Configure FOV / resolution / focal length / aperture / focusing distance, then capture a full-resolution image into on-board storage. |
| Telemetry | `telemetry_configure(frequency, key)` | Update RF link frequency (MHz) and Caesar key (0–255) on the spacecraft and the ground network together. |
| Thruster | `thruster_fire(target, duration)`, `thruster_stop(target)` | Fire / stop a named thruster for a delta-V manoeuvre. |
| Rendezvous | `rendezvous_start(target_id, dx, dy, dz)`, `rendezvous_stop(target_id)` | Hold an LVLH offset (m) from another spacecraft. Requires `enable_rpo: true`. |
| Docking | `docking_dock(target_id, component)`, `docking_undock(target_id, component)` | Physically dock / undock with a named component on another spacecraft. |
| Reset | `component_reset(target)` | Reboot a single component (or the whole bus, if you reset `Computer`). |

> All helpers accept the same `target` argument as the underlying commands — the **component name** (as configured in your scenario JSON), not a class alias. `alignment` defaults to `+z` for guidance helpers.

---

## 📚 Documentation

Full user documentation lives in [`docs/`](docs/README.md). Quick index:

| What you want | Where to look |
|---|---|
| Spacecraft uplink commands (wire format, every arg, ranges, units) | [API Reference → Spacecraft commands](docs/api-reference/spacecraft-commands.md) |
| Ground controller request/response API | [API Reference → Ground requests](docs/api-reference/ground-requests.md) |
| Admin API (telemetry, events, simulation control) | [API Reference → Admin requests](docs/api-reference/admin-requests.md) |
| Session clock message format | [API Reference → Session stream](docs/api-reference/session-stream.md) |
| MQTT topic map and encryption | [API Reference → MQTT topics](docs/api-reference/mqtt-topics.md) |
| **Authoring a brand-new scenario JSON** (teams, assets, events, questions) | [Scenarios → README](docs/scenarios/README.md) |
| Tour of an existing scenario JSON file | [Guides → Scenario configuration](docs/guides/scenario-config.md) |
| CCSDS / XTCE packet binary layouts | [Reference → Packet formats](docs/reference/packet-formats.md) |
| Units, ranges, and JSON conventions | [Reference → Data types](docs/reference/data-types.md) |
