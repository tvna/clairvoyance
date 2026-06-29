#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
plugin_root="$(cd "${script_dir}/.." && pwd)"
skill_path="${plugin_root}/skills/using-clairvoyance/SKILL.md"
project_root="${CLAUDE_PROJECT_DIR:-${CLAUDE_WORKSPACE_DIR:-${PWD:-}}}"
language_file="${project_root}/.clairvoyance/owner-language.txt"

if [ ! -f "${skill_path}" ]; then
  exit 0
fi

escape_json() {
  local value="$1"
  # Prefer python3 for a complete JSON string encode (handles every control
  # character, e.g. form feed / backspace, that a hand-rolled escaper misses).
  if command -v python3 >/dev/null 2>&1; then
    printf '%s' "$value" | python3 -c 'import json,sys; sys.stdout.write(json.dumps(sys.stdin.read())[1:-1])'
    return
  fi
  # Fallback (no python3): best-effort escaping. Backslash first, then quotes
  # and the named control characters.
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  value="${value//$'\r'/\\r}"
  value="${value//$'\t'/\\t}"
  value="${value//$'\b'/\\b}"
  value="${value//$'\f'/\\f}"
  printf '%s' "$value"
}

skill_content="$(cat "${skill_path}")"
owner_language="${CLAIRVOYANCE_OWNER_LANGUAGE:-}"

if [ -z "${owner_language}" ] && [ -f "${language_file}" ]; then
  owner_language="$(sed -n '/[^[:space:]]/{s/^[[:space:]]*//;s/[[:space:]]*$//;p;q;}' "${language_file}")"
fi

if [ -n "${owner_language}" ]; then
  language_context="Owner native language metadata is set to '${owner_language}'. This SessionStart injection is authoritative for Clairvoyance handoffs. Write operator-facing Clairvoyance output in this language unless a repository rule requires another language for outward-facing artifacts."
else
  language_context="Owner native language metadata is missing. Before any Clairvoyance handoff, use AskUserQuestion to ask the human for the primary project owner's native language. Use one focused, non-leading question with 2-3 choices when obvious. After the human answers, set up '${language_file}' with the language code or language name, then write operator-facing Clairvoyance output in that language."
fi

# Surface adaptive-coaching readiness from the local, anonymous observation
# store. The store (adaptive-store.sh) uses the sqlite3 CLI, falling back to
# python3, so this cue needs neither here: readiness is detected from the JSON
# with a shell glob. A missing store, no backend, or an unwritable/ephemeral
# environment all degrade silently to no cue (volatility is tolerated).
coaching_block=""
store_sh="${plugin_root}/hooks/adaptive-store.sh"
if [ -f "${store_sh}" ]; then
  # Count this SessionStart (startup/clear/compact) toward the grace period, then
  # read readiness. Reading no stdin keeps the hook from ever blocking.
  bash "${store_sh}" record-session >/dev/null 2>&1 || true
  status_json="$(bash "${store_sh}" status 2>/dev/null || true)"
  case "${status_json}" in
    *'"ready": true'*)
      coaching_context="Adaptive-coaching signal has reached its threshold on this workstation. Before the next agent-to-human handoff, load 'clairvoyance:adaptive-coaching', classify the technical versus adaptive split, and deliver a prosthesis-building AskUserQuestion quiz that corrects the person's adaptive challenge."
      coaching_block="\n\n$(escape_json "$coaching_context")"
      ;;
  esac
fi

escaped="$(escape_json "$skill_content")"
language_escaped="$(escape_json "$language_context")"
context="<EXTREMELY_IMPORTANT>\nYou have Clairvoyance.\n\n${language_escaped}${coaching_block}\n\nBelow is the full content of your 'using-clairvoyance' bootstrap skill. For an agent-to-human handoff, use the Skill tool to load the single matching Clairvoyance skill named by the bootstrap skill before responding.\n\n${escaped}\n</EXTREMELY_IMPORTANT>"

printf '{\n  "hookSpecificOutput": {\n    "hookEventName": "SessionStart",\n    "additionalContext": "%s"\n  }\n}\n' "$context"
