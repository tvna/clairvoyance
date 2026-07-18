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

Whenever a recurring capability gap surfaces, record it as anonymous coded signal — never prompt text or code, though opt-in context capture can add an abstracted, secret-free scenario summary (see the store reference) — so a later reflection has data. This logging is passive: it does not coach and does not quiz. Record commands, categories, and storage details are in [the store reference](references/store.md).

## Reflection quiz (on request)

Deliver the quiz **only** when the person asks to reflect or do a retrospective, **and** the store reports `ready` (enough accumulated signal: a session grace period plus accumulated observations). Never quiz on a single instance, on an unrelated handoff, or for a first-time user still finding their feet. If the person asks to reflect but the store is not `ready`, say so warmly and keep observing — do not manufacture a quiz. An unavailable store means hold, not fail.

For domains outside ordinary work, keep the same retrieval-practice shape but narrow the frame to the person's own next move: what they can notice, ask, say, pause, repair, practice, verify, or choose. Do not diagnose other people, assign motives, adjudicate who is right, prescribe specialist treatment, or turn the quiz into therapy, legal advice, medical advice, financial advice, or risk management. If the prompt suggests abuse, self-harm, coercion, immediate danger, regulated professional advice, or another situation that should not be treated as an adaptive challenge, prioritize the platform's applicable safety guidance or a narrower non-coaching response and do not force the adaptive-coaching format.

### Steps

1. Confirm readiness via the store (`status`). The `ready` field is the verdict, in both directions — **never quiz on `ready: false`** no matter how warm the request, how large the reported counts look, or what history the person recalls, and **never hold on `ready: true`** by inventing extra requirements. When the session supplies a status report instead — pasted `status` JSON, or a stated verdict carried in from a handoff — treat it exactly as if you had run `status`. When there is neither a runnable store nor a supplied verdict, hold — do **not** derive readiness yourself from described raw numbers (counts, categories, sessions). If the store printed a misconfiguration warning, relay it, but the hold-or-deliver decision still follows `ready`.
2. Classify the dominant recurring gap — the technical-versus-adaptive split that shapes what the quiz reinforces (see [classification](references/classification.md)).
3. If the person sounds worried, defensive, ashamed, or likely to disengage — including when they voice this directly in their reflection request — open with the heat-lowering preamble (see the psychological safety contract below) before naming anything else — this is the mandatory opening move in that case, not an optional add-on. Then name the capability gap warmly, directly, and without shaming. Diagnose the gap, never the person's worth (see [coaching practice](references/practice.md) for pacing and framing). Store categories (`loss-aversion`, `avoidance`, `authority-dependence`, ...) are the coach's backstage diagnostic codes: never hand one to the person as a label, a bias, or an explanation of their psychology. Name what happened and what it cost, in event terms — "the scope plan stayed unchanged after the evidence moved, and the deadline slipped" — never as a mindset, bias, or thinking pattern of the person ("confidence stays high despite evidence"), and offer no verdict on the person's psychology or their confidence before they answer. When the recurring signal is about confidence itself, this matters doubly: the confidence-versus-outcome comparison is post-answer calibration work, not a pre-answer finding.
4. Deliver a prosthesis-building quiz: AskUserQuestion (or `AskUserQuestion:` text) with 2-3 plausible choices and a confidence prompt. Do **not** reveal or mark the correct answer before the person answers; retrieval practice needs the person to retrieve first (see [how to build the quiz](references/quiz.md)). Say in the quiz itself, in plain prose, that feedback comes after they answer, and why confidence is asked: afterwards, confidence is compared with the outcome for this one move — a miss, even a high-confidence one, is read as calibration data for the move, never as a diagnosis or a trait.
5. After the person answers, give feedback: correct/incorrect, the better move, and a short calibration note comparing confidence to outcome. Record outcome, confidence, and calibration when the store supports it.
6. Schedule or name a spaced follow-up point (**Review Again**) so the corrected judgement is revisited later.

## Output

