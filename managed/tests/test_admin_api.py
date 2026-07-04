"""Admin API: RBAC, org scoping, audit trail."""

from datetime import UTC, datetime
from typing import Any

from conftest import SeededOrg, admin_override, make_settings
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from test_collector_api import auth, event_payload

from app.auth.oidc import OIDCVerifier
from app.auth.rbac import Role
from app.db.models import AuditLog, Contributor, Organization, ReviewSchedule


def seed_events(client: TestClient, seeded_org: SeededOrg) -> None:
    past = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
    assert (
        client.post(
            "/v1/events",
            json=event_payload(event_id="OBS1", occurred_at=past.isoformat()),
            headers=auth(seeded_org),
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/v1/events",
            json=event_payload(
                event_id="QUIZ1",
                event_type="quiz_attempt",
                occurred_at=past.isoformat(),
                quiz={"outcome": "correct", "confidence": "high", "calibration": "overconfident"},
            ),
            headers=auth(seeded_org),
        ).status_code
        == 201
    )


def test_admin_requires_bearer(client: TestClient) -> None:
    assert client.get("/v1/admin/contributors").status_code == 401


def test_admin_503_when_oidc_unconfigured(client: TestClient) -> None:
    response = client.get("/v1/admin/contributors", headers={"Authorization": "Bearer whatever"})
    assert response.status_code == 503
    # Drift gate: the admin SPA distinguishes the two 503 states by this
    # exact detail string (managed/ui/src/api/client.ts). Rewording it
    # silently downgrades the SPA's operator-facing config error to a
    # generic failure, so the string is part of the API contract.
    assert response.json()["detail"] == "admin OIDC is not configured"


