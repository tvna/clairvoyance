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
    """Inject a deterministic git identity via git's env-config mechanism, so
    `git config user.email/.name` returns these values regardless of any repo or
    global config the test host happens to carry."""
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
    # hook gives these precedence, so a developer/CI host that exports one would
    # otherwise mask the mapping, legacy-file, and unmapped-prompt behaviours
    # under test. A test that needs one sets it explicitly via env_overrides.
    env.pop("CLAIRVOYANCE_OPERATOR_LANGUAGE", None)
    env.pop("CLAIRVOYANCE_OWNER_LANGUAGE", None)
    # Default to a no-match identity so a test that does not set one is not
    # accidentally resolved by the host's real git config.
    env.update(_git_identity_env(email="nobody@example.invalid", name="Nobody"))
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        ["bash", str(REPO_ROOT / "plugin/hooks/session-start.sh")],
        capture_output=True,
        text=True,
        env=env,
        input="",
    )


def _write_mapping(tmp_path, body):
    lang_dir = tmp_path / ".clairvoyance"
    lang_dir.mkdir(exist_ok=True)
    (lang_dir / "contributor-languages.txt").write_text(body)


def _context(result):
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


def test_session_start_escapes_control_characters(tmp_path):
    """A control char in a mapping value must still yield valid JSON."""
    # Form feed (0x0c) is a control char a hand-rolled escaper would miss.
    _write_mapping(tmp_path, "alice@example.com = Japanese\x0c\n")
    result = _run_session_start(tmp_path, _git_identity_env(email="alice@example.com"))
    assert result.returncode == 0, result.stderr
    json.loads(result.stdout)  # raises if the hook emitted invalid JSON


def test_session_start_resolves_language_by_git_email(tmp_path):
    """The committed mapping is looked up by the session's git email."""
    _write_mapping(tmp_path, "# contributors\nalice@example.com = English\nbob@example.com = Korean\n")
    context = _context(_run_session_start(tmp_path, _git_identity_env(email="bob@example.com")))
    assert "Korean" in context
    assert "active contributor" in context


def test_session_start_email_match_is_case_insensitive(tmp_path):
    """Email keys match case-insensitively."""
    _write_mapping(tmp_path, "Alice@Example.com = English\n")
    context = _context(_run_session_start(tmp_path, _git_identity_env(email="alice@example.com")))
    assert "English" in context


def test_session_start_falls_back_to_git_name(tmp_path):
    """When the email does not match, the mapping is looked up by git name."""
    _write_mapping(tmp_path, "Carol = French\n")
    env = _git_identity_env(email="unmapped@example.com", name="Carol")
    context = _context(_run_session_start(tmp_path, env))
    assert "French" in context


def test_session_start_distinct_contributors_get_distinct_languages(tmp_path):
    """The core multi-contributor fix: each contributor resolves to their own
    language from the same committed mapping."""
    _write_mapping(tmp_path, "alice@example.com = English\nbob@example.com = Japanese\n")
    alice = _context(_run_session_start(tmp_path, _git_identity_env(email="alice@example.com")))
    bob = _context(_run_session_start(tmp_path, _git_identity_env(email="bob@example.com")))
    assert "English" in alice and "Japanese" not in alice
    assert "Japanese" in bob and "English" not in bob


def test_session_start_operator_env_overrides_mapping(tmp_path):
    """CLAIRVOYANCE_OPERATOR_LANGUAGE wins over the committed mapping."""
    _write_mapping(tmp_path, "alice@example.com = English\n")
    env = {**_git_identity_env(email="alice@example.com"), "CLAIRVOYANCE_OPERATOR_LANGUAGE": "Spanish"}
    context = _context(_run_session_start(tmp_path, env))
    assert "Spanish" in context
    assert "English" not in context


def test_session_start_does_not_apply_legacy_owner_file_to_other_contributors(tmp_path):
    """A legacy single-value owner-language file must NOT be served as the active
    contributor's language — that is the owner-fixation this design removes. It is
    surfaced only as a migration hint, and the contributor is still asked."""
    lang_dir = tmp_path / ".clairvoyance"
    lang_dir.mkdir()
    (lang_dir / "owner-language.txt").write_text("Japanese\n")
    context = _context(_run_session_start(tmp_path, _git_identity_env(email="alice@example.com")))
    assert "not recorded" in context
    assert "is set to 'Japanese'" not in context
    assert "native language is 'Japanese'" not in context
    assert "migrate it into the mapping" in context  # migration hint is surfaced


def test_session_start_legacy_owner_env_does_not_shadow_question_handoff(tmp_path):
    """Regression: a lingering legacy CLAIRVOYANCE_OWNER_LANGUAGE must NOT be
    silently served to an unmapped contributor. It is retired as a value source
    (it shadowed the SKILL.md "if missing, ask" contract); the contributor is
    asked, and the owner value is surfaced only as a migration hint."""
    context = _context(_run_session_start(tmp_path, {"CLAIRVOYANCE_OWNER_LANGUAGE": "Spanish"}))
    assert "not recorded" in context
    assert "native language is 'Spanish'" not in context
    assert "DEPRECATED CLAIRVOYANCE_OWNER_LANGUAGE" in context  # migration hint is surfaced


def test_session_start_mapping_beats_legacy_owner_env(tmp_path):
    """The legacy owner env alias is ranked BELOW the per-contributor mapping: a
    mapped contributor gets their own language even when a lingering
    CLAIRVOYANCE_OWNER_LANGUAGE from an old single-owner setup is exported."""
    _write_mapping(tmp_path, "bob@example.com = Korean\n")
    env = {**_git_identity_env(email="bob@example.com"), "CLAIRVOYANCE_OWNER_LANGUAGE": "Japanese"}
    context = _context(_run_session_start(tmp_path, env))
    assert "native language is 'Korean'" in context
    assert "Japanese" not in context


def test_session_start_prompts_for_language_when_unmapped(tmp_path):
    """With no match anywhere, the hook asks for the contributor's own language
    and points at the committed mapping with a privacy-safe identity caution —
    without echoing any real (possibly personal) identity into the message."""
    context = _context(_run_session_start(tmp_path, _git_identity_env(email="newcomer@example.com")))
    assert "not recorded" in context
    assert "contributor-languages.txt" in context
    assert "never a personal email" in context
    assert "newcomer@example.com" not in context
