#!/usr/bin/env bash
# Local, anonymous adaptive-coaching observation store.
#
# Subcommands:
#   record --category C [--signal S] [--outcome correct|incorrect] [--confidence low|medium|high] [--calibration accurate|overconfident|underconfident|unknown] [--due-days N] [--session-kind K] [--context-stdin]
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
# By default it records only coded metadata -- an adaptive-challenge category, a
# short coded signal label, a quiz outcome, the session kind, a UTC timestamp,
# and an anonymous session count -- never prompt text, code, or file paths.
# Opt-in context capture (CLAIRVOYANCE_STORE_CONTEXT) additionally stores a
# scenario summary read from stdin via `--context-stdin` -- never an argv value,
# so the unredacted text is not exposed in process listings before redaction --
# only as detailed as a later reflection needs, and after a best-effort secret
# redaction; that scrub is a backstop, the caller is the primary redactor. The store is bounded by rotation
# (CLAIRVOYANCE_MAX_OBSERVATIONS, CLAIRVOYANCE_MAX_AGE_DAYS). Storage location,
# thresholds, anonymity, rotation, and volatility are in docs/hooks.md.
set -euo pipefail

# --- argument parsing --------------------------------------------------------
cmd="${1:-}"
category=""
signal=""
outcome=""
confidence=""
calibration=""
due_days=""
session_kind=""
context=""
context_stdin=""
i=1
while [ "$i" -lt "$#" ]; do
  i=$((i + 1))
  key="${!i}"
  case "$key" in
    --category | --signal | --outcome | --confidence | --calibration | --due-days | --session-kind)
      i=$((i + 1))
      value="${!i:-}"
      case "$key" in
        --category) category="$value" ;;
        --signal) signal="$value" ;;
        --outcome) outcome="$value" ;;
        --confidence) confidence="$value" ;;
        --calibration) calibration="$value" ;;
        --due-days) due_days="$value" ;;
        --session-kind) session_kind="$value" ;;
      esac
      ;;
    --context-stdin)
      # Boolean flag: read the raw context from stdin (see record below). Kept off
      # argv so secret-bearing text never lands in a process listing.
      context_stdin=1
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
# Rotation bounds so the local store never grows without limit. Both are
# overridable and a value of 0 disables that bound: keep the newest
# CLAIRVOYANCE_MAX_OBSERVATIONS rows, and drop rows older than
# CLAIRVOYANCE_MAX_AGE_DAYS. Defaults are generous (a long personal history) yet
# finite.
DEFAULT_MAX_OBSERVATIONS=500
DEFAULT_MAX_AGE_DAYS=180
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

resolve_max_observations() {
  # Non-negative: 0 disables the count bound; empty/non-numeric -> default.
  local raw="${CLAIRVOYANCE_MAX_OBSERVATIONS:-}"
  case "${raw}" in
    '' | *[!0-9]*) printf '%s' "${DEFAULT_MAX_OBSERVATIONS}"; return ;;
  esac
  printf '%s' "$((10#${raw}))"
}

resolve_max_age_days() {
  # Non-negative: 0 disables the age bound; empty/non-numeric -> default.
  local raw="${CLAIRVOYANCE_MAX_AGE_DAYS:-}"
  case "${raw}" in
    '' | *[!0-9]*) printf '%s' "${DEFAULT_MAX_AGE_DAYS}"; return ;;
  esac
  printf '%s' "$((10#${raw}))"
}

normalize_category() {
  case " ${CATEGORIES} " in
    *" $1 "*) printf '%s' "$1" ;;
    *) printf 'other' ;;
  esac
}

normalize_outcome() {
  case "$1" in
    correct | incorrect) printf '%s' "$1" ;;
    *) printf '' ;;
  esac
}

normalize_confidence() {
  case "$1" in
    low | medium | high) printf '%s' "$1" ;;
    *) printf '' ;;
  esac
}

normalize_calibration() {
  case "$1" in
    accurate | overconfident | underconfident | unknown) printf '%s' "$1" ;;
    '') printf '' ;;
    *) printf 'unknown' ;;
  esac
}

normalize_due_days() {
  case "$1" in
    '' | *[!0-9]*) printf '' ;;
    *) printf '%s' "$((10#$1))" ;;
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

# A SQLite string literal for arbitrary text: double every single quote so the
# value cannot break out of the literal (this is what makes storing the raw
# context string by interpolation safe). Empty -> NULL.
sql_text() {
  local v="$1"
  [ -z "${v}" ] && { printf 'NULL'; return; }
  v="${v//\'/\'\'}"
  printf "'%s'" "${v}"
}

# Context capture is opt-in and off by default; the default store stays
# coded-only. Truthy values: 1/true/yes/on (any case).
store_context_enabled() {
  case "$(printf '%s' "${CLAIRVOYANCE_STORE_CONTEXT:-}" | tr '[:upper:]' '[:lower:]')" in
    1 | true | yes | on) return 0 ;;
    *) return 1 ;;
  esac
}

# Best-effort secret scrub applied to raw context before it is stored. This is a
# BACKSTOP only -- the caller is the primary redactor -- and is deliberately
# conservative: it catches the most unambiguous secret shapes (cloud keys, JWTs,
# provider tokens, bearer headers, key=value/`key: value` secrets, and lines
# bearing a PRIVATE KEY marker). It cannot catch everything (e.g. multi-line PEM
# bodies); never rely on it as the sole defence.
redact_secrets() {
  printf '%s' "$1" | sed -E \
    -e 's/AKIA[0-9A-Z]{16}/[REDACTED]/g' \
    -e 's/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/[REDACTED]/g' \
    -e 's/(ghp|gho|ghu|ghs|ghr|github_pat|xox[baprs]|sk|pk)[_-][A-Za-z0-9_]{16,}/[REDACTED]/g' \
    -e 's@[Bb][Ee][Aa][Rr][Ee][Rr][[:space:]]+[A-Za-z0-9._~+/-]+=*@Bearer [REDACTED]@g' \
    -e 's/([Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd]|[Pp][Aa][Ss][Ss][Ww][Dd]|[Ss][Ee][Cc][Rr][Ee][Tt]|[Tt][Oo][Kk][Ee][Nn]|[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]|[Aa][Cc][Cc][Ee][Ss][Ss][_-]?[Kk][Ee][Yy])([[:space:]]*[:=][[:space:]]*)("?)[^[:space:]"]+/\1\2\3[REDACTED]/g' \
    -e 's/.*PRIVATE KEY.*/[REDACTED]/g'
}

