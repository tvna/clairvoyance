"""Aggregations for the admin API."""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import CoachingEvent, Contributor, QuizAttempt
from app.schemas.admin import ContributorOut, ContributorSummaryOut, QuizStats


def contributor_out(contributor: Contributor) -> ContributorOut:
    return ContributorOut(
        id=str(contributor.id),
        provider=contributor.provider,
        external_id=contributor.external_id,
        display_name=contributor.display_name,
        email=contributor.email,
        active=contributor.active,
        created_at=contributor.created_at,
    )


def contributor_summary(db: Session, contributor: Contributor) -> ContributorSummaryOut:
    by_category: dict[str, int] = dict(
        db.execute(
            select(CoachingEvent.category, func.count())
            .where(CoachingEvent.contributor_id == contributor.id)
            .group_by(CoachingEvent.category)
        ).all()  # type: ignore[arg-type]
    )
    events_total = sum(by_category.values())
    last_event_at: datetime | None = db.scalar(
        select(func.max(CoachingEvent.occurred_at)).where(CoachingEvent.contributor_id == contributor.id)
    )

    attempts = _quiz_rows(db, contributor.id)
    correct = sum(1 for outcome, _ in attempts if outcome == "correct")
    calibration: dict[str, int] = {}
    for _, cal in attempts:
        if cal is not None:
            calibration[cal] = calibration.get(cal, 0) + 1

    return ContributorSummaryOut(
        contributor=contributor_out(contributor),
        events_total=events_total,
        events_by_category=by_category,
        quiz=QuizStats(attempts=len(attempts), correct=correct, calibration=calibration),
        last_event_at=last_event_at,
    )


def _quiz_rows(db: Session, contributor_id: uuid.UUID) -> list[tuple[str, str | None]]:
    rows = db.execute(
        select(QuizAttempt.outcome, QuizAttempt.calibration)
        .join(CoachingEvent, CoachingEvent.id == QuizAttempt.event_pk)
        .where(CoachingEvent.contributor_id == contributor_id)
    ).all()
    return [(outcome, calibration) for outcome, calibration in rows]
