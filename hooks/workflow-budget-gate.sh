#!/usr/bin/env bash
set -euo pipefail

# PreToolUse gate for the Workflow tool: a multi-agent launch must carry its
# budget. Motivated by rate-limit incidents where agent fan-outs exhausted the
# account's session window mid-run with no pre-launch budget decision (#132).
# This is the deterministic half of the discipline; the elicitation shape
# (estimate, prepared choices, recommendation) lives in
# skills/workflow-budget/SKILL.md.
#
# Contract (deny-only; the gate never auto-approves):
#   - a script that spawns no agents passes untouched (zero-agent probes);
#   - a script that calls agent() passes only when the launch carries BOTH
#     args.budgetTokens (positive integer) and a budget.spent()/remaining()
#     guard in the script text;
#   - a named workflow, whose script text is not inspectable, passes on
#     args.budgetTokens alone.
#
# Degrades OPEN: without python3, or on unparseable input, the gate allows -
# matching run-hook.cmd's no-bash degradation. A broken gate must not brick
# every workflow launch on a minimal system.
#
# The payload is read from stdin by the python child directly, so the code is
# passed via -c (a heredoc on `python3 -` would consume stdin as the program
# and leave json.load nothing to read).

command -v python3 >/dev/null 2>&1 || exit 0

exec python3 -c '
import json
import re
import sys

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)  # unparseable input: fail open

if payload.get("tool_name") != "Workflow":
    sys.exit(0)

tool_input = payload.get("tool_input") or {}
script = tool_input.get("script") or ""
script_path = tool_input.get("scriptPath") or ""
if not script and script_path:
    try:
        with open(script_path, encoding="utf-8") as fh:
            script = fh.read()
    except OSError:
        script = ""

# None = script text not inspectable (named workflow / unreadable path).
spawns_agents = bool(re.search(r"\bagent\s*\(", script)) if script else None
if spawns_agents is False:
    sys.exit(0)  # zero-agent script: nothing to budget

args = tool_input.get("args")
budget_tokens = args.get("budgetTokens") if isinstance(args, dict) else None
has_budget_args = (
    isinstance(budget_tokens, int)
    and not isinstance(budget_tokens, bool)
    and budget_tokens > 0
)
has_guard = bool(re.search(r"budget\s*\.\s*(spent|remaining)\s*\(", script))

if spawns_agents is None and has_budget_args:
    sys.exit(0)
if spawns_agents and has_budget_args and has_guard:
    sys.exit(0)

reason = (
    "Budget gate: this Workflow launch spawns agents but carries no enforced "
    "token budget. Run the workflow-budget skill first: estimate the cost, "
    "offer the human 2-3 prepared budgets via AskUserQuestion, then relaunch "
    "with args.budgetTokens set and a budget.spent() guard in the script "
    "(checked before each phase/batch, fleets scaled from the cap)."
)
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }
}))
sys.exit(0)
'
