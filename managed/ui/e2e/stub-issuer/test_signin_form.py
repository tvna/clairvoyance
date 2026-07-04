"""No-Docker regression gate for the stub issuer's sign-in form (retro #64,
repair 1).

The rendered form must POST to a path *under* the issuer's external base path,
not to the proxy host root. When the action was the root-absolute
``/authorize/submit``, the e2e front proxy -- which only routes ``/issuer/*``
to this stub -- sent the submission to the api container instead, and both
Playwright sign-ins timed out on ``page.waitForURL``. That bug only surfaced
through the proxy, so a stub-run-standalone check (Docker unavailable in the
implementing sandbox) never caught it.

Asserting the action is under the *routed* issuer prefix -- the path component
of ``STUB_ISSUER_EXTERNAL_URL`` with a trailing slash, matching the proxy's
slash-delimited ``location /issuer/`` -- catches the regression with a plain
in-process HTTP request: no proxy, no compose, no Docker. The trailing slash
matters: ``/issuer`` or ``/issuer2/...`` would fall through to the api just as
the root-absolute action did, so a bare ``startswith('/issuer')`` would leave
the gate green on that regression.
"""

from __future__ import annotations

import http.server
import threading
import urllib.parse
import urllib.request
from html.parser import HTMLParser

import app


class _FormActionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.action: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "form":
            for name, value in attrs:
                if name == "action":
                    self.action = value


def _render_signin_form() -> str:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        with urllib.request.urlopen(f"http://{host}:{port}/authorize", timeout=5) as response:
            return response.read().decode("utf-8")
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_signin_form_action_under_routed_issuer_prefix() -> None:
    base_path = urllib.parse.urlsplit(app.EXTERNAL_URL).path
    assert base_path, "STUB_ISSUER_EXTERNAL_URL must carry a path component"
    # The e2e proxy routes the slash-delimited `location /issuer/` to the stub
    # (proxy/default.conf); a `/issuer` or `/issuer2/...` action would fall
    # through to the api, so require the trailing-slash boundary, not a bare
    # prefix.
    routed_prefix = base_path.rstrip("/") + "/"

    parser = _FormActionParser()
    parser.feed(_render_signin_form())

    assert parser.action is not None, "sign-in form is missing an action attribute"
    assert parser.action.startswith(routed_prefix), (
        f"form action {parser.action!r} is not under the routed issuer prefix "
        f"{routed_prefix!r}; the e2e proxy routes only that slash-delimited "
        f"prefix, so an action outside it bypasses the stub and reproduces the "
        f"sign-in timeout"
    )
