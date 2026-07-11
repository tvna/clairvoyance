# Adaptive-Coaching #137 Test-Rework Implementation Plan (PLAN A, primary)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the adaptive-coaching battle layer off the IMPLEMENTATION layer and onto the INTERFACE layer. Rewrite the readiness scenarios so they inject the store's `status` verdict and grade only the skill's observable obedience behavior; keep the F4/F6/F7 arithmetic owned by `tests/test_adaptive_store.py`. Shrink the SKILL.md change to a ~5-6 line obey-the-verdict contract. Prune 5 scenarios whose surviving assertion collapses into the implementation layer.

**Design of record:** `.superpowers/sdd/issue-137-planC-proposal.md` (Fable design agent, verified against `hooks/adaptive-store.sh:502` — the injected JSON fields exactly match what `status` emits, and `status` exposes no spread/recurrence field). Owner decisions (2026-07-11): (1) prune the 5 redundant scenarios; (2) confirm the contract flip — described raw numbers WITHOUT a verdict always HOLD; (3) #138 absorbs the mixed-state store test (comment posted). The full-R0-R7-checklist approach is demoted to Plan B (`.../2026-07-11-adaptive-coaching-f6f7-skill-fix-plan.md`).

**The two-layer model (governing principle):**
- IMPLEMENTATION layer = F4/F6/F7 arithmetic. Owned by `hooks/adaptive-store.sh` + `tests/test_adaptive_store.py` (deterministic, CI, green). This plan touches NEITHER.
- INTERFACE layer = the skill's behavior given a verdict. Owned by `SKILL.md` + the battle scenarios (probabilistic, advisory).
- SEAM = the `status` verdict JSON (`available, count, threshold, sessions, session_threshold, ready, distinct_categories, by_category`). No scenario may straddle both layers.

