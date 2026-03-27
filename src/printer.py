# Copyright 2026 (c) Zendir, Pty Ltd. All Rights Reserved
# See the 'LICENSE' file at the root of this git repository

"""
Coloured terminal output helpers for Space Range scenario scripts.

Uses ANSI escape codes — works on any modern terminal (Windows 10+,
macOS, Linux).  Falls back to plain text automatically if the output
stream is not a TTY (e.g. when piping to a file or running in CI).

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

import sys
import os


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


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def success(msg: str) -> None:
    """Print a green success message. Use for commands sent and IDs resolved."""
    print(f"{_GREEN}{_BOLD}[OK]     {_RESET}{_GREEN}{msg}{_RESET}")


def warn(msg: str) -> None:
    """Print a yellow warning message. Use for non-fatal issues."""
    print(f"{_YELLOW}{_BOLD}[WARN]   {_RESET}{_YELLOW}{msg}{_RESET}")


def error(msg: str) -> None:
    """Print a red error message. Use for failures that need attention."""
    print(f"{_RED}{_BOLD}[ERROR]  {_RESET}{_RED}{msg}{_RESET}")


def info(msg: str) -> None:
    """Print a cyan informational message. Use for connection and instance events."""
    print(f"{_CYAN}{_BOLD}[INFO]   {_RESET}{_CYAN}{msg}{_RESET}")


def log(msg: str) -> None:
    """Print a grey log/status message. Use for periodic session heartbeats."""
    print(f"{_GREY}[LOG]    {msg}{_RESET}")


def sent(command: str, asset: str = "", args: dict | None = None) -> None:
    """Print a magenta uplink-sent message showing command, asset and args."""
    print(f"{_MAGENTA}{_BOLD}[SENT]   {_RESET}{_MAGENTA}Command : {command}{_RESET}")
    if asset:
        print(f"{_MAGENTA}         Asset   : {asset}{_RESET}")
    if args:
        print(f"{_MAGENTA}         Args    : {args}{_RESET}")


def event(sim_time: float, name: str, description: str = "") -> None:
    """Print a blue event-firing message."""
    print(f"\n{_BLUE}{_BOLD}[EVENT]  {_RESET}{_BLUE}t={sim_time:.1f}s — {name}{_RESET}")
    if description:
        print(f"{_BLUE}         {description}{_RESET}")


def complete(name: str) -> None:
    """Print a green event-completed message."""
    print(f"{_GREEN}{_BOLD}[DONE]   {_RESET}{_GREEN}{name}{_RESET}\n")


def request(request_type: str, req_id: int) -> None:
    """Print a cyan outgoing ground request message."""
    print(f"{_CYAN}[REQUEST] {request_type}  (req_id={req_id}){_RESET}")


def resolve(msg: str) -> None:
    """Print a cyan asset-resolution status message."""
    print(f"{_CYAN}[RESOLVE] {msg}{_RESET}")


def banner(title: str, width: int = 60, subtitle: str = "") -> None:
    """Print a bold white banner line."""
    print(f"{_WHITE}{_BOLD}{'=' * width}{_RESET}")
    print(f"{_WHITE}{_BOLD}{title.center(width)}{_RESET}")
    if subtitle:
        print(f"{_WHITE}{subtitle.center(width)}{_RESET}")
    print(f"{_WHITE}{_BOLD}{'=' * width}{_RESET}")


def divider(width: int = 60) -> None:
    """Print a grey divider line."""
    print(f"{_GREY}{'=' * width}{_RESET}")
