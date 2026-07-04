"""Tests for ``scripts/rulesets_apply.py``.

The GitHub API boundary is ``urllib.request``; every test injects a fake
``opener`` (and a no-op ``sleeper`` where retries are exercised) so nothing
touches the network. Adapted from the upstream tvna/claude-md suite, trimmed to
the plan/apply-only surface this repo ships.
"""

from __future__ import annotations

import io
import json
import urllib.error
from email.message import Message
from pathlib import Path
from typing import Any

import pytest
import rulesets_apply as ra


def _hdrs() -> Message:
    """An empty header container of the type ``HTTPError`` expects."""
    return Message()


class Response:
    """Minimal stand-in for a urllib response with a ``status`` attribute."""

    def __init__(self, status: int, body: Any) -> None:
        self.status = status
        self.body = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")

    def read(self) -> bytes:
        return self.body

    def close(self) -> None:
        pass


def write_sot(path: Path, name: str) -> Path:
    path.write_text(
        json.dumps(
            {
                "name": name,
                "target": "branch",
                "enforcement": "active",
                "conditions": {},
                "bypass_actors": [],
                "rules": [],
            }
        ),
        encoding="utf-8",
    )
    return path


class TestDecideAction:
    def test_post_when_no_match(self) -> None:
        assert ra.decide_action("main", []) == {"action": "POST", "live_id": None, "match_count": 0}

    def test_put_when_one_match(self) -> None:
        assert ra.decide_action("main", [{"id": 42, "name": "main"}]) == {
            "action": "PUT",
            "live_id": 42,
            "match_count": 1,
        }

    def test_ambiguous_when_multiple_matches(self) -> None:
        live = [{"id": 1, "name": "main"}, {"id": 2, "name": "main"}]
        assert ra.decide_action("main", live) == {"action": "ambiguous", "live_id": None, "match_count": 2}


class TestRendering:
    def test_canonical_projection_preserves_only_six_fields(self) -> None:
        ruleset = {
            "id": 1,
            "name": "n",
            "target": "branch",
            "enforcement": "active",
            "conditions": {},
            "bypass_actors": [],
            "rules": [],
        }
        assert list(ra.canonical_projection(ruleset)) == list(ra.PROJECTION_KEYS)
        assert "id" not in ra.canonical_projection(ruleset)

    def test_render_diff_section_shape(self) -> None:
        live = {
            "name": "n",
            "target": "branch",
            "enforcement": "evaluate",
            "conditions": {},
            "bypass_actors": [],
            "rules": [],
        }
        sot = {**live, "enforcement": "active"}
        out = ra.render_diff_section("n", 9, live, sot)
        assert "<details><summary>Diff for <code>n</code> (id 9)" in out
        assert "```diff" in out
        assert "--- live" in out
        assert "+++ sot" in out
        assert '-  "enforcement": "evaluate"' in out
        assert '+  "enforcement": "active"' in out

    def test_render_summary_row_with_id(self) -> None:
        assert (
            ra.render_summary_row("main.json", "main", 1, "PUT applied", 42)
            == "| main.json | main | 1 | PUT applied | 42 |"
        )

    def test_render_summary_row_empty_id_uses_na(self) -> None:
        assert (
            ra.render_summary_row("main.json", "main", 0, "plan-only (POST)", None)
            == "| main.json | main | 0 | plan-only (POST) | n/a |"
        )

    def test_render_dispatch_header_carries_dry_run_flag(self) -> None:
        assert "- dry_run: `true`" in ra.render_dispatch_header(dry_run=True)
        assert "- dry_run: `false`" in ra.render_dispatch_header(dry_run=False)


