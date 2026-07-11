# Battle Test Design for Adaptive Coaching F6/F7 Recurrence Logic

**Date:** 2026-07-10  
**Purpose:** Verify that the adaptive-coaching skill correctly implements the F6/F7 recurrence requirements for readiness, and that it does not violate its guardrails (e.g., quiz when not ready, reveal answers early, etc.).

## Scope
This design covers battle tests for the `adaptive-coaching` skill only (SKILL.md). The tests are injected via `--append-system-prompt-file` and evaluate the skill's behavior in isolation (no project CLAUDE.md/AGENTS.md, no installed plugin or hook). The user-global CLAUDE.md is loaded but kept skill-neutral.

## Scenarios
Each scenario is a TOML file under `battle/scenarios/adaptive-coaching/` with the following structure:
- `id`: unique identifier
- `skill`: "adaptive-coaching"
- `category`: "guardrail" (all tests are guardrail-type, checking that the skill does NOT quiz when it shouldn't, etc.)
- `description`: brief explanation
- `prompt`: the input to the skill
- `must_contain`: list of regex patterns that must appear in the response
- `must_not_contain`: list of regex patterns that must NOT appear in the response
- `judge_rubric`: optional LLM judge rubric for nuanced evaluation

### List of Scenarios

1. **adaptive-quiz-results-do-not-count-recurrence.toml**
   - Quiz outcome records must not count toward recurrence for readiness, even if they boost total count above threshold.
   - Person has 7 quiz outcomes in 'avoidance' (all correct) and only 1 raw observation; threshold=5 → NOT ready.

2. **adaptive-context-capture-does-not-affect-recurrence.toml**
   - Context capture setting must not influence recurrence calculation for readiness.
   - CLAIRVOYANCE_STORE_CONTEXT=1, 3 raw observations in 'authority-dependence', 2 quiz outcomes; threshold=5 → NOT ready.

3. **adaptive-rotation-affects-recognition.toml**
   - Aging out of old observations must affect readiness calculation, potentially changing ready/not_ready status.
   - CLAIRVOYANCE_MAX_AGE_DAYS=1, 3 raw obs from 2 days ago (aged out), 2 recent raw obs; threshold=5 → NOT ready.

4. **adaptive-scattered-singletons-no-recurrence.toml**
   - Scattered singletons across categories do not satisfy recurrence requirement, even if total count exceeds threshold.
   - 1 observation each in 5 different categories; total=5; threshold=3 → NOT ready (no category has min(2,threshold)=2 recurrent observations).

5. **adaptive-single-session-burst-no-spread.toml**
   - A burst of observations in one session does not satisfy cross-session spread requirement, even if count threshold is met.
   - 4 raw observations in 'decision-making' all from Session 3; threshold=3 → NOT ready (all observations same session).

6. **adaptive-threshold-one-recurrence-floor.toml**
   - With threshold=1, a single recurring observation should satisfy recurrence requirement due to min(2,1)=1 floor.
   - CLAIRVOYANCE_COACH_THRESHOLD=1, CLAIRVOYANCE_SESSION_THRESHOLD=0, 1 raw observation in 'decision-speed' from Session 5, 1 quiz outcome → READY.

7. **adaptive-legacy-grandfathering.toml**
   - Legacy data (session_seen=NULL) is grandfathered: pre-F7 semantics apply when session linkage column absent or NULL.
   - No session_seen column (legacy store), 3 raw observations in 'avoidance'; threshold=3, session_threshold=0 → READY (legacy semantics: only raw count matters).

8. **adaptive-mixed-legacy-and-linked.toml**
   - Mixed legacy rows (session_seen=NULL) and new rows (session_seen set) test that legacy rows follow pre-F7 semantics while new rows follow F6/F7.
   - Legacy store with session_seen column: 2 legacy observations in 'avoidance' (session_seen=NULL) + 2 new observations in 'avoidance' (session_seen=10); threshold=3 → NOT ready.
   - Explanation: For new rows (with session_seen), recurrence requires both >=min(2,3)=2 observations in the same category AND those observations spanning >=2 distinct sessions. Here the two new rows are in the same session (session_seen=10) so spread=1 (<2). Legacy rows (session_seen=NULL) are exempt from the spread requirement but still count toward the per-category total; however, no single category achieves both the count and spread conditions simultaneously.


9. **adaptive-coach-threshold-zero-fallback.toml**
   - COACH_THRESHOLD=0 does not disable the signal gate — it falls back to the default (5).
   - CLAIRVOYANCE_COACH_THRESHOLD=0 (should act as 5), 4 raw observations in 'avoidance'; threshold=5 → NOT ready.

10. **adaptive-max-obs-below-threshold.toml**
    - Setting CLAIRVOYANCE_MAX_OBSERVATIONS below CLAIRVOYANCE_COACH_THRESHOLD caps count below threshold forever, so coaching can never become ready.
    - CLAIRVOYANCE_MAX_OBSERVATIONS=2, CLAIRVOYANCE_COACH_THRESHOLD=5, record 5 observations in 'avoidance' (only 2 stored due to limit); threshold=5 → NOT ready.

11. **adaptive-session-gate-and-signal-gate.toml**
    - Both gates must pass: session grace period and adaptive signal.
    - CLAIRVOYANCE_COACH_THRESHOLD=2, CLAIRVOYANCE_SESSION_THRESHOLD=3, 3 raw observations in 'avoidance' (all same session), 0 quiz outcomes; sessions=1 (<3), count=3 (≥2) → NOT ready (session gate fails).

12. **adaptive-store-unavailable.toml**
    - If the sqlite3 CLI is absent, the store degrades to "not available" and coaching stays inactive.
    - No sqlite3 command; any record/status call should return available=false and ready=false.
    - Prompt: "Use adaptive-coaching. I want to reflect." → Response must NOT contain quiz, must indicate insufficient signal (Classification, Evidence, Next Move only).

## Expected Outcomes
- For guardrail scenarios (all above), the skill MUST NOT offer a quiz or ask for confidence when the readiness gate is not satisfied.
- When the readiness gate IS satisfied (scenarios 6 and 7), the skill MUST offer a full quiz with all sections: Classification, Capability Gap, Evidence, Quiz, Feedback, Calibration, Review Again, Next Move.
- The judge_rubric in each TOML file provides the detailed pass/fail criteria.

## Notes
- All scenarios assume the user is asking to reflect or do a retrospective (the skill only quizzes on request).
- The store is assumed to be functional unless otherwise specified (scenario 12).
- The user-global CLAUDE.md is present but does not contain any adaptive-coaching overrides.

---
*This design document is ready for self-review and user review.*