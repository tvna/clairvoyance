"""Collector API: auth, idempotency, policy gating, quiz scheduling."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from conftest import FakeRedis, SeededOrg, make_settings
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

import app.services.ingestion as ingestion_module
from app.db.models import CoachingEvent, Contributor, QuizAttempt
from app.main import create_app
from app.schemas.collector import PolicySettings
from app.services import policies


def event_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "event_type": "observation",
        "event_id": "01JZ2K6K9X5N6J5TWGEXAMPLE",
        "occurred_at": "2026-07-02T10:00:00Z",
        "contributor": {"provider": "github", "external_id": "12345678", "display_name": "octocat"},
        "source": {"repo": "acme/product", "runtime": "codex", "client_version": "0.1.0"},
        "category": "avoidance",
        "signal": "deferred-risk-call",
        "session_kind": "planning",
        "evidence_level": "observed",
    }
    payload.update(overrides)
    return payload


def auth(seeded_org: SeededOrg) -> dict[str, str]:
    return {"Authorization": f"Bearer {seeded_org.raw_token}"}


def test_events_requires_token(client: TestClient) -> None:
    assert client.post("/v1/events", json=event_payload()).status_code == 401


def test_events_rejects_unknown_token(client: TestClient, seeded_org: SeededOrg) -> None:
    response = client.post("/v1/events", json=event_payload(), headers={"Authorization": "Bearer cvk_wrong"})
    assert response.status_code == 401


def test_events_503_when_pepper_unset(seeded_org: SeededOrg, app: FastAPI) -> None:
    unconfigured = create_app(make_settings(collector_token_pepper=None))
    unconfigured.state.engine = app.state.engine
    unconfigured.state.session_factory = app.state.session_factory
    unconfigured.state.redis = FakeRedis()
    response = TestClient(unconfigured).post("/v1/events", json=event_payload(), headers=auth(seeded_org))
    assert response.status_code == 503


def test_ingest_observation(client: TestClient, seeded_org: SeededOrg, db: Session) -> None:
    response = client.post("/v1/events", json=event_payload(), headers=auth(seeded_org))
    assert response.status_code == 201
    body = response.json()
    assert body["duplicate"] is False
    assert body["context_summary_stored"] is False
    assert body["review_due_at"] is None

    contributor = db.scalars(select(Contributor)).one()
    assert contributor.provider == "github"
    assert contributor.external_id == "12345678"
    stored = db.scalars(select(CoachingEvent)).one()
    assert stored.category == "avoidance"
    assert stored.event_type == "observation"


def test_contributor_attributes_refresh_on_later_events(client: TestClient, seeded_org: SeededOrg, db: Session) -> None:
    assert client.post("/v1/events", json=event_payload(), headers=auth(seeded_org)).status_code == 201
    second = event_payload(
        event_id="SECOND",
        contributor={
            "provider": "github",
            "external_id": "12345678",
            "display_name": "octocat-renamed",
            "email": "octocat@example.com",
        },
    )
    assert client.post("/v1/events", json=second, headers=auth(seeded_org)).status_code == 201
    contributor = db.scalars(select(Contributor)).one()  # same identity, refreshed attributes
    assert contributor.display_name == "octocat-renamed"
    assert contributor.email == "octocat@example.com"


def test_replay_same_body_is_idempotent(client: TestClient, seeded_org: SeededOrg, db: Session) -> None:
    first = client.post("/v1/events", json=event_payload(), headers=auth(seeded_org))
    assert first.status_code == 201
    replay = client.post("/v1/events", json=event_payload(), headers=auth(seeded_org))
    assert replay.status_code == 200
    assert replay.json()["duplicate"] is True
    assert replay.json()["id"] == first.json()["id"]
    assert len(db.scalars(select(CoachingEvent)).all()) == 1


def test_same_event_id_different_body_conflicts(client: TestClient, seeded_org: SeededOrg) -> None:
    assert client.post("/v1/events", json=event_payload(), headers=auth(seeded_org)).status_code == 201
    response = client.post("/v1/events", json=event_payload(category="other"), headers=auth(seeded_org))
    assert response.status_code == 409


def test_organization_key_mismatch_rejected(client: TestClient, seeded_org: SeededOrg) -> None:
    response = client.post("/v1/events", json=event_payload(organization_key="ghost"), headers=auth(seeded_org))
    assert response.status_code == 400


def test_organization_key_match_accepted(client: TestClient, seeded_org: SeededOrg) -> None:
    response = client.post("/v1/events", json=event_payload(organization_key="acme"), headers=auth(seeded_org))
    assert response.status_code == 201


@pytest.mark.parametrize(
    "override",
    [
        {"occurred_at": "2026-07-02T10:00:00"},  # naive datetime
        {"category": "not-a-category"},
        {"signal": "Bad Signal!"},
        {"event_type": "quiz_attempt"},  # quiz payload missing
        {"quiz": {"outcome": "correct"}},  # quiz payload on an observation
        {"schema_version": 2},
        {"unknown_field": "x"},
    ],
)
def test_invalid_payloads_rejected(client: TestClient, seeded_org: SeededOrg, override: dict[str, Any]) -> None:
    response = client.post("/v1/events", json=event_payload(**override), headers=auth(seeded_org))
    assert response.status_code == 422


def test_context_summary_denied_by_default(client: TestClient, seeded_org: SeededOrg, db: Session) -> None:
    response = client.post(
        "/v1/events",
        json=event_payload(context_summary="abstracted moment"),
        headers=auth(seeded_org),
    )
    assert response.status_code == 201
    assert response.json()["context_summary_stored"] is False
    assert db.scalars(select(CoachingEvent)).one().context_summary is None


def test_context_summary_stored_when_policy_allows(
    client: TestClient, seeded_org: SeededOrg, session_factory: sessionmaker[Session], db: Session
) -> None:
    with session_factory() as session:
        policies.put_policy(session, seeded_org.organization.id, PolicySettings(allow_context_summary=True))
        session.commit()
    response = client.post(
        "/v1/events",
        json=event_payload(context_summary="abstracted moment"),
        headers=auth(seeded_org),
    )
    assert response.status_code == 201
    assert response.json()["context_summary_stored"] is True
    assert db.scalars(select(CoachingEvent)).one().context_summary == "abstracted moment"


def test_collection_disabled_by_policy(
    client: TestClient, seeded_org: SeededOrg, session_factory: sessionmaker[Session]
) -> None:
    with session_factory() as session:
        policies.put_policy(session, seeded_org.organization.id, PolicySettings(collect_enabled=False))
        session.commit()
    response = client.post("/v1/events", json=event_payload(), headers=auth(seeded_org))
    assert response.status_code == 403


def test_quiz_attempt_creates_attempt_and_schedule(client: TestClient, seeded_org: SeededOrg, db: Session) -> None:
    occurred = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)
    response = client.post(
        "/v1/events",
        json=event_payload(
            event_type="quiz_attempt",
            occurred_at=occurred.isoformat(),
            quiz={"outcome": "correct", "confidence": "high", "calibration": "accurate"},
        ),
        headers=auth(seeded_org),
    )
    assert response.status_code == 201
    body = response.json()
    attempt = db.scalars(select(QuizAttempt)).one()
    assert attempt.outcome == "correct"
    assert attempt.confidence == "high"
    assert attempt.calibration == "accurate"
    due_at = datetime.fromisoformat(body["review_due_at"])
    assert due_at - occurred == timedelta(days=2)


def test_quiz_outcomes_drive_spacing(client: TestClient, seeded_org: SeededOrg) -> None:
    occurred = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)

    def attempt(event_id: str, outcome: str, at: datetime) -> datetime:
        response = client.post(
            "/v1/events",
            json=event_payload(
                event_id=event_id,
                event_type="quiz_attempt",
                occurred_at=at.isoformat(),
                quiz={"outcome": outcome},
            ),
            headers=auth(seeded_org),
        )
        assert response.status_code == 201
        return datetime.fromisoformat(response.json()["review_due_at"])

    first = attempt("EV1", "correct", occurred)
    assert first - occurred == timedelta(days=2)
    second = attempt("EV2", "correct", occurred + timedelta(days=2))
    assert second - (occurred + timedelta(days=2)) == timedelta(days=4)
    third = attempt("EV3", "incorrect", occurred + timedelta(days=6))
    assert third - (occurred + timedelta(days=6)) == timedelta(days=1)


def test_client_policy_endpoint(client: TestClient, seeded_org: SeededOrg) -> None:
    response = client.get("/v1/client/policy", headers=auth(seeded_org))
    assert response.status_code == 200
    assert response.json() == {
        "organization_key": "acme",
        "settings": {"collect_enabled": True, "allow_context_summary": False, "retention_days": 365},
    }


def test_insert_race_returns_duplicate(
    client: TestClient, seeded_org: SeededOrg, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pre-check misses, the unique constraint fires, the raced row is replayed."""
    assert client.post("/v1/events", json=event_payload(), headers=auth(seeded_org)).status_code == 201

    real = ingestion_module._existing_event
    calls = {"n": 0}

    def flaky(*args: Any, **kwargs: Any) -> Any:
        calls["n"] += 1
        if calls["n"] == 1:
            return None  # simulate the losing side of a concurrent insert
        return real(*args, **kwargs)

    monkeypatch.setattr(ingestion_module, "_existing_event", flaky)
    response = client.post("/v1/events", json=event_payload(), headers=auth(seeded_org))
    assert response.status_code == 200
    assert response.json()["duplicate"] is True


def test_insert_race_reraises_when_row_vanishes(
    client: TestClient, seeded_org: SeededOrg, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert client.post("/v1/events", json=event_payload(), headers=auth(seeded_org)).status_code == 201
    monkeypatch.setattr(ingestion_module, "_existing_event", lambda *a, **k: None)
    with pytest.raises(IntegrityError):
        client.post("/v1/events", json=event_payload(), headers=auth(seeded_org))