def test_admin_401_on_invalid_token_when_oidc_configured(app: FastAPI, client: TestClient) -> None:
    app.state.oidc_verifier = OIDCVerifier(
        make_settings(
            oidc_issuer="https://idp.example.com",
            oidc_audience="clairvoyance-managed",
            oidc_jwks_url="http://127.0.0.1:9/jwks.json",
        )
    )
    response = client.get("/v1/admin/contributors", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401


def test_admin_503_when_jwks_unreachable(app: FastAPI, client: TestClient) -> None:
    from test_oidc import AUDIENCE, ISSUER, make_token

    app.state.oidc_verifier = OIDCVerifier(
        make_settings(oidc_issuer=ISSUER, oidc_audience=AUDIENCE, oidc_jwks_url="http://127.0.0.1:9/jwks.json")
    )
    response = client.get("/v1/admin/contributors", headers={"Authorization": f"Bearer {make_token()}"})
    assert response.status_code == 503
    # Drift gate: paired with managed/ui/src/api/client.ts, which maps this
    # exact detail string to the retryable transient-503 state.
    assert response.json()["detail"] == "OIDC JWKS endpoint is unavailable"


def test_unknown_organization_forbidden(app: FastAPI, client: TestClient) -> None:
    admin_override(app, org_key="ghost")
    assert client.get("/v1/admin/contributors").status_code == 403


def test_role_matrix(app: FastAPI, client: TestClient, seeded_org: SeededOrg) -> None:
    cases: list[tuple[tuple[Role, ...], str, str, int, dict[str, Any] | None]] = [
        ((Role.COACH,), "GET", "/v1/admin/contributors", 200, None),
        ((Role.TEAM_MANAGER,), "GET", "/v1/admin/reviews/due", 200, None),
        ((Role.AUDITOR,), "GET", "/v1/admin/audit-logs", 200, None),
        ((Role.COACH,), "GET", "/v1/admin/audit-logs", 403, None),
        ((Role.COACH,), "PUT", "/v1/admin/policies", 403, {"settings": {"collect_enabled": True}}),
        ((), "GET", "/v1/admin/contributors", 403, None),
    ]
    for roles, method, path, expected, body in cases:
        admin_override(app, roles=roles)
        response = client.request(method, path, json=body)
        assert response.status_code == expected, (roles, method, path)


def test_list_contributors_pagination(app: FastAPI, client: TestClient, seeded_org: SeededOrg) -> None:
    seed_events(client, seeded_org)
    admin_override(app, roles=(Role.COACH,))
    response = client.get("/v1/admin/contributors", params={"limit": 1, "offset": 0})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["contributors"][0]["external_id"] == "12345678"


def test_contributor_summary(app: FastAPI, client: TestClient, seeded_org: SeededOrg) -> None:
    seed_events(client, seeded_org)
    admin_override(app, roles=(Role.COACH,))
    contributor_id = client.get("/v1/admin/contributors").json()["contributors"][0]["id"]
    response = client.get(f"/v1/admin/contributors/{contributor_id}/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["events_total"] == 2
    assert body["events_by_category"] == {"avoidance": 2}
    assert body["quiz"] == {"attempts": 1, "correct": 1, "calibration": {"overconfident": 1}}
    assert body["last_event_at"] is not None


def test_contributor_summary_not_found_is_audited(
    app: FastAPI, client: TestClient, seeded_org: SeededOrg, db: Session
) -> None:
    admin_override(app)
    assert client.get("/v1/admin/contributors/not-a-uuid/summary").status_code == 404
    missing = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"/v1/admin/contributors/{missing}/summary").status_code == 404

    # Probing for contributors is exactly the access pattern the audit trail
    # exists for; misses must be recorded, not just hits.
    probes = db.scalars(select(AuditLog).where(AuditLog.action == "get_contributor_summary")).all()
    assert [row.target_id for row in probes] == ["not-a-uuid", missing]
    assert all(row.target_type == "contributor" for row in probes)


def test_contributor_of_other_org_hidden(
    app: FastAPI, client: TestClient, seeded_org: SeededOrg, session_factory: sessionmaker[Session]
) -> None:
    with session_factory() as session:
        other = Organization(key="other", name="Other")
        session.add(other)
        session.flush()
        foreign = Contributor(organization_id=other.id, provider="github", external_id="999")
        session.add(foreign)
        session.commit()
        foreign_id = str(foreign.id)
    admin_override(app)
    assert client.get(f"/v1/admin/contributors/{foreign_id}/summary").status_code == 404


def test_reviews_due_lists_past_due_only(app: FastAPI, client: TestClient, seeded_org: SeededOrg) -> None:
    seed_events(client, seeded_org)  # QUIZ1 occurred 2026-01-01, so its due point is long past
    admin_override(app, roles=(Role.COACH,))
    response = client.get("/v1/admin/reviews/due")
    assert response.status_code == 200
    due = response.json()["due"]
    assert len(due) == 1
    assert due[0]["category"] == "avoidance"
    assert due[0]["signal"] == "deferred-risk-call"
    assert due[0]["last_outcome"] == "correct"
    assert due[0]["interval_days"] == 7  # correct + high confidence (quiz.md contract)


def test_contributor_search_matches_identity_fields(app: FastAPI, client: TestClient, seeded_org: SeededOrg) -> None:
    seed_events(client, seeded_org)  # display_name=octocat, provider=github, external_id=12345678
    admin_override(app, roles=(Role.COACH,))

    # Case-insensitive partial match on display_name, and total counts the
    # filtered set (not every contributor).
    hit = client.get("/v1/admin/contributors", params={"q": "OCTO"}).json()
    assert hit["total"] == 1
    assert hit["contributors"][0]["external_id"] == "12345678"

    # Partial match on external_id too.
    assert client.get("/v1/admin/contributors", params={"q": "1234"}).json()["total"] == 1

    # A non-matching query returns an empty, correctly-counted page.
    miss = client.get("/v1/admin/contributors", params={"q": "nobody"}).json()
    assert miss["total"] == 0
    assert miss["contributors"] == []


def test_reviews_due_carries_contributor_identity(app: FastAPI, client: TestClient, seeded_org: SeededOrg) -> None:
    seed_events(client, seeded_org)
    admin_override(app, roles=(Role.COACH,))
    due = client.get("/v1/admin/reviews/due").json()["due"]
    assert len(due) == 1
    # Identity now rides on the row (no client-side join needed).
    assert due[0]["display_name"] == "octocat"
    assert due[0]["provider"] == "github"
    assert due[0]["external_id"] == "12345678"


def test_reviews_due_filters_by_contributor_and_offset(
    app: FastAPI, client: TestClient, seeded_org: SeededOrg, db: Session
) -> None:
    seed_events(client, seeded_org)
    admin_override(app, roles=(Role.COACH,))
    contributor_id = db.scalars(select(Contributor)).one().id

    # A matching contributor filter keeps the row.
    scoped = client.get("/v1/admin/reviews/due", params={"contributor_id": str(contributor_id)})
    assert len(scoped.json()["due"]) == 1

    # A foreign contributor id filters it out.
    other = "00000000-0000-0000-0000-000000000000"
    assert client.get("/v1/admin/reviews/due", params={"contributor_id": other}).json()["due"] == []

    # Offset past the only row yields an empty page.
    assert client.get("/v1/admin/reviews/due", params={"offset": 1}).json()["due"] == []


def test_reviews_due_pagination_is_stable_across_due_at_ties(
    app: FastAPI,
    client: TestClient,
    seeded_org: SeededOrg,
    session_factory: sessionmaker[Session],
) -> None:
    # Two schedules sharing an identical due_at: without a unique secondary
    # sort key, offset paging can duplicate or skip one of them.
    org = seeded_org.organization
    due = datetime(2026, 1, 1, tzinfo=UTC)
    expected_ids = set()
    with session_factory() as session:
        for external_id in ("aaa", "bbb"):
            contributor = Contributor(organization_id=org.id, provider="github", external_id=external_id)
            session.add(contributor)
            session.flush()
            schedule = ReviewSchedule(
                organization_id=org.id,
                contributor_id=contributor.id,
                category="avoidance",
                signal="",
                due_at=due,
                interval_days=2,
                last_outcome="incorrect",
                last_attempted_at=due,
            )
            session.add(schedule)
            session.flush()
            expected_ids.add(str(schedule.id))
        session.commit()

    admin_override(app, roles=(Role.COACH,))
    first = client.get("/v1/admin/reviews/due", params={"limit": 1, "offset": 0}).json()["due"]
    second = client.get("/v1/admin/reviews/due", params={"limit": 1, "offset": 1}).json()["due"]
    assert len(first) == 1
    assert len(second) == 1
    # Both distinct rows are returned across the two pages -- none skipped or
    # duplicated.
    assert {first[0]["id"], second[0]["id"]} == expected_ids


def test_audit_logs_report_total_and_filter_by_time(app: FastAPI, client: TestClient, seeded_org: SeededOrg) -> None:
    admin_override(app, roles=(Role.ORG_ADMIN,))
    assert client.get("/v1/admin/contributors").status_code == 200

    body = client.get("/v1/admin/audit-logs").json()
    assert body["total"] >= 2  # the contributors read plus this audit-logs read
    assert body["total"] == len(body["logs"])  # small dataset fits one page

    # A future lower bound excludes everything; a past upper bound too.
    future = client.get("/v1/admin/audit-logs", params={"from": "2999-01-01T00:00:00+00:00"}).json()
    assert future["total"] == 0
    assert future["logs"] == []
    assert client.get("/v1/admin/audit-logs", params={"to": "2000-01-01T00:00:00+00:00"}).json()["total"] == 0


def test_audit_logs_reject_naive_time_bound(app: FastAPI, client: TestClient, seeded_org: SeededOrg) -> None:
    admin_override(app, roles=(Role.ORG_ADMIN,))
    # A timezone-naive bound is ambiguous against UTC-aware storage -> 422.
    assert client.get("/v1/admin/audit-logs", params={"from": "2026-01-01T00:00:00"}).status_code == 422


def test_dismiss_removes_review_from_due_and_is_audited(
    app: FastAPI, client: TestClient, seeded_org: SeededOrg, db: Session
) -> None:
    seed_events(client, seeded_org)
    schedule_id = str(db.scalars(select(ReviewSchedule)).one().id)
    admin_override(app, roles=(Role.COACH,))
    assert len(client.get("/v1/admin/reviews/due").json()["due"]) == 1

    response = client.post(f"/v1/admin/reviews/{schedule_id}/dismiss")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "dismissed"
    assert body["dismissed_by"] == "admin@example.com"
    assert body["dismissed_at"] is not None

    # The dismissed row leaves the work queue.
    assert client.get("/v1/admin/reviews/due").json()["due"] == []

    # The write is on the audit record, targeted at the schedule.
    dismissals = db.scalars(select(AuditLog).where(AuditLog.action == "dismiss_review")).all()
    assert any(row.target_type == "review_schedule" and row.target_id == schedule_id for row in dismissals)


def test_dismiss_denied_for_non_dismiss_role_is_audited(
    app: FastAPI, client: TestClient, seeded_org: SeededOrg, db: Session
) -> None:
    seed_events(client, seeded_org)
    schedule_id = str(db.scalars(select(ReviewSchedule)).one().id)
    # Auditor can read but not dismiss (REVIEW_DISMISS_ROLES = org_admin, coach).
    admin_override(app, roles=(Role.AUDITOR,))
    assert client.post(f"/v1/admin/reviews/{schedule_id}/dismiss").status_code == 403

    denied = db.scalars(select(AuditLog).where(AuditLog.action == "dismiss_review")).all()
    assert len(denied) == 1  # the denied attempt itself is recorded
    assert denied[0].target_type == "review_schedule"
    assert denied[0].target_id == schedule_id


def test_dismiss_not_found_matches_contributor_semantics(
    app: FastAPI, client: TestClient, seeded_org: SeededOrg
) -> None:
    admin_override(app, roles=(Role.ORG_ADMIN,))
    assert client.post("/v1/admin/reviews/not-a-uuid/dismiss").status_code == 404
    missing = "00000000-0000-0000-0000-000000000000"
    assert client.post(f"/v1/admin/reviews/{missing}/dismiss").status_code == 404


def test_policies_roundtrip_and_audit(app: FastAPI, client: TestClient, seeded_org: SeededOrg, db: Session) -> None:
    admin_override(app, roles=(Role.ORG_ADMIN,))
    initial = client.get("/v1/admin/policies")
    assert initial.status_code == 200
    assert initial.json()["settings"]["allow_context_summary"] is False

    updated = client.put(
        "/v1/admin/policies",
        json={"settings": {"collect_enabled": True, "allow_context_summary": True, "retention_days": 30}},
    )
    assert updated.status_code == 200
    assert updated.json()["settings"]["retention_days"] == 30

    overwrite = client.put(
        "/v1/admin/policies",
        json={"settings": {"collect_enabled": True, "allow_context_summary": False, "retention_days": 90}},
    )
    assert overwrite.status_code == 200

    reread = client.get("/v1/admin/policies")
    assert reread.json()["settings"] == {
        "collect_enabled": True,
        "allow_context_summary": False,
        "retention_days": 90,
    }

    actions = [row.action for row in db.scalars(select(AuditLog)).all()]
    assert actions == ["get_policies", "put_policies", "put_policies", "get_policies"]
    assert all(row.actor == "admin@example.com" for row in db.scalars(select(AuditLog)).all())


def test_policy_partial_update_preserves_existing_values(
    app: FastAPI, client: TestClient, seeded_org: SeededOrg
) -> None:
    admin_override(app, roles=(Role.ORG_ADMIN,))
    full = client.put(
        "/v1/admin/policies",
        json={"settings": {"collect_enabled": True, "allow_context_summary": True, "retention_days": 30}},
    )
    assert full.status_code == 200

    partial = client.put("/v1/admin/policies", json={"settings": {"collect_enabled": False}})
    assert partial.status_code == 200
    assert partial.json()["settings"] == {
        "collect_enabled": False,
        "allow_context_summary": True,
        "retention_days": 30,
    }


def test_policy_partial_update_rejects_nulls(app: FastAPI, client: TestClient, seeded_org: SeededOrg) -> None:
    admin_override(app, roles=(Role.ORG_ADMIN,))
    response = client.put("/v1/admin/policies", json={"settings": {"collect_enabled": None}})
    assert response.status_code == 422


def test_policy_rejects_out_of_range_retention(app: FastAPI, client: TestClient, seeded_org: SeededOrg) -> None:
    admin_override(app)
    response = client.put("/v1/admin/policies", json={"settings": {"retention_days": 0}})
    assert response.status_code == 422


def test_audit_log_listing(app: FastAPI, client: TestClient, seeded_org: SeededOrg) -> None:
    admin_override(app, roles=(Role.ORG_ADMIN,))
    assert client.get("/v1/admin/contributors").status_code == 200
    response = client.get("/v1/admin/audit-logs")
    assert response.status_code == 200
    logs = response.json()["logs"]
    actions = {entry["action"] for entry in logs}
    assert "list_contributors" in actions
    assert "list_audit_logs" in actions


def test_role_denied_attempt_is_audited(app: FastAPI, client: TestClient, seeded_org: SeededOrg, db: Session) -> None:
    admin_override(app, roles=(Role.COACH,))
    assert client.get("/v1/admin/audit-logs").status_code == 403
    denied = db.scalars(select(AuditLog).where(AuditLog.action == "list_audit_logs")).all()
    assert len(denied) == 1  # the attempt itself is on the record


def test_handler_rollback_does_not_erase_audit_row(
    app: FastAPI, client: TestClient, seeded_org: SeededOrg, db: Session
) -> None:
    # 422 on the payload aborts the request transaction after the router-level
    # audit dependency ran; the audit row must survive in its own transaction.
    admin_override(app)
    assert client.put("/v1/admin/policies", json={"settings": {"retention_days": 0}}).status_code == 422
    assert len(db.scalars(select(AuditLog).where(AuditLog.action == "put_policies")).all()) == 1


def test_every_admin_route_is_audited_and_role_gated() -> None:
    """Structural gate: a new admin route cannot ship outside audit/RBAC.

    Both controls are attached at the router level, so it suffices that every
    route actually lives on that router with its dependencies intact.
    """
    from app.api.admin import router

    assert len(router.routes) >= 6
    dependency_fns = {dep.dependency for dep in router.dependencies}
    from app.deps import audit_admin_access

    assert audit_admin_access in dependency_fns
    assert len(dependency_fns) == 2  # audit + default read-role gate
