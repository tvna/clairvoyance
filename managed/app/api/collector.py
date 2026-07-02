"""Collector API: the only write path into managed mode."""

from fastapi import APIRouter, HTTPException, Response, status

from app.deps import CollectorOrgDep, DbDep
from app.schemas.collector import EventAccepted, EventIn, PolicyOut
from app.services import policies
from app.services.ingestion import CollectionDisabledError, EventConflictError, ingest_event

router = APIRouter(prefix="/v1", tags=["collector"])


@router.post("/events", response_model=EventAccepted, status_code=status.HTTP_201_CREATED)
def post_event(
    payload: EventIn,
    organization: CollectorOrgDep,
    db: DbDep,
    response: Response,
) -> EventAccepted:
    if payload.organization_key is not None and payload.organization_key != organization.key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="organization_key does not match the collector token",
        )
    policy = policies.get_policy(db, organization.id)
    try:
        result = ingest_event(db, organization, payload, policy)
    except CollectionDisabledError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="collection is disabled by organization policy",
        ) from exc
    except EventConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="event_id already exists with a different body",
        ) from exc

    if result.duplicate:
        response.status_code = status.HTTP_200_OK
    return EventAccepted(
        id=str(result.event.id),
        event_id=result.event.event_id,
        duplicate=result.duplicate,
        context_summary_stored=result.context_summary_stored,
        review_due_at=result.schedule.due_at if result.schedule else None,
    )


@router.get("/client/policy", response_model=PolicyOut)
def get_client_policy(organization: CollectorOrgDep, db: DbDep) -> PolicyOut:
    return PolicyOut(organization_key=organization.key, settings=policies.get_policy(db, organization.id))
