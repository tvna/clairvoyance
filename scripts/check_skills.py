#!/usr/bin/env python3
"""Deterministic best-practice checks for skills under ``skills/``.

Validates the mechanical subset of the Agent Skills best practices that needs no
LLM: frontmatter presence, the ``name`` rules (lowercase/hyphens, length,
reserved words, directory match), the ``description`` (present, length, third
person), the SKILL.md body length, and that relative links resolve and do not
traverse upward. Emits GitHub Actions annotations and exits non-zero on any
violation. Shared by CI and the pre-commit hook so the rule lives once.
"""
from __future__ import annotations

import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KEY_RE = re.compile(r"^(\w+):\s*(.*)$")
LINK_RE = re.compile(r"\]\(([^)]+)\)")
RESERVED_WORDS = ("anthropic", "claude")
NON_THIRD_PERSON = ("I can ", "You can ", "you can ")
MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_BODY_LINES = 500


def split_frontmatter(text: str) -> tuple[dict[str, str] | None, str]:
    """Return (frontmatter, body), or (None, text) when frontmatter is absent."""
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
    return data, text[end + 4:]


def check_skill(skill_md: pathlib.Path) -> list[tuple[str, str]]:
    """Return a list of (level, message) violations for one SKILL.md."""
    rel = skill_md.relative_to(skill_md.parents[2])
    text = skill_md.read_text()
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
    else:
        if len(description) > MAX_DESCRIPTION:
            errors.append(("error", f"{rel}: description exceeds {MAX_DESCRIPTION} characters"))
        for phrase in NON_THIRD_PERSON:
            if phrase in description:
                errors.append(("error", f"{rel}: description should be third-person (found '{phrase.strip()}')"))

    if body.count("\n") > MAX_BODY_LINES:
        errors.append(("error", f"{rel}: SKILL.md body exceeds {MAX_BODY_LINES} lines"))

    for target in LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "#")):
            continue
        if ".." in target:
            errors.append(("error", f"{rel}: link '{target}' must not traverse upward"))
            continue
        if not (skill_md.parent / target).exists():
            errors.append(("error", f"{rel}: broken link '{target}'"))

    return errors


def check_all(skills_dir: pathlib.Path) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        errors.extend(check_skill(skill_md))
    return errors


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
    sys.exit(main())
