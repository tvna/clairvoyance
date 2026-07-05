"""Organization lookup — the tenant boundary, resolved in exactly one place."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Organization


def get_by_key(db: Session, key: str) -> Organization | None:
    return db.scalars(select(Organization).where(Organization.key == key)).first()
