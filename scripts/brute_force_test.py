# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Brute-force connection stress test for Space Range.

This script opens many concurrent MQTT connections, each impersonating a
random team, and publishes random-but-valid traffic on every connection once
per cycle. The goal is to put the Studio MQTT plumbing and per-team
controllers under sustained load so instability and resource leaks are
surfaced.

Three kinds of traffic can be mixed, each independently enabled with a 0..1
weight controlling how likely it is to fire on any given publish slot:

1. **Command**  - a random valid spacecraft uplink (guidance, downlink,
   camera, capture, thrust, reset, ...). Default: enabled.
2. **Chat**     - a ground-side ``chat_query`` request to the AI assistant.
   Default: disabled.
3. **Questions** - answers a random scenario question via ``submit_answer``:
   multiple-choice picks a random option, checkbox picks random option(s),
   short answer submits a random string, and number submits a value inside
   the range (0..10 when no range is known). Default: disabled.

On every publish slot each connection picks exactly one action, weighted by
the enabled actions' scalars. When all enabled actions share the same weight
they are equally likely to fire; otherwise the weights are normalised so a
higher weight fires proportionally more often.

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
from typing import Callable, Optional

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

# How long to wait for each team's ``list_questions`` response at startup.
_QUESTIONS_FETCH_TIMEOUT = 5.0

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

# When a number question exposes no range, submit a value in this band.
_DEFAULT_NUMBER_RANGE = (0.0, 10.0)

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

# Pool of random words used to fill short-answer (text) question submissions.
_ANSWER_WORDS: list[str] = [
    "recon", "nadir", "apogee", "vector", "orbit", "beacon", "signal",
    "delta", "sigma", "photon", "quasar", "vertex", "cipher", "matrix",
]

# Colours used for GUI/CLI log emphasis (hex so both renderers agree).
_COLOR_ERROR   = "#ff5555"
_COLOR_INFO    = "#8be9fd"
_COLOR_SUCCESS = "#50fa7b"


# ---------------------------------------------------------------------------
# ANSI colour helpers (CLI logging)
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


def _cli_log(message: str, color: str = "") -> None:
    """Default log sink for the CLI: colourised print via ANSI escapes."""
    prefix = _hex_to_ansi_fg(color) if color else ""
    if prefix:
        print(f"{prefix}{message}{_ANSI_RESET}")
    else:
        print(message)


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
# Run configuration
# ---------------------------------------------------------------------------

@dataclass
class RunConfig:
    """All knobs for a single brute-force run, shared by the CLI and GUI."""

    server: str = _DEFAULT_SERVER
    port: int = _DEFAULT_PORT
    game: str = _DEFAULT_GAME
    admin_password: str = ""
    n_connections: int = 10
    cycle_seconds: float = _DEFAULT_CYCLE_SECONDS

    enable_command: bool = True
    enable_chat: bool = False
    enable_questions: bool = False

    weight_command: float = 1.0
    weight_chat: float = 1.0
    weight_questions: float = 1.0


# ---------------------------------------------------------------------------
# Minimal admin client (used once at startup to enumerate teams + assets)
# ---------------------------------------------------------------------------

class _AdminClient:
    """
    Tiny blocking admin client used at startup to discover the team
    catalogue. Not feature-complete - only the two endpoints this script
    cares about.
    """

    def __init__(self, server: str, port: int, game: str, password: str,
                 log: Optional[Callable[..., None]] = None):
        self._server   = server
        self._port     = port
        self._password = password
        self._log      = log or _cli_log

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
            self._log(f"[admin] connect error: {exc}", _COLOR_ERROR)
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
            self._log(f"[admin] no response for '{request_type}' after {timeout}s",
                      _COLOR_ERROR)
            return None

        response = slot.get("response")
        if response and not response.get("success", True):
            self._log(f"[admin] '{request_type}' failed: "
                      f"{response.get('error', 'unknown')}", _COLOR_ERROR)
        return response

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc != 0:
            self._log(f"[admin] connection failed (rc={rc})", _COLOR_ERROR)
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
            self._log(f"[admin] failed to decode response: {exc}", _COLOR_ERROR)
            return
        except Exception as exc:
            self._log(f"[admin] unexpected decode error: {exc}", _COLOR_ERROR)
            return

        # Drop unsolicited admin_event_triggered pushes - we don't care here.
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


