# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Replay-style RF helpers — tune the ground receiver, snapshot links, re-fire bytes.

Typical scripted flow (SIGINT / red-team exercises):

1. **Discover** victim RF — :func:`rf_catalog.get_all_frequencies` or
   :func:`snapshot_asset_link`.
2. **Tune** your team's ground receiver to listen on that carrier using
   :func:`tune_ground` / :class:`GroundTuneSession`.
3. **Capture** ciphertext elsewhere (Uplink Intercept downlink, logs, or another
   client). Payload must be the **on-air bytes** (often Base64 in intercept records).
4. **Replay** with :func:`replay_transmit_bytes` at the same MHz — still ciphertext;
   victims decode with their Caesar key.

Nothing here decrypts traffic; it only orchestrates **ground** ``set_telemetry`` /
``transmit_bytes`` calls that already exist on :class:`~src.mqtt_client.SpaceRangeClient`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING

from . import printer

if TYPE_CHECKING:
    from .admin_client import AdminRequestClient
    from .ground_client import GroundRequestClient


@dataclass(frozen=True)
class RFLinkSnapshot:
    """Nominal RF identity for one spacecraft (MHz / Caesar key / bandwidth MHz)."""

    frequency_mhz: float
    key: int
    bandwidth_mhz: float


def snapshot_asset_link(
    admin: "AdminRequestClient",
    asset_id: str,
    *,
    timeout: float = 5.0,
) -> Optional[RFLinkSnapshot]:
    """
    Latest ``communications.*`` from ``admin_query_data(recent=True)`` for *asset_id*.
    """
    q = admin.query_data(asset_id, recent=True, timeout=timeout)
    if not q or not q.get("success", True):
        return None
    rows = q.get("args", {}).get("data") or []
    if not rows:
        return None
    row = rows[-1]
    freq = row.get("communications.frequency")
    key = row.get("communications.key")
    bw = row.get("communications.bandwidth")
    if freq is None or key is None or bw is None:
        printer.warn(f"replay: incomplete communications row for asset '{asset_id}'")
        return None
    return RFLinkSnapshot(float(freq), int(key), float(bw))


def snapshot_from_get_telemetry_args(args: Optional[dict[str, Any]]) -> Optional[RFLinkSnapshot]:
    """Build a snapshot from ``get_telemetry`` response ``args`` (frequency/key/bandwidth)."""
    if not args:
        return None
    f = args.get("frequency")
    k = args.get("key")
    b = args.get("bandwidth")
    if f is None or k is None or b is None:
        return None
    return RFLinkSnapshot(float(f), int(k), float(b))


def tune_ground(client: "GroundRequestClient", snap: RFLinkSnapshot, *, timeout: float = 5.0) -> Optional[dict]:
    """Call ``set_telemetry`` so the team's ground receiver tracks *snap*."""
    return client.set_telemetry(snap.frequency_mhz, snap.key, snap.bandwidth_mhz, timeout=timeout)


def replay_transmit_bytes(
    client: "GroundRequestClient",
    frequency_mhz: float,
    data: str,
    *,
    encoding: str = "base64",
    timeout: float = 5.0,
) -> Optional[dict]:
    """
    Emit *data* on the ground transmitter at *frequency_mhz* (see ``transmit_bytes``).

    For ciphertext taken from an Uplink Intercept payload, pass it as Base64 and
    set *frequency_mhz* to the intercept's receiver frequency.
    """
    return client.transmit_bytes(frequency_mhz, data, encoding=encoding, timeout=timeout)


class GroundTuneSession:
    """
    Context manager: save current RF from ``get_telemetry``, tune to *target*,
    restore previous settings on exit.

    Parameters
    ----------
    client:
        Connected :class:`~src.mqtt_client.SpaceRangeClient` (or any
        :class:`~src.ground_client.GroundRequestClient`).
    asset_id:
        Spacecraft whose team's RF settings are read/changed (same asset you own).
    target:
        Snapshot to apply while inside the ``with`` block.
    """

    def __init__(
        self,
        client: "GroundRequestClient",
        asset_id: str,
        target: RFLinkSnapshot,
    ):
        self.client = client
        self.asset_id = asset_id
        self.target = target
        self._previous: Optional[RFLinkSnapshot] = None

    def __enter__(self) -> "GroundTuneSession":
        tel = self.client.get_telemetry(self.asset_id, timeout=5.0)
        if not tel or not tel.get("success", True):
            printer.warn("GroundTuneSession: get_telemetry failed; cannot save restore point")
        args = tel.get("args", {}) if isinstance(tel, dict) else {}
        self._previous = snapshot_from_get_telemetry_args(args if isinstance(args, dict) else None)
        if self._previous is None:
            printer.warn("GroundTuneSession: could not read current telemetry; restore may fail")
        tune_ground(self.client, self.target)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._previous is not None:
            tune_ground(self.client, self._previous)
        return None
