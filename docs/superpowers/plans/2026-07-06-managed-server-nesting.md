# Managed Server Nesting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the managed server project from `managed/` root into `managed/server/` so it mirrors the existing `managed/ui/` project boundary.

**Architecture:** `managed/server/` becomes the uv project root and Docker build context for the FastAPI API, worker, scheduler, migrations, and server tests. `managed/` remains the product-level folder that owns shared compose files, dev fixtures, docs, and the separate `ui/` project.

**Tech Stack:** Python, uv, FastAPI, Alembic, Celery, Docker Compose, GitHub Actions.

---

### Task 1: Move Server Project Files

**Files:**
- Move: `managed/Dockerfile` to `managed/server/Dockerfile`
- Move: `managed/pyproject.toml` to `managed/server/pyproject.toml`
- Move: `managed/uv.lock` to `managed/server/uv.lock`
- Move: `managed/alembic.ini` to `managed/server/alembic.ini`
- Move: `managed/app/` to `managed/server/app/`
- Move: `managed/alembic/` to `managed/server/alembic/`
- Move: `managed/tests/` to `managed/server/tests/`

- [x] **Step 1: Create `managed/server/`**

Run: `mkdir -p managed/server`

Expected: directory exists.

- [x] **Step 2: Move server-owned files and directories**

Run the seven `mv` operations listed above.

Expected: `managed/server/` contains `Dockerfile`, `pyproject.toml`, `uv.lock`, `alembic.ini`, `app/`, `alembic/`, and `tests/`.

### Task 2: Update Build and CI References

**Files:**
- Modify: `managed/docker-compose.dev.yml`
- Modify: `managed/docker-compose.coolify.yml`
- Modify: `managed/ui/e2e/docker-compose.e2e.yml`
- Modify: `.github/workflows/ci.yml`
- Modify: `scripts/check_managed_version.py`
- Modify: `pyproject.toml`

- [x] **Step 1: Update compose build contexts**

Change server image build contexts from `.` or `../..` to the new `server` path from each compose file's working directory.

Expected:
- `managed/docker-compose.dev.yml`: `api.build: server`
- `managed/docker-compose.coolify.yml`: worker anchor and api use `build: server`
- `managed/ui/e2e/docker-compose.e2e.yml`: `api.build: ../../server`

- [x] **Step 2: Update CI working directory and comments**

Change `managed-server` job default working directory to `managed/server` and update comments that name the old server project root.

Expected: uv, ruff, mypy, and pytest run from `managed/server`.

- [x] **Step 3: Update version parity paths**

Change `PYPROJECT` to `managed/server/pyproject.toml` and `APP_MAIN` to `managed/server/app/main.py`, and update the docstring.

Expected: `scripts/check_managed_version.py` checks the moved sources.

- [x] **Step 4: Preserve root ruff scope**

Add `managed/ui/e2e/stub-issuer` to the root ruff `extend-exclude`, because the old server-root `pyproject.toml` no longer sits above `managed/ui/`.

Expected: root `ruff check` and `ruff format --check` continue to ignore the standalone E2E fixture.

### Task 3: Update Documentation and Inline Path Comments

**Files:**
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `docs/repository-layout.md`
- Modify: `docs/versioning.md`
- Modify: `managed/README.md`
- Modify: `managed/docs/frontend-design.md`
- Modify: server/ui comments that explicitly cite moved paths

- [x] **Step 1: Replace old server-root path references**

Update prose references such as `managed/Dockerfile`, `managed/app/`, `managed/tests/`, and `managed/pyproject.toml` to the new `managed/server/...` paths where they refer to server-owned files.

Expected: docs explain that `managed/` is a product folder and `managed/server/` is the server project.

- [x] **Step 2: Preserve product-level references**

Keep references to `managed/README.md`, `managed/ui/`, `managed/dev/`, and product-level compose files unchanged.

Expected: docs do not imply the UI or shared compose files moved.

### Task 4: Verify

**Files:**
- Read/check only.

- [x] **Step 1: Search for stale moved-path references**

Run: `rg -n "managed/(app|tests|alembic|Dockerfile|pyproject.toml)|working-directory: managed$|build: \\.|build: ../.." .`

Expected: no stale moved-path references except intentional historical/changelog text or clearly updated explanatory text.

- [x] **Step 2: Run version parity gate**

Run: `python3 scripts/check_managed_version.py`

Expected: exits 0 and reports matching managed version.

- [x] **Step 3: Run server gates**

Run from `managed/server`:
- `uv run --frozen ruff check`
- `uv run --frozen ruff format --check`
- `uv run --frozen mypy`
- `uv run --frozen pytest`

Expected: all pass.

- [x] **Step 4: Validate compose files when Docker is available**

Run:
- `docker compose -f managed/docker-compose.dev.yml config`
- `docker compose -f managed/docker-compose.coolify.yml config`
- `docker compose -f managed/ui/e2e/docker-compose.e2e.yml config`

Expected: all parse successfully. If Docker is unavailable, report that limit explicitly.

Actual: Docker was unavailable in this environment (`docker: command not found`), so full `docker compose config` could not run. A Ruby YAML check confirmed every compose `build` context resolves to an existing directory, including `managed/server`.

- [x] **Step 5: Run root lint and tests**

Run:
- `.venv/bin/ruff check`
- `.venv/bin/ruff format --check`
- `uv --cache-dir .uv-cache run pytest`

Expected: all pass. Actual: root ruff and root pytest passed; the temporary `.uv-cache` was removed after verification.
