# Contributing

## Conventional Commits (required)

Commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/).
Release Please reads them to compute the next semantic version, so the prefix is
not cosmetic — it determines the release.

| Prefix | Version effect | Use for |
|--------|----------------|---------|
| `feat:` | minor | a new skill, eval, or capability |
| `fix:` | patch | a correction to existing behavior |
| `feat!:` / `fix!:` or `BREAKING CHANGE:` footer | major | a backward-incompatible change |
| `docs:` `chore:` `test:` `refactor:` `ci:` | none | no release on their own |

See [docs/versioning.md](docs/versioning.md) for the full release flow.

## Authoring skills

- Keep `SKILL.md` concise. The repo holds each skill under a **500-token** budget
  (stricter than the 500-line guideline); `waza check` reports the count.
- Use trigger-style `description` frontmatter (`Use when …`). Skills have no
  `version` field — the plugin version covers the whole bundle.
- Keep reference files one level deep under the skill directory.

## Validate before opening a PR

```bash
waza check            # spec, links, schema, token budget — no quota needed
```

CI re-runs static validation (JSON manifests, version consistency, hook scripts)
on every PR. None of it requires an external service.

## Running evaluations

```bash
waza run                       # all suites
waza run evals/<skill>/eval.yaml
```

`waza run` executes through an embedded GitHub Copilot CLI and bills against that
subscription's quota — **not** the Anthropic API. When the quota is exhausted you
get `402 quota_exceeded`. Fallbacks and the assertion-style convention are in
[docs/evaluations.md](docs/evaluations.md).

**Eval assertions:** assert the structural markers a skill reliably emits
(`Verdict`, `Premortem`, `AskUserQuestion`, …) plus `output_not_contains`
guardrails. Avoid brittle concept-keyword matches that depend on phrasing.

## Pull requests

- Fill in the PR template.
- Do not auto-merge; releases and instruction syncs land behind review.
- Design rationale and migration plans belong in GitHub Issues, not committed docs.
