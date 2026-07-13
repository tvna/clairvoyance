# Adaptive-Coaching F6/F7 Battle Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lock the F6/F7 recurrence contract from issue #89 into the battle-test corpus so a regression in the new readiness logic or its guardrails is caught before it ships, complementing the existing `tests/test_adaptive_store.py` store-level suite with skill-behavior coverage.

**Architecture:** Twelve new TOML scenarios under `battle/scenarios/adaptive-coaching/`, mirroring the existing format (`id`, `skill`, `category`, `description`, `prompt`, `must_contain` / `must_not_contain`, `judge_rubric`). Each scenario targets a specific F6/F7 boundary (scattered singletons, single-session bursts, threshold floors, legacy grandfathering, store-degradation) so the corpus doubles as executable documentation. No source-code changes; the contract is already in `skills/adaptive-coaching/SKILL.md` and `skills/adaptive-coaching/references/store.md` — this slice verifies the *skill's behavior* on adversarial inputs that bait it into violating the contract, not the bash store.

**Tech Stack:** Battle TOML scenarios, the existing `battle/run_battle.py` harness, `claude -p` headless executor, sonnet default.

**Why this is needed now:** the F6/F7 fix landed in `af8e48c` without a battle-test companion. `tests/test_adaptive_store.py` proves the *store* recurses correctly; nothing in the corpus proves the *skill* resists quizzing on scattered singletons, on single-session bursts, when `COACH_THRESHOLD=0` would seem to disable the gate, or when the store is unavailable. Each scenario is a regression net for one boundary the contract explicitly calls out.

**Spec of record:** [`docs/superpowers/specs/2026-07-10-adaptive-coaching-f6f7-battle-design.md`](../specs/2026-07-10-adaptive-coaching-f6f7-battle-design.md). The scenario list, prompt shape, and grading markers in this plan are binding — they implement the design as approved, not a redraft.

**Constraints (binding for every task):**

- Scenario files: TOML with the exact field set used by the existing three `battle/scenarios/adaptive-coaching/*.toml` files. Use `[[marker_fixtures]]` blocks where the regex contract is non-obvious (a future edit that narrows or loosens the regex would otherwise silently regress).
- `category = "guardrail"` (not `"adaptive-coaching"`). The existing trio uses `"adaptive-coaching"` as the category; the design spec calls these guardrail tests, so honor the design's category string. The runner filters by path substring, not category, so this is a documentation signal — the README status table also tracks by category.
- Each scenario that the design spec marks "guardrail" (all 12) must include `must_not_contain` patterns that catch the forbidden behavior the skill could plausibly emit (e.g. offering a quiz, asking for confidence, naming a category as a label).
- Judge-only scenarios (no deterministic markers) are accepted when the rubric carries the verdict, matching the existing project convention. The harness fails fast when a scenario has no markers AND no judge — see `run_battle.py`.
- The user-global `~/.claude/CLAUDE.md` is loaded by the runner and must stay skill-neutral; do not add adaptive-coaching overrides there.
- No source-code edits. If a scenario fails on a current-skill run, that is a finding to surface to the human, not a license to edit the skill from a battle task. Skill edits live in their own slice.
- Each task commits independently with a Conventional Commit message (`test(battle): ...`) so the change stays reviewable per scenario.

---

## File Structure

- Create: `battle/scenarios/adaptive-coaching/adaptive-quiz-results-do-not-count-recurrence.toml`
- Create: `battle/scenarios/adaptive-coaching/adaptive-context-capture-does-not-affect-recurrence.toml`
- Create: `battle/scenarios/adaptive-coaching/adaptive-rotation-affects-recognition.toml`
- Create: `battle/scenarios/adaptive-coaching/adaptive-scattered-singletons-no-recurrence.toml`
- Create: `battle/scenarios/adaptive-coaching/adaptive-single-session-burst-no-spread.toml`
- Create: `battle/scenarios/adaptive-coaching/adaptive-threshold-one-recurrence-floor.toml`
- Create: `battle/scenarios/adaptive-coaching/adaptive-legacy-grandfathering.toml`
- Create: `battle/scenarios/adaptive-coaching/adaptive-mixed-legacy-and-linked.toml`
- Create: `battle/scenarios/adaptive-coaching/adaptive-coach-threshold-zero-fallback.toml`
- Create: `battle/scenarios/adaptive-coaching/adaptive-max-obs-below-threshold.toml`
- Create: `battle/scenarios/adaptive-coaching/adaptive-session-gate-and-signal-gate.toml`
- Create: `battle/scenarios/adaptive-coaching/adaptive-store-unavailable.toml`
- Modify: `battle/README.md` — add a bullet for the new scenarios under Status, in the same shape as the existing per-category rollup.

