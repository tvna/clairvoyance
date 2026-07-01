---
name: adaptive-coaching
description: Logs a person's recurring capability gaps locally and, when they ask to reflect, turns the accumulated signal into a prosthesis-building AskUserQuestion quiz. Use on a reflection or retrospective request, not a single decision.
---

# Adaptive Coaching

Adaptive coaching builds a person's durable capability over time while preserving autonomy and psychological safety. It has two parts: it **records** recurring capability gaps as anonymous signal, and — **only when the person asks to reflect** — turns that accumulated signal into a quiz. The quiz is never pushed automatically.

**UTILITY SKILL:** invoked as `clairvoyance:adaptive-coaching` by `using-clairvoyance` when the person asks to reflect on their recurring patterns, or to log a recurring gap.

**Boundary with decision-coaching:** `decision-coaching` coaches a single decision in the moment (an LGTM or ambiguous call). `adaptive-coaching` works across sessions: it logs recurring gaps and delivers a reflection quiz only on the person's own request.

## Recording observations

Whenever a recurring capability gap surfaces, record it as anonymous coded signal — never prompt text or code, though opt-in context capture can add an abstracted, secret-free scenario summary (see the store reference) — so a later reflection has data. This logging is passive: it does not coach and does not quiz. Record commands, categories, and storage details are in [the store reference](references/store.md).

## Reflection quiz (on request)

Deliver the quiz **only** when the person asks to reflect or do a retrospective, **and** the store reports `ready` (enough accumulated signal: a session grace period plus accumulated observations). Never quiz on a single instance, on an unrelated handoff, or for a first-time user still finding their feet. If the person asks to reflect but the store is not `ready`, say so warmly and keep observing — do not manufacture a quiz. An unavailable store means hold, not fail.

### Steps

1. Confirm `ready` via the store (`status`). If not, acknowledge and hold — keep observing, do not quiz.
2. Classify the dominant recurring gap — the technical-versus-adaptive split that shapes what the quiz reinforces (see [classification](references/classification.md)).
3. Name the capability gap warmly, directly, and without shaming. Diagnose the gap, never the person's worth (see [coaching practice](references/practice.md) for pacing and framing).
4. Deliver a prosthesis-building quiz: AskUserQuestion (or `AskUserQuestion:` text) with 2-3 plausible choices and a confidence prompt. Do **not** reveal or mark the correct answer before the person answers; retrieval practice needs the person to retrieve first (see [how to build the quiz](references/quiz.md)).
5. After the person answers, give feedback: correct/incorrect, the better move, and a short calibration note comparing confidence to outcome. Record outcome, confidence, and calibration when the store supports it.
6. Schedule or name a spaced follow-up point (**Review Again**) so the corrected judgement is revisited later.
7. Write in the active contributor's language (the person driving the current session, not a fixed project owner) unless a repository rule requires another language for outward-facing artifacts.

## Output

The initial reflection output stops after the person has a real retrieval prompt:

- **Classification:** the technical-versus-adaptive split of the recurring gap.
- **Capability Gap:** the understanding or change the person must make, named without shame.
- **Evidence:** the accumulated anonymous signal (count versus threshold) that makes the reflection fair now.
- **Quiz:** AskUserQuestion (or `AskUserQuestion:` fallback) with 2-3 plausible choices and a confidence prompt; no answer is marked before the person answers.

Only after the person answers, continue with:

- **Feedback:** after the answer, identify the better move and explain why.
- **Calibration:** after the answer, compare confidence to outcome without diagnosing the person.
- **Review Again:** a lightweight due point for the next retrieval pass.
- **Next Move:** the concrete corrective the person can adopt.

Initial pattern: **Classification** -> **Capability Gap** -> **Evidence** -> **Quiz**. Then wait for the person's answer and confidence. Post-answer pattern: **Feedback** -> **Calibration** -> **Review Again** -> **Next Move**. When the store is not `ready`, emit only **Classification**, **Evidence** (insufficient signal), and **Next Move** (keep observing) — do not quiz.

## Psychological safety contract

A reflection should make the person more willing to continue learning, not more likely to leave. Use observation-based language:

- Prefer "I notice a recurring pattern..." or "The signal points to..." over "you always..." or "your problem is...".
- Name the pattern as information, not a verdict.
- Preserve agency: "you can choose the next move" and "try this once" beats coercive or moralizing language.
- Use I-message style when naming impact: "I am reading this as a risk to the decision staying owned" rather than "you are avoiding ownership."
- Normalize misses as data: a wrong answer or overconfident answer is a calibration signal for this move, not a trait.
- If the person sounds worried, defensive, ashamed, or likely to disengage, lower the heat first: acknowledge the concern, state that the reflection is opt-in, and offer a smaller next step.

## References

Load only what the task needs:

- [Technical-vs-adaptive classification](references/classification.md) — when classifying the gap.
- [Coaching practice (Heifetz moves)](references/practice.md) — when delivering the reflection: pacing, framing, giving the work back.
- [Building the prosthesis quiz](references/quiz.md) — when constructing the quiz.
- [The local store](references/store.md) — record/status commands, categories, thresholds.
- [Worked example](references/example.md) — a full reflection session.
