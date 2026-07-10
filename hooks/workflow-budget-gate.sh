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
#     args.budgetTokens (positive integer) and a spend COMPARISON in the
#     script text - budget.spent()/budget.remaining() compared with a
#     relational operator against the cap. A telemetry-only call such as
#     log(budget.spent()) is not enforcement and does not count;
#   - scriptPath takes precedence over an inline script (mirroring the
#     Workflow tool), so classification reads the text the harness will
#     actually execute; an unreadable scriptPath is treated as
#     not-inspectable, never as the stale inline script;
#   - a launch whose script text is not inspectable (named workflow or
#     unreadable scriptPath) passes on args.budgetTokens alone.
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
inline_script = tool_input.get("script") or ""
script_path = tool_input.get("scriptPath") or ""

# scriptPath outranks script and name on the Workflow tool, so the text the
# harness executes is the file, not the inline field. Never fall back to a
# stale inline script when a scriptPath is present: if the file cannot be
# read, the launch is not-inspectable and must carry args.budgetTokens.
script = ""
if script_path:
    try:
        with open(script_path, encoding="utf-8") as fh:
            script = fh.read()
    except OSError:
        script = ""
else:
    script = inline_script

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

# Enforcement evidence is a spend COMPARISON, not a spend mention: the call
# must sit next to a relational operator (either side), as in
# budget.spent() < args.budgetTokens or budget.remaining() > 50_000.
# log(budget.spent()) alone is telemetry and does not satisfy the gate.
spend_call = r"budget\s*\.\s*(spent|remaining)\s*\(\s*\)"
has_guard = bool(
    re.search(spend_call + r"\s*[<>]=?", script)
    or re.search(r"[<>]=?\s*" + spend_call, script)
)

if spawns_agents is None and has_budget_args:
    sys.exit(0)
if spawns_agents and has_budget_args and has_guard:
    sys.exit(0)

reason = (
    "Budget gate: this Workflow launch spawns agents but carries no enforced "
    "token budget. Run the workflow-budget skill first: estimate the cost, "
    "offer the human 2-3 prepared budgets via AskUserQuestion, then relaunch "
    "with args.budgetTokens set and a spend comparison in the script, e.g. "
    "if (budget.spent() < args.budgetTokens) - checked before each "
    "phase/batch, fleets scaled from the cap. A log(budget.spent()) call "
    "alone is telemetry, not enforcement."
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