class TestHttpWrappers:
    def test_fetch_live_rulesets_sends_auth_header(self) -> None:
        captured: dict[str, str] = {}

        def opener(request: Any) -> Response:
            captured["auth"] = request.headers["Authorization"]
            return Response(200, [{"id": 1, "name": "main"}])

        assert ra.fetch_live_rulesets("o/r", "tok", opener=opener) == [{"id": 1, "name": "main"}]
        assert captured["auth"] == "Bearer tok"

    def test_fetch_live_rulesets_rejects_non_list(self) -> None:
        with pytest.raises(ValueError, match="non-list JSON"):
            ra.fetch_live_rulesets("o/r", "tok", opener=lambda _r: Response(200, {"not": "a list"}))

    def test_fetch_live_rulesets_raises_on_401(self) -> None:
        def opener(request: Any) -> Response:
            raise urllib.error.HTTPError(request.full_url, 401, "Unauthorized", _hdrs(), io.BytesIO(b"bad token"))

        with pytest.raises(RuntimeError, match="HTTP 401"):
            ra.fetch_live_rulesets("o/r", "tok", opener=opener)

    def test_fetch_live_ruleset_returns_object(self) -> None:
        assert ra.fetch_live_ruleset("o/r", 7, "tok", opener=lambda _r: Response(200, {"id": 7})) == {"id": 7}

    def test_fetch_live_ruleset_rejects_non_object(self) -> None:
        with pytest.raises(ValueError, match="non-object JSON"):
            ra.fetch_live_ruleset("o/r", 7, "tok", opener=lambda _r: Response(200, [1, 2]))

    def test_apply_call_happy_path(self, tmp_path: Path) -> None:
        payload = write_sot(tmp_path / "main.json", "main")
        sleeps: list[int] = []

        def opener(request: Any) -> Response:
            assert request.get_method() == "PUT"
            assert json.loads(request.data)["name"] == "main"
            return Response(200, {"id": 42})

        code, body = ra.apply_call(
            method="PUT",
            url="https://example.test/rulesets/42",
            payload_path=payload,
            token="tok",
            opener=opener,
            sleeper=sleeps.append,
        )
        assert code == 200
        assert json.loads(body) == {"id": 42}
        assert sleeps == []

    def test_apply_call_retries_5xx_then_succeeds(self, tmp_path: Path) -> None:
        payload = write_sot(tmp_path / "main.json", "main")
        codes = [500, 500, 200]
        sleeps: list[int] = []

        def opener(request: Any) -> Response:
            code = codes.pop(0)
            if code >= 500:
                raise urllib.error.HTTPError(request.full_url, code, "Server error", _hdrs(), io.BytesIO(b"try again"))
            return Response(code, {"id": 42})

        code, _body = ra.apply_call(
            method="PUT",
            url="https://example.test/rulesets/42",
            payload_path=payload,
            token="tok",
            opener=opener,
            sleeper=sleeps.append,
        )
        assert code == 200
        assert sleeps == [5, 10]

    def test_apply_call_breaks_on_4xx(self, tmp_path: Path) -> None:
        payload = write_sot(tmp_path / "main.json", "main")
        sleeps: list[int] = []
        calls = 0

        def opener(request: Any) -> Response:
            nonlocal calls
            calls += 1
            raise urllib.error.HTTPError(request.full_url, 422, "Unprocessable", _hdrs(), io.BytesIO(b"bad json"))

        code, body = ra.apply_call(
            method="PUT",
            url="https://example.test/rulesets/42",
            payload_path=payload,
            token="tok",
            opener=opener,
            sleeper=sleeps.append,
        )
        assert code == 422
        assert body == "bad json"
        assert calls == 1
        assert sleeps == []

    def test_apply_call_retries_transport_failure(self, tmp_path: Path) -> None:
        payload = write_sot(tmp_path / "main.json", "main")
        sleeps: list[int] = []
        calls = 0

        def opener(_request: Any) -> Response:
            nonlocal calls
            calls += 1
            raise urllib.error.URLError("network down")

        code, body = ra.apply_call(
            method="PUT",
            url="https://example.test/rulesets/42",
            payload_path=payload,
            token="tok",
            opener=opener,
            sleeper=sleeps.append,
        )
        assert code == 0
        assert body == "network down"
        assert calls == 3
        assert sleeps == [5, 10]


