import json
import os
import pathlib
import subprocess

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_check_hooks_script_passes():
    """The shared hook-validation script runs clean against the real hooks."""
    result = subprocess.run(
        ["bash", str(REPO_ROOT / "scripts/check_hooks.sh")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "hooks ok" in result.stdout


def test_session_start_escapes_control_characters(tmp_path):
    """A control char in the owner-language file must still yield valid JSON."""
    lang_dir = tmp_path / ".clairvoyance"
    lang_dir.mkdir()
    # Form feed (0x0c) is a control char a hand-rolled escaper would miss.
    (lang_dir / "owner-language.txt").write_text("Japanese\x0c\n")
    # Redirect the store to a tmp dir (the hook records a session on each run) and
    # feed empty stdin so the hook never blocks reading a SessionStart payload.
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path), "CLAIRVOYANCE_DATA_DIR": str(tmp_path / "store")}
    result = subprocess.run(
        ["bash", str(REPO_ROOT / "plugin/hooks/session-start.sh")],
        capture_output=True,
        text=True,
        env=env,
        input="",
    )
    assert result.returncode == 0, result.stderr
    json.loads(result.stdout)  # raises if the hook emitted invalid JSON
