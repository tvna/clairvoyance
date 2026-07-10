#!/usr/bin/env python3
"""Drift gate: no ``assert`` in shell-invoked ``python -c`` validation.

``assert`` is stripped under ``python3 -O`` / ``PYTHONOPTIMIZE``, so a shell
script that validates something via ``python3 -c "...assert...; ..."``
silently turns into a no-op under an optimized interpreter and lets CI stay
green while the check it was meant to enforce never runs. This exact failure
happened in ``scripts/check_hooks.sh`` during PR #120 (issue #121, "green
gate, wrong shape") and was repaired by switching to ``sys.exit(...)``. This
script generalizes that repair into a permanent, repo-wide gate: no
shell-invoked ``python -c`` line under ``scripts/`` or ``hooks/`` may use
``assert`` for validation.

Detection is line-based: a physical line must contain both a
``python``/``python3 ... -c`` invocation and a word-boundary ``assert``
(``assert `` or ``assert(``) to be flagged. Known trade-offs (YAGNI for a
first version):

- A ``python3 -c`` invocation whose heredoc body spans multiple physical
  lines, with the ``assert`` on a different line than the ``-c``, is not
  caught. No such multi-line form exists in this repo today; catching it
  would require logical-line reconstruction.
- A line containing the literal substring "assert" inside an unrelated
  string (not a validation assertion) on the same line as a ``python -c``
  invocation is a false positive. Not addressed in v1; an inline
  allow-comment convention can be added if this bites.

Stdlib only, mirroring ``check_doc_test_refs.py`` and
``check_managed_version.py``.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
HOOKS_DIR = REPO_ROOT / "hooks"

# Files matching this suffix, or this exact name, are shell-invoked python
# hosts in scope for this gate. Kept as data (suffix + allow-listed name)
# rather than an enumeration of specific files, so scope grows with the
# directories scanned, not with special-cased branches.
_TARGET_SUFFIX = ".sh"
_TARGET_NAMES = {"run-hook.cmd"}

# `python3 ... -c` invocation, including single-dash clusters like `-Oc` /
# `-Ic` (Python treats `-c` as ending the cluster and consuming the rest of
# the line as the command, so `-Oc "assert ..."` runs under `-O` exactly
# like `-O -c "assert ..."` -- and strips the assert). `[^\n]*\s-[A-Za-z]*c\b`
# lets other single-letter flags precede the `c`, while the trailing `\b`
# keeps a long option like `--check` from matching (the `c` there is
# immediately followed by the word-char `h`, so no boundary).
_PYTHON_C = re.compile(r"\bpython3?\b[^\n]*\s-[A-Za-z]*c\b")
# `assert ` or `assert(` used as a validation call, not as a substring of a
# longer identifier.
_ASSERT = re.compile(r"\bassert[\s(]")


def target_files(dirs: Iterable[Path]) -> list[Path]:
    """Return shell-invoked python host files under the given directories."""
    files: list[Path] = []
    for directory in dirs:
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_file() and (path.suffix == _TARGET_SUFFIX or path.name in _TARGET_NAMES):
                files.append(path)
    return files


def find_violations(files: Iterable[Path]) -> list[str]:
    """Return human-readable violations: lines using assert inside python -c."""
    violations: list[str] = []
    for path in files:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if _PYTHON_C.search(line) and _ASSERT.search(line):
                violations.append(
                    f"{path}:{lineno}: inline `assert` inside `python -c` is stripped under "
                    "`python3 -O` / PYTHONOPTIMIZE; use `sys.exit(...)` or `raise SystemExit` instead"
                )
    return violations


def _dirs(argv: list[str] | None) -> tuple[Path, Path]:
    args = list(sys.argv[1:] if argv is None else argv)
    scripts_dir = Path(args[0]) if len(args) > 0 else SCRIPTS_DIR
    hooks_dir = Path(args[1]) if len(args) > 1 else HOOKS_DIR
    return scripts_dir, hooks_dir


def main(argv: list[str] | None = None) -> int:
    scripts_dir, hooks_dir = _dirs(argv)
    violations = find_violations(target_files([scripts_dir, hooks_dir]))
    if violations:
        for violation in violations:
            print(f"::error::{violation}")
        print(f"inline-assert gate: {len(violations)} violation(s) under {scripts_dir}, {hooks_dir}.")
        return 1
    print(f"ok: no inline assert in python -c invocations under {scripts_dir}, {hooks_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
