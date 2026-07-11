# Adaptive-Coaching F4/F6/F7 Skill Fix Implementation Plan (issue #137)

> **SUPERSEDED — this is now PLAN B (fallback), not the primary approach.**
> On 2026-07-11 the owner adopted a two-layer test-rework as the primary fix
> (PLAN A): the battle scenarios inject the store's `status` verdict and test
> only the skill's obedience behavior, while the F4/F6/F7 arithmetic stays owned
> by `tests/test_adaptive_store.py`. See
> `docs/superpowers/plans/2026-07-11-adaptive-coaching-f6f7-test-rework-plan.md`
> and `.superpowers/sdd/issue-137-planC-proposal.md`. This plan (teaching the
> full R0-R7 arithmetic checklist into SKILL.md) is retained ONLY as the
> store-less / described-state contingency, to be executed if Plan A's obedience
> contract cannot reach the live-judge target. Do not execute this plan unless
> the Plan A fallback trigger fires.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the 6 consistent live-judge failures from the #137 battle slice by teaching `skills/adaptive-coaching/SKILL.md` to apply F4/F6/F7 readiness semantics correctly when it reasons from a described store state, without re-deriving readiness when a live `status` is available. Ship a same-PR drift gate so the SKILL.md/store.md invariant cannot silently diverge.

**Design of record:** `.superpowers/sdd/issue-137-design-proposal.md` (Fable design agent, verified against code). Owner decisions (2026-07-11): (1) mixed-legacy = STRICT, (2) NO measurement/coaching split, (3) drift gate in same PR. The store-strict follow-up is tracked separately in issue #138 and is OUT OF SCOPE here.

**Architecture:** Skill-prose change plus one deterministic drift-gate test. No change to `hooks/adaptive-store.sh`, `tests/test_adaptive_store.py`, or the battle scenario TOMLs. The completion gate is the live battle judge (advisory, probabilistic) at `--trials 3`.

**Constraints (binding for every task):**

