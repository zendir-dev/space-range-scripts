#!/usr/bin/env python3
# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""Convert a Space Range telemetry SQLite database to a ``.zenrec`` archive.

Usage:
    python scripts/db_to_zenrec_conversion.py PATH_TO_DATABASE

The archive is written beside the database with the same base name. Space
Range's database contains sampled telemetry only, so metadata that was never
stored (events, questions, stations, original asset GUIDs, and the scenario
epoch) is inferred or represented by an empty value.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
import statistics
import sys
import tempfile
import zipfile
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


ZENREC_FORMAT = "zendir-session-recording"
ZENREC_VERSION = 1
DEFAULT_BUCKET = "general"

_INTEGER_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(
    r"^[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?$"
)


def _json(value: Any) -> str:
    """Return condensed JSON using the same one-object-per-line convention."""
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    )


def _iso8601(value: datetime) -> str:
    """Format a UTC datetime with an ISO-8601 ``Z`` suffix."""
    return value.astimezone(timezone.utc).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")


def _path_segment(raw: str, index: int) -> str:
    """Mirror SessionRecordingLibrary::ToPathSegment."""
    cleaned: list[str] = []
    pending_dash = False
    for character in raw:
        if character.isalnum() or character in "._-":
            if pending_dash and cleaned:
                cleaned.append("-")
            pending_dash = False
            cleaned.append(character)
        else:
            pending_dash = True
    result = "".join(cleaned).strip("-.")
    return result or f"asset-{index}"


def _quote_identifier(identifier: str) -> str:
    """Safely quote a SQLite table identifier."""
    return '"' + identifier.replace('"', '""') + '"'


def _split_key(key: str) -> tuple[str, str]:
    """Split ``section.field`` as the Studio writer does."""
    dot = key.find(".")
    if 0 < dot < len(key) - 1:
        return key[:dot], key[dot + 1 :]
    return DEFAULT_BUCKET, key


def _canonical_measurement(section: str, field: str) -> str | None:
    """Mirror the canonical measurement mapping in the C++ writer."""
    section_lower = section.lower()
    field_lower = field.lower()

    if section_lower == "power" and field_lower == "battery_percent":
        return "battery.soc"
    if section_lower == "storage" and field_lower == "storage_percent":
        return "storage.used"
    if section_lower == "location":
        return {
            "latitude": "position.latitude",
            "longitude": "position.longitude",
            "altitude": "position.altitude",
        }.get(field_lower)

    if section_lower in {"uplink", "downlink"}:
        direction = "uplink" if section_lower == "uplink" else "downlink"
        compact_field = field_lower.replace("_", "")
        if compact_field == "snr":
            return f"link.snr_{direction}"
        if compact_field in {"datarate", "baudrate"}:
            return f"link.data_rate_{direction}"
    return None


def _value_from_database(value: Any) -> Any:
    """Recover useful JSON scalar types from SQLite's untyped text columns."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    text = str(value)
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if _INTEGER_RE.fullmatch(text):
        try:
            return int(text)
        except ValueError:
            pass
    if _FLOAT_RE.fullmatch(text):
        try:
            number = float(text)
            return number if math.isfinite(number) else None
        except ValueError:
            pass
    return text


def _table_names(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [str(row[0]) for row in rows]


def _columns(connection: sqlite3.Connection, table: str) -> list[str]:
    rows = connection.execute(f"PRAGMA table_info({_quote_identifier(table)})")
    return [str(row[1]) for row in rows]


def _infer_team_and_asset(table: str) -> tuple[str, str]:
    """Infer display names from Studio's ``team-asset`` table convention."""
    if "-" in table:
        team, asset = table.rsplit("-", 1)
    else:
        team, asset = "recovered", table
    return team, asset


def _display_name(identifier: str) -> str:
    return identifier.replace("_", " ").replace("-", " ").strip().title()


def _sampling_interval(connection: sqlite3.Connection, table: str) -> float:
    quoted = _quote_identifier(table)
    times = [
        float(row[0])
        for row in connection.execute(
            f"SELECT time FROM {quoted} WHERE time IS NOT NULL "
            "ORDER BY CAST(time AS REAL)"
        )
    ]
    differences = [
        later - earlier
        for earlier, later in zip(times, times[1:])
        if later > earlier
    ]
    return statistics.median(differences) if differences else 0.0


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json(value), encoding="utf-8", newline="\n")


