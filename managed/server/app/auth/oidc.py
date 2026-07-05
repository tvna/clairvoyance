"""OIDC bearer verification for the admin API.

Provider-agnostic: issuer, audience, and the JWKS endpoint all come from the
environment. The JWKS URL is deliberately explicit — providers publish it at
different paths (Okta `/v1/keys`, Keycloak `/protocol/openid-connect/certs`,
Google a separate certs host), so deriving it from the issuer would turn a
deployment misconfiguration into per-request 401s. Configuration and JWKS
availability problems surface as 503, never as "invalid token".
"""

from typing import Protocol

import jwt

from app.auth.rbac import AdminPrincipal, parse_roles
from app.config import Settings


class SigningKeyProvider(Protocol):
    """The subset of jwt.PyJWKClient the verifier needs (test-injectable)."""

    def get_signing_key_from_jwt(self, token: str) -> jwt.PyJWK: ...


class OIDCNotConfiguredError(Exception):
    """Admin auth was requested but the OIDC settings are incomplete."""


class JWKSUnavailableError(Exception):
    """The JWKS endpoint could not be fetched or parsed (infra, not the token)."""


class InvalidAdminTokenError(Exception):
    """The bearer token failed verification or lacks required claims."""


class OIDCVerifier:
    def __init__(self, settings: Settings, jwks_client: SigningKeyProvider | None = None) -> None:
        self._issuer = settings.oidc_issuer
        self._audience = settings.oidc_audience
        self._roles_claim = settings.oidc_roles_claim
        self._org_claim = settings.oidc_org_claim
        self._jwks_url = settings.oidc_jwks_url
        self._jwks_client = jwks_client

    def _signing_key(self, token: str) -> jwt.PyJWK:
        if self._jwks_client is None:
            if self._jwks_url is None:
                raise OIDCNotConfiguredError("CLAIRVOYANCE_OIDC_JWKS_URL is not set")
            self._jwks_client = jwt.PyJWKClient(self._jwks_url, cache_keys=True)
        return self._jwks_client.get_signing_key_from_jwt(token)

    def _jwk_error_is_token_specific(self, token: str, exc: jwt.exceptions.PyJWKClientError) -> bool:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError:
            return True
        return "kid" in header and "Unable to find a signing key that matches" in str(exc)

    def verify(self, token: str) -> AdminPrincipal:
        if self._issuer is None or self._audience is None:
            raise OIDCNotConfiguredError("CLAIRVOYANCE_OIDC_ISSUER / CLAIRVOYANCE_OIDC_AUDIENCE are not set")
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
        except jwt.exceptions.PyJWKClientError as exc:
            if self._jwk_error_is_token_specific(token, exc):
                raise InvalidAdminTokenError(str(exc)) from exc
            raise JWKSUnavailableError(str(exc)) from exc
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
