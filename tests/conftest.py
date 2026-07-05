"""Shared test infrastructure for the adaptive-store and persona test suites.

Both ``test_adaptive_store.py`` and ``test_adaptive_coaching_personas.py``
drive ``hooks/adaptive-store.sh`` through subprocess and previously
duplicated the bash resolution, sqlite3-CLI availability check, and
store-specific env-clearing keys byte-for-byte (issue #95, finding 3).
"""

import os
import pathlib
import shutil

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE_SH = REPO_ROOT / "hooks" / "adaptive-store.sh"


def resolve_bash() -> str:
    """A POSIX bash for running the bundled .sh.

    On Windows a bare ``bash`` resolves to the System32 WSL launcher, which --
    with no distro installed -- prints a UTF-16 "...to install" notice and
    exits non-zero. Prefer Git Bash (the same interpreter run-hook.cmd
    locates in production); fall back to whatever ``bash`` is on PATH
    elsewhere.

    ``CLAIRVOYANCE_TEST_BASH`` overrides the resolved interpreter -- CI uses
    it to pin a specific bash (e.g. the stock bash 3.2 on macOS) regardless
    of what a later PATH entry (Homebrew, etc.) would otherwise resolve to,
    so a bash-version regression like issue #89's finding F5 is caught
    deterministically instead of depending on runner PATH order.
    """
    if override := os.environ.get("CLAIRVOYANCE_TEST_BASH"):
        return override
    if os.name == "nt":
        for candidate in (
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe",
        ):
            if pathlib.Path(candidate).exists():
                return candidate
    return shutil.which("bash") or "bash"


BASH = resolve_bash()

HAS_SQLITE3 = shutil.which("sqlite3") is not None
needs_sqlite3 = pytest.mark.skipif(not HAS_SQLITE3, reason="sqlite3 CLI not installed")

# Store-specific environment variables cleared from the ambient env before
# each subprocess invocation so tests are deterministic regardless of what
# the developer or CI runner has set.
CLAIRVOYANCE_ENV_KEYS = (
    "LOCALAPPDATA",
    "XDG_DATA_HOME",
    "CLAIRVOYANCE_COACH_THRESHOLD",
    "CLAIRVOYANCE_SESSION_THRESHOLD",
    "CLAIRVOYANCE_STORE_CONTEXT",
    "CLAIRVOYANCE_MAX_OBSERVATIONS",
    "CLAIRVOYANCE_MAX_AGE_DAYS",
)
