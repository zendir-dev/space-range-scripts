# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
MQTT client wrapper for Space Range scenarios.

Handles connecting to the broker, XOR encryption of uplink packets, and
routing of incoming session and ground response messages.

The :class:`SpaceRangeClient` inherits from :class:`~src.ground_client.GroundRequestClient`
and therefore exposes blocking ground request helpers such as
:meth:`list_assets`, :meth:`get_telemetry`, etc.

It also holds an :class:`~src.admin_client.AdminRequestClient` instance as
``client.admin``, providing access to all admin-level commands for
constructive agents and instructors.
"""

from __future__ import annotations

from typing import Callable, Optional

import datetime
import json
import os
import threading
import paho.mqtt.client as mqtt

from .config import ScenarioConfig, TeamConfig
from .event_scheduler import EventScheduler
from .ground_client import GroundRequestClient
from .admin_client import AdminRequestClient
from . import printer

_DEFAULT_GAME      = "ZENDIR"
_DEFAULT_SERVER    = "mqtt.zendir.io"
_DEFAULT_PORT      = 1883
_DEFAULTS_FILENAME = ".space-range-defaults"


# ---------------------------------------------------------------------------
# Encryption (module-level helper kept for backwards compatibility)
# ---------------------------------------------------------------------------

def xor_encrypt(data: bytes, password: str) -> bytes:
    """XOR-encrypt *data* with a repeating *password* key."""
    password_bytes = password.encode()
    encrypted = bytearray(len(data))
    for i in range(len(data)):
        encrypted[i] = data[i] ^ password_bytes[i % len(password_bytes)]
    return bytes(encrypted)


# ---------------------------------------------------------------------------
# SpaceRangeClient
# ---------------------------------------------------------------------------

class SpaceRangeClient(GroundRequestClient):
    """
    High-level MQTT client for a Space Range scenario.

    Inherits blocking ground request helpers from
    :class:`~src.ground_client.GroundRequestClient`:
    ``list_assets()``, ``list_entity()``, ``list_stations()``,
    ``get_telemetry()``, ``set_telemetry()``, ``transmit_bytes()``,
    ``chat_query()``, ``get_packet_schemas()``.

    Also exposes an :class:`~src.admin_client.AdminRequestClient` as
    ``self.admin`` for instructor/agent use, available once connected.

    Parameters
    ----------
    config:
        Scenario configuration loaded via :func:`~src.config.load_config`.
    team:
        The :class:`~src.config.TeamConfig` this client operates as.
    scheduler:
        The :class:`~src.event_scheduler.EventScheduler` to tick on every
        incoming session message.
    admin_password:
        The 6-character alphanumeric admin password for this game session.
        Required to use ``self.admin``.  Pass an empty string to disable
        admin functionality.
    on_session:
        Optional extra callback called with the raw parsed session dict on
        every incoming session message, *after* the scheduler has been ticked.
    on_event:
        Optional callback invoked for unsolicited ground notifications
        (``event_triggered``, ``chat_response``).  Receives the full
        decoded response dict.
    on_admin_event:
        Optional callback invoked for unsolicited ``admin_event_triggered``
        push messages on the admin response topic.  Receives the full
        decoded response dict.
    on_connect:
        Optional callable invoked **after** the broker connection is
        established and all subscriptions are live.  Runs in a background
        thread — safe to make blocking ground or admin requests here.  Use
        this for one-time setup work that requires the MQTT loop to be
        running (e.g. resolving enemy asset IDs via the admin API).
    """

    def __init__(
        self,
        config: ScenarioConfig,
        team: TeamConfig,
        scheduler: EventScheduler,
        admin_password: str = "",
        on_session: Optional[Callable[[dict], None]] = None,
        on_event: Optional[Callable[[dict], None]] = None,
        on_admin_event: Optional[Callable[[dict], None]] = None,
        on_connect: Optional[Callable[[], None]] = None,
    ):
        self._config      = config
        self._team        = team
        self._scheduler   = scheduler
        self._on_session  = on_session
        self.on_event     = on_event
        self._on_connect_cb = on_connect   # called in a background thread after subscriptions are live
        self.on_downlink: Optional[Callable[[bytes], None]] = None

        game = config.game

        self._session_topic  = f"Zendir/SpaceRange/{game}/Session"
        self._uplink_topic   = f"Zendir/SpaceRange/{game}/{team.id}/Uplink"
        self._request_topic  = f"Zendir/SpaceRange/{game}/{team.id}/Request"
        self._response_topic = f"Zendir/SpaceRange/{game}/{team.id}/Response"
        self._downlink_topic = f"Zendir/SpaceRange/{game}/{team.id}/Downlink"

        self._admin_request_topic  = f"Zendir/SpaceRange/{game}/Admin/Request"
        self._admin_response_topic = f"Zendir/SpaceRange/{game}/Admin/Response"

        self._current_instance: Optional[str] = None

        # Initialise ground request/response state
        self._init_ground_client()

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        # Admin client — available immediately; usable after connect
        self.admin = AdminRequestClient(
            mqtt_client=self._client,
            admin_password=admin_password,
            request_topic=self._admin_request_topic,
            response_topic=self._admin_response_topic,
            on_admin_event=on_admin_event,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_command(self, command: dict):
        """Encrypt and publish a command packet to the uplink topic."""
        json_data = json.dumps(command)
        encrypted = xor_encrypt(json_data.encode(), self._team.password)
        self._client.publish(self._uplink_topic, encrypted)
        printer.sent(command["command"], asset=command.get("id", "?"), args=command.get("args", {}))

    def register_downlink_handler(self, handler: Optional[Callable[[bytes], None]]):
        """
        Subscribe to this team's ``Downlink`` topic and deliver raw MQTT payloads.

        Pass ``None`` to detach. Used by :mod:`src.cyber_replay` to decode
        Uplink Intercept frames. Requires the team's **Caesar key** from config
        when decoding (see :mod:`src.downlink_codec`).

        If the client is already connected, subscribes immediately; otherwise
        :meth:`_on_connect` subscribes when a handler is registered.
        """
        self.on_downlink = handler
        if handler is not None and getattr(self._client, "is_connected", lambda: False)():
            self._client.subscribe(self._downlink_topic)
            printer.info(f"Subscribing to {self._downlink_topic}")

    def connect_and_run(self):
        """Connect to the broker and block in the network loop (Ctrl+C to exit)."""
        printer.info(f"Connecting to {self._config.server}:{self._config.port} …")
        self._client.connect(self._config.server, self._config.port, keepalive=60)
        try:
            self._client.loop_forever()
        except KeyboardInterrupt:
            print()
            printer.warn("Script terminated by user.")
            self._client.disconnect()

    def print_banner(self):
        """Print a startup summary banner and open a pending log file."""
        # Open a temporary log immediately so all output from this point is
        # captured.  It will be renamed to the proper instance-ID filename
        # once the first session message arrives and the instance is known.
        src_dir      = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(src_dir)
        logs_dir     = os.path.join(project_root, "logs")
        self._log_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        pending_path = os.path.join(logs_dir, f"{self._log_timestamp}_pending.log")
        printer.open_log(pending_path)

        live_id = self._scheduler.live_asset_id or "unresolved"
        printer.banner("SPACE RANGE — Event-Driven Simulation Script")
        printer.info(f"Game:    {self._config.game}")
        printer.info(f"Server:  {self._config.server}:{self._config.port}")
        printer.info(f"Team:    {self._team.name}  (ID={self._team.id})")
        printer.info(f"Asset:   {self._scheduler.asset_name}  (live ID: {live_id})")
        printer.info(f"Freq:    {self._team.frequency} MHz  |  Key: {self._team.key}")
        printer.divider()

    def _open_log(self, instance: str) -> None:
        """
        Switch to a new log file for *instance*.

        First instance after script start
        ----------------------------------
        ``print_banner`` opened a ``<timestamp>_pending.log`` to capture all
        startup output.  Here we close it, rename it in-place to the final
        ``<timestamp>_<instance>.log``, then re-open in append mode so no
        content is lost.

        Simulation reset
        ----------------
        A subsequent call means the simulation has restarted.  We close the
        current log and open a brand-new file with a fresh timestamp so each
        instance always has its own separate log.
        """
        src_dir      = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(src_dir)
        logs_dir     = os.path.join(project_root, "logs")

        old_path  = printer.current_log_path()
        is_pending = old_path is not None and os.path.basename(old_path).endswith("_pending.log")

        if is_pending:
            # First instance — rename pending → final, re-open in append mode
            timestamp  = getattr(self, "_log_timestamp",
                                  datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            final_path = os.path.join(logs_dir, f"{timestamp}_{instance}.log")
            printer.close_log()
            try:
                os.replace(old_path, final_path)
            except OSError:
                pass  # fall through — open_log will create the file if missing
            printer.open_log(final_path, mode="a")
        else:
            # Simulation reset — start a completely fresh log file
            timestamp  = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self._log_timestamp = timestamp   # update for any further resets
            final_path = os.path.join(logs_dir, f"{timestamp}_{instance}.log")
            printer.open_log(final_path, mode="w")

        printer.info(f"Log: {final_path}")

    # ------------------------------------------------------------------
    # MQTT callbacks (private)
    # ------------------------------------------------------------------

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            printer.success(f"Connected to {self._config.server}:{self._config.port}")
            printer.info(f"Subscribing to {self._session_topic}")
            client.subscribe(self._session_topic)
            printer.info(f"Subscribing to {self._response_topic}")
            client.subscribe(self._response_topic)
            if self.on_downlink:
                printer.info(f"Subscribing to {self._downlink_topic}")
                client.subscribe(self._downlink_topic)
            if self.admin._password:
                printer.info(f"Subscribing to {self._admin_response_topic}")
                client.subscribe(self._admin_response_topic)
            # Resolve own asset ID in the background (requires ground subscription live)
            threading.Thread(target=self._resolve_live_asset_id, daemon=True).start()
            # Fire the scenario's on_connect hook in the background (requires all subscriptions live)
            if self._on_connect_cb:
                threading.Thread(target=self._on_connect_cb, daemon=True).start()
        else:
            printer.error(f"Connection failed (rc={rc})")

    def _on_message(self, client, userdata, msg):
        # Route by topic
        if msg.topic == self._session_topic:
            self._handle_session_message(msg.payload)
        elif msg.topic == self._response_topic:
            self._handle_response_message(msg.payload)
        elif msg.topic == self._downlink_topic:
            if self.on_downlink:
                try:
                    self.on_downlink(msg.payload)
                except Exception as e:
                    printer.error(f"on_downlink handler raised: {e}")
        elif msg.topic == self._admin_response_topic:
            self.admin.handle_message(msg.payload)

    def _resolve_live_asset_id(self):
        """
        Query the ground controller for the team's asset list and resolve the
        live 8-character asset ID for the scheduler's target asset by name.

        Called automatically on connect and on simulation reset.
        Retries up to 3 times with a 3-second timeout each attempt.
        """
        asset_name = self._scheduler.asset_name
        printer.resolve(f"Looking up live asset ID for '{asset_name}' …")

        for attempt in range(1, 4):
            response = self.list_assets(timeout=3.0)
            if response is None:
                printer.warn(f"Resolve attempt {attempt}/3 timed out.")
                continue

            space_assets = response.get("args", {}).get("space", [])
            for asset in space_assets:
                if asset.get("name", "").lower() == asset_name.lower():
                    self._scheduler.resolve_asset_id(asset["asset_id"])
                    return

            printer.warn(f"Asset '{asset_name}' not found in response (attempt {attempt}/3).")

        printer.error(f"Could not resolve live asset ID for '{asset_name}' after 3 attempts.")
        printer.warn("Commands will be held until the ID is resolved.")

    def _handle_session_message(self, payload: bytes):
        try:
            session_data = json.loads(payload.decode())
            sim_time = session_data.get("time", 0)
            utc_time = session_data.get("utc", "")
            instance = session_data.get("instance")

            # Detect simulation reset
            if self._current_instance is None:
                self._current_instance = instance
                printer.info(f"Tracking simulation instance: {instance}")
                self._open_log(instance)
            elif instance != self._current_instance:
                printer.divider()
                printer.warn(f"Simulation reset detected!  Old: {self._current_instance}  →  New: {instance}")
                printer.divider()
                self._current_instance = instance
                self._open_log(instance)
                self._scheduler.reset_all()
                threading.Thread(target=self._resolve_live_asset_id, daemon=True).start()

            # Periodic status line (every 10 sim-seconds)
            if int(sim_time) % 10 == 0:
                pending = self._scheduler.pending_count
                printer.log(f"t={sim_time:.1f}s | UTC: {utc_time} | Pending: {pending}")

            # Tick the scheduler in a background thread so the MQTT network
            # thread stays free to send and receive messages while any
            # pre_trigger hook blocks waiting for admin/ground responses.
            _sim_time = sim_time
            _session  = session_data
            def _tick():
                self._scheduler.process(_sim_time, lambda cmd: self.send_command(cmd))
                if self._on_session:
                    self._on_session(_session)
            threading.Thread(target=_tick, daemon=True).start()

        except json.JSONDecodeError as e:
            printer.error(f"Failed to parse session data: {e}")
        except Exception as e:
            printer.error(f"Unexpected error in session handler: {e}")


# ---------------------------------------------------------------------------
# Credentials prompt helper
# ---------------------------------------------------------------------------

def _defaults_path() -> str:
    """Return the path to the local defaults file at the project root."""
    src_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(src_dir), _DEFAULTS_FILENAME)


def _load_defaults() -> dict:
    """Load saved defaults from the local defaults file, if it exists."""
    path = _defaults_path()
    if os.path.isfile(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_defaults(game: str, admin_password: str) -> None:
    """Persist game name and admin password to the local defaults file."""
    path = _defaults_path()
    try:
        with open(path, "w") as f:
            json.dump({"game": game, "admin_password": admin_password}, f, indent=2)
    except OSError as e:
        printer.warn(f"Could not save defaults to '{path}': {e}")


def prompt_credentials(
    default_game: str = _DEFAULT_GAME,
) -> tuple[str, str]:
    """
    Prompt the operator for the game/instance name and admin password.

    Saved values from the previous run are offered as defaults (shown in
    square brackets).  Press **Enter** to accept a default unchanged.

    The entered values are saved to ``.space-range-defaults`` at the project
    root for convenience on subsequent runs.  This file is excluded from
    version control via ``.gitignore``.

    Parameters
    ----------
    default_game:
        Fallback game name if no saved default exists and the operator
        presses Enter without typing.  Defaults to ``"ZENDIR"``.

    Returns
    -------
    tuple[str, str]
        ``(game_name, admin_password)``
    """
    saved = _load_defaults()
    saved_game     = saved.get("game", default_game)
    saved_password = saved.get("admin_password", "")

    try:
        game_input = input(f"Game name [{saved_game}]: ").strip()
        game = game_input if game_input else saved_game

        if saved_password:
            pw_prompt = f"Admin password [{saved_password}] (- for none): "
        else:
            pw_prompt = "Admin password (- for none): "
        pw_input = input(pw_prompt).strip()

        if pw_input == "-":
            admin_password = ""
        elif pw_input:
            admin_password = pw_input
        else:
            admin_password = saved_password  # Enter keeps the saved value
    except (EOFError, KeyboardInterrupt):
        return saved_game, saved_password

    _save_defaults(game, admin_password)
    return game, admin_password


def prompt_game_name(default: str = _DEFAULT_GAME) -> str:
    """
    Prompt the operator to enter a game/instance name at runtime.

    .. deprecated::
        Prefer :func:`prompt_credentials` which also collects the admin
        password and persists both values as defaults.

    Pressing Enter without typing anything uses *default*.
    """
    try:
        value = input(f"Game name [{default}]: ").strip()
        return value if value else default
    except (EOFError, KeyboardInterrupt):
        return default
