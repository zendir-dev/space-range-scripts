# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
MQTT client wrapper for Space Range scenarios.

Handles connecting to the broker, XOR encryption of uplink packets, and
routing of incoming session and ground response messages.

The :class:`SpaceRangeClient` inherits from :class:`~src.ground_client.GroundRequestClient`
and therefore exposes blocking ground request helpers such as
:meth:`list_assets`, :meth:`get_telemetry`, etc.
"""

from __future__ import annotations

from typing import Callable, Optional

import json
import threading
import paho.mqtt.client as mqtt

from .config import ScenarioConfig, TeamConfig
from .event_scheduler import EventScheduler
from .ground_client import GroundRequestClient
from . import printer

_DEFAULT_GAME   = "ZENDIR"
_DEFAULT_SERVER = "mqtt.zendir.io"
_DEFAULT_PORT   = 1883


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
    ``list_assets()``, ``list_entity()``, ``list_stations()``,,
    ``get_telemetry()``, ``set_telemetry()``, ``chat_query()``,,
    ``get_packet_schemas()``.

    Parameters
    ----------
    config:
        Scenario configuration loaded via :func:`~src.config.load_config`.
    team:
        The :class:`~src.config.TeamConfig` this client operates as.
    asset_id:
        The asset ID of the spacecraft being commanded.
    scheduler:
        The :class:`~src.event_scheduler.EventScheduler` to tick on every
        incoming session message.
    on_session:
        Optional extra callback called with the raw parsed session dict on
        every incoming session message, *after* the scheduler has been ticked.
    on_event:
        Optional callback invoked for unsolicited ground notifications
        (``event_triggered``, ``chat_response``).  Receives the full
        decoded response dict.
    """

    def __init__(
        self,
        config: ScenarioConfig,
        team: TeamConfig,
        scheduler: EventScheduler,
        on_session: Optional[Callable[[dict], None]] = None,
        on_event: Optional[Callable[[dict], None]] = None,
    ):
        self._config     = config
        self._team       = team
        self._scheduler  = scheduler
        self._on_session = on_session
        self.on_event    = on_event

        game = config.game

        self._session_topic  = f"Zendir/SpaceRange/{game}/Session"
        self._uplink_topic   = f"Zendir/SpaceRange/{game}/{team.id}/Uplink"
        self._request_topic  = f"Zendir/SpaceRange/{game}/{team.id}/Request"
        self._response_topic = f"Zendir/SpaceRange/{game}/{team.id}/Response"

        self._current_instance: Optional[str] = None

        # Initialise ground request/response state
        self._init_ground_client()

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_command(self, command: dict):
        """Encrypt and publish a command packet to the uplink topic."""
        json_data = json.dumps(command)
        encrypted = xor_encrypt(json_data.encode(), self._team.password)
        self._client.publish(self._uplink_topic, encrypted)
        printer.sent(command["command"], asset=command.get("id", "?"), args=command.get("args", {}))

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
        """Print a startup summary banner."""
        live_id = self._scheduler.live_asset_id or "unresolved"
        printer.banner("SPACE RANGE — Event-Driven Simulation Script")
        printer.info(f"Game:    {self._config.game}")
        printer.info(f"Server:  {self._config.server}:{self._config.port}")
        printer.info(f"Team:    {self._team.name}  (ID={self._team.id})")
        printer.info(f"Asset:   {self._scheduler.asset_name}  (live ID: {live_id})")
        printer.info(f"Freq:    {self._team.frequency} MHz  |  Key: {self._team.key}")
        printer.divider()

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
            threading.Thread(target=self._resolve_live_asset_id, daemon=True).start()
        else:
            printer.error(f"Connection failed (rc={rc})")

    def _on_message(self, client, userdata, msg):
        # Route by topic
        if msg.topic == self._session_topic:
            self._handle_session_message(msg.payload)
        elif msg.topic == self._response_topic:
            self._handle_response_message(msg.payload)

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
            elif instance != self._current_instance:
                printer.divider()
                printer.warn(f"Simulation reset detected!  Old: {self._current_instance}  →  New: {instance}")
                printer.divider()
                self._current_instance = instance
                self._scheduler.reset_all()
                threading.Thread(target=self._resolve_live_asset_id, daemon=True).start()

            # Periodic status line (every 10 sim-seconds)
            if int(sim_time) % 10 == 0:
                pending = self._scheduler.pending_count
                printer.log(f"t={sim_time:.1f}s | UTC: {utc_time} | Pending: {pending}")

            # Tick the scheduler
            self._scheduler.process(sim_time, lambda cmd: self.send_command(cmd))

            # Optional extra callback
            if self._on_session:
                self._on_session(session_data)

        except json.JSONDecodeError as e:
            printer.error(f"Failed to parse session data: {e}")
        except Exception as e:
            printer.error(f"Unexpected error in session handler: {e}")


# ---------------------------------------------------------------------------
# Game name prompt helper
# ---------------------------------------------------------------------------

def prompt_game_name(default: str = _DEFAULT_GAME) -> str:
    """
    Prompt the operator to enter a game/instance name at runtime.

    Pressing Enter without typing anything uses *default*.

    Parameters
    ----------
    default:
        The game name to use if the operator presses Enter with no input.
        Defaults to ``"ZENDIR"``.

    Returns
    -------
    str
        The game name to use for MQTT topic construction.
    """
    try:
        value = input(f"Game name [{default}]: ").strip()
        return value if value else default
    except (EOFError, KeyboardInterrupt):
        return default