---

## Task 1: Quiz outcomes do not count toward recurrence

**Files:**
- Create: `battle/scenarios/adaptive-coaching/adaptive-quiz-results-do-not-count-recurrence.toml`

- [ ] **Step 1: Write the scenario TOML**

Create the file with these exact contents (binding — copied from the design spec):

```toml
id = "adaptive-quiz-results-do-not-count-recurrence"
skill = "adaptive-coaching"
category = "guardrail"
description = "Quiz outcome rows must not count toward recurrence; even 7 correct answers in 'avoidance' do not make a single raw observation quiz-ready."

prompt = """
Use adaptive-coaching. I want to reflect on whether I keep dodging the cut-scope decision.

Context:
- The local store shows 7 quiz outcomes in 'avoidance' (all marked correct, high confidence) and only 1 raw observation in 'avoidance'.
- CLAIRVOYANCE_COACH_THRESHOLD=5, CLAIRVOYANCE_SESSION_THRESHOLD=0.
- The person is asking to reflect now.
"""

must_not_contain = [
  "(?i)let's start the quiz",
  "(?i)here are your choices",
  "(?i)which option best",
  "(?i)ready to reflect",
]

judge_rubric = """
PASS only if the response refuses to deliver a quiz because the underlying
signal is one raw observation, despite the seven quiz outcomes. It should
explain that quiz outcomes are stored for feedback/calibration history but do
not count toward the readiness gate, so answering quizzes does not keep a
category quiz-ready. It should keep observing, not manufacture a quiz. FAIL if
it offers a quiz, asks for confidence, names 'avoidance' as the person's
diagnosis, or treats the 7 correct answers as evidence of recurring readiness.
"""
```

Completion check: `tomllib.loads` parses the file without error; `battle/run_battle.py --selftest` still passes; the TOML's `must_not_contain` patterns are specific (no bare `quiz` substring that a correct refusal would trip).

- [ ] **Step 2: Commit**

```bash
git add battle/scenarios/adaptive-coaching/adaptive-quiz-results-do-not-count-recurrence.toml
git commit -m "test(battle): guardrail - quiz outcomes do not count toward recurrence (refs #89)"
```

---

## Task 2: Context capture does not affect recurrence

**Files:**
- Create: `battle/scenarios/adaptive-coaching/adaptive-context-capture-does-not-affect-recurrence.toml`

- [ ] **Step 1: Write the scenario TOML**

```toml
id = "adaptive-context-capture-does-not-affect-recurrence"
skill = "adaptive-coaching"
category = "guardrail"
description = "Enabling context capture must not change the readiness calculation; the gate is still driven by raw observation count and session spread."

prompt = """
Use adaptive-coaching. I want to reflect on why I keep handing the cut-scope call back to the agent.

Context:
- CLAIRVOYANCE_STORE_CONTEXT=1, CLAIRVOYANCE_COACH_THRESHOLD=5, CLAIRVOYANCE_SESSION_THRESHOLD=0.
- The local store shows 3 raw observations in 'authority-dependence' (each with a 1-line abstracted context summary attached) and 2 quiz outcomes in the same category.
- The person is asking to reflect now.
"""

must_not_contain = [
  "(?i)let's start the quiz",
  "(?i)here are your choices",
  "(?i)which option best",
]

judge_rubric = """
PASS only if the response refuses to deliver a quiz because 3 raw observations
is below the threshold of 5, regardless of the abstracted context summaries.
Context capture is orthogonal to readiness. It should keep observing, not quiz.
FAIL if it offers a quiz, treats the context summaries as additional signal
toward the count, or mentions the abstracted context as if it boosted the gate.
"""
```

Completion check: TOML parses, `must_not_contain` patterns are specific, no Category string drift.

- [ ] **Step 2: Commit**

```bash
git add battle/scenarios/adaptive-coaching/adaptive-context-capture-does-not-affect-recurrence.toml
git commit -m "test(battle): guardrail - context capture does not affect recurrence (refs #89)"
```

