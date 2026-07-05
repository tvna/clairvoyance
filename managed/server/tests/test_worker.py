"""Retention enforcement: per-org cutoff, FK cascade, celery entry point."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from conftest import make_settings
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.worker.tasks as tasks_module
from app.db.base import Base
from app.db.models import CoachingEvent, Contributor, Organization, QuizAttempt
from app.db.session import build_engine, build_session_factory
from app.schemas.collector import PolicySettings
from app.services import policies
from app.worker.tasks import enforce_retention, enforce_retention_once

NOW = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def seed_org_with_events(db: Session, key: str, retention_days: int | None = None) -> Organization:
    organization = Organization(key=key, name=key.title())
    db.add(organization)
    db.flush()
    if retention_days is not None:
        policies.put_policy(db, organization.id, PolicySettings(retention_days=retention_days))
    contributor = Contributor(organization_id=organization.id, provider="github", external_id=f"{key}-1")
    db.add(contributor)
    db.flush()
    for name, created_at in (("old", NOW - timedelta(days=40)), ("new", NOW - timedelta(days=1))):
        event = CoachingEvent(
            organization_id=organization.id,
            contributor_id=contributor.id,
            schema_version=1,
            event_id=f"{key}-{name}",
            event_type="quiz_attempt",
            occurred_at=created_at,
            category="avoidance",
            signal=None,
            session_kind=None,
            evidence_level="observed",
            body_hash="x" * 64,
            created_at=created_at,
        )
        db.add(event)
        db.flush()
        db.add(QuizAttempt(event_pk=event.id, outcome="correct"))
    db.flush()
    return organization


def test_enforce_retention_dry_run_counts_without_deleting(db: Session) -> None:
    seed_org_with_events(db, "strict", retention_days=30)
    affected = enforce_retention_once(db, now=NOW, dry_run=True)
    assert affected == {"strict": 1}
    assert len(db.scalars(select(CoachingEvent)).all()) == 2  # nothing deleted


def test_enforce_retention_once_respects_per_org_policy(db: Session) -> None:
    seed_org_with_events(db, "strict", retention_days=30)
    seed_org_with_events(db, "lax")  # default 365 keeps everything
    deleted = enforce_retention_once(db, now=NOW)
    assert deleted == {"strict": 1, "lax": 0}

    remaining = db.scalars(select(CoachingEvent.event_id)).all()
    assert sorted(remaining) == ["lax-new", "lax-old", "strict-new"]
    # The quiz attempt of the deleted event followed via ON DELETE CASCADE.
    assert len(db.scalars(select(QuizAttempt)).all()) == 3


def test_enforce_retention_task_runs_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = make_settings(database_url=f"sqlite:///{tmp_path}/retention.db")
    engine = build_engine(settings)
    Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as db:
        seed_org_with_events(db, "acme", retention_days=30)
        db.commit()
    engine.dispose()

    monkeypatch.setattr(tasks_module, "get_settings", lambda: settings)
    deleted = enforce_retention()
    assert deleted == {"acme": 1}
