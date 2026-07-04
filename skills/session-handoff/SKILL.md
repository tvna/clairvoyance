---
name: session-handoff
description: Produces a paste-ready handoff prompt (an attached Markdown file) so the next agent session resumes the work cleanly instead of trusting automatic context compaction. Use when context runs low and a clean restart beats compaction, when unfinished work must carry over, or when repository gates limit what this session can change.
---

# Session Handoff

Turns in-flight work into a self-contained prompt the next session can act on
without re-deriving context.

## When to use

Reach for a handoff instead of relying on the harness's automatic compaction:
when context is filling, write a clean handoff and start a fresh session rather
than let compaction silently lose fidelity. Also hand off when repository gates or
session-scoped limits block the change here - reset and resume in a new session.

## Steps

1. Context: the issue, the existing branch (do not create a new one), and what it closes.
2. Background: what remains or failed, when, and the observable symptom - 2-4 sentences.
3. Files to read before implementing, in read order, each with a one-line role; the next session reads them fully first.
4. Implementation: the exact, minimum-sufficient change and why. Name options A/B/C with a recommendation when several exist. Do not invite extra files, hooks, or abstractions.
5. Verification: the commands to run and the expected result.
6. PR creation: read the PR template; suggest a Conventional Commit title.
7. Acceptance criteria: a deterministic checklist, including CI green.

Read [the handoff template](references/handoff-template.md) for exact section order and an example.

## When the next session runs on a Fable model

When you are told the next session will use a Claude Fable model
(`claude-fable-5` or `claude-mythos-5`), optimize the handoff for it: state the
goal and constraints and drop step-by-step prescription (Fable follows brief
instructions and degrades on over-prescription), and prepend a short operating
block that sets effort, scope, and progress-reporting discipline. Never tell the
next session to echo its reasoning - on Fable that can trigger a refusal. For any
other model, emit the standard handoff unchanged. Read
[the Fable-optimized handoff](references/fable-optimization.md) for the exact
adjustments and the paste-ready operating block.

## Output

Deliver the handoff as a single attached Markdown file (`handoff.md`) so it copies and pastes in one piece. Portable delivery, in order of preference: attach the file when the harness supports attachments; otherwise write it to a Markdown file outside the repository (for example, a temporary directory) and give its path - never write into the repo workspace, since a handoff often fires in the blocked or low-context states where the session must avoid extra repo changes; if the harness supports neither attachments nor writing outside the repo, emit the same Markdown inline as the reply. The file (or inline block) holds one prompt with headings **Context**, **Background**, **Files to read**, **Implementation**, **Verification**, **PR creation**, **Acceptance criteria**.

Because the deliverable is a Markdown file rather than inline chat text, use standard Markdown: fenced code blocks for commands and `inline code` for short snippets.
