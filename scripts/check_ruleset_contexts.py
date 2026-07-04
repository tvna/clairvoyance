#!/usr/bin/env python3
"""Drift gate: the main ruleset's required checks must match the CI job set.

``.github/rulesets/main.json`` hard-codes CI job names as ``required_status_checks``
contexts. Nothing else ties those strings to the actual jobs in
``.github/workflows/ci.yml``: rename a job (or add one) and a required check
silently references a context that never reports -- blocking merges forever --
or a new job never gates merges at all. ``ci.yml`` already ships drift gates for
its other single-sources-of-truth (manifest/version parity); this is the
analogue for the ruleset context list, so the invariant is enforced
deterministically rather than by memory (CLAUDE.md section 3).

The check is intentionally dependency-free (stdlib only) so it runs in the CI
``validate`` job, which uses the system ``python3`` with no third-party YAML
module: job keys are read by a small line-scan of the ``jobs:`` block rather
than a full YAML parse.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
CI_YML = REPO_ROOT / ".github/workflows/ci.yml"
RULESET_JSON = REPO_ROOT / ".github/rulesets/main.json"

# A job key is a line indented exactly two spaces inside the top-level `jobs:`
# block, an identifier, then a colon and nothing else (job bodies sit at four
# spaces; keys with an inline value -- e.g. concurrency's `  group:` -- are not
# job keys and live outside `jobs:` anyway).
_JOB_KEY = re.compile(r"^ {2}([A-Za-z0-9_-]+):\s*$")


def ci_job_names(ci_yml_text: str) -> set[str]:
    names: set[str] = set()
    in_jobs = False
    for line in ci_yml_text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" "):
            # A top-level key: we are inside `jobs:` only while it is the one.
            in_jobs = line.rstrip() == "jobs:"
            continue
        if in_jobs:
            match = _JOB_KEY.match(line)
            if match:
                names.add(match.group(1))
    return names


def required_contexts(ruleset: dict[str, Any]) -> set[str]:
    for rule in ruleset.get("rules", []):
        if rule.get("type") == "required_status_checks":
            checks = rule.get("parameters", {}).get("required_status_checks", [])
            return {check["context"] for check in checks}
    return set()


def check(ci_yml_text: str, ruleset: dict[str, Any]) -> list[str]:
    """Return human-readable drift errors; empty means the sets agree."""
    jobs = ci_job_names(ci_yml_text)
    contexts = required_contexts(ruleset)
    errors: list[str] = []
    for context in sorted(contexts - jobs):
        errors.append(f"required status check '{context}' has no matching job in ci.yml (renamed or removed?)")
    for job in sorted(jobs - contexts):
        errors.append(f"ci.yml job '{job}' is not a required status check in the ruleset (unguarded merge?)")
    return errors


def main(argv: list[str] | None = None) -> int:
    ci_path, ruleset_path = _paths(argv)
    ruleset = json.loads(ruleset_path.read_text(encoding="utf-8"))
    errors = check(ci_path.read_text(encoding="utf-8"), ruleset)
    if errors:
        for error in errors:
            print(f"::error::{error}")
        print(f"Ruleset drift: {len(errors)} mismatch(es) between {ruleset_path.name} and {ci_path.name}.")
        return 1
    print(f"ok: {ruleset_path.name} required checks match ci.yml jobs")
    return 0


def _paths(argv: list[str] | None) -> tuple[Path, Path]:
    args = list(sys.argv[1:] if argv is None else argv)
    ci = Path(args[0]) if len(args) > 0 else CI_YML
    ruleset = Path(args[1]) if len(args) > 1 else RULESET_JSON
    return ci, ruleset


if __name__ == "__main__":
    sys.exit(main())
