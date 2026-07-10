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

# UserPromptSubmit fires every turn (see issue #116). Assert the output SHAPE, not
# just JSON validity: Claude Code reads the per-turn context from
# hookSpecificOutput.additionalContext alongside hookEventName == "UserPromptSubmit"
# (issue #119), so a top-level-only additionalContext parses as valid JSON yet is
# silently ignored at runtime. Check both the language-set and language-unset paths.
# Use an explicit sys.exit rather than `assert`: assertions are stripped under
# `python3 -O` / PYTHONOPTIMIZE, which would silently turn this durable gate back
# into a no-op -- the exact "green gate, wrong shape" failure this check exists to
# prevent. A missing hookSpecificOutput wrapper raises KeyError (non-zero) too.
CLAIRVOYANCE_OPERATOR_LANGUAGE="Japanese" bash "${root}/hooks/user-prompt-language.sh" </dev/null \
  | python3 -c "import json,sys; h=json.load(sys.stdin)['hookSpecificOutput']; sys.exit(0 if h.get('hookEventName')=='UserPromptSubmit' and h.get('additionalContext') else 1)"
env -u CLAIRVOYANCE_OPERATOR_LANGUAGE bash "${root}/hooks/user-prompt-language.sh" </dev/null \
  | python3 -c "import json,sys; h=json.load(sys.stdin)['hookSpecificOutput']; sys.exit(0 if h.get('hookEventName')=='UserPromptSubmit' and h.get('additionalContext') else 1)"

# The adaptive-coaching store ships alongside the hooks and is invoked by both
# session-start.sh and the skill. Syntax-check it (no side effects, no DB
# writes) so a broken store fails loud here, the same as the bash hooks.
bash -n "${root}/hooks/adaptive-store.sh"

# The workflow-budget gate (PreToolUse on the Workflow tool, issue #132) must
# deny an agent-spawning launch that carries no budget evidence, and stay
# silent for zero-agent scripts and properly budgeted launches. Deny is
# asserted on the nested hookSpecificOutput.permissionDecision shape (same
# lesson as issue #119: a top-level decision parses as JSON yet is silently
# ignored at runtime).
bash -n "${root}/hooks/workflow-budget-gate.sh"
printf '%s' '{"tool_name":"Workflow","tool_input":{"script":"const r = await agent(\"x\")","args":{}}}' \
  | bash "${root}/hooks/workflow-budget-gate.sh" \
  | python3 -c "import json,sys; h=json.load(sys.stdin)['hookSpecificOutput']; sys.exit(0 if h.get('hookEventName')=='PreToolUse' and h.get('permissionDecision')=='deny' and h.get('permissionDecisionReason') else 1)"
out="$(printf '%s' '{"tool_name":"Workflow","tool_input":{"script":"return {t: budget.total}"}}' | bash "${root}/hooks/workflow-budget-gate.sh")"
if [ -n "${out}" ]; then
  echo "check_hooks: budget gate must stay silent for zero-agent scripts" >&2
  exit 1
fi
out="$(printf '%s' '{"tool_name":"Workflow","tool_input":{"script":"if (budget.spent() < args.budgetTokens) { await agent(\"x\") }","args":{"budgetTokens":100000}}}' | bash "${root}/hooks/workflow-budget-gate.sh")"
if [ -n "${out}" ]; then
  echo "check_hooks: budget gate must stay silent for a budgeted launch" >&2
  exit 1
fi
out="$(printf '%s' '{"tool_name":"Workflow","tool_input":{"name":"saved-workflow","args":{"budgetTokens":50000}}}' | bash "${root}/hooks/workflow-budget-gate.sh")"
if [ -n "${out}" ]; then
  echo "check_hooks: budget gate must accept a named workflow carrying args.budgetTokens" >&2
  exit 1
fi
# Telemetry-only spend calls are not enforcement (PR #133 review): a script
# that merely logs budget.spent() while spawning agents must still be denied,
# even with args.budgetTokens set.
printf '%s' '{"tool_name":"Workflow","tool_input":{"script":"log(budget.spent()); await agent(\"x\")","args":{"budgetTokens":100000}}}' \
  | bash "${root}/hooks/workflow-budget-gate.sh" \
  | python3 -c "import json,sys; h=json.load(sys.stdin)['hookSpecificOutput']; sys.exit(0 if h.get('permissionDecision')=='deny' else 1)"
# scriptPath outranks an inline script on the Workflow tool (PR #133 review):
# a stale harmless inline script must not mask an agent-spawning file.
printf 'await agent("x")\n' > "${hooks_tmp}/wf.js"
printf '{"tool_name":"Workflow","tool_input":{"script":"return 1","scriptPath":"%s","args":{}}}' "${hooks_tmp}/wf.js" \
  | bash "${root}/hooks/workflow-budget-gate.sh" \
  | python3 -c "import json,sys; h=json.load(sys.stdin)['hookSpecificOutput']; sys.exit(0 if h.get('permissionDecision')=='deny' else 1)"

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
# ... and the budget gate's PreToolUse registration (issue #132), same rationale.
python3 -c "import json,sys; sys.exit(0 if 'PreToolUse' in json.load(open('${claude_hooks}'))['hooks'] else 1)"

codex_hooks="${root}/hooks/codex-hooks.json"
python3 -m json.tool "${codex_hooks}" > /dev/null
# shellcheck disable=SC2016  # the literal ${PLUGIN_ROOT} is matched, not expanded.
grep -qF '${PLUGIN_ROOT}/hooks/run-hook.cmd' "${codex_hooks}"
if grep -qF 'CLAUDE_PLUGIN_ROOT' "${codex_hooks}"; then
  echo "check_hooks: codex-hooks.json must use \${PLUGIN_ROOT}, not \${CLAUDE_PLUGIN_ROOT}" >&2
  exit 1
fi

echo "hooks ok"
