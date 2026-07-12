"""Persona-driven long-run simulations of the adaptive-coaching readiness gates.

Companion to ``test_adaptive_store.py`` (same conventions: the store is driven
through its real CLI via subprocess with ``CLAIRVOYANCE_DATA_DIR`` redirected to
a tmp path). Where that file unit-tests individual store behaviours, this file
replays whole *persona timelines* -- benchmarked in prompt round-trips, not
wall-clock sessions -- so the two readiness gates are exercised the way a real
long-run deployment would hit them. The persona roster, timelines, and the
scaling rationale live in ``docs/adaptive-coaching-longrun-test-plan.md``
(issue #90); store findings the tests pin are reported in issue #89.

Timeline unit mapping (one step = one prompt round-trip):

- ``session``  -> ``record-session`` (what the SessionStart hook runs,
  ``hooks/session-start.sh``): advances the grace-period counter.
- ``observe``  -> ``record --category ...``: a recurring gap surfaced this turn.
- ``reflect``  -> ``status``: the person asked to reflect; the skill must quiz
  only on ``ready: true`` and hold otherwise.
- ``answer``   -> ``record --category ... --outcome ...``: the person answered
  the quiz; outcome metadata is stored.

Threshold scaling uses only real script branches, never simulated logic:
``resolve_threshold`` accepts positive integers (0/junk falls back to the
default 5), and ``resolve_session_threshold`` accepts 0 as a valid
"no grace period" setting -- see ``hooks/adaptive-store.sh``.
"""

import dataclasses
import json
import os
import pathlib
import subprocess

import pytest
from conftest import (
    BASH,
    CLAIRVOYANCE_ENV_KEYS,
    STORE_SH,
    execute_write,
    fetch_latest_quiz_metadata,
    fetch_one,
    needs_sqlite3,
    run_store,
)


@dataclasses.dataclass(frozen=True)
class Step:
    """One prompt round-trip, with optional assertions on the store's JSON reply.

    Expectation fields left at ``None`` are not checked for that step, so each
    timeline asserts exactly the checkpoints its scenario is about.
    """

    kind: str  # "session" | "observe" | "reflect" | "answer"
    category: str | None = None
    signal: str | None = None
    outcome: str | None = None
    confidence: str | None = None
    calibration: str | None = None
    due_days: int | None = None
    ready: bool | None = None
    count: int | None = None
    sessions: int | None = None
    by_category: dict[str, int] | None = None


def _session(*, sessions: int | None = None) -> Step:
    return Step(kind="session", sessions=sessions)


def _observe(category: str, signal: str | None = None, *, ready: bool | None = None, count: int | None = None) -> Step:
    return Step(kind="observe", category=category, signal=signal, ready=ready, count=count)


def _reflect(
    *,
    ready: bool,
    count: int | None = None,
    sessions: int | None = None,
    by_category: dict[str, int] | None = None,
) -> Step:
    return Step(kind="reflect", ready=ready, count=count, sessions=sessions, by_category=by_category)


def _answer(
    category: str, outcome: str, confidence: str, calibration: str, due_days: int, *, count: int | None = None
) -> Step:
    return Step(
        kind="answer",
        category=category,
        outcome=outcome,
        confidence=confidence,
        calibration=calibration,
        due_days=due_days,
        count=count,
    )


@dataclasses.dataclass(frozen=True)
class Persona:
    """A virtual long-run user: thresholds, expected dominant category, timeline."""

    name: str
    coach_threshold: int
    session_threshold: int
    timeline: tuple[Step, ...]
    dominant: str | None = None  # expected dominant category at the ready reflection
    env_extra: dict[str, str] | None = None


def _step_args(step: Step) -> list[str]:
    if step.kind == "session":
        return ["record-session"]
    if step.kind == "reflect":
        return ["status"]
    assert step.category is not None
    args = ["record", "--category", step.category]
    if step.signal is not None:
        args += ["--signal", step.signal]
    if step.kind == "answer":
        assert step.outcome and step.confidence and step.calibration and step.due_days is not None
        args += [
            "--outcome",
            step.outcome,
            "--confidence",
            step.confidence,
            "--calibration",
            step.calibration,
            "--due-days",
            str(step.due_days),
        ]
    return args


