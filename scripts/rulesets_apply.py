#!/usr/bin/env python3
"""Plan and apply this repository's ``main`` branch ruleset from checked-in JSON.

Adapted from tvna/claude-md's ``rulesets_apply.py``, trimmed to this repo's
single main-branch ruleset (no all-branches ruleset, workflow-permissions, or
auto-delete reconcile here). The checked-in ``.github/rulesets/main.json`` is
the source of truth; the mutating ``apply-rulesets`` workflow stays thin while
the decision logic (create-vs-update, diff rendering, retry) lives here and is
unit-tested against an injected ``urllib`` opener, so no live GitHub call is
needed to cover it.

``plan`` is read-only: it renders a live-vs-SoT diff and never mutates. ``apply``
POSTs a new ruleset or PUTs the existing one by name. The GitHub API boundary is
``urllib.request`` so tests can inject a fake opener.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_VERSION = "2022-11-28"
API_ROOT = "https://api.github.com"
# The PUT payload replaces the whole ruleset, so the diff is taken over the
# fields GitHub echoes back for a ruleset object (dropping server-only keys
# like id/created_at/_links that would show as spurious changes).
PROJECTION_KEYS = (
    "name",
    "target",
    "enforcement",
    "conditions",
    "bypass_actors",
    "rules",
)


def decide_action(sot_name: str, live: list[dict[str, Any]]) -> dict[str, Any]:
    """Decide POST (create), PUT (update), or ambiguous by matching on name.

    A ruleset has no natural key other than its ``name`` in the SoT, so a single
    live ruleset of that name is updated in place; zero means create; more than
    one is ambiguous and refused rather than guessed.
    """
    matches = [item for item in live if item.get("name") == sot_name]
    if len(matches) == 0:
        return {"action": "POST", "live_id": None, "match_count": 0}
    if len(matches) == 1:
        return {"action": "PUT", "live_id": matches[0].get("id"), "match_count": 1}
    return {"action": "ambiguous", "live_id": None, "match_count": len(matches)}


def canonical_projection(ruleset: dict[str, Any]) -> dict[str, Any]:
    return {key: ruleset.get(key) for key in PROJECTION_KEYS}


def render_diff_section(name: str, live_id: int, live: dict[str, Any], sot: dict[str, Any]) -> str:
    live_text = _canonical_json_lines(canonical_projection(live))
    sot_text = _canonical_json_lines(canonical_projection(sot))
    diff = "".join(difflib.unified_diff(live_text, sot_text, fromfile="live", tofile="sot"))
    return "\n".join(
        [
            "",
            f"<details><summary>Diff for <code>{name}</code> (id {live_id})</summary>",
            "",
            "```diff",
            diff,
            "```",
            "</details>",
        ]
    )


def render_summary_row(file: str, name: str, matches: int, action: str, live_id: str | int | None) -> str:
    result_id = "n/a" if live_id in (None, "") else str(live_id)
    return f"| {file} | {name} | {matches} | {action} | {result_id} |"


def render_dispatch_header(*, dry_run: bool) -> str:
    return "\n".join(
        [
            "## Apply main ruleset; dispatch summary",
            "",
            f"- dry_run: `{str(dry_run).lower()}`",
            "",
            "| File | Ruleset name | Matches | Action | Result id |",
            "|---|---|---|---|---|",
        ]
    )


def fetch_live_rulesets(repo: str, token: str, *, opener: Any = urllib.request.urlopen) -> list[dict[str, Any]]:
    body = _request_json(f"{API_ROOT}/repos/{repo}/rulesets", token=token, opener=opener)
    if not isinstance(body, list):
        raise ValueError("GET /rulesets returned non-list JSON")
    return body


def fetch_live_ruleset(
    repo: str, ruleset_id: int, token: str, *, opener: Any = urllib.request.urlopen
) -> dict[str, Any]:
    body = _request_json(f"{API_ROOT}/repos/{repo}/rulesets/{ruleset_id}", token=token, opener=opener)
    if not isinstance(body, dict):
        raise ValueError(f"ruleset {ruleset_id} returned non-object JSON")
    return body


def apply_call(
    *,
    method: str,
    url: str,
    payload_path: Path,
    token: str,
    opener: Any = urllib.request.urlopen,
    sleeper: Any = time.sleep,
) -> tuple[int, str]:
    """Issue the mutating call with a short 5xx/transport retry.

    2xx returns immediately; a 4xx (including 429) is a request-level error that
    a retry would not fix, so it breaks out; 5xx and transport failures (code 0)
    back off and retry up to three attempts total.
    """
    payload = payload_path.read_bytes()
    final_code = 0
    final_body = ""
    for attempt in range(1, 4):
        code, body = _request(url, token=token, method=method, data=payload, opener=opener)
        final_code, final_body = code, body
        if 200 <= code < 300:
            return code, body
        print(f"Attempt {attempt}: HTTP {_display_http_code(code)} for {method} {url}")
        if code != 0 and code < 500:
            return code, body
        if attempt < 3:
            sleeper(attempt * 5)
    return final_code, final_body


def _prepare(
    *,
    repo: str,
    sot_file: Path,
    summary_file: Path,
    token: str,
    dry_run: bool,
    opener: Any,
) -> tuple[str, str, int, Any, list[str]]:
    """Load the SoT, decide the action, and build the summary rows (with diff).

    On an ambiguous match it flushes an abort row and exits non-zero rather than
    guess which live ruleset to overwrite.
    """
    sot = _load_sot(sot_file)
    name = str(sot["name"])
    live_rulesets = fetch_live_rulesets(repo, token, opener=opener)
    decision = decide_action(name, live_rulesets)
    action = str(decision["action"])
    match_count = int(decision["match_count"])
    live_id = decision["live_id"]
    rows = [render_dispatch_header(dry_run=dry_run)]
    if action == "ambiguous":
        rows.append(render_summary_row(sot_file.name, name, match_count, "abort", None))
        _append_summary(summary_file, rows)
        print(
            f"::error::Multiple existing rulesets named '{name}' ({match_count}). Refusing to guess; resolve manually."
        )
        raise SystemExit(1)
    if action == "PUT":
        live = fetch_live_ruleset(repo, int(live_id), token, opener=opener)
        rows.append(render_diff_section(name, int(live_id), live, sot))
    return name, action, match_count, live_id, rows


def plan_ruleset(
    *,
    repo: str,
    sot_file: Path,
    summary_file: Path,
    token: str,
    opener: Any = urllib.request.urlopen,
) -> dict[str, Any]:
    name, action, match_count, live_id, rows = _prepare(
        repo=repo, sot_file=sot_file, summary_file=summary_file, token=token, dry_run=True, opener=opener
    )
    rows.append(render_summary_row(sot_file.name, name, match_count, f"plan-only ({action})", live_id))
    _append_summary(summary_file, rows)
    return {"name": name, "action": action, "matches": match_count, "live_id": live_id}


def apply_ruleset(
    *,
    repo: str,
    sot_file: Path,
    summary_file: Path,
    token: str,
    opener: Any = urllib.request.urlopen,
    sleeper: Any = time.sleep,
) -> dict[str, Any]:
    name, action, match_count, live_id, rows = _prepare(
        repo=repo, sot_file=sot_file, summary_file=summary_file, token=token, dry_run=False, opener=opener
    )
    url = f"{API_ROOT}/repos/{repo}/rulesets"
    if action == "PUT":
        url = f"{url}/{live_id}"
    code, body = apply_call(method=action, url=url, payload_path=sot_file, token=token, opener=opener, sleeper=sleeper)
    if not 200 <= code < 300:
        rows.extend(["", f"**Error applying {sot_file.name} (HTTP {_display_http_code(code)}):**", "```", body, "```"])
        _append_summary(summary_file, rows)
        print(f"::error::Failed to {action} {sot_file.name} (last HTTP {_display_http_code(code)}).")
        raise SystemExit(1)
    response = json.loads(body or "{}")
    rows.append(render_summary_row(sot_file.name, name, match_count, f"{action} applied", response.get("id")))
    _append_summary(summary_file, rows)
    return {"name": name, "action": action, "matches": match_count, "live_id": response.get("id")}


def _load_sot(sot_file: Path) -> dict[str, Any]:
    with sot_file.open(encoding="utf-8") as fp:
        body = json.load(fp)
    if not isinstance(body, dict):
        raise ValueError(f"{sot_file} must contain a JSON object")
    if not isinstance(body.get("name"), str) or not body["name"]:
        # decide_action matches the live ruleset by name, so a missing/blank
        # name would otherwise KeyError deep in _prepare; fail with a clear
        # message the main() handler turns into a clean ::error:: instead.
        raise ValueError(f"{sot_file} must set a non-empty string 'name'")
    return body


def _canonical_json_lines(value: dict[str, Any]) -> list[str]:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    return text.splitlines(keepends=True)


def _append_summary(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        for line in lines:
            fp.write(line)
            fp.write("\n")


def _request_json(url: str, *, token: str, opener: Any = urllib.request.urlopen) -> Any:
    code, body = _request(url, token=token, method="GET", opener=opener)
    if not 200 <= code < 300:
        raise RuntimeError(f"GET {url} failed (HTTP {_display_http_code(code)}): {body}")
    return json.loads(body)


def _request(
    url: str,
    *,
    token: str,
    method: str,
    data: bytes | None = None,
    opener: Any = urllib.request.urlopen,
) -> tuple[int, str]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    # url is built from the fixed API_ROOT (https://api.github.com) plus the
    # workflow-supplied repo/ruleset_id; opener is injectable for tests but
    # defaults to urllib.request.urlopen on that fixed https endpoint.
    request = urllib.request.Request(url, data=data, headers=headers, method=method)  # noqa: S310 -- fixed https endpoint
    try:
        response = opener(request)
        return _response_status(response), _response_body(response)
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        return 0, str(exc.reason)


def _response_status(response: Any) -> int:
    status = getattr(response, "status", None) or getattr(response, "code", None)
    if status is None and hasattr(response, "getcode"):
        status = response.getcode()
    if status is None:
        return 0
    return int(status)


def _response_body(response: Any) -> str:
    try:
        data = response.read()
    finally:
        close = getattr(response, "close", None)
        if close is not None:
            close()
    return data.decode("utf-8", errors="replace")


def _display_http_code(code: int) -> str:
    return "000" if code == 0 else str(code)


def _env_token() -> str:
    token = os.environ.get("GH_TOKEN")
    if not token:
        print('::error::RULESETS_PAT secret is not set. See docs/runbooks/rulesets.md "Required secret".')
        raise SystemExit(1)
    return token


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", required=True)
    common.add_argument("--sot-file", required=True, type=Path)
    common.add_argument("--summary-file", required=True, type=Path)

    plan = sub.add_parser("plan", parents=[common])
    plan.set_defaults(func=_cmd_plan)

    apply = sub.add_parser("apply", parents=[common])
    apply.set_defaults(func=_cmd_apply)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (ValueError, RuntimeError) as exc:
        # ValueError: bad SoT / non-JSON API body. RuntimeError: a non-2xx GET
        # (e.g. an expired or under-scoped RULESETS_PAT returning 401/403).
        # Both are operational failures, so surface a clean ::error:: and exit 1
        # rather than let the raw traceback through.
        print(f"::error::{exc}")
        return 1
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


def _cmd_plan(args: argparse.Namespace) -> None:
    plan_ruleset(repo=args.repo, sot_file=args.sot_file, summary_file=args.summary_file, token=_env_token())


def _cmd_apply(args: argparse.Namespace) -> None:
    apply_ruleset(repo=args.repo, sot_file=args.sot_file, summary_file=args.summary_file, token=_env_token())


if __name__ == "__main__":
    sys.exit(main())
