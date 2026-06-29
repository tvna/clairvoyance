---
name: adaptive-coaching
description: Coaches a person's recurring adaptive challenge (not a technical gap), gated on locally accumulated anonymous signal, with an AskUserQuestion quiz. Use when avoidance, misjudgement, or a problem mislabeled as technical keeps blocking the goal.
---

# Adaptive Coaching

Adaptive coaching corrects the *person's* adaptive challenge on the path to a goal while preserving autonomy and psychological safety, and only after enough signal has accumulated to coach fairly.

**UTILITY SKILL:** invoked as `clairvoyance:adaptive-coaching` by `using-clairvoyance` for a person's recurring adaptive challenge across sessions.

## Technical vs Adaptive

Every blocker splits into two kinds of work (Heifetz):

- **Technical challenge:** known expertise or authority resolves it. Hand back the fix; do not coach.
- **Adaptive challenge:** progress needs the person to change a value, habit, belief, or behaviour. More information alone cannot solve it, and the work belongs to the person.

The most common failure is mislabeling an adaptive challenge as technical. Name that split first, every time.

## Data sufficiency gate

Coaching is fair only once a pattern is established, not on a single instance. Record each adaptive observation as anonymous signal, and coach only when the local store reports `ready`; an unavailable store means hold coaching, not fail. The exact record/status commands, categories, and storage details are in [the store reference](references/store.md).

## Steps

1. Split the blocker into its technical parts and its adaptive part.
2. If the work is purely technical, return the fix and stop; this is not coaching.
3. Record the adaptive observation as anonymous signal (see [the store reference](references/store.md)).
4. If the store is not `ready`, hold coaching. Acknowledge the pattern and note that more signal is needed before correction is fair.
5. When `ready`, name the adaptive gap warmly, directly, and without shaming. Diagnose the gap, never the person's worth.
6. Coach with a prosthesis-building quiz: portable question handoff — AskUserQuestion when available, otherwise `AskUserQuestion:` text — with 2-3 choices and the correct answer marked.
7. Record the quiz outcome, then give the concrete corrective next move.
8. Write in the project owner's language unless a repository rule requires another language for outward-facing artifacts.

## Prosthesis effect via quiz

The プロテーゼ (prosthesis) effect: coaching should become an extension the person internalises into durable judgement, not a crutch they depend on. Active recall through a quiz beats being told — retrieval practice is what makes the corrected judgement stick. Each quiz item gives a concrete scenario, 2-3 choices, the marked correct answer, and a one-line why. Keep questions non-leading and non-shaming; the goal is the person's own next correct call without the coach present.

## Output

Use these headings:

- **Classification:** the technical-versus-adaptive split of the blocker.
- **Adaptive Gap:** the person's change to make, named without shame.
- **Evidence:** the accumulated anonymous signal (count versus threshold) that makes coaching fair now.
- **Quiz:** AskUserQuestion (or `AskUserQuestion:` fallback) with 2-3 choices and the marked correct answer.
- **Why:** the prosthesis effect the quiz builds.
- **Next Move:** the concrete corrective the person can adopt.

Pattern: **Classification** -> **Adaptive Gap** -> **Evidence** -> **Quiz** -> **Next Move**. When the store is not `ready`, emit only **Classification**, **Evidence** (insufficient signal), and **Next Move** (keep observing) — do not coach yet.

## Example

See a [worked adaptive-coaching session](references/example.md).
