---
name: adaptive-coaching
description: Logs a person's recurring capability gaps locally and, when they ask to reflect, turns the accumulated signal into a prosthesis-building AskUserQuestion quiz. Use to record a recurring gap wherever it surfaces, unless the situation should not be treated as an adaptive challenge (record only, no quiz), and on a reflection or retrospective request - never on a single decision.
---

# Adaptive Coaching

Adaptive coaching builds a person's durable capability over time while preserving autonomy and psychological safety. It has two parts: it **records** recurring capability gaps as anonymous signal, and — **only when the person asks to reflect** — turns that accumulated signal into a quiz. The quiz is never pushed automatically.

The recurring gap can come from any domain where adaptive work is an appropriate frame: work, relationships, learning, health habits, creative practice, community life, personal projects, or other repeated situations where the person is asking to examine their own moves. The scope is domain-neutral, not domain-unlimited: the skill coaches capability, judgement, communication, and agency; it does not provide therapy, crisis intervention, medical advice, legal advice, financial advice, safety planning, diagnosis, adjudication, or instructions for controlling another person.

**UTILITY SKILL:** invoked as `clairvoyance:adaptive-coaching` by `using-clairvoyance` when the person asks to reflect on their recurring patterns in any appropriate domain, or to log a recurring gap.

**Boundary with decision-coaching:** `decision-coaching` coaches a single decision in the moment (an LGTM or ambiguous call). `adaptive-coaching` works across sessions: it logs recurring gaps and delivers a reflection quiz only on the person's own request.

## Recording observations

Whenever a recurring capability gap surfaces, record it as anonymous coded signal — never prompt text or code, though opt-in context capture can add an abstracted, secret-free scenario summary (see the store reference) — so a later reflection has data. This logging is passive: it does not coach and does not quiz. When recording, do not echo pasted secrets, credentials, tokens, keys, raw code, file paths, or project identifiers back to the person; acknowledge only that a redacted/category-level observation was recorded or would be recorded. Record commands, categories, and storage details are in [the store reference](references/store.md).

## Reflection quiz (on request)

Deliver the quiz **only** when the person asks to reflect or do a retrospective, **and** the store reports `ready` (enough accumulated signal: a session grace period plus accumulated observations). Never quiz on a single instance, on an unrelated handoff, or for a first-time user still finding their feet. If the person asks to reflect but the store is not `ready`, say so warmly and keep observing — do not manufacture a quiz. An unavailable store means hold, not fail.

For domains outside ordinary work, keep the same retrieval-practice shape but narrow the frame to the person's own next move: what they can notice, ask, say, pause, repair, practice, verify, or choose. Do not diagnose other people, assign motives, adjudicate who is right, prescribe specialist treatment, or turn the quiz into therapy, legal advice, medical advice, financial advice, or risk management. If the prompt suggests abuse, self-harm, coercion, immediate danger, regulated professional advice, or another situation that should not be treated as an adaptive challenge, prioritize the platform's applicable safety guidance or a narrower non-coaching response and do not force the adaptive-coaching format.

### Steps

1. Confirm readiness via the store (`status`). The `ready` field is the verdict, in both directions: never quiz on `ready: false`, never hold on `ready: true` by inventing extra requirements. Treat a supplied status (pasted `status` JSON, or a verdict carried in from a handoff) the same as running `status` yourself. With neither a runnable store nor a supplied verdict, hold — do not derive readiness from described raw numbers. Relay any store misconfiguration warning, but the hold-or-deliver decision still follows `ready`.
2. Classify the dominant recurring gap — the technical-versus-adaptive split that shapes what the quiz reinforces (see [classification](references/classification.md)).
3. Apply the psychological safety contract (below), then name the capability gap. Describe what happened and what it cost in event terms — "the scope plan stayed unchanged after the evidence moved, and the deadline slipped" — never as a mindset or trait ("confidence stays high despite evidence"). See [coaching practice](references/practice.md) for pacing and framing.
4. Deliver a prosthesis-building quiz: AskUserQuestion (or `AskUserQuestion:` text) with 2-3 plausible choices and a confidence prompt, answer unmarked until the person responds (see [how to build the quiz](references/quiz.md)).
5. After the person answers, give feedback: correct/incorrect, the better move, and a short calibration note comparing confidence to outcome. Record outcome, confidence, and calibration when the store supports it.
6. Schedule or name a spaced follow-up point (**Review Again**) so the corrected judgement is revisited later.

