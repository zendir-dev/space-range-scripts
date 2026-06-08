# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Brute-force connection stress test for Space Range.

This script opens many concurrent MQTT connections, each impersonating a
random team, and publishes a random valid spacecraft command on every
connection once per second. The goal is to put the Studio MQTT plumbing
and per-team controllers under sustained load so instability and resource
leaks are surfaced.

Flow
----
1. Prompt the operator for the **game name**, **admin password**, and
   **number of connections** to open.
2. Use the admin password to query the ``Admin/Request`` topic for the
   full team list (``admin_list_entities``) followed by each team's
   detailed asset/component list (``admin_list_team``). This builds an
   in-memory catalogue of teams together with their per-asset component
   names that random commands will target.
3. Open *N* MQTT clients. Each is assigned a random team from the
   catalogue and uses that team's XOR password to encrypt its uplinks.
4. Every second, each connection publishes one random — but structurally
   valid — uplink command on
   ``Zendir/SpaceRange/<GAME>/<TEAM>/Uplink`` targeting a random asset
   from its team. Component-bound commands (``camera``, ``capture``,
   ``thrust``, ``reset``) only fire when the asset actually owns a
   compatible component.

Press Ctrl+C to stop. A short summary of total sent / failed publishes is
printed on exit.

Usage
-----
::

    python scripts/brute_force_test.py
"""

from __future__ import annotations

import json
import os
import random
import string
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Optional

import paho.mqtt.client as mqtt


# Make ``src.utils.decode_payload`` importable for robust JSON unwrapping
# of admin responses (Studio is known to emit double-encoded payloads).
_SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.utils import decode_payload  # noqa: E402


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULTS_FILENAME = ".space-range-defaults"
_DEFAULT_SERVER    = "mqtt.zendir.io"
_DEFAULT_PORT      = 1883
_DEFAULT_GAME      = "ZENDIR"

# Default length (seconds) of one publish cycle. Every connection publishes
# exactly once per cycle, with the publishes spread evenly across the window
# (so 30 connections over a 5 s cycle = one publish every ~166 ms globally).
_DEFAULT_CYCLE_SECONDS = 5.0

# How long to wait for the admin TCP handshake / each admin request.
_ADMIN_TIMEOUT = 10.0

# How long to wait for each brute-force client's TCP handshake.
_CONNECT_TIMEOUT = 10.0

# Max time to block on ``MQTTMessageInfo.wait_for_publish`` after each publish.
# Forces paho to flush its outbound buffer so we don't build a backlog.
_PUBLISH_FLUSH_TIMEOUT = 1.0

# Probability that any single publish step issues a chat_query (a ground
# request, see docs/api-reference/ground-requests.md) instead of a normal
# spacecraft uplink. Only checked when the team is not on chat cooldown.
_CHAT_QUERY_PROBABILITY = 0.10

# Minimum seconds between chat_query requests for any one team, enforced
# across all connections sharing that team. The chat assistant takes a few
# seconds to respond, so we keep this generous to avoid piling up requests.
_CHAT_QUERY_MIN_INTERVAL = 20.0

# Minimum seconds between ``reset`` commands for any one team, enforced
# across all connections sharing that team. A reset triggers a spacecraft
# reboot (~60 sim s, see docs/api-reference/spacecraft-commands.md#reset),
# so issuing too many in a row makes the test spend more time waiting on
# reboots than exercising the broker.
_RESET_MIN_INTERVAL = 120.0

# Pool of random prompts used for chat_query stress-testing. Short, generic
# questions that any team's AI assistant should be able to attempt.
_CHAT_PROMPTS: list[str] = [
    "How is the spacecraft performing right now?",
    "Why is the battery draining so fast?",
    "Summarise the last few telemetry packets.",
    "What is the current pointing mode?",
    "Are we in line of sight of the ground station?",
    "Is the camera ready to capture an image?",
    "Why is the downlink rate so low?",
    "Which components are currently active?",
    "Walk me through a normal pass.",
    "Should I rotate the encryption key now?",
    "What's the next event on the schedule?",
    "Any anomalies in the recent telemetry?",
]


# ---------------------------------------------------------------------------
# ANSI colour helpers
# ---------------------------------------------------------------------------

_ANSI_RESET = "\x1b[0m"


def _enable_windows_ansi() -> None:
    """Enable virtual-terminal processing so ANSI escapes render on Windows."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        # 0x0001 ENABLE_PROCESSED_OUTPUT | 0x0004 ENABLE_VIRTUAL_TERMINAL_PROCESSING
        for handle_id in (-11, -12):  # stdout, stderr
            handle = kernel32.GetStdHandle(handle_id)
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0001 | 0x0004)
    except Exception:
        # Fall back to the os.system trick which also flips the VT bit on
        # modern Windows terminals; harmless if it fails.
        try:
            os.system("")
        except Exception:
            pass


