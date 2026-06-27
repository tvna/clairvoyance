#!/usr/bin/env bash
# Validate the hook scripts: syntax of both, and that the SessionStart hook emits
# valid JSON for Claude Code to consume. Shared by CI and the pre-commit hook.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"

bash -n "${root}/hooks/run-hook.cmd"
bash -n "${root}/hooks/session-start.sh"
bash "${root}/hooks/session-start.sh" | python3 -m json.tool > /dev/null

echo "hooks ok"
