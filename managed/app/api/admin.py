"""Admin API: JSON-only read/write surface for org admins, coaches, auditors.

Access control and audit are router-level, so they hold for every route by
construction: `audit_admin_access` records each request (action = route
name, including 404 probes and role-denied attempts), and a default
read-role gate applies to any route that does not declare a stricter one.
"""

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from app.auth.rbac import AUDIT_READ_ROLES, POLICY_WRITE_ROLES, READ_ROLES
from app.db.models import AuditLog, Contributor, ReviewSchedule
from app.deps import AdminOrgDep, DbDep, audit_admin_access, require_roles
from app.schemas.admin import (
    AuditLogListOut,
    AuditLogOut,
    ContributorListOut,
    ContributorOut,
    ContributorSummaryOut,
    PolicyUpdateIn,
    ReviewDueListOut,
    ReviewDueOut,
)
from app.schemas.collector import PolicyOut
from app.services import policies, summaries

router = APIRouter(
    prefix="/v1/admin",
    tags=["admin"],
    # Order matters: audit first so denied attempts are recorded too.
    dependencies=[Depends(audit_admin_access), require_roles(*READ_ROLES)],
)

LimitParam = Annotated[int, Query(ge=1, le=200)]
OffsetParam = Annotated[int, Query(ge=0)]


def _get_contributor(db: DbDep, organization_id: uuid.UUID, contributor_id: str) -> Contributor:
    try:
        parsed = uuid.UUID(contributor_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contributor not found") from exc
    contributor = db.get(Contributor, parsed)
    if contributor is None or contributor.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contributor not found")
    return contributor


@router.get("/contributors", response_model=ContributorListOut)
def list_contributors(
    organization: AdminOrgDep,
    db: DbDep,
    limit: LimitParam = 50,
    offset: OffsetParam = 0,
) -> ContributorListOut:
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
    return ContributorListOut(contributors=[ContributorOut.model_validate(row) for row in rows], total=total or 0)


@router.get("/contributors/{contributor_id}/summary", response_model=ContributorSummaryOut)
def get_contributor_summary(
    contributor_id: str,
    organization: AdminOrgDep,
    db: DbDep,
) -> ContributorSummaryOut:
    contributor = _get_contributor(db, organization.id, contributor_id)
    return summaries.contributor_summary(db, contributor)


@router.get("/reviews/due", response_model=ReviewDueListOut)
def list_reviews_due(
    organization: AdminOrgDep,
    db: DbDep,
    limit: LimitParam = 50,
) -> ReviewDueListOut:
    now = datetime.now(UTC)
    rows = db.scalars(
        select(ReviewSchedule)
        .where(ReviewSchedule.organization_id == organization.id, ReviewSchedule.due_at <= now)
        .order_by(ReviewSchedule.due_at)
        .limit(limit)
    ).all()
    return ReviewDueListOut(due=[ReviewDueOut.model_validate(row) for row in rows])


@router.get("/policies", response_model=PolicyOut)
def get_policies(organization: AdminOrgDep, db: DbDep) -> PolicyOut:
    return PolicyOut(organization_key=organization.key, settings=policies.get_policy(db, organization.id))


@router.put("/policies", response_model=PolicyOut, dependencies=[require_roles(*POLICY_WRITE_ROLES)])
def put_policies(
    payload: PolicyUpdateIn,
    organization: AdminOrgDep,
    db: DbDep,
) -> PolicyOut:
    updated = policies.put_policy(db, organization.id, payload.settings)
    return PolicyOut(organization_key=organization.key, settings=updated)


@router.get("/audit-logs", response_model=AuditLogListOut, dependencies=[require_roles(*AUDIT_READ_ROLES)])
def list_audit_logs(
    organization: AdminOrgDep,
    db: DbDep,
    limit: LimitParam = 50,
    offset: OffsetParam = 0,
) -> AuditLogListOut:
    rows = db.scalars(
        select(AuditLog)
        .where(AuditLog.organization_id == organization.id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return AuditLogListOut(logs=[AuditLogOut.model_validate(row) for row in rows])
