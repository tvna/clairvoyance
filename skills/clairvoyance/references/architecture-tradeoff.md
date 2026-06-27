# Architecture Trade-Off

Use this when the human needs system-level judgment, not just task status.

## Map

- Current architecture and ownership boundary.
- Proposed change or competing options.
- Dependencies and data flow.
- Invariants that must remain true.
- Failure modes and safety controls.
- Operational cost and reversibility.

## Recommendation

Recommend the option that best preserves the system's important invariants while solving the active problem with the smallest sufficient change.

## Quality Bar

Do not optimize for elegance alone. Explain what the choice makes easier, what it makes harder, and what proof would change the recommendation.

## Failure Modes

- **Raw status dump:** lists activity without a decision surface.
- **Unsupported confidence:** recommends without evidence.
- **Diff-only verdict:** reviews changed lines without tracing behavior.
- **Unbounded question:** asks the human to scope the problem from scratch.
- **Hidden assumption:** treats speculation as fact.
- **Missing reversibility:** omits how hard the choice is to undo.
- **No next move:** leaves the human informed but unable to act.
