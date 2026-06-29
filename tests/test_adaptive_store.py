"""Behavioural tests for the adaptive-coaching observation store.

The store ships in ``plugin/hooks/`` (consumer-facing, outside the ``scripts/``
coverage scope), so it is exercised the same way ``check_hooks.sh`` exercises
the bash hooks: through its real CLI via subprocess, with the data directory
redirected to a tmp path so nothing touches the developer's workstation.

The store has two interchangeable backends behind one entry point
(``adaptive-store.sh``): the ``sqlite3`` CLI (primary) and the ``python3``
stdlib fallback. Every behavioural test runs against both — ``sqlite3`` is
skipped when the CLI is absent — and ``test_backends_are_equivalent`` asserts
the two cannot drift.
"""

import json
import os
import pathlib
import shutil
import sqlite3
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE_SH = REPO_ROOT / "plugin" / "hooks" / "adaptive-store.sh"

HAS_SQLITE3 = shutil.which("sqlite3") is not None
BACKENDS = ["python", *(["sqlite3"] if HAS_SQLITE3 else [])]


def run(args, data_dir, backend, threshold=None):
    """Invoke the store entry point on one backend with an isolated data dir."""
    env = {**os.environ, "CLAIRVOYANCE_DATA_DIR": str(data_dir), "CLAIRVOYANCE_STORE_BACKEND": backend}
    env.pop("LOCALAPPDATA", None)
    env.pop("XDG_DATA_HOME", None)
    if threshold is not None:
        env["CLAIRVOYANCE_COACH_THRESHOLD"] = str(threshold)
    result = subprocess.run(["bash", str(STORE_SH), *args], capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize("backend", BACKENDS)
def test_status_on_empty_store_is_not_ready(tmp_path, backend):
    """A fresh workstation has no data, so coaching must not trigger."""
    out = run(["status"], tmp_path / "store", backend, threshold=3)
    assert out == {"available": False, "count": 0, "threshold": 3, "ready": False}


@pytest.mark.parametrize("backend", BACKENDS)
def test_record_accumulates_until_threshold(tmp_path, backend):
    """Coaching becomes ready only once enough observations accumulate."""
    data_dir = tmp_path / "store"
    first = run(["record", "--category", "avoidance"], data_dir, backend, threshold=2)
    assert first["recorded"] is True
    assert first["count"] == 1
    assert first["ready"] is False

    second = run(["record", "--category", "loss-aversion", "--outcome", "incorrect"], data_dir, backend, threshold=2)
    assert second["count"] == 2
    assert second["ready"] is True

    status = run(["status"], data_dir, backend, threshold=2)
    assert status == {
        "available": True,
        "count": 2,
        "threshold": 2,
        "ready": True,
        "distinct_categories": 2,
        "by_category": {"avoidance": 1, "loss-aversion": 1},
    }


@pytest.mark.parametrize("backend", BACKENDS)
def test_unknown_category_is_folded_to_other(tmp_path, backend):
    """Free-text categories never persist; they collapse to the coded 'other'."""
    out = run(["record", "--category", "some free text leak"], tmp_path / "store", backend, threshold=5)
    assert out["by_category"] == {"other": 1}


@pytest.mark.parametrize("backend", BACKENDS)
def test_signal_is_coded_and_truncated(tmp_path, backend):
    """Signal labels are sanitised to a short [a-z0-9-] token, not content."""
    data_dir = tmp_path / "store"
    run(["record", "--category", "avoidance", "--signal", "Skipped The Hard Call!!"], data_dir, backend)
    db = data_dir / "coaching.db"
    assert db.exists()
    rows = sqlite3.connect(str(db)).execute("SELECT signal FROM observations").fetchall()
    assert rows == [("skipped-the-hard-call",)]


@pytest.mark.parametrize("backend", BACKENDS)
def test_default_threshold_applies_when_unset(tmp_path, backend):
    """With no override the store uses the default coaching threshold."""
    out = run(["record", "--category", "no-experiment"], tmp_path / "store", backend)
    assert out["threshold"] == 5


@pytest.mark.parametrize("backend", BACKENDS)
def test_invalid_threshold_falls_back_to_default(tmp_path, backend):
    """A non-numeric or non-positive threshold degrades to the default."""
    assert run(["status"], tmp_path / "store", backend, threshold="0")["threshold"] == 5
    assert run(["status"], tmp_path / "store", backend, threshold="not-a-number")["threshold"] == 5


@pytest.mark.parametrize("backend", BACKENDS)
def test_unwritable_data_dir_degrades_gracefully(tmp_path, backend):
    """Volatility is tolerated: an unusable store reports not-available, not error."""
    blocker = tmp_path / "blocked"
    blocker.write_text("not a directory")  # a file where a dir is expected
    out = run(["record", "--category", "avoidance"], blocker / "store", backend)
    assert out["available"] is False
    assert out["recorded"] is False
    assert out["ready"] is False


@pytest.mark.skipif(not HAS_SQLITE3, reason="sqlite3 CLI not installed")
def test_backends_are_equivalent(tmp_path):
    """The sqlite3 and python backends must emit identical JSON for the same ops."""
    ops = [
        ["record", "--category", "avoidance", "--signal", "Skipped The Hard Call!!"],
        ["record", "--category", "free text leak", "--outcome", "incorrect"],
        ["record", "--category", "authority-dependence", "--session-kind", "Startup"],
        ["status"],
    ]
    sqlite_dir = tmp_path / "sqlite"
    python_dir = tmp_path / "python"
    for op in ops:
        sqlite_out = run(op, sqlite_dir, "sqlite3", threshold=2)
        python_out = run(op, python_dir, "python", threshold=2)
        assert sqlite_out == python_out, op