def _hex_to_ansi_fg(hex_color: str) -> str:
    """Convert a ``#RRGGBB`` (or ``RRGGBB``) string into a 24-bit ANSI prefix."""
    if not hex_color:
        return ""
    s = hex_color.lstrip("#").strip()
    if len(s) != 6:
        return ""
    try:
        r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    except ValueError:
        return ""
    return f"\x1b[38;2;{r};{g};{b}m"


# ---------------------------------------------------------------------------
# Encryption
# ---------------------------------------------------------------------------

def xor_crypt(data: bytes, password: str) -> bytes:
    """XOR-encrypt/decrypt *data* with a repeating *password* key."""
    if not password:
        return data
    key = password.encode("utf-8")
    out = bytearray(len(data))
    for i, b in enumerate(data):
        out[i] = b ^ key[i % len(key)]
    return bytes(out)


# ---------------------------------------------------------------------------
# Defaults file (shared with src.mqtt_client.prompt_credentials)
# ---------------------------------------------------------------------------

def _defaults_path() -> str:
    return os.path.join(_PROJECT_ROOT, _DEFAULTS_FILENAME)


def _load_defaults() -> dict:
    path = _defaults_path()
    if os.path.isfile(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


# ---------------------------------------------------------------------------
# Minimal admin client (used once at startup to enumerate teams + assets)
# ---------------------------------------------------------------------------

class _AdminClient:
    """
    Tiny blocking admin client used at startup to discover the team
    catalogue. Not feature-complete — only the two endpoints this script
    cares about.
    """

    def __init__(self, server: str, port: int, game: str, password: str):
        self._server   = server
        self._port     = port
        self._password = password

        self._req_topic  = f"Zendir/SpaceRange/{game}/Admin/Request"
        self._resp_topic = f"Zendir/SpaceRange/{game}/Admin/Response"

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                   client_id=f"bf-admin-{random.randint(0, 1 << 30)}")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        self._connected = threading.Event()
        self._pending: dict[int, dict] = {}
        self._lock = threading.Lock()

    def connect(self, timeout: float = _ADMIN_TIMEOUT) -> bool:
        try:
            self._client.connect(self._server, self._port, keepalive=60)
        except OSError as exc:
            print(f"[admin] connect error: {exc}")
            return False
        self._client.loop_start()
        return self._connected.wait(timeout)

    def disconnect(self) -> None:
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception:
            pass

    def list_entities(self, timeout: float = _ADMIN_TIMEOUT) -> Optional[dict]:
        return self._request("admin_list_entities", {}, timeout=timeout)

    def list_team(self, team_name: str, timeout: float = _ADMIN_TIMEOUT) -> Optional[dict]:
        return self._request("admin_list_team", {"team": team_name}, timeout=timeout)

    def _request(self, request_type: str, args: dict, timeout: float) -> Optional[dict]:
        req_id = random.randint(1, 2_147_483_647)
        packet: dict = {"type": request_type, "req_id": req_id}
        if args:
            packet["args"] = args

        event = threading.Event()
        with self._lock:
            self._pending[req_id] = {"event": event, "response": None}

        payload = xor_crypt(json.dumps(packet).encode("utf-8"), self._password)
        self._client.publish(self._req_topic, payload)

        arrived = event.wait(timeout=timeout)
        with self._lock:
            slot = self._pending.pop(req_id, {})

        if not arrived:
            print(f"[admin] no response for '{request_type}' after {timeout}s")
            return None

        response = slot.get("response")
        if response and not response.get("success", True):
            print(f"[admin] '{request_type}' failed: {response.get('error', 'unknown')}")
        return response

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc != 0:
            print(f"[admin] connection failed (rc={rc})")
            return
        client.subscribe(self._resp_topic)
        self._connected.set()

    def _on_message(self, client, userdata, msg):
        if msg.topic != self._resp_topic:
            return
        try:
            decrypted = xor_crypt(msg.payload, self._password)
            data = decode_payload(decrypted)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            print(f"[admin] failed to decode response: {exc}")
            return
        except Exception as exc:
            print(f"[admin] unexpected decode error: {exc}")
            return

        # Drop unsolicited admin_event_triggered pushes — we don't care here.
        if data.get("type") == "admin_event_triggered":
            return

        req_id = data.get("req_id", 0)
        with self._lock:
            slot = self._pending.get(req_id)
            if slot is not None:
                slot["response"] = data
                slot["event"].set()


