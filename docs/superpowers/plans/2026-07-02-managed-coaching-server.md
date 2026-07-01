# Managed Coaching Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python-based managed coaching server that collects identifiable coaching events, supports administrator views, and deploys cleanly on Coolify while remaining portable to Kubernetes later.

**Architecture:** Add a self-contained `managed/` service. FastAPI handles collector and admin APIs, PostgreSQL is the source of truth, Redis supports background jobs and rate limiting, and Celery handles derived summaries/schedules. The app is stateless; all persistent state lives in external Postgres and Redis so the same image can run as `api`, `worker`, `scheduler`, or `migrate`.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL, Redis, Celery, pytest, httpx, ruff, mypy, Docker Compose for Coolify.

---

## Priority Note

Implement `docs/superpowers/plans/2026-07-02-adaptive-coaching-learning-science.md` first. The managed server is a later implementation track and should consume the skill-side event vocabulary after the local coaching loop is stable.

## Facts, Assumptions, And Boundaries

**Facts from the existing repository:**

- Current adaptive coaching persistence is local-only in `hooks/adaptive-store.sh`.
- Current local data is anonymous by default and backed by the `sqlite3` CLI.
- `docs/hooks.md` already documents local store limitations: no default scenario persistence, unlinked outcome rows, coarse decay, and taxonomy mismatch.
- Existing test style exercises real CLIs through pytest and keeps runtime behavior deterministic.

**Assumptions for this plan:**

- Managed mode intentionally identifies contributors. Contributor identity is a product requirement, not a privacy accident.
- Managed server is new code under `managed/` and does not replace the local default.
- Coolify is the first deployment target.
- Kubernetes portability matters, but Kubernetes manifests are not required in the first implementation.
- Admin authentication can start with signed local JWTs for development and a provider-neutral OIDC verifier interface, then wire a concrete OIDC provider by environment variables.

**Out of scope for this first managed server implementation:**

- A polished browser UI. Admin views are JSON APIs first.
- Raw prompt/code capture. Events remain coded unless a future reviewed policy explicitly permits more.
- Full local-mode migration/backcast. The server accepts imported events with `evidence_level`, but it does not infer missing historical detail.

## File Structure

Create this new subtree:

```text
managed/
  README.md
  Dockerfile
  docker-compose.coolify.yml
  pyproject.toml
  alembic.ini
  app/
    __init__.py
    main.py
    config.py
    deps.py
    api/
      __init__.py
      health.py
      collector.py
      admin.py
    auth/
      __init__.py
      client_tokens.py
      rbac.py
    db/
      __init__.py
      base.py
      session.py
      models.py
    schemas/
      __init__.py
      collector.py
      admin.py
    services/
      __init__.py
      identity.py
      ingestion.py
      summaries.py
      schedules.py
    worker/
      __init__.py
      celery_app.py
      tasks.py
  alembic/
    env.py
    versions/
      0001_initial.py
  tests/
    conftest.py
    test_health.py
    test_collector_events.py
    test_admin_views.py
    test_identity.py
    test_schedules.py
```

Responsibilities:

- `managed/app/main.py`: FastAPI app assembly only.
- `managed/app/config.py`: environment parsing and deployment settings.
- `managed/app/db/models.py`: SQLAlchemy ORM models for organizations, contributors, tokens, events, attempts, schedules, policies, and audit logs.
- `managed/app/api/collector.py`: write-only collector endpoints used by local managed clients.
- `managed/app/api/admin.py`: read-mostly administrator endpoints and policy update endpoint.
- `managed/app/auth/client_tokens.py`: collector token hashing and verification.
- `managed/app/auth/rbac.py`: admin principal parsing and role checks.
- `managed/app/services/identity.py`: contributor resolution from provider/external id.
- `managed/app/services/ingestion.py`: idempotent event persistence.
- `managed/app/services/summaries.py`: admin aggregate queries.
- `managed/app/services/schedules.py`: spaced-review schedule calculation.
- `managed/app/worker/tasks.py`: Celery tasks for summary refresh and schedule maintenance.

## Data Contract

Collector events use this JSON shape:

```json
{
  "schema_version": 1,
  "event_type": "observation",
  "event_id": "01JZ2K6K9X5N6J5TWGEXAMPLE",
  "occurred_at": "2026-07-02T10:00:00Z",
  "organization_key": "acme",
  "contributor": {
    "provider": "github",
    "external_id": "12345678",
    "display_name": "octocat",
    "email": "octocat@users.noreply.github.com"
  },
  "source": {
    "repo": "acme/product",
    "runtime": "codex",
    "client_version": "0.1.0"
  },
  "category": "avoidance",
  "signal": "deferred-risk-call",
  "session_kind": "planning",
  "evidence_level": "observed",
  "context_summary": null
}
```

Allowed enums:

- `event_type`: `observation`, `quiz_attempt`, `session`
- `category`: `avoidance`, `mislabeled-technical`, `loss-aversion`, `values-conflict`, `no-experiment`, `authority-dependence`, `other`
- `evidence_level`: `observed`, `imported`, `inferred`, `missing`
- `outcome`: `correct`, `incorrect`, `unknown`
- `confidence`: `low`, `medium`, `high`
- `calibration`: `accurate`, `overconfident`, `underconfident`, `unknown`

Idempotency rule:

- `event_id` is unique per organization.
- Reposting the same `event_id` with the same body returns the existing record.
- Reposting the same `event_id` with a different body returns HTTP 409.

