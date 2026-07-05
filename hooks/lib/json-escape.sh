#!/usr/bin/env bash
# Shared by every hook script that needs to embed an operator-supplied string
# (env var value) inside hand-built JSON. Source this file; do not execute it.

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