# ---------------------------------------------------------------------------
# Catalogue dataclasses
# ---------------------------------------------------------------------------

@dataclass
class _Asset:
    asset_id: str
    name: str
    components: list[dict] = field(default_factory=list)

    def imagers(self) -> list[dict]:
        return [c for c in self.components if c.get("is_imager")]

    def thrusters(self) -> list[dict]:
        return [c for c in self.components
                if "thrust" in str(c.get("class", "")).lower()
                or "thrust" in str(c.get("name", "")).lower()]

    def has_jammer(self) -> bool:
        for c in self.components:
            cls  = str(c.get("class", "")).lower()
            name = str(c.get("name",  "")).lower()
            if "jammer" in cls or "jamming" in cls:
                return True
            if "jammer" in name or "jamming" in name:
                return True
        return False


@dataclass
class _Team:
    name: str
    id: int
    password: str
    color: str = "#FFFFFF"
    assets: list[_Asset] = field(default_factory=list)

    @property
    def ansi_prefix(self) -> str:
        return _hex_to_ansi_fg(self.color)


def _build_team_catalogue(admin: _AdminClient) -> list[_Team]:
    """Use the admin API to enumerate every team and its assets/components."""
    entities = admin.list_entities()
    if entities is None:
        return []

    raw_teams = entities.get("args", {}).get("teams", []) or []
    if not raw_teams:
        print("[admin] no teams returned by admin_list_entities")
        return []

    catalogue: list[_Team] = []
    for raw in raw_teams:
        name = raw.get("name")
        password = raw.get("password", "")
        team_id  = raw.get("id")
        if not name or team_id is None or not password:
            print(f"[admin] skipping team with missing fields: {raw}")
            continue

        detail = admin.list_team(name)
        if detail is None:
            continue

        space = detail.get("args", {}).get("assets", {}).get("space", []) or []
        assets = [
            _Asset(
                asset_id=a.get("asset_id", ""),
                name=a.get("name", ""),
                components=a.get("components", []) or [],
            )
            for a in space
            if a.get("asset_id")
        ]
        if not assets:
            print(f"[admin] team '{name}' has no space assets, skipping")
            continue

        color = str(raw.get("color", "#FFFFFF")) or "#FFFFFF"
        team = _Team(name=name, id=int(team_id), password=password,
                     color=color, assets=assets)
        catalogue.append(team)
        print(f"[admin] {team.ansi_prefix}{name}{_ANSI_RESET} "
              f"(id={team_id}, color={color}) "
              f"-> {len(assets)} asset(s), "
              f"{sum(len(a.components) for a in assets)} component(s)")

    return catalogue


# ---------------------------------------------------------------------------
# Random valid command generation
# ---------------------------------------------------------------------------

_GUIDANCE_MODES = ["sun", "nadir", "velocity", "inertial", "idle", "ground", "location"]
_AXES           = ["+x", "-x", "+y", "-y", "+z", "-z"]
_PLANETS        = ["earth", "moon", "mars", "sun"]


