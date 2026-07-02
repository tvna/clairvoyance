"""OIDC verification against real RS256 signatures (no network)."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast

import jwt
import pytest
from conftest import make_settings
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.auth.oidc import InvalidAdminTokenError, OIDCNotConfiguredError, OIDCVerifier
from app.auth.rbac import Role, parse_roles

ISSUER = "https://idp.example.com"
AUDIENCE = "clairvoyance-managed"

_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PRIVATE_PEM = _PRIVATE_KEY.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
)
_PUBLIC_PEM = _PRIVATE_KEY.public_key().public_bytes(
    serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo,
)


class FakeJWKSClient:
    def get_signing_key_from_jwt(self, token: str) -> jwt.PyJWK:
        return cast(jwt.PyJWK, SimpleNamespace(key=_PUBLIC_PEM))


def make_token(**overrides: Any) -> str:
    claims: dict[str, Any] = {
        "sub": "admin@example.com",
        "iss": ISSUER,
        "aud": AUDIENCE,
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "org": "acme",
        "roles": ["org_admin", "coach", "not-a-known-role"],
    }
    claims.update(overrides)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, _PRIVATE_PEM, algorithm="RS256")


def make_verifier(**settings_overrides: Any) -> OIDCVerifier:
    settings = make_settings(oidc_issuer=ISSUER, oidc_audience=AUDIENCE, **settings_overrides)
    return OIDCVerifier(settings, jwks_client=FakeJWKSClient())


def test_valid_token_yields_principal() -> None:
    principal = make_verifier().verify(make_token())
    assert principal.subject == "admin@example.com"
    assert principal.organization_key == "acme"
    assert principal.roles == frozenset({Role.ORG_ADMIN, Role.COACH})


def test_custom_claim_names() -> None:
    verifier = make_verifier(oidc_roles_claim="groups", oidc_org_claim="tenant")
    token = make_token(groups=["auditor"], tenant="acme2", roles=None, org=None)
    principal = verifier.verify(token)
    assert principal.organization_key == "acme2"
    assert principal.roles == frozenset({Role.AUDITOR})


@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": "someone-else"},
        {"iss": "https://evil.example.com"},
        {"exp": datetime.now(UTC) - timedelta(minutes=5)},
        {"exp": None},
        {"sub": None},
        {"org": None},
        {"org": ""},
    ],
)
def test_invalid_tokens_rejected(overrides: dict[str, Any]) -> None:
    with pytest.raises(InvalidAdminTokenError):
        make_verifier().verify(make_token(**overrides))


def test_unconfigured_verifier_refuses() -> None:
    verifier = OIDCVerifier(make_settings())
    with pytest.raises(OIDCNotConfiguredError):
        verifier.verify(make_token())


def test_signing_key_without_jwks_url_refuses() -> None:
    verifier = OIDCVerifier(make_settings())
    with pytest.raises(OIDCNotConfiguredError):
        verifier._signing_key(make_token())


def test_unreachable_jwks_is_invalid_token() -> None:
    settings = make_settings(
        oidc_issuer=ISSUER,
        oidc_audience=AUDIENCE,
        oidc_jwks_url="http://127.0.0.1:9/jwks.json",
    )
    with pytest.raises(InvalidAdminTokenError):
        OIDCVerifier(settings).verify(make_token())


def test_jwks_url_derived_from_issuer() -> None:
    verifier = OIDCVerifier(make_settings(oidc_issuer=ISSUER + "/", oidc_audience=AUDIENCE))
    assert verifier._jwks_url == ISSUER + "/.well-known/jwks.json"


def test_parse_roles_ignores_non_lists() -> None:
    assert parse_roles("org_admin") == frozenset()
    assert parse_roles(None) == frozenset()
    assert parse_roles(["org_admin", 42]) == frozenset({Role.ORG_ADMIN})
