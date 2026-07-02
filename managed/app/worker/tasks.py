"""Background jobs.

Retention is the first real policy enforcement point: events older than the
organization's ``retention_days`` are deleted (quiz attempts follow via FK
cascade). Runs daily from beat; safe to run repeatedly.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import CursorResult, delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import CoachingEvent, Organization
from app.db.session import build_engine, build_session_factory
from app.services import policies
from app.worker.celery_app import celery_app


def enforce_retention_once(db: Session, now: datetime | None = None) -> dict[str, int]:
    """Delete out-of-retention events per organization; returns counts by org key."""
    now = now or datetime.now(UTC)
    deleted: dict[str, int] = {}
    for organization in db.scalars(select(Organization)).all():
        retention_days = policies.get_policy(db, organization.id).retention_days
        cutoff = now - timedelta(days=retention_days)
        result: CursorResult[object] = db.execute(  # type: ignore[assignment]
            delete(CoachingEvent).where(
                CoachingEvent.organization_id == organization.id,
                CoachingEvent.created_at < cutoff,
            )
        )
        deleted[organization.key] = result.rowcount
    db.flush()
    return deleted


@celery_app.task(name="app.worker.tasks.enforce_retention")
def enforce_retention() -> dict[str, int]:
    engine = build_engine(get_settings())
    session_factory = build_session_factory(engine)
    with session_factory() as db:
        deleted = enforce_retention_once(db)
        db.commit()
    engine.dispose()
    return deleted
