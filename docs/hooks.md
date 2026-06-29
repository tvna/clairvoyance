# Hooks

## SessionStart injection

`plugin/hooks/hooks.json` registers one `SessionStart` hook (matching `startup`, `clear`,
and `compact`). It runs `plugin/hooks/session-start.sh`, which:

1. Reads `plugin/skills/using-clairvoyance/SKILL.md` and injects it as
   `additionalContext` so the agent has the bootstrap router from the first turn.
2. Resolves the project owner's language and injects it as authoritative for
   Clairvoyance handoffs.
3. Queries the adaptive-coaching store (below) and, only when it reports `ready`,
   appends a cue telling the agent to load `adaptive-coaching` for the next handoff.

If the bootstrap skill file is missing, the hook exits 0 and injects nothing.

## Adaptive-coaching store

`plugin/hooks/adaptive-store.sh` is the store entry point: a CLI that persists a
small, **anonymous** record of adaptive-challenge observations on the operator's own
workstation, so `adaptive-coaching` waits until enough signal has accumulated before
it coaches. It stores only coded metadata — an adaptive-challenge category, a short
coded signal label, a quiz outcome, the session kind, and a UTC timestamp — never
prompt text, code, or file paths.

- **Subcommands.** `record --category <c> [--signal …] [--outcome correct|incorrect]
  [--session-kind …]` appends one observation; `status` reports the count and whether
  it is `ready`. Both print one JSON object and always exit 0.
- **Location** (first match wins): `$CLAIRVOYANCE_DATA_DIR`, else
  `%LOCALAPPDATA%\clairvoyance` (the Windows workstation default), else
  `$XDG_DATA_HOME/clairvoyance`, else `~/.clairvoyance`; the file is `coaching.db`.
- **Threshold.** `$CLAIRVOYANCE_COACH_THRESHOLD` (default 5).
- **Volatility is tolerated.** Ephemeral or read-only environments (remote sessions,
  sandboxes) simply do not persist, and any storage error degrades to
  "not available / not ready" rather than failing the session.

### Backends (SQLite, no Python required)

The store keeps a SQLite database but does **not** require Python. Two
interchangeable backends sit behind `adaptive-store.sh`, selected by
`$CLAIRVOYANCE_STORE_BACKEND` (default `auto`):

- **`sqlite3` CLI (primary)** — install with `choco install sqlite` on Windows
  (Git for Windows bundles no `sqlite3`); on macOS/Linux it is usually present.
- **`python3` stdlib `sqlite3` (fallback)** — used when the CLI is absent.
- **`auto`** picks the CLI if present, else `python3`, else degrades to
  "not available" (coaching simply stays inactive; the session is unaffected).

Both backends read and write the same `coaching.db` and emit byte-identical JSON;
`tests/test_adaptive_store.py` runs every behavioural case against both and asserts
their equivalence so they cannot drift. `session-start.sh` detects readiness from the
store's JSON with a shell glob, so the readiness cue itself needs neither runtime.

`scripts/check_hooks.sh` syntax-checks both `adaptive-store.sh` (`bash -n`) and the
`adaptive-store.py` fallback (no side effects).

### Codex

Codex reads its own `SessionStart` manifest, `plugin/hooks/codex-hooks.json`
(pointed at by `plugin/.codex-plugin/plugin.json`). It matches the same events
(plus Codex's `resume`) and drives the **same** `session-start.sh` through the
**same** `run-hook.cmd` wrapper. The only difference is the plugin-root variable:
Claude Code substitutes `${CLAUDE_PLUGIN_ROOT}` and Codex substitutes
`${PLUGIN_ROOT}`. Keeping a separate manifest per runtime avoids that variable
clash in a single shared file while reusing one hook implementation.

### Owner language

The owner's language is resolved in this order:

1. `CLAIRVOYANCE_OWNER_LANGUAGE` environment variable.
2. The first non-blank line of `<project>/.clairvoyance/owner-language.txt`.

If neither is set, the injected context instructs the agent to ask the human once
(via `AskUserQuestion`) and then write `.clairvoyance/owner-language.txt`.

## Cross-platform entry point

`hooks.json` invokes `plugin/hooks/run-hook.cmd session-start.sh`. `run-hook.cmd` is a
**polyglot** that runs as both a Windows batch file and a POSIX shell script, so a
single entry point works on every platform:

- **Windows** (`cmd.exe` runs the batch block): locates a Bash interpreter by
  checking, in order, system Git for Windows (`C:\Program Files\Git`,
  `C:\Program Files (x86)\Git`), per-user Git
  (`%LOCALAPPDATA%\Programs\Git`), then any `bash` on `PATH`. If none is found it
  exits 0 — the session starts normally without injection rather than erroring.
- **macOS / Linux**: the file is executable but has no shebang, so the shell falls
  back to interpreting it; the batch block is a no-op heredoc and the script
  `exec`s `bash` on the target hook.

`run-hook.cmd` must keep its executable bit (`100755`) for the Unix fall-through to
work. CI validates both hook scripts with `bash -n`, asserts that
`session-start.sh` emits valid JSON, and parses `codex-hooks.json` to confirm it
routes through the same wrapper with the `${PLUGIN_ROOT}` variable.
