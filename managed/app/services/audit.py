"""Audit trail for admin access (reads and writes alike)."""

import uuid

from sqlalchemy.orm import Session

from app.db.models import AuditLog


def record(
    db: Session,
    *,
    organization_id: uuid.UUID,
    actor: str,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
) -> None:
    db.add(
        AuditLog(
            organization_id=organization_id,
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
        )
    )
    db.flush()
