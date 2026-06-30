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


def _run_session_start(tmp_path, env_overrides=None):
    """Run the SessionStart hook against an isolated project + store."""
    # Redirect the store to a tmp dir (the hook records a session on each run) and
    # feed empty stdin so the hook never blocks reading a SessionStart payload.
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path), "CLAIRVOYANCE_DATA_DIR": str(tmp_path / "store")}
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        ["bash", str(REPO_ROOT / "plugin/hooks/session-start.sh")],
        capture_output=True,
        text=True,
        env=env,
        input="",
    )


def test_session_start_escapes_control_characters(tmp_path):
    """A control char in the contributor-language file must still yield valid JSON."""
    lang_dir = tmp_path / ".clairvoyance"
    lang_dir.mkdir()
    # Form feed (0x0c) is a control char a hand-rolled escaper would miss.
    (lang_dir / "operator-language.txt").write_text("Japanese\x0c\n")
    result = _run_session_start(tmp_path)
    assert result.returncode == 0, result.stderr
    json.loads(result.stdout)  # raises if the hook emitted invalid JSON


def test_session_start_uses_contributor_language_file(tmp_path):
    """The per-contributor operator-language file drives the injected language."""
    lang_dir = tmp_path / ".clairvoyance"
    lang_dir.mkdir()
    (lang_dir / "operator-language.txt").write_text("Korean\n")
    result = _run_session_start(tmp_path)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert "Korean" in context
    assert "active contributor" in context


def test_session_start_reads_legacy_owner_language_file(tmp_path):
    """The legacy owner-language file is still honored for backward compatibility."""
    lang_dir = tmp_path / ".clairvoyance"
    lang_dir.mkdir()
    (lang_dir / "owner-language.txt").write_text("Japanese\n")
    result = _run_session_start(tmp_path)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "Japanese" in payload["hookSpecificOutput"]["additionalContext"]


def test_session_start_operator_env_overrides_legacy_file(tmp_path):
    """CLAIRVOYANCE_OPERATOR_LANGUAGE wins over a committed legacy file."""
    lang_dir = tmp_path / ".clairvoyance"
    lang_dir.mkdir()
    (lang_dir / "owner-language.txt").write_text("Japanese\n")
    result = _run_session_start(tmp_path, {"CLAIRVOYANCE_OPERATOR_LANGUAGE": "Spanish"})
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "Spanish" in context
    assert "Japanese" not in context
