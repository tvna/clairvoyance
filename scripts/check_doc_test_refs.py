#!/usr/bin/env python3
"""Drift gate: every test name cited in docs/ must exist under tests/.

``docs/adaptive-coaching-longrun-test-plan.md`` cites specific ``test_*``
identifiers as the pinned proof for a behaviour (issue #98). Nothing tied
those citations to the actual test suite: a test gets renamed during a
conscious rewrite and the doc silently keeps citing a name that no longer
exists -- a reader can no longer find the pin. The same drift almost
recurred in PR #102. This is the docs-side analogue of the other
single-source-of-truth gates already in ``ci.yml``
(``check_ruleset_contexts.py``, ``check_managed_version.py``): the
invariant is enforced deterministically rather than by memory (CLAUDE.md
section 3).

Only ``docs/**/*.md`` is scanned. ``skills/`` and ``evals/`` are deliberately
excluded: ``skills/session-handoff/references/handoff-template.md`` cites a
fictional ``test_cache_expiry`` as a template example, and that must not fail
this gate.

A citation that intentionally names a retired test (e.g. "renamed from
``test_old_name``") is exempted by placing the literal marker
``<!-- former-test-name -->`` anywhere later on the same line, with no other
backticked span in between -- so the exemption attaches to that one
citation, not to every citation on the line (a line can carry both the live
name and the retired one it replaced). The marker was chosen over rewording
away from backticks or a "renamed from" text heuristic because it is
explicit and deterministic.

Stdlib only, so this runs in the CI ``validate`` job's system ``python3``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
TESTS_DIR = REPO_ROOT / "tests"

_BACKTICK_SPAN = re.compile(r"`[^`]*test_[a-z0-9_]+[^`]*`")
_TEST_TOKEN = re.compile(r"test_[a-z0-9_]+")
_TEST_DEF = re.compile(r"^\s*(?:async\s+)?def (test_[a-z0-9_]+)")
# Ties the `<!-- former-test-name -->` marker to the single backtick span
# immediately before it (no other backtick in between), not the whole line.
_FORMER_SPAN = re.compile(r"(`[^`]*test_[a-z0-9_]+[^`]*`)(?:(?!`).)*<!-- former-test-name -->")


def known_test_names(tests_dir: Path) -> set[str]:
    """Return every real test identifier: function names and file stems."""
    names: set[str] = set()
    for path in sorted(tests_dir.rglob("test_*.py")):
        names.add(path.stem)
        for line in path.read_text(encoding="utf-8").splitlines():
            match = _TEST_DEF.match(line)
            if match:
                names.add(match.group(1))
    return names


def cited_names(doc_path: Path) -> list[tuple[int, str]]:
    """Return (line number, cited test name) for every backticked citation.

    A citation whose span is exempted by an adjacent `<!-- former-test-name
    -->` marker is skipped; other citations on the same line are still
    checked.
    """
    citations: list[tuple[int, str]] = []
    for lineno, line in enumerate(doc_path.read_text(encoding="utf-8").splitlines(), start=1):
        exempt_starts = {match.start(1) for match in _FORMER_SPAN.finditer(line)}
        for span in _BACKTICK_SPAN.finditer(line):
            if span.start() in exempt_starts:
                continue
            citations.extend((lineno, token) for token in _TEST_TOKEN.findall(span.group()))
    return citations


def check(doc_files: list[Path], known: set[str]) -> list[str]:
    """Return human-readable drift errors; empty means every citation resolves."""
    errors: list[str] = []
    for doc_path in doc_files:
        for lineno, name in cited_names(doc_path):
            if name not in known:
                errors.append(f"{doc_path}:{lineno}: cites unknown test '{name}' (renamed or removed?)")
    return errors


def main(argv: list[str] | None = None) -> int:
    docs_dir, tests_dir = _paths(argv)
    doc_files = sorted(docs_dir.rglob("*.md"))
    known = known_test_names(tests_dir)
    errors = check(doc_files, known)
    if errors:
        for error in errors:
            print(f"::error::{error}")
        print(f"Doc test-ref drift: {len(errors)} unknown citation(s) under {docs_dir}.")
        return 1
    print(f"ok: every test citation under {docs_dir} exists in {tests_dir}")
    return 0


def _paths(argv: list[str] | None) -> tuple[Path, Path]:
    args = list(sys.argv[1:] if argv is None else argv)
    docs_dir = Path(args[0]) if len(args) > 0 else DOCS_DIR
    tests_dir = Path(args[1]) if len(args) > 1 else TESTS_DIR
    return docs_dir, tests_dir


if __name__ == "__main__":
    sys.exit(main())
