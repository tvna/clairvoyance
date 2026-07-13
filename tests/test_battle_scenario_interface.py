"""Seam drift gate for the adaptive-coaching battle scenarios (issue #137).

The adaptive-coaching battle slice tests the INTERFACE layer: each readiness
scenario injects the store's ``status`` verdict as JSON and grades whether the
skill obeys it. The F4/F6/F7 arithmetic that produces the verdict lives in the
IMPLEMENTATION layer (``hooks/adaptive-store.sh`` + ``tests/test_adaptive_store``)
and is not re-tested here.

This gate guards the seam between the two layers:

1. Every embedded verdict JSON uses only keys the real ``status`` command emits
   (the shape source of truth is the live store, not a hardcoded list), and
   carries a boolean ``ready``. A store field rename that orphaned the scenarios,
   or a scenario regressing back to prose-described raw numbers without a
   verdict, fails here.
2. ``skills/adaptive-coaching/SKILL.md`` still carries the both-directions
   obey-the-verdict authority phrase the whole interface layer assumes; a later
   "simplification" that drops it fails here.
"""

import json
import pathlib
import re

from conftest import needs_sqlite3
from conftest import run_store as run

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
ADAPTIVE_DIR = REPO_ROOT / "battle" / "scenarios" / "adaptive-coaching"
SKILL_MD = REPO_ROOT / "skills" / "adaptive-coaching" / "SKILL.md"

# Scenarios that legitimately carry no embedded status verdict: the
# store-unavailable case (no store, no verdict -> hold is the whole point) and
# the three sibling scenarios that state the verdict in English prose rather than
# JSON. Any OTHER adaptive-* scenario without an embedded ``ready`` JSON is a
# regression back to the prose-re-derivation shape this rework removed.
NO_VERDICT_ALLOWLIST = {
    "adaptive-store-unavailable.toml",
    "confidence-calibration.toml",
    "psychological-safety-retention.toml",
    "retrieval-before-feedback.toml",
}


def _live_status_keys(tmp_path) -> set[str]:
    """The real key set a ready-path ``status`` emits, read from the live store.

    Record one observation first so ``status`` takes the available branch and
    emits its full field set (the unavailable branch omits by_category etc.).
    """
    data_dir = tmp_path / "store"
    run(["record", "--category", "avoidance"], data_dir, coach_threshold=1)
    verdict = run(["status"], data_dir, coach_threshold=1)
    return set(verdict.keys())


def _extract_verdict_json(prompt: str) -> dict[str, object] | None:
    """Return the embedded status-verdict object from a prompt, or None.

    Finds the first ``{`` on a line mentioning ``"ready"`` and brace-matches to
    its close, so a nested ``by_category`` object does not truncate the parse.
    """
    idx = prompt.find('"ready"')
    if idx == -1:
        return None
    start = prompt.rfind("{", 0, idx)
    if start == -1:
        return None
    depth = 0
    for pos in range(start, len(prompt)):
        if prompt[pos] == "{":
            depth += 1
        elif prompt[pos] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(prompt[start : pos + 1])
    return None


def _load_prompt(toml_path: pathlib.Path) -> str:
    import tomllib

    return tomllib.loads(toml_path.read_text()).get("prompt", "")


@needs_sqlite3
def test_embedded_verdicts_use_only_real_status_keys(tmp_path):
    """Every embedded verdict's keys are a subset of the live status key set."""
    real_keys = _live_status_keys(tmp_path)
    for toml_path in sorted(ADAPTIVE_DIR.glob("*.toml")):
        verdict = _extract_verdict_json(_load_prompt(toml_path))
        if verdict is None:
            continue
        extra = set(verdict) - real_keys
        assert not extra, f"{toml_path.name}: verdict has keys {extra} not emitted by status {sorted(real_keys)}"
        assert isinstance(verdict.get("ready"), bool), (
            f"{toml_path.name}: embedded verdict must carry a boolean 'ready'"
        )


def test_every_adaptive_scenario_has_a_verdict_or_is_allowlisted():
    """No adaptive-* scenario regresses to prose raw numbers without a verdict."""
    for toml_path in sorted(ADAPTIVE_DIR.glob("*.toml")):
        if toml_path.name in NO_VERDICT_ALLOWLIST:
            continue
        verdict = _extract_verdict_json(_load_prompt(toml_path))
        assert verdict is not None, (
            f"{toml_path.name}: no embedded status verdict JSON found. Interface-layer "
            f"scenarios must inject the store's status verdict, not describe raw numbers "
            f"in prose. If this scenario legitimately has no verdict, add it to "
            f"NO_VERDICT_ALLOWLIST with a reason."
        )


def test_skill_carries_both_directions_authority_phrase():
    """SKILL.md keeps the obey-the-verdict contract the interface layer assumes."""
    text = SKILL_MD.read_text()
    assert re.search(r"never quiz on `ready: false`", text), (
        "SKILL.md must carry the 'never quiz on `ready: false`' clause (deliver-pull resistance)"
    )
    assert re.search(r"never hold on `ready: true`", text), (
        "SKILL.md must carry the 'never hold on `ready: true`' clause (anti-over-hold)"
    )
