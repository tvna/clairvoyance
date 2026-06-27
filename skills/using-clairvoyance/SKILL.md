---
name: using-clairvoyance
description: Use when starting a session or after context compaction to route future agent-to-human handoffs, owner choices, review readiness, and architecture trade-off requests to exactly one matching Clairvoyance skill before the agent responds.
---

# Using Clairvoyance

Clairvoyance is the agent-to-human handoff discipline.

**BOOTSTRAP SKILL:** choose one handoff skill before responding.

## Rule

Before any response that hands a decision, verdict, blocker, architecture judgment, or trade-off to a human, select one Clairvoyance skill.

When naming a route, use `clairvoyance:clairvoyance`, `clairvoyance:review-verdict`, or `clairvoyance:architecture-tradeoff`.

## Trigger

Route by scene:

- Human owner decision, blocker, or prepared options -> `clairvoyance:clairvoyance`.
- PR, commit, branch, review verdict, or merge readiness -> `clairvoyance:review-verdict`.
- Architecture judgment, system trade-off, or failure-mode analysis -> `clairvoyance:architecture-tradeoff`.

Do not route ordinary implementation, progress updates, test runs, typo fixes, or refactors unless the response becomes a human decision handoff.

If the human asks for readiness, review, architecture judgment, options, or a recommendation, use the matching skill even when evidence is incomplete. Treat gaps as risks or unknowns.

## Priority

Use other needed skills first. Use Clairvoyance when the result is handed to the human for judgment.

When unsure, prefer the narrowest matching scene; if none applies, continue normally.

If the host cannot load the selected skill, follow its handoff shape: **Verdict**, evidence, risks, reversibility, and next move. Owner decisions also include **Options**.

## Examples

- "Should we merge this?" -> load `clairvoyance:review-verdict`.
- "Which architecture path should we choose?" -> load `clairvoyance:architecture-tradeoff`.
- "I am blocked; tell the owner the choices." -> load `clairvoyance:clairvoyance`.
- "Run the tests" -> do not load the handoff skill.