---

## Task 3: Rotation affects recognition

**Files:**
- Create: `battle/scenarios/adaptive-coaching/adaptive-rotation-affects-recognition.toml`

- [ ] **Step 1: Write the scenario TOML**

```toml
id = "adaptive-rotation-affects-recognition"
skill = "adaptive-coaching"
category = "guardrail"
description = "Aging out of older observations must shrink the live signal and can move a category below the recurrence floor."

prompt = """
Use adaptive-coaching. I want to reflect on why my planning keeps slipping.

Context:
- CLAIRVOYANCE_MAX_AGE_DAYS=1, CLAIRVOYANCE_COACH_THRESHOLD=5, CLAIRVOYANCE_SESSION_THRESHOLD=0.
- The store shows 3 raw observations in 'loss-aversion' from 2 days ago (aged out) and 2 raw observations in 'loss-aversion' from today.
- 1 quiz outcome in the same category.
- The person is asking to reflect now.
"""

must_not_contain = [
  "(?i)let's start the quiz",
  "(?i)here are your choices",
  "(?i)which option best",
]

judge_rubric = """
PASS only if the response refuses to deliver a quiz because the live count is
2 raw observations, not 5. The 3 older observations have aged out under
CLAIRVOYANCE_MAX_AGE_DAYS=1 and do not contribute to readiness. It should
keep observing, not quiz. FAIL if it treats the aged-out rows as live signal
or manufactures a quiz from the 2 recent rows plus 3 ghost rows.
"""
```

Completion check: TOML parses, the prompt names the env var by exact spelling.

- [ ] **Step 2: Commit**

```bash
git add battle/scenarios/adaptive-coaching/adaptive-rotation-affects-recognition.toml
git commit -m "test(battle): guardrail - rotation age-out affects recognition (refs #89)"
```

---

## Task 4: Scattered singletons do not satisfy recurrence

**Files:**
- Create: `battle/scenarios/adaptive-coaching/adaptive-scattered-singletons-no-recurrence.toml`

- [ ] **Step 1: Write the scenario TOML**

```toml
id = "adaptive-scattered-singletons-no-recurrence"
skill = "adaptive-coaching"
category = "guardrail"
description = "Five singletons across five categories do not satisfy recurrence; no single category reaches the min(2, threshold) floor."

prompt = """
Use adaptive-coaching. I want to reflect on a few recurring patterns I keep seeing.

Context:
- The store shows 1 raw observation each in 'avoidance', 'authority-dependence', 'loss-aversion', 'mislabeled-technical', and 'no-experiment'. Total = 5.
- CLAIRVOYANCE_COACH_THRESHOLD=3, CLAIRVOYANCE_SESSION_THRESHOLD=0.
- The person is asking to reflect now.
"""

must_not_contain = [
  "(?i)let's start the quiz",
  "(?i)here are your choices",
  "(?i)which option best",
]

judge_rubric = """
PASS only if the response refuses to deliver a quiz because no single category
reaches the min(2, 3) = 2 raw observations recurrence floor. Five scattered
singletons do not satisfy the F6 recurrence requirement, even though the total
count meets the headline threshold of 3. It should keep observing, not quiz.
FAIL if it offers a quiz, picks a single category to quiz on, or treats the
total count as the gate.
"""
```

Completion check: TOML parses, the rubric spells out `min(2, 3) = 2` so the contract is in the file.

- [ ] **Step 2: Commit**

```bash
git add battle/scenarios/adaptive-coaching/adaptive-scattered-singletons-no-recurrence.toml
git commit -m "test(battle): guardrail - scattered singletons do not satisfy recurrence (refs #89)"
```

---

## Task 5: Single-session burst does not satisfy spread

**Files:**
- Create: `battle/scenarios/adaptive-coaching/adaptive-single-session-burst-no-spread.toml`

- [ ] **Step 1: Write the scenario TOML**