def _random_guidance_args(asset: _Asset) -> dict:
    mode = random.choice(_GUIDANCE_MODES)

    if mode == "idle":
        return {"pointing": "idle"}

    if mode == "inertial":
        return {
            "pointing":  "inertial",
            "pitch":     round(random.uniform(-90.0, 90.0), 2),
            "roll":      round(random.uniform(-180.0, 180.0), 2),
            "yaw":       round(random.uniform(-180.0, 180.0), 2),
            "alignment": random.choice(_AXES),
        }

    target = (random.choice(asset.components).get("name", "")
              if asset.components else "")
    args: dict = {
        "pointing":  mode,
        "target":    target,
        "alignment": random.choice(_AXES),
    }

    if mode == "nadir":
        args["planet"] = random.choice(_PLANETS)
    elif mode == "ground":
        # Picking a likely-real ground station — fallback "singapore" is the
        # default used elsewhere in the codebase. Studio silently keeps the
        # current target if the name is unknown, so this is safe.
        args["station"] = "singapore"
    elif mode == "location":
        args["planet"]    = random.choice(_PLANETS)
        args["latitude"]  = round(random.uniform(-90.0, 90.0), 4)
        args["longitude"] = round(random.uniform(-180.0, 180.0), 4)
        args["altitude"]  = round(random.uniform(0.0, 1_000.0), 2)

    return args


def _random_command_for_asset(asset: _Asset, *, allow_reset: bool = True) -> dict:
    """
    Return a structurally valid uplink envelope targeting *asset*.

    Pass ``allow_reset=False`` to exclude the ``reset`` command from the
    random pool — used by the caller when a team's reset cooldown is still
    in effect.
    """
    options: list[tuple[str, dict]] = [
        ("guidance",     _random_guidance_args(asset)),
        ("downlink",     {"downlink": random.choice([True, False]),
                          "ping":     random.choice([True, False])}),
        ("get_schedule", {}),
        ("get_configuration", {"scope": "power"}),
    ]

    if asset.has_jammer():
        options.append(("jammer", {
            "active":      random.choice([True, False]),
            "frequencies": [round(random.uniform(100.0, 1_000.0), 2)],
            "power":       round(random.uniform(0.0, 100.0), 2),
        }))

    if allow_reset and asset.components:
        target = random.choice(asset.components).get("name", "")
        if target:
            options.append(("reset", {"target": target}))

    imagers = asset.imagers()
    if imagers:
        camera_name = random.choice(imagers).get("name", "")
        options.append(("camera", {
            "target":        camera_name,
            "fov":           round(random.uniform(10.0, 90.0), 1),
            "resolution":    random.choice([128, 256, 512, 1024]),
            "monochromatic": random.choice([True, False]),
        }))
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        options.append(("capture", {"target": camera_name, "name": f"bf_{suffix}"}))

    thrusters = asset.thrusters()
    if thrusters:
        thr = random.choice(thrusters).get("name", "")
        options.append(("thrust", {
            "target":   thr,
            "active":   True,
            "duration": round(random.uniform(0.5, 5.0), 2),
        }))

    command, args = random.choice(options)
    return {
        "Asset":   asset.asset_id,
        "Command": command,
        "Time":    0,
        "Args":    args,
    }


# ---------------------------------------------------------------------------
# Per-team rate limiter (shared across connections impersonating the same team)
# ---------------------------------------------------------------------------

class _PerTeamRateLimiter:
    """
    Generic per-team cooldown gate.

    A single instance protects one rate-limited action (e.g. ``chat_query``
    or ``reset``) across all brute-force connections sharing a team. Call
    :meth:`try_acquire` when about to send the action; it returns ``True``
    and stamps the current time iff the team's cooldown has expired.
    """

    def __init__(self, min_interval: float):
        self._min_interval = min_interval
        self._last: dict[int, float] = {}
        self._lock = threading.Lock()

    def try_acquire(self, team_id: int) -> bool:
        """Return ``True`` and stamp 'now' iff the team's cooldown has expired."""
        now = time.monotonic()
        with self._lock:
            last = self._last.get(team_id, float("-inf"))
            if now - last < self._min_interval:
                return False
            self._last[team_id] = now
            return True


# ---------------------------------------------------------------------------
# Brute-force connection worker
# ---------------------------------------------------------------------------

