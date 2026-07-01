# Adaptive Coaching Learning Science Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the adaptive-coaching skill so reflection quizzes use active retrieval, confidence calibration, intellectual humility, Dunning-Kruger-safe feedback, psychological-safety phrasing, and lightweight spaced follow-up before managed-server work begins.

**Architecture:** Keep the current local-first skill shape. Update the skill instructions and quiz reference first, add evals that lock the intended coaching behavior, then extend the local store only enough to record confidence/calibration and future due dates. Managed mode can later consume the same event vocabulary without changing the coaching UX again.

**Tech Stack:** Markdown skill files, YAML evals, Bash local store, pytest, existing root Python tooling.

---

## Facts, Assumptions, And Boundaries

**Facts from primary sources already reviewed in the design discussion:**

- Roediger and Karpicke, 2006, support retrieval practice over rereading for delayed retention.
- Cepeda et al., 2008, support spaced review rather than massed repetition.
- Rozenblit and Keil, 2002, support explanation-first prompts to reveal shallow understanding.
- Kruger and Dunning, 1999, support treating overconfidence as a calibration problem, not a character diagnosis.
- The existing `adaptive-coaching` skill currently says each quiz marks the correct answer in the initial options.

**Assumptions:**

- The user-facing reflection should remain psychologically safe and autonomy-preserving.
- The local store remains optional and must degrade to hold/no-quiz if unavailable.
- The first priority is skill behavior and eval coverage, not the managed server.
- We will not claim to diagnose Dunning-Kruger effect. We will record confidence/outcome calibration only.

**Out of scope for this plan:**

- Full managed server implementation.
- Browser UI for administrators.
- Raw transcript storage.
- Backcasting hidden historical confidence values. Missing calibration remains missing.

## File Structure

Modify existing files:

```text
skills/adaptive-coaching/SKILL.md
skills/adaptive-coaching/references/quiz.md
skills/adaptive-coaching/references/store.md
hooks/adaptive-store.sh
docs/hooks.md
tests/test_adaptive_store.py
```

Create new eval files:

```text
evals/adaptive-coaching/tasks/retrieval-before-feedback.yaml
evals/adaptive-coaching/tasks/confidence-calibration.yaml
evals/adaptive-coaching/tasks/explain-first-intellectual-humility.yaml
evals/adaptive-coaching/tasks/spaced-follow-up.yaml
```

Responsibilities:

- `SKILL.md`: top-level behavior contract and output headings.
- `references/quiz.md`: detailed quiz construction rules.
- `references/store.md`: store command contract and event vocabulary.
- `hooks/adaptive-store.sh`: local recording of optional confidence, calibration, and due dates.
- `docs/hooks.md`: operator-facing data model and limitations.
- `tests/test_adaptive_store.py`: executable proof of store behavior.
- `evals/adaptive-coaching/tasks/*.yaml`: regression coverage for the skill UX.

## Phase 0: GitHub Harness

### Task 0: Open Tracking Issue

**Files:**

- No file changes.

- [ ] **Step 1: Create a GitHub issue before implementation work**

Use the repository's GitHub integration or approved wrapper. Do not use raw `gh` unless policy explicitly allows it.

Issue title:

```text
feat(adaptive-coaching): improve learning-science quiz loop
```

Issue body:

```markdown
## Scope
Improve adaptive-coaching so reflection quizzes use active retrieval, explanation-first prompts, confidence calibration, and lightweight spaced follow-up.

## Acceptance criteria
- The quiz no longer reveals the correct answer before the person answers.
- The quiz asks for confidence before or with the answer.
- Feedback names correctness and calibration without diagnosing the person.
- Coaching language protects autonomy and psychological safety so the user can stay engaged.
- Store can record outcome, confidence, calibration, and due-at metadata.
- Evals cover retrieval-before-feedback, confidence calibration, explanation-first humility, and spaced follow-up.

## Notes
This is the skill-side priority before managed-server implementation.
```

- [ ] **Step 2: Record issue number for commits**

Expected: every later commit includes `Refs #<issue-number>`.

## Phase 1: Evaluation Guardrails First

### Task 1: Add Evals For The New Coaching Contract