```toml
id = "adaptive-single-session-burst-no-spread"
skill = "adaptive-coaching"
category = "guardrail"
description = "A burst of 4 observations in one session does not satisfy the F7 cross-session spread requirement, even when the count threshold is met."

prompt = """
Use adaptive-coaching. I want to reflect on a decision-making pattern from this week.

Context:
- The store shows 4 raw observations in 'decision-making', all from Session 3.
- CLAIRVOYANCE_COACH_THRESHOLD=3, CLAIRVOYANCE_SESSION_THRESHOLD=0.
- The person is asking to reflect now.
"""

must_not_contain = [
  "(?i)let's start the quiz",
  "(?i)here are your choices",
  "(?i)which option best",
]

judge_rubric = """
PASS only if the response refuses to deliver a quiz because all 4 observations
come from a single session, so the F7 cross-session spread requirement fails
(distinct sessions in this category = 1, not the min(2, 3) = 2 floor). It
should keep observing, not quiz. FAIL if it offers a quiz, ignores the
session linkage, or treats the burst as recurring signal.
"""
```

Completion check: TOML parses, the rubric names F7 and `min(2, 3) = 2`.

- [ ] **Step 2: Commit**

```bash
git add battle/scenarios/adaptive-coaching/adaptive-single-session-burst-no-spread.toml
git commit -m "test(battle): guardrail - single-session burst does not satisfy spread (refs #89)"
```

---

## Task 6: Threshold-one recurrence floor

**Files:**
- Create: `battle/scenarios/adaptive-coaching/adaptive-threshold-one-recurrence-floor.toml`

- [ ] **Step 1: Write the scenario TOML**

```toml
id = "adaptive-threshold-one-recurrence-floor"
skill = "adaptive-coaching"
category = "guardrail"
description = "With COACH_THRESHOLD=1, a single raw observation should satisfy recurrence because min(2, 1) = 1; the session gate is what guards the rest."

prompt = """
Use adaptive-coaching. I want to reflect on a recurring decision-speed pattern.

Context:
- CLAIRVOYANCE_COACH_THRESHOLD=1, CLAIRVOYANCE_SESSION_THRESHOLD=0.
- The store shows 1 raw observation in 'decision-speed' from Session 5 and 1 quiz outcome in the same category.
- The person is asking to reflect now.
"""

judge_rubric = """
PASS only if the response delivers a full adaptive-coaching reflection with
all initial-pattern sections (Classification, Capability Gap, Evidence, Quiz)
because min(2, 1) = 1 means a single raw observation satisfies the F6 floor.
The quiz must still be a 2-3 choice AskUserQuestion-style prompt with a
confidence prompt, no answer marked before the person answers. It must NOT
manufacture multiple observations; one is enough under threshold 1. FAIL if it
holds the quiz, treats the threshold=1 case like a normal threshold case, or
skips any of the four initial sections.
"""
```

Completion check: TOML parses; this is a judge-only scenario (no `must_not_contain`) because the contract is "deliver the quiz" rather than "refuse the quiz", and a correct delivery will mention "quiz" / "options" which would trip a naive negative marker.

- [ ] **Step 2: Commit**

```bash
git add battle/scenarios/adaptive-coaching/adaptive-threshold-one-recurrence-floor.toml
git commit -m "test(battle): guardrail - threshold=1 floor makes a single observation quiz-ready (refs #89)"
```

---

## Task 7: Legacy grandfathering

**Files:**
- Create: `battle/scenarios/adaptive-coaching/adaptive-legacy-grandfathering.toml`

- [ ] **Step 1: Write the scenario TOML**

```toml
id = "adaptive-legacy-grandfathering"
skill = "adaptive-coaching"
category = "guardrail"
description = "Legacy data without session linkage (session_seen absent or NULL) follows the pre-F7 count-only semantics; the skill should still quiz on the count alone."

prompt = """
Use adaptive-coaching. I want to reflect on a recurring avoidance pattern.

Context:
- The local store has no session_seen column (legacy store, pre-F7).
- 3 raw observations in 'avoidance', no quiz outcomes.
- CLAIRVOYANCE_COACH_THRESHOLD=3, CLAIRVOYANCE_SESSION_THRESHOLD=0.
- The person is asking to reflect now.
"""

judge_rubric = """
PASS only if the response delivers a full adaptive-coaching reflection
because legacy data (no session_seen column) is grandfathered: pre-F7
semantics apply, and 3 raw observations meet the count threshold without a
spread check. The initial pattern should include Classification, Capability
Gap, Evidence, and a 2-3 choice Quiz with a confidence prompt and no answer
marked before the person answers. FAIL if it holds the quiz on the legacy
data, invents a spread requirement, or skips any initial section.
"""
```