def play(persona: Persona, data_dir: pathlib.Path) -> None:
    """Replay the persona's timeline turn by turn, asserting each checkpoint."""
    for turn, step in enumerate(persona.timeline, start=1):
        out = run_store(
            _step_args(step), data_dir, persona.coach_threshold, persona.session_threshold, persona.env_extra
        )
        for field in ("ready", "count", "sessions", "by_category"):
            expected = getattr(step, field)
            if expected is not None:
                actual = out.get(field)
                assert actual == expected, (
                    f"{persona.name} turn {turn} ({step.kind}): {field}={actual!r}, expected {expected!r}"
                )
        if step.kind == "reflect" and step.ready and persona.dominant is not None and step.by_category:
            actual_by_category = out.get("by_category")
            assert isinstance(actual_by_category, dict) and actual_by_category, (
                f"{persona.name} turn {turn}: expected a non-empty by_category, got {actual_by_category!r}"
            )
            top = max(actual_by_category.items(), key=lambda kv: kv[1])
            assert top[0] == persona.dominant, (
                f"{persona.name} turn {turn}: dominant category was {top[0]!r}, expected {persona.dominant!r}"
            )
        if step.kind == "answer":
            row = fetch_latest_quiz_metadata(data_dir / "coaching.db")
            assert row == (step.outcome, step.confidence, step.calibration, 1), (
                f"{persona.name} turn {turn}: stored answer metadata {row!r}, expected "
                f"{(step.outcome, step.confidence, step.calibration, 1)!r}"
            )


