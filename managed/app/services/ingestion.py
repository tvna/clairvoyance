"""Idempotent event ingestion.

Contract: (organization_id, event_id) is unique. A replay with the same
body hash is acknowledged as a duplicate (idempotent retry) and reports the
same facts as the original acknowledgement — whether the context summary was
stored and the current review due point. The same event_id with a different
body is a conflict — an event is never overwritten.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import CoachingEvent, Organization, QuizAttempt, ReviewSchedule
from app.schemas.collector import EventIn, PolicySettings
from app.services import scheduling
from app.services.identity import resolve_contributor


class EventConflictError(Exception):
    """Same event_id resubmitted with a different body."""


class CollectionDisabledError(Exception):
    """The organization policy has collection turned off."""


@dataclass
class IngestResult:
    event: CoachingEvent
    duplicate: bool
    context_summary_stored: bool
    schedule: ReviewSchedule | None


def _existing_event(db: Session, organization_id: uuid.UUID, event_id: str) -> CoachingEvent | None:
    return db.scalars(
        select(CoachingEvent).where(
            CoachingEvent.organization_id == organization_id,
            CoachingEvent.event_id == event_id,
        )
    ).first()


def _current_schedule(db: Session, event: CoachingEvent) -> ReviewSchedule | None:
    return db.scalars(
        select(ReviewSchedule).where(
            ReviewSchedule.organization_id == event.organization_id,
            ReviewSchedule.contributor_id == event.contributor_id,
            ReviewSchedule.category == event.category,
            ReviewSchedule.signal == (event.signal or ""),
        )
    ).first()


def ingest_event(db: Session, organization: Organization, payload: EventIn, policy: PolicySettings) -> IngestResult:
    if not policy.collect_enabled:
        raise CollectionDisabledError
    body_hash = payload.body_hash()

    existing = _existing_event(db, organization.id, payload.event_id)
    if existing is not None:
        return _replay(db, existing, body_hash)

    contributor = resolve_contributor(db, organization, payload.contributor)
    store_context = payload.context_summary is not None and policy.allow_context_summary
    source = payload.source
    event = CoachingEvent(
        organization_id=organization.id,
        contributor_id=contributor.id,
        schema_version=payload.schema_version,
        event_id=payload.event_id,
        event_type=payload.event_type,
        occurred_at=payload.occurred_at,
        category=payload.category,
        signal=payload.signal,
        session_kind=payload.session_kind,
        evidence_level=payload.evidence_level,
        source_repo=source.repo if source else None,
        runtime=source.runtime if source else None,
        client_version=source.client_version if source else None,
        context_summary=payload.context_summary if store_context else None,
        body_hash=body_hash,
    )
    try:
        # SAVEPOINT: losing the concurrent-insert race on (organization_id,
        # event_id) must not discard the contributor work above. The unique
        # constraint is the backstop the pre-check cannot provide.
        with db.begin_nested():
            db.add(event)
    except IntegrityError:
        raced = _existing_event(db, organization.id, payload.event_id)
        if raced is None:
            raise
        return _replay(db, raced, body_hash)

    schedule = None
    if payload.quiz is not None:
        db.add(
            QuizAttempt(
                event_pk=event.id,
                outcome=payload.quiz.outcome,
                confidence=payload.quiz.confidence,
                calibration=payload.quiz.calibration,
            )
        )
        schedule = scheduling.apply_outcome(
            db,
            organization_id=organization.id,
            contributor_id=contributor.id,
            category=payload.category,
            signal=payload.signal,
            outcome=payload.quiz.outcome,
            confidence=payload.quiz.confidence,
            occurred_at=payload.occurred_at,
        )
    return IngestResult(event=event, duplicate=False, context_summary_stored=store_context, schedule=schedule)


def _replay(db: Session, existing: CoachingEvent, body_hash: str) -> IngestResult:
    if existing.body_hash != body_hash:
        raise EventConflictError(existing.event_id)
    schedule = _current_schedule(db, existing) if existing.event_type == "quiz_attempt" else None
    return IngestResult(
        event=existing,
        duplicate=True,
        context_summary_stored=existing.context_summary is not None,
        schedule=schedule,
    )
