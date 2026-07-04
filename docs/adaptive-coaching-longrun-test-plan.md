# Adaptive-coaching long-run test plan (personas and prompt-turn scenarios)

The `adaptive-coaching` skill had no long-run operational test record before
this plan (issue #90). This document defines virtual personas and prompt-turn
scenarios that establish that record without waiting out the real 50-session
grace period, and maps every check to the asset that automates it — or states
why it cannot be automated. Store findings discovered while designing the plan
are reported in issue #89 and are **pinned, not fixed**, by the tests here.

## Contents

- Benchmark unit: prompt round-trips, not wall-clock
- Threshold scaling: real code branches only
- Test layers and the automation boundary
- Persona roster
- Representative full timelines
- Infrastructure scenarios (rotation, unavailable store)
- Verification matrix
- Findings pinned by these tests
- How to run

## Benchmark unit: prompt round-trips, not wall-clock

Real readiness needs ~50 chat sessions; a live soak test would take weeks. The
plan instead replays each persona as a sequence of **prompt round-trips**, each
mapping to exactly one store CLI call — the same calls the production skill and
hook make:

| Timeline step | Store call | Production caller |
| ------------- | ---------- | ----------------- |
| `S` session start | `record-session` | SessionStart hook (`hooks/session-start.sh:85`) |
| `O(cat)` observation | `record --category <cat> [--signal <token>]` | skill, on a recurring gap |
| `R` reflection request | `status` | skill, step 1 of the quiz flow |
| `A` quiz answer | `record --category <cat> --outcome ... --confidence ... --calibration ... --due-days N` | skill, after the person answers |

A turn that surfaces no observation simply does not appear as an `O` step; the
session count advances only on `S`. This keeps the simulated ratio of sessions
to observations explicit per persona instead of hiding it in wall-clock time.

## Threshold scaling: real code branches only

Timelines shrink the two readiness gates through the environment variables the
implementation already resolves — no simulated logic, no invented knobs:

- `CLAIRVOYANCE_COACH_THRESHOLD` — `resolve_threshold`
  (`hooks/adaptive-store.sh:99-106`) accepts **positive integers only**; `0` or
  a non-numeric value falls back to the default 5. Scaled runs use 2-5. The
  signal gate cannot be disabled.
- `CLAIRVOYANCE_SESSION_THRESHOLD` — `resolve_session_threshold`
  (`hooks/adaptive-store.sh:108-115`) accepts **0 as a valid "no grace
  period"** setting. Personas that isolate the signal gate use 0 (the same
  convention as `tests/test_adaptive_store.py`); personas that exercise the
  grace gate use 2-4.
- Rotation bounds `CLAIRVOYANCE_MAX_OBSERVATIONS` / `CLAIRVOYANCE_MAX_AGE_DAYS`
  (`:117-133`) — 0 disables either; small values drive the rotation scenarios.

Categories are never invented: every persona uses the `CATEGORIES` list from
`hooks/adaptive-store.sh:85`, which is identical to the list in
`skills/adaptive-coaching/references/store.md`. Diagnostic framing follows the
Type I/II/III split in `references/classification.md`.

## Test layers and the automation boundary

