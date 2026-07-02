"""Admin API contract (JSON only; UI is a later layer).

Out-models map straight from ORM rows (``from_attributes``) so a new column
reaches the API by touching the model and the schema, with no hand-copy site
to forget.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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


class PolicySettingsPatch(BaseModel):
    """Partial admin update; omitted fields preserve the current policy."""

    model_config = ConfigDict(extra="forbid")

    collect_enabled: bool | None = None
    allow_context_summary: bool | None = None
    retention_days: int | None = Field(default=None, ge=1, le=3650)

    @model_validator(mode="after")
    def reject_null_updates(self) -> "PolicySettingsPatch":
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class PolicyUpdateIn(BaseModel):
    settings: PolicySettingsPatch

    def merge_with(self, current: PolicySettings) -> PolicySettings:
        merged = current.model_dump()
        merged.update(self.settings.model_dump(exclude_unset=True))
        return PolicySettings.model_validate(merged)


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    actor: str
    action: str
    target_type: str | None
    target_id: str | None
    created_at: datetime


class AuditLogListOut(BaseModel):
    logs: list[AuditLogOut]
