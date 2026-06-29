"""Behavioural tests for the adaptive-coaching observation store.

The store ships in ``plugin/hooks/`` (consumer-facing, outside the ``scripts/``
coverage scope), so it is exercised the same way ``check_hooks.sh`` exercises
the bash hooks: through its real CLI via subprocess, with the data directory
redirected to a tmp path so nothing touches the developer's workstation.
"""

import json
import os
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE = REPO_ROOT / "plugin" / "hooks" / "adaptive-store.py"


def run(args, data_dir, threshold=None):
    """Invoke the store CLI with an isolated data dir; return parsed JSON."""
    env = {**os.environ, "CLAIRVOYANCE_DATA_DIR": str(data_dir)}
    env.pop("LOCALAPPDATA", None)
    env.pop("XDG_DATA_HOME", None)
    if threshold is not None:
        env["CLAIRVOYANCE_COACH_THRESHOLD"] = str(threshold)
    result = subprocess.run(
        [sys.executable, str(STORE), *args],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_status_on_empty_store_is_not_ready(tmp_path):
    """A fresh workstation has no data, so coaching must not trigger."""
    out = run(["status"], tmp_path / "store", threshold=3)
    assert out == {"available": False, "count": 0, "threshold": 3, "ready": False}


def test_record_accumulates_until_threshold(tmp_path):
    """Coaching becomes ready only once enough observations accumulate."""
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
        "ready": True,
        "distinct_categories": 2,
        "by_category": {"avoidance": 1, "loss-aversion": 1},
    }


def test_unknown_category_is_folded_to_other(tmp_path):
    """Free-text categories never persist; they collapse to the coded 'other'."""
    data_dir = tmp_path / "store"
    out = run(["record", "--category", "some free text leak"], data_dir, threshold=5)
    assert out["by_category"] == {"other": 1}


def test_signal_is_coded_and_truncated(tmp_path):
    """Signal labels are sanitised to a short [a-z0-9-] token, not content."""
    data_dir = tmp_path / "store"
    run(["record", "--category", "avoidance", "--signal", "Skipped The Hard Call!!"], data_dir)
    db = data_dir / "coaching.db"
    assert db.exists()
    import sqlite3

    rows = sqlite3.connect(str(db)).execute("SELECT signal FROM observations").fetchall()
    assert rows == [("skipped-the-hard-call",)]


def test_default_threshold_applies_when_unset(tmp_path):
    """With no override the store uses the default coaching threshold."""
    out = run(["record", "--category", "no-experiment"], tmp_path / "store")
    assert out["threshold"] == 5


def test_invalid_threshold_falls_back_to_default(tmp_path):
    """A non-numeric or non-positive threshold degrades to the default."""
    out = run(["status"], tmp_path / "store", threshold="0")
    assert out["threshold"] == 5
    out = run(["status"], tmp_path / "store", threshold="not-a-number")
    assert out["threshold"] == 5


def test_unwritable_data_dir_degrades_gracefully(tmp_path):
    """Volatility is tolerated: an unusable store reports not-available, not error."""
    blocker = tmp_path / "blocked"
    blocker.write_text("not a directory")  # a file where a dir is expected
    out = run(["record", "--category", "avoidance"], blocker / "store")
    assert out["available"] is False
    assert out["recorded"] is False
    assert out["ready"] is False