class _Connection:
    """One MQTT client impersonating a random team."""

    _id_counter = 0
    _id_lock    = threading.Lock()

    def __init__(self, server: str, port: int, game: str, team: _Team,
                 chat_limiter:  Optional[_PerTeamRateLimiter] = None,
                 reset_limiter: Optional[_PerTeamRateLimiter] = None):
        with _Connection._id_lock:
            _Connection._id_counter += 1
            self.index = _Connection._id_counter

        self.team        = team
        self.sent_count  = 0
        self.error_count = 0

        self._chat_limiter  = chat_limiter
        self._reset_limiter = reset_limiter

        self._server        = server
        self._port          = port
        self._uplink_topic  = f"Zendir/SpaceRange/{game}/{team.id}/Uplink"
        self._request_topic = f"Zendir/SpaceRange/{game}/{team.id}/Request"

        client_id = (f"bf-{self.index:05d}-"
                     f"{int(time.time())}-"
                     f"{random.randint(1000, 9999)}")
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                   client_id=client_id, clean_session=True)
        self._client.on_connect    = self._on_connect
        self._client.on_disconnect = self._on_disconnect

        self._connected = threading.Event()
        self._alive     = False

    def connect(self, timeout: float = _CONNECT_TIMEOUT) -> bool:
        try:
            self._client.connect(self._server, self._port, keepalive=60)
        except (OSError, ValueError) as exc:
            print(f"[conn {self.index:05d}] connect error: {exc}")
            return False
        self._client.loop_start()
        if not self._connected.wait(timeout):
            print(f"[conn {self.index:05d}] connect timeout")
            return False
        self._alive = True
        return True

    def disconnect(self) -> None:
        self._alive = False
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception:
            pass

    def publish_random(self) -> Optional[dict]:
        """
        Send one random action and return a display-friendly envelope for the
        caller to log. Returns ``None`` if the client wasn't alive.

        With low probability, and only if the per-team chat rate limiter
        allows it, the action is a ground-side ``chat_query`` request
        published on ``…/Request`` instead of a spacecraft uplink command on
        ``…/Uplink``. See ``docs/api-reference/ground-requests.md`` for the
        chat request envelope.
        """
        if not self._alive:
            return None

        if (self._chat_limiter is not None
                and random.random() < _CHAT_QUERY_PROBABILITY
                and self._chat_limiter.try_acquire(self.team.id)):
            return self._publish_chat_query()
        return self._publish_command()

    # ---- publish helpers ----

    def _publish_command(self) -> dict:
        asset = random.choice(self.team.assets)
        cmd   = _random_command_for_asset(asset)

        # Gate ``reset`` behind a per-team cooldown — see _RESET_MIN_INTERVAL.
        # If the random draw landed on reset but the team is still cooling
        # down, re-roll without reset in the pool so we still send something.
        if (cmd.get("Command") == "reset"
                and self._reset_limiter is not None
                and not self._reset_limiter.try_acquire(self.team.id)):
            cmd = _random_command_for_asset(asset, allow_reset=False)

        payload = xor_crypt(json.dumps(cmd).encode("utf-8"), self.team.password)
        info    = self._client.publish(self._uplink_topic, payload)
        return self._track_publish(info, cmd)

    def _publish_chat_query(self) -> dict:
        asset  = random.choice(self.team.assets)
        prompt = random.choice(_CHAT_PROMPTS)
        request = {
            "type":   "chat_query",
            "req_id": random.randint(1, 2_147_483_647),
            "args": {
                "asset_id": asset.asset_id,
                "prompt":   prompt,
                "messages": [],
            },
        }
        payload = xor_crypt(json.dumps(request).encode("utf-8"), self.team.password)
        info    = self._client.publish(self._request_topic, payload)
        # Synthesise an "uplink envelope shape" purely for log formatting.
        display = {
            "Asset":   asset.asset_id,
            "Command": "chat_query",
            "Args":    {"prompt": prompt},
        }
        return self._track_publish(info, display)

    def _track_publish(self, info, display_cmd: dict) -> dict:
        """
        Common post-publish bookkeeping: increment counters and block briefly
        on ``wait_for_publish`` so paho's outbound buffer drains.

        With QoS 0 this returns as soon as the bytes are on the socket, so
        normal load sees no extra latency — but it bounds the worst case so
        the queue can never balloon unchecked if the broker stalls.
        """
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            self.error_count += 1
            return display_cmd

        self.sent_count += 1
        try:
            info.wait_for_publish(timeout=_PUBLISH_FLUSH_TIMEOUT)
        except (RuntimeError, ValueError):
            # RuntimeError: client disconnected before publish completed.
            # ValueError:   QoS 0 message already removed from the queue.
            pass
        return display_cmd

    # ---- callbacks ----

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self._connected.set()
        else:
            print(f"[conn {self.index:05d}] connect rc={rc}")

    def _on_disconnect(self, client, userdata, *args, **kwargs):
        # paho calls _on_disconnect on both clean and unexpected closes; only
        # warn for the latter so a successful shutdown stays quiet.
        if self._alive:
            print(f"[conn {self.index:05d}] disconnected unexpectedly")
        self._alive = False


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