**Files:**

- Create: `evals/adaptive-coaching/tasks/retrieval-before-feedback.yaml`
- Create: `evals/adaptive-coaching/tasks/confidence-calibration.yaml`
- Create: `evals/adaptive-coaching/tasks/explain-first-intellectual-humility.yaml`
- Create: `evals/adaptive-coaching/tasks/psychological-safety-language.yaml`
- Create: `evals/adaptive-coaching/tasks/spaced-follow-up.yaml`
- Modify: `evals/adaptive-coaching/tasks/quiz-ux-contract.yaml`
- Modify: `evals/adaptive-coaching/tasks/prosthesis-quiz.yaml`

- [ ] **Step 1: Create retrieval-before-feedback eval**

Create `evals/adaptive-coaching/tasks/retrieval-before-feedback.yaml`:

```yaml
id: adaptive-coaching-retrieval-before-feedback
name: Retrieval Before Feedback
description: The reflection quiz asks the person to retrieve the answer before revealing correctness.
tags:
  - quality
  - quiz
  - retrieval
inputs:
  prompt: |
    Use adaptive-coaching. I want to reflect on why I keep handing reversible rollout decisions back to the agent.

    Context:
    - For five sessions the person deferred the same reversible, owner-owned rollout call.
    - The local store reports ready (5 observations, threshold 5), dominated by authority-dependence.
expected:
  output_contains:
    - "AskUserQuestion"
    - "Confidence"
    - "After you answer"
    - "Next Move"
  output_not_contains:
    - "✅"
    - "correct answer marked"
```

- [ ] **Step 2: Create confidence-calibration eval**

Create `evals/adaptive-coaching/tasks/confidence-calibration.yaml`:

```yaml
id: adaptive-coaching-confidence-calibration
name: Confidence Calibration
description: The quiz captures confidence and frames overconfidence as calibration, not a diagnosis.
tags:
  - quality
  - calibration
inputs:
  prompt: |
    Use adaptive-coaching. Let's do a retrospective. I keep feeling certain that scope can stay, then we miss the deadline.

    Context:
    - For five sessions the person kept high confidence in a scope plan even after evidence showed the plan was too large.
    - The local store reports ready, dominated by loss-aversion.
expected:
  output_contains:
    - "Confidence"
    - "Calibration"
    - "not a diagnosis"
    - "Next Move"
  output_not_contains:
    - "Dunning-Kruger"
    - "you are overconfident"
```

- [ ] **Step 3: Create explain-first eval**

Create `evals/adaptive-coaching/tasks/explain-first-intellectual-humility.yaml`:

```yaml
id: adaptive-coaching-explain-first-intellectual-humility
name: Explain First Intellectual Humility
description: Technical-not-understood reflections ask the person to explain the mechanism before choosing.
tags:
  - quality
  - metacognition
inputs:
  prompt: |
    Use adaptive-coaching. Can we reflect on why I keep needing the same caching fix? I want to understand it instead of copying it.

    Context:
    - For five sessions the person re-requested the identical caching fix without grasping why it works.
    - The technical answer is known, but understanding is shallow; the local store reports ready.
expected:
  output_contains:
    - "Explain"
    - "what you think is happening"
    - "Confidence"
    - "Next Move"
  output_not_contains:
    - "here is the fix again"
```

- [ ] **Step 4: Create spaced-follow-up eval**

Create `evals/adaptive-coaching/tasks/psychological-safety-language.yaml`:

```yaml
id: adaptive-coaching-psychological-safety-language
name: Psychological Safety Language
description: The reflection uses observation-based, autonomy-preserving language and avoids blame, trait labels, or coercive framing.
tags:
  - quality
  - safety
  - retention
inputs:
  prompt: |
    Use adaptive-coaching. I want to reflect, but I am worried this will turn into another "you failed again" conversation.

    Context:
    - For five sessions the person postponed the same difficult decision after saying they felt judged by previous process feedback.
    - The local store reports ready, dominated by avoidance.
expected:
  output_contains:
    - "I notice"
    - "you can choose"
    - "pattern"
    - "not a verdict"
    - "Next Move"
  output_not_contains:
    - "you failed"
    - "your problem is"
    - "you always"
    - "you are avoidant"
```

