#!/usr/bin/env python3
"""Local, anonymous adaptive-coaching observation store (SQLite).

Persists a small, anonymous record of adaptive-challenge observations on the
operator's own workstation so the ``adaptive-coaching`` skill can wait until
enough signal has accumulated before it coaches. It stores only coded
metadata -- an adaptive-challenge category, a short coded signal label, a quiz
outcome, the session kind, and a UTC timestamp -- and never prompt text, code,
file paths, or any other content.

Volatility is tolerated by design. Ephemeral or read-only environments (remote
sessions, sandboxes, throwaway containers) simply do not persist, and any
storage error degrades to "not available / not recorded" instead of breaking
the session: every subcommand exits 0 and reports state as JSON.

Storage directory, first match wins:

1. ``$CLAIRVOYANCE_DATA_DIR``
2. ``%LOCALAPPDATA%\\clairvoyance``        (the Windows workstation default)
3. ``$XDG_DATA_HOME/clairvoyance``
4. ``~/.clairvoyance``

The database file is ``coaching.db`` inside that directory.

Subcommands (each prints one JSON object to stdout):

* ``record --category C [--signal S] [--outcome correct|incorrect]
  [--session-kind K]`` -- append one observation, then report the new count.
* ``status`` -- report the accumulated count and whether enough data has
  accumulated to coach (``ready``).

The coaching threshold is ``$CLAIRVOYANCE_COACH_THRESHOLD`` (default 5).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

DB_FILENAME = "coaching.db"
# Five observations is the smallest sample that reads as a repeated pattern
# rather than a one-off, so coaching stays fair without a long wait. Override
# per operator with $CLAIRVOYANCE_COACH_THRESHOLD.
DEFAULT_THRESHOLD = 5

# Anonymous, coded adaptive-challenge categories (Heifetz framing). Anything
# outside this allowlist is folded into "other" so free-text content can never
# reach the store.
CATEGORIES = (
    "avoidance",  # the person sidesteps the work that only they can do
    "mislabeled-technical",  # an adaptive challenge framed as a technical one
    "loss-aversion",  # progress blocked by an unnamed loss the person fears
    "values-conflict",  # competing commitments the person has not reconciled
    "no-experiment",  # no learning loop is being run on the hard part
    "authority-dependence",  # the person defers the judgement they must own
    "other",
)
OUTCOMES = ("correct", "incorrect")
SIGNAL_RE = re.compile(r"[^a-z0-9-]")
# 40 chars fits a readable coded label (e.g. "skipped-the-hard-call") while
# capping anything longer, so a stray free-text value cannot bloat the row.
MAX_SIGNAL = 40


def resolve_data_dir() -> Path:
    """Return the storage directory, honouring the first source that is set."""
    override = os.environ.get("CLAIRVOYANCE_DATA_DIR")
    if override:
        return Path(override)
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / "clairvoyance"
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "clairvoyance"
    return Path.home() / "clairvoyance"


def threshold() -> int:
    """Return the coaching threshold, falling back to the default on bad input."""
    raw = os.environ.get("CLAIRVOYANCE_COACH_THRESHOLD")
    if not raw:
        return DEFAULT_THRESHOLD
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_THRESHOLD
    return value if value > 0 else DEFAULT_THRESHOLD


def _connect(create: bool) -> sqlite3.Connection | None:
    """Open the store, creating the directory/schema only when ``create``.

    Returns ``None`` when the environment cannot host the store (read-only or
    otherwise unwritable), which the caller reports as "not available".
    """
    data_dir = resolve_data_dir()
    db_path = data_dir / DB_FILENAME
    try:
        if create:
            data_dir.mkdir(parents=True, exist_ok=True)
        elif not db_path.exists():
            return None
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "CREATE TABLE IF NOT EXISTS observations ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "ts TEXT NOT NULL, "
            "category TEXT NOT NULL, "
            "signal TEXT, "
            "outcome TEXT, "
            "session_kind TEXT)"
        )
    except (OSError, sqlite3.Error):
        return None
    return conn


def _coded_signal(raw: str | None) -> str | None:
    """Coerce a signal label to a short, anonymous, coded token."""
    if not raw:
        return None
    coded = SIGNAL_RE.sub("-", raw.strip().lower())[:MAX_SIGNAL].strip("-")
    return coded or None


def _summary(conn: sqlite3.Connection) -> tuple[int, dict[str, int]]:
    """Return the total observation count and a per-category breakdown."""
    total = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    by_category = dict(conn.execute("SELECT category, COUNT(*) FROM observations GROUP BY category").fetchall())
    return total, by_category


def cmd_record(args: argparse.Namespace) -> dict[str, object]:
    """Append one anonymous observation and report the resulting state."""
    limit = threshold()
    conn = _connect(create=True)
    if conn is None:
        return {"recorded": False, "available": False, "count": 0, "threshold": limit, "ready": False}
    category = args.category if args.category in CATEGORIES else "other"
    outcome = args.outcome if args.outcome in OUTCOMES else None
    try:
        with conn:
            conn.execute(
                "INSERT INTO observations (ts, category, signal, outcome, session_kind) VALUES (?, ?, ?, ?, ?)",
                (
                    datetime.now(tz=UTC).isoformat(),
                    category,
                    _coded_signal(args.signal),
                    outcome,
                    _coded_signal(args.session_kind),
                ),
            )
        total, by_category = _summary(conn)
    except sqlite3.Error:
        return {"recorded": False, "available": False, "count": 0, "threshold": limit, "ready": False}
    finally:
        conn.close()
    return {
        "recorded": True,
        "available": True,
        "count": total,
        "threshold": limit,
        "ready": total >= limit,
        "distinct_categories": len(by_category),
        "by_category": by_category,
    }


def cmd_status(_args: argparse.Namespace) -> dict[str, object]:
    """Report the accumulated count and whether coaching should trigger."""
    limit = threshold()
    conn = _connect(create=False)
    if conn is None:
        return {"available": False, "count": 0, "threshold": limit, "ready": False}
    try:
        total, by_category = _summary(conn)
    except sqlite3.Error:
        return {"available": False, "count": 0, "threshold": limit, "ready": False}
    finally:
        conn.close()
    return {
        "available": True,
        "count": total,
        "threshold": limit,
        "ready": total >= limit,
        "distinct_categories": len(by_category),
        "by_category": by_category,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local, anonymous adaptive-coaching observation store.")
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser("record", help="append one anonymous observation")
    record.add_argument(
        "--category", required=True, help=f"adaptive-challenge category (one of: {', '.join(CATEGORIES)})"
    )
    record.add_argument("--signal", default=None, help="optional short coded label ([a-z0-9-], <=40 chars)")
    record.add_argument("--outcome", default=None, help="quiz outcome: correct or incorrect")
    record.add_argument(
        "--session-kind", default=None, help="optional coded session kind (startup/clear/compact/manual)"
    )
    record.set_defaults(func=cmd_record)

    status = sub.add_parser("status", help="report accumulated count and readiness")
    status.set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = args.func(args)
    json.dump(result, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
