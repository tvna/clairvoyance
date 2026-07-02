"""Admin API contract (JSON only; UI is a later layer).

Out-models map straight from ORM rows (``from_attributes``) so a new column
reaches the API by touching the model and the schema, with no hand-copy site
to forget.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.collector import PolicySettings


class ContributorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: str
    external_id: str
    display_name: str | None
    email: str | None
    active: bool
    created_at: datetime


class ContributorListOut(BaseModel):
    contributors: list[ContributorOut]
    total: int


class QuizStats(BaseModel):
    attempts: int
    correct: int
    calibration: dict[str, int]


class ContributorSummaryOut(BaseModel):
    contributor: ContributorOut
    events_total: int
    events_by_category: dict[str, int]
    quiz: QuizStats
    last_event_at: datetime | None


class ReviewDueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contributor_id: uuid.UUID
    category: str
    signal: str | None
    due_at: datetime
    interval_days: int
    last_outcome: str | None

    @field_validator("signal", mode="before")
    @classmethod
    def empty_signal_is_none(cls, value: str | None) -> str | None:
        # Stored as '' (unique-constraint requirement); '' means "no signal".
        return value or None


class ReviewDueListOut(BaseModel):
    due: list[ReviewDueOut]


class PolicyUpdateIn(BaseModel):
    settings: PolicySettings


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    actor: str
    action: str
    target_type: str | None
    target_id: str | None
    created_at: datetime


class AuditLogListOut(BaseModel):
    logs: list[AuditLogOut]
