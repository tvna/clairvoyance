"""Spacing contract (quiz.md) and schedule row lifecycle."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from app.db.models import Contributor, Organization
from app.services import scheduling


@pytest.mark.parametrize(
    ("outcome", "confidence", "expected"),
    [
        ("incorrect", "high", 1),  # overconfident miss
        ("incorrect", "medium", 2),
        ("incorrect", "low", 2),
        ("incorrect", None, 2),
        ("correct", "low", 3),
        ("correct", "medium", 5),
        ("correct", None, 5),  # unstated confidence treated as medium
        ("correct", "high", 7),
    ],
)
def test_interval_days_for_matches_quiz_contract(outcome: str, confidence: str | None, expected: int) -> None:
    assert scheduling.interval_days_for(outcome, confidence) == expected


def _seed(db: Session) -> tuple[Organization, Contributor]:
    organization = Organization(key="acme", name="Acme")
    db.add(organization)
    db.flush()
    contributor = Contributor(organization_id=organization.id, provider="github", external_id="1")
    db.add(contributor)
    db.flush()
    return organization, contributor


def _upsert_values(organization: Organization, contributor: Contributor) -> dict[str, object]:
    occurred = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)
    return {
        "id": uuid4(),
        "organization_id": organization.id,
        "contributor_id": contributor.id,
        "category": "avoidance",
        "signal": "deferred-risk-call",
        "due_at": occurred + timedelta(days=5),
        "interval_days": 5,
        "last_outcome": "correct",
        "last_attempted_at": occurred,
        "updated_at": occurred,
    }


def test_postgresql_upsert_statement_is_conditional(db: Session) -> None:
    organization, contributor = _seed(db)
    fake_db = cast(
        Session,
        SimpleNamespace(get_bind=lambda: SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))),
    )
    statement = scheduling._upsert_statement(
        fake_db,
        values=_upsert_values(organization, contributor),
        occurred_at=datetime(2026, 7, 2, 10, 0, tzinfo=UTC),
    )
    compiled = str(statement.compile(dialect=postgresql.dialect()))

    assert "ON CONFLICT" in compiled
    assert "last_attempted_at" in compiled


def test_schedule_upsert_rejects_unsupported_dialect(db: Session) -> None:
    organization, contributor = _seed(db)
    fake_db = cast(
        Session,
        SimpleNamespace(get_bind=lambda: SimpleNamespace(dialect=SimpleNamespace(name="mysql"))),
    )
    with pytest.raises(RuntimeError, match="unsupported review schedule dialect"):
        scheduling._upsert_statement(
            fake_db,
            values=_upsert_values(organization, contributor),
            occurred_at=datetime(2026, 7, 2, 10, 0, tzinfo=UTC),
        )


def test_apply_outcome_creates_then_updates(db: Session) -> None:
    organization, contributor = _seed(db)
    occurred = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)

    schedule = scheduling.apply_outcome(
        db,
        organization_id=organization.id,
        contributor_id=contributor.id,
        category="avoidance",
        signal=None,
        outcome="correct",
        confidence="high",
        occurred_at=occurred,
    )
    assert schedule.signal == ""
    assert schedule.interval_days == 7
    assert schedule.due_at == occurred + timedelta(days=7)
    assert schedule.last_attempted_at == occurred

    updated = scheduling.apply_outcome(
        db,
        organization_id=organization.id,
        contributor_id=contributor.id,
        category="avoidance",
        signal=None,
        outcome="incorrect",
        confidence="high",
        occurred_at=occurred + timedelta(days=7),
    )
    assert updated.id == schedule.id
    assert updated.interval_days == 1
    assert updated.last_outcome == "incorrect"
    assert updated.last_attempted_at == occurred + timedelta(days=7)


def test_stale_attempt_does_not_overwrite_newer_schedule(db: Session) -> None:
    organization, contributor = _seed(db)
    newer = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)

    current = scheduling.apply_outcome(
        db,
        organization_id=organization.id,
        contributor_id=contributor.id,
        category="avoidance",
        signal="deferred-risk-call",
        outcome="correct",
        confidence="medium",
        occurred_at=newer,
    )
    stale = scheduling.apply_outcome(
        db,
        organization_id=organization.id,
        contributor_id=contributor.id,
        category="avoidance",
        signal="deferred-risk-call",
        outcome="incorrect",
        confidence=None,
        occurred_at=newer - timedelta(days=30),  # late-arriving historical attempt
    )
    assert stale.id == current.id
    assert stale.last_outcome == "correct"  # unchanged
    assert stale.due_at == newer + timedelta(days=5)
    assert stale.last_attempted_at == newer


def _dismiss(schedule: object, db: Session) -> None:
    schedule.status = "dismissed"  # type: ignore[attr-defined]
    schedule.dismissed_at = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)  # type: ignore[attr-defined]
    schedule.dismissed_by = "coach@example.com"  # type: ignore[attr-defined]
    db.flush()


def test_newer_attempt_reopens_a_dismissed_schedule(db: Session) -> None:
    organization, contributor = _seed(db)
    occurred = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)
    schedule = scheduling.apply_outcome(
        db,
        organization_id=organization.id,
        contributor_id=contributor.id,
        category="avoidance",
        signal="deferred-risk-call",
        outcome="correct",
        confidence="medium",
        occurred_at=occurred,
    )
    _dismiss(schedule, db)

    reopened = scheduling.apply_outcome(
        db,
        organization_id=organization.id,
        contributor_id=contributor.id,
        category="avoidance",
        signal="deferred-risk-call",
        outcome="incorrect",
        confidence=None,
        occurred_at=occurred + timedelta(days=1),  # newer than the dismissal's attempt
    )
    assert reopened.id == schedule.id
    assert reopened.status == "active"  # back in the work queue
    assert reopened.dismissed_at is None  # dismissal metadata cleared
    assert reopened.dismissed_by is None


def test_stale_attempt_does_not_reopen_a_dismissed_schedule(db: Session) -> None:
    organization, contributor = _seed(db)
    occurred = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)
    schedule = scheduling.apply_outcome(
        db,
        organization_id=organization.id,
        contributor_id=contributor.id,
        category="avoidance",
        signal="deferred-risk-call",
        outcome="correct",
        confidence="medium",
        occurred_at=occurred,
    )
    _dismiss(schedule, db)

    stale = scheduling.apply_outcome(
        db,
        organization_id=organization.id,
        contributor_id=contributor.id,
        category="avoidance",
        signal="deferred-risk-call",
        outcome="incorrect",
        confidence=None,
        occurred_at=occurred - timedelta(days=30),  # older than the last applied attempt
    )
    # The out-of-order guard wins: a late-arriving attempt must not resurrect a
    # deliberately dismissed row.
    assert stale.id == schedule.id
    assert stale.status == "dismissed"
    assert stale.dismissed_by == "coach@example.com"


def test_equal_timestamp_attempt_does_not_reopen_a_dismissed_schedule(db: Session) -> None:
    organization, contributor = _seed(db)
    occurred = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)
    schedule = scheduling.apply_outcome(
        db,
        organization_id=organization.id,
        contributor_id=contributor.id,
        category="avoidance",
        signal="deferred-risk-call",
        outcome="correct",
        confidence="medium",
        occurred_at=occurred,
    )
    _dismiss(schedule, db)

    # A distinct attempt sharing the exact occurred_at (e.g. coarse historical
    # imports) is not strictly newer, so it must not reopen the dismissal --
    # while its field refresh still applies (the WHERE guard is inclusive).
    equal = scheduling.apply_outcome(
        db,
        organization_id=organization.id,
        contributor_id=contributor.id,
        category="avoidance",
        signal="deferred-risk-call",
        outcome="incorrect",
        confidence="high",
        occurred_at=occurred,
    )
    assert equal.id == schedule.id
    assert equal.status == "dismissed"  # operator intent preserved
    assert equal.dismissed_by == "coach@example.com"
    assert equal.last_outcome == "incorrect"  # field refresh still happened