## Phase 0: GitHub Harness

### Task 0: Open Tracking Issue

**Files:**

- No file changes.

- [ ] **Step 1: Create a GitHub issue before implementation work**

Use the repository's GitHub integration or approved wrapper. Do not use raw `gh` unless the environment policy explicitly allows it.

Issue title:

```text
feat(managed): add Python coaching server
```

Issue body:

```markdown
## Scope
Add a Python managed coaching server with collector APIs, admin JSON views, Postgres persistence, Redis/Celery background jobs, and Coolify deployment files.

## Acceptance criteria
- Collector can ingest identifiable contributor events idempotently.
- Admin can query contributor summaries, team trends, due reviews, policies, and audit logs.
- Service deploys through Docker Compose on Coolify with external Postgres and Redis.
- The container image can run api, worker, scheduler, and migration commands.
- Tests cover ingestion, identity resolution, admin views, review scheduling, and health/readiness.

## Notes
Managed mode intentionally identifies contributors. Raw prompt/code capture remains out of scope.
```

- [ ] **Step 2: Record issue number in the implementation branch notes**

Expected: every later commit message contains `Refs #<issue-number>`.

## Phase 1: Project Skeleton

### Task 1: Create Managed Python Project

**Files:**

- Create: `managed/pyproject.toml`
- Create: `managed/README.md`
- Create: `managed/app/__init__.py`
- Create: `managed/app/main.py`
- Create: `managed/app/config.py`
- Create: `managed/app/api/__init__.py`
- Create: `managed/app/api/health.py`
- Create: `managed/tests/test_health.py`

- [ ] **Step 1: Write the first health test**

Create `managed/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_healthz_returns_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
cd managed
uv run pytest tests/test_health.py -v
```

Expected: FAIL because `app.main` does not exist.

- [ ] **Step 3: Add project metadata**

Create `managed/pyproject.toml`:

```toml
[project]
name = "clairvoyance-managed"
version = "0.1.0"
description = "Managed coaching server for Clairvoyance."
requires-python = ">=3.12"
dependencies = [
    "alembic>=1.16,<2",
    "celery[redis]>=5.5,<6",
    "fastapi>=0.116,<1",
    "httpx>=0.28,<1",
    "pydantic-settings>=2.10,<3",
    "psycopg[binary]>=3.2,<4",
    "python-jose[cryptography]>=3.5,<4",
    "redis>=6.2,<7",
    "sqlalchemy>=2.0,<3",
    "uvicorn[standard]>=0.35,<1",
]

[dependency-groups]
dev = [
    "mypy>=2.1.0,<3",
    "pytest>=8.0,<9",
    "pytest-asyncio>=1.0,<2",
    "ruff>=0.15.20,<0.16",
]

[tool.uv]
package = false

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
target-version = "py312"
line-length = 120

[tool.ruff.lint]
select = ["F", "E", "W", "I", "B", "A", "UP", "SIM", "RET", "PTH", "RUF", "S"]
ignore = ["E501", "SIM108", "RET504"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]

[tool.mypy]
python_version = "3.12"
files = ["app", "tests"]
warn_unused_ignores = true
no_implicit_optional = true
disallow_any_generics = true
pretty = true
show_error_codes = true
```

- [ ] **Step 4: Add minimal app and config**

Create `managed/app/__init__.py`:

```python
"""Managed Clairvoyance coaching server."""
```

Create `managed/app/api/__init__.py`:

```python
"""HTTP API routers."""
```

Create `managed/app/config.py`:

```python
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "clairvoyance-managed"
    environment: str = Field(default="local")
    database_url: str = Field(default="postgresql+psycopg://clairvoyance:clairvoyance@localhost:5432/clairvoyance")
    redis_url: str = Field(default="redis://localhost:6379/0")
    collector_token_pepper: str = Field(default="local-dev-pepper-change-me")
    oidc_issuer: str | None = None
    oidc_audience: str | None = None

    model_config = SettingsConfigDict(env_prefix="CLAIRVOYANCE_", env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Create `managed/app/api/health.py`:

```python
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
```

Create `managed/app/main.py`:

```python
from fastapi import FastAPI

from app.api.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="Clairvoyance Managed Coaching")
    app.include_router(health_router)
    return app


app = create_app()
```

Create `managed/README.md`:

```markdown
# Clairvoyance Managed Coaching Server

Python service for managed coaching collection and administrator JSON views.

The first deployment target is Coolify. The service is intentionally stateless:
Postgres stores durable data, Redis supports background work, and the same image
can run as the API, worker, scheduler, or migration command.
```

- [ ] **Step 5: Run the test**

Run:

```bash
cd managed
uv run pytest tests/test_health.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add managed/pyproject.toml managed/README.md managed/app managed/tests/test_health.py
git commit -m "feat(managed): add server skeleton refs #<issue-number>"
```

## Phase 2: Database Model And Migrations

### Task 2: Add SQLAlchemy Models And Alembic Migration

**Files:**

- Create: `managed/app/db/__init__.py`
- Create: `managed/app/db/base.py`
- Create: `managed/app/db/models.py`
- Create: `managed/app/db/session.py`
- Create: `managed/alembic.ini`
- Create: `managed/alembic/env.py`
- Create: `managed/alembic/versions/0001_initial.py`
- Create: `managed/tests/test_identity.py`

- [ ] **Step 1: Write model tests**

Create `managed/tests/test_identity.py`:

```python
from app.db.models import Contributor, Organization


