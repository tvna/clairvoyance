#!/bin/bash
# SessionStart hook for Claude Code on the web.
#
# Installs the `sqlite3` CLI so the adaptive-coaching store and its tests work in
# remote web sessions. The store degrades gracefully without sqlite3 (coaching
# just stays inactive) and CI runners already ship it, so this hook only matters
# for the ephemeral web container. Runs synchronously: the session waits until
# sqlite3 is present, which avoids a race where a test runs before it installs.
set -euo pipefail

# Web/remote sessions only — local machines manage their own tooling.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Idempotent: the container state is cached after the first run, so once sqlite3
# is present there is nothing to do.
if command -v sqlite3 >/dev/null 2>&1; then
  exit 0
fi

# Non-interactive install. Use sudo only when not already root. Tolerate failures
# (e.g. a blocked third-party PPA index): the main repositories carry sqlite3, and
# a failed install must not break session startup — the store degrades gracefully.
export DEBIAN_FRONTEND=noninteractive
sudo_prefix=()
if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
  sudo_prefix=(sudo)
fi

"${sudo_prefix[@]}" apt-get update -qq || true
"${sudo_prefix[@]}" apt-get install -y -qq sqlite3 || true

command -v sqlite3 >/dev/null 2>&1 || echo "session-start: sqlite3 install did not succeed; adaptive-coaching store will stay inactive" >&2
exit 0
