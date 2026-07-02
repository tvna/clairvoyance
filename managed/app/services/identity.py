"""Contributor identity resolution.

Identity is (organization, provider, external_id); display name and email are
descriptive attributes refreshed from the latest event, never identity.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Contributor, Organization
from app.schemas.collector import ContributorIn


def resolve_contributor(db: Session, organization: Organization, payload: ContributorIn) -> Contributor:
    contributor = db.scalars(
        select(Contributor).where(
            Contributor.organization_id == organization.id,
            Contributor.provider == payload.provider,
            Contributor.external_id == payload.external_id,
        )
    ).first()
    if contributor is None:
        contributor = Contributor(
            organization_id=organization.id,
            provider=payload.provider,
            external_id=payload.external_id,
            display_name=payload.display_name,
            email=payload.email,
        )
        db.add(contributor)
        db.flush()
        return contributor

    if payload.display_name is not None and payload.display_name != contributor.display_name:
        contributor.display_name = payload.display_name
    if payload.email is not None and payload.email != contributor.email:
        contributor.email = payload.email
    return contributor
