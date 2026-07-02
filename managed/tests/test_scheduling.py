"""Spacing contract (quiz.md) and schedule row lifecycle."""

from datetime import UTC, datetime, timedelta

import pytest
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