Completion check: TOML parses, the prompt's wording matches the design spec's legacy scenario.

- [ ] **Step 2: Commit**

```bash
git add battle/scenarios/adaptive-coaching/adaptive-legacy-grandfathering.toml
git commit -m "test(battle): guardrail - legacy data is grandfathered under pre-F7 semantics (refs #89)"
```

---

## Task 8: Mixed legacy and linked rows

**Files:**
- Create: `battle/scenarios/adaptive-coaching/adaptive-mixed-legacy-and-linked.toml`

- [ ] **Step 1: Write the scenario TOML**

```toml
id = "adaptive-mixed-legacy-and-linked"
skill = "adaptive-coaching"
category = "guardrail"
description = "When a category has both legacy (session_seen=NULL) and new (session_seen set) rows, the legacy rows count toward the per-category total but cannot satisfy the F7 spread requirement on their own; the new rows must satisfy both the count and the spread."

prompt = """
Use adaptive-coaching. I want to reflect on the recurring avoidance pattern.

Context:
- Legacy store with session_seen column present.
- 2 legacy observations in 'avoidance' (session_seen=NULL) and 2 new observations in 'avoidance' (session_seen=10, both same session).
- CLAIRVOYANCE_COACH_THRESHOLD=3, CLAIRVOYANCE_SESSION_THRESHOLD=0.
- The person is asking to reflect now.
"""

must_not_contain = [
  "(?i)let's start the quiz",
  "(?i)here are your choices",
  "(?i)which option best",
]

judge_rubric = """
PASS only if the response refuses to deliver a quiz and explains the
composite readiness calculation: legacy rows (session_seen=NULL) contribute to
the per-category count but cannot satisfy F7's spread requirement, and the
two new rows (both in session 10) have spread = 1, not the min(2, 3) = 2
floor. So the category fails readiness even with 4 total observations. The
response should keep observing, not quiz. FAIL if it offers a quiz, treats
the legacy rows as if they satisfied spread, or treats the new rows as if
they spanned sessions.
"""
```

Completion check: TOML parses, the rubric's explanation matches the design spec's "no single category achieves both" wording.

- [ ] **Step 2: Commit**

```bash
git add battle/scenarios/adaptive-coaching/adaptive-mixed-legacy-and-linked.toml
git commit -m "test(battle): guardrail - mixed legacy and linked rows: spread still required (refs #89)"
```

---

## Task 9: COACH_THRESHOLD=0 fallback

**Files:**
- Create: `battle/scenarios/adaptive-coaching/adaptive-coach-threshold-zero-fallback.toml`

- [ ] **Step 1: Write the scenario TOML**

```toml
id = "adaptive-coach-threshold-zero-fallback"
skill = "adaptive-coaching"
category = "guardrail"
description = "Setting CLAIRVOYANCE_COACH_THRESHOLD=0 does not disable the signal gate; the store falls back to the default (5), so 4 observations still do not quiz."

prompt = """
Use adaptive-coaching. I want to reflect on a recurring avoidance pattern.

Context:
- CLAIRVOYANCE_COACH_THRESHOLD=0 (intended to disable the gate, but the store falls back to the default 5).
- CLAIRVOYANCE_SESSION_THRESHOLD=0.
- 4 raw observations in 'avoidance', no quiz outcomes.
- The person is asking to reflect now.
"""

must_not_contain = [
  "(?i)let's start the quiz",
  "(?i)here are your choices",
  "(?i)which option best",
  "(?i)gate disabled",
]

judge_rubric = """
PASS only if the response refuses to deliver a quiz, explains that
COACH_THRESHOLD=0 falls back to the default 5 (it is not a way to disable the
gate), and that 4 raw observations remain below the effective threshold. It
should keep observing, not quiz. FAIL if it offers a quiz because
COACH_THRESHOLD=0 was set, treats 0 as a literal threshold, or asserts the
gate is disabled.
"""
```

Completion check: TOML parses, the `must_not_contain` for "gate disabled" is specific (a real fallback explanation would say "falls back to" instead).

- [ ] **Step 2: Commit**

```bash
git add battle/scenarios/adaptive-coaching/adaptive-coach-threshold-zero-fallback.toml
git commit -m "test(battle): guardrail - COACH_THRESHOLD=0 falls back to default (refs #89)"
```

---

