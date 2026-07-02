"""Collector API contract.

One ingestion path: every observation, session marker, or quiz attempt is a
``POST /v1/events`` envelope discriminated by ``event_type``, so there is a
single idempotency mechanism and a single schema version to evolve.
"""

import hashlib
import json
from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Vocabulary shared with the local adaptive store (store.md). Anything outside
# CATEGORIES is folded to "other" by local clients; the server rejects instead
# of folding so bad clients surface early.
CATEGORIES = (
    "avoidance",
    "mislabeled-technical",
    "loss-aversion",
    "values-conflict",
    "no-experiment",
    "authority-dependence",
    "other",
)

Category = Literal[
    "avoidance",
    "mislabeled-technical",
    "loss-aversion",
    "values-conflict",
    "no-experiment",
    "authority-dependence",
    "other",
]
Outcome = Literal["correct", "incorrect"]
Confidence = Literal["low", "medium", "high"]
Calibration = Literal["accurate", "overconfident", "underconfident", "unknown"]
EvidenceLevel = Literal["observed", "imported", "inferred", "missing"]
EventType = Literal["observation", "session", "quiz_attempt"]

SIGNAL_PATTERN = r"^[a-z0-9-]{1,64}$"


class ContributorIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1, max_length=64)
    external_id: str = Field(min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=320)


class SourceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repo: str | None = Field(default=None, max_length=255)
    runtime: str | None = Field(default=None, max_length=64)
    client_version: str | None = Field(default=None, max_length=64)


class QuizAttemptIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: Outcome
    confidence: Confidence | None = None
    calibration: Calibration | None = None


class EventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    event_type: EventType
    event_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    occurred_at: datetime
    # The collector token is authoritative for the organization; when the body
    # carries a key too, a mismatch is rejected rather than silently rerouted.
    organization_key: str | None = Field(default=None, max_length=64)
    contributor: ContributorIn
    source: SourceIn | None = None
    category: Category
    signal: str | None = Field(default=None, pattern=SIGNAL_PATTERN)
    session_kind: str | None = Field(default=None, max_length=64)
    evidence_level: EvidenceLevel = "observed"
    context_summary: str | None = Field(default=None, max_length=4000)
    quiz: QuizAttemptIn | None = None

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        return value

    @model_validator(mode="after")
    def quiz_matches_type(self) -> Self:
        if self.event_type == "quiz_attempt" and self.quiz is None:
            raise ValueError("quiz payload is required when event_type is quiz_attempt")
        if self.event_type != "quiz_attempt" and self.quiz is not None:
            raise ValueError("quiz payload is only allowed when event_type is quiz_attempt")
        return self

    def body_hash(self) -> str:
        """Canonical digest for replay detection (sorted keys, no None)."""
        canonical = json.dumps(self.model_dump(mode="json", exclude_none=True), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


class EventAccepted(BaseModel):
    id: str
    event_id: str
    duplicate: bool
    # Explicit so a policy-stripped context is never a silent drop.
    context_summary_stored: bool
    review_due_at: datetime | None = None


class PolicySettings(BaseModel):
    """Organization policy served to clients and edited by admins."""

    model_config = ConfigDict(extra="forbid")

    collect_enabled: bool = True
    # Default-deny: context summaries carry abstracted work content.
    allow_context_summary: bool = False
    retention_days: int = Field(default=365, ge=1, le=3650)


class PolicyOut(BaseModel):
    organization_key: str
    settings: PolicySettings
