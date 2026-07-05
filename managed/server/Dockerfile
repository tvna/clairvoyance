# One image, four commands: api (default), worker, scheduler, migrate.
# Compose (and later Kubernetes) selects the process via `command`.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /srv/app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Dependency layer first so code changes do not re-resolve.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

ENV PATH="/srv/app/.venv/bin:$PATH"

RUN groupadd --system appuser && useradd --system --gid appuser appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
