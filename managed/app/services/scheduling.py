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

from sqlalchemy import ColumnElement, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.db.models import ReviewSchedule, utcnow

_MISS_OVERCONFIDENT_DAYS = 1
_MISS_DAYS = 2
_CORRECT_DAYS = {"low": 3, "medium": 5, "high": 7}
_CORRECT_DEFAULT_DAYS = 5


def interval_days_for(outcome: str, confidence: str | None) -> int:
    if outcome != "correct":
        return _MISS_OVERCONFIDENT_DAYS if confidence == "high" else _MISS_DAYS
    return _CORRECT_DAYS.get(confidence or "", _CORRECT_DEFAULT_DAYS)


def _schedule_key(
    *,
    organization_id: uuid.UUID,
    contributor_id: uuid.UUID,
    category: str,
    signal: str,
) -> tuple[ColumnElement[bool], ...]:
    return (
        ReviewSchedule.organization_id == organization_id,
        ReviewSchedule.contributor_id == contributor_id,
        ReviewSchedule.category == category,
        ReviewSchedule.signal == signal,
    )


def _upsert_statement(
    db: Session,
    *,
    values: dict[str, object],
    occurred_at: datetime,
):
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        pg_statement = postgresql_insert(ReviewSchedule).values(**values)
        excluded = pg_statement.excluded
        return pg_statement.on_conflict_do_update(
            index_elements=["organization_id", "contributor_id", "category", "signal"],
            set_={
                "due_at": excluded.due_at,
                "interval_days": excluded.interval_days,
                "last_outcome": excluded.last_outcome,
                "last_attempted_at": excluded.last_attempted_at,
                "updated_at": excluded.updated_at,
            },
            where=ReviewSchedule.last_attempted_at <= occurred_at,
        )
    if dialect == "sqlite":
        sqlite_statement = sqlite_insert(ReviewSchedule).values(**values)
        excluded = sqlite_statement.excluded
        return sqlite_statement.on_conflict_do_update(
            index_elements=["organization_id", "contributor_id", "category", "signal"],
            set_={
                "due_at": excluded.due_at,
                "interval_days": excluded.interval_days,
                "last_outcome": excluded.last_outcome,
                "last_attempted_at": excluded.last_attempted_at,
                "updated_at": excluded.updated_at,
            },
            where=ReviewSchedule.last_attempted_at <= occurred_at,
        )
    raise RuntimeError(f"unsupported review schedule dialect: {dialect}")


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
    interval = interval_days_for(outcome, confidence)
    due_at = occurred_at + timedelta(days=interval)
    values = {
        "id": uuid.uuid4(),
        "organization_id": organization_id,
        "contributor_id": contributor_id,
        "category": category,
        "signal": normalized_signal,
        "due_at": due_at,
        "interval_days": interval,
        "last_outcome": outcome,
        "last_attempted_at": occurred_at,
        "updated_at": utcnow(),
    }

    db.execute(_upsert_statement(db, values=values, occurred_at=occurred_at))
    db.flush()
    db.expire_all()
    return db.scalars(
        select(ReviewSchedule)
        .where(
            *_schedule_key(
                organization_id=organization_id,
                contributor_id=contributor_id,
                category=category,
                signal=normalized_signal,
            )
        )
        .execution_options(populate_existing=True)
    ).one()
