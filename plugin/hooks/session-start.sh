#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
plugin_root="$(cd "${script_dir}/.." && pwd)"
skill_path="${plugin_root}/skills/using-clairvoyance/SKILL.md"
project_root="${CLAUDE_PROJECT_DIR:-${CLAUDE_WORKSPACE_DIR:-${PWD:-}}}"
# Per-contributor, git-ignored. The language tracks whoever is driving THIS
# session, not a fixed repository owner, so a multi-contributor project never
# forces one person's language on everyone. The legacy owner-scoped file is
# still read as a fallback for projects set up before this reframe.
language_file="${project_root}/.clairvoyance/operator-language.txt"
legacy_language_file="${project_root}/.clairvoyance/owner-language.txt"

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
# Resolve the active contributor's language, first match wins. The env var is
# the per-contributor authoritative source (each contributor sets it in their
# own environment); CLAIRVOYANCE_OWNER_LANGUAGE stays as a legacy alias.
operator_language="${CLAIRVOYANCE_OPERATOR_LANGUAGE:-${CLAIRVOYANCE_OWNER_LANGUAGE:-}}"

read_language_file() {
  sed -n '/[^[:space:]]/{s/^[[:space:]]*//;s/[[:space:]]*$//;p;q;}' "$1"
}

if [ -z "${operator_language}" ] && [ -f "${language_file}" ]; then
  operator_language="$(read_language_file "${language_file}")"
fi
if [ -z "${operator_language}" ] && [ -f "${legacy_language_file}" ]; then
  operator_language="$(read_language_file "${legacy_language_file}")"
fi

if [ -n "${operator_language}" ]; then
  language_context="The active contributor's native language is set to '${operator_language}'. This SessionStart injection is authoritative for Clairvoyance handoffs in this session. Write operator-facing Clairvoyance output in this language unless a repository rule requires another language for outward-facing artifacts."
else
  language_context="The active contributor's native language is not set. Before any Clairvoyance handoff, use AskUserQuestion to ask the human in this session for their own native language (the contributor driving the work, not a fixed repository owner). Use one focused, non-leading question with 2-3 choices when obvious. After the human answers, record it for this contributor — set the CLAIRVOYANCE_OPERATOR_LANGUAGE environment variable, or write '${language_file}' (git-ignored, per-contributor) with the language code or language name — then write operator-facing Clairvoyance output in that language."
fi

# Count this session toward the adaptive-coaching grace period. The hook pushes
# NO coaching: the reflection quiz fires only when the human asks to reflect
# (handled by adaptive-coaching reading the store), never from here. A missing
# store, no sqlite3, or an unwritable/ephemeral environment degrade silently
# (volatility is tolerated); reading no stdin keeps the hook from ever blocking.
store_sh="${plugin_root}/hooks/adaptive-store.sh"
if [ -f "${store_sh}" ]; then
  bash "${store_sh}" record-session >/dev/null 2>&1 || true
fi

escaped="$(escape_json "$skill_content")"
language_escaped="$(escape_json "$language_context")"
context="<EXTREMELY_IMPORTANT>\nYou have Clairvoyance.\n\n${language_escaped}\n\nBelow is the full content of your 'using-clairvoyance' bootstrap skill. For an agent-to-human handoff, use the Skill tool to load the single matching Clairvoyance skill named by the bootstrap skill before responding.\n\n${escaped}\n</EXTREMELY_IMPORTANT>"

printf '{\n  "hookSpecificOutput": {\n    "hookEventName": "SessionStart",\n    "additionalContext": "%s"\n  }\n}\n' "$context"
