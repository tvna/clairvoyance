---
name: using-clairvoyance
description: |
  USE FOR: session start, context compaction, checking whether a response is an agent-to-human decision handoff, routing human-facing recommendations to clairvoyance.
  DO NOT USE FOR: ordinary implementation, test runs, progress updates, typo fixes, refactors, or answers that do not hand a decision to a human.
---

# Using Clairvoyance

Clairvoyance is the agent-to-human handoff discipline.

**BOOTSTRAP SKILL:** invokes `clairvoyance`; does not create the handoff itself.

## Rule

Before any response that hands a decision, verdict, blocker, architecture judgment, or trade-off to a human, check whether `clairvoyance` applies.

If it applies, load `clairvoyance` before responding.

## Trigger

Use `clairvoyance` when the response will:

- Recommend a next move to a human.
- Say whether work is ready, blocked, risky, or worth merging.
- Explain an architecture trade-off or system impact.
- Ask the human to choose between options.
- Escalate a blocker, missing proof, or human-only decision.

Do not use it for ordinary implementation, quick progress updates, test runs, typo fixes, or refactors unless the response becomes a human decision handoff.

If the human asks for merge readiness, review readiness, or a recommendation, use `clairvoyance` even when evidence is incomplete. Treat missing evidence as a risk or unknown instead of skipping the handoff.

## Priority

If another skill is needed to do the work, use that skill first. Use `clairvoyance` when the result is being handed to the human for judgment.

When unsure, prefer checking `clairvoyance`; if it does not apply, continue normally.

## Examples

- "Should we merge this?" -> load `clairvoyance`.
- "Run the tests" -> do not load `clairvoyance`.
