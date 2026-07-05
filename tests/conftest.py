"""Shared test infrastructure for the adaptive-store and persona test suites.

Both ``test_adaptive_store.py`` and ``test_adaptive_coaching_personas.py``
drive ``hooks/adaptive-store.sh`` through subprocess and inspect its sqlite3
db directly; they previously duplicated the bash resolution, sqlite3-CLI
availability check, store-specific env-clearing keys, and the
subprocess-invocation/db-query helpers themselves (issue #95, finding 3, and
a follow-up self-review pass on PR #108).
"""

import json
import os
import pathlib
import shutil
import sqlite3
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE_SH = REPO_ROOT / "hooks" / "adaptive-store.sh"


def resolve_bash() -> str:
    """A POSIX bash for running the bundled .sh.

    On Windows a bare ``bash`` resolves to the System32 WSL launcher, which --
    with no distro installed -- prints a UTF-16 "...to install" notice and
    exits non-zero. Prefer Git Bash (the same interpreter run-hook.cmd
    locates in production); fall back to whatever ``bash`` is on PATH
    elsewhere.

    ``CLAIRVOYANCE_TEST_BASH`` overrides the resolved interpreter -- CI uses
    it to pin a specific bash (e.g. the stock bash 3.2 on macOS) regardless
    of what a later PATH entry (Homebrew, etc.) would otherwise resolve to,
    so a bash-version regression like issue #89's finding F5 is caught
    deterministically instead of depending on runner PATH order.
    """
    if override := os.environ.get("CLAIRVOYANCE_TEST_BASH"):
        return override
    if os.name == "nt":
        for candidate in (
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe",
        ):
            if pathlib.Path(candidate).exists():
                return candidate
    return shutil.which("bash") or "bash"


BASH = resolve_bash()

HAS_SQLITE3 = shutil.which("sqlite3") is not None
needs_sqlite3 = pytest.mark.skipif(not HAS_SQLITE3, reason="sqlite3 CLI not installed")

# Store-specific environment variables cleared from the ambient env before
# each subprocess invocation so tests are deterministic regardless of what
# the developer or CI runner has set.
CLAIRVOYANCE_ENV_KEYS = (
    "LOCALAPPDATA",
    "XDG_DATA_HOME",
    "CLAIRVOYANCE_COACH_THRESHOLD",
    "CLAIRVOYANCE_SESSION_THRESHOLD",
    "CLAIRVOYANCE_STORE_CONTEXT",
    "CLAIRVOYANCE_MAX_OBSERVATIONS",
    "CLAIRVOYANCE_MAX_AGE_DAYS",
)


def run_store_raw(
    args: list[str],
    data_dir: pathlib.Path,
    coach_threshold: int | str | None = None,
    session_threshold: int | str | None = 0,
    env_extra: dict[str, str] | None = None,
    stdin_text: str = "",
) -> subprocess.CompletedProcess[str]:
    """Invoke the store CLI with an isolated data dir; return the raw CompletedProcess.

    ``coach_threshold``/``session_threshold`` are only set in the environment
    when not ``None``, so callers can exercise the store's own defaults. All
    store-specific vars are cleared from the ambient env first so tests are
    deterministic. ``stdin_text`` feeds stdin, used by ``--context-stdin`` so
    raw context never travels through argv.
    """
    env = {**os.environ, "CLAIRVOYANCE_DATA_DIR": str(data_dir)}
    for key in CLAIRVOYANCE_ENV_KEYS:
        env.pop(key, None)
    if coach_threshold is not None:
        env["CLAIRVOYANCE_COACH_THRESHOLD"] = str(coach_threshold)
    if session_threshold is not None:
        env["CLAIRVOYANCE_SESSION_THRESHOLD"] = str(session_threshold)
    if env_extra:
        env.update({k: str(v) for k, v in env_extra.items()})
    return subprocess.run([BASH, STORE_SH.as_posix(), *args], capture_output=True, text=True, env=env, input=stdin_text)


def run_store(
    args: list[str],
    data_dir: pathlib.Path,
    coach_threshold: int | str | None = None,
    session_threshold: int | str | None = 0,
    env_extra: dict[str, str] | None = None,
    stdin_text: str = "",
) -> dict[str, object]:
    """Invoke the store CLI and parse its JSON reply, asserting a clean exit."""
    result = run_store_raw(args, data_dir, coach_threshold, session_threshold, env_extra, stdin_text)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def fetch_one(db_path: pathlib.Path, sql: str) -> tuple[object, ...] | None:
    """Run a single-row read query against the store's sqlite3 db, closing the connection."""
    conn = sqlite3.connect(str(db_path))
    row = conn.execute(sql).fetchone()
    conn.close()
    return row


def fetch_all(db_path: pathlib.Path, sql: str) -> list[tuple[object, ...]]:
    """Run a read query against the store's sqlite3 db, closing the connection."""
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(sql).fetchall()
    conn.close()
    return rows


def execute_write(db_path: pathlib.Path, sql: str) -> None:
    """Run a write statement against the store's sqlite3 db, committing and closing."""
    conn = sqlite3.connect(str(db_path))
    conn.execute(sql)
    conn.commit()
    conn.close()


def fetch_latest_quiz_metadata(db_path: pathlib.Path) -> tuple[object, ...] | None:
    """Read outcome/confidence/calibration/due_at off the newest observations row."""
    return fetch_one(
        db_path,
        "SELECT outcome, confidence, calibration, due_at IS NOT NULL FROM observations ORDER BY id DESC LIMIT 1",
    )
