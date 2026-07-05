"""Probe endpoints: liveness always up, readiness reflects DB and Redis."""

from conftest import FakeRedis
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine


def test_healthz_and_livez(client: TestClient) -> None:
    for path in ("/healthz", "/livez"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_readyz_ok(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"ready": True, "checks": {"database": "ok", "redis": "ok"}}


def test_readyz_reports_redis_failure(app: FastAPI, client: TestClient) -> None:
    app.state.redis = FakeRedis(fail=True)
    response = client.get("/readyz")
    assert response.status_code == 503
    body = response.json()
    assert body["ready"] is False
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["redis"].startswith("error:")


def test_readyz_reports_database_failure(app: FastAPI, client: TestClient) -> None:
    app.state.engine = create_engine("sqlite:///nonexistent-dir/broken.db")
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json()["checks"]["database"].startswith("error:")
