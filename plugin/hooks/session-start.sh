#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
plugin_root="$(cd "${script_dir}/.." && pwd)"
skill_path="${plugin_root}/skills/using-clairvoyance/SKILL.md"
project_root="${CLAUDE_PROJECT_DIR:-${CLAUDE_WORKSPACE_DIR:-${PWD:-}}}"
# A COMMITTED, per-contributor mapping of identity -> native language. The
# language tracks whoever is driving THIS session, not a fixed repository owner,
# so a multi-contributor project never forces one person's language on everyone.
# It is committed on purpose: it is the repository's signal of which native
# languages its contributors use, and it is the only per-contributor source that
# survives a volatile/ephemeral checkout (Claude web, CI) where local-only state
# is lost. Format: one `identity = language` line per contributor, keyed by git
# email (or name); `#` comments and blank lines are ignored. A legacy
# single-value owner file is detected only to surface a migration hint — never
# applied as a contributor's language (see the resolution block below).
mapping_file="${project_root}/.clairvoyance/contributor-languages.txt"
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

# Look up a language for one identity key in the committed mapping. Prints the
# language (and exits 0) on the first matching `key = language` line; prints
# nothing otherwise. Matching on the key is case-insensitive.
lookup_language() {
  local key="$1" file="$2"
  [ -n "${key}" ] && [ -f "${file}" ] || return 0
  awk -v key="${key}" '
    /^[[:space:]]*#/ { next }
    index($0, "=") == 0 { next }
    {
      k = substr($0, 1, index($0, "=") - 1)
      v = substr($0, index($0, "=") + 1)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", k)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", v)
      if (tolower(k) == tolower(key) && v != "") { print v; exit }
    }
  ' "${file}"
}

# Resolve the active contributor's language, first match wins. Every source here
# is contributor-scoped — keyed to whoever drives THIS session — so the owner's
# language is never served to a different contributor:
#   1. CLAIRVOYANCE_OPERATOR_LANGUAGE (or the deprecated CLAIRVOYANCE_OWNER_LANGUAGE
#      alias) — a per-session env override, set in the contributor's own
#      environment; survives volatile checkouts via the environment config.
#   2. The committed mapping, keyed by this session's git identity (email, then
#      name) — the durable per-contributor signal.
# A legacy single-value `owner-language.txt` is deliberately NOT used as a value
# source: it holds one person's (the owner's) language, so applying it to any
# other contributor is exactly the owner-fixation this design removes. When it is
# present it is surfaced below only as a one-time migration hint.
git_email="$(git -C "${project_root}" config user.email 2>/dev/null || true)"
git_name="$(git -C "${project_root}" config user.name 2>/dev/null || true)"

operator_language="${CLAIRVOYANCE_OPERATOR_LANGUAGE:-${CLAIRVOYANCE_OWNER_LANGUAGE:-}}"
if [ -z "${operator_language}" ]; then
  operator_language="$(lookup_language "${git_email}" "${mapping_file}")"
fi
if [ -z "${operator_language}" ]; then
  operator_language="$(lookup_language "${git_name}" "${mapping_file}")"
fi

if [ -n "${operator_language}" ]; then
  language_context="The active contributor's native language is '${operator_language}'. This SessionStart injection is authoritative for Clairvoyance handoffs in this session and overrides any instruction to default to a repository owner's (or any other person's) language. Write operator-facing Clairvoyance output in this language unless a repository rule requires another language for outward-facing artifacts."
else
  migration_hint=""
  if [ -f "${legacy_language_file}" ]; then
    migration_hint=" A legacy '${legacy_language_file}' is present; it records only one person's language and MUST NOT be reused for other contributors — migrate it into the mapping under that person's own identity."
  fi
  language_context="The active contributor's native language is not recorded. Do NOT default to a repository owner's or any other person's language. Before any Clairvoyance handoff, use AskUserQuestion to ask the human in this session for their own native language (the contributor driving the work, not a fixed repository owner). Use one focused, non-leading question with 2-3 choices when obvious. After the human answers, add a '<identity> = <language>' line to the committed mapping '${mapping_file}' (so the repository keeps a signal of its contributors' languages and the answer survives a volatile checkout), or set CLAIRVOYANCE_OPERATOR_LANGUAGE for this session, then write operator-facing Clairvoyance output in that language. The mapping is committed, so use a non-harvestable identity key — a git name or a GitHub users.noreply address, never a personal email.${migration_hint}"
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