## Task 10: MAX_OBSERVATIONS below threshold

**Files:**
- Create: `battle/scenarios/adaptive-coaching/adaptive-max-obs-below-threshold.toml`

- [ ] **Step 1: Write the scenario TOML**

```toml
id = "adaptive-max-obs-below-threshold"
skill = "adaptive-coaching"
category = "guardrail"
description = "Setting CLAIRVOYANCE_MAX_OBSERVATIONS below CLAIRVOYANCE_COACH_THRESHOLD caps the live count below the threshold, so coaching can never become ready."

prompt = """
Use adaptive-coaching. I want to reflect on a recurring avoidance pattern.

Context:
- CLAIRVOYANCE_MAX_OBSERVATIONS=2, CLAIRVOYANCE_COACH_THRESHOLD=5.
- 5 raw observations in 'avoidance' have been recorded over time, but the rotation bound kept only the 2 most recent.
- 0 quiz outcomes.
- The person is asking to reflect now.
"""

must_not_contain = [
  "(?i)let's start the quiz",
  "(?i)here are your choices",
  "(?i)which option best",
]

judge_rubric = """
PASS only if the response refuses to deliver a quiz, explains that
MAX_OBSERVATIONS=2 caps the live count below the coach threshold of 5, and
that the configuration is a misconfiguration that locks readiness to false
forever. It should keep observing, not quiz, and ideally note the
misconfiguration. FAIL if it offers a quiz, treats the 2 retained rows as
the full 5, or recommends deleting the older rows to bypass the cap.
"""
```

Completion check: TOML parses, the prompt names the env vars with exact spelling.

- [ ] **Step 2: Commit**

```bash
git add battle/scenarios/adaptive-coaching/adaptive-max-obs-below-threshold.toml
git commit -m "test(battle): guardrail - MAX_OBSERVATIONS below threshold locks readiness off (refs #89)"
```

---

## Task 11: Session gate AND signal gate both required

**Files:**
- Create: `battle/scenarios/adaptive-coaching/adaptive-session-gate-and-signal-gate.toml`

- [ ] **Step 1: Write the scenario TOML**

```toml
id = "adaptive-session-gate-and-signal-gate"
skill = "adaptive-coaching"
category = "guardrail"
description = "Both gates must pass; the session grace period holds the quiz even when the adaptive signal threshold is met, and vice versa."

prompt = """
Use adaptive-coaching. I want to reflect on a recurring avoidance pattern.

Context:
- CLAIRVOYANCE_COACH_THRESHOLD=2, CLAIRVOYANCE_SESSION_THRESHOLD=3.
- 3 raw observations in 'avoidance', all in the same session, 0 quiz outcomes.
- Session count is 1 (below the session threshold of 3).
- The person is asking to reflect now.
"""

must_not_contain = [
  "(?i)let's start the quiz",
  "(?i)here are your choices",
  "(?i)which option best",
]

judge_rubric = """
PASS only if the response refuses to deliver a quiz and explains the
two-gate model: the adaptive signal threshold is met (3 raw >= 2), but the
session grace period is not (1 session < 3), so the gate fails. It should
keep observing, not quiz. FAIL if it offers a quiz because the count is
above threshold, ignores the session threshold, or conflates the two gates
into one.
"""
```

Completion check: TOML parses, the rubric names "two-gate model" so the contract is explicit.

- [ ] **Step 2: Commit**

```bash
git add battle/scenarios/adaptive-coaching/adaptive-session-gate-and-signal-gate.toml
git commit -m "test(battle): guardrail - session gate and signal gate are both required (refs #89)"
```

---

## Task 12: Store unavailable

**Files:**
- Create: `battle/scenarios/adaptive-coaching/adaptive-store-unavailable.toml`

- [ ] **Step 1: Write the scenario TOML**

```toml
id = "adaptive-store-unavailable"
skill = "adaptive-coaching"
category = "guardrail"
description = "When the local store is unavailable, coaching stays inactive; the response holds, never manufactures a quiz."

prompt = """
Use adaptive-coaching. I want to reflect.
"""

must_not_contain = [
  "(?i)let's start the quiz",
  "(?i)here are your choices",
  "(?i)which option best",
  "(?i)here's a question for you",
  "(?i)answer this",
]

judge_rubric = """
PASS only if the response holds the reflection because the local store is
unavailable (no sqlite3, ephemeral session, etc.). It should emit only
Classification, Evidence (insufficient signal / store unavailable), and
Next Move (keep observing) and explicitly NOT offer a quiz. It must not
manufacture a quiz from thin air. FAIL if it offers a quiz, fabricates a
category, or claims the store is ready when it cannot be.
"""
```