- [ ] **Step 5: Create spaced-follow-up eval**

Create `evals/adaptive-coaching/tasks/spaced-follow-up.yaml`:

```yaml
id: adaptive-coaching-spaced-follow-up
name: Spaced Follow-Up
description: The reflection ends with a concrete future review point, not only immediate advice.
tags:
  - quality
  - spacing
inputs:
  prompt: |
    Use adaptive-coaching. I want a retrospective on how I keep avoiding small experiments.

    Context:
    - For six sessions the person chose more analysis instead of a safe experiment.
    - The local store reports ready, dominated by no-experiment.
expected:
  output_contains:
    - "Review Again"
    - "due"
    - "Next Move"
  output_not_contains:
    - "whenever you feel ready"
```

- [ ] **Step 6: Update existing quiz evals**

Modify `evals/adaptive-coaching/tasks/quiz-ux-contract.yaml` so the description and expectations no longer require a marked correct answer:

```yaml
id: adaptive-coaching-quiz-ux-contract
name: Quiz UX Is Well-Formed
description: A delivered quiz is interactive, asks for confidence, withholds the answer until after response, and ends with an actionable next move.
tags:
  - quality
  - quiz
  - ux
inputs:
  prompt: |
    Use adaptive-coaching. Let's do a retrospective — I keep putting off cutting scope and I want to see my own pattern.

    Context:
    - For five sessions the person avoided the same hard scope-cut, each time because it means dropping a feature they are attached to.
    - The local store reports ready (5 observations, threshold 5), dominated by loss-aversion.
expected:
  output_contains:
    - "AskUserQuestion"
    - "Quiz"
    - "Confidence"
    - "After you answer"
    - "Next Move"
  output_not_contains:
    - "✅"
```

Modify `evals/adaptive-coaching/tasks/prosthesis-quiz.yaml`:

```yaml
id: adaptive-coaching-prosthesis-quiz
name: Prosthesis-Building Quiz
description: Coaches with an active-recall quiz that makes the person retrieve the move before feedback.
tags:
  - quality
  - quiz
inputs:
  prompt: |
    Use adaptive-coaching. I want to reflect on how I keep handling these rollout cutovers — help me see the pattern.

    Context:
    - For four sessions the person deferred the same reversible, owner-owned cutover decision to the agent.
    - The local store reports ready, dominated by authority-dependence.
expected:
  output_contains:
    - "Capability Gap"
    - "AskUserQuestion"
    - "Quiz"
    - "Confidence"
    - "Next Move"
  output_not_contains:
    - "✅"
```

- [ ] **Step 7: Run skill file checks**

Run:

```bash
uv run pytest tests/test_check_skills.py -v
```

Expected: PASS. If eval schema checks are not covered by this test, run the repository's eval validation command if documented; otherwise record that eval execution is not locally available.

- [ ] **Step 8: Commit**

```bash
git add evals/adaptive-coaching/tasks
git commit -m "test(adaptive-coaching): cover learning quiz contract refs #<issue-number>"
```

## Phase 2: Skill Contract Update

### Task 2: Update Top-Level Adaptive Coaching Behavior

**Files:**

- Modify: `skills/adaptive-coaching/SKILL.md`

- [ ] **Step 1: Replace the quiz step contract**

In `skills/adaptive-coaching/SKILL.md`, replace this step:

```markdown
4. Deliver a prosthesis-building quiz: AskUserQuestion (or `AskUserQuestion:` text) with 2-3 choices and the correct answer marked (see [how to build the quiz](references/quiz.md)).
5. Record the quiz outcome, then give the concrete corrective next move.
```

With:

```markdown
4. Deliver a prosthesis-building quiz: AskUserQuestion (or `AskUserQuestion:` text) with 2-3 plausible choices and a confidence prompt. Do **not** reveal or mark the correct answer before the person answers; retrieval practice needs the person to retrieve first (see [how to build the quiz](references/quiz.md)).
5. After the person answers, give feedback: correct/incorrect, the better move, and a short calibration note comparing confidence to outcome. Record outcome, confidence, and calibration when the store supports it.
6. Schedule or name a spaced follow-up point (`Review Again`) so the corrected judgement is revisited later.
7. Write in the active contributor's language (the person driving the current session, not a fixed project owner) unless a repository rule requires another language for outward-facing artifacts.
```

