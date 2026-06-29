# Responsibility matrix and gap analysis

This document adapts the ownership-lane model and the gap-analysis procedure from
the upstream [`tvna/claude-md` design philosophy][upstream] (its sections 2, 3,
and 6) to Clairvoyance. The upstream is an instruction-export repository; this is
a Claude Code **plugin** whose product is a family of Agent Skills. The concepts
transfer; the concrete lanes and matrix axis are reframed around skills.

## The four ownership lanes (adapted)

A rule an agent must follow lives in exactly one lane. The lane decides who
enforces it, who reads it, and how it changes.

| Lane | Source of truth | Audience | Change mechanism |
|---|---|---|---|
| Skill instruction | `plugin/skills/*/SKILL.md` bodies and descriptions; `using-clairvoyance` bootstrap router | The agent loading the skill at runtime | Edit the SKILL.md; `waza check` and `scripts/check_skills.py` enforce shape |
| Harness | `scripts/*`, `.github/workflows/*.yml`, `plugin/hooks/*` | The repository itself; runs without agent involvement | Edit the script/workflow/hook; add or update a paired test under `tests/` |
| Repo-local doc | `docs/*.md` | Contributors and reviewers of this repository | Edit the doc; reference skills by name, never by copying their wording |
| Project-local | The consumer's `.clairvoyance/owner-language.txt`, their own `CLAUDE.md` | Agents working in that one project | Owned entirely by the consumer; this repository neither ships nor reviews it |

`AGENTS.md` is **imported**, not authored here: it is synced and SHA-verified from
the upstream by `.github/workflows/sync-agent-instructions.yml`. It is therefore
outside these lanes — treat it as read-only provenance, not a lane this repo owns.

## Coverage matrix

The matrix axis is the **skill**, not a list of principles. Each skill should be
carried across the lanes: a SKILL.md contract, a deterministic harness check, an
eval suite, and a repo-local doc mention.

| Skill | Skill instruction | Harness (structural) | Eval (behavioural) | Repo-local doc |
|---|---|---|---|---|
| `using-clairvoyance` | `plugin/skills/using-clairvoyance/SKILL.md` | `scripts/check_skills.py` | `plugin/evals/using-clairvoyance/` | `docs/skills.md`, `docs/hooks.md` |
| `clairvoyance` | `plugin/skills/clairvoyance/SKILL.md` | `scripts/check_skills.py` | `plugin/evals/clairvoyance/` | `docs/skills.md` |
| `review-verdict` | `plugin/skills/review-verdict/SKILL.md` | `scripts/check_skills.py` | `plugin/evals/review-verdict/` | `docs/skills.md` |
| `architecture-tradeoff` | `plugin/skills/architecture-tradeoff/SKILL.md` | `scripts/check_skills.py` | `plugin/evals/architecture-tradeoff/` | `docs/skills.md` |
| `decision-coaching` | `plugin/skills/decision-coaching/SKILL.md` | `scripts/check_skills.py` | `plugin/evals/decision-coaching/` | `docs/skills.md` |
| `human-harness` | `plugin/skills/human-harness/SKILL.md` | `scripts/check_skills.py` | `plugin/evals/human-harness/` | `docs/human-harness.md`, `docs/skills.md` |
| `session-handoff` | `plugin/skills/session-handoff/SKILL.md` | `scripts/check_skills.py` | `plugin/evals/session-handoff/` | `docs/session-handoff.md`, `docs/skills.md` |

The forward/backward coverage of this matrix is enforced deterministically by
`scripts/check_coverage.py` (every skill has an eval and a doc mention; no eval
suite is an orphan). The per-skill structural quality is enforced by
`scripts/check_skills.py`; hook integrity by `scripts/check_hooks.sh`.

## Gap analysis procedure

Run these three sweeps whenever a skill, script, workflow, hook, doc, or eval
lands. `scripts/check_coverage.py` automates the mechanical core of the first two;
the drift sweep stays a manual review.

### Forward sweep — skill to carrier

For each skill under `plugin/skills/`, confirm a carrier exists in each lane it needs: a
harness check covers it, an eval suite exercises it, and a repo-local doc names
it. A skill with no eval or no doc mention is a gap — add the carrier, or record
in this matrix why the cell is intentionally empty. Automated by
`check_coverage.py`.

### Backward sweep — carrier to skill

For each harness artifact and eval suite, confirm it maps to a real skill or a
stated invariant. An eval directory with no matching skill is an orphan (delete or
rename it). A script that serves no documented concern is either an orphan or an
undocumented invariant — give it a doc. The eval-orphan case is automated by
`check_coverage.py`.

### Drift sweep — duplicated concrete wording

The same *concrete* wording must not live in two lanes of the same row, or the two
copies drift. The known drift surface here is the output-contract headings: a
skill's `SKILL.md` emits headings (`Verdict`, `Evidence`, `Risks`, `Next Move`,
…) and its `plugin/evals/*/eval.yaml` asserts the same strings as `output_contains`
markers. Keep the abstract contract in `docs/skills.md`, the concrete headings in
the SKILL.md, and have the eval assert structural markers (the headings the skill
emits) rather than re-stating concepts — see the eval-assertion convention in
`CONTRIBUTING.md`. Renaming a heading therefore requires updating its eval in the
same change. The version number is the worked example of drift designed *out*:
rather than copying one version across several files and policing them, the git
tag is the single source of truth and the release writes it into `plugin.json`
alone (`marketplace.json` carries none) — so there is nothing to keep in sync.

### Cadence

Run the sweeps on every change that touches `plugin/skills/`, `scripts/`,
`.github/workflows/`, `plugin/hooks/`, `docs/`, or `plugin/evals/`. CI runs `check_coverage.py`
on every pull request, so the forward/backward mechanical core runs automatically;
the drift sweep is a reviewer responsibility.

## Out of scope

Deliberately **not** harvested from the upstream, because this plugin has no
downstream consumers and no instruction-export surface: authoring/exporting
universal instruction text, `apm compile` drift between source and compiled files,
the six master-principle rows, the retrospective auto-open harness and metrics
store, the self-modifying evolution loop, and the security-control floor. If
Clairvoyance ever grows downstream consumers, revisit the upstream sections 6.4
and 7 for the retrospective and review machinery.

[upstream]: https://github.com/tvna/claude-md/blob/main/docs/prd/agent-rules-design-philosophy.md
