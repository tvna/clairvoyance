# Skill maturity checklist (probabilistic review)

Skill maturity is measured along two lanes. This document owns the **probabilistic**
lane; the **deterministic** lane is owned by `scripts/check_skills.py`.

- **Deterministic** — best-practice rules a script can decide without judgement.
  Enforced by `scripts/check_skills.py` on every push, with a per-skill pass/fail
  table published to the CI job summary so the latest state is always visible
  (see the *Publish skill best-practice summary* step in
  [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)). Do **not** re-check
  these by hand — if the gate is green they hold.
- **Probabilistic** — best-practice rules that need a model or a human to judge
  meaning, tone, or sufficiency. No script can decide them, so they are *issued as
  this checklist* and run during review of any skill change.

Both lanes draw from the same upstream sources:
[Agent Skills best practices][skills-bp] and [Claude Code best practices][cc-bp].
The reasoning behind each probabilistic item — the standard and what a pass/fail
looks like — is captured in [skill-quality-knowledge.md](skill-quality-knowledge.md),
a self-contained reference you can inject into a harness that does not already carry
this knowledge (Codex, the Copilot CLI, a bare API call), so a grader there has the
rubric this checklist assumes.

## How to use this checklist

Copy the checklist for the skill you are reviewing into the PR (or your review
notes) and check off each item against that skill's `SKILL.md`, its `references/`,
and its `evals/<skill>/eval.yaml`. An unchecked item is a maturity gap:
fix it, or record in the PR why it does not apply. The deterministic gate is the
floor; this checklist is what separates a *passing* skill from a *mature* one.

## What the deterministic gate already covers (do not re-review)

`scripts/check_skills.py` decides these; they are listed here only so reviewers
know what is already automated:

- Frontmatter present; `name` is lowercase/hyphens, ≤ 64 chars, carries no
  reserved word, and matches its directory.
- `description` present, single-line, ≤ 1024 chars, third person, free of XML
  tags, and carries a when-to-use trigger ("Use when …").
- `SKILL.md` body ≤ 500 lines.
- Body links resolve, use forward slashes, and never traverse upward.
- Reference files stay one level deep from `SKILL.md`, and any reference over
  100 lines carries a table of contents.

## Probabilistic checklist

### Discovery — `name` and `description`

- [ ] The `description` says both **what** the skill does and **when** to use it,
      in terms a router would match (the gate only checks a trigger *exists*, not
      that it is the *right* trigger).
- [ ] The `description` includes specific key terms a real request would contain,
      not vague filler ("helps with", "does stuff").
- [ ] The `name` reads as an activity (gerund or action phrase) and is distinct
      from sibling skills — no overlap that would make routing ambiguous.
- [ ] `name` and `description` together let Claude pick this skill over the other
      skills in `skills/` for its intended trigger, and *not* pick it for a
      neighbouring skill's trigger.

### Conciseness — every token earns its place

- [ ] No explanation of things Claude already knows (general concepts, common
      tools, standard formats).
- [ ] Each paragraph justifies its token cost; nothing is restated.
- [ ] Detail that is only sometimes needed is pushed into `references/` via
      progressive disclosure, not inlined into `SKILL.md`.

### Clarity and structure

- [ ] Terminology is consistent — one term per concept throughout the skill and
      its references.
- [ ] The degree of freedom fits the task: high freedom (prose) where many paths
      are valid, low freedom (exact steps/commands) where the operation is fragile.
- [ ] Examples are concrete (real input/output), not abstract description.
- [ ] Multi-step work is expressed as clear, ordered steps — with a copyable
      progress checklist when the sequence is long or skippable steps are risky.
- [ ] Quality-critical steps have a feedback loop (validate → fix → repeat).

### Content durability

- [ ] No time-sensitive information ("after August 2025…"); anything historical
      lives in an "old patterns" section.
- [ ] No assumption that a tool or package is installed without saying so.
- [ ] MCP tools, if any, are referenced by fully qualified `Server:tool` names.

### References and progressive disclosure (meaning, not just shape)

- [ ] Reference files are named for their content (`decision-handoff.md`, not
      `doc2.md`) and are organised by domain.
- [ ] `SKILL.md` actually points to each reference at the moment it is needed, so
      Claude loads it on demand rather than guessing.
- [ ] Reference splits avoid forcing Claude to read several files to act on the
      common case.

### Behavioural evidence — the eval suite

- [ ] `evals/<skill>/eval.yaml` exercises the skill's real trigger and
      asserts the structural markers it reliably emits (its output-contract
      headings), plus `output_not_contains` guardrails — see
      [evaluations.md](evaluations.md).
- [ ] The suite covers at least three representative scenarios, including the
      failure/guardrail case the skill exists to prevent.
- [ ] Behaviour has been observed on the models the skill targets (the doc-stated
      Haiku/Sonnet/Opus spread), not just one.

### Scripts bundled with the skill (only if it ships code)

- [ ] Scripts handle their own error conditions rather than punting to Claude.
- [ ] No "voodoo constants" — every configuration value is justified in a comment.
- [ ] Required packages are listed, and the script's intent (execute vs. read as
      reference) is stated.

## Relationship to the other gates

This checklist is the probabilistic complement to the structural gate
(`check_skills.py`), the cross-lane coverage gate (`check_coverage.py`, see
[responsibility-matrix.md](responsibility-matrix.md)), and the behavioural evals
(`waza`, see [evaluations.md](evaluations.md)). The deterministic gate proves a
skill is *well-formed*; this checklist is how a reviewer judges it is *good*.

[skills-bp]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
[cc-bp]: https://code.claude.com/docs/en/best-practices
