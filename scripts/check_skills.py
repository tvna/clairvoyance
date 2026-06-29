#!/usr/bin/env python3
"""Deterministic best-practice checks for skills under ``plugin/skills/``.

Validates the mechanical subset of the Agent Skills best practices that needs no
LLM. For each ``SKILL.md`` it checks frontmatter presence, the ``name`` rules
(lowercase/hyphens, length, reserved words, directory match), the ``description``
(present, single-line, length, third person, no XML tags, and a when-to-use
trigger), the SKILL.md body length, and that relative links resolve, use forward
slashes, and do not traverse upward. For each bundled reference file it checks the
progressive-disclosure rules: references stay one level deep from SKILL.md, and a
reference longer than 100 lines carries a table of contents.

Emits GitHub Actions annotations and exits non-zero on any violation. Shared by
CI and the pre-commit hook. ``--summary`` prints a Markdown compliance table
(per-skill pass/fail) for the CI job summary so the deterministic state is always
visible on the latest run; see the source URLs below for the upstream rules.

Best-practice sources:
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- https://code.claude.com/docs/en/best-practices
"""

from __future__ import annotations

import io
import pathlib
import re
import sys
from typing import IO

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "plugin" / "skills"

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KEY_RE = re.compile(r"^([\w-]+):\s*(.*)$")
LINK_RE = re.compile(r"\]\(([^)]+)\)")
BLOCK_SCALAR_RE = re.compile(r"^[|>][+-]?$")
# An XML/HTML tag: '<' (optionally '/') immediately followed by a tag name, up
# to the next '>'. Anchored on a leading letter so spaced comparisons in prose
# ("a < b and c > d") are not misread as tags.
XML_TAG_RE = re.compile(r"</?[A-Za-z][^<>]*>")
# A when-to-use trigger: the docs require the description to say *when* to use the
# skill, and the repo convention spells it "Use when/on/to ...". Match that
# discovery clause so a description that only says *what* it does is flagged.
TRIGGER_RE = re.compile(r"\buse\s+(when|on|to|for|after|before|during|while|whenever|as|if|in)\b", re.IGNORECASE)
# A table-of-contents heading for long reference files.
TOC_RE = re.compile(r"(?im)^#{1,6}\s+(table of contents|contents)\b")
RESERVED_WORDS = ("anthropic", "claude")
NON_THIRD_PERSON = ("I can ", "You can ", "you can ")
MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_BODY_LINES = 500
MAX_REFERENCE_LINES = 100

CHECKS_BLURB = (
    "Checks applied per skill: frontmatter present; `name` lowercase/hyphens, "
    "within 64 chars, no reserved word, matches its directory; `description` "
    "present, single-line, within 1024 chars, third person, no XML tags, with a "
    "when-to-use trigger; SKILL.md body within 500 lines; body links resolve, "
    "use forward slashes, and never traverse upward; reference files stay one "
    "level deep and carry a table of contents past 100 lines."
)


def split_frontmatter(text: str) -> tuple[dict[str, str] | None, str]:
    """Return (frontmatter, body), or (None, text) when frontmatter is absent.

    ``Path.read_text`` normalises CRLF to LF (universal newlines), so a file
    saved with Windows line endings still starts with ``---\\n`` here.
    """
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        match = KEY_RE.match(line)
        if match:
            data[match.group(1)] = match.group(2).strip()
    return data, text[end + 4 :]


