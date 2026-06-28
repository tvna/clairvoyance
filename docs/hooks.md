# Hooks

## SessionStart injection

`plugin/hooks/hooks.json` registers one `SessionStart` hook (matching `startup`, `clear`,
and `compact`). It runs `plugin/hooks/session-start.sh`, which:

1. Reads `plugin/skills/using-clairvoyance/SKILL.md` and injects it as
   `additionalContext` so the agent has the bootstrap router from the first turn.
2. Resolves the project owner's language and injects it as authoritative for
   Clairvoyance handoffs.

If the bootstrap skill file is missing, the hook exits 0 and injects nothing.

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
work. CI validates both hook scripts with `bash -n` and asserts that
`session-start.sh` emits valid JSON.