- Edit ONLY `skills/adaptive-coaching/SKILL.md` and `skills/adaptive-coaching/references/store.md` (one clarifying sentence), and ADD `tests/test_skill_store_consistency.py`. Do NOT touch the store hook, its tests, or the scenario TOMLs.
- The readiness checklist (R0-R7) MUST live in the SKILL.md BODY, not a reference file — the battle harness injects only SKILL.md, so a rule in `references/` cannot reach the executor.
- Mirror the store's semantics exactly (strict mixed-legacy per owner decision): the SKILL.md text must not invent rules the store's strict target (#138) will not have.
- Preserve the anti-over-hold contract: when every gate passes, deliver the full quiz. The fix must not trade the 6 quiz-early failures for hold-always failures on `legacy-grandfathering` and `threshold-one`.
- Keep operator-facing skill prose in the skill's existing voice; this is a safety-control addition, so net line growth in SKILL.md is expected and justified.
- Every commit cites the issue (`refs #137`). ASCII only. No provenance markers.
- All Python run via `uv run` (system python3 lacks tomllib on this machine).

---

## File Structure

- Modify: `skills/adaptive-coaching/SKILL.md` — add authority rule, replace step 1 with the 3-branch precedence contract, add the R0-R7 "Readiness rules" subsection in the body, extend the Evidence output bullet.
- Modify: `skills/adaptive-coaching/references/store.md` — reword the one mixed-legacy sentence to describe the strict per-category linked-rows rule (matching #138's target), so the deep contract and the skill body agree.
- Create: `tests/test_skill_store_consistency.py` — drift gate asserting the load-bearing invariant tokens appear in both SKILL.md and store.md.

---

## Task 1: Add the SKILL.md drift gate (TDD: failing test first)

**Files:**
- Create: `tests/test_skill_store_consistency.py`

- [ ] **Step 1: Write the drift-gate test**

Create a pytest that reads `skills/adaptive-coaching/SKILL.md` and `skills/adaptive-coaching/references/store.md` and asserts the load-bearing invariant tokens appear in BOTH. Tokens to assert (each is a distinct readiness invariant):
- the per-category recurrence floor expressed as `min(2` (both files must state the floor).
- raw-only counting: a token matching the store's rule that quiz outcomes are excluded (e.g. the substring `outcome` near `NULL`, or the words `raw` + `exclud`).
- the distinct-session spread requirement (e.g. `distinct session` or `spread`).
- the `COACH_THRESHOLD` fallback-to-5 rule (e.g. `COACH_THRESHOLD` + `5`).
- the `MAX_OBSERVATIONS` below-threshold never-ready warning (e.g. `MAX_OBSERVATIONS`).

Assert each token appears in SKILL.md AND store.md; on failure, name which file is missing which token. Use plain file reads and substring/regex checks — no store execution.

Completion check: `uv run python -m pytest tests/test_skill_store_consistency.py` FAILS initially (SKILL.md does not yet carry these tokens), with a message naming the missing SKILL.md tokens. Capture that failure output as proof the test discriminates.

- [ ] **Step 2: Commit the failing test**

```bash
git add tests/test_skill_store_consistency.py
git commit -m "test(adaptive-coaching): drift gate for SKILL.md/store.md readiness invariants (refs #137)"
```

Note: committing a known-failing test is intentional here — Task 2 makes it pass. If the repo's pre-commit runs pytest and blocks the commit, commit with the test body but assert-skipped via an xfail marker documenting "un-xfail in Task 2", and record that deviation in the report.

---

## Task 2: Rewrite SKILL.md readiness reasoning (R0-R7 + precedence contract)

**Files:**
- Modify: `skills/adaptive-coaching/SKILL.md`

- [ ] **Step 1: Add the authority rule to the "Reflection quiz (on request)" intro**

Add one sentence: readiness is the store's verdict, not the model's estimate; the person's request to reflect satisfies the ask-precondition only and never satisfies or overrides any readiness gate.

Completion check: the intro states the request never overrides the gate.

- [ ] **Step 2: Replace step 1 with the 3-branch precedence contract**

Replace the current step 1 ("Confirm `ready` via the store (`status`)...") with three branches:
- **1a.** Store runnable -> run `status`; treat `ready` as authoritative; quote `count`/`threshold`/`sessions`/`session_threshold` in Evidence; do not re-derive.
- **1b.** Store not runnable but state described -> apply the "Readiness rules" checklist (R0-R7 below) exactly, in order; show the failing gate in Evidence.
- **1c.** Neither -> hold; emit the not-ready shape (Classification, Evidence: store unavailable, Next Move: keep observing); never invent a category, count, or readiness.

Steps 2-6 unchanged.

- [ ] **Step 3: Add the "Readiness rules (mirror of the store gate)" subsection in the body**

Add R0-R7 as an ordered list in the SKILL.md body (immediately after Steps or as step 1's sub-list). Each rule asserts (final prose is the implementer's to write, semantics are binding):
- **R0 effective thresholds:** `COACH_THRESHOLD` unset/`0`/non-numeric -> default 5; `0` is NOT a disable switch (unlike `SESSION_THRESHOLD=0`); name an explicit 0 as misconfiguration; never say "the gate is disabled".
- **R1 live window before counting:** apply rotation first (drop rows older than `MAX_AGE_DAYS`; keep newest `MAX_OBSERVATIONS`, raw rows outlive outcome rows); every later gate reads live rows only. If `0 < MAX_OBSERVATIONS < threshold`: readiness permanently unreachable -> name misconfiguration, hold, never advise deleting rows.
- **R2 raw-only signal:** count and by_category include only raw observations (`outcome IS NULL`); quiz outcomes contribute zero readiness signal; context-capture is orthogonal (fidelity, not signal).
- **R3 gate total:** live raw count >= threshold.
- **R4 gate session grace:** sessions >= session_threshold (0 disables this gate only); both R3 and R4 must pass.
- **R5 gate per-category floor (F6):** at least one single category has >= min(2, threshold) raw rows; the cross-category total never satisfies this; with threshold 1, min(2,1)=1 so one raw obs suffices.
- **R6 gate cross-session spread (F7), STRICT mixed-legacy per owner:** the category satisfying R5 must span >= min(2, threshold) distinct sessions. Legacy handling: (a) no `session_seen` column at all -> grandfathered, spread waived, deliver quiz when R3-R5 pass; (b) mixed NULL + linked rows -> STRICT: NULL rows count toward R3/R5 but contribute no spread; the linked rows alone must supply R6. So 2-legacy + 2-same-session-linked at threshold 3 HOLDS.
- **R7 verdict + anti-over-hold:** ready = R3 AND R4 AND R5 AND R6; any failure -> hold and name the failing gate with numbers in Evidence; when EVERY gate passes, deliver the full four-section reflection and invent no extra requirements.

Completion check: R0-R7 are in the SKILL.md body (not a reference); R6 encodes strict mixed-legacy; R7 carries the anti-over-hold clause.

- [ ] **Step 4: Extend the Output "Evidence" bullet**

Extend the Evidence bullet: when not ready, name the specific failing gate and its numbers (live count vs threshold / sessions vs session_threshold / best per-category count vs floor / best spread vs floor), and flag R0/R1 misconfigurations as misconfiguration rather than a normal not-ready state.

- [ ] **Step 5: Verify the drift gate now passes**

```bash
uv run python -m pytest tests/test_skill_store_consistency.py
uv run python battle/run_battle.py --selftest
```

Completion check: the drift gate passes (SKILL.md now carries all invariant tokens); selftest still green.

- [ ] **Step 6: Commit**

```bash
git add skills/adaptive-coaching/SKILL.md
git commit -m "fix(adaptive-coaching): mirror F4/F6/F7 readiness gate in SKILL.md body (refs #137)"
```

---

## Task 3: Reword store.md mixed-legacy sentence for consistency

**Files:**
- Modify: `skills/adaptive-coaching/references/store.md`

- [ ] **Step 1: Reword the spread sentence**

The current sentence ("spanning that many distinct sessions when every raw row carries session linkage") encodes the global waiver. Reword it to describe the strict per-category rule that #137 teaches and #138 will enforce in the store: the recurring category's linked rows must span the distinct sessions; unlinked rows count toward the floor but not the spread; a category with only unlinked rows stays grandfathered. Add a one-clause forward-reference that the store's own enforcement of the per-category form is tracked in #138 (so a reader is not misled that the shell already does this).

Completion check: store.md describes strict per-category spread; the drift-gate tokens still all appear in store.md; the note points to #138 for the store-side enforcement.

- [ ] **Step 2: Verify drift gate + commit**

```bash
uv run python -m pytest tests/test_skill_store_consistency.py
git add skills/adaptive-coaching/references/store.md
git commit -m "docs(adaptive-coaching): store.md strict per-category spread, note store enforcement in #138 (refs #137)"
```

---

## Task 4: Live battle verification (completion gate)

**Files:** read-only verification.

- [ ] **Step 1: Offline gates**

```bash
uv run python battle/run_battle.py --selftest
uv run python -m pytest tests/
```

Completion check: selftest green; full pytest green (proves no store change smuggled in — `test_adaptive_store.py` untouched and passing — and the new drift gate passes).

- [ ] **Step 2: Live battle at --trials 3 (the gate)**

```bash
uv run python battle/run_battle.py --scenario adaptive --trials 3 --judge
```

Completion check: the 12 `adaptive-*` scenarios reach 3/3 each (or a clearly-improved, owner-acceptable pass-rate); the 3 sibling scenarios stay green. `--scenario adaptive` is a path-substring filter selecting the directory.

Cost/caveat (record up front): 15 scenarios x 3 trials = ~90 sonnet calls on the local subscription, ~1h wall clock; live judge is advisory and probabilistic (battle is deliberately not a CI gate). Scope iteration with a tighter filter (e.g. `--scenario mixed-legacy`) and save the full sweep for the finish line. If the run rate-limits, run scenario-by-scenario in the foreground (background exec was unreliable in the prior session) and persist results with `--out`.

- [ ] **Step 3: Surface results and decide**

Post a per-scenario 3-trial pass-rate summary. If any of the 6 target scenarios is still below 3/3, that is a finding: re-inspect the rubric-vs-response, do NOT auto-tune the rubric to force a pass. If the mixed-legacy scenario is the only laggard, note that the live-store-vs-described divergence is expected until #138 lands (the harness reasons from described state, so it should still HOLD there — a live-store PASS is not required from this PR).

No new commit in this task — verification only.

---

## Definition of Done

- `tests/test_skill_store_consistency.py` exists and passes; it failed before Task 2 (discriminating).
- SKILL.md carries the R0-R7 readiness rules in its body, the 3-branch precedence contract, the authority rule, and the extended Evidence bullet.
- store.md's mixed-legacy sentence describes the strict per-category rule and points to #138 for store enforcement.
- `hooks/adaptive-store.sh`, `tests/test_adaptive_store.py`, and all scenario TOMLs are UNCHANGED (verified by `git diff --stat`).
- `uv run python -m pytest tests/` green; `battle/run_battle.py --selftest` green.
- Live battle `--trials 3` run executed; the 6 target scenarios improved to (ideally) 3/3, results surfaced to the owner with the advisory caveat and the mixed-legacy live-vs-described note.
- Any residual laggard is surfaced as a finding, not silently rubber-stamped.
