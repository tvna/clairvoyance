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


def _git_identity_env(email=None, name=None):
    """Inject a deterministic git identity via git's env-config mechanism. The
    language resolution no longer reads the git identity at all; this helper
    exists only so a regression test can PROVE that — by setting an identity that
    would have matched a legacy mapping and asserting it is ignored."""
    pairs = []
    if email is not None:
        pairs.append(("user.email", email))
    if name is not None:
        pairs.append(("user.name", name))
    env = {"GIT_CONFIG_COUNT": str(len(pairs))}
    for i, (key, value) in enumerate(pairs):
        env[f"GIT_CONFIG_KEY_{i}"] = key
        env[f"GIT_CONFIG_VALUE_{i}"] = value
    return env


def _run_session_start(tmp_path, env_overrides=None):
    """Run the SessionStart hook against an isolated project + store."""
    # Redirect the store to a tmp dir (the hook records a session on each run) and
    # feed empty stdin so the hook never blocks reading a SessionStart payload.
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path), "CLAIRVOYANCE_DATA_DIR": str(tmp_path / "store")}
    # Strip any ambient language overrides from the inherited environment: the
    # hook gives CLAIRVOYANCE_OPERATOR_LANGUAGE precedence, so a developer/CI host
    # that exports one (or a lingering legacy CLAIRVOYANCE_OWNER_LANGUAGE) would
    # otherwise mask the unrecorded-path behaviour under test. A test that needs
    # one sets it explicitly via env_overrides.
    env.pop("CLAIRVOYANCE_OPERATOR_LANGUAGE", None)
    env.pop("CLAIRVOYANCE_OWNER_LANGUAGE", None)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        ["bash", str(REPO_ROOT / "hooks/session-start.sh")],
        capture_output=True,
        text=True,
        env=env,
        input="",
    )


def _write_legacy_mapping(tmp_path, body):
    lang_dir = tmp_path / ".clairvoyance"
    lang_dir.mkdir(exist_ok=True)
    (lang_dir / "contributor-languages.txt").write_text(body)


def _context(result):
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


def test_session_start_resolves_language_from_env(tmp_path):
    """The operator language is fixed by CLAIRVOYANCE_OPERATOR_LANGUAGE."""
    context = _context(_run_session_start(tmp_path, {"CLAIRVOYANCE_OPERATOR_LANGUAGE": "Japanese"}))
    assert "native language is 'Japanese'" in context
    assert "authoritative" in context


def test_session_start_escapes_control_characters(tmp_path):
    """A control char in the env value must still yield valid JSON."""
    # Form feed (0x0c) is a control char a hand-rolled escaper would miss.
    result = _run_session_start(tmp_path, {"CLAIRVOYANCE_OPERATOR_LANGUAGE": "Japanese\x0c"})
    assert result.returncode == 0, result.stderr
    json.loads(result.stdout)  # raises if the hook emitted invalid JSON


def test_session_start_ignores_git_identity_and_legacy_mapping(tmp_path):
    """The core fix: the unstable path is gone. Even with a git identity that
    exactly matches a leftover committed mapping, the language is NOT resolved
    from it — git identity is never read and the mapping is never applied."""
    _write_legacy_mapping(tmp_path, "bob@example.com = Korean\n")
    env = {**_git_identity_env(email="bob@example.com"), "CLAUDE_PROJECT_DIR": str(tmp_path)}
    context = _context(_run_session_start(tmp_path, env))
    assert "Korean" not in context
    assert "not recorded" in context


def test_session_start_prompts_and_flags_operator_task_when_unset(tmp_path):
    """With the env var unset, the hook asks for the operator's own language and
    states that persisting it is an operator task that cannot be automated on a
    volatile checkout (Claude web)."""
    context = _context(_run_session_start(tmp_path))
    assert "not recorded" in context
    assert "CLAIRVOYANCE_OPERATOR_LANGUAGE" in context
    assert "OPERATOR task that cannot be automated" in context
    assert "Claude web" in context


def test_session_start_legacy_owner_env_is_migration_hint_only(tmp_path):
    """A lingering legacy CLAIRVOYANCE_OWNER_LANGUAGE is never applied as a value;
    it is surfaced only as a rename-to-the-env-var migration hint."""
    context = _context(_run_session_start(tmp_path, {"CLAIRVOYANCE_OWNER_LANGUAGE": "Spanish"}))
    assert "not recorded" in context
    assert "native language is 'Spanish'" not in context
    assert "DEPRECATED CLAIRVOYANCE_OWNER_LANGUAGE" in context


def test_session_start_legacy_committed_file_is_migration_hint_only(tmp_path):
    """A leftover committed language file is no longer applied; it only triggers a
    migration hint to move the value into the environment variable."""
    _write_legacy_mapping(tmp_path, "Tsubasa Nagano = Japanese\n")
    context = _context(_run_session_start(tmp_path))
    assert "not recorded" in context
    assert "native language is 'Japanese'" not in context
    assert "legacy committed language file" in context
