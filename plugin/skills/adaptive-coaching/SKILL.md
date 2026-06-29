---
name: adaptive-coaching
description: Coaches a person's recurring capability gap across sessions — a misunderstood technical challenge or an adaptive one — once enough local signal has accumulated, using an AskUserQuestion quiz to build durable understanding. Use for a repeated pattern, not a single in-the-moment decision (route those to decision-coaching).
---

# Adaptive Coaching

Adaptive coaching builds a person's durable capability on the path to a goal while preserving autonomy and psychological safety, and only after enough signal has accumulated to coach fairly.

**UTILITY SKILL:** invoked as `clairvoyance:adaptive-coaching` by `using-clairvoyance` for a person's recurring capability gap across sessions.

**Boundary with decision-coaching:** `decision-coaching` coaches a single decision in the moment (an LGTM or ambiguous call). `adaptive-coaching` coaches a *recurring* pattern across sessions, gated on accumulated signal, and builds durable capability with a quiz.

## Technical vs Adaptive

Diagnose which kind of work the blocker is (Heifetz). The split shapes *how* to coach, not *whether*:

- **Technical challenge:** a known answer exists. If the person already understands it, hand back the fix — no coaching needed. If they do not, coach the understanding: teach the known answer and let the quiz reinforce it.
- **Adaptive challenge:** progress needs the person to change a value, habit, belief, or behaviour. More information alone cannot solve it; coach by facilitating the person's own change.

Name the split — mislabeling an adaptive challenge as technical is the most common failure. Coach whenever the gap recurs and the person cannot yet make the call alone; skip only when the fix is understood and just execution remains.

## Data sufficiency gate

Coaching is fair only once a pattern is established, not on a single instance. Record each adaptive observation as anonymous signal, and coach only when the local store reports `ready`; an unavailable store means hold coaching, not fail. The exact record/status commands, categories, and storage details are in [the store reference](references/store.md).

## Steps

1. Split the blocker into its technical parts and its adaptive part.
2. If the technical fix is already understood and only execution remains, return it and stop. Otherwise coach the gap — teach a misunderstood technical challenge, or facilitate an adaptive one.
3. Record the adaptive observation as anonymous signal (see [the store reference](references/store.md)).
4. If the store is not `ready`, hold coaching. Acknowledge the pattern and note that more signal is needed before correction is fair.
5. When `ready`, name the capability gap warmly, directly, and without shaming. Diagnose the gap, never the person's worth.
6. Coach with a prosthesis-building quiz: portable question handoff — AskUserQuestion when available, otherwise `AskUserQuestion:` text — with 2-3 choices and the correct answer marked.
7. Record the quiz outcome, then give the concrete corrective next move.
8. Write in the project owner's language unless a repository rule requires another language for outward-facing artifacts.

## Prosthesis effect via quiz

The プロテーゼ (prosthesis) effect: coaching should become an extension the person internalises into durable judgement, not a crutch they depend on. Active recall through a quiz beats being told — retrieval practice is what makes the corrected judgement stick. Each quiz item gives a concrete scenario, 2-3 choices, the marked correct answer, and a one-line why. Keep questions non-leading and non-shaming; the goal is the person's own next correct call without the coach present.

## Output

Use these headings:

- **Classification:** the technical-versus-adaptive split of the blocker.
- **Capability Gap:** the understanding or change the person must make, named without shame (a misunderstood technical challenge or an adaptive one).
- **Evidence:** the accumulated anonymous signal (count versus threshold) that makes coaching fair now.
- **Quiz:** AskUserQuestion (or `AskUserQuestion:` fallback) with 2-3 choices and the marked correct answer.
- **Why:** the prosthesis effect the quiz builds.
- **Next Move:** the concrete corrective the person can adopt.

Pattern: **Classification** -> **Capability Gap** -> **Evidence** -> **Quiz** -> **Next Move**. When the store is not `ready`, emit only **Classification**, **Evidence** (insufficient signal), and **Next Move** (keep observing) — do not coach yet.

## Example

See a [worked adaptive-coaching session](references/example.md).
