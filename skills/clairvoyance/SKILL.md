---
name: clairvoyance
description: |
  USE FOR: agent-to-human decisions, review verdicts, architecture judgments, blocked states, merge readiness, trade-offs, recommendations.
  DO NOT USE FOR: implementation, quick status updates, test execution, typo fixes, refactors, or private reasoning.
---

# Clairvoyance

Clairvoyance turns agent work into an evidence-backed handoff a human can inspect, trust, and safely disagree with.

**UTILITY SKILL:** invoked as `clairvoyance:clairvoyance` by `using-clairvoyance` for human-facing handoffs.

## Steps

1. Classify the handoff: decision, review verdict, architecture trade-off, blocked state, or rollback.
2. Separate facts, assumptions, speculation, and unknowns.
3. Gather evidence: canonical URLs, local files, tests, command output, screenshots, logs, or observed behavior.
4. Map system context: entry points, changed surfaces, callers/callees, data flow, contracts, and user-facing behavior as relevant.
5. Prepare named options when the human must decide. Prefer 2-3 reversible choices.
6. Recommend one option and explain why.
7. State risks, reversibility, missing proof, and the next move.
8. Write in the project owner's language unless a repository rule requires another language for outward-facing artifacts.

## References

Read only what the handoff needs:

- [Decision handoffs](references/decision-handoff.md) for merge, owner choices, blockers, and human-only decisions.
- [Review verdicts](references/review-verdict.md) for PR or code-review readiness.
- [Architecture trade-offs and failure modes](references/architecture-tradeoff.md) for system impact, raw status dumps, unsupported claims, or diff-only verdicts.

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
