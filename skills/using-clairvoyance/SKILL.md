---
name: using-clairvoyance
description: Routes an agent-to-human handoff. Use when starting a session or after compaction to dispatch owner choices, review readiness, architecture trade-offs, and unclear decisions.
---

# Using Clairvoyance

**BOOTSTRAP SKILL:** choose one handoff skill.

## Rule

Before handoff, select one plugin-qualified Clairvoyance skill. One exception: an explicit visualization request never changes the route — pick the base skill as if no diagram had been asked, then additionally load `clairvoyance:visual-handoff` as a layer on it. `clairvoyance:session-handoff` is not routed here: it hands work to the next agent session, not a human — load it directly when a clean restart beats compaction.

SessionStart contributor language (the active contributor's, not a fixed owner's) is authoritative and covers every operator-facing string: prose, section headings, question bullet titles, and AskUserQuestion questions, header chips, and choice labels alike. The English heading names in the skill files are canonical identifiers for the output contract, not display strings — render them in the operator's language. If the language is missing, use portable question handoff.

Portable question handoff: AskUserQuestion if available; else print `AskUserQuestion:` plus the same question and 1-3 choices — question, headers, bullet titles, and choices all in the operator's language.

Depth after routing — branch by stakes:

- Reversible, low-risk, one clear call? -> compact handoff: **Verdict** + **Next Move**.
- Irreversible, high-risk, contested, or detail requested? -> full handoff: all routed-skill headings.

## Trigger

Route:

- Human owner decision, blocker, or prepared options outside PR readiness -> `clairvoyance:clairvoyance`.
- PR, commit, branch, review verdict, "should this merge?", or LGTM sought on a concrete, inspectable change -> `clairvoyance:review-verdict`.
- Architecture judgment, system trade-off, or failure-mode analysis -> `clairvoyance:architecture-tradeoff`.
- A single decision in the moment: LGTM sought without an inspectable change, missing subject, noisy input, sycophancy pressure, or a decision without architecture understanding -> `clairvoyance:decision-coaching`.
- A request to reflect or do a retrospective on one's own recurring patterns -> `clairvoyance:adaptive-coaching`, which delivers a reflection quiz when enough signal has accumulated.
- A recurring capability gap surfacing mid-task (repeated deferral, avoidance, a technical fix standing in for an owner call) -> `clairvoyance:adaptive-coaching` to record it as anonymous local signal — record only, never a quiz.
- High-blast-radius, irreversible, or compliance-violating instruction (the human harness) -> `clairvoyance:human-harness`.
- An explicit request to visualize a handoff, plan, or system state (a diagram, UML, graph, "show me visually") is **not a route**: first choose the base handoff from the bullets above as if no diagram had been asked, then also load `clairvoyance:visual-handoff` — both skills load, and the base skill's headings stay. Never push a diagram unrequested.

The two coaching skills split by intent: a live decision goes to `decision-coaching`; an explicit reflection/retrospective request goes to `adaptive-coaching`. A reflection quiz is never pushed — it fires only on the person's own request.

Do not route implementation, progress, tests, typos, or refactors unless they become a decision handoff or carry high-blast-radius or compliance risk, which routes to `human-harness`. Treat evidence gaps as risks or unknowns.

## Priority

Use other needed skills first; use Clairvoyance for the human handoff. When two routes match, `human-harness` outranks every other route; otherwise prefer the narrowest matching scene, and if none applies, continue normally. If a human-only answer blocks the handoff, use portable question handoff with prepared choices.

## Examples

- Merge: `review-verdict` -> **Verdict**, **Findings**, **Evidence**, **Risks**, **Next Move**.
- Architecture: `architecture-tradeoff` -> **Verdict**, **Options**, **Future Story**, **Premortem**, **Next Move**.
- Owner decision: `clairvoyance` -> **Verdict**, **Evidence**, **Options**, **Risks**, **Reversibility**, **Next Move**.
- LGTM/unclear subject: `decision-coaching` -> portable question handoff.
- Reflection request: `adaptive-coaching` -> **Classification**, **Capability Gap**, **Evidence**, **Quiz**, **Next Move**.
- Risky order: `human-harness` -> **Stop**, **Blast Radius**, **Premortem**, **Confirm**, **Next Move**.
- "Show it as a diagram": routed skill's headings + `visual-handoff` -> **Diagram**, **Reading**.
