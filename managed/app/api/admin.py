"""Admin API: JSON-only read/write surface for org admins, coaches, auditors.

Every handler appends to the audit trail — reads included — because admin
visibility over contributor data is itself the thing being audited.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.auth.rbac import AUDIT_READ_ROLES, POLICY_WRITE_ROLES, READ_ROLES
from app.db.models import AuditLog, Contributor, ReviewSchedule
from app.deps import AdminOrgDep, AdminPrincipalDep, DbDep, require_roles
from app.schemas.admin import (
    AuditLogListOut,
    AuditLogOut,
    ContributorListOut,
    ContributorSummaryOut,
    PolicyUpdateIn,
    ReviewDueListOut,
    ReviewDueOut,
)
from app.schemas.collector import PolicyOut
from app.services import audit, policies, summaries

router = APIRouter(prefix="/v1/admin", tags=["admin"])


def _get_contributor(db: DbDep, organization_id: uuid.UUID, contributor_id: str) -> Contributor:
    try:
        parsed = uuid.UUID(contributor_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contributor not found") from exc
    contributor = db.get(Contributor, parsed)
    if contributor is None or contributor.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contributor not found")
    return contributor


@router.get("/contributors", response_model=ContributorListOut, dependencies=[require_roles(*READ_ROLES)])
def list_contributors(
    organization: AdminOrgDep,
    principal: AdminPrincipalDep,
    db: DbDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ContributorListOut:
    audit.record(db, organization_id=organization.id, actor=principal.subject, action="contributors.list")
    total = db.scalar(
        select(func.count()).select_from(Contributor).where(Contributor.organization_id == organization.id)
    )
    rows = db.scalars(
        select(Contributor)
        .where(Contributor.organization_id == organization.id)
        .order_by(Contributor.created_at, Contributor.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return ContributorListOut(contributors=[summaries.contributor_out(row) for row in rows], total=total or 0)


@router.get(
    "/contributors/{contributor_id}/summary",
    response_model=ContributorSummaryOut,
    dependencies=[require_roles(*READ_ROLES)],
)
def get_contributor_summary(
    contributor_id: str,
    organization: AdminOrgDep,
    principal: AdminPrincipalDep,
    db: DbDep,
) -> ContributorSummaryOut:
    contributor = _get_contributor(db, organization.id, contributor_id)
    audit.record(
        db,
        organization_id=organization.id,
        actor=principal.subject,
        action="contributors.summary",
        target_type="contributor",
        target_id=str(contributor.id),
    )
    return summaries.contributor_summary(db, contributor)


@router.get("/reviews/due", response_model=ReviewDueListOut, dependencies=[require_roles(*READ_ROLES)])
def list_reviews_due(
    organization: AdminOrgDep,
    principal: AdminPrincipalDep,
    db: DbDep,
    limit: int = Query(default=50, ge=1, le=200),
) -> ReviewDueListOut:
    audit.record(db, organization_id=organization.id, actor=principal.subject, action="reviews.due")
    now = datetime.now(UTC)
    rows = db.scalars(
        select(ReviewSchedule)
        .where(ReviewSchedule.organization_id == organization.id, ReviewSchedule.due_at <= now)
        .order_by(ReviewSchedule.due_at)
        .limit(limit)
    ).all()
    return ReviewDueListOut(
        due=[
            ReviewDueOut(
                contributor_id=str(row.contributor_id),
                category=row.category,
                signal=row.signal or None,
                due_at=row.due_at,
                interval_days=row.interval_days,
                last_outcome=row.last_outcome,
            )
            for row in rows
        ]
    )


@router.get("/policies", response_model=PolicyOut, dependencies=[require_roles(*READ_ROLES)])
def get_policies(organization: AdminOrgDep, principal: AdminPrincipalDep, db: DbDep) -> PolicyOut:
    audit.record(db, organization_id=organization.id, actor=principal.subject, action="policies.get")
    return PolicyOut(organization_key=organization.key, settings=policies.get_policy(db, organization.id))


@router.put("/policies", response_model=PolicyOut, dependencies=[require_roles(*POLICY_WRITE_ROLES)])
def put_policies(
    payload: PolicyUpdateIn,
    organization: AdminOrgDep,
    principal: AdminPrincipalDep,
    db: DbDep,
) -> PolicyOut:
    updated = policies.put_policy(db, organization.id, payload.settings)
    audit.record(
        db,
        organization_id=organization.id,
        actor=principal.subject,
        action="policies.put",
        target_type="policy",
        target_id=organization.key,
    )
    return PolicyOut(organization_key=organization.key, settings=updated)


@router.get("/audit-logs", response_model=AuditLogListOut, dependencies=[require_roles(*AUDIT_READ_ROLES)])
def list_audit_logs(
    organization: AdminOrgDep,
    principal: AdminPrincipalDep,
    db: DbDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> AuditLogListOut:
    audit.record(db, organization_id=organization.id, actor=principal.subject, action="audit_logs.list")
    rows = db.scalars(
        select(AuditLog)
        .where(AuditLog.organization_id == organization.id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return AuditLogListOut(
        logs=[
            AuditLogOut(
                actor=row.actor,
                action=row.action,
                target_type=row.target_type,
                target_id=row.target_id,
                created_at=row.created_at,
            )
            for row in rows
        ]
    )