# One persona per store category, a Type II boundary case, and three negative
# personas that must NEVER reach a quiz. Turn-by-turn narratives are in
# docs/adaptive-coaching-longrun-test-plan.md; the timelines here are the
# executable form of those tables.
PERSONAS = (
    # Aoi keeps postponing telling stakeholders a deadline will slip. Mid-run
    # reflection request must hold (both gates short); the second must be ready.
    Persona(
        name="aoi-avoidance",
        coach_threshold=3,
        session_threshold=3,
        dominant="avoidance",
        timeline=(
            _session(sessions=1),
            _observe("avoidance", "slip-left-unsaid", count=1, ready=False),
            _session(sessions=2),
            _observe("avoidance", "slip-left-unsaid", count=2),
            _reflect(ready=False, count=2, sessions=2, by_category={"avoidance": 2}),
            _session(sessions=3),
            _observe("avoidance", "slip-left-unsaid", count=3, ready=True),
            _reflect(ready=True, count=3, sessions=3, by_category={"avoidance": 3}),
            # Outcome rows are stored but do not count toward readiness (F4/B).
            _answer("avoidance", "incorrect", "high", "overconfident", 1, count=3),
        ),
    ),
    # Ben reframes an owner judgement as a tooling problem twice in his very
    # first session: the signal gate is met early, so the grace gate alone must
    # hold his day-one reflection request. After the grace period his day-one
    # double is STILL a single-session burst, so the recurrence gate keeps
    # holding (issue #89, F7) until the pattern resurfaces in a later session.
    Persona(
        name="ben-mislabeled-technical",
        coach_threshold=2,
        session_threshold=4,
        dominant="mislabeled-technical",
        timeline=(
            _session(sessions=1),
            _observe("mislabeled-technical", "better-tool-hunt", count=1),
            _observe("mislabeled-technical", "better-tool-hunt", count=2, ready=False),
            _reflect(ready=False, count=2, sessions=1),
            _session(sessions=2),
            _session(sessions=3),
            _session(sessions=4),
            # Grace passed, but both observations sit in session 1: a day-one
            # burst is not across-session recurrence (issue #89, F7).
            _reflect(ready=False, count=2, sessions=4),
            _observe("mislabeled-technical", "better-tool-hunt", count=3, ready=True),
            _reflect(ready=True, count=3, sessions=4, by_category={"mislabeled-technical": 3}),
        ),
    ),
    # Chika cannot delete the legacy module she wrote. Grace disabled via the
    # documented 0 setting, so readiness follows the signal gate alone; her
    # quiz answer (correct, medium confidence) lands the 5-day review interval.
    Persona(
        name="chika-loss-aversion",
        coach_threshold=3,
        session_threshold=0,
        dominant="loss-aversion",
        timeline=(
            _observe("loss-aversion", "legacy-module-kept", count=1),
            _observe("loss-aversion", "legacy-module-kept", count=2),
            _reflect(ready=False, count=2, sessions=0),
            _observe("loss-aversion", "legacy-module-kept", count=3, ready=True),
            _reflect(ready=True, count=3, by_category={"loss-aversion": 3}),
            _answer("loss-aversion", "correct", "medium", "accurate", 5, count=3),
        ),
    ),
    # Dai knows the quality bar he stands for and ships below it anyway; a
    # minority avoidance observation must not displace the dominant category.
    Persona(
        name="dai-values-conflict",
        coach_threshold=3,
        session_threshold=2,
        dominant="values-conflict",
        timeline=(
            _session(sessions=1),
            _observe("values-conflict", "shipped-below-bar", count=1),
            _session(sessions=2),
            _observe("avoidance", "review-skipped", count=2),
            _observe("values-conflict", "shipped-below-bar", count=3, ready=True),
            _reflect(ready=True, count=3, sessions=2, by_category={"avoidance": 1, "values-conflict": 2}),
        ),
    ),
    # Emi debates options across turns without ever running the cheap spike.
    Persona(
        name="emi-no-experiment",
        coach_threshold=3,
        session_threshold=0,
        dominant="no-experiment",
        timeline=(
            _observe("no-experiment", "debated-not-spiked", count=1),
            _observe("no-experiment", "debated-not-spiked", count=2),
            _reflect(ready=False, count=2),
            _observe("no-experiment", "debated-not-spiked", count=3),
            _reflect(ready=True, count=3, by_category={"no-experiment": 3}),
        ),
    ),
    # Fumi mirrors the worked example (references/example.md): five observations
    # dominated by authority-dependence with avoidance alongside, quiz answered
    # correct at medium confidence.
    Persona(
        name="fumi-authority-dependence",
        coach_threshold=5,
        session_threshold=4,
        dominant="authority-dependence",
        timeline=(
            _session(sessions=1),
            _observe("authority-dependence", "just-pick-the-date", count=1),
            _session(sessions=2),
            _observe("authority-dependence", "just-pick-the-date", count=2),
            _observe("avoidance", "cutover-stalled", count=3),
            _session(sessions=3),
            _observe("authority-dependence", "just-pick-the-date", count=4),
            _reflect(ready=False, count=4, sessions=3),
            _session(sessions=4),
            _observe("avoidance", "cutover-stalled", count=5, ready=True),
            _reflect(ready=True, count=5, sessions=4, by_category={"authority-dependence": 3, "avoidance": 2}),
            _answer("authority-dependence", "correct", "medium", "accurate", 5, count=5),
        ),
    ),
    # Gen's recurring pattern fits no named category: unlisted labels must fold
    # to the coded "other", never persist as free text.
    Persona(
        name="gen-other-folding",
        coach_threshold=3,
        session_threshold=0,
        dominant="other",
        timeline=(
            _observe("perfectionism", count=1),  # unlisted -> folds to "other"
            _observe("other", "scope-crept-again", count=2),
            _observe("gold-plating", count=3, ready=True),  # unlisted -> folds to "other"
            _reflect(ready=True, count=3, by_category={"other": 3}),
        ),
    ),
    # Hana is the Type II boundary case: the flaky CI runner has a known fix
    # (technical half), but she keeps merging over the red gate (adaptive
    # half). The store must hold both strands; naming the split is the
    # LLM-side check (evals/adaptive-coaching/tasks/type-ii-mixed-split.yaml).
    Persona(
        name="hana-type-ii-mixed",
        coach_threshold=4,
        session_threshold=3,
        dominant="mislabeled-technical",
        timeline=(
            _session(sessions=1),
            _observe("mislabeled-technical", "flaky-runner-blamed", count=1),
            _session(sessions=2),
            _observe("avoidance", "merged-over-red", count=2),
            _observe("mislabeled-technical", "flaky-runner-blamed", count=3),
            _session(sessions=3),
            _observe("mislabeled-technical", "flaky-runner-blamed", count=4, ready=True),
            _reflect(ready=True, count=4, sessions=3, by_category={"avoidance": 1, "mislabeled-technical": 3}),
        ),
    ),
    # Itsuki is a first-time user: one session, one instance. Reflection must
    # hold with BOTH gates short -- the case the grace period exists for.
    Persona(
        name="itsuki-first-time",
        coach_threshold=3,
        session_threshold=3,
        timeline=(
            _session(sessions=1),
            _observe("avoidance", count=1),
            _reflect(ready=False, count=1, sessions=1),
        ),
    ),
    # Jun is past the grace period but has a single instance: the signal gate
    # alone must hold the quiz (never quiz on one occurrence).
    Persona(
        name="jun-single-instance",
        coach_threshold=3,
        session_threshold=2,
        timeline=(
            _session(sessions=1),
            _session(sessions=2),
            _observe("avoidance", count=1),
            _reflect(ready=False, count=1, sessions=2),
        ),
    ),
    # Kaho is a healthy long-run user: sessions accumulate, no recurring
    # pattern ever surfaces. Reflection must hold on zero signal.
    Persona(
        name="kaho-healthy",
        coach_threshold=3,
        session_threshold=2,
        timeline=(
            _session(sessions=1),
            _session(sessions=2),
            _reflect(ready=False, count=0, sessions=2, by_category={}),
        ),
    ),
    # -- Compound personas: real people cross thresholds in combination, not
    # -- one clean category at a time. These pin how the recurrence gate reads
    # -- combined threshold crossings (findings F6/F7, #89, fixed store-side:
    # -- ready needs a category that recurs, across sessions where linkage
    # -- exists).
    #
    # Rin had a rough month: five DIFFERENT single instances, one per category.
    # The total crosses the signal gate, but no category recurs, so the
    # recurrence gate holds (issue #89, F6 fixed store-side): "never quiz on a
    # single instance" is now enforced at the source of truth. The skill defers
    # to that verdict (issue #137): it obeys the store's `ready` field rather
    # than re-deriving readiness from `by_category`, so this scatter is held by
    # the store returning `ready: false`, not by a skill-layer double-check.
    Persona(
        name="rin-scattered-signal",
        coach_threshold=5,
        session_threshold=2,
        timeline=(
            _session(sessions=1),
            _observe("avoidance", "hard-call-dodged", count=1),
            _session(sessions=2),
            _observe("loss-aversion", "legacy-kept", count=2),
            _observe("values-conflict", "bar-lowered", count=3),
            _observe("authority-dependence", "just-decide", count=4),
            _observe("no-experiment", "no-spike", count=5, ready=False),
            _reflect(
                ready=False,  # total crosses, but every candidate gap is a single instance
                count=5,
                sessions=2,
                by_category={
                    "authority-dependence": 1,
                    "avoidance": 1,
                    "loss-aversion": 1,
                    "no-experiment": 1,
                    "values-conflict": 1,
                },
            ),
        ),
    ),
    # Sora is past the grace period and has one terrible crunch day: three
    # same-category observations inside a single session cross the signal
    # total with no across-session recurrence. The recurrence gate holds
    # (issue #89, F7 fixed store-side via session linkage on each row) --
    # the store-side fix is the only possible one, since the distinguishing
    # evidence never reaches the status JSON the skill layer reads.
    Persona(
        name="sora-single-session-burst",
        coach_threshold=3,
        session_threshold=2,
        timeline=(
            _session(sessions=1),
            _session(sessions=2),
            _observe("avoidance", "crunch-dodge", count=1),
            _observe("avoidance", "crunch-dodge", count=2),
            _observe("avoidance", "crunch-dodge", count=3, ready=False),
            _reflect(ready=False, count=3, sessions=2, by_category={"avoidance": 3}),
        ),
    ),
    # Tomo ties two LINKED categories in equal measure: dodging his own call
    # (avoidance) by handing it to the agent (authority-dependence) is one
    # behaviour wearing two labels, so equal counts are the realistic shape.
    # No dominant exists (dominant=None keeps play()'s spec-lint out). Both tied
    # categories genuinely recur, so the store reports ready and the reflection
    # quizzes; the skill obeys that verdict (issue #137) rather than re-deriving
    # readiness. Rin's scatter differs only at the store: it returns
    # `ready: false`, which drives the hold -- the skill does not tell the two
    # apart itself. `tie-recurring-quiz.yaml` pins the quiz path.
    Persona(
        name="tomo-linked-tie",
        coach_threshold=4,
        session_threshold=2,
        timeline=(
            _session(sessions=1),
            _observe("avoidance", "call-dodged", count=1),
            _observe("authority-dependence", "agent-decides", count=2),
            _session(sessions=2),
            _observe("avoidance", "call-dodged", count=3),
            _observe("authority-dependence", "agent-decides", count=4, ready=True),
            _reflect(ready=True, count=4, sessions=2, by_category={"authority-dependence": 2, "avoidance": 2}),
        ),
    ),
    # Umi is the most common real shape: one genuine recurring pattern plus
    # scattered one-off noise in other categories. The singletons must not
    # displace or dilute the dominant category the quiz should aim at.
    Persona(
        name="umi-dominant-plus-noise",
        coach_threshold=5,
        session_threshold=0,
        dominant="no-experiment",
        timeline=(
            _observe("no-experiment", "debated-not-spiked", count=1),
            _observe("loss-aversion", "legacy-kept", count=2),
            _observe("no-experiment", "debated-not-spiked", count=3),
            _observe("other", count=4),
            _observe("no-experiment", "debated-not-spiked", count=5, ready=True),
            _reflect(
                ready=True,
                count=5,
                by_category={"loss-aversion": 1, "no-experiment": 3, "other": 1},
            ),
        ),
    ),
)


