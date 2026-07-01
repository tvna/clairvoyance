"""Behavioural tests for the adaptive-coaching observation store.

The store ships in ``hooks/`` (consumer-facing, outside the ``scripts/``
coverage scope), so it is exercised the same way ``check_hooks.sh`` exercises
the bash hooks: through its real CLI via subprocess, with the data directory
redirected to a tmp path so nothing touches the developer's workstation.

The store is backed by the ``sqlite3`` CLI with no Python fallback, so the
recording cases are skipped when the CLI is absent; the argument-validation case
needs no backend and always runs. Readiness has two gates -- a session grace
period and accumulated adaptive signal -- so the observation-focused tests set
the session threshold to 0 to isolate the signal gate.
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


def _resolve_bash():
    """A POSIX bash for running the bundled .sh.

    On Windows a bare ``bash`` resolves to the System32 WSL launcher, which —
    with no distro installed — prints a UTF-16 "…to install" notice and exits
    non-zero. Prefer Git Bash (the same interpreter run-hook.cmd locates in
    production); fall back to whatever ``bash`` is on PATH elsewhere.
    """
    if os.name == "nt":
        for candidate in (
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe",
        ):
            if pathlib.Path(candidate).exists():
                return candidate
    return shutil.which("bash") or "bash"


BASH = _resolve_bash()

HAS_SQLITE3 = shutil.which("sqlite3") is not None
needs_sqlite3 = pytest.mark.skipif(not HAS_SQLITE3, reason="sqlite3 CLI not installed")


def run_raw(args, data_dir, threshold=None, session_threshold=0, env_extra=None, stdin_text=""):
    """Invoke the store with an isolated data dir; return the CompletedProcess.

    ``session_threshold`` defaults to 0 (grace disabled) so signal-gate tests are
    not blocked by it; pass ``None`` to leave it unset and exercise the default.
    ``env_extra`` sets extra environment variables (e.g. raw capture or rotation
    bounds); all store-specific vars are cleared from the ambient env first so
    tests are deterministic. ``stdin_text`` feeds stdin, used by ``--context-stdin``
    so raw context never travels through argv.
    """
    env = {**os.environ, "CLAIRVOYANCE_DATA_DIR": str(data_dir)}
    for key in (
        "LOCALAPPDATA",
        "XDG_DATA_HOME",
        "CLAIRVOYANCE_COACH_THRESHOLD",
        "CLAIRVOYANCE_SESSION_THRESHOLD",
        "CLAIRVOYANCE_STORE_CONTEXT",
        "CLAIRVOYANCE_MAX_OBSERVATIONS",
        "CLAIRVOYANCE_MAX_AGE_DAYS",
    ):
        env.pop(key, None)
    if threshold is not None:
        env["CLAIRVOYANCE_COACH_THRESHOLD"] = str(threshold)
    if session_threshold is not None:
        env["CLAIRVOYANCE_SESSION_THRESHOLD"] = str(session_threshold)
    if env_extra:
        env.update({k: str(v) for k, v in env_extra.items()})
    return subprocess.run([BASH, STORE_SH.as_posix(), *args], capture_output=True, text=True, env=env, input=stdin_text)


def run(args, data_dir, threshold=None, session_threshold=0, env_extra=None, stdin_text=""):
    """Invoke the store and parse its JSON, asserting a clean exit."""
    result = run_raw(args, data_dir, threshold, session_threshold, env_extra, stdin_text)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@needs_sqlite3
def test_status_on_empty_store_is_not_ready(tmp_path):
    """A fresh workstation has no data, so coaching must not trigger."""
    out = run(["status"], tmp_path / "store", threshold=3)
    assert out == {
        "available": False,
        "count": 0,
        "threshold": 3,
        "sessions": 0,
        "session_threshold": 0,
        "ready": False,
    }


@needs_sqlite3
def test_record_accumulates_until_threshold(tmp_path):
    """With the grace gate disabled, readiness follows the adaptive-signal gate."""
    data_dir = tmp_path / "store"
    first = run(["record", "--category", "avoidance"], data_dir, threshold=2)
    assert first["recorded"] is True
    assert first["count"] == 1
    assert first["ready"] is False

    second = run(["record", "--category", "loss-aversion", "--outcome", "incorrect"], data_dir, threshold=2)
    assert second["count"] == 2
    assert second["ready"] is True

    status = run(["status"], data_dir, threshold=2)
    assert status == {
        "available": True,
        "count": 2,
        "threshold": 2,
        "sessions": 0,
        "session_threshold": 0,
        "ready": True,
        "distinct_categories": 2,
        "by_category": {"avoidance": 1, "loss-aversion": 1},
    }


@needs_sqlite3
def test_session_grace_blocks_until_threshold(tmp_path):
    """Even with signal met, coaching waits out the session grace period."""
    data_dir = tmp_path / "store"
    # Signal gate satisfied immediately (threshold 1), but grace needs 2 sessions.
    recorded = run(["record", "--category", "avoidance"], data_dir, threshold=1, session_threshold=2)
    assert recorded["count"] == 1
    assert recorded["ready"] is False  # sessions 0 < 2

    run(["record-session"], data_dir, session_threshold=2)
    blocked = run(["status"], data_dir, threshold=1, session_threshold=2)
    assert blocked["sessions"] == 1
    assert blocked["ready"] is False  # sessions 1 < 2

    run(["record-session"], data_dir, session_threshold=2)
    ready = run(["status"], data_dir, threshold=1, session_threshold=2)
    assert ready["sessions"] == 2
    assert ready["ready"] is True  # sessions 2 >= 2 and count 1 >= 1


@needs_sqlite3
def test_sessions_without_signal_are_not_ready(tmp_path):
    """Reaching the session count alone does not trigger coaching without signal."""
    data_dir = tmp_path / "store"
    run(["record-session"], data_dir, session_threshold=1)
    out = run(["status"], data_dir, threshold=5, session_threshold=1)
    assert out["sessions"] == 1
    assert out["count"] == 0
    assert out["ready"] is False


@needs_sqlite3
def test_record_session_increments(tmp_path):
    """record-session counts up and reports the configured grace threshold."""
    data_dir = tmp_path / "store"
    for expected in (1, 2, 3):
        out = run(["record-session"], data_dir, session_threshold=50)
        assert out == {
            "recorded_session": True,
            "available": True,
            "sessions": expected,
            "session_threshold": 50,
        }


@needs_sqlite3
def test_default_session_threshold_is_50(tmp_path):
    """With no override the grace period defaults to 50 sessions."""
    out = run(["record-session"], tmp_path / "store", session_threshold=None)
    assert out["session_threshold"] == 50


@needs_sqlite3
def test_unknown_category_is_folded_to_other(tmp_path):
    """Free-text categories never persist; they collapse to the coded 'other'."""
    out = run(["record", "--category", "some free text leak"], tmp_path / "store", threshold=5)
    assert out["by_category"] == {"other": 1}


@needs_sqlite3
def test_signal_is_coded_and_truncated(tmp_path):
    """Signal labels are sanitised to a short [a-z0-9-] token, not content."""
    data_dir = tmp_path / "store"
    run(["record", "--category", "avoidance", "--signal", "Skipped The Hard Call!!"], data_dir)
    db = data_dir / "coaching.db"
    assert db.exists()
    rows = sqlite3.connect(str(db)).execute("SELECT signal FROM observations").fetchall()
    assert rows == [("skipped-the-hard-call",)]


@needs_sqlite3
def test_default_threshold_applies_when_unset(tmp_path):
    """With no override the store uses the default coaching threshold."""
    out = run(["record", "--category", "no-experiment"], tmp_path / "store")
    assert out["threshold"] == 5


@needs_sqlite3
def test_invalid_threshold_falls_back_to_default(tmp_path):
    """A non-numeric or non-positive threshold degrades to the default."""
    assert run(["status"], tmp_path / "store", threshold="0")["threshold"] == 5
    assert run(["status"], tmp_path / "store", threshold="not-a-number")["threshold"] == 5


@needs_sqlite3
def test_unwritable_data_dir_degrades_gracefully(tmp_path):
    """Volatility is tolerated: an unusable store reports not-available, not error."""
    blocker = tmp_path / "blocked"
    blocker.write_text("not a directory")  # a file where a dir is expected
    out = run(["record", "--category", "avoidance"], blocker / "store")
    assert out["available"] is False
    assert out["recorded"] is False
    assert out["ready"] is False


def test_record_requires_category(tmp_path):
    """An outcome-only record (no --category) is rejected and writes nothing."""
    data_dir = tmp_path / "store"
    result = run_raw(["record", "--outcome", "incorrect"], data_dir)
    assert result.returncode != 0
    assert not (data_dir / "coaching.db").exists()


@needs_sqlite3
def test_home_fallback_dir_is_dotted(tmp_path):
    """With no override vars set, the store falls back to ~/.clairvoyance (dotted)."""
    home = tmp_path / "home"
    home.mkdir()
    env = {**os.environ, "HOME": str(home)}
    for key in ("CLAIRVOYANCE_DATA_DIR", "LOCALAPPDATA", "XDG_DATA_HOME"):
        env.pop(key, None)
    result = subprocess.run(
        [BASH, STORE_SH.as_posix(), "record-session"], capture_output=True, text=True, env=env, input=""
    )
    assert result.returncode == 0, result.stderr
    assert (home / ".clairvoyance" / "coaching.db").exists()
    assert not (home / "clairvoyance").exists()


def _contexts(data_dir):
    """The stored context column for every observation, oldest first."""
    db = data_dir / "coaching.db"
    return [
        row[0] for row in sqlite3.connect(str(db)).execute("SELECT context FROM observations ORDER BY id").fetchall()
    ]


@needs_sqlite3
def test_context_not_stored_by_default(tmp_path):
    """Raw capture is opt-in: without it, stdin context is dropped, not persisted."""
    data_dir = tmp_path / "store"
    run(["record", "--category", "avoidance", "--context-stdin"], data_dir, stdin_text="deferred the cutover decision")
    assert _contexts(data_dir) == [None]


@needs_sqlite3
def test_context_stored_verbatim_when_raw_enabled(tmp_path):
    """With raw capture on, non-sensitive context is stored as-is."""
    data_dir = tmp_path / "store"
    run(
        ["record", "--category", "authority-dependence", "--context-stdin"],
        data_dir,
        env_extra={"CLAIRVOYANCE_STORE_CONTEXT": "1"},
        stdin_text="deferred the cutover decision again",
    )
    assert _contexts(data_dir) == ["deferred the cutover decision again"]


@needs_sqlite3
def test_raw_context_redacts_secrets(tmp_path):
    """The store-side backstop scrubs obvious secrets before persisting context."""
    data_dir = tmp_path / "store"
    leaky = "use AKIAABCDEFGHIJKLMNOP and password: hunter2 and token=deadbeefcafe1234 then normal text"
    run(
        ["record", "--category", "other", "--context-stdin"],
        data_dir,
        env_extra={"CLAIRVOYANCE_STORE_CONTEXT": "on"},
        stdin_text=leaky,
    )
    ctx = _contexts(data_dir)[0]
    assert "AKIAABCDEFGHIJKLMNOP" not in ctx
    assert "hunter2" not in ctx
    assert "deadbeefcafe1234" not in ctx
    assert "[REDACTED]" in ctx
    assert "normal text" in ctx  # ordinary content survives


@needs_sqlite3
def test_raw_context_quotes_are_safe(tmp_path):
    """A context with quotes and SQL metacharacters is stored literally, not executed."""
    data_dir = tmp_path / "store"
    tricky = "it's 'tricky'); DROP TABLE observations;--"
    run(
        ["record", "--category", "other", "--context-stdin"],
        data_dir,
        env_extra={"CLAIRVOYANCE_STORE_CONTEXT": "1"},
        stdin_text=tricky,
    )
    # The table survived the injection attempt and stored the text verbatim.
    assert _contexts(data_dir) == [tricky]


@needs_sqlite3
def test_rotation_by_count_keeps_newest(tmp_path):
    """A count bound prunes oldest rows so the store cannot grow without limit."""
    data_dir = tmp_path / "store"
    for n in range(5):
        run(
            ["record", "--category", "avoidance", "--signal", f"n{n}"],
            data_dir,
            env_extra={"CLAIRVOYANCE_MAX_OBSERVATIONS": "2"},
        )
    out = run(["status"], data_dir)
    assert out["count"] == 2


@needs_sqlite3
def test_rotation_by_age_drops_old(tmp_path):
    """An age bound prunes rows older than the window on the next record."""
    data_dir = tmp_path / "store"
    run(["record", "--category", "avoidance"], data_dir)
    # Backdate the existing row well past any window, then record under a 1-day bound.
    conn = sqlite3.connect(str(data_dir / "coaching.db"))
    conn.execute("UPDATE observations SET ts = '2000-01-01T00:00:00+00:00'")
    conn.commit()
    conn.close()
    out = run(["record", "--category", "loss-aversion"], data_dir, env_extra={"CLAIRVOYANCE_MAX_AGE_DAYS": "1"})
    assert out["count"] == 1
    cats = sqlite3.connect(str(data_dir / "coaching.db")).execute("SELECT category FROM observations").fetchall()
    assert cats == [("loss-aversion",)]


@needs_sqlite3
def test_rotation_zero_disables_bounds(tmp_path):
    """A 0 bound disables that rotation, so nothing is pruned."""
    data_dir = tmp_path / "store"
    for _ in range(4):
        run(
            ["record", "--category", "avoidance"],
            data_dir,
            env_extra={"CLAIRVOYANCE_MAX_OBSERVATIONS": "0", "CLAIRVOYANCE_MAX_AGE_DAYS": "0"},
        )
    assert run(["status"], data_dir)["count"] == 4


@needs_sqlite3
def test_quiz_metadata_is_recorded_when_present(tmp_path):
    """Outcome rows can carry confidence, calibration, and due date metadata."""
    data_dir = tmp_path / "store"
    run(
        [
            "record",
            "--category",
            "avoidance",
            "--outcome",
            "incorrect",
            "--confidence",
            "high",
            "--calibration",
            "overconfident",
            "--due-days",
            "1",
        ],
        data_dir,
    )
    row = (
        sqlite3.connect(str(data_dir / "coaching.db"))
        .execute("SELECT outcome, confidence, calibration, due_at IS NOT NULL FROM observations")
        .fetchone()
    )
    assert row == ("incorrect", "high", "overconfident", 1)


@needs_sqlite3
def test_invalid_quiz_metadata_is_folded_to_unknown_or_null(tmp_path):
    """Free-text quiz metadata never persists as-is."""
    data_dir = tmp_path / "store"
    run(
        [
            "record",
            "--category",
            "avoidance",
            "--outcome",
            "incorrect",
            "--confidence",
            "very sure",
            "--calibration",
            "personal flaw",
            "--due-days",
            "soon",
        ],
        data_dir,
    )
    row = (
        sqlite3.connect(str(data_dir / "coaching.db"))
        .execute("SELECT confidence, calibration, due_at FROM observations")
        .fetchone()
    )
    assert row == (None, "unknown", None)
