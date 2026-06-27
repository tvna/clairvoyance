---
name: architecture-tradeoff
description: Use when a human asks for one system-level architecture judgment between implementation options, ownership boundaries, dependency shapes, data-flow choices, or failure-mode trade-offs.
---

# Architecture Trade-Off

Architecture trade-offs turn system context into a decision a human can inspect.

**UTILITY SKILL:** invoked as `clairvoyance:architecture-tradeoff` by `using-clairvoyance` for system-level choices.

## Steps

1. Name the decision and competing options.
2. Separate facts, assumptions, speculation, and unknowns.
3. Map current architecture, ownership boundary, dependencies, data flow, invariants, and failure modes.
4. Compare cost, safety, operational impact, reversibility, and time-to-value.
5. Recommend the option that preserves important invariants with the smallest sufficient change.
6. State what proof would change the recommendation.
7. If only the human can answer a blocking architecture choice, use AskUserQuestion with 1-3 prepared choices; otherwise list it as a risk or unknown.
8. Write in the project owner's language unless a repository rule requires another language for outward-facing artifacts.

## Output

Use these headings:

- **Verdict:** the recommended option in one sentence.
- **Evidence:** proof and limits of the recommendation.
- **System Context:** architecture boundary, dependencies, contracts, and data flow.
- **Options:** named choices with trade-offs.
- **Risks:** failure modes, missing proof, and operational concerns.
- **Reversibility:** rollback path and cost.
- **Next Move:** the concrete action the human can approve, reject, or modify.

Do not optimize for elegance alone.
