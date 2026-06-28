#!/usr/bin/env python3
"""Coverage gap gate: the harness form of the forward/backward sweeps.

Enforces the coverage matrix in ``docs/responsibility-matrix.md``:

* Forward sweep -- every skill under ``skills/`` is carried by an eval suite
  (``evals/<skill>/eval.yaml``) and named in at least one ``docs/*.md``.
* Backward sweep -- every eval suite under ``evals/`` maps to a real skill, so
  no eval directory is left orphaned by a skill rename or deletion.

Emits GitHub Actions annotations and exits non-zero on any gap. Pure stdlib so
it runs in the CI ``validate`` job without uv. The per-skill *structural* quality
(frontmatter, name rules, links) is a separate concern owned by
``scripts/check_skills.py``; this gate only checks cross-lane coverage.
"""

from __future__ import annotations

import pathlib
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


def check_all(root: pathlib.Path) -> list[tuple[str, str]]:
    """Return a list of (level, message) coverage gaps."""
    skills = list_skills(root)
    evals = set(list_evals(root))
    docs = docs_text(root)

    errors: list[tuple[str, str]] = []
    for name in skills:
        if name not in evals:
            errors.append(("error", f"skill '{name}' has no eval suite (evals/{name}/eval.yaml)"))
        if name not in docs:
            errors.append(("error", f"skill '{name}' is not documented in any docs/*.md"))

    skill_set = set(skills)
    for name in sorted(evals):
        if name not in skill_set:
            errors.append(("error", f"eval suite '{name}' has no matching skill (skills/{name}/SKILL.md)"))

    return errors


def main(root: pathlib.Path | None = None) -> int:
    errors = check_all(root if root is not None else REPO_ROOT)
    for level, message in errors:
        print(f"::{level}::{message}", file=sys.stderr)
        print(f"{level.upper()}: {message}")
    if errors:
        return 1
    print("all skills have eval + doc coverage; no orphan evals")
    return 0


if __name__ == "__main__":
    sys.exit(main())
