import check_skills as cs


def _skill(tmp_path, dirname, name="ok", description="Does a thing. Use when needed.", body="# Body\n", extra_fm=""):
    d = tmp_path / "skills" / dirname
    d.mkdir(parents=True)
    fm = f"name: {name}\ndescription: {description}\n{extra_fm}"
    (d / "SKILL.md").write_text(f"---\n{fm}---\n\n{body}")
    return d / "SKILL.md"


def _errors(tmp_path):
    return cs.check_all(tmp_path / "skills")


def test_valid_skill_passes(tmp_path):
    _skill(tmp_path, "ok")
    assert _errors(tmp_path) == []


def test_missing_frontmatter(tmp_path):
    d = tmp_path / "skills" / "nofm"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("# No frontmatter here\n")
    assert any("missing YAML frontmatter" in m for _, m in _errors(tmp_path))


def test_malformed_frontmatter_no_close(tmp_path):
    d = tmp_path / "skills" / "bad"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("---\nname: bad\nno closing fence\n")
    assert any("missing YAML frontmatter" in m for _, m in _errors(tmp_path))


def test_non_key_frontmatter_line_is_ignored(tmp_path):
    _skill(tmp_path, "ok", extra_fm="\n")  # blank line in frontmatter
    assert _errors(tmp_path) == []


def test_missing_name(tmp_path):
    _skill(tmp_path, "x", name="")
    assert any("has no name" in m for _, m in _errors(tmp_path))


def test_bad_name_characters(tmp_path):
    _skill(tmp_path, "Bad_Name", name="Bad_Name")
    assert any("lowercase letters" in m for _, m in _errors(tmp_path))


def test_name_too_long(tmp_path):
    long = "a" * 65
    _skill(tmp_path, long, name=long)
    assert any("exceeds 64 characters" in m for _, m in _errors(tmp_path))


def test_reserved_word_in_name(tmp_path):
    _skill(tmp_path, "claude-helper", name="claude-helper")
    assert any("reserved word 'claude'" in m for _, m in _errors(tmp_path))


def test_name_directory_mismatch(tmp_path):
    _skill(tmp_path, "dirname", name="othername")
    assert any("does not match directory" in m for _, m in _errors(tmp_path))


def test_missing_description(tmp_path):
    _skill(tmp_path, "ok", description="")
    assert any("has no description" in m for _, m in _errors(tmp_path))


def test_description_too_long(tmp_path):
    _skill(tmp_path, "ok", description="x" * 1025)
    assert any("description exceeds 1024" in m for _, m in _errors(tmp_path))


def test_description_not_third_person(tmp_path):
    _skill(tmp_path, "ok", description="You can use this to do a thing.")
    assert any("third-person" in m for _, m in _errors(tmp_path))


def test_body_too_long(tmp_path):
    _skill(tmp_path, "ok", body="content\n" * 501)
    assert any("body exceeds 500 lines" in m for _, m in _errors(tmp_path))


def test_body_at_limit_passes(tmp_path):
    _skill(tmp_path, "ok", body="content\n" * 500)
    assert _errors(tmp_path) == []


def test_broken_link(tmp_path):
    _skill(tmp_path, "ok", body="See [x](references/missing.md).\n")
    assert any("broken link" in m for _, m in _errors(tmp_path))


def test_upward_link(tmp_path):
    _skill(tmp_path, "ok", body="See [x](../escape.md).\n")
    assert any("must not traverse upward" in m for _, m in _errors(tmp_path))


def test_external_and_anchor_links_are_skipped(tmp_path):
    _skill(tmp_path, "ok", body="See [a](https://example.com) and [b](#section).\n")
    assert _errors(tmp_path) == []


def test_resolving_link_passes(tmp_path):
    md = _skill(tmp_path, "ok", body="See [t](references/t.md).\n")
    refs = md.parent / "references"
    refs.mkdir()
    (refs / "t.md").write_text("# ref\n")
    assert _errors(tmp_path) == []


def test_committed_skills_pass():
    assert cs.main() == 0


def test_main_returns_one_on_violation(tmp_path, capsys):
    _skill(tmp_path, "x", name="")
    assert cs.main(tmp_path / "skills") == 1
    assert "ERROR" in capsys.readouterr().out


def test_main_returns_zero_when_clean(tmp_path, capsys):
    _skill(tmp_path, "ok")
    assert cs.main(tmp_path / "skills") == 0
    assert "all skills pass" in capsys.readouterr().out


def test_crlf_frontmatter_is_accepted(tmp_path):
    # Path.read_text normalises CRLF -> LF, so Windows-authored files are fine.
    d = tmp_path / "skills" / "ok"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_bytes(
        b"---\r\nname: ok\r\ndescription: Does a thing. Use when needed.\r\n---\r\n\r\n# Body\r\n"
    )
    assert _errors(tmp_path) == []


def test_block_scalar_description_is_flagged(tmp_path):
    _skill(tmp_path, "ok", description=">")
    assert any("single-line scalar" in m for _, m in _errors(tmp_path))


def test_hyphenated_frontmatter_key_does_not_break_parsing(tmp_path):
    _skill(tmp_path, "ok", extra_fm="allowed-tools: Read\n")
    assert _errors(tmp_path) == []


def test_link_like_text_in_description_is_not_flagged(tmp_path):
    # Links are scanned in the body only, never the frontmatter description.
    _skill(tmp_path, "ok", description="Handles markdown ](x.md) syntax. Use when needed.")
    assert _errors(tmp_path) == []


def test_fragment_link_to_existing_file_resolves(tmp_path):
    md = _skill(tmp_path, "ok", body="See [t](references/t.md#section).\n")
    (md.parent / "references").mkdir()
    (md.parent / "references/t.md").write_text("x")
    assert _errors(tmp_path) == []


def test_link_with_title_resolves(tmp_path):
    md = _skill(tmp_path, "ok", body='See [t](references/t.md "Title").\n')
    (md.parent / "references").mkdir()
    (md.parent / "references/t.md").write_text("x")
    assert _errors(tmp_path) == []


def test_mailto_link_is_skipped(tmp_path):
    _skill(tmp_path, "ok", body="Contact [m](mailto:a@b.com).\n")
    assert _errors(tmp_path) == []
