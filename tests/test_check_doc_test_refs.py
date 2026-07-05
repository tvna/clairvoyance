"""Tests for ``scripts/check_doc_test_refs.py`` (the doc test-ref drift gate)."""

from __future__ import annotations

from pathlib import Path

import check_doc_test_refs as cdtr
import pytest


def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


class TestKnownTestNames:
    def test_collects_function_names_and_file_stems(self, tmp_path: Path) -> None:
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        write(
            tests_dir / "test_store.py",
            "def test_one():\n    pass\n\n\ndef test_two():\n    pass\n",
        )
        assert cdtr.known_test_names(tests_dir) == {"test_store", "test_one", "test_two"}

    def test_non_test_files_are_ignored(self, tmp_path: Path) -> None:
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        write(tests_dir / "conftest.py", "def test_hidden():\n    pass\n")
        assert cdtr.known_test_names(tests_dir) == set()


class TestCitedNames:
    def test_extracts_backticked_test_names(self, tmp_path: Path) -> None:
        doc = write(tmp_path / "plan.md", "pinned by `test_readiness_holds`.\n")
        assert cdtr.cited_names(doc) == [(1, "test_readiness_holds")]

    def test_extracts_file_stem_from_path_citation(self, tmp_path: Path) -> None:
        doc = write(tmp_path / "plan.md", "unit-covered in `tests/test_adaptive_store.py`.\n")
        assert cdtr.cited_names(doc) == [(1, "test_adaptive_store")]

    def test_multiple_citations_on_one_line(self, tmp_path: Path) -> None:
        doc = write(tmp_path / "plan.md", "see `test_alpha` and `test_beta` too.\n")
        assert cdtr.cited_names(doc) == [(1, "test_alpha"), (1, "test_beta")]

    def test_marked_line_is_skipped(self, tmp_path: Path) -> None:
        doc = write(
            tmp_path / "plan.md",
            "renamed from `test_old_name` <!-- former-test-name -->\n",
        )
        assert cdtr.cited_names(doc) == []

    def test_line_without_backticks_is_ignored(self, tmp_path: Path) -> None:
        doc = write(tmp_path / "plan.md", "no citation here at all.\n")
        assert cdtr.cited_names(doc) == []


class TestCheck:
    def test_known_citations_have_no_errors(self, tmp_path: Path) -> None:
        doc = write(tmp_path / "plan.md", "pinned by `test_alpha`.\n")
        assert cdtr.check([doc], {"test_alpha"}) == []

    def test_unknown_citation_is_flagged(self, tmp_path: Path) -> None:
        doc = write(tmp_path / "plan.md", "pinned by `test_ghost`.\n")
        errors = cdtr.check([doc], {"test_alpha"})
        assert len(errors) == 1
        assert "test_ghost" in errors[0]
        assert str(doc) in errors[0]
        assert ":1:" in errors[0]


class TestMain:
    def test_real_repo_docs_are_in_sync(self) -> None:
        # The gate must pass against the actually checked-in docs and tests.
        assert cdtr.main([str(cdtr.DOCS_DIR), str(cdtr.TESTS_DIR)]) == 0

    def test_defaults_to_repo_paths(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert cdtr.main([]) == 0
        assert "ok:" in capsys.readouterr().out

    def test_drift_returns_one(self, tmp_path: Path) -> None:
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        write(docs_dir / "plan.md", "pinned by `test_ghost`.\n")
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        write(tests_dir / "test_real.py", "def test_alpha():\n    pass\n")
        assert cdtr.main([str(docs_dir), str(tests_dir)]) == 1

    def test_empty_docs_dir_passes(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        assert cdtr.main([str(docs_dir), str(tests_dir)]) == 0
        assert "ok:" in capsys.readouterr().out