def _prompt(label: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default not in (None, "") else ""
    while True:
        try:
            value = input(f"{label}{suffix}: ").strip()
        except (EOFError, KeyboardInterrupt):
            raise
        if value:
            return value
        if default not in (None, ""):
            return default  # type: ignore[return-value]
        print("  value required")


def _prompt_positive_int(label: str, default: int) -> int:
    while True:
        raw = _prompt(label, str(default))
        try:
            n = int(raw)
        except ValueError:
            print("  please enter a whole number")
            continue
        if n <= 0:
            print("  please enter a positive integer")
            continue
        return n


def _prompt_positive_float(label: str, default: float) -> float:
    while True:
        raw = _prompt(label, f"{default:g}")
        try:
            v = float(raw)
        except ValueError:
            print("  please enter a number")
            continue
        if v <= 0:
            print("  please enter a positive number")
            continue
        return v


def _prompt_yes_no(label: str, default: bool = True) -> bool:
    default_str = "Y/n" if default else "y/N"
    while True:
        try:
            raw = input(f"{label} [{default_str}]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            raise
        if not raw:
            return default
        if raw in ("y", "yes", "true", "1"):
            return True
        if raw in ("n", "no", "false", "0"):
            return False
        print("  please answer yes or no")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _format_args(args: dict) -> str:
    """Compact ``key=value`` rendering of a command's Args, for log output."""
    if not args:
        return ""
    parts = []
    for k, v in args.items():
        if isinstance(v, float):
            text = f"{v:g}"
        else:
            text = str(v)
        if len(text) > 24:
            text = text[:21] + "..."
        parts.append(f"{k}={text}")
    return " ".join(parts)


def main() -> int:
    _enable_windows_ansi()

    print("Space Range — brute-force connection stress test")
    print("=" * 60)

    defaults = _load_defaults()
    try:
        game           = _prompt("Game name",      defaults.get("game", _DEFAULT_GAME))
        admin_password = _prompt("Admin password", defaults.get("admin_password", ""))
        n_connections  = _prompt_positive_int("Number of connections", 10)
        cycle_seconds  = _prompt_positive_float(
            "Cycle interval (seconds, every connection sends once per cycle)",
            _DEFAULT_CYCLE_SECONDS,
        )
        enable_chat = _prompt_yes_no(
            "Include random chat_query requests?",
            default=True,
        )
    except (EOFError, KeyboardInterrupt):
        print()
        return 130

    server = _DEFAULT_SERVER
    port   = _DEFAULT_PORT

    print()
    print(f"Broker: {server}:{port}")
    print(f"Game:   {game}")
    print()

    # ---- 1. Enumerate teams via admin --------------------------------
    print(f"[admin] connecting to {server}:{port} ...")
    admin = _AdminClient(server, port, game, admin_password)
    if not admin.connect():
        print("[admin] connect failed — aborting")
        return 1

    print("[admin] fetching team catalogue ...")
    catalogue = _build_team_catalogue(admin)
    admin.disconnect()

    if not catalogue:
        print("No teams discovered — check the game name and admin password.")
        return 1
    print(f"[admin] catalogue ready: {len(catalogue)} team(s)")
    print()

    # ---- 2. Open N connections in parallel ---------------------------
    # Round-robin assignment: with N connections and T teams, each team gets
    # floor(N/T) connections and the first (N mod T) teams get one extra. So
    # for N=10 / T=8: teams 0–1 get 2 connections each, teams 2–7 get 1.
    print(f"Opening {n_connections} brute-force connection(s) "
          f"across {len(catalogue)} team(s) (round-robin) ...")
    chat_limiter  = (_PerTeamRateLimiter(_CHAT_QUERY_MIN_INTERVAL)
                     if enable_chat else None)
    reset_limiter = _PerTeamRateLimiter(_RESET_MIN_INTERVAL)
    pending = [
        _Connection(server, port, game,
                    catalogue[i % len(catalogue)],
                    chat_limiter=chat_limiter,
                    reset_limiter=reset_limiter)
        for i in range(n_connections)
    ]

    connections: list[_Connection] = []
    # Cap the connect concurrency so we don't try to open thousands of TCP
    # sockets in one go; paho's per-client loop_start() runs independently
    # afterwards regardless.
    max_workers = min(32, max(4, n_connections))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for ok, conn in zip(pool.map(_Connection.connect, pending), pending):
            if ok:
                connections.append(conn)

    if not connections:
        print("No connections established — aborting")
        return 1

    print(f"Connected: {len(connections)}/{n_connections}")
    by_team: dict[str, tuple[int, _Team]] = {}
    for c in connections:
        count, _ = by_team.get(c.team.name, (0, c.team))
        by_team[c.team.name] = (count + 1, c.team)
    name_width = max((len(t.name) for _, t in by_team.values()), default=10)
    for name, (count, team) in sorted(by_team.items(), key=lambda kv: -kv[1][0]):
        print(f"   {team.ansi_prefix}{name:>{name_width}s}{_ANSI_RESET} : {count}")
    print()

    # ---- 3. Per-cycle staggered publishes ----------------------------
    # Spread one publish per connection evenly across the cycle window so the
    # broker sees a steady stream rather than a once-per-cycle burst.
    per_msg_delay = cycle_seconds / len(connections)
    print(f"Cycle: {cycle_seconds:g}s across {len(connections)} connection(s) "
          f"-> one publish every {per_msg_delay*1000:.1f} ms.")
    if enable_chat:
        print(f"chat_query: {int(_CHAT_QUERY_PROBABILITY*100)}% probability per publish, "
              f"max 1 / {_CHAT_QUERY_MIN_INTERVAL:g}s per team.")
    else:
        print("chat_query: disabled.")
    print(f"reset:      gated to max 1 / {_RESET_MIN_INTERVAL:g}s per team.")
    print("Ctrl+C to stop.")
    print()

    # Pre-compute display width for team name column in log lines.
    team_name_width = max((len(c.team.name) for c in connections), default=10)

    cycle      = 0
    next_send  = time.monotonic()
    try:
        while True:
            cycle += 1
            cycle_start = time.monotonic()

            # Shuffle a fresh copy each cycle so within a single window the
            # broker sees an interleaved stream of teams rather than the same
            # team order over and over.
            order = connections[:]
            random.shuffle(order)

            for conn in order:
                now = time.monotonic()
                if next_send > now:
                    time.sleep(next_send - now)
                next_send += per_msg_delay

                try:
                    cmd = conn.publish_random()
                except Exception as exc:
                    conn.error_count += 1
                    print(f"[conn {conn.index:05d}] publish raised: {exc}")
                    continue
                if cmd is None:
                    continue

                team   = conn.team
                prefix = team.ansi_prefix
                name   = f"{team.name:<{team_name_width}s}"
                asset  = cmd.get("Asset", "")
                action = cmd.get("Command", "")
                args   = _format_args(cmd.get("Args", {}))
                print(f"  {prefix}[{name}]{_ANSI_RESET} "
                      f"conn {conn.index:05d} | "
                      f"asset={asset} cmd={action:<13s} {args}")

            total_sent   = sum(c.sent_count   for c in connections)
            total_errors = sum(c.error_count for c in connections)
            elapsed = time.monotonic() - cycle_start
            print(f"  -- cycle {cycle:5d} | sent={total_sent:>8d} | "
                  f"errors={total_errors:>6d} | took={elapsed:6.2f}s "
                  f"(target {cycle_seconds:g}s)")

            # If the cycle ran slow (publishes/flush stalled), reset the
            # schedule so we don't try to play catch-up by spamming.
            if next_send < time.monotonic():
                next_send = time.monotonic()
    except KeyboardInterrupt:
        print()
        print("Stopping brute-force test ...")

    # ---- 4. Shutdown -------------------------------------------------
    for conn in connections:
        conn.disconnect()

    total_sent   = sum(c.sent_count   for c in connections)
    total_errors = sum(c.error_count for c in connections)
    print(f"Done. cycles={cycle} sent={total_sent} errors={total_errors}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
