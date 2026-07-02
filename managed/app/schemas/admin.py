"""Admin API contract (JSON only; UI is a later layer)."""

from datetime import datetime

from pydantic import BaseModel

from app.schemas.collector import PolicySettings


class ContributorOut(BaseModel):
    id: str
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
    contributor_id: str
    category: str
    signal: str | None
    due_at: datetime
    interval_days: int
    last_outcome: str | None


class ReviewDueListOut(BaseModel):
    due: list[ReviewDueOut]


class PolicyUpdateIn(BaseModel):
    settings: PolicySettings


class AuditLogOut(BaseModel):
    actor: str
    action: str
    target_type: str | None
    target_id: str | None
    created_at: datetime


class AuditLogListOut(BaseModel):
    logs: list[AuditLogOut]
