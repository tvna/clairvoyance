"""Purpose-built stub OIDC issuer for the managed-ui E2E smoke (design doc
§13). Not a reusable OIDC test fixture -- scoped to this issue, matching
tests/test_oidc.py's RS256 approach but adding a real Authorization Code +
PKCE (S256) flow with an HTML form so Playwright drives an actual browser
redirect, not a mocked one.

Deliberately standalone (own requirements.txt/Dockerfile): it must never
touch managed/pyproject.toml, so the real backend's dependency tree stays
exactly what it was before this issue -- zero backend change.
"""

from __future__ import annotations

import base64
import hashlib
import http.server
import json
import os
import secrets
import threading
import time
import urllib.parse
from html import escape
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# The browser-facing origin (through the e2e front proxy, same origin as
# the ui and api paths -- design §3's "one domain" mirrored for e2e). The
# api container reaches this same process over the compose network
# directly (CLAIRVOYANCE_OIDC_JWKS_URL), bypassing this value entirely;
# EXTERNAL_URL only has to be correct for what the *browser* reaches and
# for the `iss` claim api verifies against CLAIRVOYANCE_OIDC_ISSUER.
EXTERNAL_URL = os.environ.get("STUB_ISSUER_EXTERNAL_URL", "http://localhost:18080/issuer").rstrip("/")
PORT = int(os.environ.get("STUB_ISSUER_PORT", "8000"))
KID = "stub-issuer-key-1"
ACCESS_TOKEN_TTL_SECONDS = 3600
KNOWN_ROLES = ["org_admin", "team_manager", "coach", "auditor"]
DEFAULT_SUB = "e2e-admin@example.com"
DEFAULT_ORG = "acme"

_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_private_pem = _private_key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
)
_public_numbers = _private_key.public_key().public_numbers()


def _b64url_uint(value: int) -> str:
    byte_length = (value.bit_length() + 7) // 8 or 1
    return base64.urlsafe_b64encode(value.to_bytes(byte_length, "big")).rstrip(b"=").decode("ascii")


JWKS = {
    "keys": [
        {
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "kid": KID,
            "n": _b64url_uint(_public_numbers.n),
            "e": _b64url_uint(_public_numbers.e),
        }
    ]
}

DISCOVERY_DOCUMENT = {
    "issuer": EXTERNAL_URL,
    "authorization_endpoint": f"{EXTERNAL_URL}/authorize",
    "token_endpoint": f"{EXTERNAL_URL}/token",
    "jwks_uri": f"{EXTERNAL_URL}/jwks.json",
    "end_session_endpoint": f"{EXTERNAL_URL}/logout",
    "response_types_supported": ["code"],
    "subject_types_supported": ["public"],
    "id_token_signing_alg_values_supported": ["RS256"],
    "scopes_supported": ["openid", "profile", "offline_access"],
    "token_endpoint_auth_methods_supported": ["client_secret_post", "none"],
    "code_challenge_methods_supported": ["S256"],
}

_lock = threading.Lock()
AUTH_CODES: dict[str, dict[str, Any]] = {}
REFRESH_TOKENS: dict[str, dict[str, Any]] = {}


def mint_access_token(sub: str, org: str, roles: list[str], audience: str) -> str:
    now = int(time.time())
    claims = {
        "sub": sub,
        "iss": EXTERNAL_URL,
        "aud": audience,
        "iat": now,
        "exp": now + ACCESS_TOKEN_TTL_SECONDS,
        "org": org,
        "roles": roles,
    }
    return jwt.encode(claims, _private_pem, algorithm="RS256", headers={"kid": KID})


def mint_id_token(sub: str, client_id: str, nonce: str | None) -> str:
    now = int(time.time())
    claims: dict[str, Any] = {
        "sub": sub,
        "iss": EXTERNAL_URL,
        "aud": client_id,
        "iat": now,
        "exp": now + ACCESS_TOKEN_TTL_SECONDS,
    }
    if nonce:
        claims["nonce"] = nonce
    return jwt.encode(claims, _private_pem, algorithm="RS256", headers={"kid": KID})


def verify_pkce(code_verifier: str, code_challenge: str, method: str) -> bool:
    if method == "plain":
        return code_verifier == code_challenge
    if method == "S256":
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        return computed == code_challenge
    return False


