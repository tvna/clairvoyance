"""Background jobs.

Retention is the first real policy enforcement point: events whose
``occurred_at`` is older than the organization's ``retention_days`` are
deleted (quiz attempts follow via FK cascade). The cutoff is on when the
event happened, not when the server received it, so imported history does
not outlive the policy by a fresh ingestion window. Runs daily from beat;
safe to run repeatedly. ``CLAIRVOYANCE_RETENTION_DRY_RUN=true`` reports what
would be deleted without deleting — the verification pass for a new policy.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import CursorResult, delete, func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import CoachingEvent, Organization
from app.db.session import build_engine, build_session_factory
from app.services import policies
from app.worker.celery_app import celery_app


def enforce_retention_once(db: Session, now: datetime | None = None, dry_run: bool = False) -> dict[str, int]:
    """Delete (or, on dry_run, count) out-of-retention events per organization."""
    now = now or datetime.now(UTC)
    affected: dict[str, int] = {}
    for organization in db.scalars(select(Organization)).all():
        retention_days = policies.get_policy(db, organization.id).retention_days
        cutoff = now - timedelta(days=retention_days)
        out_of_retention = (
            CoachingEvent.organization_id == organization.id,
            CoachingEvent.occurred_at < cutoff,
        )
        if dry_run:
            count = db.scalar(select(func.count()).select_from(CoachingEvent).where(*out_of_retention))
            affected[organization.key] = count or 0
        else:
            result: CursorResult[object] = db.execute(  # type: ignore[assignment]
                delete(CoachingEvent).where(*out_of_retention)
            )
            affected[organization.key] = result.rowcount
    return affected


@celery_app.task(name="app.worker.tasks.enforce_retention")
def enforce_retention() -> dict[str, int]:
    settings = get_settings()
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)
    with session_factory() as db:
        affected = enforce_retention_once(db, dry_run=settings.retention_dry_run)
        db.commit()
    engine.dispose()
    return affected
