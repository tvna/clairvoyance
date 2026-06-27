import json

import check_version_consistency as cvc


def _write_repo(tmp_path, plugin="1.0.0", market=None, manifest=None, vtxt=None):
    market = plugin if market is None else market
    manifest = plugin if manifest is None else manifest
    vtxt = plugin if vtxt is None else vtxt
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin/plugin.json").write_text(json.dumps({"version": plugin}))
    (tmp_path / ".claude-plugin/marketplace.json").write_text(json.dumps({"plugins": [{"version": market}]}))
    (tmp_path / ".release-please-manifest.json").write_text(json.dumps({".": manifest}))
    (tmp_path / "version.txt").write_text(vtxt + "\n")
    return tmp_path


def test_read_versions_parses_all_files(tmp_path):
    _write_repo(tmp_path, plugin="1.2.3")
    assert cvc.read_versions(tmp_path) == {
        "plugin.json": "1.2.3",
        "marketplace.json": "1.2.3",
        ".release-please-manifest.json": "1.2.3",
        "version.txt": "1.2.3",
    }


def test_consistent_versions_have_no_mismatches(tmp_path):
    _write_repo(tmp_path, plugin="1.0.0")
    assert cvc.find_mismatches(cvc.read_versions(tmp_path)) == []


def test_drift_is_reported(tmp_path):
    _write_repo(tmp_path, plugin="1.0.0", market="0.9.0", vtxt="1.0.1")
    mismatches = cvc.find_mismatches(cvc.read_versions(tmp_path))
    assert len(mismatches) == 2
    assert any("marketplace.json=0.9.0" in m for m in mismatches)
    assert any("version.txt=1.0.1" in m for m in mismatches)


def test_main_returns_zero_when_consistent(tmp_path, capsys):
    _write_repo(tmp_path, plugin="2.0.0")
    assert cvc.main(tmp_path) == 0
    assert "versions agree: 2.0.0" in capsys.readouterr().out


def test_main_returns_one_on_drift(tmp_path, capsys):
    _write_repo(tmp_path, plugin="1.0.0", manifest="9.9.9")
    assert cvc.main(tmp_path) == 1
    out = capsys.readouterr().out
    assert "version mismatch" in out
    assert ".release-please-manifest.json=9.9.9" in out


def test_committed_repo_is_consistent():
    # The repository itself must always be self-consistent.
    assert cvc.main(cvc.REPO_ROOT) == 0