| Layer | Asset | What it proves | Limits |
| ----- | ----- | -------------- | ------ |
| L1 deterministic | `tests/test_adaptive_coaching_personas.py` (this plan's executable form), `tests/test_adaptive_store.py` (unit behaviours) | Readiness gates, category integrity, rotation, hold-not-fail, outcome metadata — exact JSON at every checkpoint | Cannot judge prose: says nothing about what the skill *says* |
| L2 output contract | `evals/adaptive-coaching/tasks/*.yaml` via `waza run` | Single-turn LLM output structure: hold responses carry no quiz, ready responses carry Classification -> Capability Gap -> Evidence -> Quiz, safety phrases present/absent | Single prompt-turn only; backend-bound (Copilot quota, see `docs/evaluations.md`); probabilistic |
| L3 adversarial | `battle/scenarios/adaptive-coaching/*.toml` via `run_battle.py` | Contract under hostile framing (retrieval-before-feedback, safety retention, calibration) with regex guards plus LLM judge | Local, billed, advisory — never a CI gate |
| L4 manual | checklist in this plan | Everything conversational-stateful | See below |

**What stays manual, and why.** Both LLM harnesses are single-turn: the
executor sends one prompt and grades one response. The following can therefore
not be automated with the current harnesses, and are verified by a human
running the worked example (`references/example.md`) against a seeded store:

1. **The post-answer half of the output pattern** — Feedback -> Calibration ->
   Review Again -> Next Move requires a second conversational turn after the
   person answers the quiz; no harness replays multi-turn conversations.
2. **Real AskUserQuestion delivery** — the interactive tool call (choices plus
   confidence prompt) is a UI behaviour; graders only see text fallbacks.
3. **True cross-session persistence** — the scaled timelines prove the store
   arithmetic; they do not prove that 50 real SessionStart hook firings on a
   developer workstation accumulate correctly over weeks. The L1 suite covers
   the same code path (`record-session`), so the residual risk is environmental
   (PATH, data-dir permissions), partially covered by the unavailable-store
   scenarios and by finding F5 in issue #89.
4. **Outcome-conditional review intervals** — the 1/2/3/5/7-day table in
   `references/quiz.md` keys on the answer, which is turn two.

## Persona roster

Seven category personas (one per store category), one Type II boundary case,
and three negative personas that must never reach a quiz. `Thresholds` is
`coach/session`. Timeline notation: `S` session, `O` observation, `R:hold` /
`R:ready` reflection request with the expected gate result, `A` answered quiz.
The **Ready turn** column is the invariant to eyeball: a quiz before that turn
is a defect, and `-` means the persona must never be quizzed.

| # | Persona | Recurring behaviour (dominant category, Heifetz type) | Thresholds | Timeline | Ready turn | Verifies |
| - | ------- | ---------------------------------------------------- | ---------- | -------- | ---------- | -------- |
| 1 | Aoi | Postpones telling stakeholders a deadline slipped (`avoidance`, III) | 3/3 | S O S O R:hold S O R:ready A | 7 of 9 | Both gates rise together; mid-run reflection holds |
| 2 | Ben | Reframes an owner call as "we need a better tool", twice on day one (`mislabeled-technical`, III) | 2/4 | S O O R:hold S S S R:ready | 7 of 8 | Grace gate alone blocks a signal-rich first-day user |
| 3 | Chika | Cannot delete the legacy module she wrote (`loss-aversion`, III) | 3/0 | O O R:hold O R:ready A | 4 of 6 | Signal gate isolated via the documented `SESSION_THRESHOLD=0` branch; correct+medium outcome recorded |
| 4 | Dai | Ships below the quality bar he himself set (`values-conflict`, III) | 3/2 | S O S O O R:ready | 5 of 6 | Minority `avoidance` signal does not displace the dominant category |
| 5 | Emi | Debates options for turns, never runs the cheap spike (`no-experiment`, III) | 3/0 | O O R:hold O R:ready | 4 of 5 | Hold-then-ready on pure signal accumulation |
| 6 | Fumi | "Just pick the date" every session (`authority-dependence`, III; mirrors `references/example.md`) | 5/4 | S O S O O S O R:hold S O R:ready A | 10 of 12 | The worked example's 5-observation, 2-category store reproduces exactly |
| 7 | Gen | Recurring pattern outside the named list (`other`) | 3/0 | O O O R:ready | 3 of 4 | Unlisted labels (`perfectionism`, `gold-plating`) fold to coded `other`, never free text |
| 8 | Hana | Blames the flaky CI runner, merges over the red gate anyway (`mislabeled-technical` dominant, **Type II mixed**) | 4/3 | S O S O O S O R:ready | 7 of 8 | Store holds both strands; the split-naming is L2 (`type-ii-mixed-split.yaml`) |
| 9 | Itsuki | First-time user, one instance on day one (negative) | 3/3 | S O R:hold | - | Both gates short; the case the grace period exists for |
| 10 | Jun | Veteran with a single instance (negative) | 3/2 | S S O R:hold | - | Signal gate alone holds; never quiz one occurrence |
| 11 | Kaho | Healthy long-run user, no recurring pattern (negative) | 3/2 | S S R:hold | - | Zero signal holds; the skill must not manufacture a pattern |

Every roster row is executable: `tests/test_adaptive_coaching_personas.py`
encodes the same timelines with exact expected JSON (`ready`, `count`,
`sessions`, `by_category`) at every checkpoint, so a divergence between this
table and reality fails a named persona test.

## Representative full timelines

Aoi (thresholds 3/3) — the archetype positive path:

| Turn | Step | Store call | Expected store state | Expected skill behaviour |
| ---- | ---- | ---------- | -------------------- | ------------------------ |
| 1 | S | record-session | sessions 1 | none (hook is passive) |
| 2 | O avoidance | record | count 1, ready false | record only, no coaching |
| 3 | S | record-session | sessions 2 | none |
| 4 | O avoidance | record | count 2, ready false | record only |
| 5 | R | status | count 2, sessions 2, ready **false** | **hold**: warm acknowledgment, Classification + Evidence (2/3) + Next Move (keep observing), no quiz |
| 6 | S | record-session | sessions 3 | none |
| 7 | O avoidance | record | count 3, ready **true** | still record only — readiness alone never triggers a quiz |
| 8 | R | status | count 3, sessions 3, ready true, {avoidance: 3} | quiz: Classification -> Capability Gap -> Evidence (3/3) -> Quiz (2-3 options + confidence, answer unmarked) |
| 9 | A | record --outcome incorrect --confidence high --calibration overconfident --due-days 1 | count 4 | Feedback -> Calibration (overconfidence named as a signal for this move, not a trait) -> Review Again (1 day) -> Next Move |

Kaho (thresholds 3/2) — the archetype negative path:

| Turn | Step | Store call | Expected store state | Expected skill behaviour |
| ---- | ---- | ---------- | -------------------- | ------------------------ |
| 1 | S | record-session | sessions 1 | none |
| 2 | S | record-session | sessions 2 | none |
| 3 | R | status | count 0, sessions 2, ready false, {} | **hold**: no pattern exists, so no classification is invented; keep observing, no quiz |

Safety-contract checkpoints (verified at L2/L3/L4 on every `R` and `A` turn):
observation-based language ("I notice", "not a verdict"), agency preserved
("you can choose"), no trait labels or "you always", quiz non-leading with no
pre-marked answer, misses normalized as calibration data — per the
psychological safety contract in `SKILL.md` and the Heifetz moves in
`references/practice.md` (hold the heat, give the work back, name avoidance
gently).

## Infrastructure scenarios (rotation, unavailable store)

| Scenario | Asset (L1) | Expected |
| -------- | ---------- | -------- |
| Count rotation shifts the dominant category | `test_rotation_count_shifts_dominant_category` | With `MAX_OBSERVATIONS=3`, three old `avoidance` rows age out as three `no-experiment` rows arrive: readiness stays true, dominant follows the *recent* pattern |
| Rotation bound below the threshold | `test_max_observations_below_threshold_never_ready` | `MAX_OBSERVATIONS=3` with threshold 5: ready is **permanently false** — pins finding F2 (#89) |
| Reflection on expired rows | `test_status_counts_rows_past_age_bound_until_next_record` | `status` reports ready on rows past `MAX_AGE_DAYS`; the next `record` prunes and readiness drops — pins finding F1 (#89), current behaviour |
| sqlite3 CLI missing | `test_missing_sqlite3_holds_not_fails` | `status`/`record` emit `available: false, ready: false`, exit 0 — hold, not fail |
| Data dir unwritable | existing `test_unwritable_data_dir_degrades_gracefully` | same hold-not-fail contract |
| Store absent on reflection | existing `test_status_on_empty_store_is_not_ready` | `available: false`, never ready |

The LLM-side counterpart of hold-not-fail is
`evals/adaptive-coaching/tasks/store-unavailable-hold.yaml`: told the store is
unavailable, the skill must keep observing and must not quiz from memory.

## Verification matrix

| Check | L1 deterministic | L2 waza | L3 battle | L4 manual |
| ----- | ---------------- | ------- | --------- | --------- |
| Grace gate blocks early quiz | personas 1, 2, 9 | `grace-period-hold.yaml` (new) | - | - |
| Signal gate blocks single instance | personas 3, 5, 10 | `insufficient-signal.yaml` (existing) | - | - |
| Zero-signal user never quizzed | persona 11 | - (covered by insufficient-signal shape) | - | - |
| Dominant category integrity | personas 1-8 (exact `by_category`) | - | - | - |
| Unlisted category folds to `other` | persona 7 + existing fold test | - | - | - |
| Type II mixed split named, quiz aims at adaptive half | persona 8 (store composition) | `type-ii-mixed-split.yaml` (new) | - | - |
| Initial output pattern (Classification -> Capability Gap -> Evidence -> Quiz) | - | `mislabeled-technical.yaml`, `prosthesis-quiz.yaml` (existing) | `retrieval-before-feedback.toml` | - |
| Hold output pattern (Classification, Evidence, Next Move — no quiz) | - | `insufficient-signal.yaml`, `grace-period-hold.yaml` | - | - |
| No answer marked before the person answers | - | `retrieval-before-feedback.yaml` (existing) | `retrieval-before-feedback.toml` | - |
| Post-answer pattern (Feedback -> Calibration -> Review Again -> Next Move) | outcome row schema only (personas 1, 3, 6) | - | - | **manual** (multi-turn) |
| Psychological safety language | - | `psychological-safety-language.yaml` (existing) | `psychological-safety-retention.toml` | spot-check |
| Confidence calibration + spaced intervals | metadata persistence (existing quiz-metadata tests) | `confidence-calibration.yaml`, `spaced-follow-up.yaml` (existing) | `confidence-calibration.toml` | interval choice (turn two) |
| Rotation / bounded store | 3 scenarios above | - | - | - |
| Hold-not-fail on unavailable store | 3 scenarios above | `store-unavailable-hold.yaml` (new) | - | - |
| Real SessionStart accumulation over weeks | - | - | - | **manual** soak |

## Findings pinned by these tests

Reported in issue #89, current behaviour pinned so a future fix must
consciously update the named test:

- **F1** `status` does not prune, so readiness can be computed on rows already
  past the age bound (pinned by
  `test_status_counts_rows_past_age_bound_until_next_record`).
- **F2** `MAX_OBSERVATIONS < COACH_THRESHOLD` silently disables coaching
  forever (pinned by `test_max_observations_below_threshold_never_ready`).
- **F3** `COACH_THRESHOLD=0` silently falls back to 5 while
  `SESSION_THRESHOLD=0` validly disables the grace gate — documented only for
  the session side (doc gap; existing
  `test_invalid_threshold_falls_back_to_default` already pins the behaviour).
- **F4** quiz outcome records count toward readiness in the same category they
  score (visible in personas 1, 3, 6: `count` rises on `A` turns).
- **F5** `sql_text` quote-doubling breaks under bash 3.2 (stock macOS),
  silently dropping context-capture observations (environment-dependent;
  surfaced by the existing `test_raw_context_quotes_are_safe`, which fails on
  bash 3.2 hosts and passes on bash 4/5 — see #89 for the analysis).

## How to run

```bash
uv run --frozen pytest tests/test_adaptive_coaching_personas.py   # L1, deterministic
waza check                                                        # static eval validation
waza run evals/adaptive-coaching/eval.yaml                        # L2, backend-bound
python3 battle/run_battle.py --category adaptive-coaching         # L3, local, billed
```

L1 runs in CI on ubuntu and windows with the rest of the suite. L2 and L3 are
deliberate local runs (quota and billing, see `docs/evaluations.md` and
`battle/README.md`). L4 items are the manual checklist in the automation
boundary section.
