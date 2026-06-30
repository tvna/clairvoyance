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
- **`adaptive-coaching`** — works across sessions on a person's *recurring* capability
  gaps (a misunderstood technical challenge or an adaptive one — a value, habit, or
  belief). It logs those gaps as anonymous local signal, and — only when the person
  asks to **reflect** (a retrospective) — turns the accumulated signal into a
  prosthesis-building `AskUserQuestion` quiz, classifying the technical-versus-adaptive
  split to shape it. The quiz is never pushed: it fires on the person's own request,
  and only once enough has accumulated (a session grace period plus signal). The
  boundary with `decision-coaching` is intent: a live decision there, an explicit
  reflection request here. See [hooks.md](hooks.md) for the local store.
- **`human-harness`** — the human harness: a high-blast-radius, irreversible, or
  compliance-violating instruction. It is the inverse of rubber-stamping the human's
  order — instead of executing, it stops, measures blast radius, and presses the
  human to confirm intent one focused question at a time so a human error is caught
  before it lands. It is one layer; the deterministic, process, and eval measures
  that must back it live outside the skill — see [human-harness.md](human-harness.md).

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

Skill maturity is measured along two lanes — deterministic and probabilistic.

**Deterministic.** Each skill keeps `SKILL.md` concise (the repo holds a 500-token
budget, checked by `waza check`), carries an eval suite under `evals/`, and
passes the best-practice checks in `scripts/check_skills.py`: frontmatter; name
rules; the description (single-line, third person, no XML tags, a when-to-use
trigger); body length; link resolution, forward slashes, and no upward traversal;
and the progressive-disclosure rules on reference files (one level deep, table of
contents past 100 lines). CI publishes a per-skill pass/fail table to the run's job
summary on every push (the *Publish skill best-practice summary* step in
[ci.yml](../.github/workflows/ci.yml)), so the latest deterministic state is always
visible — run `python3 scripts/check_skills.py --summary` to preview it locally.
Cross-lane coverage — every skill has an eval and a doc mention, and no eval is
orphaned — is enforced by `scripts/check_coverage.py`; see
[responsibility-matrix.md](responsibility-matrix.md) for the ownership lanes and
gap-analysis procedure.

**Probabilistic.** The best-practice rules that need a model or a human to judge
meaning, tone, or sufficiency cannot be scripted, so they are issued as a review
checklist in [skill-maturity-checklist.md](skill-maturity-checklist.md) and run on
any skill change. The standards behind that checklist — extracted so they can be
injected into a harness that does not already carry them — live in
[skill-quality-knowledge.md](skill-quality-knowledge.md). See also
[CONTRIBUTING.md](../CONTRIBUTING.md) and [evaluations.md](evaluations.md).
