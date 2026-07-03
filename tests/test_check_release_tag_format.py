"""Tests for the product-prefixed release-tag-format drift gate.

The gate lives under ``scripts/`` (100%-coverage scope), so it is exercised
directly: ``check`` runs against tmp repo roots holding fixture configs, and
``main`` is driven through its success, failure, and error branches.
"""

import json

import check_release_tag_format as crtf


def _config(root, name, tag_format):
    root.joinpath(name).write_text(json.dumps({"tagFormat": tag_format}), encoding="utf-8")


def test_find_release_configs_sorted(tmp_path):
    _config(tmp_path, ".releaserc.managed.json", "managed-v${version}")
    _config(tmp_path, ".releaserc.json", "plugin-v${version}")
    names = [p.name for p in crtf.find_release_configs(tmp_path)]
    assert names == [".releaserc.json", ".releaserc.managed.json"]


def test_check_product_prefixed_ok(tmp_path):
    _config(tmp_path, ".releaserc.json", "plugin-v${version}")
    _config(tmp_path, ".releaserc.managed.json", "managed-v${version}")
    ok, message = crtf.check(tmp_path)
    assert ok is True
    assert "2 release config" in message


def test_check_rejects_bare_v(tmp_path):
    _config(tmp_path, ".releaserc.json", "v${version}")
    ok, message = crtf.check(tmp_path)
    assert ok is False
    assert "plugin" not in message
    assert "v${version}" in message


def test_check_rejects_missing_placeholder(tmp_path):
    _config(tmp_path, ".releaserc.json", "plugin-v1.0.0")
    ok, _ = crtf.check(tmp_path)
    assert ok is False


def test_check_no_config_is_error(tmp_path):
    ok, message = crtf.check(tmp_path)
    assert ok is False
    assert "no .releaserc" in message


def test_repo_config_is_product_prefixed():
    """The committed .releaserc.json must satisfy the gate it is checked by."""
    ok, _ = crtf.check()
    assert ok is True


def test_main_success(capsys):
    assert crtf.main() == 0
    assert "ok:" in capsys.readouterr().out


def test_main_reports_failure(monkeypatch, capsys):
    monkeypatch.setattr(crtf, "check", lambda: (False, "bad tagFormat"))
    assert crtf.main() == 1
    assert "bad tagFormat" in capsys.readouterr().out


def test_main_handles_error(monkeypatch, capsys):
    def _raise():
        raise ValueError("boom")

    monkeypatch.setattr(crtf, "check", _raise)
    assert crtf.main() == 1
    assert "boom" in capsys.readouterr().err