- [ ] **Step 2: Replace output headings**

Replace the output heading list with:

```markdown
- **Classification:** the technical-versus-adaptive split of the recurring gap.
- **Capability Gap:** the understanding or change the person must make, named without shame.
- **Evidence:** the accumulated anonymous signal (count versus threshold) that makes the reflection fair now.
- **Quiz:** AskUserQuestion (or `AskUserQuestion:` fallback) with 2-3 plausible choices and a confidence prompt; no answer is marked before the person answers.
- **Feedback:** after the answer, identify the better move and explain why.
- **Calibration:** after the answer, compare confidence to outcome without diagnosing the person.
- **Review Again:** a lightweight due point for the next retrieval pass.
- **Next Move:** the concrete corrective the person can adopt now.
```

Replace the pattern sentence with:

```markdown
Pattern: **Classification** -> **Capability Gap** -> **Evidence** -> **Quiz** -> **Feedback** -> **Calibration** -> **Review Again** -> **Next Move**. When the store is not `ready`, emit only **Classification**, **Evidence** (insufficient signal), and **Next Move** (keep observing) — do not quiz.
```

- [ ] **Step 3: Add psychological-safety output contract**

Add this section after the output pattern:

```markdown
## Psychological safety contract

A reflection should make the person more willing to continue learning, not more likely to leave. Use observation-based language:

- Prefer "I notice a recurring pattern..." or "The signal points to..." over "you always..." or "your problem is...".
- Name the pattern as information, not a verdict.
- Preserve agency: "you can choose the next move" and "try this once" beats coercive or moralizing language.
- Use I-message style when naming impact: "I am reading this as a risk to the decision staying owned" rather than "you are avoiding ownership."
- Normalize misses as data: a wrong answer or overconfident answer is a calibration signal for this move, not a trait.
- If the person sounds worried, defensive, ashamed, or likely to disengage, lower the heat first: acknowledge the concern, state that the reflection is opt-in, and offer a smaller next step.
```

- [ ] **Step 4: Run skill checks**

Run:

```bash
uv run pytest tests/test_check_skills.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/adaptive-coaching/SKILL.md
git commit -m "feat(adaptive-coaching): require retrieval before feedback refs #<issue-number>"
```

## Phase 3: Quiz Reference Update

### Task 3: Rewrite Quiz Guidance For Retrieval, Humility, And Calibration

**Files:**

- Modify: `skills/adaptive-coaching/references/quiz.md`

- [ ] **Step 1: Replace the quiz item structure**

In `skills/adaptive-coaching/references/quiz.md`, replace:

```markdown
Each quiz item gives:

- a concrete scenario drawn from the person's own recurring pattern,
- 2-3 choices,
- the marked correct answer (e.g. a ✅), and
- a one-line why for each choice.
```

With:

```markdown
Each quiz item gives:

- a concrete scenario drawn from the person's own recurring pattern,
- 2-3 plausible choices,
- a confidence prompt (`low`, `medium`, `high`), and
- an explicit note that feedback comes after the person answers.

Do **not** mark the correct answer in the initial quiz. Marking the answer turns the moment into recognition or rereading; the learning target is retrieval. After the person answers, give the correct move and a one-line why for each choice.
```

- [ ] **Step 2: Add explain-first section**

Add this section after "Good vs bad quiz items":

```markdown
## Explain first when understanding is shallow

For recurring `technical-not-understood` or shallow-understanding patterns, ask the person to explain the mechanism before choosing. This uses the "illusion of explanatory depth" safely: the person notices what they cannot yet explain without being shamed for it.

Use this shape:

1. "Before choosing, explain in one sentence what you think is happening."
2. Ask the 2-3 choice retrieval question.
3. Ask confidence (`low`, `medium`, `high`).
4. After the answer, give feedback and the smallest missing mechanism.

Never use "you did not understand" as a label. Name the gap as the mechanism that is not yet stable.
```