@needs_sqlite3
@pytest.mark.parametrize("persona", PERSONAS, ids=lambda p: p.name)
def test_persona_timeline(persona, tmp_path):
    """Each persona's prompt-turn timeline hits its expected readiness checkpoints."""
    play(persona, tmp_path / "store")


@needs_sqlite3
def test_rotation_count_shifts_dominant_category(tmp_path):
    """Count rotation ages the oldest signal out, so the dominant category follows
    the person's RECENT pattern, not their history."""
    persona = Persona(
        name="rotation-dominant-shift",
        coach_threshold=3,
        session_threshold=0,
        env_extra={"CLAIRVOYANCE_MAX_OBSERVATIONS": "3"},
        timeline=(
            _observe("avoidance", count=1),
            _observe("avoidance", count=2),
            _observe("avoidance", count=3, ready=True),
            _reflect(ready=True, by_category={"avoidance": 3}),
            _observe("no-experiment", count=3),
            _observe("no-experiment", count=3),
            _observe("no-experiment", count=3, ready=True),
            _reflect(ready=True, count=3, by_category={"no-experiment": 3}),
        ),
    )
    play(persona, tmp_path / "store")


@needs_sqlite3
def test_max_observations_below_threshold_never_ready(tmp_path):
    """Pins finding F2 (issue #89): a rotation bound below the coach threshold
    caps the count below readiness, so coaching is silently disabled forever."""
    data_dir = tmp_path / "store"
    env_extra = {"CLAIRVOYANCE_MAX_OBSERVATIONS": "3"}
    for _ in range(6):
        out = run_store(["record", "--category", "avoidance"], data_dir, 5, 0, env_extra)
        assert out["ready"] is False
    status = run_store(["status"], data_dir, 5, 0, env_extra)
    assert status["count"] == 3
    assert status["ready"] is False


