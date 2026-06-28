# Session handoff

`session-handoff` produces a paste-ready prompt that lets the **next** agent
session resume work without re-deriving context. It is an agent-to-next-session
handoff, distinct from the human-facing handoffs in the rest of this package.

## Why it exists

**Don't depend on automatic compaction.** When a session's context fills, the
harness compacts it automatically — and that compaction can silently lose detail
the work depends on. This skill is the deliberate alternative: before context runs
out, write a complete, self-contained handoff and start a fresh session, so
continuity rests on an explicit artifact rather than trusted compaction.

**Reset when the harness limits the session.** A strong repository-side harness
(session-scoped branch authz, gates, freshness checks) can cap what a single
session is allowed to change. When the needed change is blocked by those limits,
hand off and regroup in a new session rather than fighting the gate in place.

## What a good handoff contains

A handoff is self-contained — the next session should not need the prior
conversation. It carries Context (issue, existing branch, closes), Background, the
files to read in order, the precise minimum-sufficient Implementation, Verification
commands and expected results, PR guidance, and deterministic Acceptance criteria.
See [`plugin/skills/session-handoff/references/handoff-template.md`](../skills/session-handoff/references/handoff-template.md)
for the template and a worked example.

Handoffs avoid fenced code blocks (they use 4-space-indented command blocks) so the
prompt pastes into a chat input without breaking.

## Origin

Adapted from the next-session handoff mechanism in
[tvna/claude-md](https://github.com/tvna/claude-md). Upstream also drives it from a
Stop hook; here it is a skill the agent invokes when a handoff is warranted. A Stop
hook to auto-prompt it can be added later.