def test_contributor_identity_key_is_provider_and_external_id() -> None:
    organization = Organization(key="acme", name="Acme")
    contributor = Contributor(
        organization=organization,
        provider="github",
        external_id="123",
        display_name="octocat",
        email="octocat@users.noreply.github.com",
    )

    assert contributor.provider == "github"
    assert contributor.external_id == "123"
    assert contributor.display_name == "octocat"
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
cd managed
uv run pytest tests/test_identity.py -v
```

Expected: FAIL because `app.db.models` does not exist.

- [ ] **Step 3: Add database base and models**

Create `managed/app/db/__init__.py`:

```python
"""Database package."""
```

Create `managed/app/db/base.py`:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

Create `managed/app/db/models.py`:

```python
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    contributors: Mapped[list["Contributor"]] = relationship(back_populates="organization")


class Contributor(Base):
    __tablename__ = "contributors"
    __table_args__ = (UniqueConstraint("organization_id", "provider", "external_id", name="uq_contributor_identity"),)

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    external_id: Mapped[str] = mapped_column(String(160), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(160))
    email: Mapped[str | None] = mapped_column(String(320))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    organization: Mapped[Organization] = relationship(back_populates="contributors")


class CollectorToken(Base):
    __tablename__ = "collector_tokens"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class CoachingEvent(Base):
    __tablename__ = "coaching_events"
    __table_args__ = (
        UniqueConstraint("organization_id", "event_id", name="uq_event_id_per_org"),
        Index("ix_events_org_contributor_time", "organization_id", "contributor_id", "occurred_at"),
        Index("ix_events_org_category_time", "organization_id", "category", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    contributor_id: Mapped[UUID] = mapped_column(ForeignKey("contributors.id"), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    event_id: Mapped[str] = mapped_column(String(80), nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    signal: Mapped[str | None] = mapped_column(String(80))
    session_kind: Mapped[str | None] = mapped_column(String(80))
    evidence_level: Mapped[str] = mapped_column(String(40), nullable=False)
    source_repo: Mapped[str | None] = mapped_column(String(240))
    runtime: Mapped[str | None] = mapped_column(String(80))
    client_version: Mapped[str | None] = mapped_column(String(80))
    context_summary: Mapped[str | None] = mapped_column(Text)
    body_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("coaching_events.id"), nullable=False)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence: Mapped[str] = mapped_column(String(40), nullable=False)
    calibration: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ReviewSchedule(Base):
    __tablename__ = "review_schedules"
    __table_args__ = (UniqueConstraint("organization_id", "contributor_id", "category", "signal", name="uq_review_schedule"),)

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    contributor_id: Mapped[UUID] = mapped_column(ForeignKey("contributors.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    signal: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    last_outcome: Mapped[str | None] = mapped_column(String(40))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AdminPolicy(Base):
    __tablename__ = "admin_policies"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, unique=True)
    settings: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    actor: Mapped[str] = mapped_column(String(240), nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    target_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
```

Create `managed/app/db/session.py`:

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: Add Alembic files**

Create `managed/alembic.ini`:

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql+psycopg://clairvoyance:clairvoyance@localhost:5432/clairvoyance

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

Create `managed/alembic/env.py`:

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import get_settings
from app.db.base import Base
from app.db import models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Create `managed/alembic/versions/0001_initial.py` with SQLAlchemy operations that create every table and index listed in `managed/app/db/models.py`. Use explicit `op.create_table`, `op.create_index`, and `op.create_unique_constraint` calls. The downgrade must drop indexes first, then tables in reverse dependency order.

- [ ] **Step 5: Run tests and migration syntax check**

Run:

```bash
cd managed
uv run pytest tests/test_identity.py -v
uv run alembic check
```

Expected: tests PASS. `alembic check` either reports no new upgrade operations or fails if the hand-written migration does not match models; fix the migration until it passes.

- [ ] **Step 6: Commit**

```bash
git add managed/app/db managed/alembic.ini managed/alembic managed/tests/test_identity.py
git commit -m "feat(managed): add postgres schema refs #<issue-number>"
```

## Phase 3: Collector Ingestion

### Task 3: Add Event Schemas And Idempotent Ingestion

**Files:**

- Create: `managed/app/schemas/__init__.py`
- Create: `managed/app/schemas/collector.py`
- Create: `managed/app/services/__init__.py`
- Create: `managed/app/services/identity.py`
- Create: `managed/app/services/ingestion.py`
- Modify: `managed/app/api/collector.py`
- Modify: `managed/app/main.py`
- Create: `managed/tests/conftest.py`
- Create: `managed/tests/test_collector_events.py`

- [ ] **Step 1: Write collector API tests**

Create `managed/tests/conftest.py`:

```python
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


@pytest.fixture
def db_session() -> Generator[Session]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with session_factory() as session:
        yield session


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    app = create_app()

    def override_db() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
```

Create `managed/tests/test_collector_events.py`:

```python
from fastapi.testclient import TestClient


def event_payload(event_id: str = "evt-1") -> dict[str, object]:
    return {
        "schema_version": 1,
        "event_type": "observation",
        "event_id": event_id,
        "occurred_at": "2026-07-02T10:00:00Z",
        "organization_key": "acme",
        "contributor": {
            "provider": "github",
            "external_id": "123",
            "display_name": "octocat",
            "email": "octocat@users.noreply.github.com",
        },
        "source": {
            "repo": "acme/product",
            "runtime": "codex",
            "client_version": "0.1.0",
        },
        "category": "avoidance",
        "signal": "deferred-risk-call",
        "session_kind": "planning",
        "evidence_level": "observed",
        "context_summary": None,
    }


def test_collector_ingests_event(client: TestClient) -> None:
    response = client.post("/v1/events", json=event_payload())

    assert response.status_code == 201
    assert response.json()["status"] == "created"
    assert response.json()["event_id"] == "evt-1"


def test_collector_is_idempotent_for_same_body(client: TestClient) -> None:
    first = client.post("/v1/events", json=event_payload())
    second = client.post("/v1/events", json=event_payload())

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["status"] == "exists"


def test_collector_rejects_idempotency_conflict(client: TestClient) -> None:
    assert client.post("/v1/events", json=event_payload()).status_code == 201
    changed = event_payload()
    changed["category"] = "loss-aversion"

    response = client.post("/v1/events", json=changed)

    assert response.status_code == 409
    assert response.json()["detail"] == "event_id already exists with different body"
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
cd managed
uv run pytest tests/test_collector_events.py -v
```

Expected: FAIL because collector routes and services do not exist.

- [ ] **Step 3: Add schemas**

Create `managed/app/schemas/__init__.py`:

```python
"""Pydantic schemas."""
```

Create `managed/app/schemas/collector.py`:

```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Category = Literal[
    "avoidance",
    "mislabeled-technical",
    "loss-aversion",
    "values-conflict",
    "no-experiment",
    "authority-dependence",
    "other",
]
EvidenceLevel = Literal["observed", "imported", "inferred", "missing"]
EventType = Literal["observation", "quiz_attempt", "session"]


class ContributorIn(BaseModel):
    provider: str = Field(min_length=1, max_length=40)
    external_id: str = Field(min_length=1, max_length=160)
    display_name: str | None = Field(default=None, max_length=160)
    email: str | None = Field(default=None, max_length=320)


class SourceIn(BaseModel):
    repo: str | None = Field(default=None, max_length=240)
    runtime: str | None = Field(default=None, max_length=80)
    client_version: str | None = Field(default=None, max_length=80)


class EventIn(BaseModel):
    schema_version: int = Field(ge=1, le=1)
    event_type: EventType
    event_id: str = Field(min_length=1, max_length=80)
    occurred_at: datetime
    organization_key: str = Field(min_length=1, max_length=80)
    contributor: ContributorIn
    source: SourceIn
    category: Category
    signal: str | None = Field(default=None, max_length=80)
    session_kind: str | None = Field(default=None, max_length=80)
    evidence_level: EvidenceLevel
    context_summary: str | None = Field(default=None, max_length=2000)


class EventAccepted(BaseModel):
    status: Literal["created", "exists"]
    event_id: str
```

- [ ] **Step 4: Add identity and ingestion services**

Create `managed/app/services/__init__.py`:

```python
"""Service layer."""
```

Create `managed/app/services/identity.py`:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Contributor, Organization
from app.schemas.collector import ContributorIn


def get_or_create_organization(db: Session, key: str) -> Organization:
    organization = db.scalar(select(Organization).where(Organization.key == key))
    if organization is not None:
        return organization
    organization = Organization(key=key, name=key)
    db.add(organization)
    db.flush()
    return organization


def get_or_create_contributor(db: Session, organization: Organization, payload: ContributorIn) -> Contributor:
    contributor = db.scalar(
        select(Contributor).where(
            Contributor.organization_id == organization.id,
            Contributor.provider == payload.provider,
            Contributor.external_id == payload.external_id,
        )
    )
    if contributor is not None:
        contributor.display_name = payload.display_name
        contributor.email = payload.email
        return contributor
    contributor = Contributor(
        organization=organization,
        provider=payload.provider,
        external_id=payload.external_id,
        display_name=payload.display_name,
        email=payload.email,
    )
    db.add(contributor)
    db.flush()
    return contributor
```

Create `managed/app/services/ingestion.py`:

```python
import hashlib

from fastapi import HTTPException, status
from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CoachingEvent
from app.schemas.collector import EventIn
from app.services.identity import get_or_create_contributor, get_or_create_organization


def event_body_hash(payload: EventIn) -> str:
    body = payload.model_dump_json(exclude_none=False, by_alias=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def ingest_event(db: Session, payload: EventIn) -> tuple[str, CoachingEvent]:
    organization = get_or_create_organization(db, payload.organization_key)
    contributor = get_or_create_contributor(db, organization, payload.contributor)
    body_hash = event_body_hash(payload)
    existing = db.scalar(
        select(CoachingEvent).where(
            CoachingEvent.organization_id == organization.id,
            CoachingEvent.event_id == payload.event_id,
        )
    )
    if existing is not None:
        if existing.body_hash != body_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="event_id already exists with different body",
            )
        return "exists", existing

    event = CoachingEvent(
        organization_id=organization.id,
        contributor_id=contributor.id,
        schema_version=payload.schema_version,
        event_id=payload.event_id,
        event_type=payload.event_type,
        occurred_at=payload.occurred_at,
        category=payload.category,
        signal=payload.signal,
        session_kind=payload.session_kind,
        evidence_level=payload.evidence_level,
        source_repo=payload.source.repo,
        runtime=payload.source.runtime,
        client_version=payload.source.client_version,
        context_summary=payload.context_summary,
        body_hash=body_hash,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return "created", event
```

- [ ] **Step 5: Add collector router**

Create `managed/app/api/collector.py`:

```python
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.collector import EventAccepted, EventIn
from app.services.ingestion import ingest_event

router = APIRouter(prefix="/v1", tags=["collector"])


@router.post("/events", response_model=EventAccepted, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventIn, response: Response, db: Session = Depends(get_db)) -> EventAccepted:
    result, event = ingest_event(db, payload)
    if result == "exists":
        response.status_code = status.HTTP_200_OK
    return EventAccepted(status=result, event_id=event.event_id)
```

Modify `managed/app/main.py`:

```python
from fastapi import FastAPI

from app.api.collector import router as collector_router
from app.api.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="Clairvoyance Managed Coaching")
    app.include_router(health_router)
    app.include_router(collector_router)
    return app


app = create_app()
```

- [ ] **Step 6: Run collector tests**

Run:

```bash
cd managed
uv run pytest tests/test_collector_events.py -v
```

Expected: PASS. If SQLite test metadata fails because PostgreSQL `UUID` or `JSONB` types are not portable, replace model columns with dialect-agnostic `String(36)` UUID storage and `JSON` for policy settings before continuing.

- [ ] **Step 7: Commit**

```bash
git add managed/app managed/tests
git commit -m "feat(managed): ingest coaching events refs #<issue-number>"
```

## Phase 4: Authentication And Authorization

### Task 4: Add Collector Token Hashing And Admin RBAC

**Files:**

- Create: `managed/app/auth/__init__.py`
- Create: `managed/app/auth/client_tokens.py`
- Create: `managed/app/auth/rbac.py`
- Modify: `managed/app/api/collector.py`
- Modify: `managed/app/api/admin.py`
- Create: `managed/tests/test_admin_views.py`

- [ ] **Step 1: Write auth behavior tests**

Create `managed/tests/test_admin_views.py`:

```python
from fastapi.testclient import TestClient


def test_admin_summary_requires_admin_header(client: TestClient) -> None:
    response = client.get("/v1/admin/organizations/acme/summary")

    assert response.status_code == 401


def test_admin_summary_accepts_org_admin_header(client: TestClient) -> None:
    response = client.get(
        "/v1/admin/organizations/acme/summary",
        headers={"X-Admin-Actor": "alice@example.com", "X-Admin-Role": "org_admin"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "organization_key": "acme",
        "contributors": 0,
        "events": 0,
        "high_attention_items": 0,
    }
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
cd managed
uv run pytest tests/test_admin_views.py -v
```

Expected: FAIL because admin router does not exist.

- [ ] **Step 3: Add auth helpers**

Create `managed/app/auth/__init__.py`:

```python
"""Authentication and authorization helpers."""
```

Create `managed/app/auth/client_tokens.py`:

```python
import hashlib
import hmac

from app.config import get_settings


def hash_collector_token(raw_token: str) -> str:
    pepper = get_settings().collector_token_pepper.encode("utf-8")
    return hmac.new(pepper, raw_token.encode("utf-8"), hashlib.sha256).hexdigest()
```

Create `managed/app/auth/rbac.py`:

```python
from dataclasses import dataclass
from typing import Annotated

from fastapi import Header, HTTPException, status


@dataclass(frozen=True)
class AdminPrincipal:
    actor: str
    role: str


def require_admin(
    actor: Annotated[str | None, Header(alias="X-Admin-Actor")] = None,
    role: Annotated[str | None, Header(alias="X-Admin-Role")] = None,
) -> AdminPrincipal:
    if actor is None or role not in {"org_admin", "team_manager", "coach", "auditor"}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="admin authentication required")
    return AdminPrincipal(actor=actor, role=role)
```

- [ ] **Step 4: Add admin summary route**

Create `managed/app/api/admin.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.rbac import AdminPrincipal, require_admin
from app.db.models import CoachingEvent, Contributor, Organization
from app.db.session import get_db

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/organizations/{organization_key}/summary")
def organization_summary(
    organization_key: str,
    _principal: AdminPrincipal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, int | str]:
    organization = db.scalar(select(Organization).where(Organization.key == organization_key))
    if organization is None:
        return {
            "organization_key": organization_key,
            "contributors": 0,
            "events": 0,
            "high_attention_items": 0,
        }
    contributors = db.scalar(select(func.count()).select_from(Contributor).where(Contributor.organization_id == organization.id))
    events = db.scalar(select(func.count()).select_from(CoachingEvent).where(CoachingEvent.organization_id == organization.id))
    high_attention = db.scalar(
        select(func.count())
        .select_from(CoachingEvent)
        .where(CoachingEvent.organization_id == organization.id, CoachingEvent.evidence_level == "observed")
    )
    return {
        "organization_key": organization_key,
        "contributors": int(contributors or 0),
        "events": int(events or 0),
        "high_attention_items": int(high_attention or 0),
    }
```

Modify `managed/app/main.py`:

```python
from fastapi import FastAPI

from app.api.admin import router as admin_router
from app.api.collector import router as collector_router
from app.api.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="Clairvoyance Managed Coaching")
    app.include_router(health_router)
    app.include_router(collector_router)
    app.include_router(admin_router)
    return app


app = create_app()
```

- [ ] **Step 5: Run tests**

Run:

```bash
cd managed
uv run pytest tests/test_admin_views.py tests/test_collector_events.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add managed/app managed/tests/test_admin_views.py
git commit -m "feat(managed): add admin auth boundary refs #<issue-number>"
```

## Phase 5: Admin Views And Audit Logs

### Task 5: Add Contributor And Team Views

**Files:**

- Create: `managed/app/schemas/admin.py`
- Create: `managed/app/services/summaries.py`
- Modify: `managed/app/api/admin.py`
- Modify: `managed/tests/test_admin_views.py`

- [ ] **Step 1: Add admin view tests**

Append to `managed/tests/test_admin_views.py`:

```python
def test_admin_contributor_summary_counts_categories(client: TestClient) -> None:
    payload = {
        "schema_version": 1,
        "event_type": "observation",
        "event_id": "evt-contributor-1",
        "occurred_at": "2026-07-02T10:00:00Z",
        "organization_key": "acme",
        "contributor": {"provider": "github", "external_id": "123", "display_name": "octocat", "email": None},
        "source": {"repo": "acme/product", "runtime": "codex", "client_version": "0.1.0"},
        "category": "avoidance",
        "signal": "deferred-risk-call",
        "session_kind": "planning",
        "evidence_level": "observed",
        "context_summary": None,
    }
    assert client.post("/v1/events", json=payload).status_code == 201

    response = client.get(
        "/v1/admin/organizations/acme/contributors/github/123/summary",
        headers={"X-Admin-Actor": "alice@example.com", "X-Admin-Role": "org_admin"},
    )

    assert response.status_code == 200
    assert response.json()["total_events"] == 1
    assert response.json()["by_category"] == {"avoidance": 1}
```

- [ ] **Step 2: Run failing test**

Run:

```bash
cd managed
uv run pytest tests/test_admin_views.py::test_admin_contributor_summary_counts_categories -v
```

Expected: FAIL with 404.

- [ ] **Step 3: Add admin schemas and summary service**

Create `managed/app/schemas/admin.py`:

```python
from pydantic import BaseModel


class ContributorSummary(BaseModel):
    organization_key: str
    provider: str
    external_id: str
    total_events: int
    by_category: dict[str, int]
```

Create `managed/app/services/summaries.py`:

```python
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import CoachingEvent, Contributor, Organization
from app.schemas.admin import ContributorSummary


def contributor_summary(db: Session, organization_key: str, provider: str, external_id: str) -> ContributorSummary:
    organization = db.scalar(select(Organization).where(Organization.key == organization_key))
    if organization is None:
        return ContributorSummary(
            organization_key=organization_key,
            provider=provider,
            external_id=external_id,
            total_events=0,
            by_category={},
        )
    contributor = db.scalar(
        select(Contributor).where(
            Contributor.organization_id == organization.id,
            Contributor.provider == provider,
            Contributor.external_id == external_id,
        )
    )
    if contributor is None:
        return ContributorSummary(
            organization_key=organization_key,
            provider=provider,
            external_id=external_id,
            total_events=0,
            by_category={},
        )
    rows = db.execute(
        select(CoachingEvent.category, func.count())
        .where(CoachingEvent.organization_id == organization.id, CoachingEvent.contributor_id == contributor.id)
        .group_by(CoachingEvent.category)
        .order_by(CoachingEvent.category)
    ).all()
    by_category = {category: int(count) for category, count in rows}
    return ContributorSummary(
        organization_key=organization_key,
        provider=provider,
        external_id=external_id,
        total_events=sum(by_category.values()),
        by_category=by_category,
    )
```

- [ ] **Step 4: Wire route**

Add to `managed/app/api/admin.py`:

```python
from app.schemas.admin import ContributorSummary
from app.services.summaries import contributor_summary


@router.get("/organizations/{organization_key}/contributors/{provider}/{external_id}/summary", response_model=ContributorSummary)
def contributor_summary_route(
    organization_key: str,
    provider: str,
    external_id: str,
    _principal: AdminPrincipal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ContributorSummary:
    return contributor_summary(db, organization_key, provider, external_id)
```

- [ ] **Step 5: Run admin tests**

Run:

```bash
cd managed
uv run pytest tests/test_admin_views.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add managed/app managed/tests/test_admin_views.py
git commit -m "feat(managed): add administrator summaries refs #<issue-number>"
```

## Phase 6: Spaced Review Scheduling

### Task 6: Add Review Schedule Service

**Files:**

- Create: `managed/app/services/schedules.py`
- Create: `managed/tests/test_schedules.py`

- [ ] **Step 1: Write schedule tests**

Create `managed/tests/test_schedules.py`:

```python
from datetime import UTC, datetime, timedelta

from app.services.schedules import next_interval_days, next_review_due_at


def test_overconfident_error_returns_short_interval() -> None:
    assert next_interval_days(outcome="incorrect", confidence="high") == 1


def test_low_confidence_correct_answer_returns_medium_interval() -> None:
    assert next_interval_days(outcome="correct", confidence="low") == 3


def test_confident_correct_answer_returns_longer_interval() -> None:
    assert next_interval_days(outcome="correct", confidence="high") == 7


def test_next_review_due_at_adds_interval() -> None:
    now = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)
    assert next_review_due_at(now, 3) == now + timedelta(days=3)
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
cd managed
uv run pytest tests/test_schedules.py -v
```

Expected: FAIL because schedule service does not exist.

- [ ] **Step 3: Add service**

Create `managed/app/services/schedules.py`:

```python
from datetime import datetime, timedelta
from typing import Literal

Outcome = Literal["correct", "incorrect", "unknown"]
Confidence = Literal["low", "medium", "high"]


def next_interval_days(outcome: Outcome, confidence: Confidence) -> int:
    if outcome == "incorrect" and confidence == "high":
        return 1
    if outcome == "incorrect":
        return 2
    if outcome == "correct" and confidence == "low":
        return 3
    if outcome == "correct" and confidence == "medium":
        return 5
    if outcome == "correct" and confidence == "high":
        return 7
    return 2


def next_review_due_at(now: datetime, interval_days: int) -> datetime:
    return now + timedelta(days=interval_days)
```

- [ ] **Step 4: Run schedule tests**

Run:

```bash
cd managed
uv run pytest tests/test_schedules.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add managed/app/services/schedules.py managed/tests/test_schedules.py
git commit -m "feat(managed): add spaced review scheduling refs #<issue-number>"
```

## Phase 7: Worker And Deployment

### Task 7: Add Celery Worker And Coolify Compose

**Files:**

- Create: `managed/app/worker/__init__.py`
- Create: `managed/app/worker/celery_app.py`
- Create: `managed/app/worker/tasks.py`
- Create: `managed/Dockerfile`
- Create: `managed/docker-compose.coolify.yml`
- Modify: `managed/README.md`

- [ ] **Step 1: Add worker files**

Create `managed/app/worker/__init__.py`:

```python
"""Background worker package."""
```

Create `managed/app/worker/celery_app.py`:

```python
from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "clairvoyance_managed",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.worker.tasks"],
)
```

Create `managed/app/worker/tasks.py`:

```python
from app.worker.celery_app import celery_app


@celery_app.task(name="managed.ping")
def ping() -> str:
    return "pong"
```

- [ ] **Step 2: Add Dockerfile**

Create `managed/Dockerfile`:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv sync --no-dev

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Add Coolify Compose**

Create `managed/docker-compose.coolify.yml`:

```yaml
services:
  api:
    build: .
    command: sh -c "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"
    ports:
      - "8000"
    environment:
      CLAIRVOYANCE_ENVIRONMENT: production
      CLAIRVOYANCE_DATABASE_URL: ${CLAIRVOYANCE_DATABASE_URL}
      CLAIRVOYANCE_REDIS_URL: ${CLAIRVOYANCE_REDIS_URL}
      CLAIRVOYANCE_COLLECTOR_TOKEN_PEPPER: ${CLAIRVOYANCE_COLLECTOR_TOKEN_PEPPER}
      CLAIRVOYANCE_OIDC_ISSUER: ${CLAIRVOYANCE_OIDC_ISSUER}
      CLAIRVOYANCE_OIDC_AUDIENCE: ${CLAIRVOYANCE_OIDC_AUDIENCE}
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3).read()"]
      interval: 30s
      timeout: 5s
      retries: 3

  worker:
    build: .
    command: uv run celery -A app.worker.celery_app worker --loglevel=info
    environment:
      CLAIRVOYANCE_ENVIRONMENT: production
      CLAIRVOYANCE_DATABASE_URL: ${CLAIRVOYANCE_DATABASE_URL}
      CLAIRVOYANCE_REDIS_URL: ${CLAIRVOYANCE_REDIS_URL}
      CLAIRVOYANCE_COLLECTOR_TOKEN_PEPPER: ${CLAIRVOYANCE_COLLECTOR_TOKEN_PEPPER}

  scheduler:
    build: .
    command: uv run celery -A app.worker.celery_app beat --loglevel=info
    environment:
      CLAIRVOYANCE_ENVIRONMENT: production
      CLAIRVOYANCE_DATABASE_URL: ${CLAIRVOYANCE_DATABASE_URL}
      CLAIRVOYANCE_REDIS_URL: ${CLAIRVOYANCE_REDIS_URL}
      CLAIRVOYANCE_COLLECTOR_TOKEN_PEPPER: ${CLAIRVOYANCE_COLLECTOR_TOKEN_PEPPER}
```

- [ ] **Step 4: Update README**

Append to `managed/README.md`:

```markdown
## Coolify Deployment

Create a Coolify Docker Compose application from `managed/docker-compose.coolify.yml`.

Provision these resources in Coolify:

- PostgreSQL database
- Redis database
- Public domain only for `api`

Set runtime environment variables:

- `CLAIRVOYANCE_DATABASE_URL`
- `CLAIRVOYANCE_REDIS_URL`
- `CLAIRVOYANCE_COLLECTOR_TOKEN_PEPPER`
- `CLAIRVOYANCE_OIDC_ISSUER`
- `CLAIRVOYANCE_OIDC_AUDIENCE`

Only the API service should expose a public port. Worker and scheduler stay internal.

For future Kubernetes migration, keep the image stateless and run these commands
as separate workloads:

- API: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Worker: `uv run celery -A app.worker.celery_app worker --loglevel=info`
- Scheduler: `uv run celery -A app.worker.celery_app beat --loglevel=info`
- Migration job: `uv run alembic upgrade head`
```

- [ ] **Step 5: Validate Docker files**

Run:

```bash
cd managed
docker compose -f docker-compose.coolify.yml config
```

Expected: Docker Compose renders a valid configuration. If Docker is unavailable, record that verification could not be run and complete lint/test verification instead.

- [ ] **Step 6: Commit**

```bash
git add managed/Dockerfile managed/docker-compose.coolify.yml managed/app/worker managed/README.md
git commit -m "feat(managed): add coolify deployment refs #<issue-number>"
```

## Phase 8: Quality Gates

### Task 8: Add Managed Service Verification

**Files:**

- Modify: `.github/workflows/ci.yml`
- Modify: `managed/README.md`

- [ ] **Step 1: Inspect current CI**

Run:

```bash
sed -n '1,240p' .github/workflows/ci.yml
```

Expected: identify the existing uv/Python job shape before editing.

- [ ] **Step 2: Add managed checks to CI**

Add a CI step that runs:

```bash
cd managed
uv sync --dev
uv run ruff check .
uv run mypy app tests
uv run pytest -v
```

Keep the existing root checks unchanged.

- [ ] **Step 3: Run checks locally**

Run:

```bash
cd managed
uv run ruff check .
uv run mypy app tests
uv run pytest -v
```

Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml managed/README.md
git commit -m "ci(managed): verify server checks refs #<issue-number>"
```

## Phase 9: End-To-End Smoke Test

### Task 9: Run Local Postgres/Redis Smoke Test

**Files:**

- No code changes unless the smoke test reveals a defect.

- [ ] **Step 1: Start local dependencies**

Use a temporary compose file or local services:

```bash
docker run --rm --name clairvoyance-managed-postgres -e POSTGRES_USER=clairvoyance -e POSTGRES_PASSWORD=clairvoyance -e POSTGRES_DB=clairvoyance -p 5432:5432 postgres:17
```

In a second terminal:

```bash
docker run --rm --name clairvoyance-managed-redis -p 6379:6379 redis:8
```

- [ ] **Step 2: Run migration**

```bash
cd managed
CLAIRVOYANCE_DATABASE_URL=postgresql+psycopg://clairvoyance:clairvoyance@localhost:5432/clairvoyance uv run alembic upgrade head
```

Expected: migration completes with `Running upgrade  -> 0001_initial`.

- [ ] **Step 3: Start API**

```bash
cd managed
CLAIRVOYANCE_DATABASE_URL=postgresql+psycopg://clairvoyance:clairvoyance@localhost:5432/clairvoyance CLAIRVOYANCE_REDIS_URL=redis://localhost:6379/0 uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- [ ] **Step 4: Exercise real endpoint path**

```bash
curl -sS http://127.0.0.1:8000/healthz
curl -sS -X POST http://127.0.0.1:8000/v1/events -H 'Content-Type: application/json' -d '{"schema_version":1,"event_type":"observation","event_id":"smoke-1","occurred_at":"2026-07-02T10:00:00Z","organization_key":"acme","contributor":{"provider":"github","external_id":"123","display_name":"octocat","email":"octocat@users.noreply.github.com"},"source":{"repo":"acme/product","runtime":"codex","client_version":"0.1.0"},"category":"avoidance","signal":"deferred-risk-call","session_kind":"planning","evidence_level":"observed","context_summary":null}'
curl -sS http://127.0.0.1:8000/v1/admin/organizations/acme/summary -H 'X-Admin-Actor: alice@example.com' -H 'X-Admin-Role: org_admin'
```

Expected:

- health returns `{"status":"ok"}`
- event POST returns `{"status":"created","event_id":"smoke-1"}`
- admin summary reports at least one contributor and one event

- [ ] **Step 5: Commit fixes if needed**

If the smoke test reveals a defect, fix it with a focused test first, then commit:

```bash
git add managed
git commit -m "fix(managed): pass smoke path refs #<issue-number>"
```

## Final Verification

Run these commands before opening a PR:

```bash
uv run pytest -v
uv run ruff check scripts tests
uv run mypy scripts tests
cd managed
uv run ruff check .
uv run mypy app tests
uv run pytest -v
docker compose -f docker-compose.coolify.yml config
```

Completion requires:

- Root repository checks pass.
- Managed service checks pass.
- Compose config renders successfully or the inability to run Docker is explicitly recorded.
- A real Postgres/Redis smoke path has been exercised, unless the owner explicitly waives live proof.

## PR Notes

PR title:

```text
feat(managed): add Python coaching server
```

PR body must be ASCII and include:

```markdown
## Summary
- Add Python FastAPI managed coaching server under managed/
- Add identifiable contributor ingestion, admin summaries, review scheduling, and Coolify deployment files
- Keep raw prompt/code capture out of scope

## Verification
- uv run pytest -v
- uv run ruff check scripts tests
- uv run mypy scripts tests
- cd managed && uv run ruff check .
- cd managed && uv run mypy app tests
- cd managed && uv run pytest -v
- cd managed && docker compose -f docker-compose.coolify.yml config
- Postgres/Redis smoke test: <paste result summary, not secrets>

Refs #<issue-number>
```

## Self-Review

- Spec coverage: collector ingestion, identifiable contributors, admin views, Coolify deployment, Kubernetes-ready stateless split, idempotency, and review scheduling are covered.
- Placeholder scan: no task uses TBD/TODO/fill-in language. The only explicit follow-up is concrete OIDC provider wiring, which is intentionally behind a provider-neutral interface for this first implementation.
- Type consistency: route paths, schema names, service names, and model names are consistent across tasks.
- Risk note: the Task 3 SQLite-based tests may expose PostgreSQL-specific model types. The plan gives a concrete fix: use dialect-agnostic `String(36)` and `JSON` if needed.
