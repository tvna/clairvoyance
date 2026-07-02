"""Spacing math and schedule row lifecycle."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.db.models import Contributor, Organization
from app.services import scheduling


@pytest.mark.parametrize(
    ("current", "outcome", "expected"),
    [
        (None, "incorrect", 1),
        (8, "incorrect", 1),
        (None, "correct", 2),
        (2, "correct", 4),
        (40, "correct", 60),  # capped
        (60, "correct", 60),
    ],
)
def test_next_interval_days(current: int | None, outcome: str, expected: int) -> None:
    assert scheduling.next_interval_days(current, outcome) == expected


def test_apply_outcome_creates_then_updates(db: Session) -> None:
    organization = Organization(key="acme", name="Acme")
    db.add(organization)
    db.flush()
    contributor = Contributor(organization_id=organization.id, provider="github", external_id="1")
    db.add(contributor)
    db.flush()
    occurred = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)

    schedule = scheduling.apply_outcome(
        db,
        organization_id=organization.id,
        contributor_id=contributor.id,
        category="avoidance",
        signal=None,
        outcome="correct",
        occurred_at=occurred,
    )
    assert schedule.signal == ""
    assert schedule.interval_days == 2
    assert schedule.due_at == occurred + timedelta(days=2)

    updated = scheduling.apply_outcome(
        db,
        organization_id=organization.id,
        contributor_id=contributor.id,
        category="avoidance",
        signal=None,
        outcome="incorrect",
        occurred_at=occurred + timedelta(days=2),
    )
    assert updated.id == schedule.id
    assert updated.interval_days == 1
    assert updated.last_outcome == "incorrect"
