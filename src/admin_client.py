# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Admin request/response client for Space Range.

Provides :class:`AdminRequestClient` — used by
:class:`~src.mqtt_client.SpaceRangeClient` to send admin-level requests to
the Space Range server and block until a matching response arrives.

This client is intended for **instructors and constructive agents**, not for
participant teams.  It uses a separate set of MQTT topics and a dedicated
admin password that is distinct from all team passwords.

Request/Response model
-----------------------
- Each request is assigned a random integer ``req_id``.
- The request is XOR-encrypted with the **admin password** and published to
  the ``Admin/Request`` topic.
- The client waits on a :class:`threading.Event` that is set when a response
  with the same ``req_id`` arrives on the ``Admin/Response`` topic.
- If the response does not arrive within *timeout* seconds, ``None`` is
  returned.

Unsolicited ``admin_event_triggered`` messages arrive on the same
``Admin/Response`` topic and are routed to an optional ``on_admin_event``
callback registered on the client.

MQTT Topics
-----------
- Request:  ``Zendir/SpaceRange/[GAME]/Admin/Request``
- Response: ``Zendir/SpaceRange/[GAME]/Admin/Response``
"""

from __future__ import annotations

import json
import random
import threading
from typing import Callable, Optional

from . import printer
from .utils import decode_payload


class AdminRequestClient:
    """
    Blocking admin request/response client.

    Instantiated and held as ``SpaceRangeClient.admin``.  After
    ``connect_and_run()`` is called the MQTT client is live and all methods
    below are usable from any thread.

    Parameters
    ----------
    mqtt_client:
        The underlying ``paho.mqtt.client.Client`` instance (shared with
        :class:`~src.mqtt_client.SpaceRangeClient`).
    admin_password:
        The 6-character alphanumeric admin password for this game session.
    request_topic:
        Full MQTT topic for admin requests.
    response_topic:
        Full MQTT topic for admin responses / push notifications.
    on_admin_event:
        Optional callback invoked for unsolicited ``admin_event_triggered``
        push messages.  Receives the full decoded response dict.
    """

    def __init__(
        self,
        mqtt_client,
        admin_password: str,
        request_topic: str,
        response_topic: str,
        on_admin_event: Optional[Callable[[dict], None]] = None,
    ):
        self._client          = mqtt_client
        self._password        = admin_password
        self._request_topic   = request_topic
        self._response_topic  = response_topic
        self.on_admin_event   = on_admin_event

        self._pending: dict[int, dict] = {}
        self._pending_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public request methods
    # ------------------------------------------------------------------

    def list_entities(self, timeout: float = 5.0) -> Optional[dict]:
        """
        Fetch all teams (name, id, password, color) and all ground stations.

        Returns the full response dict on success, or ``None`` on timeout.

        Example response args (under the ``"args"`` key)::

            {
                "teams": [{"name": "Red Team", "id": 10, "password": "AAAAAA", "color": "#FF366A"}, ...],
                "stations": [{"name": "Singapore", "latitude": 1.35, ...}, ...]
            }
        """
        return self._admin_request("admin_list_entities", {}, timeout=timeout)

    def list_team(self, team_name: str, timeout: float = 5.0) -> Optional[dict]:
        """
        Fetch full details for a single team, including all asset IDs and
        component lists.

        Parameters
        ----------
        team_name:
            The team's display name (case-insensitive, e.g. ``"Red Team"``).

        Returns the full response dict on success, or ``None`` on timeout.

        Example response args (under the ``"args"`` key)::

            {
                "name": "Red Team",
                "id": 10,
                "password": "AAAAAA",
                "color": "#FF366A",
                "assets": {
                    "space": [
                        {
                            "asset_id": "fb345a0c",
                            "name": "Microsat",
                            "rpo_enabled": True,
                            "components": [...]
                        }
                    ]
                }
            }
        """
        return self._admin_request("admin_list_team", {"team": team_name}, timeout=timeout)

    def query_data(
        self,
        asset_id: str,
        recent: bool = False,
        min_time: Optional[float] = None,
        max_time: Optional[float] = None,
        timeout: float = 5.0,
    ) -> Optional[dict]:
        """
        Fetch telemetry data for a specific asset.

        Set ``recent=True`` to return only the single most-recent data point
        (ignores ``min_time`` / ``max_time``).  Omit both time bounds to
        return all stored data.

        Parameters
        ----------
        asset_id:
            The 8-character hex asset ID of the spacecraft to query.
        recent:
            If ``True``, return only the latest data point.
        min_time:
            Minimum simulation time (seconds) for the query range.
        max_time:
            Maximum simulation time (seconds) for the query range.
        timeout:
            Seconds to wait for a response.

        Returns the full response dict on success (the ``"args"`` key contains
        ``asset_id``, ``team``, ``data``), or ``None`` on timeout.

        The ``data`` list contains flat dicts keyed by ``"category.property"``,
        e.g. ``"communications.frequency"``, ``"location.latitude"``, etc.
        Each entry also has a ``"time"`` key (simulation seconds).
        """
        args: dict = {"asset_id": asset_id, "recent": recent}
        if min_time is not None:
            args["min_time"] = min_time
        if max_time is not None:
            args["max_time"] = max_time
        return self._admin_request("admin_query_data", args, timeout=timeout)

    def query_events(
        self,
        asset_id: Optional[str] = None,
        team: Optional[str] = None,
        timeout: float = 5.0,
    ) -> Optional[dict]:
        """
        Fetch historical events, optionally filtered by asset ID or team name.
        Provide at least one of *asset_id* or *team*.

        Returns the full response dict on success (the ``"args"`` key contains
        an ``"events"`` list), or ``None`` on timeout.
        """
        args: dict = {}
        if asset_id is not None:
            args["asset_id"] = asset_id
        if team is not None:
            args["team"] = team
        return self._admin_request("admin_query_events", args, timeout=timeout)

    def get_simulation(self, timeout: float = 5.0) -> Optional[dict]:
        """
        Fetch the current simulation state and speed.

        Returns the full response dict on success (the ``"args"`` key contains
        ``"state"`` and ``"speed"``), or ``None`` on timeout.

        Possible ``state`` values: ``"Running"``, ``"Paused"``,
        ``"Stopped"``, ``"Scrubbing"``.
        """
        return self._admin_request("admin_get_simulation", {}, timeout=timeout)

    def get_scenario_events(self, timeout: float = 5.0) -> Optional[dict]:
        """
        Fetch the list of predefined scenario events (instructor-configured
        failures, triggers, etc.) loaded into the current scenario.

        Returns the full response dict on success (the ``"args"`` key contains
        an ``"events"`` list), or ``None`` on timeout.
        """
        return self._admin_request("admin_get_scenario_events", {}, timeout=timeout)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def get_live_frequency(self, asset_id: str, timeout: float = 5.0) -> Optional[float]:
        """
        Query the most-recent telemetry for *asset_id* and extract the
        current ``communications.frequency`` value.

        Returns the frequency in MHz, or ``None`` if the query failed or
        the field was not present.

        This is the key helper used by the jammer ``pre_trigger`` hook in
        scenario scripts to fetch live enemy frequencies at the moment of
        firing rather than using values fixed at schedule-build time.
        """
        response = self.query_data(asset_id, recent=True, timeout=timeout)
        if response is None:
            printer.warn(f"admin: no response for query_data on asset '{asset_id}'")
            return None

        data_list = response.get("args", {}).get("data", [])
        if not data_list:
            printer.warn(f"admin: empty data for asset '{asset_id}'")
            return None

        freq = data_list[-1].get("communications.frequency")
        if freq is None:
            printer.warn(f"admin: 'communications.frequency' missing for asset '{asset_id}'")
        return freq

    def get_live_frequencies(
        self,
        asset_ids: list[str],
        fallback_frequencies: Optional[list[float]] = None,
        timeout: float = 5.0,
    ) -> list[float]:
        """
        Query live ``communications.frequency`` for each asset in *asset_ids*.

        For any asset where the query fails, the corresponding value from
        *fallback_frequencies* is used (if provided), otherwise that asset is
        skipped.

        Parameters
        ----------
        asset_ids:
            List of 8-character hex asset IDs to query.
        fallback_frequencies:
            Optional list of fallback values, parallel to *asset_ids*.
        timeout:
            Per-asset query timeout in seconds.

        Returns
        -------
        list[float]
            Live frequencies (MHz) for each asset, in the same order as
            *asset_ids*, with fallbacks applied where needed.
        """
        frequencies = []
        for i, asset_id in enumerate(asset_ids):
            freq = self.get_live_frequency(asset_id, timeout=timeout)
            if freq is not None:
                printer.info(f"admin: asset '{asset_id}' live frequency = {freq} MHz")
                frequencies.append(freq)
            elif fallback_frequencies and i < len(fallback_frequencies):
                fallback = fallback_frequencies[i]
                printer.warn(f"admin: using fallback frequency {fallback} MHz for asset '{asset_id}'")
                frequencies.append(fallback)
            else:
                printer.warn(f"admin: skipping asset '{asset_id}' — no frequency data and no fallback")
        return frequencies

    def resolve_enemy_asset_ids(
        self,
        enemy_team_names: list[str],
        timeout: float = 5.0,
    ) -> dict[str, list[str]]:
        """
        Resolve the live asset IDs for a list of enemy team names using
        ``admin_list_team``.

        Asset IDs are stable within a running scenario (they only change on
        reset), so it is safe to resolve them once at connect time and cache
        them.

        Parameters
        ----------
        enemy_team_names:
            List of team display names to resolve (e.g. ``["Blue Team"]``).
        timeout:
            Per-team request timeout in seconds.

        Returns
        -------
        dict[str, list[str]]
            Mapping of team name → list of asset IDs for that team's space
            assets.  Teams that could not be resolved are omitted.
        """
        result: dict[str, list[str]] = {}
        for name in enemy_team_names:
            response = self.list_team(name, timeout=timeout)
            if response is None:
                printer.warn(f"admin: could not resolve asset IDs for team '{name}'")
                continue
            space_assets = response.get("args", {}).get("assets", {}).get("space", [])
            ids = [a["asset_id"] for a in space_assets if "asset_id" in a]
            if ids:
                printer.success(f"admin: team '{name}' → asset IDs: {ids}")
                result[name] = ids
            else:
                printer.warn(f"admin: team '{name}' returned no space assets")
        return result

    # ------------------------------------------------------------------
    # Core send/wait logic
    # ------------------------------------------------------------------

    def _admin_request(
        self,
        request_type: str,
        args: dict,
        timeout: float = 5.0,
    ) -> Optional[dict]:
        """
        Build, encrypt, and publish an admin request then block until the
        matching response arrives or *timeout* elapses.

        Returns the full response dict on success, ``None`` on timeout.
        """
        req_id = random.randint(1, 2_147_483_647)

        packet: dict = {"type": request_type, "req_id": req_id}
        if args:
            packet["args"] = args

        event = threading.Event()
        with self._pending_lock:
            self._pending[req_id] = {"event": event, "response": None}

        json_data = json.dumps(packet)
        encrypted = self._xor_encrypt(json_data.encode(), self._password)
        self._client.publish(self._request_topic, encrypted)
        printer.request(request_type, req_id)

        arrived = event.wait(timeout=timeout)

        with self._pending_lock:
            slot = self._pending.pop(req_id, {})

        if not arrived:
            printer.warn(f"admin: no response for '{request_type}' (req_id={req_id}) after {timeout}s")
            return None

        response = slot.get("response")
        if response and not response.get("success", True):
            printer.error(f"admin request '{request_type}' failed: {response.get('error', 'unknown error')}")

        return response

    # ------------------------------------------------------------------
    # Incoming message handler (called by SpaceRangeClient._on_message)
    # ------------------------------------------------------------------

    def handle_message(self, payload: bytes):
        """
        Decrypt and dispatch an incoming admin response message.

        - Matched responses unblock the waiting ``_admin_request`` call.
        - Unsolicited ``admin_event_triggered`` messages are routed to
          ``on_admin_event`` if registered.
        """
        decrypted = b""
        try:
            decrypted = self._xor_encrypt(payload, self._password)
            data = decode_payload(decrypted)
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            printer.error(f"admin: failed to decode response: {e}")
            printer.error(f"admin: raw decrypted bytes (first 256): {decrypted[:256]!r}")
            return
        except Exception as e:
            printer.error(f"admin: unexpected error decoding response: {e}")
            return

        msg_type = data.get("type", "")
        req_id   = data.get("req_id", 0)

        if msg_type == "admin_event_triggered":
            args = data.get("args", {})
            if not isinstance(args, dict):
                args = {}
            name     = args.get("name", "unknown")
            sim_time = args.get("simulation_time", "?")
            team_id  = args.get("team_id", "?")
            printer.info(f"admin event  t={sim_time}s  team={team_id}  — {name}")
            if self.on_admin_event:
                self.on_admin_event(data)
            return

        # Matched response — wake the waiting thread
        with self._pending_lock:
            slot = self._pending.get(req_id)

        if slot is not None:
            with self._pending_lock:
                if req_id in self._pending:
                    self._pending[req_id]["response"] = data
                    self._pending[req_id]["event"].set()
        else:
            # Unmatched response — could be a push notification we don't recognise yet
            printer.warn(f"admin: received unmatched response (type={msg_type}, req_id={req_id})")

    # ------------------------------------------------------------------
    # Encryption helper
    # ------------------------------------------------------------------

    @staticmethod
    def _xor_encrypt(data: bytes, password: str) -> bytes:
        """XOR-encrypt/decrypt *data* with a repeating *password* key."""
        if not password:
            return data
        password_bytes = password.encode()
        result = bytearray(len(data))
        for i in range(len(data)):
            result[i] = data[i] ^ password_bytes[i % len(password_bytes)]
        return bytes(result)
