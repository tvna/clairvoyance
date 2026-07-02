"""Data model for managed mode.

Value vocabularies (category, outcome, confidence, calibration, evidence
level) match the local adaptive store contract
(skills/adaptive-coaching/references/store.md) so local-to-managed migration
does not re-encode history. They are enforced at the API boundary (Pydantic)
and stored as plain strings, so adding a value is a code change, not a
migration.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Dialect,
    ForeignKey,
    Integer,
    String,
    Text,
    TypeDecorator,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator[datetime]):
    """timestamptz that always loads timezone-aware.

    All stored timestamps are UTC. PostgreSQL round-trips tzinfo natively;
    SQLite (tests, local smoke) drops it, which would make loaded values
    incomparable with the aware datetimes the API validates in.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)


class CollectorToken(Base):
    """Organization-scoped write credential for the collector API.

    Only the HMAC-SHA256(pepper, token) digest is stored; the raw token is
    shown once at mint time and never persisted.
    """

    __tablename__ = "collector_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String(255))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)

    organization: Mapped[Organization] = relationship()


class Contributor(Base):
    __tablename__ = "contributors"
    __table_args__ = (UniqueConstraint("organization_id", "provider", "external_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    provider: Mapped[str] = mapped_column(String(64))
    external_id: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)


class CoachingEvent(Base):
    """Coded event sent by a local client or skill runtime.

    ``event_id`` is client-generated and unique within the organization;
    ``body_hash`` disambiguates replays (same hash: idempotent duplicate;
    different hash: conflict, never an overwrite).
    """

    __tablename__ = "coaching_events"
    __table_args__ = (UniqueConstraint("organization_id", "event_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    contributor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contributors.id"))
    schema_version: Mapped[int] = mapped_column(Integer)
    event_id: Mapped[str] = mapped_column(String(64))
    event_type: Mapped[str] = mapped_column(String(32))
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime())
    category: Mapped[str] = mapped_column(String(64))
    signal: Mapped[str | None] = mapped_column(String(64), nullable=True)
    session_kind: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_level: Mapped[str] = mapped_column(String(16))
    source_repo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    runtime: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    context_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)


class QuizAttempt(Base):
    """Outcome and calibration for a quiz_attempt event (one per event)."""

    __tablename__ = "quiz_attempts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    event_pk: Mapped[uuid.UUID] = mapped_column(ForeignKey("coaching_events.id", ondelete="CASCADE"), unique=True)
    outcome: Mapped[str] = mapped_column(String(16))
    confidence: Mapped[str | None] = mapped_column(String(16), nullable=True)
    calibration: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)


class ReviewSchedule(Base):
    """Spaced-review due point per (contributor, category, signal).

    ``signal`` uses '' (never NULL) for "no signal" so the unique constraint
    holds — SQL treats NULLs as distinct in unique indexes.
    """

    __tablename__ = "review_schedules"
    __table_args__ = (UniqueConstraint("organization_id", "contributor_id", "category", "signal"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    contributor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contributors.id"))
    category: Mapped[str] = mapped_column(String(64))
    signal: Mapped[str] = mapped_column(String(64), default="")
    due_at: Mapped[datetime] = mapped_column(UTCDateTime())
    interval_days: Mapped[int] = mapped_column(Integer)
    last_outcome: Mapped[str | None] = mapped_column(String(16), nullable=True)
    last_attempted_at: Mapped[datetime] = mapped_column(UTCDateTime())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow)


class AdminPolicy(Base):
    __tablename__ = "admin_policies"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), primary_key=True)
    settings: Mapped[dict[str, object]] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    actor: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(64))
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