def _write_json_lines(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as output:
        for row in rows:
            output.write(_json(row))
            output.write("\n")
            count += 1
    return count


def convert_database(
    database_path: Path,
    output_path: Path,
    *,
    overwrite: bool = False,
    sim_start: datetime | None = None,
) -> tuple[int, int]:
    """Convert *database_path* and return ``(asset_count, telemetry_rows)``."""
    database_path = database_path.resolve()
    output_path = output_path.resolve()

    if not database_path.is_file():
        raise FileNotFoundError(f"Database does not exist: {database_path}")
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"Output already exists: {output_path} (use --force to replace it)"
        )

    uri = database_path.as_uri() + "?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True)
    except sqlite3.Error as error:
        raise RuntimeError(f"Could not open SQLite database: {error}") from error
    connection.row_factory = sqlite3.Row

    try:
        tables = _table_names(connection)
        if not tables:
            raise ValueError("The database contains no telemetry tables")

        table_columns = {table: _columns(connection, table) for table in tables}
        invalid = [table for table, cols in table_columns.items() if "time" not in cols]
        if invalid:
            names = ", ".join(repr(name) for name in invalid)
            raise ValueError(f"Telemetry table(s) have no 'time' column: {names}")

        maximum_time = max(
            float(
                connection.execute(
                    f"SELECT COALESCE(MAX(CAST(time AS REAL)), 0) "
                    f"FROM {_quote_identifier(table)}"
                ).fetchone()[0]
            )
            for table in tables
        )
        captured_at = datetime.fromtimestamp(
            database_path.stat().st_mtime, timezone.utc
        )
        inferred_start = captured_at - timedelta(seconds=maximum_time)
        simulation_start = sim_start or inferred_start
        epoch_seconds = simulation_start.timestamp()

        with tempfile.TemporaryDirectory(prefix="zenrec-") as temporary:
            root = Path(temporary)
            (root / "session").mkdir(parents=True)
            (root / "session" / "events.jsonl").write_text(
                "", encoding="utf-8", newline="\n"
            )
            (root / "session" / "brief.md").write_text(
                "Recovered from a Space Range telemetry database.\n",
                encoding="utf-8",
                newline="\n",
            )
            _write_json(root / "session" / "stations.json", [])
            _write_json(root / "session" / "questions.json", [])

            assets: list[dict[str, Any]] = []
            teams: OrderedDict[str, dict[str, Any]] = OrderedDict()
            contents: list[dict[str, Any]] = [
                {"path": "session/events.jsonl", "rows": 0}
            ]
            total_rows = 0

            for asset_index, table in enumerate(tables):
                columns = table_columns[table]
                team_key, asset_key = _infer_team_and_asset(table)
                team_id = team_key
                asset_id = table
                asset_name = _display_name(asset_key) or table
                asset_dir = _path_segment(asset_id, asset_index)
                neutral = team_key.lower() == "neutral"

                if not neutral and team_id not in teams:
                    teams[team_id] = {
                        "id": team_id,
                        "name": _display_name(team_key) or team_key,
                        "color": "#808080",
                    }

                bucket_fields: OrderedDict[str, list[tuple[str, str]]] = OrderedDict()
                for column in columns:
                    if column.lower() == "time":
                        continue
                    bucket, field = _split_key(column)
                    bucket_fields.setdefault(bucket, []).append((column, field))

                bucket_files: dict[str, Any] = {}
                bucket_counts = {bucket: 0 for bucket in bucket_fields}
                try:
                    for bucket in bucket_fields:
                        relative = f"assets/{asset_dir}/telemetry/{bucket}.jsonl"
                        path = root / Path(relative)
                        path.parent.mkdir(parents=True, exist_ok=True)
                        bucket_files[bucket] = path.open(
                            "w", encoding="utf-8", newline="\n"
                        )

                    query = (
                        f"SELECT * FROM {_quote_identifier(table)} "
                        "ORDER BY CAST(time AS REAL)"
                    )
                    for database_row in connection.execute(query):
                        elapsed = float(database_row["time"])
                        for bucket, fields in bucket_fields.items():
                            field_values: dict[str, Any] = {}
                            for column, field in fields:
                                value = _value_from_database(database_row[column])
                                if value is not None:
                                    field_values[field] = value
                            if not field_values:
                                continue
                            line = {
                                "t": elapsed,
                                "u": epoch_seconds + elapsed,
                                "s": None,
                                "f": field_values,
                            }
                            bucket_files[bucket].write(_json(line) + "\n")
                            bucket_counts[bucket] += 1
                            total_rows += 1
                finally:
                    for output in bucket_files.values():
                        output.close()

                telemetry_meta = []
                for bucket, fields in bucket_fields.items():
                    measurements = {
                        field: measurement
                        for _, field in fields
                        if (
                            measurement := _canonical_measurement(bucket, field)
                        )
                    }
                    telemetry_meta.append(
                        {
                            "bucket": bucket,
                            "name": bucket,
                            "apid": None,
                            "subType": None,
                            "rows": bucket_counts[bucket],
                            "measurements": measurements,
                        }
                    )
                    contents.append(
                        {
                            "path": (
                                f"assets/{asset_dir}/telemetry/{bucket}.jsonl"
                            ),
                            "rows": bucket_counts[bucket],
                        }
                    )

                _write_json(
                    root / "assets" / asset_dir / "meta.json",
                    {
                        "id": asset_id,
                        "name": asset_name,
                        "teamId": None if neutral else team_id,
                        "neutral": neutral,
                        "components": [],
                        "configuration": None,
                        "limits": [],
                        "telemetry": telemetry_meta,
                    },
                )
                assets.append(
                    {
                        "id": asset_id,
                        "name": asset_name,
                        "dir": asset_dir,
                        "telemetry": list(bucket_fields),
                    }
                )

            interval = _sampling_interval(connection, tables[0])
            manifest = {
                "format": ZENREC_FORMAT,
                "version": ZENREC_VERSION,
                "producer": {
                    "app": "studio",
                    "role": "runtime",
                    "appVersion": "database-converter",
                },
                "capturedAt": _iso8601(captured_at),
                "captureReason": "recovered-database",
                "complete": True,
                "fidelity": "ground-truth",
                "workshop": {
                    "id": database_path.stem,
                    "title": _display_name(database_path.stem),
                    "durationSec": maximum_time,
                },
                "team": None,
                "teams": list(teams.values()),
                "sessionInstance": database_path.stem,
                "userId": None,
                "clocks": {
                    "simStartUtc": _iso8601(simulation_start),
                    "sessionStartMs": None,
                    "units": {
                        "time": "sim-seconds",
                        "utcTime": "epoch-seconds",
                        "timestamp": "iso-8601",
                    },
                },
                "assets": assets,
                "schemas": [],
                "contents": contents,
                "sampling": {"intervalSec": interval},
            }
            _write_json(root / "manifest.json", manifest)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_output = output_path.with_suffix(output_path.suffix + ".tmp")
            temporary_output.unlink(missing_ok=True)
            try:
                with zipfile.ZipFile(
                    temporary_output,
                    "w",
                    compression=zipfile.ZIP_DEFLATED,
                    compresslevel=6,
                    allowZip64=True,
                ) as archive:
                    for path in sorted(root.rglob("*")):
                        if path.is_file():
                            archive.write(path, path.relative_to(root).as_posix())
                temporary_output.replace(output_path)
            finally:
                temporary_output.unlink(missing_ok=True)

        return len(assets), total_rows
    finally:
        connection.close()


def _parse_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "expected an ISO-8601 datetime, for example 2026-09-16T04:00:00Z"
        ) from error
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a Space Range telemetry SQLite database into a .zenrec "
            "archive beside it."
        )
    )
    parser.add_argument("database", type=Path, help="path to the input .db file")
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing .zenrec output",
    )
    parser.add_argument(
        "--sim-start-utc",
        type=_parse_datetime,
        metavar="ISO8601",
        help=(
            "scenario epoch; defaults to database modification time minus "
            "the last telemetry timestamp"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _arguments(argv)
    database = args.database.expanduser()
    output = database.with_suffix(".zenrec")

    try:
        assets, rows = convert_database(
            database,
            output,
            overwrite=args.force,
            sim_start=args.sim_start_utc,
        )
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError, sqlite3.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"Error writing recording: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {output.resolve()}")
    print(f"Converted {assets} assets and {rows} telemetry rows.")
    if args.sim_start_utc is None:
        print(
            "Note: the database has no scenario epoch; simStartUtc was inferred "
            "from its modification time. Use --sim-start-utc for an exact epoch."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
