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
from pydantic import AwareDatetime
from sqlalchemy import ColumnElement, func, or_, select

from app.auth.rbac import AUDIT_READ_ROLES, POLICY_WRITE_ROLES, READ_ROLES, REVIEW_DISMISS_ROLES
from app.db.models import AuditLog, Contributor, ReviewSchedule
from app.deps import AdminOrgDep, AdminPrincipalDep, DbDep, audit_admin_access, require_roles
from app.schemas.admin import (
    AuditLogListOut,
    AuditLogOut,
    ContributorListOut,
    ContributorOut,
    ContributorSummaryOut,
    PolicyUpdateIn,
    ReviewDismissOut,
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


def _contributor_search(q: str) -> ColumnElement[bool]:
    """Case-insensitive partial match over the identity fields. LIKE
    metacharacters in the query are escaped so they match literally."""
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    return or_(
        Contributor.display_name.ilike(pattern, escape="\\"),
        Contributor.external_id.ilike(pattern, escape="\\"),
        Contributor.email.ilike(pattern, escape="\\"),
    )


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
    q: Annotated[str | None, Query()] = None,
) -> ContributorListOut:
    filters: list[ColumnElement[bool]] = [Contributor.organization_id == organization.id]
    if q:
        filters.append(_contributor_search(q))
    # total counts the filtered set, so paging math stays correct under search.
    total = db.scalar(select(func.count()).select_from(Contributor).where(*filters))
    rows = db.scalars(
        select(Contributor).where(*filters).order_by(Contributor.created_at, Contributor.id).limit(limit).offset(offset)
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


def _get_schedule(db: DbDep, organization_id: uuid.UUID, schedule_id: str) -> ReviewSchedule:
    # 404 (not 422) on a malformed id, mirroring _get_contributor: the caller
    # is probing for a schedule that may not be theirs, and org-foreign or
    # nonexistent ids are indistinguishable by design.
    try:
        parsed = uuid.UUID(schedule_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="review schedule not found") from exc
    schedule = db.get(ReviewSchedule, parsed)
    if schedule is None or schedule.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="review schedule not found")
    return schedule


@router.get("/reviews/due", response_model=ReviewDueListOut)
def list_reviews_due(
    organization: AdminOrgDep,
    db: DbDep,
    limit: LimitParam = 50,
    offset: OffsetParam = 0,
    contributor_id: Annotated[uuid.UUID | None, Query()] = None,
) -> ReviewDueListOut:
    now = datetime.now(UTC)
    filters: list[ColumnElement[bool]] = [
        ReviewSchedule.organization_id == organization.id,
        ReviewSchedule.due_at <= now,
        # Dismissed rows leave the work queue until a newer attempt reopens them.
        ReviewSchedule.status == "active",
    ]
    if contributor_id is not None:
        filters.append(ReviewSchedule.contributor_id == contributor_id)
    rows = db.execute(
        select(ReviewSchedule, Contributor)
        .join(Contributor, Contributor.id == ReviewSchedule.contributor_id)
        .where(*filters)
        # Stable secondary key: due_at ties (coarse/imported timestamps) would
        # otherwise let offset paging duplicate or skip rows, matching the
        # tiebreaker the contributors and audit-log endpoints already use.
        .order_by(ReviewSchedule.due_at, ReviewSchedule.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return ReviewDueListOut(
        due=[
            ReviewDueOut(
                id=schedule.id,
                contributor_id=schedule.contributor_id,
                display_name=contributor.display_name,
                provider=contributor.provider,
                external_id=contributor.external_id,
                category=schedule.category,
                signal=schedule.signal,
                due_at=schedule.due_at,
                interval_days=schedule.interval_days,
                last_outcome=schedule.last_outcome,
            )
            for schedule, contributor in rows
        ]
    )


@router.post(
    "/reviews/{schedule_id}/dismiss",
    response_model=ReviewDismissOut,
    dependencies=[require_roles(*REVIEW_DISMISS_ROLES)],
)
def dismiss_review(
    schedule_id: str,
    organization: AdminOrgDep,
    principal: AdminPrincipalDep,
    db: DbDep,
) -> ReviewDismissOut:
    schedule = _get_schedule(db, organization.id, schedule_id)
    # Idempotent: re-dismissing an already-dismissed row refreshes the actor
    # and timestamp rather than erroring. A newer quiz attempt reopens it
    # (scheduling.apply_outcome), so this is not a terminal state.
    schedule.status = "dismissed"
    schedule.dismissed_at = datetime.now(UTC)
    schedule.dismissed_by = principal.subject
    db.flush()
    return ReviewDismissOut.model_validate(schedule)


@router.get("/policies", response_model=PolicyOut)
def get_policies(organization: AdminOrgDep, db: DbDep) -> PolicyOut:
    return PolicyOut(organization_key=organization.key, settings=policies.get_policy(db, organization.id))


@router.put("/policies", response_model=PolicyOut, dependencies=[require_roles(*POLICY_WRITE_ROLES)])
def put_policies(
    payload: PolicyUpdateIn,
    organization: AdminOrgDep,
    db: DbDep,
) -> PolicyOut:
    current = policies.get_policy(db, organization.id)
    updated = policies.put_policy(db, organization.id, payload.merge_with(current))
    return PolicyOut(organization_key=organization.key, settings=updated)


@router.get("/audit-logs", response_model=AuditLogListOut, dependencies=[require_roles(*AUDIT_READ_ROLES)])
def list_audit_logs(
    organization: AdminOrgDep,
    db: DbDep,
    limit: LimitParam = 50,
    offset: OffsetParam = 0,
    # AwareDatetime rejects a naive value with 422: the audit trail is stored
    # UTC-aware end to end, so a tz-less bound would be an ambiguous filter.
    from_: Annotated[AwareDatetime | None, Query(alias="from")] = None,
    to: Annotated[AwareDatetime | None, Query(alias="to")] = None,
) -> AuditLogListOut:
    filters: list[ColumnElement[bool]] = [AuditLog.organization_id == organization.id]
    if from_ is not None:
        filters.append(AuditLog.created_at >= from_)
    if to is not None:
        filters.append(AuditLog.created_at <= to)
    total = db.scalar(select(func.count()).select_from(AuditLog).where(*filters))
    rows = db.scalars(
        select(AuditLog).where(*filters).order_by(AuditLog.created_at.desc(), AuditLog.id).limit(limit).offset(offset)
    ).all()
    return AuditLogListOut(logs=[AuditLogOut.model_validate(row) for row in rows], total=total or 0)
