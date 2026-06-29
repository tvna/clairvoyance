---
name: adaptive-coaching
description: Logs a person's recurring capability gaps locally and, when they ask to reflect, turns the accumulated signal into a prosthesis-building AskUserQuestion quiz. Use on a reflection or retrospective request, not a single decision.
---

# Adaptive Coaching

Adaptive coaching builds a person's durable capability over time while preserving autonomy and psychological safety. It has two parts: it **records** recurring capability gaps as anonymous signal, and — **only when the person asks to reflect** — turns that accumulated signal into a quiz. The quiz is never pushed automatically.

**UTILITY SKILL:** invoked as `clairvoyance:adaptive-coaching` by `using-clairvoyance` when the person asks to reflect on their recurring patterns, or to log a recurring gap.

**Boundary with decision-coaching:** `decision-coaching` coaches a single decision in the moment (an LGTM or ambiguous call). `adaptive-coaching` works across sessions: it logs recurring gaps and delivers a reflection quiz only on the person's own request.

## Technical vs Adaptive

Diagnose which kind of work a recurring gap is (Heifetz). The split shapes *what the quiz reinforces*, not whether to coach:

- **Technical challenge:** a known answer exists. If the person already understands it, there is nothing to coach. If they keep getting it wrong, the quiz reinforces the correct understanding.
- **Adaptive challenge:** progress needs the person to change a value, habit, belief, or behaviour. More information alone cannot solve it; the quiz builds the person's own judgement.

Name the split — mislabeling an adaptive challenge as technical is the most common failure.

## Recording observations

Whenever a recurring capability gap surfaces, record it as anonymous coded signal (never prompt text or code) so a later reflection has data. This logging is passive: it does not coach and does not quiz. Record commands, categories, and storage details are in [the store reference](references/store.md).

## Reflection quiz (on request)

Deliver the quiz **only** when the person asks to reflect or do a retrospective, **and** the store reports `ready` (enough accumulated signal: a session grace period plus accumulated observations). Never quiz on a single instance, on an unrelated handoff, or for a first-time user still finding their feet. If the person asks to reflect but the store is not `ready`, say so warmly and keep observing — do not manufacture a quiz. An unavailable store means hold, not fail.

### Steps

1. Confirm `ready` via the store (`status`). If not, acknowledge and hold — keep observing, do not quiz.
2. Classify the dominant recurring gap (the technical-versus-adaptive split).
3. Name the capability gap warmly, directly, and without shaming. Diagnose the gap, never the person's worth.
4. Deliver a prosthesis-building quiz: portable question handoff — AskUserQuestion when available, otherwise `AskUserQuestion:` text — with 2-3 choices and the correct answer marked.
5. Record the quiz outcome, then give the concrete corrective next move.
6. Write in the project owner's language unless a repository rule requires another language for outward-facing artifacts.

## Prosthesis effect via quiz

The プロテーゼ (prosthesis) effect: coaching should become an extension the person internalises into durable judgement, not a crutch they depend on. Active recall through a quiz beats being told — retrieval practice is what makes the corrected judgement stick. Each quiz item gives a concrete scenario, 2-3 choices, the marked correct answer, and a one-line why. Keep questions non-leading and non-shaming; the goal is the person's own next correct call without the coach present.

## Output

A reflection quiz uses these headings:

- **Classification:** the technical-versus-adaptive split of the recurring gap.
- **Capability Gap:** the understanding or change the person must make, named without shame.
- **Evidence:** the accumulated anonymous signal (count versus threshold) that makes the reflection fair now.
- **Quiz:** AskUserQuestion (or `AskUserQuestion:` fallback) with 2-3 choices and the marked correct answer.
- **Why:** the prosthesis effect the quiz builds.
- **Next Move:** the concrete corrective the person can adopt.

Pattern: **Classification** -> **Capability Gap** -> **Evidence** -> **Quiz** -> **Next Move**. When the store is not `ready`, emit only **Classification**, **Evidence** (insufficient signal), and **Next Move** (keep observing) — do not quiz.

## Example

See a [worked adaptive-coaching session](references/example.md).
