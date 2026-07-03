#!/usr/bin/env python3
"""Product-prefixed release-tag-format drift gate.

Product-scoped versioning (see ``docs/versioning.md``) namespaces every release
tag by product -- ``plugin-vX.Y.Z`` for the plugin bundle, ``managed-vX.Y.Z`` for
the managed server. semantic-release derives the tag it creates and the prior
release it reads from a config's ``tagFormat``. A bare ``v${version}`` would
reintroduce a single repo-wide release line and let a plugin-only change look
like it released the server (and vice versa), so this gate fails CI on any
release config whose ``tagFormat`` is not ``<product>-v${version}``.

It scans every ``.releaserc*.json`` at the repository root, so a managed release
config added later is covered without touching this gate.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# <product>-v${version}: a lowercase product prefix, then the literal version
# placeholder semantic-release substitutes. Bare "v${version}" is rejected.
_TAG_FORMAT = re.compile(r"[a-z][a-z0-9-]*-v\$\{version\}")


def find_release_configs(root: Path = REPO_ROOT) -> list[Path]:
    """Return the semantic-release JSON configs at the repository root, sorted."""
    return sorted(root.glob(".releaserc*.json"))


def check(root: Path = REPO_ROOT) -> tuple[bool, str]:
    """Verify every release config uses a product-prefixed tagFormat.

    Return (ok, human-readable message). A repository with no release config is
    reported as an error rather than a silent pass -- the gate exists to guard a
    config that should be present.
    """
    configs = find_release_configs(root)
    if not configs:
        return False, "no .releaserc*.json release config found"
    bad = []
    for config in configs:
        tag_format = json.loads(config.read_text(encoding="utf-8")).get("tagFormat", "")
        if not _TAG_FORMAT.fullmatch(tag_format):
            bad.append(f"{config.name}={tag_format!r}")
    if bad:
        return False, "release config tagFormat must be <product>-v${version}: " + ", ".join(bad)
    return True, f"ok: {len(configs)} release config(s) use product-prefixed tag formats"


def main() -> int:
    try:
        ok, message = check()
    except (OSError, ValueError) as err:
        print(f"check_release_tag_format: {err}", file=sys.stderr)
        return 1
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