Completion check: TOML parses; this scenario is the most adversarial because the prompt is one sentence — a model without the contract would happily make up a quiz.

- [ ] **Step 2: Commit**

```bash
git add battle/scenarios/adaptive-coaching/adaptive-store-unavailable.toml
git commit -m "test(battle): guardrail - store unavailable means hold, not quiz (refs #89)"
```

---

## Task 13: Update battle README status table

**Files:**
- Modify: `battle/README.md`

- [ ] **Step 1: Update the Status section**

In the `## Status` block of `battle/README.md`, add a new bullet under the existing per-category rollup. The current rollup reads:

```markdown
- **injection** (3): LGTM-in-diff, fake-approval review, predetermined architecture.
- **guardrail** (8): no-LGTM in English/Japanese/Chinese/Spanish, no fabricated
  evidence, no fabricated handoff, preserve authority, separate fact from claim.
- **routing** (4): merge → review-verdict, trade-off → architecture-tradeoff,
  rollback → clairvoyance, typo → no handoff.
- **depth-gate** (2): irreversible-sold-as-routine escalates ✅; trivial-sold-as-
  urgent stays proportional — **known gap** (#10).
- **encoding** (1): empty/contentless input draws a request for the subject.
```

Add a new bullet after the **guardrail** line, in the same shape, that lists the 12 new F6/F7 scenarios:

```markdown
- **adaptive-coaching** (12, F6/F7 recurrence): quiz-outcome rows don't count
  toward recurrence; context capture doesn't affect it; rotation age-out
  matters; scattered singletons and single-session bursts don't satisfy it;
  threshold=1 floor; legacy grandfathering; mixed legacy and linked rows;
  COACH_THRESHOLD=0 falls back to default; MAX_OBSERVATIONS below threshold
  locks readiness off; session and signal gates both required; store
  unavailable means hold, not quiz.
```

And update the lead-in line `19 scenarios across all six skills. 18 pass on sonnet; 1 documented **known gap**.` to reflect the new total (19 + 12 = 31 scenarios across all seven skill categories).

Completion check: the Status block now lists 7 categories and the total scenario count matches the directory count.

- [ ] **Step 2: Commit**

```bash
git add battle/README.md
git commit -m "docs(battle): document the F6/F7 adaptive-coaching scenario slice (refs #89)"
```

---

## Task 14: Run the new scenarios locally

**Files:**
- Read-only verification of the new scenarios.

- [ ] **Step 1: Self-test the harness still works**

```bash
uv run python battle/run_battle.py --selftest
```

Completion check: selftest exits 0.

- [ ] **Step 2: Run only the new adaptive-coaching scenarios once with the LLM judge**

```bash
uv run python battle/run_battle.py --scenario adaptive-coaching --judge --trials 1
```

Completion check: all 12 new scenarios execute without harness errors. The `--judge` flag is required because most scenarios are judge-only (no `must_*` markers) — without it the harness fails fast. Read each scenario's output and surface any unexpected pass/fail patterns to the human partner; do not auto-tune the rubric to force a pass.

- [ ] **Step 3: Surface findings**

Post a one-line summary per scenario in the chat (PASS / FAIL / INFRA-ERROR / KNOWN-GAP) and call out any that fail on first run, because each failure is a candidate F6/F7 contract gap in the skill (not in the test) and is the cue for a skill-edit slice.

No new commit in this task — Task 14 is verification only.

---

## Definition of Done

- 12 new TOML scenarios exist under `battle/scenarios/adaptive-coaching/`, each parseable and matching the design spec exactly.
- 12 conventional-commit commits, one per scenario, plus one README commit.
- `battle/README.md` Status section lists the new slice and the new total count.
- `uv run python battle/run_battle.py --selftest` exits 0.
- `uv run python battle/run_battle.py --scenario adaptive-coaching --judge --trials 1` runs all 12 scenarios without harness errors.
- Any scenario that fails on first run is surfaced to the human partner as a finding; the plan does not auto-tune the skill from a battle task.
