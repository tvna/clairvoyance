#!/usr/bin/env python3
"""Managed-server version-parity drift gate.

The managed coaching server carries its version in two places that must always
agree: the package manifest ``managed/pyproject.toml`` (`[project].version`) and
the FastAPI application factory in ``managed/app/main.py`` (the ``version=``
argument the running server reports at ``/openapi.json`` and ``/docs``). A hand
edit to one without the other ships a server whose advertised version disagrees
with its package, so this check fails CI when they drift.

This is the managed-product analogue of the plugin manifest-parity gate in
``.github/workflows/ci.yml``; see ``docs/versioning.md`` for the product-scoped
versioning model. Exit non-zero (loudly) on any drift or missing source.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "managed" / "pyproject.toml"
APP_MAIN = REPO_ROOT / "managed" / "app" / "main.py"

# The version handed to ``FastAPI(..., version="X.Y.Z")``. Anchored on the
# FastAPI constructor so an unrelated ``version=`` elsewhere cannot satisfy it;
# ``.*?`` (non-greedy, DOTALL) reaches the ``version=`` keyword across any other
# arguments -- including a ``title`` that itself contains parentheses or newlines
# -- while ``\b`` still keeps it from latching onto e.g. ``api_version=``.
_APP_VERSION = re.compile(r"FastAPI\(.*?\bversion\s*=\s*[\"']([^\"']+)[\"']", re.DOTALL)


def read_pyproject_version(path: Path) -> str:
    """Return ``[project].version`` from a pyproject.toml, or raise ValueError."""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    try:
        version = data["project"]["version"]
    except (KeyError, TypeError):
        raise ValueError(f"{path}: no [project].version found") from None
    if not isinstance(version, str):
        raise ValueError(f"{path}: [project].version is not a string")
    return version


def read_app_version(path: Path) -> str:
    """Return the version passed to FastAPI() in main.py, or raise ValueError."""
    match = _APP_VERSION.search(path.read_text(encoding="utf-8"))
    if match is None:
        raise ValueError(f"{path}: no FastAPI(version=...) found")
    return match.group(1)


def check(pyproject_path: Path = PYPROJECT, app_path: Path = APP_MAIN) -> tuple[bool, str]:
    """Compare the two managed version sources. Return (ok, human-readable message)."""
    pkg = read_pyproject_version(pyproject_path)
    app = read_app_version(app_path)
    if pkg != app:
        return False, f"managed version drift: pyproject={pkg} app={app}"
    return True, f"ok: managed version {pkg} matches across pyproject and app"


def main() -> int:
    try:
        ok, message = check()
    except (OSError, ValueError) as err:
        print(f"check_managed_version: {err}", file=sys.stderr)
        return 1
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
