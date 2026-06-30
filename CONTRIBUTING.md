# Contributing

## Conventional Commits (required)

Commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/).
semantic-release reads them to compute the next semantic version, so the prefix is
not cosmetic — it determines the release.

| Prefix | Version effect | Use for |
|--------|----------------|---------|
| `feat:` | minor | a new skill, eval, or capability |
| `fix:` | patch | a correction to existing behavior |
| `feat!:` / `fix!:` or `BREAKING CHANGE:` footer | major | a backward-incompatible change |
| `docs:` `chore:` `test:` `refactor:` `ci:` | none | no release on their own |

While the project is on `0.x.x`, a breaking change bumps **minor** (not major) —
the version stays below `1.0.0` until the API is declared stable (configured by a
release rule in `.releaserc.json`). See [docs/versioning.md](docs/versioning.md)
for the full release flow, the git-tag source of truth, and the branch strategy.

## Authoring skills

- Keep `SKILL.md` concise. The repo holds each skill under a **500-token** budget
  (stricter than the 500-line guideline); `waza check` reports the count.
- Use trigger-style `description` frontmatter (`Use when …`). Skills have no
  `version` field — the plugin version covers the whole bundle.
- Keep reference files one level deep under the skill directory.

## Validate before opening a PR

```bash
cd plugin && waza check   # spec, links, schema, token budget — no quota needed
```

CI re-runs static validation (JSON manifests, hook scripts, deterministic skill
best-practice checks via `scripts/check_skills.py`, and cross-lane coverage via
`scripts/check_coverage.py`) on every PR. None of it
requires an external service. `waza check` stays the richer local gate;
`scripts/check_skills.py` is the subset that runs everywhere.

`scripts/check_coverage.py` is the harness form of the forward/backward gap
sweeps: it fails if a skill lacks an eval suite or a doc mention, or if an eval
suite has no matching skill. See
[docs/responsibility-matrix.md](docs/responsibility-matrix.md) for the lane model
and the full gap-analysis procedure.

### Pre-commit hooks

A [`.pre-commit-config.yaml`](.pre-commit-config.yaml) runs the same checks before
each commit. Install the git hook once with [prek](https://github.com/j178/prek)
(or `pre-commit`):

```bash
prek install            # enable the hook
prek run --all-files     # run across the whole repo
```

It runs format hygiene (JSON/YAML, end-of-file, line endings), `shellcheck` on the
bash hook, `ruff` lint/format and `mypy` types on Python, and the project's own validators
(`waza check` and hook-script checks via the shared `scripts/`). `waza check` needs
the `waza` binary on your PATH.

## Tests

The helper scripts under `scripts/` are tested with pytest, managed by
[uv](https://docs.astral.sh/uv/). Dev dependencies are declared in
`pyproject.toml` and pinned in `uv.lock`, and the Python version is pinned in
`.python-version` (uv provisions it automatically). This is a non-package tooling
project — the plugin version still lives in `plugin.json`.

```bash
uv run pytest            # run the tests with coverage
```

Coverage is enforced at 100% for `scripts/` (see `pyproject.toml`). The same
command runs in CI and as a pre-commit hook when `scripts/`, `tests/`, or the
dependency files change.

## Lint, format, and types

Python under `scripts/` and `tests/` is linted and formatted with
[ruff](https://docs.astral.sh/ruff/) and type-checked with
[mypy](https://mypy-lang.org/) (both configured in `pyproject.toml`, with the
rule/flag selection mirrored from the upstream `tvna/claude-md`). All run in CI
and as pre-commit hooks:

```bash
uv run ruff check          # lint; add --fix to auto-fix
uv run ruff format         # format in place (--check to verify only)
uv run mypy                # type-check scripts/ and tests/
```

## Running evaluations

Run from the repository root (where `skills/` and `evals/` are siblings):

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

## Branching and releases

Development is **trunk-based**: `main` is always releasable, work lands through
short-lived branches and squash-merged PRs (the PR title becomes the Conventional
Commit that drives the bump), and releasing is decoupled from merging — a tag is
cut weekly (plus on-demand `workflow_dispatch`), not on every merge. Full detail
in [docs/versioning.md](docs/versioning.md).

## Pull requests

- Fill in the PR template.
- Do not auto-merge; changes land behind review.
- Design rationale and migration plans belong in GitHub Issues, not committed docs.

## Signed-commit bot App (sync-agent-instructions.yml)

The `Sync agent instructions` workflow opens its refresh PR via a GitHub App
installation token, not the default `GITHUB_TOKEN`: a runner `git push`
produces an unsigned commit, which this repository's `required_signatures`
branch-protection rule rejects at merge time. `scripts/sync_pr_publish.py`
creates the commit server-side via GraphQL `createCommitOnBranch` instead,
which GitHub signs and shows as Verified.

This requires a one-time, repo-admin-only setup:

1. **Create the App** — github.com/settings/apps → New GitHub App, owned by
   the `tvna` account. Disable webhooks. Repository permissions: **Contents:
   Read and write**, **Pull requests: Read and write**. No other permissions.
2. **Install it** — on the App's page, Install App → select only
   `tvna/clairvoyance`.
3. **Generate a private key** — on the App's page, "Generate a private key"
   downloads a `.pem` file once; store it securely (e.g. a password manager),
   it cannot be re-downloaded.
4. **Register the two secrets** — repo Settings → Secrets and variables →
   Actions:
   - `SYNC_BOT_APP_ID`: the App ID shown on the App's settings page.
   - `SYNC_BOT_APP_PRIVATE_KEY`: the full contents of the downloaded `.pem`
     file.
5. **Rotate** — regenerate the private key from the App's settings page and
   update `SYNC_BOT_APP_PRIVATE_KEY` if the key is ever suspected leaked;
   GitHub keeps the old key valid for a short overlap window so this can be
   done without a workflow outage.
6. **Verify the handoff** — run the workflow manually
   (`workflow_dispatch`) and confirm the opened PR's commit shows a green
   "Verified" badge on GitHub.

Until this App exists, the workflow's "Mint GitHub App token" step fails
fast with a clear error rather than silently falling back to an unsigned
push.