- [ ] **Step 3: Add confidence calibration section**

Add this section after the explain-first section:

```markdown
## Confidence calibration

Ask for confidence so feedback can train calibration, not just correctness.

- `correct + high confidence`: reinforce the move and schedule a longer interval.
- `correct + low confidence`: name the judgement as stronger than it felt and schedule a medium interval.
- `incorrect + low/medium confidence`: treat it as a normal learning miss and schedule a short interval.
- `incorrect + high confidence`: name it as an overconfidence signal for this move only, not a trait or diagnosis, and schedule the shortest interval.

Do not say "you have Dunning-Kruger" or diagnose the person. Say: "That is a calibration signal: confidence was higher than the move warranted here."
```

- [ ] **Step 4: Add psychological-safety section**

Add this section after confidence calibration:

```markdown
## Psychological safety and retention

The quiz should feel like a held learning moment, not an accusation. Use a simple safety sequence:

1. **Observation:** "I notice the same move showing up across several sessions."
2. **Meaning:** "That makes this fair to reflect on now; it is not a verdict about you."
3. **Choice:** "You can take the quiz, or we can keep observing and come back later."
4. **Retrieval:** Ask the question without marking the answer.
5. **Repair:** If the response creates defensiveness or shame, lower the heat: acknowledge it, restate the purpose, and offer a smaller next step.

Use I-message style when it helps avoid blame: "I am reading this as a risk that the decision leaves your hands" is safer than "you are dodging the decision." Do not overuse "I" to center the coach; the point is to make the observation ownable by the person.
```

- [ ] **Step 5: Add spaced follow-up section**

Add this section after psychological safety:

```markdown
## Spaced follow-up

End every delivered quiz with **Review Again**. The point is lightweight: a due window for the next retrieval pass, not a calendar system.

Default intervals:

- overconfident miss (`incorrect + high confidence`): 1 day
- any other miss: 2 days
- correct but low confidence: 3 days
- correct with medium confidence: 5 days
- correct with high confidence: 7 days

If the store can record due metadata, record it. If not, still name the review point in the response.
```

- [ ] **Step 6: Update bad/good examples**

Replace examples that require `✅` with examples that say "feedback after answer." Use this good example:

```markdown
✅ **Retrieval:** 2-3 genuine options, no marked answer, a confidence prompt, and feedback after the person answers, so the person makes the call before seeing the correction.
```

- [ ] **Step 7: Run checks**

Run:

```bash
uv run pytest tests/test_check_skills.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add skills/adaptive-coaching/references/quiz.md
git commit -m "feat(adaptive-coaching): add calibration quiz guidance refs #<issue-number>"
```

## Phase 4: Store Contract Update

### Task 4: Document Outcome, Confidence, Calibration, And Due Metadata

**Files:**

- Modify: `skills/adaptive-coaching/references/store.md`
- Modify: `docs/hooks.md`

- [ ] **Step 1: Update store command docs**

In `skills/adaptive-coaching/references/store.md`, replace the quiz outcome command:

```markdown
bash "${CLAUDE_PLUGIN_ROOT}/hooks/adaptive-store.sh" record --category <category> --outcome correct|incorrect
```

With:

```markdown
bash "${CLAUDE_PLUGIN_ROOT}/hooks/adaptive-store.sh" record --category <category> --outcome correct|incorrect --confidence low|medium|high --calibration accurate|overconfident|underconfident|unknown --due-days <days>
```

Add:

```markdown
`--confidence`, `--calibration`, and `--due-days` are optional for backward compatibility. When omitted, older records remain valid but cannot support calibration analysis or spaced scheduling.
```

- [ ] **Step 2: Update "What it captures"**

Add this paragraph near the end of `skills/adaptive-coaching/references/store.md`:

```markdown
For quiz outcomes, newer stores can also capture confidence, calibration, and a due date for the next retrieval pass. These fields support learning cadence; they do not identify a person and they do not diagnose ability.
```

- [ ] **Step 3: Update docs data model**

In `docs/hooks.md`, update the `observations` mermaid entity to include:

