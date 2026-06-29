#!/usr/bin/env bash
# Local, anonymous adaptive-coaching observation store.
#
# Subcommands:
#   record --category C [--signal S] [--outcome correct|incorrect] [--session-kind K]
#   record-session   -- count one chat session toward the grace period
#   status           -- report counts and whether coaching should trigger
# Each prints one JSON object on stdout and (apart from a missing required
# `--category` on `record`) always exits 0.
#
# Coaching is gated on two counters so a first-time user is never quizzed early:
#   1. a grace period -- the first ~50 chat sessions (CLAIRVOYANCE_SESSION_THRESHOLD)
#      record no coaching, and
#   2. accumulated adaptive signal (CLAIRVOYANCE_COACH_THRESHOLD observations).
# `ready` is true only once BOTH thresholds are met.
#
# The store is backed by the `sqlite3` CLI (e.g. `choco install sqlite` on
# Windows; usually present on macOS/Linux). There is no Python fallback: if the
# CLI is absent the store degrades to "not available" and coaching stays
# inactive, leaving the session unaffected.
#
# It records only coded metadata -- an adaptive-challenge category, a short
# coded signal label, a quiz outcome, the session kind, a UTC timestamp, and an
# anonymous session count -- never prompt text, code, or file paths. Storage
# location, thresholds, anonymity, and volatility tolerance are in docs/hooks.md.
set -euo pipefail

# --- argument parsing --------------------------------------------------------
cmd="${1:-}"
category=""
signal=""
outcome=""
session_kind=""
i=1
while [ "$i" -lt "$#" ]; do
  i=$((i + 1))
  key="${!i}"
  case "$key" in
    --category | --signal | --outcome | --session-kind)
      i=$((i + 1))
      value="${!i:-}"
      case "$key" in
        --category) category="$value" ;;
        --signal) signal="$value" ;;
        --outcome) outcome="$value" ;;
        --session-kind) session_kind="$value" ;;
      esac
      ;;
  esac
done

# Five observations is the smallest sample that reads as a repeated pattern
# rather than a one-off; override per operator with $CLAIRVOYANCE_COACH_THRESHOLD.
DEFAULT_THRESHOLD=5
# Fifty chat sessions is the grace period: a first-time user (the core target,
# who may not self-set-up the environment) is never quizzed during their first
# ~50 sessions. Override with $CLAIRVOYANCE_SESSION_THRESHOLD (0 disables it).
DEFAULT_SESSION_THRESHOLD=50
CATEGORIES="avoidance mislabeled-technical loss-aversion values-conflict no-experiment authority-dependence other"

resolve_data_dir() {
  if [ -n "${CLAIRVOYANCE_DATA_DIR:-}" ]; then
    printf '%s' "${CLAIRVOYANCE_DATA_DIR}"
  elif [ -n "${LOCALAPPDATA:-}" ]; then
    printf '%s' "${LOCALAPPDATA}/clairvoyance"
  elif [ -n "${XDG_DATA_HOME:-}" ]; then
    printf '%s' "${XDG_DATA_HOME}/clairvoyance"
  else
    printf '%s' "${HOME}/.clairvoyance"
  fi
}

resolve_threshold() {
  local raw="${CLAIRVOYANCE_COACH_THRESHOLD:-}"
  case "${raw}" in
    '' | *[!0-9]*) printf '%s' "${DEFAULT_THRESHOLD}"; return ;;
  esac
  local value=$((10#${raw}))
  if [ "${value}" -gt 0 ]; then printf '%s' "${value}"; else printf '%s' "${DEFAULT_THRESHOLD}"; fi
}

resolve_session_threshold() {
  # Non-negative: 0 is a valid "no grace period" setting; empty/non-numeric -> default.
  local raw="${CLAIRVOYANCE_SESSION_THRESHOLD:-}"
  case "${raw}" in
    '' | *[!0-9]*) printf '%s' "${DEFAULT_SESSION_THRESHOLD}"; return ;;
  esac
  printf '%s' "$((10#${raw}))"
}

