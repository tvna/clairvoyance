#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/json-escape.sh
source "${script_dir}/lib/json-escape.sh"

# Re-asserts the operator-language rule on EVERY turn. SessionStart
# (session-start.sh) injects the full onboarding context once, at session
# start/clear/compact; a long, tool-call-heavy session was observed to drift
# back into English for brief in-progress status narration well after that one
# injection, even though the final line of each turn stayed correct (issue
# #116). UserPromptSubmit fires fresh on every turn and cannot decay the way a
# single SessionStart injection can across many turns or a compaction, so this
# hook is deliberately cheap: no skill-file reload, no store write, just the
# same single-source language lookup session-start.sh uses.
operator_language="${CLAIRVOYANCE_OPERATOR_LANGUAGE:-}"

if [ -n "${operator_language}" ]; then
  reminder="Operator language reminder: continue writing EVERY operator-facing string this turn in '${operator_language}' -- prose, section headings, brief in-progress status lines, and AskUserQuestion text alike. Do not drift into English for intermediate status updates just because surrounding code, commands, or tool output is in English."
else
  reminder="Operator language reminder: if this session already established the operator's native language (e.g. via SessionStart's AskUserQuestion handoff), continue writing EVERY operator-facing string this turn in that language -- prose, section headings, brief in-progress status lines, and AskUserQuestion text alike. Do not drift into English for intermediate status updates."
fi

escaped="$(escape_json "$reminder")"
printf '{\n  "additionalContext": "%s"\n}\n' "$escaped"
