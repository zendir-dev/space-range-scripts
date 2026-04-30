# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Ground request/response client for Space Range.

Provides :class:`GroundRequestClient` — a mixin used by
:class:`~src.mqtt_client.SpaceRangeClient` to send typed requests to the
ground controller and block until a matching response arrives (or a timeout
elapses).

Request/Response model
-----------------------
- Each request is assigned a random integer ``req_id``.
- The request is XOR-encrypted and published to the team's ``Request`` topic.
- The client waits on a :class:`threading.Event` that is set when a response
  with the same ``req_id`` arrives on the ``Response`` topic.
- If the response does not arrive within *timeout* seconds, the call returns
  ``None``.

Unsolicited ``event_triggered`` messages are routed to an optional
``on_event`` callback registered on the client.
"""

from __future__ import annotations

import json
import random
import threading
from typing import Callable, Optional
from . import printer
from .utils import decode_payload


# ---------------------------------------------------------------------------
# GroundRequestClient
# ---------------------------------------------------------------------------

class GroundRequestClient:
    """
    Mixin that adds blocking ground request/response calls to
    :class:`~src.mqtt_client.SpaceRangeClient`.

    Concrete subclasses must expose:
    - ``self._team``      — :class:`~src.config.TeamConfig`
    - ``self._config``    — :class:`~src.config.ScenarioConfig`
    - ``self._client``    — a ``paho.mqtt.client.Client`` instance
    - ``self.xor_encrypt(data, password)`` — encryption helper

    The mixin subscribes to the Response topic during ``_on_connect`` and
    routes incoming messages via ``_handle_response_message``.
    """

    # Set by the concrete class (SpaceRangeClient.__init__)
    _request_topic:  str = ""
    _response_topic: str = ""

    # on_event callback: callable that receives the raw event dict
    on_event: Optional[Callable[[dict], None]] = None

    # ------------------------------------------------------------------
    # Internal state
    # ------------------------------------------------------------------

    def _init_ground_client(self):
        """Initialise ground-client state. Call from __init__."""
        # pending_requests: req_id → {"event": threading.Event, "response": dict | None}
        self._pending_requests: dict[int, dict] = {}
        self._pending_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public request methods
    # ------------------------------------------------------------------

    def list_assets(self, timeout: float = 3.0) -> Optional[dict]:
        """
        Fetch all space assets assigned to this team.

        Returns the ``args`` dict from the response, or ``None`` on timeout.

        Example response args::

            {
                "space": [
                    {"asset_id": "SC_002", "name": "Recon", "rpo_enabled": True, "intercept_enabled": True},
                    ...
                ]
            }
        """
        return self._ground_request("list_assets", {}, timeout=timeout)

    def list_entity(self, asset_id: str, timeout: float = 3.0) -> Optional[dict]:
        """
        Fetch component and jammer information for *asset_id*.

        Returns the ``args`` dict from the response, or ``None`` on timeout.

        Example response args::

            {
                "asset_id": "SC_002",
                "components": [{"name": "Jammer", "class": "Jammer", ...}, ...],
                "jammer": {"is_active": False, "frequency": 0.0, "power": 0.0}
            }
        """
        return self._ground_request("list_entity", {"asset_id": asset_id}, timeout=timeout)

    def list_stations(self, timeout: float = 3.0) -> Optional[dict]:
        """
        Fetch all ground stations available to this team.

        Returns the ``args`` dict from the response, or ``None`` on timeout.

        Example response args::

            {
                "stations": [
                    {"name": "Dubai", "latitude": 25.2, "longitude": 55.3, "altitude": 10.0},
                    ...
                ]
            }
        """
        return self._ground_request("list_stations", {}, timeout=timeout)

    def get_telemetry(self, asset_id: str, timeout: float = 3.0) -> Optional[dict]:
        """
        Fetch current telemetry link-budget status for *asset_id*.

        Returns the ``args`` dict from the response, or ``None`` on timeout.
        """
        return self._ground_request("get_telemetry", {"asset_id": asset_id}, timeout=timeout)

    def set_telemetry(
        self,
        frequency: float,
        key: int,
        bandwidth: float = 1.0,
        timeout: float = 3.0,
    ) -> Optional[dict]:
        """
        Update the frequency, Caesar-cypher key, and bandwidth for this team.

        Returns the response dict (``{"success": True}``), or ``None`` on timeout.
        """
        return self._ground_request(
            "set_telemetry",
            {"frequency": frequency, "key": key, "bandwidth": bandwidth},
            timeout=timeout,
        )

    def chat_query(
        self,
        asset_id: str,
        prompt: str,
        messages: Optional[list] = None,
        timeout: float = 3.0,
    ) -> Optional[dict]:
        """
        Send a prompt to the AI chat assistant.

        The initial response simply acknowledges receipt (``{"success": True}``).
        The actual answer arrives later as an unsolicited ``chat_response``
        message on the Response topic and will be routed to ``on_event``.

        Returns the acknowledgement dict, or ``None`` on timeout.
        """
        return self._ground_request(
            "chat_query",
            {"asset_id": asset_id, "prompt": prompt, "messages": messages or []},
            timeout=timeout,
        )

    def get_packet_schemas(self, timeout: float = 3.0) -> Optional[dict]:
        """
        Fetch XTCE telemetry packet schema definitions.

        Returns the ``args`` dict containing ``"telemetry"`` (list of XML
        strings), or ``None`` on timeout.
        """
        return self._ground_request("get_packet_schemas", {}, timeout=timeout)

    def transmit_bytes(
        self,
        frequency_mhz: float,
        data: str,
        encoding: str = "base64",
        timeout: float = 5.0,
    ) -> Optional[dict]:
        """
        Transmit arbitrary bytes from the ground transmitter at *frequency_mhz*,
        bypassing normal uplink encryption.

        Parameters
        ----------
        frequency_mhz:
            Carrier frequency in MHz (must be ``> 0``).
        data:
            Payload interpreted per *encoding*.
        encoding:
            One of ``base64``, ``hex``, ``utf8``, ``ascii`` — same as the API.

        Returns the full response dict (``args`` may contain ``bytes_sent``),
        or ``None`` on timeout / failure.
        """
        return self._ground_request(
            "transmit_bytes",
            {"frequency": frequency_mhz, "encoding": encoding, "data": data},
            timeout=timeout,
        )

    # ------------------------------------------------------------------
    # Core send/wait logic
    # ------------------------------------------------------------------

    def _ground_request(
        self,
        request_type: str,
        args: dict,
        timeout: float = 3.0,
    ) -> Optional[dict]:
        """
        Build, encrypt, and publish a ground request then block until the
        matching response arrives or *timeout* elapses.

        Parameters
        ----------
        request_type:
            The ``type`` field of the request packet.
        args:
            The ``args`` dict to include (may be empty).
        timeout:
            Seconds to wait for a response before returning ``None``.

        Returns
        -------
        dict or None
            The full response packet dict on success, ``None`` on timeout.
        """
        req_id = random.randint(1, 2_147_483_647)

        packet: dict = {"type": request_type, "req_id": req_id}
        if args:
            packet["args"] = args

        # Register pending slot before publishing (avoid race condition)
        event = threading.Event()
        with self._pending_lock:
            self._pending_requests[req_id] = {"event": event, "response": None}

        # Encrypt and publish to the Request topic
        json_data = json.dumps(packet)
        encrypted = self._xor_encrypt(json_data.encode(), self._team.password)
        self._client.publish(self._request_topic, encrypted)
        printer.request(request_type, req_id)

        # Block until response or timeout
        arrived = event.wait(timeout=timeout)

        with self._pending_lock:
            slot = self._pending_requests.pop(req_id, {})

        if not arrived:
            printer.warn(f"No response for '{request_type}' (req_id={req_id}) after {timeout}s")
            return None

        response = slot.get("response")
        if response and not response.get("success", True):
            printer.error(f"Ground request '{request_type}' failed: {response.get('error', 'unknown error')}")

        return response

    # ------------------------------------------------------------------
    # Incoming response routing (called by the MQTT on_message handler)
    # ------------------------------------------------------------------

    def _handle_response_message(self, payload: bytes):
        """
        Decrypt and dispatch an incoming message from the Response topic.

        - If ``req_id`` matches a pending request, unblock the waiting thread.
        - If ``type`` is ``"event_triggered"`` or ``"chat_response"`` (unsolicited),
          route to ``on_event`` callback if registered.
        """
        decrypted = b""
        try:
            decrypted = self._xor_encrypt(payload, self._team.password)
            data = decode_payload(decrypted)
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            printer.error(f"Failed to decode response message: {e}")
            printer.error(f"Raw decrypted bytes (first 256): {decrypted[:256]!r}")
            return
        except Exception as e:
            printer.error(f"Unexpected error decoding response: {e}")
            return

        msg_type = data.get("type", "")
        req_id   = data.get("req_id", 0)

        # Check if this is an unsolicited notification
        unsolicited_types = {"event_triggered", "chat_response"}

        with self._pending_lock:
            pending = self._pending_requests.get(req_id)

        if pending is not None and msg_type not in unsolicited_types:
            # Matched response — wake the waiting thread
            with self._pending_lock:
                if req_id in self._pending_requests:
                    self._pending_requests[req_id]["response"] = data
                    self._pending_requests[req_id]["event"].set()
            return

        # Unsolicited message (event_triggered, chat_response, or unmatched)
        if msg_type in unsolicited_types:
            args = data.get("args", {})
            if not isinstance(args, dict):
                args = {}

            if msg_type == "event_triggered":
                name     = args.get("name", "unknown")
                sim_time = args.get("simulation_time", "?")
                printer.info(f"Event triggered  t={sim_time}s — {name}")
            elif msg_type == "chat_response":
                message = args.get("message", "")
                printer.info(f"Chat response: {message}")

            if self.on_event:
                self.on_event(data)

    # ------------------------------------------------------------------
    # Encryption helper (delegates to the concrete class implementation)
    # ------------------------------------------------------------------

    def _xor_encrypt(self, data: bytes, password: str) -> bytes:
        """XOR-encrypt/decrypt *data* with a repeating *password* key."""
        password_bytes = password.encode()
        result = bytearray(len(data))
        for i in range(len(data)):
            result[i] = data[i] ^ password_bytes[i % len(password_bytes)]
        return bytes(result)
