---
name: using-clairvoyance
description: Use when starting a session or after compaction to route handoffs, owner choices, review readiness, architecture trade-offs, and unclear decisions.
---

# Using Clairvoyance

**BOOTSTRAP SKILL:** choose one handoff skill.

## Rule

Before handoff, select one plugin-qualified Clairvoyance skill.

SessionStart owner language is authoritative; if missing, use portable question handoff.

Portable question handoff: AskUserQuestion if available; else print `AskUserQuestion:` plus the same question and 1-3 choices.

Depth after routing — branch by stakes:

- Reversible, low-risk, one clear call? -> compact handoff: **Verdict** + **Next Move**.
- Irreversible, high-risk, contested, or detail requested? -> full handoff: all routed-skill headings.

## Trigger

Route:

- Human owner decision, blocker, or prepared options outside PR readiness -> `clairvoyance:clairvoyance`.
- PR, commit, branch, review verdict, or "should this merge?" -> `clairvoyance:review-verdict`.
- Architecture judgment, system trade-off, or failure-mode analysis -> `clairvoyance:architecture-tradeoff`.
- LGTM requests, missing subject, noisy input, sycophancy pressure, or decision without architecture understanding -> `clairvoyance:decision-coaching`.

Do not route implementation, progress, tests, typos, or refactors unless they become a decision handoff. Treat evidence gaps as risks or unknowns.

## Priority

Use other needed skills first; use Clairvoyance for the human handoff. When unsure, prefer the narrowest matching scene; if none applies, continue normally. If a human-only answer blocks the handoff, use portable question handoff with prepared choices.

## Examples

- Merge: `review-verdict` -> **Verdict**, **Findings**, **Evidence**, **Risks**, **Next Move**.
- Architecture: `architecture-tradeoff` -> **Verdict**, **Options**, **Future Story**, **Premortem**, **Next Move**.
- Owner decision: `clairvoyance` -> **Verdict**, **Evidence**, **Options**, **Risks**, **Reversibility**, **Next Move**.
- LGTM/unclear subject: `decision-coaching` -> portable question handoff.
