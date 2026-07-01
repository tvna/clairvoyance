# Building the prosthesis quiz

## Contents

- Quiz shape
- Good vs bad quiz items
- Explain first when understanding is shallow
- Confidence calibration
- Psychological safety and retention
- Spaced follow-up
- Meet the person where they are

## Quiz shape

The prosthesis effect: coaching should become an extension the person
internalises into durable judgement, not a crutch they depend on. Active recall
through a quiz beats being told — retrieval practice is what makes the corrected
judgement stick.

Why a quiz and not just the answer — the Heifetz grounding. Supplying the answer
is *authority*: it provides direction from on high and works for technical gaps,
where a known answer exists. But it cannot close an adaptive gap, and used there
it breeds dependence. *Leadership*, by contrast, mobilises people to do their own
learning; the move Heifetz calls **"giving the work back to the people"** — the
work belongs to whoever holds the problem, because only they can do the learning.
A retrieval quiz *is* giving the work back: the person
reaches the correct call themselves rather than receiving it, which is exactly
what builds the prosthesis. So match the form to the classification — for a
technical gap, reinforcing the right answer is fine; for an adaptive gap, the
quiz must make the person do the judgement, never hand it to them.

Each quiz item gives:

- a concrete scenario drawn from the person's own recurring pattern,
- 2-3 plausible choices,
- a confidence prompt (`low`, `medium`, `high`), and
- an explicit note that feedback comes after the person answers.

Do **not** mark the correct answer in the initial quiz. Marking the answer turns
the moment into recognition or rereading; the learning target is retrieval. After
the person answers, give the correct move and a one-line why for each choice.

Keep questions non-leading and non-shaming; the goal is the person's own next
correct call without the coach present. Keep the feedback on the move and its
consequence, not on the classification — lecturing the technical/adaptive
framework turns coaching into a topic to study and invites intellectualising the
work. Deliver via AskUserQuestion when available, otherwise an `AskUserQuestion:`
text block with the same choices.

## Good vs bad quiz items

Same gap, contrasting builds — the failure modes are subtle, so each ❌ is paired
with the ✅ that fixes it:

- ❌ **Leading:** *"You wouldn't hand off your own cutover call again, would
  you?"* — telegraphs the answer and shames; the person performs agreement
  instead of reasoning.
  ✅ **Non-leading:** *"A reversible cutover with two prepared options is waiting
  on you. What is the soundest next move?"* — a real choice to reason through.
- ❌ **Telling, not retrieving:** stating the correct move in prose, or offering a
  one-real-option "quiz" — that is supplying the answer (authority), not giving
  the work back.
  ✅ **Retrieval:** 2-3 genuine options, no marked answer, a confidence prompt,
  and feedback after the person answers, so the person makes the call before
  seeing the correction.
- ❌ **Generic:** *"What makes a good decision?"* — abstract, not their pattern.
  ✅ **Concrete:** drawn from the person's own recurring signal, so the recall
  transfers to the next real moment.

## Explain first when understanding is shallow

For recurring `technical-not-understood` or shallow-understanding patterns, ask
the person to explain the mechanism before choosing. This uses the "illusion of
explanatory depth" safely: the person notices what they cannot yet explain
without being shamed for it.

Use this shape:

1. "Before choosing, explain in one sentence what you think is happening."
2. Ask the 2-3 choice retrieval question.
3. Ask confidence (`low`, `medium`, `high`).
4. After the answer, give feedback and the smallest missing mechanism.

Never use "you did not understand" as a label. Name the gap as the mechanism that
is not yet stable.

## Confidence calibration

Ask for confidence so feedback can train calibration, not just correctness.

- `correct + high confidence`: reinforce the move and schedule a longer interval.
- `correct + low confidence`: name the judgement as stronger than it felt and schedule a medium interval.
- `incorrect + low/medium confidence`: treat it as a normal learning miss and schedule a short interval.
- `incorrect + high confidence`: name it as an overconfidence signal for this move only, not a trait or diagnosis, and schedule the shortest interval.

Do not say "you have Dunning-Kruger" or diagnose the person. Say: "That is a
calibration signal: confidence was higher than the move warranted here."

## Psychological safety and retention

The quiz should feel like a held learning moment, not an accusation. Use a simple
safety sequence:

1. **Observation:** "I notice the same move showing up across several sessions."
2. **Meaning:** "That makes this fair to reflect on now; it is not a verdict about you."
3. **Choice:** "You can take the quiz, or we can keep observing and come back later."
4. **Retrieval:** Ask the question without marking the answer.
5. **Repair:** If the response creates defensiveness or shame, lower the heat: acknowledge it, restate the purpose, and offer a smaller next step.

Use I-message style when it helps avoid blame: "I am reading this as a risk that
the decision leaves your hands" is safer than "you are dodging the decision." Do
not overuse "I" to center the coach; the point is to make the observation ownable
by the person.

## Spaced follow-up

End every delivered quiz with **Review Again**. The point is lightweight: a due
window for the next retrieval pass, not a calendar system.

Default intervals:

- overconfident miss (`incorrect + high confidence`): 1 day
- any other miss: 2 days
- correct but low confidence: 3 days
- correct with medium confidence: 5 days
- correct with high confidence: 7 days

If the store can record due metadata, record it. If not, still name the review
point in the response.

## Meet the person where they are

The quiz builds judgement only if the person can actually parse it — giving the
work back *at a rate they can stand*. A scenario pitched above their level gets
skim-read or guessed, and no learning happens. So calibrate to the person:

- **Plain language.** Write the scenario in concrete, everyday terms, and define
  any unavoidable term inline on first use — e.g. "the cutover (the moment traffic
  switches to the new release)".
- **Their lived instance, not an abstraction.** Anchor the scenario in the actual
  situation they were in and already understand, not a generalised reframing.
- **Scaffold a not-understood concept first.** When the gap is a concept they do
  not yet grasp (a recurring Type I technical gap), ask them to explain the
  mechanism first, then give the smallest missing piece after they answer — don't
  pose options that assume the understanding.

Calibrate vocabulary and scaffolding, never the difficulty of the call itself —
the judgement still belongs to the person. Lowering the language barrier is giving
the work back; handing over the answer is not.
