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
import shutil
import sqlite3
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE_SH = REPO_ROOT / "hooks" / "adaptive-store.sh"


def _resolve_bash():
    """A POSIX bash for running the bundled .sh (same logic as test_adaptive_store)."""
    if os.name == "nt":
        for candidate in (
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe",
        ):
            if pathlib.Path(candidate).exists():
                return candidate
    return shutil.which("bash") or "bash"


BASH = _resolve_bash()

HAS_SQLITE3 = shutil.which("sqlite3") is not None
needs_sqlite3 = pytest.mark.skipif(not HAS_SQLITE3, reason="sqlite3 CLI not installed")


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
    available: bool | None = None
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
    available: bool = True,
) -> Step:
    return Step(
        kind="reflect", ready=ready, count=count, sessions=sessions, by_category=by_category, available=available
    )


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


def run_store(
    args: list[str],
    data_dir: pathlib.Path,
    coach_threshold: int,
    session_threshold: int,
    env_extra: dict[str, str] | None = None,
) -> dict[str, object]:
    """Invoke the store CLI with an isolated data dir and parse its JSON reply."""
    env = {**os.environ, "CLAIRVOYANCE_DATA_DIR": str(data_dir)}
    for key in (
        "LOCALAPPDATA",
        "XDG_DATA_HOME",
        "CLAIRVOYANCE_COACH_THRESHOLD",
        "CLAIRVOYANCE_SESSION_THRESHOLD",
        "CLAIRVOYANCE_STORE_CONTEXT",
        "CLAIRVOYANCE_MAX_OBSERVATIONS",
        "CLAIRVOYANCE_MAX_AGE_DAYS",
    ):
        env.pop(key, None)
    env["CLAIRVOYANCE_COACH_THRESHOLD"] = str(coach_threshold)
    env["CLAIRVOYANCE_SESSION_THRESHOLD"] = str(session_threshold)
    if env_extra:
        env.update(env_extra)
    result = subprocess.run([BASH, STORE_SH.as_posix(), *args], capture_output=True, text=True, env=env, input="")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


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
        for field in ("ready", "count", "sessions", "available", "by_category"):
            expected = getattr(step, field)
            if expected is not None:
                actual = out.get(field)
                assert actual == expected, (
                    f"{persona.name} turn {turn} ({step.kind}): {field}={actual!r}, expected {expected!r}"
                )
        if step.kind == "reflect" and step.ready and persona.dominant is not None and step.by_category:
            top = max(step.by_category.items(), key=lambda kv: kv[1])
            assert top[0] == persona.dominant, f"{persona.name}: timeline spec dominant mismatch"


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
            _answer("avoidance", "incorrect", "high", "overconfident", 1, count=4),
        ),
    ),
    # Ben reframes an owner judgement as a tooling problem twice in his very
    # first session: the signal gate is met early, so the grace gate alone must
    # hold his day-one reflection request.
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
            _reflect(ready=True, count=2, sessions=4, by_category={"mislabeled-technical": 2}),
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
            _answer("loss-aversion", "correct", "medium", "accurate", 5, count=4),
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
            _answer("authority-dependence", "correct", "medium", "accurate", 5, count=6),
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
    # -- one clean category at a time. These pin what the store-level gate can
    # -- and cannot see when threshold crossings combine (findings F6/F7, #89).
    #
    # Rin had a rough month: five DIFFERENT single instances, one per category.
    # The total crosses the signal gate, so the store reports ready -- the gate
    # is category-blind (F6) and cannot see that every candidate gap is a
    # single instance. The contract-faithful hold ("never quiz on a single
    # instance", SKILL.md) must come from the skill layer reading by_category:
    # evals/adaptive-coaching/tasks/scattered-signal-hold.yaml is that check.
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
            _observe("no-experiment", "no-spike", count=5, ready=True),
            _reflect(
                ready=True,  # current behaviour: total count crosses, composition invisible
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
    # same-category observations inside a single session cross the signal gate
    # with no across-session recurrence (F7). Unlike F6, the skill layer cannot
    # detect this from status JSON at all -- rows carry no session linkage --
    # so no L2 eval task exists; only a store-side change could surface it.
    Persona(
        name="sora-single-session-burst",
        coach_threshold=3,
        session_threshold=2,
        dominant="avoidance",
        timeline=(
            _session(sessions=1),
            _session(sessions=2),
            _observe("avoidance", "crunch-dodge", count=1),
            _observe("avoidance", "crunch-dodge", count=2),
            _observe("avoidance", "crunch-dodge", count=3, ready=True),
            _reflect(ready=True, count=3, sessions=2, by_category={"avoidance": 3}),
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
def test_status_counts_rows_past_age_bound_until_next_record(tmp_path):
    """Pins finding F1 (issue #89): rotation pruning runs only on record, so a
    reflection request (status) can report ready on rows already past the age
    bound; the next record prunes them and readiness drops back."""
    data_dir = tmp_path / "store"
    env_extra = {"CLAIRVOYANCE_MAX_AGE_DAYS": "30"}
    run_store(["record", "--category", "avoidance"], data_dir, 2, 0, env_extra)
    run_store(["record", "--category", "avoidance"], data_dir, 2, 0, env_extra)
    conn = sqlite3.connect(str(data_dir / "coaching.db"))
    conn.execute("UPDATE observations SET ts = '2000-01-01T00:00:00+00:00'")
    conn.commit()
    conn.close()
    stale = run_store(["status"], data_dir, 2, 0, env_extra)
    assert stale["count"] == 2
    assert stale["ready"] is True  # current behaviour: expired rows still count
    pruned = run_store(["record", "--category", "no-experiment"], data_dir, 2, 0, env_extra)
    assert pruned["count"] == 1
    assert pruned["ready"] is False


@needs_sqlite3
def test_outcome_rows_alone_sustain_readiness_after_rotation(tmp_path):
    """Pins the F4 corollary (issue #89) in its compound form: after every raw
    observation ages past the rotation bound, the quiz-answer rows recorded in
    the same category re-cross the threshold on their own. A person whose
    behaviour improved (no new raw signal for months) stays quiz-ready purely
    because they answered quizzes."""
    data_dir = tmp_path / "store"
    env_extra = {"CLAIRVOYANCE_MAX_AGE_DAYS": "30"}
    for _ in range(3):
        run_store(["record", "--category", "avoidance"], data_dir, 3, 0, env_extra)
    assert run_store(["status"], data_dir, 3, 0, env_extra)["ready"] is True
    # Age every raw observation past the bound; the outcome rows recorded below
    # stay fresh, so each answer prunes the stale rows and adds itself.
    conn = sqlite3.connect(str(data_dir / "coaching.db"))
    conn.execute("UPDATE observations SET ts = '2000-01-01T00:00:00+00:00' WHERE outcome IS NULL")
    conn.commit()
    conn.close()
    answer = ["record", "--category", "avoidance", "--outcome", "correct", "--confidence", "high"]
    assert run_store(answer, data_dir, 3, 0, env_extra)["ready"] is False  # stale rows pruned
    assert run_store(answer, data_dir, 3, 0, env_extra)["ready"] is False
    third = run_store(answer, data_dir, 3, 0, env_extra)
    assert third["count"] == 3
    assert third["ready"] is True  # current behaviour: readiness rebuilt from answers alone
    rows = (
        sqlite3.connect(str(data_dir / "coaching.db"))
        .execute("SELECT COUNT(*), SUM(outcome IS NOT NULL) FROM observations")
        .fetchone()
    )
    assert rows == (3, 3)  # every remaining row is a quiz outcome, zero raw signal


def test_missing_sqlite3_holds_not_fails(tmp_path):
    """With no sqlite3 CLI on PATH the store reports unavailable (hold), never an
    error: the reflection contract is "hold the quiz", exit 0."""
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    env = {**os.environ, "CLAIRVOYANCE_DATA_DIR": str(tmp_path / "store"), "PATH": str(empty_bin)}
    env.pop("BASH_ENV", None)
    for args in (["status"], ["record", "--category", "avoidance"]):
        result = subprocess.run([BASH, STORE_SH.as_posix(), *args], capture_output=True, text=True, env=env, input="")
        assert result.returncode == 0, result.stderr
        out = json.loads(result.stdout)
        assert out["available"] is False
        assert out["ready"] is False