class TestRequestPrimitives:
    def test_request_sets_content_type_when_data(self) -> None:
        captured: dict[str, Any] = {}

        def opener(request: Any) -> Response:
            captured["method"] = request.get_method()
            captured["content_type"] = request.headers.get("Content-type")
            captured["api_version"] = request.headers["X-github-api-version"]
            return Response(201, {"ok": True})

        code, body = ra._request("https://x.test", token="tok", method="POST", data=b"{}", opener=opener)
        assert code == 201
        assert json.loads(body) == {"ok": True}
        assert captured["method"] == "POST"
        assert captured["content_type"] == "application/json"
        assert captured["api_version"] == ra.API_VERSION

    def test_request_json_raises_on_non_2xx(self) -> None:
        def opener(request: Any) -> Response:
            raise urllib.error.HTTPError(request.full_url, 404, "Not Found", _hdrs(), io.BytesIO(b"missing"))

        with pytest.raises(RuntimeError, match="HTTP 404"):
            ra._request_json("https://x.test", token="tok", opener=opener)

    def test_response_status_prefers_status_then_code_then_getcode(self) -> None:
        class OnlyCode:
            code = 204

        class OnlyGetcode:
            def getcode(self) -> int:
                return 202

        class Nothing:
            pass

        assert ra._response_status(Response(200, {})) == 200
        assert ra._response_status(OnlyCode()) == 204
        assert ra._response_status(OnlyGetcode()) == 202
        assert ra._response_status(Nothing()) == 0

    def test_response_body_closes_response(self) -> None:
        closed: list[bool] = []

        class Body:
            def read(self) -> bytes:
                return b"payload"

            def close(self) -> None:
                closed.append(True)

        assert ra._response_body(Body()) == "payload"
        assert closed == [True]

    def test_display_http_code(self) -> None:
        assert ra._display_http_code(0) == "000"
        assert ra._display_http_code(503) == "503"


