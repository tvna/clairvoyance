"""Tests for ``scripts/check_no_inline_assert.py`` (the inline-assert drift gate)."""

from __future__ import annotations

from pathlib import Path

import check_no_inline_assert as cnia
import pytest


def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


class TestTargetFiles:
    def test_collects_sh_files(self, tmp_path: Path) -> None:
        write(tmp_path / "check.sh", "echo hi\n")
        assert cnia.target_files([tmp_path]) == [tmp_path / "check.sh"]

    def test_collects_run_hook_cmd_by_name(self, tmp_path: Path) -> None:
        write(tmp_path / "run-hook.cmd", "@echo off\n")
        assert cnia.target_files([tmp_path]) == [tmp_path / "run-hook.cmd"]

    def test_ignores_unrelated_extensions(self, tmp_path: Path) -> None:
        write(tmp_path / "manifest.json", "{}\n")
        write(tmp_path / "other.cmd", "@echo off\n")
        assert cnia.target_files([tmp_path]) == []

    def test_missing_directory_is_skipped(self, tmp_path: Path) -> None:
        assert cnia.target_files([tmp_path / "does-not-exist"]) == []

    def test_collects_from_nested_directories(self, tmp_path: Path) -> None:
        nested = tmp_path / "sub"
        nested.mkdir()
        write(nested / "deep.sh", "echo hi\n")
        assert cnia.target_files([tmp_path]) == [nested / "deep.sh"]

    def test_collects_yml_and_yaml_files(self, tmp_path: Path) -> None:
        write(tmp_path / "ci.yml", "jobs: {}\n")
        write(tmp_path / "ci.yaml", "jobs: {}\n")
        assert cnia.target_files([tmp_path]) == [tmp_path / "ci.yaml", tmp_path / "ci.yml"]


class TestFindViolations:
    def test_flags_assert_with_space(self, tmp_path: Path) -> None:
        script = write(tmp_path / "check.sh", 'python3 -c "assert True"\n')
        violations = cnia.find_violations([script])
        assert len(violations) == 1
        assert str(script) in violations[0]
        assert ":1:" in violations[0]

    def test_flags_assert_with_paren(self, tmp_path: Path) -> None:
        script = write(tmp_path / "check.sh", 'python3 -c "assert(True)"\n')
        assert len(cnia.find_violations([script])) == 1

    def test_flags_clustered_optimize_flag(self, tmp_path: Path) -> None:
        # `-Oc` strips assert exactly like `-O -c`, so it must be caught too
        # (this is the failure class the gate exists to prevent).
        script = write(tmp_path / "check.sh", 'python3 -Oc "assert False"\n')
        assert len(cnia.find_violations([script])) == 1

    def test_flags_windows_py_launcher(self, tmp_path: Path) -> None:
        script = write(tmp_path / "run-hook.cmd", 'py -c "assert False"\n')
        assert len(cnia.find_violations([script])) == 1

    def test_sys_exit_form_is_not_flagged(self, tmp_path: Path) -> None:
        script = write(tmp_path / "check.sh", 'python3 -c "sys.exit(0 if True else 1)"\n')
        assert cnia.find_violations([script]) == []

    def test_assert_without_python_c_is_not_flagged(self, tmp_path: Path) -> None:
        script = write(tmp_path / "check.sh", "# Assert the output shape is correct\n")
        assert cnia.find_violations([script]) == []

    def test_long_option_does_not_match_dash_c(self, tmp_path: Path) -> None:
        script = write(tmp_path / "check.sh", 'python3 --check "assert True"\n')
        assert cnia.find_violations([script]) == []

    def test_whole_line_comment_mentioning_both_phrases_is_not_flagged(self, tmp_path: Path) -> None:
        # A comment merely discussing the pattern must not itself be flagged.
        script = write(
            tmp_path / "check.sh",
            "# Don't run python3 -c here; assert(x) style checks belong elsewhere.\n",
        )
        assert cnia.find_violations([script]) == []

    def test_assert_before_python_c_on_same_line_is_not_flagged(self, tmp_path: Path) -> None:
        # assert must appear at or after the python -c invocation, not merely
        # anywhere on the same physical line.
        script = write(tmp_path / "check.sh", 'echo "assert" | python3 -c "sys.exit(0)"\n')
        assert cnia.find_violations([script]) == []

    def test_multiple_violations_across_files_and_lines(self, tmp_path: Path) -> None:
        first = write(tmp_path / "a.sh", 'echo start\npython3 -c "assert 1"\n')
        second = write(tmp_path / "b.sh", 'python3 -c "assert 2"\n')
        violations = cnia.find_violations([first, second])
        assert len(violations) == 2
        assert f"{first}:2:" in violations[0]
        assert f"{second}:1:" in violations[1]


class TestMain:
    def test_real_repo_is_clean(self) -> None:
        assert cnia.main([str(cnia.SCRIPTS_DIR), str(cnia.HOOKS_DIR), str(cnia.WORKFLOWS_DIR)]) == 0

    def test_defaults_to_repo_paths(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert cnia.main([]) == 0
        assert "ok:" in capsys.readouterr().out

    def test_no_args_uses_sys_argv(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["check_no_inline_assert.py"])
        assert cnia.main() == 0

    def test_violation_reports_path_and_fails(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        bad_scripts = tmp_path / "scripts"
        bad_scripts.mkdir()
        script = write(bad_scripts / "bad.sh", 'python3 -c "assert False"\n')
        empty_hooks = tmp_path / "hooks"
        empty_hooks.mkdir()
        empty_workflows = tmp_path / "workflows"
        empty_workflows.mkdir()
        assert cnia.main([str(bad_scripts), str(empty_hooks), str(empty_workflows)]) == 1
        out = capsys.readouterr().out
        assert str(script) in out
        assert "1 violation(s)" in out

    def test_violation_in_workflows_dir_is_caught(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        # Regression: a CI workflow's `run:` block is shell too, and must be
        # in scope alongside scripts/ and hooks/ (see docstring).
        empty_scripts = tmp_path / "scripts"
        empty_scripts.mkdir()
        empty_hooks = tmp_path / "hooks"
        empty_hooks.mkdir()
        workflows = tmp_path / "workflows"
        workflows.mkdir()
        workflow = write(workflows / "ci.yml", '        run: python3 -c "assert False"\n')
        assert cnia.main([str(empty_scripts), str(empty_hooks), str(workflows)]) == 1
        out = capsys.readouterr().out
        assert str(workflow) in out
