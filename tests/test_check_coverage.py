import check_coverage as cc


def _skill(tmp_path, name, body="# Body\n"):
    d = tmp_path / "skills" / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: x\n---\n\n{body}")


def _eval(tmp_path, name):
    d = tmp_path / "evals" / name
    d.mkdir(parents=True)
    (d / "eval.yaml").write_text("name: x\n")


def _doc(tmp_path, text):
    d = tmp_path / "docs"
    d.mkdir(parents=True, exist_ok=True)
    (d / "skills.md").write_text(text)


def _errors(tmp_path):
    return cc.check_all(tmp_path)


def test_full_coverage_passes(tmp_path):
    _skill(tmp_path, "alpha")
    _eval(tmp_path, "alpha")
    _doc(tmp_path, "The alpha skill does things.\n")
    assert _errors(tmp_path) == []


def test_missing_eval_is_flagged(tmp_path):
    _skill(tmp_path, "alpha")
    _doc(tmp_path, "alpha\n")
    assert any("has no eval suite" in m for _, m in _errors(tmp_path))


def test_missing_doc_mention_is_flagged(tmp_path):
    _skill(tmp_path, "alpha")
    _eval(tmp_path, "alpha")
    _doc(tmp_path, "unrelated text\n")
    assert any("not documented" in m for _, m in _errors(tmp_path))


def test_orphan_eval_is_flagged(tmp_path):
    _eval(tmp_path, "ghost")
    _doc(tmp_path, "nothing here\n")
    assert any("eval suite 'ghost' has no matching skill" in m for _, m in _errors(tmp_path))


def test_no_docs_directory_flags_undocumented(tmp_path):
    _skill(tmp_path, "alpha")
    _eval(tmp_path, "alpha")
    # No docs/ at all: docs_text returns "" and the skill is undocumented.
    assert any("not documented" in m for _, m in _errors(tmp_path))


def test_list_helpers(tmp_path):
    _skill(tmp_path, "beta")
    _skill(tmp_path, "alpha")
    _eval(tmp_path, "alpha")
    assert cc.list_skills(tmp_path) == ["alpha", "beta"]
    assert cc.list_evals(tmp_path) == ["alpha"]


def test_committed_repo_passes():
    assert cc.main() == 0


def test_main_returns_one_on_gap(tmp_path, capsys):
    _eval(tmp_path, "ghost")
    assert cc.main(tmp_path) == 1
    assert "ERROR" in capsys.readouterr().out


def test_main_returns_zero_when_clean(tmp_path, capsys):
    _skill(tmp_path, "alpha")
    _eval(tmp_path, "alpha")
    _doc(tmp_path, "alpha\n")
    assert cc.main(tmp_path) == 0
    assert "no orphan evals" in capsys.readouterr().out
