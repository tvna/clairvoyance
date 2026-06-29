#!/usr/bin/env bash
# Validate the hook scripts: syntax of both, and that the SessionStart hook emits
# valid JSON for Claude Code to consume. Shared by CI and the pre-commit hook.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"

# `bash -n` only parses the POSIX half of run-hook.cmd; the cmd.exe batch block
# lives inside the heredoc and is verified manually / on Windows. Assert the
# polyglot structure is at least intact so a broken heredoc fails loud here.
grep -q "^CMDBLOCK$" "${root}/plugin/hooks/run-hook.cmd"
bash -n "${root}/plugin/hooks/run-hook.cmd"
bash -n "${root}/plugin/hooks/session-start.sh"
bash "${root}/plugin/hooks/session-start.sh" | python3 -m json.tool > /dev/null

# The adaptive-coaching store ships alongside the hooks and is invoked by both
# session-start.sh and the skill. Parse it for syntax without side effects (no
# DB writes) so a broken store fails loud here, the same as the bash hooks.
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('${root}/plugin/hooks/adaptive-store.py').read_text())"

# Both runtimes drive session-start.sh through the same run-hook.cmd wrapper; the
# only difference is the plugin-root variable each substitutes into its hooks
# manifest (Claude: CLAUDE_PLUGIN_ROOT, Codex: PLUGIN_ROOT). Assert the Codex
# manifest parses, routes through that shared wrapper with its own variable, and
# does NOT carry Claude's variable — Codex never expands ${CLAUDE_PLUGIN_ROOT},
# so it would silently break the hook. The `${PLUGIN_ROOT}` match is anchored on
# the leading `${` so it cannot be satisfied by `${CLAUDE_PLUGIN_ROOT}`.
codex_hooks="${root}/plugin/hooks/codex-hooks.json"
python3 -m json.tool "${codex_hooks}" > /dev/null
# shellcheck disable=SC2016  # the literal ${PLUGIN_ROOT} is matched, not expanded.
grep -qF '${PLUGIN_ROOT}/hooks/run-hook.cmd' "${codex_hooks}"
if grep -qF 'CLAUDE_PLUGIN_ROOT' "${codex_hooks}"; then
  echo "check_hooks: codex-hooks.json must use \${PLUGIN_ROOT}, not \${CLAUDE_PLUGIN_ROOT}" >&2
  exit 1
fi

echo "hooks ok"