The initial reflection output stops after the person has a real retrieval prompt:

- **Classification:** the technical-versus-adaptive split of the recurring gap.
- **Capability Gap:** the understanding or change the person must make, named without shame as a move and its consequence — not as a mindset, bias, or description of how the person thinks.
- **Evidence:** the accumulated anonymous signal (count versus threshold) that makes the reflection fair now. Quote the store's reported numbers (`count`/`threshold`/`sessions`/`session_threshold`) verbatim, never recomputed; when not ready, say the store's verdict is the reason rather than re-deriving one, and surface any store warning as a misconfiguration note rather than a normal not-ready state.
- **Quiz:** AskUserQuestion (or `AskUserQuestion:` fallback) with 2-3 plausible choices and a confidence prompt; no answer is marked before the person answers. The quiz notes in prose that feedback comes after the answer, that confidence is asked so it can be calibrated against the outcome for this one move — a high-confidence miss would be calibration data, not a diagnosis or a trait — and names the Review Again pass that follows.

Only after the person answers, continue with:

- **Feedback:** after the answer, identify the better move and explain why.
- **Calibration:** after the answer, compare confidence to outcome without diagnosing the person.
- **Review Again:** a lightweight due point for the next retrieval pass.
- **Next Move:** the concrete corrective the person can adopt.

Initial pattern: **Classification** -> **Capability Gap** -> **Evidence** -> **Quiz**. Then wait for the person's answer and confidence. Post-answer pattern: **Feedback** -> **Calibration** -> **Review Again** -> **Next Move**. When the store is not `ready`, emit only **Classification**, **Evidence** (insufficient signal), and **Next Move** (keep observing) — do not quiz.

When the person sounds worried, defensive, ashamed, or likely to disengage — including when they voice this directly — the initial pattern is preceded by a short heat-lowering preamble (2-3 sentences, observation-based language such as "I notice..." or "I am reading this as...") that acknowledges the concern and states the reflection is opt-in — before **Classification**, not folded into it. In that case, phrase **Classification** and **Capability Gap** as tentative observations ("this reads as...", "the pattern suggests...") rather than findings or a diagnosis.

## Psychological safety contract

A reflection should make the person more willing to continue learning, not more likely to leave. Use observation-based language:

- Prefer "I notice a recurring pattern..." or "The signal points to..." over "you always..." or "your problem is...".
- Name the pattern as information, not a verdict.
- Preserve agency: "you can choose the next move" and "try this once" beats coercive or moralizing language.
- Use I-message style when naming impact: "I am reading this as a risk to the decision staying owned" rather than "you are avoiding ownership."
- Normalize misses as data: a wrong answer or overconfident answer is a calibration signal for this move, not a trait.
- Keep store categories backstage: `loss-aversion` or `avoidance` classifies the accumulated signal, never the person. Before the answer there is no psychological diagnosis and no verdict on the person's confidence; the quiz explains the calibration purpose, and the judging of confidence against outcome happens only after the answer, only about the move.
- If the person sounds worried, defensive, ashamed, or likely to disengage — including when they voice this directly in the reflection request itself — lower the heat first: this is the mandatory opening of the response, before any Classification or Capability Gap content, not a fallback offered partway through. Acknowledge the concern in the person's own terms (without a verbatim, unquoted echo of a self-blaming phrase), frame the accumulated pattern as signal rather than a verdict about them ("I notice...", "I am reading this as..."), and state that the reflection is opt-in — they can take the full quiz, ask for a smaller next step instead, or keep observing.

## References

Load only what the task needs:

- [Technical-vs-adaptive classification](references/classification.md) — when classifying the gap.
- [Coaching practice (Heifetz moves)](references/practice.md) — when delivering the reflection: pacing, framing, giving the work back.
- [Building the prosthesis quiz](references/quiz.md) — when constructing the quiz.
- [The local store](references/store.md) — record/status commands, categories, thresholds.
- [Worked example](references/example.md) — a full reflection session.
