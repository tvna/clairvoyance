# Adaptive-coaching observation store

The store accumulates anonymous signal locally so a reflection quiz has enough
data to be fair. It does not trigger anything on its own: the quiz fires only when
the person asks to reflect. Entry point `adaptive-store.sh`, backed by the
`sqlite3` CLI (`choco install sqlite`). Record only coded metadata — never prompt
text, code, or file paths.

## Commands

Use `${CLAUDE_PLUGIN_ROOT}` (Codex substitutes `${PLUGIN_ROOT}`).

Record an observation:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/hooks/adaptive-store.sh" record --category <category> [--signal <coded-label>]
```

Record a quiz outcome (same category as the observation it scores):

```bash
bash "${CLAUDE_PLUGIN_ROOT}/hooks/adaptive-store.sh" record --category <category> --outcome correct|incorrect
```

On a reflection request, check whether enough has accumulated for a fair quiz:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/hooks/adaptive-store.sh" status
```

`status` prints JSON with `ready: true` only once **both** gates pass: the
session grace period and the adaptive-signal threshold (below). `--category` is
required on every `record`; an outcome-only record is rejected.

The SessionStart hook calls `record-session` on each session to advance the
grace period — the skill does not need to. (`record-session` bumps the anonymous
session count; it takes no flags.) The hook pushes no coaching of its own.

## Readiness: two gates

A reflection quiz is delivered only when the person asks AND **both** gates hold,
so a first-time user with thin data is never quizzed:

- **Session grace:** at least `$CLAIRVOYANCE_SESSION_THRESHOLD` chat sessions
  have elapsed (default 50; 0 disables the grace period).
- **Adaptive signal:** at least `$CLAIRVOYANCE_COACH_THRESHOLD` observations have
  accumulated (default 5).

`status` reports `sessions`, `session_threshold`, `count`, and `threshold`
alongside `ready` so the split is visible.

## Categories

`avoidance`, `mislabeled-technical`, `loss-aversion`, `values-conflict`,
`no-experiment`, `authority-dependence`, `other`. Anything outside this list is
folded to `other`; the optional `--signal` is sanitised to a short `[a-z0-9-]`
token so no free text persists.

## Storage and volatility

Persists on the local workstation (`%LOCALAPPDATA%\clairvoyance` on Windows;
`$CLAIRVOYANCE_DATA_DIR` overrides). Volatility is tolerated: ephemeral or remote
sessions simply do not persist, and an unavailable store means hold the quiz, not
fail.