normalize_category() {
  case " ${CATEGORIES} " in
    *" $1 "*) printf '%s' "$1" ;;
    *) printf 'other' ;;
  esac
}

# Coerce a label to a short, anonymous, coded token: lowercase, every character
# outside [a-z0-9-] becomes '-', truncate to 40, strip outer hyphens. This is
# what guarantees no free-text content (and no SQL quote character) can reach
# the store, which is why direct SQL interpolation below is safe.
coded_token() {
  local raw="$1" s
  [ -z "${raw}" ] && return 0
  s="$(printf '%s' "${raw}" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9-' '-')"
  s="${s:0:40}"
  s="${s#"${s%%[!-]*}"}"
  s="${s%"${s##*[!-]}"}"
  printf '%s' "${s}"
}

sql_value() {
  if [ -z "$1" ]; then printf 'NULL'; else printf "'%s'" "$1"; fi
}

emit() {
  printf '%s\n' "$1"
  exit 0
}

limit="$(resolve_threshold)"
session_limit="$(resolve_session_threshold)"

unavailable_json() {
  case "${cmd}" in
    record) printf '{"recorded": false, "available": false, "count": 0, "threshold": %s, "ready": false}' "${limit}" ;;
    record-session) printf '{"recorded_session": false, "available": false, "sessions": 0, "session_threshold": %s}' "${session_limit}" ;;
    *) printf '{"available": false, "count": 0, "threshold": %s, "sessions": 0, "session_threshold": %s, "ready": false}' "${limit}" "${session_limit}" ;;
  esac
}

# Requires the sqlite3 CLI; with none present the store is simply unavailable.
command -v sqlite3 >/dev/null 2>&1 || emit "$(unavailable_json)"

# --- sqlite3 store -----------------------------------------------------------
data_dir="$(resolve_data_dir)"
db="${data_dir}/coaching.db"
schema="CREATE TABLE IF NOT EXISTS observations (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, category TEXT NOT NULL, signal TEXT, outcome TEXT, session_kind TEXT); CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value INTEGER NOT NULL);"
# Wait briefly for a concurrent writer instead of failing, so simultaneous
# SessionStarts (multiple windows, compact storms) do not drop session counts.
# The `.timeout` dot-command sets the busy timeout silently; a `PRAGMA
# busy_timeout` would print its value and corrupt the captured query output.
busy_opts=(-cmd ".timeout 2000")

summary_json() {
  # Echoes: <total> <distinct> <by_category-json-body> on three lines, or fails.
  local total rows pairs="" distinct=0 cat cnt
  total="$(sqlite3 "${busy_opts[@]}" -noheader "${db}" "SELECT COUNT(*) FROM observations;" 2>/dev/null)" || return 1
  rows="$(sqlite3 "${busy_opts[@]}" -noheader -separator '|' "${db}" "SELECT category, COUNT(*) FROM observations GROUP BY category ORDER BY category;" 2>/dev/null)" || return 1
  while IFS='|' read -r cat cnt; do
    [ -z "${cat}" ] && continue
    [ -n "${pairs}" ] && pairs="${pairs}, "
    pairs="${pairs}\"${cat}\": ${cnt}"
    distinct=$((distinct + 1))
  done <<EOF
${rows}
EOF
  printf '%s\n%s\n%s\n' "${total}" "${distinct}" "${pairs}"
}

read_sessions() {
  # The accumulated session count, or 0 if unset/unreadable.
  local v
  v="$(sqlite3 "${busy_opts[@]}" -noheader "${db}" "SELECT value FROM meta WHERE key='sessions';" 2>/dev/null)" || { printf '0'; return 0; }
  [ -z "${v}" ] && v=0
  printf '%s' "${v}"
}

