# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Coloured terminal output helpers for Space Range scenario scripts.

Uses ANSI escape codes — works on any modern terminal (Windows 10+,
macOS, Linux).  Falls back to plain text automatically if the output
stream is not a TTY (e.g. when piping to a file or running in CI).

Every line printed to the terminal is also written in plain text (no ANSI
codes) to a rotating log file opened via :func:`open_log`.  Call
:func:`open_log` once per simulation instance — the framework does this
automatically when a new instance ID is detected.

Usage
-----
::

    from src.printer import success, warn, error, info, log, sent, event, banner

    success("Asset ID resolved: 2D708E04")
    warn("Live asset ID not yet resolved — skipping event.")
    error("Connection failed (rc=5)")
    info("Tracking simulation instance: 77224032")
    log("t=100.0s | UTC: 2025/04/15 07:31:40 | Pending: 4")
    sent("guidance", asset="2D708E04", args={"pointing": "sun"})
    event(sim_time=100.0, name="Sun Pointing")
    banner("SPACE RANGE", width=60)
"""

from __future__ import annotations

import os
import re
import sys
from typing import Optional


# ---------------------------------------------------------------------------
# ANSI colour codes
# ---------------------------------------------------------------------------

def _supports_colour() -> bool:
    """Return True if the terminal supports ANSI colour codes."""
    # Respect NO_COLOR standard (https://no-color.org/)
    if os.environ.get("NO_COLOR"):
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


_COLOUR = _supports_colour()

_RESET   = "\033[0m"   if _COLOUR else ""
_BOLD    = "\033[1m"   if _COLOUR else ""

# Foreground colours
_GREEN   = "\033[32m"  if _COLOUR else ""
_YELLOW  = "\033[33m"  if _COLOUR else ""
_RED     = "\033[31m"  if _COLOUR else ""
_CYAN    = "\033[36m"  if _COLOUR else ""
_WHITE   = "\033[37m"  if _COLOUR else ""
_GREY    = "\033[90m"  if _COLOUR else ""  # bright black
_MAGENTA = "\033[35m"  if _COLOUR else ""
_BLUE    = "\033[34m"  if _COLOUR else ""

_ANSI_ESCAPE = re.compile(r"\033\[[0-9;]*m")


# ---------------------------------------------------------------------------
# Log file management
# ---------------------------------------------------------------------------

_log_file: Optional["_LogFile"] = None


class _LogFile:
    """Thin wrapper around an open text file for plain-text log output."""

    def __init__(self, path: str, mode: str = "w"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._f = open(path, mode, encoding="utf-8", buffering=1)  # line-buffered
        self.path = path
        self._closed = False

    def write(self, line: str) -> None:
        if self._closed:
            return
        plain = _ANSI_ESCAPE.sub("", line)
        try:
            self._f.write(plain + "\n")
        except ValueError:
            pass  # file was closed between the guard check and the write

    def close(self) -> None:
        self._closed = True
        try:
            self._f.close()
        except OSError:
            pass


def open_log(path: str, mode: str = "w") -> None:
    """
    Open a new plain-text log file at *path*, closing any previously open one.

    Parameters
    ----------
    path:
        Absolute path to the log file to create (parent directories are
        created automatically).
    mode:
        File open mode — ``"w"`` (default) to create/overwrite, ``"a"`` to
        append to an existing file (used after a rename).
    """
    global _log_file
    close_log()
    _log_file = _LogFile(path, mode=mode)


def close_log() -> None:
    """Close the current log file, if one is open."""
    global _log_file
    if _log_file is not None:
        _log_file.close()
        _log_file = None


def current_log_path() -> Optional[str]:
    """Return the path of the currently open log file, or ``None``."""
    return _log_file.path if _log_file else None


# ---------------------------------------------------------------------------
# Internal print wrapper
# ---------------------------------------------------------------------------

def _p(*args, **kwargs) -> None:
    """
    Drop-in replacement for ``print()`` that also mirrors output to the log
    file (without ANSI escape codes).
    """
    print(*args, **kwargs)
    if _log_file is not None:
        # Reconstruct the line exactly as print() would produce it
        sep  = kwargs.get("sep", " ")
        end  = kwargs.get("end", "\n")
        line = sep.join(str(a) for a in args)
        # Strip the trailing newline — _LogFile.write adds its own
        if end == "\n":
            _log_file.write(line)
        else:
            # Non-standard end (e.g. empty string) — just strip ANSI and write
            _log_file.write(line + end.rstrip("\n"))


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

# All tag labels are padded to 10 characters so message bodies align:
#   [OK]       → 10 chars
#   [WARN]     → 10 chars
#   [ERROR]    → 10 chars
#   [INFO]     → 10 chars
#   [LOG]      → 10 chars
#   [SENT]     → 10 chars
#   [EVENT]    → 10 chars
#   [DONE]     → 10 chars
#   [REQUEST]  → 10 chars
#   [RESOLVE]  → 10 chars

def success(msg: str) -> None:
    """Print a green success message. Use for commands sent and IDs resolved."""
    _p(f"{_GREEN}{_BOLD}[OK]      {_RESET}{_GREEN}{msg}{_RESET}")


def warn(msg: str) -> None:
    """Print a yellow warning message. Use for non-fatal issues."""
    _p(f"{_YELLOW}{_BOLD}[WARN]    {_RESET}{_YELLOW}{msg}{_RESET}")


def error(msg: str) -> None:
    """Print a red error message. Use for failures that need attention."""
    _p(f"{_RED}{_BOLD}[ERROR]   {_RESET}{_RED}{msg}{_RESET}")


def info(msg: str) -> None:
    """Print a cyan informational message. Use for connection and instance events."""
    _p(f"{_CYAN}{_BOLD}[INFO]    {_RESET}{_CYAN}{msg}{_RESET}")


def log(msg: str) -> None:
    """Print a grey log/status message. Use for periodic session heartbeats."""
    _p(f"{_GREY}[LOG]     {msg}{_RESET}")


def sent(command: str, asset: str = "", args: dict | None = None) -> None:
    """Print a magenta uplink-sent message showing command, asset and args."""
    _p(f"{_MAGENTA}{_BOLD}[SENT]    {_RESET}{_MAGENTA}Command : {command}{_RESET}")
    if asset:
        _p(f"{_MAGENTA}          Asset   : {asset}{_RESET}")
    if args:
        _p(f"{_MAGENTA}          Args    : {args}{_RESET}")


def event(sim_time: float, name: str, description: str = "") -> None:
    """Print a blue event-firing message."""
    _p(f"\n{_BLUE}{_BOLD}[EVENT]   {_RESET}{_BLUE}t={sim_time:.1f}s — {name}{_RESET}")
    if description:
        _p(f"{_BLUE}          {description}{_RESET}")


def complete(name: str) -> None:
    """Print a green event-completed message."""
    _p(f"{_GREEN}{_BOLD}[DONE]    {_RESET}{_GREEN}{name}{_RESET}\n")


def request(request_type: str, req_id: int) -> None:
    """Print a cyan outgoing ground request message."""
    _p(f"{_CYAN}{_BOLD}[REQUEST] {_RESET}{_CYAN}{request_type}  (req_id={req_id}){_RESET}")


def resolve(msg: str) -> None:
    """Print a cyan asset-resolution status message."""
    _p(f"{_CYAN}{_BOLD}[RESOLVE] {_RESET}{_CYAN}{msg}{_RESET}")


def banner(title: str, width: int = 60, subtitle: str = "") -> None:
    """Print a bold white banner line."""
    _p(f"{_WHITE}{_BOLD}{'=' * width}{_RESET}")
    _p(f"{_WHITE}{_BOLD}{title.center(width)}{_RESET}")
    if subtitle:
        _p(f"{_WHITE}{subtitle.center(width)}{_RESET}")
    _p(f"{_WHITE}{_BOLD}{'=' * width}{_RESET}")


def divider(width: int = 60) -> None:
    """Print a grey divider line."""
    _p(f"{_GREY}{'=' * width}{_RESET}")