def _build_team_catalogue(admin: _AdminClient,
                          log: Callable[..., None]) -> list[_Team]:
    """Use the admin API to enumerate every team and its assets/components."""
    entities = admin.list_entities()
    if entities is None:
        return []

    raw_teams = entities.get("args", {}).get("teams", []) or []
    if not raw_teams:
        log("[admin] no teams returned by admin_list_entities", _COLOR_ERROR)
        return []

    catalogue: list[_Team] = []
    for raw in raw_teams:
        name = raw.get("name")
        password = raw.get("password", "")
        team_id  = raw.get("id")
        if not name or team_id is None or not password:
            log(f"[admin] skipping team with missing fields: {raw}", _COLOR_ERROR)
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
            log(f"[admin] team '{name}' has no space assets, skipping", _COLOR_ERROR)
            continue

        color = str(raw.get("color", "#FFFFFF")) or "#FFFFFF"
        team = _Team(name=name, id=int(team_id), password=password,
                     color=color, assets=assets)
        catalogue.append(team)
        log(f"[admin] {name} (id={team_id}, color={color}) "
            f"-> {len(assets)} asset(s), "
            f"{sum(len(a.components) for a in assets)} component(s)", color)

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
        # Picking a likely-real ground station - fallback "singapore" is the
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
    random pool - used by the caller when a team's reset cooldown is still
    in effect.
    """
    options: list[tuple[str, dict]] = [
        ("guidance",     _random_guidance_args(asset)),
        ("downlink",     {"downlink": random.choice([True, False]),
                          "ping":     random.choice([True, False])}),
        ("get_schedule", {}),
        ("get_configuration", {"scope": "power_bus"}),
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
            "fov":           round(random.uniform(10.0, 60.0), 1),
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
# Random question answers
# ---------------------------------------------------------------------------

def _random_answer_for_question(question: dict):
    """
    Build a structurally valid random ``submit_answer`` value for *question*.

    * ``number``   - a value inside the exposed range, or 0..10 when unknown.
    * ``select``   - a random zero-based option index.
    * ``checkbox`` - a random non-empty subset of option indices.
    * ``text``     - a random short string.
    """
    qtype = str(question.get("type", "")).lower()

    if qtype == "number":
        lo, hi = question.get("min"), question.get("max")
        if lo is None or hi is None:
            lo, hi = _DEFAULT_NUMBER_RANGE
        return round(random.uniform(float(lo), float(hi)), 2)

    if qtype == "select":
        options = question.get("options") or []
        return random.randrange(len(options)) if options else 0

    if qtype == "checkbox":
        options = question.get("options") or []
        if not options:
            return []
        count = random.randint(1, len(options))
        return sorted(random.sample(range(len(options)), count))

    # text (and any unknown type): submit something arbitrary.
    return f"{random.choice(_ANSWER_WORDS)}{random.randint(0, 99)}"


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
# Per-team scenario question store (shared across a team's connections)
# ---------------------------------------------------------------------------

class _TeamQuestions:
    """
    Thread-safe cache of one team's scenario questions.

    Populated from a ``list_questions`` response (any of the team's
    connections may deliver it). Questions are claimed with
    :meth:`claim_unanswered`, which atomically marks a question as taken so
    two connections never submit the same one.
    """

    def __init__(self):
        self._questions: list[dict] = []
        self._claimed: set[int] = set()
        self._lock = threading.Lock()
        self.loaded = threading.Event()

    def set_questions(self, questions: list[dict]) -> None:
        with self._lock:
            self._questions = questions
        self.loaded.set()

    def mark_answered(self, question_id: int) -> None:
        with self._lock:
            self._claimed.add(question_id)

    def has_unanswered(self) -> bool:
        with self._lock:
            return any(q["id"] not in self._claimed for q in self._questions)

    def count(self) -> int:
        with self._lock:
            return len(self._questions)

    def claim_unanswered(self) -> Optional[dict]:
        """Atomically claim and return a random unanswered question, or None."""
        with self._lock:
            pool = [q for q in self._questions if q["id"] not in self._claimed]
            if not pool:
                return None
            chosen = random.choice(pool)
            self._claimed.add(chosen["id"])
            return chosen


# ---------------------------------------------------------------------------
# Brute-force connection worker
# ---------------------------------------------------------------------------

class _Connection:
    """One MQTT client impersonating a random team."""

    _id_counter = 0
    _id_lock    = threading.Lock()

    def __init__(self, config: RunConfig, team: _Team,
                 chat_limiter:  Optional[_PerTeamRateLimiter] = None,
                 reset_limiter: Optional[_PerTeamRateLimiter] = None,
                 team_questions: Optional[_TeamQuestions] = None,
                 log: Optional[Callable[..., None]] = None):
        with _Connection._id_lock:
            _Connection._id_counter += 1
            self.index = _Connection._id_counter

        self.team        = team
        self.sent_count  = 0
        self.error_count = 0

        self._log            = log or _cli_log
        self._chat_limiter   = chat_limiter
        self._reset_limiter  = reset_limiter
        self._team_questions = team_questions

        self._enable_command   = config.enable_command
        self._enable_chat      = config.enable_chat and chat_limiter is not None
        self._enable_questions = config.enable_questions and team_questions is not None
        self._weight_command   = max(0.0, config.weight_command)
        self._weight_chat      = max(0.0, config.weight_chat)
        self._weight_questions = max(0.0, config.weight_questions)

        self._server         = config.server
        self._port           = config.port
        self._uplink_topic   = f"Zendir/SpaceRange/{config.game}/{team.id}/Uplink"
        self._request_topic  = f"Zendir/SpaceRange/{config.game}/{team.id}/Request"
        self._response_topic = f"Zendir/SpaceRange/{config.game}/{team.id}/Response"

        client_id = (f"bf-{self.index:05d}-"
                     f"{int(time.time())}-"
                     f"{random.randint(1000, 9999)}")
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                   client_id=client_id, clean_session=True)
        self._client.on_connect    = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        if self._enable_questions:
            self._client.on_message = self._on_message

        self._connected = threading.Event()
        self._alive     = False

    def connect(self, timeout: float = _CONNECT_TIMEOUT) -> bool:
        try:
            self._client.connect(self._server, self._port, keepalive=60)
        except (OSError, ValueError) as exc:
            self._log(f"[conn {self.index:05d}] connect error: {exc}", _COLOR_ERROR)
            return False
        self._client.loop_start()
        if not self._connected.wait(timeout):
            self._log(f"[conn {self.index:05d}] connect timeout", _COLOR_ERROR)
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

    def request_questions(self) -> None:
        """Ask the team's ground controller for its scenario question list."""
        request = {"type": "list_questions",
                   "req_id": random.randint(1, 2_147_483_647)}
        payload = xor_crypt(json.dumps(request).encode("utf-8"), self.team.password)
        self._client.publish(self._request_topic, payload)

    def publish_random(self) -> Optional[dict]:
        """
        Pick one enabled action (weighted) and publish it. Returns a
        display-friendly envelope for the caller to log, or ``None`` if the
        client wasn't alive.
        """
        if not self._alive:
            return None

        action = self._pick_action()

        if action == "chat":
            if self._chat_limiter is None or not self._chat_limiter.try_acquire(self.team.id):
                action = "command"  # on cooldown: fall back rather than skip
        elif action == "questions":
            question = (self._team_questions.claim_unanswered()
                        if self._team_questions is not None else None)
            if question is None:
                action = "command"  # nothing left to answer: fall back
            else:
                return self._publish_question(question)

        if action == "chat":
            return self._publish_chat_query()
        return self._publish_command()

    def _pick_action(self) -> str:
        """Weighted choice among the currently available enabled actions."""
        choices: list[str] = []
        weights: list[float] = []

        if self._enable_command and self._weight_command > 0:
            choices.append("command")
            weights.append(self._weight_command)
        if self._enable_chat and self._weight_chat > 0:
            choices.append("chat")
            weights.append(self._weight_chat)
        if (self._enable_questions and self._weight_questions > 0
                and self._team_questions is not None
                and self._team_questions.has_unanswered()):
            choices.append("questions")
            weights.append(self._weight_questions)

        if not choices:
            return "command"
        return random.choices(choices, weights=weights, k=1)[0]

    # ---- publish helpers ----

    def _publish_command(self) -> dict:
        asset = random.choice(self.team.assets)
        cmd   = _random_command_for_asset(asset)

        # Gate ``reset`` behind a per-team cooldown - see _RESET_MIN_INTERVAL.
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

    def _publish_question(self, question: dict) -> dict:
        value = _random_answer_for_question(question)
        request = {
            "type":   "submit_answer",
            "req_id": random.randint(1, 2_147_483_647),
            "args":   {"submissions": [{"id": question["id"], "value": value}]},
        }
        payload = xor_crypt(json.dumps(request).encode("utf-8"), self.team.password)
        info    = self._client.publish(self._request_topic, payload)
        display = {
            "Asset":   "-",
            "Command": "submit_answer",
            "Args":    {"id": question["id"],
                        "type": question.get("type", ""),
                        "value": value},
        }
        return self._track_publish(info, display)

    def _track_publish(self, info, display_cmd: dict) -> dict:
        """
        Common post-publish bookkeeping: increment counters and block briefly
        on ``wait_for_publish`` so paho's outbound buffer drains.

        With QoS 0 this returns as soon as the bytes are on the socket, so
        normal load sees no extra latency - but it bounds the worst case so
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
            if self._enable_questions:
                client.subscribe(self._response_topic)
            self._connected.set()
        else:
            self._log(f"[conn {self.index:05d}] connect rc={rc}", _COLOR_ERROR)

    def _on_disconnect(self, client, userdata, *args, **kwargs):
        # paho calls _on_disconnect on both clean and unexpected closes; only
        # warn for the latter so a successful shutdown stays quiet.
        if self._alive:
            self._log(f"[conn {self.index:05d}] disconnected unexpectedly",
                      _COLOR_ERROR)
        self._alive = False

    def _on_message(self, client, userdata, msg):
        """Populate the shared question store from ``list_questions`` responses."""
        if self._team_questions is None:
            return
        try:
            data = decode_payload(xor_crypt(msg.payload, self.team.password))
        except Exception:
            return
        if not isinstance(data, dict) or data.get("type") != "list_questions":
            return

        raw = data.get("args", {}).get("questions", []) or []
        parsed: list[dict] = []
        for q in raw:
            qid = q.get("id")
            if qid is None:
                continue
            answer = q.get("answer", {}) or {}
            entry = {
                "id":      qid,
                "type":    str(q.get("type", "")).lower(),
                "title":   q.get("title", ""),
                "options": answer.get("options", []) or [],
                "min":     answer.get("min"),
                "max":     answer.get("max"),
            }
            parsed.append(entry)
            # Already-submitted questions are locked; don't re-target them.
            if q.get("submitted") is not None or q.get("submission") is not None:
                self._team_questions.mark_answered(qid)

        self._team_questions.set_questions(parsed)


# ---------------------------------------------------------------------------
# Brute-force engine (shared by CLI + GUI)
# ---------------------------------------------------------------------------

class BruteForceEngine:
    """
    Runs the full brute-force flow for a :class:`RunConfig`.

    ``log(message, color="")`` receives every human-readable line. Call
    :meth:`stop` from any thread to end the run; :meth:`run` blocks until the
    stop flag is set or setup fails.
    """

    def __init__(self, config: RunConfig,
                 log: Optional[Callable[..., None]] = None):
        self.config    = config
        self._log      = log or _cli_log
        self._stop     = threading.Event()
        self.connections: list[_Connection] = []
        self.cycle = 0

    def stop(self) -> None:
        self._stop.set()

    # ---- helpers ----

    def _sleep_until(self, deadline: float) -> None:
        """Sleep in small chunks so :meth:`stop` stays responsive."""
        while not self._stop.is_set():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            time.sleep(min(remaining, 0.2))

    def _fetch_questions(self, connections: list[_Connection],
                         team_questions: dict[int, _TeamQuestions]) -> None:
        self._log("Fetching scenario questions per team ...", _COLOR_INFO)
        requested: set[int] = set()
        for conn in connections:
            if conn.team.id not in requested:
                requested.add(conn.team.id)
                conn.request_questions()

        deadline = time.monotonic() + _QUESTIONS_FETCH_TIMEOUT
        for store in team_questions.values():
            remaining = deadline - time.monotonic()
            if remaining > 0:
                store.loaded.wait(remaining)

        for conn_team_id, store in team_questions.items():
            count = store.count()
            if count:
                self._log(f"   team {conn_team_id}: {count} question(s) loaded",
                          _COLOR_SUCCESS)
            else:
                self._log(f"   team {conn_team_id}: no questions (or none returned)",
                          _COLOR_ERROR)

    # ---- main entry ----

    def run(self) -> None:
        cfg = self.config
        log = self._log

        log(f"Broker: {cfg.server}:{cfg.port}   Game: {cfg.game}", _COLOR_INFO)
        active = [name for name, on in (("command", cfg.enable_command),
                                        ("chat", cfg.enable_chat),
                                        ("questions", cfg.enable_questions)) if on]
        log(f"Actions: {', '.join(active) if active else '(none)'} "
            f"[weights c={cfg.weight_command:g} chat={cfg.weight_chat:g} "
            f"q={cfg.weight_questions:g}]", _COLOR_INFO)

        # ---- 1. Enumerate teams via admin ----
        log(f"[admin] connecting to {cfg.server}:{cfg.port} ...")
        admin = _AdminClient(cfg.server, cfg.port, cfg.game, cfg.admin_password, log=log)
        if not admin.connect():
            log("[admin] connect failed - aborting", _COLOR_ERROR)
            return

        log("[admin] fetching team catalogue ...")
        catalogue = _build_team_catalogue(admin, log)
        admin.disconnect()

        if not catalogue:
            log("No teams discovered - check the game name and admin password.",
                _COLOR_ERROR)
            return
        log(f"[admin] catalogue ready: {len(catalogue)} team(s)", _COLOR_SUCCESS)

        # ---- 2. Shared per-team limiters + question stores ----
        chat_limiter  = (_PerTeamRateLimiter(_CHAT_QUERY_MIN_INTERVAL)
                         if cfg.enable_chat else None)
        reset_limiter = _PerTeamRateLimiter(_RESET_MIN_INTERVAL)
        team_questions: dict[int, _TeamQuestions] = {}
        if cfg.enable_questions:
            for team in catalogue:
                team_questions[team.id] = _TeamQuestions()

        # ---- 3. Open N connections in parallel (round-robin over teams) ----
        log(f"Opening {cfg.n_connections} connection(s) across "
            f"{len(catalogue)} team(s) (round-robin) ...")
        pending = [
            _Connection(cfg,
                        catalogue[i % len(catalogue)],
                        chat_limiter=chat_limiter,
                        reset_limiter=reset_limiter,
                        team_questions=team_questions.get(catalogue[i % len(catalogue)].id),
                        log=log)
            for i in range(cfg.n_connections)
        ]

        connections: list[_Connection] = []
        max_workers = min(32, max(4, cfg.n_connections))
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            for ok, conn in zip(pool.map(_Connection.connect, pending), pending):
                if ok:
                    connections.append(conn)

        if not connections:
            log("No connections established - aborting", _COLOR_ERROR)
            return
        self.connections = connections
        log(f"Connected: {len(connections)}/{cfg.n_connections}", _COLOR_SUCCESS)

        by_team: dict[str, tuple[int, _Team]] = {}
        for c in connections:
            count, _ = by_team.get(c.team.name, (0, c.team))
            by_team[c.team.name] = (count + 1, c.team)
        for name, (count, team) in sorted(by_team.items(), key=lambda kv: -kv[1][0]):
            log(f"   {name}: {count}", team.color)

        # ---- 4. Fetch scenario questions (if enabled) ----
        if cfg.enable_questions and team_questions:
            self._fetch_questions(connections, team_questions)

        # ---- 5. Per-cycle staggered publishes ----
        per_msg_delay = cfg.cycle_seconds / len(connections)
        log(f"Cycle: {cfg.cycle_seconds:g}s across {len(connections)} connection(s) "
            f"-> one publish every {per_msg_delay*1000:.1f} ms.", _COLOR_INFO)
        if cfg.enable_chat:
            log(f"chat_query: gated to max 1 / {_CHAT_QUERY_MIN_INTERVAL:g}s per team.")
        log(f"reset:      gated to max 1 / {_RESET_MIN_INTERVAL:g}s per team.")

        team_name_width = max((len(c.team.name) for c in connections), default=10)

        self.cycle = 0
        next_send  = time.monotonic()
        while not self._stop.is_set():
            self.cycle += 1
            cycle_start = time.monotonic()

            order = connections[:]
            random.shuffle(order)

            for conn in order:
                if self._stop.is_set():
                    break
                if next_send > time.monotonic():
                    self._sleep_until(next_send)
                next_send += per_msg_delay

                try:
                    cmd = conn.publish_random()
                except Exception as exc:
                    conn.error_count += 1
                    log(f"[conn {conn.index:05d}] publish raised: {exc}", _COLOR_ERROR)
                    continue
                if cmd is None:
                    continue

                name   = f"{conn.team.name:<{team_name_width}s}"
                asset  = cmd.get("Asset", "")
                action = cmd.get("Command", "")
                args   = _format_args(cmd.get("Args", {}))
                log(f"  [{name}] conn {conn.index:05d} | "
                    f"asset={asset} cmd={action:<13s} {args}", conn.team.color)

            total_sent   = sum(c.sent_count   for c in connections)
            total_errors = sum(c.error_count for c in connections)
            elapsed = time.monotonic() - cycle_start
            log(f"  -- cycle {self.cycle:5d} | sent={total_sent:>8d} | "
                f"errors={total_errors:>6d} | took={elapsed:6.2f}s "
                f"(target {cfg.cycle_seconds:g}s)", _COLOR_INFO)

            # If the cycle ran slow, reset the schedule so we don't try to
            # play catch-up by spamming.
            if next_send < time.monotonic():
                next_send = time.monotonic()

        # ---- 6. Shutdown ----
        log("Stopping brute-force test ...", _COLOR_INFO)
        for conn in connections:
            conn.disconnect()
        total_sent   = sum(c.sent_count   for c in connections)
        total_errors = sum(c.error_count for c in connections)
        log(f"Done. cycles={self.cycle} sent={total_sent} errors={total_errors}",
            _COLOR_SUCCESS)


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


# ---------------------------------------------------------------------------
# CLI prompts + entry
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


def _prompt_scalar(label: str, default: float) -> float:
    """Prompt for a 0..1 probability weight."""
    while True:
        raw = _prompt(label, f"{default:g}")
        try:
            v = float(raw)
        except ValueError:
            print("  please enter a number between 0 and 1")
            continue
        if not 0.0 <= v <= 1.0:
            print("  please enter a value between 0 and 1")
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


def main() -> int:
    """Terminal (prompt-driven) entry point."""
    _enable_windows_ansi()

    print("Space Range - brute-force connection stress test")
    print("=" * 60)

    defaults = _load_defaults()
    cfg = RunConfig(
        server=str(defaults.get("server", _DEFAULT_SERVER)),
        port=int(defaults.get("port", _DEFAULT_PORT)),
    )
    try:
        cfg.game           = _prompt("Game name",      defaults.get("game", _DEFAULT_GAME))
        cfg.admin_password = _prompt("Admin password", defaults.get("admin_password", ""))
        cfg.n_connections  = _prompt_positive_int("Number of connections", 10)
        cfg.cycle_seconds  = _prompt_positive_float(
            "Cycle interval (seconds, every connection sends once per cycle)",
            _DEFAULT_CYCLE_SECONDS,
        )

        print("\nActions (each fires with a 0..1 weight; equal weights = equally likely):")
        cfg.enable_command = _prompt_yes_no("  Include random commands?", default=True)
        if cfg.enable_command:
            cfg.weight_command = _prompt_scalar("    command weight (0-1)", 1.0)
        cfg.enable_chat = _prompt_yes_no("  Include random chat_query requests?", default=False)
        if cfg.enable_chat:
            cfg.weight_chat = _prompt_scalar("    chat weight (0-1)", 1.0)
        cfg.enable_questions = _prompt_yes_no("  Include random question answers?", default=False)
        if cfg.enable_questions:
            cfg.weight_questions = _prompt_scalar("    questions weight (0-1)", 1.0)
    except (EOFError, KeyboardInterrupt):
        print()
        return 130

    if not (cfg.enable_command or cfg.enable_chat or cfg.enable_questions):
        print("No actions enabled - nothing to do.")
        return 1

    print()
    print("Ctrl+C to stop.")
    print()

    engine = BruteForceEngine(cfg, log=_cli_log)

    # Run the engine on a worker thread so the main thread can catch Ctrl+C
    # and signal a clean stop.
    worker = threading.Thread(target=engine.run, name="brute-force-engine")
    worker.start()
    try:
        while worker.is_alive():
            worker.join(timeout=0.2)
    except KeyboardInterrupt:
        print()
        engine.stop()
        worker.join()
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(main())