## Output

The initial reflection output stops after the person has a real retrieval prompt:

- **Classification:** the technical-versus-adaptive split of the recurring gap.
- **Capability Gap:** the understanding or change the person must make, named without shame as a move and its consequence — not as a mindset, bias, or description of how the person thinks.
- **Evidence:** the accumulated anonymous signal (count versus threshold) that makes the reflection fair now. Quote the store's reported numbers (`count`/`threshold`/`sessions`/`session_threshold`) verbatim, never recomputed; when not ready, cite the store's verdict rather than re-deriving one, and surface any store warning as a misconfiguration note.
- **Quiz:** AskUserQuestion (or `AskUserQuestion:` fallback), answer unmarked, per the psychological safety contract and the quiz reference.

Only after the person answers, continue with:

- **Feedback:** after the answer, identify the better move and explain why.
- **Calibration:** after the answer, compare confidence to outcome without diagnosing the person.
- **Review Again:** a lightweight due point for the next retrieval pass.
- **Next Move:** the concrete corrective the person can adopt.

Initial pattern: **Classification** -> **Capability Gap** -> **Evidence** -> **Quiz**. Then wait for the person's answer and confidence. Post-answer pattern: **Feedback** -> **Calibration** -> **Review Again** -> **Next Move**. When the store is not `ready`, emit only **Classification**, **Evidence** (insufficient signal), and **Next Move** (keep observing) — do not quiz. When the psychological safety contract's heat-lowering preamble applies, it precedes **Classification** (see below); phrase **Classification** and **Capability Gap** as tentative in that case.

For recording-only requests, keep the response short and content-minimal: state the category-level signal and whether context was omitted or stored only as a redacted abstract. Never repeat a secret or unsafe detail from the request to prove you saw it; redaction applies to the conversational response as well as to persisted context.

## Psychological safety contract

A reflection should make the person more willing to continue learning, not more likely to leave. This is the single canonical statement of these rules — the Steps and Output above apply it, they don't restate it.

- **Lower the heat first, when needed.** If the person sounds worried, defensive, ashamed, or likely to disengage — including when they voice this directly — open the response with a 2-3 sentence heat-lowering preamble before naming anything else: acknowledge the concern in the person's own terms (no verbatim echo of a self-blaming phrase), frame the pattern as signal rather than a verdict ("I notice...", "I am reading this as..."), and state that the reflection is opt-in — full quiz, a smaller next step, or keep observing. This is the mandatory opening move in that case, not an optional add-on.
- **Diagnose the move, never the person.** Store categories (`loss-aversion`, `avoidance`, `authority-dependence`, ...) are the coach's backstage diagnostic codes — never hand one to the person as a label, a bias, or an explanation of their psychology.
- **Use observation-based language.** Prefer "I notice a recurring pattern..." or "The signal points to..." over "you always..." or "your problem is..."; use I-message style for impact ("I am reading this as a risk to the decision staying owned" rather than "you are avoiding ownership").
- **Preserve agency.** "You can choose the next move" and "try this once" beats coercive or moralizing language.
- **Confidence is calibration data, not a diagnosis.** A wrong or overconfident answer is a signal for this one move, never a trait. Any comparison of confidence against outcome happens only after the person answers — before that, offer no verdict on the person's psychology or their confidence.

## References

Load only what the task needs:

- [Technical-vs-adaptive classification](references/classification.md) — when classifying the gap.
- [Coaching practice (Heifetz moves)](references/practice.md) — when delivering the reflection: pacing, framing, giving the work back.
- [Building the prosthesis quiz](references/quiz.md) — when constructing the quiz.
- [The local store](references/store.md) — record/status commands, categories, thresholds.
- [Worked example](references/example.md) — a full reflection session.
