#!/usr/bin/env python3
"""Coverage gap gate: the harness form of the forward/backward sweeps.

Enforces the coverage matrix in ``docs/responsibility-matrix.md``:

* Forward sweep -- every skill under ``skills/`` is carried by an eval
  suite (``evals/<skill>/eval.yaml``), named in at least one ``docs/*.md``,
  and listed in ``README.md`` (the canonical skill table a marketplace user
  reads first; translated READMEs are best-effort and not gated).
* Backward sweep -- every eval suite under ``evals/`` maps to a real skill,
  so no eval directory is left orphaned by a skill rename or deletion.
* Banned lanes -- the Claude Code rules lane (``.claude/rules/``) is banned in
  this repository by operator decision: the SessionStart hook and the skills
  are the only instruction carriers, so constraints must not fork into a lane
  that loads outside them.

Emits GitHub Actions annotations and exits non-zero on any gap. Pure stdlib so
it runs in the CI ``validate`` job without uv. The per-skill *structural* quality
(frontmatter, name rules, links) is a separate concern owned by
``scripts/check_skills.py``; this gate only checks cross-lane coverage.
"""

from __future__ import annotations

import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def list_skills(root: pathlib.Path) -> list[str]:
    """Return the directory name of every skill that has a SKILL.md."""
    return sorted(p.parent.name for p in root.glob("skills/*/SKILL.md"))


def list_evals(root: pathlib.Path) -> list[str]:
    """Return the directory name of every eval suite that has an eval.yaml."""
    return sorted(p.parent.name for p in root.glob("evals/*/eval.yaml"))


def docs_text(root: pathlib.Path) -> str:
    """Return the concatenated text of every repo-local doc."""
    return "".join(p.read_text() for p in sorted(root.glob("docs/*.md")))


def readme_text(root: pathlib.Path) -> str:
    """Return the text of the canonical README.md, or "" when absent."""
    readme = root / "README.md"
    return readme.read_text() if readme.exists() else ""


def readme_lists(readme: str, name: str) -> bool:
    """Return whether the README skill table carries a row for ``name``.

    Matches an exact backticked skill cell at the start of a table row, not a
    raw substring: ``clairvoyance`` appearing inside ``using-clairvoyance`` (or
    in prose) must not satisfy the gate for the ``clairvoyance`` row.
    """
    return bool(re.search(rf"(?m)^\|\s*`{re.escape(name)}`\s*\|", readme))


def check_all(root: pathlib.Path) -> list[tuple[str, str]]:
    """Return a list of (level, message) coverage gaps."""
    skills = list_skills(root)
    evals = set(list_evals(root))
    docs = docs_text(root)
    readme = readme_text(root)

    errors: list[tuple[str, str]] = []
    for name in skills:
        if name not in evals:
            errors.append(("error", f"skill '{name}' has no eval suite (evals/{name}/eval.yaml)"))
        if name not in docs:
            errors.append(("error", f"skill '{name}' is not documented in any docs/*.md"))
        if not readme_lists(readme, name):
            errors.append(("error", f"skill '{name}' is not listed in the README.md skill table"))

    skill_set = set(skills)
    for name in sorted(evals):
        if name not in skill_set:
            errors.append(("error", f"eval suite '{name}' has no matching skill (skills/{name}/SKILL.md)"))

    if (root / ".claude" / "rules").exists():
        errors.append(
            (
                "error",
                ".claude/rules/ is banned in this repository: keep constraints in the "
                "SessionStart hook or the skills, not the rules lane",
            )
        )

    return errors


def main(root: pathlib.Path | None = None) -> int:
    errors = check_all(root if root is not None else REPO_ROOT)
    for level, message in errors:
        print(f"::{level}::{message}", file=sys.stderr)
        print(f"{level.upper()}: {message}")
    if errors:
        return 1
    print("all skills have eval + doc + README coverage; no orphan evals")
    return 0


if __name__ == "__main__":
    sys.exit(main())
