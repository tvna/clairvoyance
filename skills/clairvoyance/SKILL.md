---
name: clairvoyance
description: Use when an agent is blocked by a human-owned choice and must hand the owner a prepared decision, approval request, deferral choice, rollback choice, or 2-3 concrete options with evidence.
---

# Clairvoyance

Clairvoyance turns a blocker or owner decision into an evidence-backed handoff a human can inspect, trust, and safely disagree with.

**UTILITY SKILL:** invoked as `clairvoyance:clairvoyance` by `using-clairvoyance` for owner decisions and blockers.

## Steps

1. Classify the handoff: owner decision, blocked state, approval, deferral, sequencing, or rollback.
2. Separate facts, assumptions, speculation, and unknowns.
3. Gather evidence: canonical URLs, local files, tests, command output, screenshots, logs, or observed behavior.
4. State what is blocked or what the human must decide.
5. Prepare named options when the human must decide. Prefer 2-3 reversible choices.
6. Recommend one option and explain why.
7. State risks, reversibility, missing proof, and the next move.
8. Write in the project owner's language unless a repository rule requires another language for outward-facing artifacts.

## References

Read [decision handoffs](references/decision-handoff.md) for owner choices, blockers, and human-only decisions.

## Output

Use these headings; do not omit any:

- **Verdict:** the recommendation in one sentence.
- **Evidence:** what proves or limits the recommendation.
- **System Context:** architecture impact and dependency surface.
- **Options:** named choices with trade-offs when a decision is required.
- **Risks:** known failure modes and missing proof.
- **Reversibility:** how hard it is to undo.
- **Next Move:** the concrete action the human can approve, reject, or modify.

Keep the answer compact. Do not bury the recommendation under process notes.
