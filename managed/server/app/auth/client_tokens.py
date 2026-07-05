"""Collector token issuance and verification.

Tokens are random 256-bit URL-safe strings. Only HMAC-SHA256(pepper, token)
is stored, so a database dump alone cannot forge a token; the pepper lives
only in the api process environment.
"""

import hashlib
import hmac
import secrets

TOKEN_PREFIX = "cvk_"  # noqa: S105 - a public identifier prefix, not a secret.


def generate_token() -> str:
    return TOKEN_PREFIX + secrets.token_urlsafe(32)


def hash_token(pepper: str, raw_token: str) -> str:
    return hmac.new(pepper.encode(), raw_token.encode(), hashlib.sha256).hexdigest()
