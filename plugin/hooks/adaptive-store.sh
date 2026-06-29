#!/usr/bin/env bash
# Local, anonymous adaptive-coaching observation store.
#
# Subcommands `record` and `status` each print one JSON object on stdout and
# (apart from a missing required `--category`) always exit 0. The store is
# backed by the `sqlite3` CLI (e.g. `choco install sqlite` on Windows; usually
# present on macOS/Linux). There is no Python fallback: if the CLI is absent the
# store degrades to "not available" and coaching stays inactive, leaving the
# session unaffected.
#
# It records only coded metadata -- an adaptive-challenge category, a short
# coded signal label, a quiz outcome, the session kind, and a UTC timestamp --
# never prompt text, code, or file paths. Storage location, threshold,
# anonymity, and volatility tolerance are documented in docs/hooks.md.
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
CATEGORIES="avoidance mislabeled-technical loss-aversion values-conflict no-experiment authority-dependence other"

resolve_data_dir() {
  if [ -n "${CLAIRVOYANCE_DATA_DIR:-}" ]; then
    printf '%s' "${CLAIRVOYANCE_DATA_DIR}"
  elif [ -n "${LOCALAPPDATA:-}" ]; then
    printf '%s' "${LOCALAPPDATA}/clairvoyance"
  elif [ -n "${XDG_DATA_HOME:-}" ]; then
    printf '%s' "${XDG_DATA_HOME}/clairvoyance"
  else
    printf '%s' "${HOME}/clairvoyance"
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

unavailable_json() {
  if [ "${cmd}" = "record" ]; then
    printf '{"recorded": false, "available": false, "count": 0, "threshold": %s, "ready": false}' "${limit}"
  else
    printf '{"available": false, "count": 0, "threshold": %s, "ready": false}' "${limit}"
  fi
}

# Requires the sqlite3 CLI; with none present the store is simply unavailable.
command -v sqlite3 >/dev/null 2>&1 || emit "$(unavailable_json)"

# --- sqlite3 store -----------------------------------------------------------
data_dir="$(resolve_data_dir)"
db="${data_dir}/coaching.db"
schema="CREATE TABLE IF NOT EXISTS observations (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, category TEXT NOT NULL, signal TEXT, outcome TEXT, session_kind TEXT);"

summary_json() {
  # Echoes: <total> <distinct> <by_category-json-body> on three lines, or fails.
  local total rows pairs="" distinct=0 cat cnt
  total="$(sqlite3 -noheader "${db}" "SELECT COUNT(*) FROM observations;" 2>/dev/null)" || return 1
  rows="$(sqlite3 -noheader -separator '|' "${db}" "SELECT category, COUNT(*) FROM observations GROUP BY category ORDER BY category;" 2>/dev/null)" || return 1
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

ready_word() {
  if [ "$1" -ge "${limit}" ]; then printf 'true'; else printf 'false'; fi
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
    if ! sqlite3 "${db}" \
      "${schema} INSERT INTO observations (ts, category, signal, outcome, session_kind) VALUES ('${ts}', '${cat_value}', $(sql_value "${sig}"), $(sql_value "${outcome}"), $(sql_value "${skind}"));" \
      2>/dev/null; then
      emit "$(unavailable_json)"
    fi
    if ! out="$(summary_json)"; then emit "$(unavailable_json)"; fi
    total="$(printf '%s' "${out}" | sed -n '1p')"
    distinct="$(printf '%s' "${out}" | sed -n '2p')"
    pairs="$(printf '%s' "${out}" | sed -n '3p')"
    emit "$(printf '{"recorded": true, "available": true, "count": %s, "threshold": %s, "ready": %s, "distinct_categories": %s, "by_category": {%s}}' "${total}" "${limit}" "$(ready_word "${total}")" "${distinct}" "${pairs}")"
    ;;
  status)
    [ -f "${db}" ] || emit "$(unavailable_json)"
    sqlite3 "${db}" "${schema}" >/dev/null 2>&1 || emit "$(unavailable_json)"
    if ! out="$(summary_json)"; then emit "$(unavailable_json)"; fi
    total="$(printf '%s' "${out}" | sed -n '1p')"
    distinct="$(printf '%s' "${out}" | sed -n '2p')"
    pairs="$(printf '%s' "${out}" | sed -n '3p')"
    emit "$(printf '{"available": true, "count": %s, "threshold": %s, "ready": %s, "distinct_categories": %s, "by_category": {%s}}' "${total}" "${limit}" "$(ready_word "${total}")" "${distinct}" "${pairs}")"
    ;;
  *)
    printf 'adaptive-store.sh: unknown command %s\n' "${cmd:-<none>}" >&2
    exit 2
    ;;
esac
