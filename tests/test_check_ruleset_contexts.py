"""Tests for ``scripts/check_ruleset_contexts.py`` (the ruleset drift gate)."""

from __future__ import annotations

import json
from pathlib import Path

import check_ruleset_contexts as crc
import pytest

CI_YML_SAMPLE = """\
name: CI

on:
  pull_request:
  push:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}
  cancel-in-progress: true

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
  tests:
    # a comment at two-space indent must be ignored
    runs-on: ubuntu-latest
  managed-ui-e2e:
    needs: [tests]
    runs-on: ubuntu-latest
"""


def ruleset_with(contexts: list[str]) -> dict[str, object]:
    return {
        "name": "main-protection",
        "rules": [
            {"type": "deletion"},
            {
                "type": "required_status_checks",
                "parameters": {"required_status_checks": [{"context": c} for c in contexts]},
            },
        ],
    }


class TestCiJobNames:
    def test_reads_only_top_level_job_keys(self) -> None:
        # push/group are two-space keys OUTSIDE the jobs block and must not leak in.
        assert crc.ci_job_names(CI_YML_SAMPLE) == {"validate", "tests", "managed-ui-e2e"}

    def test_no_jobs_block_returns_empty(self) -> None:
        assert crc.ci_job_names("name: CI\non:\n  push:\n") == set()


class TestRequiredContexts:
    def test_extracts_contexts(self) -> None:
        assert crc.required_contexts(ruleset_with(["validate", "tests"])) == {"validate", "tests"}

    def test_missing_rule_returns_empty(self) -> None:
        assert crc.required_contexts({"name": "x", "rules": [{"type": "deletion"}]}) == set()


class TestCheck:
    def test_in_sync_has_no_errors(self) -> None:
        ruleset = ruleset_with(["validate", "tests", "managed-ui-e2e"])
        assert crc.check(CI_YML_SAMPLE, ruleset) == []

    def test_context_without_job_is_flagged(self) -> None:
        ruleset = ruleset_with(["validate", "tests", "managed-ui-e2e", "renamed-job"])
        errors = crc.check(CI_YML_SAMPLE, ruleset)
        assert any("renamed-job" in e and "no matching job" in e for e in errors)

    def test_job_without_context_is_flagged(self) -> None:
        ruleset = ruleset_with(["validate", "tests"])  # missing managed-ui-e2e
        errors = crc.check(CI_YML_SAMPLE, ruleset)
        assert any("managed-ui-e2e" in e and "not a required status check" in e for e in errors)


class TestMain:
    def test_real_repo_files_are_in_sync(self) -> None:
        # The gate must pass against the actually checked-in files.
        assert crc.main([str(crc.CI_YML), str(crc.RULESET_JSON)]) == 0

    def test_defaults_to_repo_files(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert crc.main([]) == 0
        assert "required checks match" in capsys.readouterr().out

    def test_drift_returns_one(self, tmp_path: Path) -> None:
        ci = tmp_path / "ci.yml"
        ci.write_text("jobs:\n  validate:\n  tests:\n", encoding="utf-8")
        ruleset = tmp_path / "main.json"
        ruleset.write_text(json.dumps(ruleset_with(["validate", "ghost"])), encoding="utf-8")
        assert crc.main([str(ci), str(ruleset)]) == 1
