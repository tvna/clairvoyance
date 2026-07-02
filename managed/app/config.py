"""Runtime configuration.

All settings come from ``CLAIRVOYANCE_``-prefixed environment variables so the
same image can run as api, worker, scheduler, or migrate (Kubernetes-ready:
config via environment, no baked-in state).

``database_url`` and ``redis_url`` are required everywhere. The collector
pepper and the OIDC settings are only needed by the api process, so they stay
optional here and the corresponding auth layer fails loudly (503) when a
request arrives while they are unset.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CLAIRVOYANCE_")

    database_url: str
    redis_url: str

    # Collector auth: HMAC pepper for token hashing (api only).
    collector_token_pepper: str | None = None

    # Admin auth: OIDC bearer validation (api only).
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    # Defaults to `{issuer}/.well-known/jwks.json` when unset.
    oidc_jwks_url: str | None = None
    oidc_roles_claim: str = "roles"
    oidc_org_claim: str = "org"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