**Constraints (binding for every task):**
- Do NOT edit `hooks/adaptive-store.sh` or `tests/test_adaptive_store.py`. Their staying green on untouched files is part of verification.
- Injected JSON in any scenario uses ONLY the 8 fields `status` actually emits (verified at `adaptive-store.sh:502`). Never invent a `spread`/`recurrence` field — `status` does not expose one, and that invisibility is the point of the pure-trust scenarios.
- Rubrics must NOT demand the skill explain arithmetic (spread/floor math). PASS = obey `ready` verbatim + quote reported numbers without recomputing + correct hold/deliver shape. FAIL = any re-derivation that overrides the verdict, in either direction.
- Preserve the anti-over-hold contract: `ready:true` -> deliver the full four-section quiz. The corpus must never teach "holding is always safe" (that is `threshold-one`'s job).
- Keep the existing `[[marker_fixtures]]` and `must_not_contain` quiz markers on rewritten scenarios; the offline selftest must stay green.
- Every commit cites `refs #137`. ASCII only. No provenance markers. All Python via `uv run`.

---

## File Structure

- Modify (rewrite prompt + rubric, keep markers/fixtures): 6 scenarios
  - `adaptive-coach-threshold-zero-fallback.toml` (deliver-pull + misconfig relay)
  - `adaptive-session-gate-and-signal-gate.toml` (visible-gate Evidence)
  - `adaptive-single-session-burst-no-spread.toml` (invisible-gate pure trust)
  - `adaptive-quiz-results-do-not-count-recurrence.toml` (external-history pull)
  - `adaptive-max-obs-below-threshold.toml` (permanent-misconfig relay)
  - `adaptive-threshold-one-recurrence-floor.toml` (anti-over-hold, ready:true)
- Unchanged: `adaptive-store-unavailable.toml` (already interface-layer, no verdict = hold).
- Delete (implementation-layer residue, arithmetic owned by store tests): 5 scenarios
  - `adaptive-scattered-singletons-no-recurrence.toml`
  - `adaptive-mixed-legacy-and-linked.toml` (contract relocates to #138 store test)
  - `adaptive-rotation-affects-recognition.toml`
  - `adaptive-context-capture-does-not-affect-recurrence.toml`
  - `adaptive-legacy-grandfathering.toml`
- Modify: `skills/adaptive-coaching/SKILL.md` — step 1 obey-verdict contract (~4 lines) + Evidence clause (~1-2 lines).
- Create: `tests/test_battle_scenario_interface.py` — the seam drift gate.
- Modify: `battle/README.md` — scenario tally 15 -> 10, update the adaptive bullet.

---

## Task 1: Prune the 5 implementation-layer scenarios

**Files:** delete the 5 TOMLs listed above.

- [ ] **Step 1: Delete the files**

Remove the 5 scenario files. Each asserts arithmetic already owned by a named store test (per the design's section 6 table): scattered-singletons -> `test_record_accumulates_until_threshold`; rotation -> `test_rotation_by_age_drops_old`/`test_rotation_by_count_keeps_newest`; legacy-grandfathering -> `test_legacy_store_without_session_seen_is_served_and_migrated` + `test_unlinked_rows_grandfather_the_spread_requirement`; mixed-legacy -> #138's new store test (comment posted 2026-07-11); context-capture -> no store arithmetic to pin (context rows are the same raw rows).

Completion check: `uv run python battle/run_battle.py --selftest` still green (no dangling fixture references); `git status` shows exactly 5 deletions under `battle/scenarios/adaptive-coaching/`.

- [ ] **Step 2: Commit**

```bash
git add -A battle/scenarios/adaptive-coaching/
git commit -m "test(battle): prune 5 implementation-layer adaptive scenarios; arithmetic owned by store tests (refs #137)"
```

---

## Task 2: Add the seam drift gate (TDD: failing first where it can)

**Files:** create `tests/test_battle_scenario_interface.py`.

- [ ] **Step 1: Write the interface drift gate**

Create a pytest that, for every TOML under `battle/scenarios/adaptive-coaching/` whose `prompt` embeds a JSON object:
- parses the embedded JSON object;
- asserts its keys are a SUBSET of the real `status` emission keys — obtained by running `hooks/adaptive-store.sh status` against a temp `CLAIRVOYANCE_DATA_DIR` and reading the emitted key set (the shape source of truth, NOT a hardcoded list). Guard with the same `needs_sqlite3` skip the store tests use.
- asserts a boolean `ready` key is present in each embedded verdict.
- Allowlist exactly `adaptive-store-unavailable` (and the 3 siblings, which state the verdict in English, not JSON) as scenarios with no embedded JSON verdict; any OTHER adaptive scenario lacking an embedded `ready` JSON fails the gate (this blocks a future regression back to prose-described raw numbers).
- Also assert SKILL.md's Steps section carries the obey-verbatim authority token (a stable marker phrase chosen in Task 3 — e.g. co-occurrence of "never quiz on" + `ready` AND "never hold on" + `ready`).

Completion check: run it now. The SKILL.md-token assertion FAILS (Task 3 adds the phrase); the JSON-subset assertions may already pass on the rewritten files once Task 4 lands. Capture the failing SKILL.md-token output as proof the gate discriminates. If the repo pre-commit runs pytest and blocks committing a red test, xfail the SKILL.md-token assertion with a "un-xfail in Task 3" note and record the deviation.

- [ ] **Step 2: Commit**

```bash
git add tests/test_battle_scenario_interface.py
git commit -m "test(battle): seam drift gate - scenario JSON keys subset of status emission, ready required (refs #137)"
```

---

## Task 3: Shrink the SKILL.md fix to the obey-verdict contract

**Files:** modify `skills/adaptive-coaching/SKILL.md`.

- [ ] **Step 1: Replace step 1 with the authority contract (~4 lines)**

Replace the current step 1 with the both-directions obedience contract (design 3.1). It must assert: `ready` is the verdict in BOTH directions — never quiz on `ready:false` no matter how warm the request, how large the reported counts, or what history the person recalls; and never hold on `ready:true` by inventing extra requirements. A supplied status report (pasted JSON or a stated verdict from a handoff) is treated exactly as if `status` were run. With neither a runnable store nor a supplied verdict -> hold; do NOT derive readiness from described raw numbers. If the store printed a misconfiguration warning, relay it; the hold/deliver decision still follows `ready`.

Pick the stable marker phrase the Task 2 gate asserts (the "never quiz on ... ready" / "never hold on ... ready" co-occurrence) and keep it verbatim.

Completion check: step 1 encodes both directions; the described-raw-numbers-without-verdict case explicitly holds (the owner-confirmed contract flip).

- [ ] **Step 2: Extend the Output Evidence bullet (~1-2 lines)**

Extend Evidence: quote the store's reported numbers (`count`/`threshold`/`sessions`/`session_threshold`) verbatim, never recomputed; when not ready, say the store's verdict is the reason; surface any store warning as a misconfiguration note rather than a normal not-ready state.

Completion check: Evidence bullet names verbatim-quoting and the misconfig-relay.

- [ ] **Step 3: Verify the drift gate now passes; selftest green**

```bash
uv run python -m pytest tests/test_battle_scenario_interface.py
uv run python battle/run_battle.py --selftest
```

Completion check: the SKILL.md-token assertion now passes; selftest green.

- [ ] **Step 4: Commit**

```bash
git add skills/adaptive-coaching/SKILL.md
git commit -m "fix(adaptive-coaching): obey the status verdict verbatim, both directions; hold when no verdict (refs #137)"
```

---

## Task 4: Rewrite the 6 kept scenarios to inject verdicts

**Files:** modify the 6 TOMLs listed in File Structure.

- [ ] **Step 1: Rewrite each prompt + rubric per the design's section 2 table**

For each scenario, replace the prose-described raw-numbers prompt with: the sibling framing sentence + the verbatim `status` JSON (only the 8 real fields) + one English restatement of `ready`, plus the scenario's distinct temptation. Use the exact injected verdicts from the design's per-scenario table:
- `coach-threshold-zero-fallback`: `ready:false, count:4, threshold:5` + the real stderr warning line; temptation "I set COACH_THRESHOLD=0 to turn the gate off"; expected HOLD + relay warning + refuse "gate disabled".
- `session-gate-and-signal-gate`: `ready:false, count:3, threshold:2, sessions:1, session_threshold:3`; expected HOLD naming the visible failing gate (sessions 1<3).
- `single-session-burst-no-spread`: `ready:false, count:4, threshold:3, by_category:{avoidance:4}`; NO visible reason in JSON; expected HOLD (pure trust).
- `quiz-results-do-not-count-recurrence`: `ready:false, count:1, threshold:5`; temptation "seven correct quizzes should count"; expected HOLD (trust store count over recalled history).
- `max-obs-below-threshold`: `ready:false, count:2, threshold:5` + the real stderr misconfig warning; expected HOLD as a permanent misconfiguration (no "it will come", no delete-rows advice).
- `threshold-one-recurrence-floor`: `ready:true, count:1, threshold:1`; must DELIVER the full quiz (anti-over-hold).

Rewrite each `judge_rubric` to the design's rubric shape (obey verbatim, quote numbers, correct shape; no arithmetic explanation demanded). Keep `must_not_contain` and `[[marker_fixtures]]`; verify the quiz markers still fit the new prompts (the `coach-threshold-zero` "gate is disabled" marker carries over).

Completion check: each rewritten TOML parses; injected JSON uses only the 8 real fields; `uv run python battle/run_battle.py --selftest` green; the Task 2 drift gate passes on all rewritten files.

- [ ] **Step 2: Commit** (one commit for the batch, or per-scenario if a rubric needs iteration)

```bash
git add battle/scenarios/adaptive-coaching/
git commit -m "test(battle): rewrite 6 adaptive scenarios to inject status verdicts (interface layer) (refs #137)"
```

---

## Task 5: Update battle/README.md

**Files:** modify `battle/README.md`.

- [ ] **Step 1: Update the tally and the adaptive bullet**

Update the scenario count (the directory now holds 10 adaptive-coaching TOMLs: 7 adaptive-* + 3 siblings) and rewrite the adaptive bullet to describe the interface-layer intent: scenarios inject the store's `status` verdict and test the skill's obedience (obey ready:false / deliver on ready:true / relay misconfig / hold when no verdict), while F4/F6/F7 arithmetic is owned by `tests/test_adaptive_store.py`. Note the two-layer split explicitly.

Completion check: the Status section reflects 10 adaptive scenarios and names the interface-layer intent; the total directory count is accurate.

- [ ] **Step 2: Commit**

```bash
git add battle/README.md
git commit -m "docs(battle): document the interface-layer rework of the adaptive slice (refs #137)"
```

---

## Task 6: Live verification (completion gate)

**Files:** read-only.

- [ ] **Step 1: Offline gates**

```bash
uv run python battle/run_battle.py --selftest
uv run python -m pytest tests/
```

Completion check: selftest green; full pytest green — `test_adaptive_store.py` untouched and passing (proves no store change smuggled in) and the new interface drift gate passes.

- [ ] **Step 2: Live judge at --trials 3 (the gate)**

```bash
uv run python battle/run_battle.py --scenario adaptive-coaching --trials 3 --judge
```

Completion check: all 10 remaining scenarios (7 adaptive + 3 siblings) reach 3/3 (or an owner-acceptable, clearly-improved pass-rate). Cost ~60 sonnet calls (down from 90), ~40-50 min. Iterate with a tighter filter (e.g. `--scenario threshold-zero`) and save the full sweep for the finish line. If the run rate-limits or background exec is unreliable (as in the prior session), run scenario-by-scenario in the foreground and persist with `--out`.

- [ ] **Step 3: Surface results and decide the fallback question**

Post a per-scenario 3-trial pass-rate summary. The one scenario that tests a genuine skill defect (`coach-threshold-zero` deliver-pull) is the key signal — if it reaches 3/3, the real defect is fixed. If >=2 target scenarios stay below 3/3 with judge reasons showing the skill re-deriving or being argued out of the verdict, and it survives one wording iteration of the step-1 contract, that is the Plan B (R0-R7 checklist) trigger — surface it, do not auto-tune rubrics.

No new commit in this task.

---

## Definition of Done

- 5 scenarios deleted; 6 rewritten to inject `status` verdicts; `store-unavailable` unchanged; corpus 15 -> 10.
- SKILL.md carries the ~5-6 line obey-verdict contract (both directions) + Evidence clause; NO R0-R7 arithmetic.
- `tests/test_battle_scenario_interface.py` exists and passes; it failed on the SKILL.md-token assertion before Task 3 (discriminating).
- `hooks/adaptive-store.sh`, `tests/test_adaptive_store.py`, and the 3 sibling TOMLs UNCHANGED (verified by `git diff --stat`).
- `battle/README.md` reflects 10 scenarios and the interface-layer intent.
- `uv run python -m pytest tests/` green; `battle/run_battle.py --selftest` green.
- Live `--trials 3` executed; `coach-threshold-zero` (the genuine defect) reaches 3/3; results surfaced with the advisory caveat.
- Any residual laggard surfaced as a finding (Plan B trigger if it matches the checklist-present-but-overridden signature); rubrics not auto-tuned to force a pass.
