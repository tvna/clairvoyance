#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
plugin_root="$(cd "${script_dir}/.." && pwd)"
skill_path="${plugin_root}/skills/using-clairvoyance/SKILL.md"
project_root="${CLAUDE_PROJECT_DIR:-${CLAUDE_WORKSPACE_DIR:-${PWD:-}}}"
# The operator's native language is fixed by ONE source: the
# CLAIRVOYANCE_OPERATOR_LANGUAGE environment variable (resolved below). There is
# deliberately no git-identity lookup and no committed per-contributor mapping.
#
# Why: the previous design also keyed a COMMITTED mapping by the session's git
# identity (user.email / user.name). On a volatile host — notably Claude web —
# the git identity is rewritten to a platform-specific value, so that lookup
# matched the wrong row or no row at all and the resolved language flipped
# between runs. Fixing the language to one explicit environment variable removes
# that instability; the deliberate trade-off is that the repository no longer
# carries a visible per-contributor language signal.
#
# Two legacy on-disk sources are detected ONLY to surface a one-time migration
# hint — never applied as a value (see the resolution block below).
legacy_mapping_file="${project_root}/.clairvoyance/contributor-languages.txt"
legacy_owner_file="${project_root}/.clairvoyance/owner-language.txt"

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

# Resolve the operator's native language from a single fixed source: the
# CLAIRVOYANCE_OPERATOR_LANGUAGE environment variable, set in the operator's own
# environment configuration. No git identity is read and no committed mapping is
# consulted, so the result is stable on volatile hosts (Claude web, CI) where the
# git identity is rewritten.
#
# If the variable is unset, the language is treated as NOT recorded and the
# unrecorded branch below drives the portable question handoff. The two legacy
# on-disk/owner sources — a DEPRECATED CLAIRVOYANCE_OWNER_LANGUAGE env and the
# now-removed committed files (contributor-languages.txt, owner-language.txt) —
# are surfaced there only as one-time migration hints (move the value into
# CLAIRVOYANCE_OPERATOR_LANGUAGE), never applied as a value.
operator_language="${CLAIRVOYANCE_OPERATOR_LANGUAGE:-}"

if [ -n "${operator_language}" ]; then
  language_context="The operator's native language is '${operator_language}'. This SessionStart injection is authoritative for Clairvoyance handoffs in this session and overrides any instruction to default to a repository owner's (or any other person's) language. Write operator-facing Clairvoyance output in this language unless a repository rule requires another language for outward-facing artifacts."
else
  migration_hint=""
  if [ -n "${CLAIRVOYANCE_OWNER_LANGUAGE:-}" ]; then
    migration_hint="${migration_hint} A DEPRECATED CLAIRVOYANCE_OWNER_LANGUAGE is set; it is no longer applied — rename it to CLAIRVOYANCE_OPERATOR_LANGUAGE in your environment configuration."
  fi
  if [ -f "${legacy_mapping_file}" ] || [ -f "${legacy_owner_file}" ]; then
    migration_hint="${migration_hint} A legacy committed language file (.clairvoyance/contributor-languages.txt or owner-language.txt) is present; it is no longer applied — move the value into the CLAIRVOYANCE_OPERATOR_LANGUAGE environment variable and delete the file."
  fi
  language_context="The operator's native language is not recorded. Do NOT default to a repository owner's or any other person's language. Before any Clairvoyance handoff, use AskUserQuestion to ask the human in this session for their own native language. Use one focused, non-leading question with 2-3 choices when obvious, and write operator-facing Clairvoyance output in the answered language for this session. To make the choice durable, the operator must set CLAIRVOYANCE_OPERATOR_LANGUAGE in the environment's configuration. On Claude web and any volatile/ephemeral checkout this is an OPERATOR task that cannot be automated from inside the session, because local files do not survive the checkout — setting the environment variable is the only thing that persists.${migration_hint}"
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