def _link_targets(text: str) -> list[tuple[str, str]]:
    """Return (raw, target) for each resolvable relative link in a markdown text.

    Strips any markdown title, ``#fragment``, or ``?query`` from the target and
    skips empty (anchor-only) and external (http/https/mailto) links, so callers
    only see local targets worth resolving."""
    pairs: list[tuple[str, str]] = []
    for raw in LINK_RE.findall(text):
        target = raw.strip().split(" ", 1)[0].split("#", 1)[0].split("?", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        pairs.append((raw, target))
    return pairs


def _scan_links(text: str, rel: pathlib.PurePath, base: pathlib.Path) -> list[tuple[str, str]]:
    """Return link violations for one markdown text: bad slashes, upward
    traversal, and unresolved relative targets (external/anchor links skipped)."""
    errors: list[tuple[str, str]] = []
    for raw, target in _link_targets(text):
        if "\\" in target:
            errors.append(("error", f"{rel}: link '{raw}' must use forward slashes, not backslashes"))
            continue
        if ".." in target:
            errors.append(("error", f"{rel}: link '{raw}' must not traverse upward"))
            continue
        if not (base / target).exists():
            errors.append(("error", f"{rel}: broken link '{raw}'"))
    return errors


def check_skill(skill_md: pathlib.Path) -> list[tuple[str, str]]:
    """Return a list of (level, message) violations for one SKILL.md."""
    rel = skill_md.relative_to(skill_md.parents[2])
    text = skill_md.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    if frontmatter is None:
        return [("error", f"{rel}: missing YAML frontmatter")]

    errors: list[tuple[str, str]] = []
    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")

    if not name:
        errors.append(("error", f"{rel}: frontmatter has no name"))
    else:
        if not NAME_RE.match(name):
            errors.append(("error", f"{rel}: name '{name}' must be lowercase letters, numbers, and hyphens"))
        if len(name) > MAX_NAME:
            errors.append(("error", f"{rel}: name exceeds {MAX_NAME} characters"))
        for word in RESERVED_WORDS:
            if word in name:
                errors.append(("error", f"{rel}: name must not contain reserved word '{word}'"))
        if name != skill_md.parent.name:
            errors.append(("error", f"{rel}: name '{name}' does not match directory '{skill_md.parent.name}'"))

    if not description:
        errors.append(("error", f"{rel}: frontmatter has no description"))
    elif BLOCK_SCALAR_RE.match(description):
        # A YAML block scalar ('>' / '|') can't be validated by this line-based
        # parser; require a single-line description instead of misparsing it.
        errors.append(("error", f"{rel}: description must be a single-line scalar, not a block scalar"))
    else:
        if len(description) > MAX_DESCRIPTION:
            errors.append(("error", f"{rel}: description exceeds {MAX_DESCRIPTION} characters"))
        for phrase in NON_THIRD_PERSON:
            if phrase in description:
                errors.append(("error", f"{rel}: description should be third-person (found '{phrase.strip()}')"))
        if XML_TAG_RE.search(description):
            errors.append(("error", f"{rel}: description must not contain XML tags"))
        if not TRIGGER_RE.search(description):
            errors.append(("error", f"{rel}: description should state when to use the skill (e.g. 'Use when ...')"))

    if len(body.strip().splitlines()) > MAX_BODY_LINES:
        errors.append(("error", f"{rel}: SKILL.md body exceeds {MAX_BODY_LINES} lines"))

    errors.extend(_scan_links(body, rel, skill_md.parent))
    return errors


def check_references(skill_md: pathlib.Path) -> list[tuple[str, str]]:
    """Return progressive-disclosure violations for a skill's bundled reference
    files: nested references (a reference linking to another markdown file) and
    long references that lack a table of contents."""
    errors: list[tuple[str, str]] = []
    rel_root = skill_md.parents[2]
    for ref in sorted(skill_md.parent.rglob("*.md")):
        if ref == skill_md:
            continue
        rel = ref.relative_to(rel_root)
        text = ref.read_text(encoding="utf-8")
        if len(text.splitlines()) > MAX_REFERENCE_LINES and not TOC_RE.search(text):
            errors.append(("error", f"{rel}: reference over {MAX_REFERENCE_LINES} lines needs a table of contents"))
        # References get the same slash/traversal/resolution checks as SKILL.md,
        # plus a one-level-deep rule: a reference must not link to another
        # markdown file (that would nest progressive disclosure two deep).
        errors.extend(_scan_links(text, rel, ref.parent))
        for raw, target in _link_targets(text):
            if target.endswith(".md"):
                errors.append(("error", f"{rel}: reference link '{raw}' must stay one level deep from SKILL.md"))
    return errors


def check_one(skill_md: pathlib.Path) -> list[tuple[str, str]]:
    """Return all violations for one skill: its SKILL.md and its references."""
    return check_skill(skill_md) + check_references(skill_md)


def check_all(skills_dir: pathlib.Path) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        errors.extend(check_one(skill_md))
    return errors


def build_summary(skills_dir: pathlib.Path) -> str:
    """Render a Markdown compliance table (per-skill pass/fail) for the CI job
    summary, so the deterministic state is always visible on the latest run."""
    rows: list[str] = []
    details: list[str] = []
    passing = 0
    total = 0
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        total += 1
        name = skill_md.parent.name
        errors = check_one(skill_md)
        if errors:
            rows.append(f"| `{name}` | ❌ fail | {len(errors)} |")
            details.extend(f"- {message}" for _, message in errors)
        else:
            passing += 1
            rows.append(f"| `{name}` | ✅ pass | — |")

    lines = [
        "## Skill best-practice compliance (deterministic)",
        "",
        CHECKS_BLURB,
        "",
        "| Skill | Status | Issues |",
        "| --- | --- | --- |",
        *rows,
        "",
        f"**{passing}/{total} skills pass** the deterministic best-practice checks.",
    ]
    if details:
        lines += ["", "<details><summary>Open issues</summary>", "", *details, "", "</details>"]
    return "\n".join(lines) + "\n"


def write_summary(skills_dir: pathlib.Path | None = None, stream: IO[str] | None = None) -> None:
    """Print the Markdown compliance table to ``stream`` (stdout by default)."""
    out = stream if stream is not None else sys.stdout
    print(build_summary(skills_dir if skills_dir is not None else SKILLS_DIR), file=out)


def main(skills_dir: pathlib.Path | None = None) -> int:
    errors = check_all(skills_dir if skills_dir is not None else SKILLS_DIR)
    for level, message in errors:
        print(f"::{level}::{message}", file=sys.stderr)
        print(f"{level.upper()}: {message}")
    if errors:
        return 1
    print("all skills pass best-practice checks")
    return 0


if __name__ == "__main__":
    # Emit UTF-8 regardless of the runner's locale: skills and their messages
    # carry non-ASCII (em dashes), and the summary uses ✅/❌ glyphs, so a C/POSIX
    # locale would otherwise raise UnicodeEncodeError on output.
    for _stream in (sys.stdout, sys.stderr):
        if isinstance(_stream, io.TextIOWrapper):
            _stream.reconfigure(encoding="utf-8")
    if "--summary" in sys.argv[1:]:
        write_summary()
        sys.exit(0)
    sys.exit(main())
