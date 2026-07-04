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

First decide whether the Fable-optimized path applies. Confirm the next session's
model from, in order: an explicit statement of which model the next session will
use; failing that, the model identifier the harness reports for a session the
operator is continuing on the same model (`claude-fable-5` or `claude-mythos-5`).
Judge the *next* session's model, not this one's - they can differ. If neither
source confirms a Fable model, emit the standard handoff; do not infer Fable from
the task alone. When it is plausibly Fable but unconfirmed, ask one question
rather than assume.

Once Fable is confirmed, optimize the handoff for it by prepending a short
operating block that names Fable in its heading and sets effort, scope, and
progress-reporting discipline. Fable follows brief instructions and degrades on
over-prescription, but Fable is not always available - a safety-classifier
refusal falls back to Opus 4.8, and some harnesses do not offer Fable at all - so
keep the handoff body model-agnostic rather than stripping it: the block tells
Fable to treat the sections as constraints, not a script, and its first line
tells a non-Fable session to ignore it. The result is one artifact, explicitly
labeled for Fable yet still correct if it degrades. Never tell the next session
to echo its reasoning - on Fable that can trigger a refusal. Read
[the Fable-optimized handoff](references/fable-optimization.md) for the decision
signals, the safe-degradation rationale, and the paste-ready operating block.

## Output

Deliver the handoff as a single attached Markdown file (`handoff.md`) so it copies and pastes in one piece. Portable delivery, in order of preference: attach the file when the harness supports attachments; otherwise write it to a Markdown file outside the repository (for example, a temporary directory) and give its path - never write into the repo workspace, since a handoff often fires in the blocked or low-context states where the session must avoid extra repo changes; if the harness supports neither attachments nor writing outside the repo, emit the same Markdown inline as the reply. The file (or inline block) holds one prompt with headings **Context**, **Background**, **Files to read**, **Implementation**, **Verification**, **PR creation**, **Acceptance criteria**.

Because the deliverable is a Markdown file rather than inline chat text, use standard Markdown: fenced code blocks for commands and `inline code` for short snippets.
