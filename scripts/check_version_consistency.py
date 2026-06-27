#!/usr/bin/env python3
"""Fail if the version-bearing files disagree.

`.claude-plugin/plugin.json` is the single source of truth; Release Please keeps
the others in sync. Shared by CI and the pre-commit hook so the rule lives once.
"""
from __future__ import annotations

import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def read_versions(root: pathlib.Path) -> dict[str, str]:
    """Return the version recorded in each version-bearing file."""
    return {
        "plugin.json": json.loads(
            (root / ".claude-plugin/plugin.json").read_text()
        )["version"],
        "marketplace.json": json.loads(
            (root / ".claude-plugin/marketplace.json").read_text()
        )["plugins"][0]["version"],
        ".release-please-manifest.json": json.loads(
            (root / ".release-please-manifest.json").read_text()
        )["."],
        "version.txt": (root / "version.txt").read_text().strip(),
    }


def find_mismatches(versions: dict[str, str]) -> list[str]:
    """Return one message per file whose version differs from plugin.json."""
    source = versions["plugin.json"]
    return [
        f"{name}={value} != plugin.json={source}"
        for name, value in versions.items()
        if name != "plugin.json" and value != source
    ]


def main(root: pathlib.Path | None = None) -> int:
    versions = read_versions(root if root is not None else REPO_ROOT)
    mismatches = find_mismatches(versions)
    if mismatches:
        print("version mismatch (plugin.json is the source of truth):")
        for line in mismatches:
            print(f"  {line}")
        return 1
    print(f"versions agree: {versions['plugin.json']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