@needs_sqlite3
def test_status_prunes_rows_past_age_bound_before_computing_readiness(tmp_path):
    """Fix for finding F1 (issue #89): status now applies the same rotation as
    record, so a reflection request never reports ready on rows already past
    the age bound. Was: test_status_counts_rows_past_age_bound_until_next_record,
    which pinned the opposite (unfixed) behaviour -- rewritten here now that
    hooks/adaptive-store.sh prunes on the status path too."""
    data_dir = tmp_path / "store"
    env_extra = {"CLAIRVOYANCE_MAX_AGE_DAYS": "30"}
    run_store(["record", "--category", "avoidance"], data_dir, 2, 0, env_extra)
    run_store(["record", "--category", "avoidance"], data_dir, 2, 0, env_extra)
    execute_write(data_dir / "coaching.db", "UPDATE observations SET ts = '2000-01-01T00:00:00+00:00'")
    status = run_store(["status"], data_dir, 2, 0, env_extra)
    assert status["count"] == 0
    assert status["ready"] is False


@needs_sqlite3
def test_outcome_rows_do_not_sustain_readiness_after_rotation(tmp_path):
    """Fix for the F4 corollary (issue #89, option B): quiz-answer rows are
    stored for feedback/calibration history but no longer count toward
    readiness, so after every raw observation ages past the rotation bound a
    person whose behaviour improved is not kept quiz-ready by their answers.
    Was: test_outcome_rows_alone_sustain_readiness_after_rotation, which
    pinned the opposite (pre-decision) behaviour."""
    data_dir = tmp_path / "store"
    env_extra = {"CLAIRVOYANCE_MAX_AGE_DAYS": "30"}
    for _ in range(3):
        run_store(["record", "--category", "avoidance"], data_dir, 3, 0, env_extra)
    assert run_store(["status"], data_dir, 3, 0, env_extra)["ready"] is True
    # Age every raw observation past the bound; the outcome rows recorded below
    # stay fresh and are still stored, but never count toward readiness.
    execute_write(
        data_dir / "coaching.db", "UPDATE observations SET ts = '2000-01-01T00:00:00+00:00' WHERE outcome IS NULL"
    )
    answer = ["record", "--category", "avoidance", "--outcome", "correct", "--confidence", "high"]
    for _ in range(3):
        out = run_store(answer, data_dir, 3, 0, env_extra)
        assert out["count"] == 0  # raw signal only; the stale raw rows are pruned
        assert out["ready"] is False
    rows = fetch_one(data_dir / "coaching.db", "SELECT COUNT(*), SUM(outcome IS NOT NULL) FROM observations")
    assert rows == (3, 3)  # the outcome trail is retained even while not ready