emit() {
  printf '%s\n' "$1"
  exit 0
}

limit="$(resolve_threshold)"
session_limit="$(resolve_session_threshold)"
max_obs="$(resolve_max_observations)"
max_age="$(resolve_max_age_days)"

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
schema="CREATE TABLE IF NOT EXISTS observations (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, category TEXT NOT NULL, signal TEXT, outcome TEXT, session_kind TEXT, context TEXT, confidence TEXT, calibration TEXT, due_at TEXT); CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value INTEGER NOT NULL);"
# Wait briefly for a concurrent writer instead of failing, so simultaneous
# SessionStarts (multiple windows, compact storms) do not drop session counts.
# The `.timeout` dot-command sets the busy timeout silently; a `PRAGMA
# busy_timeout` would print its value and corrupt the captured query output.
busy_opts=(-cmd ".timeout 2000")

ensure_schema() {
  # Create the tables, then migrate stores that predate the optional raw
  # `context` column (SQLite has no ADD COLUMN IF NOT EXISTS).
  sqlite3 "${busy_opts[@]}" "${db}" "${schema}" 2>/dev/null || return 1
  # `PRAGMA table_info` works on every SQLite version (unlike the pragma_table_info
  # table-valued function); each row is `cid|name|type|...`, so a present column
  # shows up as `|context|`.
  local cols
  cols="$(sqlite3 "${busy_opts[@]}" -noheader "${db}" "PRAGMA table_info(observations);" 2>/dev/null)" || return 1
  case "${cols}" in
    *"|context|"*) : ;;
    *) sqlite3 "${busy_opts[@]}" "${db}" "ALTER TABLE observations ADD COLUMN context TEXT;" 2>/dev/null || return 1 ;;
  esac
  case "${cols}" in
    *"|confidence|"*) : ;;
    *) sqlite3 "${busy_opts[@]}" "${db}" "ALTER TABLE observations ADD COLUMN confidence TEXT;" 2>/dev/null || return 1 ;;
  esac
  case "${cols}" in
    *"|calibration|"*) : ;;
    *) sqlite3 "${busy_opts[@]}" "${db}" "ALTER TABLE observations ADD COLUMN calibration TEXT;" 2>/dev/null || return 1 ;;
  esac
  case "${cols}" in
    *"|due_at|"*) : ;;
    *) sqlite3 "${busy_opts[@]}" "${db}" "ALTER TABLE observations ADD COLUMN due_at TEXT;" 2>/dev/null || return 1 ;;
  esac
  return 0
}

prune_observations() {
  # Keep the store bounded: drop rows past the age bound, then all but the newest
  # ${max_obs}. A 0 bound is disabled. Rotation intentionally lets a since-faded
  # signal age out of the readiness count.
  if [ "${max_age}" -gt 0 ]; then
    sqlite3 "${busy_opts[@]}" "${db}" \
      "DELETE FROM observations WHERE julianday(ts) < julianday('now', '-${max_age} days');" 2>/dev/null || return 1
  fi
  if [ "${max_obs}" -gt 0 ]; then
    sqlite3 "${busy_opts[@]}" "${db}" \
      "DELETE FROM observations WHERE id NOT IN (SELECT id FROM observations ORDER BY id DESC LIMIT ${max_obs});" 2>/dev/null || return 1
  fi
  return 0
}

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
    outcome="$(normalize_outcome "${outcome}")"
    confidence="$(normalize_confidence "${confidence}")"
    calibration="$(normalize_calibration "${calibration}")"
    due_days="$(normalize_due_days "${due_days}")"
    sig="$(coded_token "${signal}")"
    skind="$(coded_token "${session_kind}")"
    ts="$(date -u +%Y-%m-%dT%H:%M:%S+00:00)"
    due_at_sql="NULL"
    if [ -n "${due_days}" ]; then
      due_at_sql="datetime('now', '+${due_days} days')"
    fi
    # Context is opt-in and is only ever stored after a best-effort secret
    # redaction; with context capture off, no scenario text is persisted at all.
    # The raw context arrives on stdin (never argv), so the unredacted text is not
    # exposed in a process listing before redaction runs.
    ctx=""
    if [ -n "${context_stdin}" ]; then
      context="$(cat)"
    fi
    if store_context_enabled && [ -n "${context}" ]; then
      ctx="$(redact_secrets "${context}")"
    fi
    ensure_schema || emit "$(unavailable_json)"
    if ! sqlite3 "${busy_opts[@]}" "${db}" \
      "INSERT INTO observations (ts, category, signal, outcome, session_kind, context, confidence, calibration, due_at) VALUES ('${ts}', '${cat_value}', $(sql_value "${sig}"), $(sql_value "${outcome}"), $(sql_value "${skind}"), $(sql_text "${ctx}"), $(sql_value "${confidence}"), $(sql_value "${calibration}"), ${due_at_sql});" \
      2>/dev/null; then
      emit "$(unavailable_json)"
    fi
    prune_observations || emit "$(unavailable_json)"
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