combined_ready() {
  # $1 = observation total, $2 = session count. Both gates must pass.
  if [ "$1" -ge "${limit}" ] && [ "$2" -ge "${session_limit}" ]; then printf 'true'; else printf 'false'; fi
}

case "${cmd}" in
  record)
    # --category is required: every observation row carries a category
    # (schema: category TEXT NOT NULL). Reject an outcome-only record (exit 2,
    # nothing written) rather than silently storing it as 'other'.
    if [ -z "${category}" ]; then
      printf 'adaptive-store.sh: record requires --category\n' >&2
      exit 2
    fi
    mkdir -p "${data_dir}" 2>/dev/null || emit "$(unavailable_json)"
    cat_value="$(normalize_category "${category}")"
    case "${outcome}" in
      correct | incorrect) : ;;
      *) outcome="" ;;
    esac
    sig="$(coded_token "${signal}")"
    skind="$(coded_token "${session_kind}")"
    ts="$(date -u +%Y-%m-%dT%H:%M:%S+00:00)"
    if ! sqlite3 "${busy_opts[@]}" "${db}" \
      "${schema} INSERT INTO observations (ts, category, signal, outcome, session_kind) VALUES ('${ts}', '${cat_value}', $(sql_value "${sig}"), $(sql_value "${outcome}"), $(sql_value "${skind}"));" \
      2>/dev/null; then
      emit "$(unavailable_json)"
    fi
    if ! out="$(summary_json)"; then emit "$(unavailable_json)"; fi
    total="$(printf '%s' "${out}" | sed -n '1p')"
    distinct="$(printf '%s' "${out}" | sed -n '2p')"
    pairs="$(printf '%s' "${out}" | sed -n '3p')"
    sessions="$(read_sessions)"
    emit "$(printf '{"recorded": true, "available": true, "count": %s, "threshold": %s, "sessions": %s, "session_threshold": %s, "ready": %s, "distinct_categories": %s, "by_category": {%s}}' "${total}" "${limit}" "${sessions}" "${session_limit}" "$(combined_ready "${total}" "${sessions}")" "${distinct}" "${pairs}")"
    ;;
  record-session)
    mkdir -p "${data_dir}" 2>/dev/null || emit "$(unavailable_json)"
    # Portable increment (INSERT OR IGNORE then UPDATE) so it works on sqlite
    # before 3.24, which lacks UPSERT's ON CONFLICT ... DO UPDATE.
    if ! sqlite3 "${busy_opts[@]}" "${db}" \
      "${schema} INSERT OR IGNORE INTO meta (key, value) VALUES ('sessions', 0); UPDATE meta SET value = value + 1 WHERE key = 'sessions';" \
      2>/dev/null; then
      emit "$(unavailable_json)"
    fi
    sessions="$(read_sessions)"
    emit "$(printf '{"recorded_session": true, "available": true, "sessions": %s, "session_threshold": %s}' "${sessions}" "${session_limit}")"
    ;;
  status)
    [ -f "${db}" ] || emit "$(unavailable_json)"
    sqlite3 "${busy_opts[@]}" "${db}" "${schema}" >/dev/null 2>&1 || emit "$(unavailable_json)"
    if ! out="$(summary_json)"; then emit "$(unavailable_json)"; fi
    total="$(printf '%s' "${out}" | sed -n '1p')"
    distinct="$(printf '%s' "${out}" | sed -n '2p')"
    pairs="$(printf '%s' "${out}" | sed -n '3p')"
    sessions="$(read_sessions)"
    emit "$(printf '{"available": true, "count": %s, "threshold": %s, "sessions": %s, "session_threshold": %s, "ready": %s, "distinct_categories": %s, "by_category": {%s}}' "${total}" "${limit}" "${sessions}" "${session_limit}" "$(combined_ready "${total}" "${sessions}")" "${distinct}" "${pairs}")"
    ;;
  *)
    printf 'adaptive-store.sh: unknown command %s\n' "${cmd:-<none>}" >&2
    exit 2
    ;;
esac
