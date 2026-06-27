---
name: using-clairvoyance
description: Use when starting a session or after compaction to route future handoffs, owner choices, review readiness, architecture trade-offs, and unclear decisions to one Clairvoyance skill.
---

# Using Clairvoyance

Clairvoyance is the agent-to-human handoff discipline.

**BOOTSTRAP SKILL:** choose one handoff skill.

## Rule

Before handing a decision, verdict, blocker, architecture judgment, trade-off, or question to a human, select one Clairvoyance skill.

Route names are plugin-qualified.

SessionStart owner language is authoritative; if missing, AskUserQuestion before handoff.

## Trigger

Route by scene:

- Human owner decision, blocker, or prepared options outside PR readiness -> `clairvoyance:clairvoyance`.
- PR, commit, branch, review verdict, or "should this merge?" -> `clairvoyance:review-verdict`.
- Architecture judgment, system trade-off, or failure-mode analysis -> `clairvoyance:architecture-tradeoff`.
- LGTM requests, missing subject, noisy input, sycophancy pressure, or decision without architecture understanding -> `clairvoyance:decision-coaching`.

Do not route implementation, progress, tests, typos, or refactors unless they become a human decision handoff.

For readiness, review, architecture, options, or recommendations, use the matching skill. Treat evidence gaps as risks or unknowns.

## Priority

Use other needed skills first. Use Clairvoyance for the human handoff.

When unsure, prefer the narrowest matching scene; if none applies, continue normally.

If the agent answers directly, use exact headings. Owner: **Verdict**, **Evidence**, **Options**, **Risks**, **Reversibility**, **Next Move**. Review/architecture: start with **Verdict**. Coaching starts with AskUserQuestion.

If a human-only answer blocks the handoff, use AskUserQuestion with prepared choices.

## Examples

- "Should we merge?" -> `clairvoyance:review-verdict`.
- "Which architecture path?" -> `clairvoyance:architecture-tradeoff`.
- "I am blocked; owner choices?" -> `clairvoyance:clairvoyance`.
- "LGTM?" or "it should use the service, right?" -> `clairvoyance:decision-coaching`.
- "Run the tests" -> do not load the handoff skill.