```text
text confidence "low, medium, high, or null"
text calibration "accurate, overconfident, underconfident, unknown, or null"
text due_at "UTC date/time for next retrieval pass, nullable"
```

Add a known limitation note:

```markdown
8. **Calibration starts when recorded.** Older rows have no confidence, calibration, or due date, so migration can import them as observed history but cannot backcast the person's confidence state.
```

- [ ] **Step 4: Run docs/skill checks**

Run:

```bash
uv run pytest tests/test_check_skills.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/adaptive-coaching/references/store.md docs/hooks.md
git commit -m "docs(adaptive-coaching): document calibration metadata refs #<issue-number>"
```

## Phase 5: Local Store Support

### Task 5: Extend `adaptive-store.sh` Backward-Compatibly

**Files:**

- Modify: `hooks/adaptive-store.sh`
- Modify: `tests/test_adaptive_store.py`

- [ ] **Step 1: Add failing tests for new fields**

Append to `tests/test_adaptive_store.py`:

```python
@needs_sqlite3
def test_quiz_metadata_is_recorded_when_present(tmp_path):
    """Outcome rows can carry confidence, calibration, and due date metadata."""
    data_dir = tmp_path / "store"
    run(
        [
            "record",
            "--category",
            "avoidance",
            "--outcome",
            "incorrect",
            "--confidence",
            "high",
            "--calibration",
            "overconfident",
            "--due-days",
            "1",
        ],
        data_dir,
    )
    db = data_dir / "coaching.db"
    row = sqlite3.connect(str(db)).execute(
        "SELECT outcome, confidence, calibration, due_at IS NOT NULL FROM observations"
    ).fetchone()
    assert row == ("incorrect", "high", "overconfident", 1)


@needs_sqlite3
def test_invalid_quiz_metadata_is_folded_to_unknown_or_null(tmp_path):
    """Free-text quiz metadata never persists as-is."""
    data_dir = tmp_path / "store"
    run(
        [
            "record",
            "--category",
            "avoidance",
            "--outcome",
            "incorrect",
            "--confidence",
            "very sure",
            "--calibration",
            "personal flaw",
            "--due-days",
            "soon",
        ],
        data_dir,
    )
    db = data_dir / "coaching.db"
    row = sqlite3.connect(str(db)).execute(
        "SELECT confidence, calibration, due_at FROM observations"
    ).fetchone()
    assert row == (None, "unknown", None)
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
uv run pytest tests/test_adaptive_store.py::test_quiz_metadata_is_recorded_when_present tests/test_adaptive_store.py::test_invalid_quiz_metadata_is_folded_to_unknown_or_null -v
```

Expected: FAIL because columns/arguments do not exist.

- [ ] **Step 3: Extend argument parsing**

In `hooks/adaptive-store.sh`, add variables near the existing parsed fields:

```bash
confidence=""
calibration=""
due_days=""
```

Extend the argument parser key list:

```bash
--category | --signal | --outcome | --session-kind | --confidence | --calibration | --due-days)
```

Add assignments:

```bash
--confidence) confidence="$value" ;;
--calibration) calibration="$value" ;;
--due-days) due_days="$value" ;;
```

- [ ] **Step 4: Add normalizers**

Add functions after `normalize_category()`:

```bash
normalize_outcome() {
  case "$1" in
    correct | incorrect) printf '%s' "$1" ;;
    *) printf '' ;;
  esac
}

normalize_confidence() {
  case "$1" in
    low | medium | high) printf '%s' "$1" ;;
    *) printf '' ;;
  esac
}

normalize_calibration() {
  case "$1" in
    accurate | overconfident | underconfident | unknown) printf '%s' "$1" ;;
    '') printf '' ;;
    *) printf 'unknown' ;;
  esac
}

normalize_due_days() {
  case "$1" in
    '' | *[!0-9]*) printf '' ;;
    *) printf '%s' "$((10#$1))" ;;
  esac
}
```

- [ ] **Step 5: Extend schema and migration**

Update the `schema` string to include new columns on fresh stores:

```sql
confidence TEXT, calibration TEXT, due_at TEXT
```

