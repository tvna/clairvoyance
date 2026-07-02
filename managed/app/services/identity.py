"""Contributor identity resolution.

Identity is (organization, provider, external_id); display name and email are
descriptive attributes refreshed from the latest event, never identity.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Contributor, Organization
from app.schemas.collector import ContributorIn


def _find(db: Session, organization: Organization, payload: ContributorIn) -> Contributor | None:
    return db.scalars(
        select(Contributor).where(
            Contributor.organization_id == organization.id,
            Contributor.provider == payload.provider,
            Contributor.external_id == payload.external_id,
        )
    ).first()


def resolve_contributor(db: Session, organization: Organization, payload: ContributorIn) -> Contributor:
    contributor = _find(db, organization, payload)
    if contributor is None:
        contributor = Contributor(
            organization_id=organization.id,
            provider=payload.provider,
            external_id=payload.external_id,
            display_name=payload.display_name,
            email=payload.email,
        )
        try:
            # SAVEPOINT so losing a concurrent first-insert race only rolls
            # back this insert, not the caller's transaction.
            with db.begin_nested():
                db.add(contributor)
        except IntegrityError:
            raced = _find(db, organization, payload)
            if raced is None:
                raise
            contributor = raced
        else:
            return contributor

    if payload.display_name is not None:
        contributor.display_name = payload.display_name
    if payload.email is not None:
        contributor.email = payload.email
    return contributor
