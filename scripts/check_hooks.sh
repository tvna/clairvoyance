#!/usr/bin/env bash
# Validate the hook scripts: syntax of both, and that the SessionStart hook emits
# valid JSON for Claude Code to consume. Shared by CI and the pre-commit hook.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"

# `bash -n` only parses the POSIX half of run-hook.cmd; the cmd.exe batch block
# lives inside the heredoc and is verified manually / on Windows. Assert the
# polyglot structure is at least intact so a broken heredoc fails loud here.
grep -q "^CMDBLOCK$" "${root}/hooks/run-hook.cmd"
bash -n "${root}/hooks/run-hook.cmd"
bash -n "${root}/hooks/lib/json-escape.sh"
bash -n "${root}/hooks/session-start.sh"
bash -n "${root}/hooks/user-prompt-language.sh"
# Redirect the store's data dir to a throwaway path: the hook records a session
# on each run, so this keeps the check from touching the real workstation store.
hooks_tmp="$(mktemp -d)"
trap 'rm -rf "${hooks_tmp}"' EXIT
CLAIRVOYANCE_DATA_DIR="${hooks_tmp}" bash "${root}/hooks/session-start.sh" </dev/null | python3 -m json.tool > /dev/null

# UserPromptSubmit fires every turn (see issue #116) -- assert it emits valid
# JSON in both the language-set and language-unset paths.
CLAIRVOYANCE_OPERATOR_LANGUAGE="Japanese" bash "${root}/hooks/user-prompt-language.sh" </dev/null | python3 -m json.tool > /dev/null
env -u CLAIRVOYANCE_OPERATOR_LANGUAGE bash "${root}/hooks/user-prompt-language.sh" </dev/null | python3 -m json.tool > /dev/null

# The adaptive-coaching store ships alongside the hooks and is invoked by both
# session-start.sh and the skill. Syntax-check it (no side effects, no DB
# writes) so a broken store fails loud here, the same as the bash hooks.
bash -n "${root}/hooks/adaptive-store.sh"

# Both runtimes drive session-start.sh through the same run-hook.cmd wrapper; the
# only difference is the plugin-root variable each substitutes into its hooks
# manifest (Claude: CLAUDE_PLUGIN_ROOT, Codex: PLUGIN_ROOT). Assert the Codex
# manifest parses, routes through that shared wrapper with its own variable, and
# does NOT carry Claude's variable — Codex never expands ${CLAUDE_PLUGIN_ROOT},
# so it would silently break the hook. The `${PLUGIN_ROOT}` match is anchored on
# the leading `${` so it cannot be satisfied by `${CLAUDE_PLUGIN_ROOT}`.
# hooks.json (Claude Code's own manifest) must parse and must actually register
# the new per-turn hook -- this is the gate that would have caught a malformed
# or missing UserPromptSubmit registration (issue #116).
claude_hooks="${root}/hooks/hooks.json"
python3 -m json.tool "${claude_hooks}" > /dev/null
python3 -c "import json,sys; sys.exit(0 if 'UserPromptSubmit' in json.load(open('${claude_hooks}'))['hooks'] else 1)"

codex_hooks="${root}/hooks/codex-hooks.json"
python3 -m json.tool "${codex_hooks}" > /dev/null
# shellcheck disable=SC2016  # the literal ${PLUGIN_ROOT} is matched, not expanded.
grep -qF '${PLUGIN_ROOT}/hooks/run-hook.cmd' "${codex_hooks}"
if grep -qF 'CLAUDE_PLUGIN_ROOT' "${codex_hooks}"; then
  echo "check_hooks: codex-hooks.json must use \${PLUGIN_ROOT}, not \${CLAUDE_PLUGIN_ROOT}" >&2
  exit 1
fi

echo "hooks ok"
