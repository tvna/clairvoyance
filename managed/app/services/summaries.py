"""Aggregations for the admin API (SQL-side, O(distinct values) per request)."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import CoachingEvent, Contributor, QuizAttempt
from app.schemas.admin import ContributorOut, ContributorSummaryOut, QuizStats


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

    quiz_rows = db.execute(
        select(QuizAttempt.outcome, QuizAttempt.calibration, func.count())
        .join(CoachingEvent, CoachingEvent.id == QuizAttempt.event_pk)
        .where(CoachingEvent.contributor_id == contributor.id)
        .group_by(QuizAttempt.outcome, QuizAttempt.calibration)
    ).all()
    attempts = sum(count for _, _, count in quiz_rows)
    correct = sum(count for outcome, _, count in quiz_rows if outcome == "correct")
    calibration: dict[str, int] = {}
    for _, cal, count in quiz_rows:
        if cal is not None:
            calibration[cal] = calibration.get(cal, 0) + count

    return ContributorSummaryOut(
        contributor=ContributorOut.model_validate(contributor),
        events_total=events_total,
        events_by_category=by_category,
        quiz=QuizStats(attempts=attempts, correct=correct, calibration=calibration),
        last_event_at=last_event_at,
    )
