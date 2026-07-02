"""Spaced-review scheduling.

Lightweight expanding schedule matching the skill-side loop: a correct answer
doubles the interval (capped), an incorrect one resets it, and the next due
point is measured from when the attempt actually happened.
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ReviewSchedule

INITIAL_INTERVAL_DAYS = 1
MAX_INTERVAL_DAYS = 60


def next_interval_days(current: int | None, outcome: str) -> int:
    if outcome != "correct":
        return INITIAL_INTERVAL_DAYS
    if current is None:
        return INITIAL_INTERVAL_DAYS * 2
    return min(current * 2, MAX_INTERVAL_DAYS)


def apply_outcome(
    db: Session,
    *,
    organization_id: uuid.UUID,
    contributor_id: uuid.UUID,
    category: str,
    signal: str | None,
    outcome: str,
    occurred_at: datetime,
) -> ReviewSchedule:
    normalized_signal = signal or ""
    schedule = db.scalars(
        select(ReviewSchedule).where(
            ReviewSchedule.organization_id == organization_id,
            ReviewSchedule.contributor_id == contributor_id,
            ReviewSchedule.category == category,
            ReviewSchedule.signal == normalized_signal,
        )
    ).first()
    interval = next_interval_days(schedule.interval_days if schedule else None, outcome)
    due_at = occurred_at + timedelta(days=interval)
    if schedule is None:
        schedule = ReviewSchedule(
            organization_id=organization_id,
            contributor_id=contributor_id,
            category=category,
            signal=normalized_signal,
            due_at=due_at,
            interval_days=interval,
            last_outcome=outcome,
        )
        db.add(schedule)
    else:
        schedule.due_at = due_at
        schedule.interval_days = interval
        schedule.last_outcome = outcome
    db.flush()
    return schedule
