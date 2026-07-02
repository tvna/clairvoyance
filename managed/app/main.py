"""Application factory.

Run with ``uvicorn app.main:create_app --factory``. State (engine, session
factory, Redis client, OIDC verifier) hangs off ``app.state`` so tests can
build an app around their own backends.
"""

from fastapi import FastAPI
from redis import Redis

from app.api import admin, collector, health
from app.auth.oidc import OIDCVerifier
from app.config import Settings, get_settings
from app.db.session import build_engine, build_session_factory


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Clairvoyance Managed Coaching Server", version="0.1.0")
    app.state.settings = settings
    app.state.engine = build_engine(settings)
    app.state.session_factory = build_session_factory(app.state.engine)
    app.state.redis = Redis.from_url(settings.redis_url, socket_connect_timeout=3, socket_timeout=3)
    app.state.oidc_verifier = OIDCVerifier(settings)

    app.include_router(health.router)
    app.include_router(collector.router)
    app.include_router(admin.router)
    return app