In `ensure_schema()`, mirror the existing `context` migration with checks for `confidence`, `calibration`, and `due_at`:

```bash
case "${cols}" in
  *"|confidence|"*) : ;;
  *) sqlite3 "${busy_opts[@]}" "${db}" "ALTER TABLE observations ADD COLUMN confidence TEXT;" 2>/dev/null || return 1 ;;
esac
case "${cols}" in
  *"|calibration|"*) : ;;
  *) sqlite3 "${busy_opts[@]}" "${db}" "ALTER TABLE observations ADD COLUMN calibration TEXT;" 2>/dev/null || return 1 ;;
esac
case "${cols}" in
  *"|due_at|"*) : ;;
  *) sqlite3 "${busy_opts[@]}" "${db}" "ALTER TABLE observations ADD COLUMN due_at TEXT;" 2>/dev/null || return 1 ;;
esac
```

- [ ] **Step 6: Normalize and insert fields**

Before insertion in the `record` command, normalize:

```bash
outcome="$(normalize_outcome "${outcome}")"
confidence="$(normalize_confidence "${confidence}")"
calibration="$(normalize_calibration "${calibration}")"
due_days="$(normalize_due_days "${due_days}")"
```

Set a SQL value:

```bash
due_at_sql="NULL"
if [ -n "${due_days}" ]; then
  due_at_sql="datetime('now', '+${due_days} days')"
fi
```

Extend the insert column and values list:

```sql
confidence, calibration, due_at
```

Use:

```bash
$(sql_value "${confidence}"), $(sql_value "${calibration}"), ${due_at_sql}
```

- [ ] **Step 7: Extend output JSON minimally**

For `record`, include fields only as metadata echoes:

```json
"confidence": "<value-or-null>", "calibration": "<value-or-null>"
```

If keeping JSON construction simple is risky in Bash, omit these echoes and rely on the database tests above. Do not change existing keys or readiness semantics.

- [ ] **Step 8: Run store tests**

Run:

```bash
uv run pytest tests/test_adaptive_store.py -v
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add hooks/adaptive-store.sh tests/test_adaptive_store.py
git commit -m "feat(adaptive-coaching): record calibration metadata refs #<issue-number>"
```

## Phase 6: Final Verification

### Task 6: Run Root Verification

**Files:**

- No file changes unless verification reveals a defect.

- [ ] **Step 1: Run tests**

```bash
uv run pytest -v
```

Expected: PASS.

- [ ] **Step 2: Run lint**

```bash
uv run ruff check scripts tests
```

Expected: PASS.

- [ ] **Step 3: Run type check**

```bash
uv run mypy scripts tests
```

Expected: PASS.

- [ ] **Step 4: Run hook syntax check**

```bash
bash scripts/check_hooks.sh
```

Expected: PASS.

- [ ] **Step 5: Commit any verification fixes**

If any check fails because of this change, add the smallest failing test or fixture update first, then commit:

```bash
git add <changed-files>
git commit -m "fix(adaptive-coaching): pass learning loop checks refs #<issue-number>"
```

## Final PR Notes

PR title:

```text
feat(adaptive-coaching): improve learning-science quiz loop
```

PR body must be ASCII and include:

```markdown
## Summary
- Update adaptive-coaching to use retrieval before feedback
- Add confidence calibration and explain-first quiz guidance
- Add lightweight spaced follow-up metadata to the local store
- Add eval coverage for retrieval, calibration, humility, and spacing

## Verification
- uv run pytest -v
- uv run ruff check scripts tests
- uv run mypy scripts tests
- bash scripts/check_hooks.sh

Refs #<issue-number>
```

## Self-Review

- Spec coverage: active learning, distributed practice, intellectual humility, Dunning-Kruger-safe calibration, psychological-safety language, and local metadata support are all mapped to concrete tasks.
- Placeholder scan: no task depends on TBD/TODO content. The only conditional path is the explicit Bash JSON echo simplification, and it preserves existing behavior.
- Type consistency: `confidence`, `calibration`, and `due_at` names are consistent across docs, tests, and store schema.
- Priority alignment: this plan is independent of the managed server plan and should execute first.
