---
name: using-clairvoyance
description: Use when starting a session or after compaction to route safe handoffs, owner choices, review readiness, architecture trade-offs, and unclear decisions.
---

# Using Clairvoyance

**BOOTSTRAP SKILL:** choose one handoff skill.

## Rule

Before handoff, select one plugin-qualified Clairvoyance skill.

SessionStart owner language is authoritative; if missing, use portable question handoff before decision handoff.

Portable question handoff: AskUserQuestion if available; else print `AskUserQuestion:` plus the same question and 1-3 choices.

Progressive disclosure: start compact; expand context, risks, or open questions only for uncertainty, high risk, or human request.

## Trigger

Route:

- Human owner decision, blocker, or prepared options outside PR readiness -> `clairvoyance:clairvoyance`.
- PR, commit, branch, review verdict, or "should this merge?" -> `clairvoyance:review-verdict`.
- Architecture judgment, system trade-off, or failure-mode analysis -> `clairvoyance:architecture-tradeoff`.
- LGTM requests, missing subject, noisy input, sycophancy pressure, or decision without architecture understanding -> `clairvoyance:decision-coaching`.

Do not route implementation, progress, tests, typos, or refactors unless they become a decision handoff.

For readiness, review, architecture, options, or recommendations, use the matching skill; treat evidence gaps as risks or unknowns.

## Priority

Use other needed skills first. Use Clairvoyance for the human handoff.

When unsure, prefer the narrowest matching scene; if none applies, continue normally.

Direct headings: Owner uses **Verdict**, **Evidence**, **Options**, **Risks**, **Reversibility**, **Next Move**. Review/architecture starts with **Verdict**. Coaching starts with portable question handoff.

If a human-only answer blocks the handoff, use portable question handoff with prepared choices.

## Examples

- "Should we merge?" -> `clairvoyance:review-verdict`.
- "Which architecture path?" -> `clairvoyance:architecture-tradeoff`.
- "LGTM?" or "it should use the service, right?" -> `clairvoyance:decision-coaching`.
- "Run the tests" -> do not load the handoff skill.
