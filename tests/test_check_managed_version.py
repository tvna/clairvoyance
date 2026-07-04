"""Tests for the managed-server version-parity drift gate.

The gate is a plain Python module under ``scripts/`` (inside the 100%-coverage
scope), so it is exercised directly rather than through a subprocess: the pure
read/compare functions run against tmp fixtures, and ``main`` is driven through
its success, drift, and error branches by substituting the ``check`` it calls.
"""

import check_managed_version as cmv
import pytest


def _write(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def test_read_pyproject_version_ok(tmp_path):
    p = _write(tmp_path / "pyproject.toml", '[project]\nname = "x"\nversion = "1.2.3"\n')
    assert cmv.read_pyproject_version(p) == "1.2.3"


def test_read_pyproject_version_missing(tmp_path):
    p = _write(tmp_path / "pyproject.toml", "[tool.ruff]\nline-length = 120\n")
    with pytest.raises(ValueError, match=r"no \[project\].version"):
        cmv.read_pyproject_version(p)


def test_read_pyproject_version_not_a_string(tmp_path):
    p = _write(tmp_path / "pyproject.toml", "[project]\nversion = 1\n")
    with pytest.raises(ValueError, match="not a string"):
        cmv.read_pyproject_version(p)


def test_read_app_version_ok(tmp_path):
    p = _write(tmp_path / "main.py", 'app = FastAPI(title="Srv", version="4.5.6")\n')
    assert cmv.read_app_version(p) == "4.5.6"


def test_read_app_version_tolerates_parens_and_newlines(tmp_path):
    # A title containing ')' before version=, and a multi-line call, must not
    # break the match -- the version did not change, so the gate must not fail.
    p = _write(
        tmp_path / "main.py",
        'app = FastAPI(\n    title="Clairvoyance Server (managed)",\n    version="7.8.9",\n)\n',
    )
    assert cmv.read_app_version(p) == "7.8.9"


def test_read_app_version_ignores_unrelated_version_kwarg(tmp_path):
    # \b keeps the match off api_version=; it must pick the real version=.
    p = _write(tmp_path / "main.py", 'FastAPI(api_version="1", version="2.0.0")\n')
    assert cmv.read_app_version(p) == "2.0.0"


def test_read_app_version_missing(tmp_path):
    p = _write(tmp_path / "main.py", "app = FastAPI(title='Srv')\n")
    with pytest.raises(ValueError, match="no FastAPI"):
        cmv.read_app_version(p)


def test_check_match(tmp_path):
    py = _write(tmp_path / "pyproject.toml", '[project]\nversion = "0.1.0"\n')
    app = _write(tmp_path / "main.py", 'FastAPI(title="s", version="0.1.0")\n')
    ok, message = cmv.check(py, app)
    assert ok is True
    assert "0.1.0" in message


def test_check_drift(tmp_path):
    py = _write(tmp_path / "pyproject.toml", '[project]\nversion = "0.1.0"\n')
    app = _write(tmp_path / "main.py", 'FastAPI(title="s", version="0.2.0")\n')
    ok, message = cmv.check(py, app)
    assert ok is False
    assert "drift" in message


def test_repo_sources_are_in_parity():
    """The real managed sources must agree; this is the invariant CI enforces."""
    ok, _ = cmv.check()
    assert ok is True


def test_main_success(capsys):
    assert cmv.main() == 0
    assert "ok:" in capsys.readouterr().out


def test_main_reports_drift(monkeypatch, capsys):
    monkeypatch.setattr(cmv, "check", lambda: (False, "managed version drift: a b"))
    assert cmv.main() == 1
    assert "drift" in capsys.readouterr().out


def test_main_handles_missing_source(monkeypatch, capsys):
    def _raise():
        raise ValueError("boom")

    monkeypatch.setattr(cmv, "check", _raise)
    assert cmv.main() == 1
    assert "boom" in capsys.readouterr().err
