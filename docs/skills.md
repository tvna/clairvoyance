# Skills

Clairvoyance is a family of handoff skills. Most hand a decision to a **human**;
`session-handoff` hands work to the **next agent session**
(see [session-handoff.md](session-handoff.md)).

## Bootstrap and routing

The `SessionStart` hook injects `using-clairvoyance`, a bootstrap router that picks
exactly one human-facing handoff skill for the moment at hand:

- **`clairvoyance`** — an owner decision, blocker, approval, deferral, rollback, or
  2–3 prepared options.
- **`review-verdict`** — a readiness verdict for a PR, commit, branch, working tree,
  or merge candidate.
- **`architecture-tradeoff`** — a system-level architecture decision between options,
  boundaries, dependencies, or failure modes.
- **`decision-coaching`** — a human seeking LGTM or a decision from ambiguous, noisy,
  or architecture-poor input; it refuses to rubber-stamp and coaches a sound call
  with a focused question.
- **`adaptive-coaching`** — a person's *recurring* adaptive challenge (a value, habit,
  or belief blocking the goal — distinct from a technical fix); it classifies the
  technical-versus-adaptive split, waits until enough anonymous signal has accumulated
  in the local store, and corrects the gap with a prosthesis-building `AskUserQuestion`
  quiz. See [hooks.md](hooks.md) for the readiness cue and the local store.

## Depth gate

After routing, the handoff branches by stakes: a reversible, low-risk call gets a
compact `Verdict` + `Next Move`; an irreversible, high-risk, or contested call gets
the full set of headings the routed skill defines.

## Output contract

Human handoffs share named headings so the owner can inspect by section — at minimum
**Verdict**, **Evidence**, **Risks**, and **Next Move**, plus skill-specific sections
(`Findings`, `System Context`, `Options`, `Future Story`, `Premortem`,
`Reversibility`, `Open Questions`). Each skill lists its exact set and a worked
example under `references/`.

## Evidence and authority

Every handoff ties claims to evidence (URLs, files, tests, command output, observed
behaviour), separates facts from assumptions, and preserves human authority by
presenting prepared, reversible options with a recommendation rather than raw status
or an unbounded question. When only a human can unblock a decision, the skill uses
`AskUserQuestion` (or a text fallback).

## Quality bars

Each skill keeps `SKILL.md` concise (the repo holds a 500-token budget, checked by
`waza check`), carries an eval suite under `plugin/evals/`, and passes the deterministic
checks in `scripts/check_skills.py` (frontmatter, name rules, description, and link
resolution). Cross-lane coverage — every skill has an eval and a doc mention, and
no eval is orphaned — is enforced by `scripts/check_coverage.py`; see
[responsibility-matrix.md](responsibility-matrix.md) for the ownership lanes and
gap-analysis procedure. See also [CONTRIBUTING.md](../CONTRIBUTING.md) and
[evaluations.md](evaluations.md).
