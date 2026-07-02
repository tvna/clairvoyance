"""Liveness and readiness probes (Coolify health checks, Kubernetes probes)."""

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Request, Response, status
from sqlalchemy import text

router = APIRouter()


@router.get("/healthz")
@router.get("/livez")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


def _check_database(request: Request) -> None:
    with request.app.state.engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def _check_redis(request: Request) -> None:
    request.app.state.redis.ping()


_PROBES: dict[str, Callable[[Request], None]] = {
    "database": _check_database,
    "redis": _check_redis,
}


@router.get("/readyz")
def readyz(request: Request, response: Response) -> dict[str, Any]:
    checks: dict[str, str] = {}
    for name, probe in _PROBES.items():
        try:
            probe(request)
            checks[name] = "ok"
        except Exception as exc:  # readiness reports any backend failure, not just known ones.
            checks[name] = f"error: {type(exc).__name__}"

    ready = all(value == "ok" for value in checks.values())
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"ready": ready, "checks": checks}