class TestPlanApplyFlows:
    def test_plan_new_writes_post_row(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sot = write_sot(tmp_path / "main.json", "main-protection")
        summary = tmp_path / "summary.md"
        monkeypatch.setenv("GH_TOKEN", "tok")
        monkeypatch.setattr(ra, "fetch_live_rulesets", lambda *_a, **_k: [])

        rc = ra.main(["plan", "--repo", "o/r", "--sot-file", str(sot), "--summary-file", str(summary)])
        assert rc == 0
        text = summary.read_text(encoding="utf-8")
        assert "- dry_run: `true`" in text
        assert "| main.json | main-protection | 0 | plan-only (POST) | n/a |" in text

    def test_plan_existing_renders_diff(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sot = write_sot(tmp_path / "main.json", "main-protection")
        summary = tmp_path / "summary.md"
        monkeypatch.setenv("GH_TOKEN", "tok")
        monkeypatch.setattr(ra, "fetch_live_rulesets", lambda *_a, **_k: [{"id": 5, "name": "main-protection"}])
        live = {
            "name": "main-protection",
            "target": "branch",
            "enforcement": "evaluate",
            "conditions": {},
            "bypass_actors": [],
            "rules": [],
        }
        monkeypatch.setattr(ra, "fetch_live_ruleset", lambda *_a, **_k: live)

        rc = ra.main(["plan", "--repo", "o/r", "--sot-file", str(sot), "--summary-file", str(summary)])
        assert rc == 0
        text = summary.read_text(encoding="utf-8")
        assert "Diff for <code>main-protection</code> (id 5)" in text
        assert "| main.json | main-protection | 1 | plan-only (PUT) | 5 |" in text

    def test_plan_ambiguous_exits_nonzero(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sot = write_sot(tmp_path / "main.json", "main-protection")
        summary = tmp_path / "summary.md"
        monkeypatch.setenv("GH_TOKEN", "tok")
        monkeypatch.setattr(
            ra,
            "fetch_live_rulesets",
            lambda *_a, **_k: [{"name": "main-protection"}, {"name": "main-protection"}],
        )
        rc = ra.main(["plan", "--repo", "o/r", "--sot-file", str(sot), "--summary-file", str(summary)])
        assert rc == 1
        assert "| main.json | main-protection | 2 | abort | n/a |" in summary.read_text(encoding="utf-8")

    def test_plan_invalid_sot_returns_one(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sot = tmp_path / "main.json"
        sot.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        summary = tmp_path / "summary.md"
        monkeypatch.setenv("GH_TOKEN", "tok")
        rc = ra.main(["plan", "--repo", "o/r", "--sot-file", str(sot), "--summary-file", str(summary)])
        assert rc == 1

    def test_apply_posts_new_ruleset(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sot = write_sot(tmp_path / "main.json", "main-protection")
        summary = tmp_path / "summary.md"
        monkeypatch.setenv("GH_TOKEN", "tok")
        calls: list[tuple[str, str]] = []

        def opener(request: Any) -> Response:
            calls.append((request.get_method(), request.full_url))
            if request.get_method() == "GET":
                return Response(200, [])
            assert json.loads(request.data)["name"] == "main-protection"
            return Response(201, {"id": 99})

        ra.apply_ruleset(
            repo="o/r",
            sot_file=sot,
            summary_file=summary,
            token="tok",
            opener=opener,
            sleeper=lambda _s: None,
        )
        assert calls == [
            ("GET", "https://api.github.com/repos/o/r/rulesets"),
            ("POST", "https://api.github.com/repos/o/r/rulesets"),
        ]
        text = summary.read_text(encoding="utf-8")
        assert "| main.json | main-protection | 0 | POST applied | 99 |" in text
        assert "plan-only" not in text

    def test_apply_puts_existing_ruleset(self, tmp_path: Path) -> None:
        sot = write_sot(tmp_path / "main.json", "main-protection")
        summary = tmp_path / "summary.md"
        live = {
            "name": "main-protection",
            "target": "branch",
            "enforcement": "active",
            "conditions": {},
            "bypass_actors": [],
            "rules": [],
        }

        def opener(request: Any) -> Response:
            method = request.get_method()
            if method == "GET" and request.full_url.endswith("/rulesets"):
                return Response(200, [{"id": 5, "name": "main-protection"}])
            if method == "GET":
                return Response(200, live)
            assert method == "PUT"
            assert request.full_url == "https://api.github.com/repos/o/r/rulesets/5"
            return Response(200, {"id": 5})

        result = ra.apply_ruleset(
            repo="o/r",
            sot_file=sot,
            summary_file=summary,
            token="tok",
            opener=opener,
            sleeper=lambda _s: None,
        )
        assert result["action"] == "PUT"
        assert "| main.json | main-protection | 1 | PUT applied | 5 |" in summary.read_text(encoding="utf-8")

    def test_apply_empty_body_yields_na_id(self, tmp_path: Path) -> None:
        sot = write_sot(tmp_path / "main.json", "main-protection")
        summary = tmp_path / "summary.md"

        def opener(request: Any) -> Response:
            if request.get_method() == "GET":
                return Response(200, [])
            return Response(200, b"")

        ra.apply_ruleset(
            repo="o/r", sot_file=sot, summary_file=summary, token="tok", opener=opener, sleeper=lambda _s: None
        )
        assert "| main.json | main-protection | 0 | POST applied | n/a |" in summary.read_text(encoding="utf-8")

    def test_apply_error_exits_and_records_body(self, tmp_path: Path) -> None:
        sot = write_sot(tmp_path / "main.json", "main-protection")
        summary = tmp_path / "summary.md"

        def opener(request: Any) -> Response:
            if request.get_method() == "GET":
                return Response(200, [])
            raise urllib.error.HTTPError(
                request.full_url, 422, "Unprocessable", _hdrs(), io.BytesIO(b"invalid ruleset")
            )

        with pytest.raises(SystemExit) as exc:
            ra.apply_ruleset(
                repo="o/r",
                sot_file=sot,
                summary_file=summary,
                token="tok",
                opener=opener,
                sleeper=lambda _s: None,
            )
        assert exc.value.code == 1
        text = summary.read_text(encoding="utf-8")
        assert "Error applying main.json (HTTP 422)" in text
        assert "invalid ruleset" in text


class TestCliEntrypoints:
    def test_apply_command_dispatches(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sot = write_sot(tmp_path / "main.json", "main-protection")
        summary = tmp_path / "summary.md"
        monkeypatch.setenv("GH_TOKEN", "tok")
        seen: dict[str, Any] = {}

        def fake_apply(**kwargs: Any) -> dict[str, Any]:
            seen.update(kwargs)
            return {}

        monkeypatch.setattr(ra, "apply_ruleset", fake_apply)
        rc = ra.main(["apply", "--repo", "o/r", "--sot-file", str(sot), "--summary-file", str(summary)])
        assert rc == 0
        assert seen["repo"] == "o/r"
        assert seen["sot_file"] == sot

    def test_env_token_missing_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GH_TOKEN", raising=False)
        with pytest.raises(SystemExit) as exc:
            ra._env_token()
        assert exc.value.code == 1

    def test_env_token_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GH_TOKEN", "abc")
        assert ra._env_token() == "abc"