def _first(form: dict[str, list[str]], name: str, default: str = "") -> str:
    values = form.get(name)
    return values[0] if values else default


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "StubIssuer/1.0"

    def log_message(self, log_format: str, *args: Any) -> None:
        print(f"stub-issuer: {self.address_string()} " + (log_format % args), flush=True)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status: int, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, location: str) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/healthz":
            self._send_json(200, {"status": "ok"})
        elif parsed.path == "/.well-known/openid-configuration":
            self._send_json(200, DISCOVERY_DOCUMENT)
        elif parsed.path == "/jwks.json":
            self._send_json(200, JWKS)
        elif parsed.path == "/authorize":
            self._handle_authorize_form(query)
        elif parsed.path == "/logout":
            self._handle_logout(query)
        else:
            self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw_body = self.rfile.read(length) if length else b""
        form = urllib.parse.parse_qs(raw_body.decode("utf-8"))
        if parsed.path == "/authorize/submit":
            self._handle_authorize_submit(form)
        elif parsed.path == "/token":
            self._handle_token(form)
        else:
            self._send_json(404, {"error": "not_found"})

    def _handle_authorize_form(self, query: dict[str, list[str]]) -> None:
        def one(name: str, default: str = "") -> str:
            return query.get(name, [default])[0]

        hidden_fields = {
            "client_id": one("client_id"),
            "redirect_uri": one("redirect_uri"),
            "state": one("state"),
            "scope": one("scope"),
            "code_challenge": one("code_challenge"),
            "code_challenge_method": one("code_challenge_method", "S256"),
            "audience": one("audience"),
            "nonce": one("nonce"),
        }
        hidden_html = "\n".join(
            f'<input type="hidden" name="{escape(name)}" value="{escape(value)}">'
            for name, value in hidden_fields.items()
        )
        role_checkboxes = "\n".join(
            '<label><input type="checkbox" name="roles" value="{role}"{checked}> {role}</label><br>'.format(
                role=escape(role), checked=" checked" if role == "org_admin" else ""
            )
            for role in KNOWN_ROLES
        )
        html = f"""<!doctype html>
<html>
<head><title>Stub OIDC Issuer sign-in</title></head>
<body>
<h1>Stub OIDC Issuer</h1>
<form method="post" action="/authorize/submit">
{hidden_html}
<p><label>Organization key <input type="text" name="org" value="{escape(DEFAULT_ORG)}"></label></p>
<p><label>Subject <input type="text" name="sub" value="{escape(DEFAULT_SUB)}"></label></p>
<fieldset>
<legend>Roles</legend>
{role_checkboxes}
</fieldset>
<button type="submit">Sign in</button>
</form>
</body>
</html>"""
        self._send_html(200, html)

    def _handle_authorize_submit(self, form: dict[str, list[str]]) -> None:
        redirect_uri = _first(form, "redirect_uri")
        state = _first(form, "state")
        if not redirect_uri:
            self._send_json(400, {"error": "invalid_request", "error_description": "missing redirect_uri"})
            return
        code = secrets.token_urlsafe(24)
        with _lock:
            AUTH_CODES[code] = {
                "client_id": _first(form, "client_id"),
                "redirect_uri": redirect_uri,
                "code_challenge": _first(form, "code_challenge"),
                "code_challenge_method": _first(form, "code_challenge_method", "S256"),
                "audience": _first(form, "audience"),
                "nonce": _first(form, "nonce") or None,
                "sub": _first(form, "sub") or DEFAULT_SUB,
                "org": _first(form, "org") or DEFAULT_ORG,
                "roles": [role for role in form.get("roles", []) if role in KNOWN_ROLES],
                "used": False,
            }
        location = f"{redirect_uri}?code={urllib.parse.quote(code)}&state={urllib.parse.quote(state)}"
        self._redirect(location)

    def _handle_token(self, form: dict[str, list[str]]) -> None:
        grant_type = _first(form, "grant_type")
        if grant_type == "authorization_code":
            self._handle_authorization_code_grant(form)
        elif grant_type == "refresh_token":
            self._handle_refresh_token_grant(form)
        else:
            self._send_json(400, {"error": "unsupported_grant_type"})

    def _handle_authorization_code_grant(self, form: dict[str, list[str]]) -> None:
        code = _first(form, "code")
        with _lock:
            record = AUTH_CODES.get(code)
            if record is None or record["used"]:
                self._send_json(400, {"error": "invalid_grant", "error_description": "unknown or reused code"})
                return
            if record["redirect_uri"] != _first(form, "redirect_uri") or record["client_id"] != _first(
                form, "client_id"
            ):
                self._send_json(
                    400, {"error": "invalid_grant", "error_description": "redirect_uri/client_id mismatch"}
                )
                return
            if record["code_challenge"] and not verify_pkce(
                _first(form, "code_verifier"), record["code_challenge"], record["code_challenge_method"]
            ):
                self._send_json(400, {"error": "invalid_grant", "error_description": "PKCE verification failed"})
                return
            record["used"] = True
            claims_source = dict(record)
        self._issue_tokens(claims_source)

    def _handle_refresh_token_grant(self, form: dict[str, list[str]]) -> None:
        refresh_token = _first(form, "refresh_token")
        with _lock:
            record = REFRESH_TOKENS.pop(refresh_token, None)
        if record is None:
            self._send_json(400, {"error": "invalid_grant", "error_description": "unknown refresh token"})
            return
        self._issue_tokens(record)

    def _issue_tokens(self, record: dict[str, Any]) -> None:
        audience = record.get("audience") or ""
        access_token = mint_access_token(record["sub"], record["org"], record["roles"], audience)
        id_token = mint_id_token(record["sub"], record["client_id"], record.get("nonce"))
        new_refresh_token = secrets.token_urlsafe(24)
        with _lock:
            # Rotation (design §5): each refresh grant invalidates the
            # token that was just spent and issues a new one.
            REFRESH_TOKENS[new_refresh_token] = {
                "client_id": record["client_id"],
                "audience": audience,
                "nonce": record.get("nonce"),
                "sub": record["sub"],
                "org": record["org"],
                "roles": record["roles"],
            }
        self._send_json(
            200,
            {
                "access_token": access_token,
                "id_token": id_token,
                "refresh_token": new_refresh_token,
                "token_type": "Bearer",
                "expires_in": ACCESS_TOKEN_TTL_SECONDS,
            },
        )

    def _handle_logout(self, query: dict[str, list[str]]) -> None:
        redirect = query.get("post_logout_redirect_uri", [""])[0]
        if redirect:
            self._redirect(redirect)
        else:
            self._send_html(200, "<html><body>Signed out.</body></html>")


def main() -> None:
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)  # noqa: S104 (intentional: container-internal)
    print(f"stub-issuer: listening on :{PORT}, external URL {EXTERNAL_URL}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
