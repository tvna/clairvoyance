"""OIDC bearer verification for the admin API.

Provider-agnostic: the issuer, audience, and JWKS endpoint come from the
environment, so any OIDC/SSO provider that issues RS256/ES256 JWTs works.
The organization key and roles ride in configurable claims.
"""

from typing import Protocol

import jwt

from app.auth.rbac import AdminPrincipal, parse_roles
from app.config import Settings


class SigningKeyProvider(Protocol):
    """The subset of jwt.PyJWKClient the verifier needs (test-injectable)."""

    def get_signing_key_from_jwt(self, token: str) -> jwt.PyJWK: ...


class OIDCNotConfiguredError(Exception):
    """Admin auth was requested but the OIDC settings are unset."""


class InvalidAdminTokenError(Exception):
    """The bearer token failed verification or lacks required claims."""


class OIDCVerifier:
    def __init__(self, settings: Settings, jwks_client: SigningKeyProvider | None = None) -> None:
        self._issuer = settings.oidc_issuer
        self._audience = settings.oidc_audience
        self._roles_claim = settings.oidc_roles_claim
        self._org_claim = settings.oidc_org_claim
        self._jwks_url = settings.oidc_jwks_url
        if self._jwks_url is None and self._issuer is not None:
            self._jwks_url = self._issuer.rstrip("/") + "/.well-known/jwks.json"
        self._jwks_client = jwks_client

    def _signing_key(self, token: str) -> jwt.PyJWK:
        if self._jwks_client is None:
            if self._jwks_url is None:
                raise OIDCNotConfiguredError
            self._jwks_client = jwt.PyJWKClient(self._jwks_url, cache_keys=True)
        return self._jwks_client.get_signing_key_from_jwt(token)

    def verify(self, token: str) -> AdminPrincipal:
        if self._issuer is None or self._audience is None:
            raise OIDCNotConfiguredError
        try:
            key = self._signing_key(token)
            claims = jwt.decode(
                token,
                key.key,
                algorithms=["RS256", "ES256"],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise InvalidAdminTokenError(str(exc)) from exc

        organization_key = claims.get(self._org_claim)
        if not isinstance(organization_key, str) or not organization_key:
            raise InvalidAdminTokenError(f"missing organization claim '{self._org_claim}'")
        return AdminPrincipal(
            subject=str(claims["sub"]),
            organization_key=organization_key,
            roles=parse_roles(claims.get(self._roles_claim)),
        )
