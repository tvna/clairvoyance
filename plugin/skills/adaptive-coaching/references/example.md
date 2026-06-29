# Worked example: adaptive coaching

## Input

Help me get this release unblocked.

- For the fourth session running, the owner asks the agent to "just pick" the rollout cutover date instead of deciding it.
- Each time, the agent has already laid out the same two reversible options with a recommendation.
- The local store now reports `ready` (5 observations, threshold 5), mostly `authority-dependence` and `avoidance`.
- The owner says the blocker is "we need a better deploy tool."

## Output

**Classification:** The deploy tooling is a *technical* concern with a known fix and is not what stalls the cutover. The recurring stall is *adaptive*: a decision only the owner can own is being handed off each session. Treating it as a tooling problem is the mislabel.

**Capability Gap:** The cutover date is an owner judgement, not a task to delegate. The pattern to correct is reaching for a tool fix to avoid making the call — not a competence gap, a habit of deferring the irreversible choice.

**Evidence:** Five accumulated observations across four sessions (threshold reached), `authority-dependence` and `avoidance` dominant — enough signal to coach fairly, not a one-off.

**Quiz:** AskUserQuestion — *"A reversible cutover with two prepared options and a recommendation is waiting on you. What is the soundest next move?"*
- Ask the agent to choose the date — *creates dependence; the call is yours to own.*
- **Pick the recommended option now and set the rollback trigger — ✅ correct: you own the reversible call and keep the safety net.**
- Buy a new deploy tool first — *mislabels an adaptive call as a technical one.*

**Why:** Retrieving the right move under a concrete scenario — rather than being told — builds the prosthesis: next time the owner makes the reversible call themselves without the coach present.

**Next Move:** Owner selects the recommended cutover option and names the rollback trigger this session; record the quiz outcome so the store can tell whether the deferral habit is fading.
