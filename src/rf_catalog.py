# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
RF discovery helpers — list nominal frequencies / keys for every spacecraft.

Uses the admin API (``admin_list_entities`` + ``admin_list_team`` + ``admin_query_data``
with ``recent=True``), so you must hold the admin password on the client.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from . import printer

if TYPE_CHECKING:
    from .admin_client import AdminRequestClient


def _parse_communications_row(row: dict[str, Any]) -> tuple[Optional[float], Optional[int], Optional[float]]:
    """Extract frequency (MHz), Caesar key, bandwidth (MHz) from one ``query_data`` sample."""
    freq = row.get("communications.frequency")
    key = row.get("communications.key")
    bw = row.get("communications.bandwidth")
    try:
        freq_f = float(freq) if freq is not None else None
    except (TypeError, ValueError):
        freq_f = None
    try:
        key_i = int(key) if key is not None else None
    except (TypeError, ValueError):
        key_i = None
    try:
        bw_f = float(bw) if bw is not None else None
    except (TypeError, ValueError):
        bw_f = None
    return freq_f, key_i, bw_f


def get_all_frequencies(
    admin: "AdminRequestClient",
    *,
    timeout: float = 5.0,
) -> list[dict[str, Any]]:
    """
    Return one row per space asset with latest nominal RF parameters from the DB.

    Each row contains:

    ``team_name``, ``team_id``, ``asset_id``, ``asset_name``,
    ``frequency_mhz``, ``key``, ``bandwidth_mhz``, ``sim_time`` (sample time).

    Rows are skipped when ``admin_query_data`` fails or communications fields
    are missing.
    """
    ent = admin.list_entities(timeout=timeout)
    if not ent or not ent.get("success", True):
        printer.warn("rf_catalog: admin_list_entities failed")
        return []

    teams = ent.get("args", {}).get("teams") or []
    out: list[dict[str, Any]] = []

    for team in teams:
        tname = team.get("name")
        tid = team.get("id")
        if not tname:
            continue
        detail = admin.list_team(str(tname), timeout=timeout)
        if not detail or not detail.get("success", True):
            printer.warn(f"rf_catalog: admin_list_team skipped for '{tname}'")
            continue

        assets = detail.get("args", {}).get("assets", {}).get("space") or []
        for asset in assets:
            aid = asset.get("asset_id")
            if not aid:
                continue
            q = admin.query_data(str(aid), recent=True, timeout=timeout)
            if not q or not q.get("success", True):
                printer.warn(f"rf_catalog: no query_data for asset '{aid}'")
                continue
            rows = q.get("args", {}).get("data") or []
            if not rows:
                printer.warn(f"rf_catalog: empty data for asset '{aid}'")
                continue
            row = rows[-1]
            freq, key, bw = _parse_communications_row(row)
            out.append(
                {
                    "team_name": tname,
                    "team_id": tid,
                    "asset_id": aid,
                    "asset_name": asset.get("name") or "",
                    "frequency_mhz": freq,
                    "key": key,
                    "bandwidth_mhz": bw,
                    "sim_time": row.get("time"),
                }
            )

    return out


def frequency_table(admin: "AdminRequestClient", *, timeout: float = 5.0) -> str:
    """Human-readable table string for :func:`get_all_frequencies`."""
    rows = get_all_frequencies(admin, timeout=timeout)
    if not rows:
        return "(no RF rows)"
    lines = [
        f"{'Team':<22} {'Asset':<12} {'Name':<18} {'MHz':>10} {'Key':>5} {'BW':>8}",
        "-" * 84,
    ]
    for r in rows:
        lines.append(
            f"{str(r['team_name'])[:21]:<22} {r['asset_id']:<12} {str(r['asset_name'])[:17]:<18} "
            f"{r['frequency_mhz'] if r['frequency_mhz'] is not None else '—':>10} "
            f"{r['key'] if r['key'] is not None else '—':>5} "
            f"{r['bandwidth_mhz'] if r['bandwidth_mhz'] is not None else '—':>8}"
        )
    return "\n".join(lines)
