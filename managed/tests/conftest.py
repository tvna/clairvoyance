"""Shared fixtures: in-memory SQLite app, seeded org + collector token.

Environment defaults are set before any app import because the Celery module
builds its app (and therefore Settings) at import time.
"""

import os

os.environ.setdefault("CLAIRVOYANCE_DATABASE_URL", "sqlite://")
os.environ.setdefault("CLAIRVOYANCE_REDIS_URL", "redis://127.0.0.1:6399/0")

from collections.abc import Iterator
from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.client_tokens import generate_token, hash_token
from app.auth.rbac import AdminPrincipal, Role
from app.config import Settings
from app.db.base import Base
from app.db.models import CollectorToken, Organization
from app.deps import get_admin_principal
from app.main import create_app

TEST_PEPPER = "unit-test-pepper"


class FakeRedis:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    def ping(self) -> bool:
        if self.fail:
            raise ConnectionError("redis down")
        return True


@dataclass
class SeededOrg:
    organization: Organization
    raw_token: str


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "database_url": "sqlite://",
        "redis_url": "redis://127.0.0.1:6399/0",
        "collector_token_pepper": TEST_PEPPER,
    }
    values.update(overrides)
    return Settings.model_validate(values)


@pytest.fixture
def engine() -> Iterator[Engine]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_fks(dbapi_connection: object, _record: object) -> None:
        # SQLite ships with FK enforcement off; the prod schema relies on
        # ON DELETE CASCADE, so tests must exercise it too.
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def db(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    with session_factory() as session:
        yield session


@pytest.fixture
def app(engine: Engine, session_factory: sessionmaker[Session]) -> FastAPI:
    application = create_app(make_settings())
    application.state.engine = engine
    application.state.session_factory = session_factory
    application.state.redis = FakeRedis()
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture
def seeded_org(session_factory: sessionmaker[Session]) -> SeededOrg:
    raw = generate_token()
    with session_factory() as session:
        organization = Organization(key="acme", name="Acme")
        session.add(organization)
        session.flush()
        session.add(
            CollectorToken(
                organization_id=organization.id,
                name="ci-token",
                token_hash=hash_token(TEST_PEPPER, raw),
            )
        )
        session.commit()
        return SeededOrg(organization=organization, raw_token=raw)


def admin_override(app: FastAPI, *, org_key: str = "acme", roles: tuple[Role, ...] = (Role.ORG_ADMIN,)) -> None:
    principal = AdminPrincipal(subject="admin@example.com", organization_key=org_key, roles=frozenset(roles))
    app.dependency_overrides[get_admin_principal] = lambda: principal
