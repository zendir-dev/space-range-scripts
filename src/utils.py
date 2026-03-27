# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Shared utility helpers for the Space Range src package.
"""

from __future__ import annotations

import json


def decode_payload(decrypted: bytes) -> dict:
    """
    Parse a decrypted MQTT payload into a dict, handling both normal and
    double-stringified JSON, including partially double-encoded responses
    where individual string fields inside the object contain embedded JSON.

    The Space Range server exhibits two known encoding anomalies:

    1. **Fully double-stringified** — the entire payload is a JSON string
       whose value is the actual JSON object, e.g. ``"\"{ ... }\""``.
       Handled by a second ``json.loads`` on the string result.

    2. **Partially embedded JSON strings** — the outer JSON object parses
       correctly, but one or more string-valued fields within it contain
       JSON-encoded arrays or objects (often with heavy backslash escaping
       such as ``\\\\\\\\"``).  This manifests as, e.g., a
       ``"components"`` field whose value is the string
       ``"[{\\"name\\":\\"Chassis\\", ...}]"`` rather than a proper list.
       Handled by :func:`_decode_embedded_strings`, which walks the
       decoded dict recursively and calls ``json.loads`` on any string
       value that looks like a JSON array or object.

    Parameters
    ----------
    decrypted:
        Raw decrypted bytes from an MQTT message payload.

    Returns
    -------
    dict
        The fully parsed JSON object, with embedded JSON strings decoded.

    Raises
    ------
    json.JSONDecodeError
        If the payload cannot be parsed as JSON even after unwrapping.
    UnicodeDecodeError
        If the bytes cannot be decoded as UTF-8.
    """
    text = decrypted.decode("utf-8")

    # The server mangles JSON in two distinct ways that must be handled in order:
    #
    # Stage A — raw-text repair (before any json.loads call):
    #   The server emits bare JSON arrays/objects with backslash-escaped quotes
    #   instead of proper JSON string escaping.  For example the components field
    #   arrives as:
    #       "components": [{\\"name\\":\\"Chassis\\"}]
    #   The \\\" sequences are literal backslash + quote in the raw text; they
    #   are not inside a JSON string so json.loads rejects them immediately.
    #
    #   Strategy: replace every  \\"  (backslash-quote) with  "  in the raw
    #   text, then retry.  We also try halving double-backslash runs first in
    #   case the escaping is deeper (\\\\\" → \\" → ").
    #
    # Stage B — embedded-string unwrap (after json.loads succeeds):
    #   Some fields are valid JSON strings whose *value* is itself a JSON
    #   object/array serialised with json.dumps one or more times.
    #   Handled by _decode_embedded_strings() below.

    parsed = None
    last_exc: json.JSONDecodeError | None = None

    # Build the repair sequence:
    #   first try as-is, then halve \\, then strip \\ entirely, then strip \"
    # Each step is tried in order; the first one that lets json.loads succeed wins.
    def _repair_candidates(t: str):
        yield t                          # 0: as-is
        cur = t
        for _ in range(8):              # 1–8: halve double-backslash runs
            nxt = cur.replace("\\\\", "\\")
            if nxt == cur:
                break
            yield nxt
            cur = nxt
        # Final fallback: replace remaining backslash-quote with just quote.
        # This handles the bare-array case: [{\\"name\\"  →  [{"name"
        yield cur.replace('\\"', '"')

    for candidate in _repair_candidates(text):
        try:
            parsed = json.loads(candidate)
            break
        except json.JSONDecodeError as exc:
            last_exc = exc

    if parsed is None:
        raise last_exc  # type: ignore[misc]

    # Case 1: server double-stringified the whole payload.
    if isinstance(parsed, str):
        parsed = json.loads(parsed)

    if not isinstance(parsed, dict):
        raise json.JSONDecodeError(
            f"Expected a JSON object after decoding, got {type(parsed).__name__}",
            text,
            0,
        )

    # Case 2: individual string fields inside the dict contain embedded JSON.
    return _decode_embedded_strings(parsed)


def _decode_embedded_strings(obj):
    """
    Recursively walk *obj* (dict, list, or scalar) and fully unwrap any
    string values that are JSON-encoded containers.

    The server can encode the same value through many layers of
    ``json.dumps``, so a string field may need to be decoded multiple times
    before it becomes a proper dict/list.  We keep calling ``json.loads``
    on string values until either:

    - the result is no longer a string (it became a dict/list → done), or
    - ``json.loads`` raises (it's a plain string → leave it as-is), or
    - the string is unchanged after a ``json.loads`` round-trip (no-op).

    After unwrapping to a dict/list we recurse into it so nested fields
    that are also over-encoded are handled too.
    """
    if isinstance(obj, dict):
        return {k: _decode_embedded_strings(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decode_embedded_strings(item) for item in obj]
    if isinstance(obj, str):
        current = obj
        for _ in range(16):   # hard cap — prevents infinite loops on pathological input
            stripped = current.strip()
            # Only try to decode if it looks like a JSON container or quoted string.
            if not (
                (stripped.startswith("{") and stripped.endswith("}")) or
                (stripped.startswith("[") and stripped.endswith("]")) or
                (stripped.startswith('"') and stripped.endswith('"'))
            ):
                break
            try:
                decoded = json.loads(stripped)
            except json.JSONDecodeError:
                break
            if decoded == current:
                break   # json.loads was a no-op
            if not isinstance(decoded, str):
                # Unwrapped to a dict or list — recurse into it and return.
                return _decode_embedded_strings(decoded)
            # Still a string — go around again (another layer of encoding).
            current = decoded
        return current
    return obj
