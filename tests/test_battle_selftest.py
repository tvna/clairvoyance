"""CI gate for the battle harness's offline self-check (issue #92).

``battle/run_battle.py --selftest`` is offline (no ``claude`` calls) and already
validates grading logic plus, since #92, every ``[[marker_fixtures]]`` block
that pins a scenario's ``must_not_contain`` contract. Nothing previously ran it
in CI, so a marker regex could regress (false positive or missed violation)
without any automated signal. Invoked via subprocess so battle/ -- out of this
project's ``--cov=scripts`` coverage scope -- stays out of the coverage gate.
"""

import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_battle_selftest_passes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "battle/run_battle.py"), "--selftest"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "selftest ok" in result.stdout
