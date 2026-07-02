"""Spaced-review scheduling.

Intervals follow the skill-side contract
(skills/adaptive-coaching/references/quiz.md, "Spaced follow-up"), so managed
mode schedules the same review points the local loop names:

- overconfident miss (incorrect + high confidence): 1 day
- any other miss: 2 days
- correct but low confidence: 3 days
- correct with medium (or unstated) confidence: 5 days
- correct with high confidence: 7 days

The due point is measured from when the attempt occurred. Out-of-order
arrivals (retry queues, historical imports) must not let an older attempt
overwrite the schedule a newer one produced, so an attempt older than the
last applied one is ignored.
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ReviewSchedule

_MISS_OVERCONFIDENT_DAYS = 1
_MISS_DAYS = 2
_CORRECT_DAYS = {"low": 3, "medium": 5, "high": 7}
_CORRECT_DEFAULT_DAYS = 5


def interval_days_for(outcome: str, confidence: str | None) -> int:
    if outcome != "correct":
        return _MISS_OVERCONFIDENT_DAYS if confidence == "high" else _MISS_DAYS
    return _CORRECT_DAYS.get(confidence or "", _CORRECT_DEFAULT_DAYS)


def _last_applied_at(schedule: ReviewSchedule) -> datetime:
    # Derived, not stored: due_at was computed as occurred_at + interval.
    return schedule.due_at - timedelta(days=schedule.interval_days)


def apply_outcome(
    db: Session,
    *,
    organization_id: uuid.UUID,
    contributor_id: uuid.UUID,
    category: str,
    signal: str | None,
    outcome: str,
    confidence: str | None,
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
    if schedule is not None and occurred_at < _last_applied_at(schedule):
        return schedule  # stale attempt: a newer one already set the schedule

    interval = interval_days_for(outcome, confidence)
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
