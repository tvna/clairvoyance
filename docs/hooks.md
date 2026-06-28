# Hooks

## SessionStart injection

`plugin/hooks/hooks.json` registers one `SessionStart` hook (matching `startup`, `clear`,
and `compact`). It runs `plugin/hooks/session-start.sh`, which:

1. Reads `plugin/skills/using-clairvoyance/SKILL.md` and injects it as
   `additionalContext` so the agent has the bootstrap router from the first turn.
2. Resolves the project owner's language and injects it as authoritative for
   Clairvoyance handoffs.

If the bootstrap skill file is missing, the hook exits 0 and injects nothing.

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
