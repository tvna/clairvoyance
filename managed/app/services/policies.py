"""Organization policy read/write with validated defaults."""

import uuid

from sqlalchemy.orm import Session

from app.db.models import AdminPolicy
from app.schemas.collector import PolicySettings


def get_policy(db: Session, organization_id: uuid.UUID) -> PolicySettings:
    row = db.get(AdminPolicy, organization_id)
    if row is None:
        return PolicySettings()
    return PolicySettings.model_validate(row.settings)


def put_policy(db: Session, organization_id: uuid.UUID, settings: PolicySettings) -> PolicySettings:
    row = db.get(AdminPolicy, organization_id)
    if row is None:
        row = AdminPolicy(organization_id=organization_id, settings=settings.model_dump())
        db.add(row)
    else:
        row.settings = settings.model_dump()
    db.flush()
    return settings