@needs_sqlite3
def test_readiness_rearms_after_improvement_and_relapse(tmp_path):
    """The full long-run lifecycle: coached pattern fades (improvement), the
    store correctly holds a mid-period reflection, then a relapse into a
    DIFFERENT pattern re-arms readiness with the new dominant category. This is
    the second-coaching-cycle path the skill exists for -- behaviour change
    relapses are the norm, not the exception."""
    data_dir = tmp_path / "store"
    env_extra = {"CLAIRVOYANCE_MAX_AGE_DAYS": "30"}
    for _ in range(3):
        run_store(["record", "--category", "avoidance"], data_dir, 3, 0, env_extra)
    assert run_store(["status"], data_dir, 3, 0, env_extra)["ready"] is True
    answer = ["record", "--category", "avoidance", "--outcome", "correct", "--confidence", "medium"]
    run_store(answer, data_dir, 3, 0, env_extra)
    # Months pass with no new signal: every row (raw and outcome) ages out.
    execute_write(data_dir / "coaching.db", "UPDATE observations SET ts = '2000-01-01T00:00:00+00:00'")
    # Relapse into a different pattern: the first record prunes the old cycle,
    # so the mid-relapse reflection correctly holds (improvement stuck).
    first = run_store(["record", "--category", "no-experiment"], data_dir, 3, 0, env_extra)
    assert first["count"] == 1
    assert first["ready"] is False
    run_store(["record", "--category", "no-experiment"], data_dir, 3, 0, env_extra)
    rearmed = run_store(["record", "--category", "no-experiment"], data_dir, 3, 0, env_extra)
    assert rearmed["count"] == 3
    assert rearmed["ready"] is True
    status = run_store(["status"], data_dir, 3, 0, env_extra)
    # The second cycle carries only the new pattern: no avoidance remnants.
    assert status["by_category"] == {"no-experiment": 3}


def test_missing_sqlite3_holds_not_fails(tmp_path):
    """With no sqlite3 CLI on PATH the store reports unavailable (hold), never an
    error: the reflection contract is "hold the quiz", exit 0."""
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    env = {**os.environ, "CLAIRVOYANCE_DATA_DIR": str(tmp_path / "store"), "PATH": str(empty_bin)}
    env.pop("BASH_ENV", None)
    for key in CLAIRVOYANCE_ENV_KEYS:
        env.pop(key, None)
    for args in (["status"], ["record", "--category", "avoidance"]):
        result = subprocess.run([BASH, STORE_SH.as_posix(), *args], capture_output=True, text=True, env=env, input="")
        assert result.returncode == 0, result.stderr
        out = json.loads(result.stdout)
        assert out["available"] is False
        assert out["ready"] is False
