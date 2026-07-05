# Versioning

## Policy

The repository ships **more than one product**, so it uses **product-scoped**
[Semantic Versioning](https://semver.org/): each deployable artifact has its own
version line, its own tag namespace, and its own changelog. A single repo-wide
version would make release notes misleading -- a plugin-only fix would look like it
released the server, and a server-only migration would look like it released the
plugin.

| Product | Scope | Tag format | Version files | Changelog |
|---------|-------|------------|---------------|-----------|
| **plugin** | Claude Code / Codex plugin bundle at the repo root | `plugin-vX.Y.Z` | `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json` | `CHANGELOG.md` |
| **managed** | managed coaching server under `managed/server/` | `managed-vX.Y.Z` | `managed/server/pyproject.toml`, `managed/server/app/main.py` (FastAPI `version=`) | `managed/CHANGELOG.md` |

Both products are in **initial development** (`0.x.x`). `1.0.0` is reserved for the
first release each product is willing to guarantee as a stable surface, so until
then the version stays in the `0.x` range and may change freely (see the
[SemVer §4](https://semver.org/#spec-item-4) major-version-zero clause).

### Rollout status

This is the adopted **direction**; the migration is staged so it stays reversible
(design: issue #53). What is live today vs. staged:

- **Live now:** this documentation of the product-scoped model, the managed
  version-parity CI gate (`scripts/check_managed_version.py`), and a commit-analyzer
  rule so a `managed`-scoped commit cannot cut a plugin release
  (`.releaserc.json`).
- **Staged (later slices):** the plugin release line moving to `plugin-v` tags, the
  release-notes filtering that also drops managed commits from plugin release notes,
  the managed release workflow, and the baseline tags. Until those land, the plugin
  release config still uses the legacy `v${version}` tag format described under
  [Release automation](#release-automation-semantic-release). See the
  [rollout order](#rollout-order).

### Product boundaries

A change releases the product it belongs to. Shared repository infrastructure
(`.github/`, root tooling, generic docs) stays **unversioned** unless it changes
shipped behavior for a product; a change that affects both products can produce
two releases.

- **plugin** owns: `skills/`, `hooks/`, `.claude-plugin/plugin.json`,
  `.codex-plugin/plugin.json`, and the plugin-facing docs/evals when they change
  shipped plugin behavior.
- **managed** owns: `managed/server/app/`, `managed/server/alembic/`,
  `managed/server/Dockerfile`, `managed/docker-compose.coolify.yml`,
  `managed/server/pyproject.toml`, and the managed
  API / worker / scheduler / migration behavior.

### Legacy `vX.Y.Z` tags

Bare `vX.Y.Z` tags are **legacy plugin release tags**. They are immutable history:
they are **not rewritten or deleted**. Once the plugin line moves to the `plugin-v`
namespace (a staged slice), no new bare `vX.Y.Z` tag is created for future releases,
and the plugin baseline (`plugin-v0.3.0`) is cut at the same commit that the legacy
`v0.3.0` plugin version represents.

## Single source of truth: the git tag

For each product the **git tag is the source of truth** for the version. There is
no version file to hand-edit: the version is written into that product's runtime
manifests automatically at release time, and CI parity checks keep the manifests
from drifting.

**plugin.** The release computes the next version from commit history and creates
the plugin tag (legacy `v` today, `plugin-v` after the staged rename). Both runtime
manifests -- `.claude-plugin/plugin.json`
and `.codex-plugin/plugin.json` -- have `$.version` written **automatically** at
release time (`scripts/apply_version.mjs`) so the manifest each runtime reads at
the installed ref agrees with the tag. CI fails if the two ever drift
(`.github/workflows/ci.yml`). `.claude-plugin/marketplace.json` deliberately
carries **no** `version`: Claude Code
[resolves the version](https://code.claude.com/docs/en/plugin-marketplaces) from
`plugin.json` first and warns against setting it in both places, so CI fails if a
`version` is ever re-added.

**managed.** The managed server carries its version in `managed/server/pyproject.toml`
(`[project].version`) and in the FastAPI app factory (`managed/server/app/main.py`, the
`version=` the running server advertises at `/openapi.json`). These must agree;
`scripts/check_managed_version.py` fails CI on any drift.

Each eval suite (`evals/*/eval.yaml`) carries its own `version` that identifies
that **evaluation specification**. It is independent of any product version --
bumping a release does not touch it, and changing an eval spec does not require a
release.

External versions remain out of scope and intentionally separate: the APM
instruction version in `AGENTS.md`, the upstream revision the sync workflow tracks,
and SHA-pinned GitHub Action versions.

## Commit and changelog policy

Conventional Commits carry **product intent in the scope** so the right product
releases and its changelog is the only one touched:

```
feat(plugin): ...   fix(plugin): ...   docs(plugin): ...
feat(managed): ...   fix(managed): ...   docs(managed): ...
```

Infrastructure-only commits (`ci:`, `chore:`) do not release unless they alter a
shipped artifact. If one PR changes both products, make both release impacts
explicit in the commits or PR body. See [CONTRIBUTING.md](../CONTRIBUTING.md) for
the prefix-to-bump table.

**The `0.x` guard.** While a product is below `1.0.0`, a breaking change must
**not** silently jump to `1.0.0`. `.releaserc.json` overrides the commit analyzer
so a breaking change (`feat!:` / `BREAKING CHANGE:`) bumps **minor**
(`0.1.0` -> `0.2.0`):

```jsonc
"releaseRules": [{ "breaking": true, "release": "minor" }]
```

The jump to `1.0.0` is therefore a deliberate, manual act: when a product's surface
is stable enough to guarantee, remove that rule (restoring default breaking ->
major) and land a breaking change, or cut `1.0.0` by hand.

## CI drift gates

Deterministic checks enforce each product boundary on every PR
(`.github/workflows/ci.yml`):

- **Plugin manifest parity** -- `.claude-plugin/plugin.json` and
  `.codex-plugin/plugin.json` carry the same version.
- **Marketplace carries no version** -- the version lives only in `plugin.json`.
- **Managed version parity** -- `managed/server/pyproject.toml` and the FastAPI app
  version agree (`scripts/check_managed_version.py`).

The release-config gates that pair with the automation split -- product-prefixed
tag formats and product-specific changelog paths -- land with that slice (below),
so a gate never fails against a config that has not been migrated yet.

## Release automation (semantic-release)

The target is one semantic-release config per product, each reading the
[Conventional Commits](https://www.conventionalcommits.org/) on `main` since **that
product's** last tag, filtered to that product's scope. On a release it computes the
next semver, writes it into the product's version files, updates the product's
changelog, commits them, creates the product-prefixed git tag, and publishes a
GitHub Release with generated notes.

**plugin** (`.releaserc.json`, `.github/workflows/release.yml`) exists today and
writes both `plugin.json` manifests and `CHANGELOG.md`. A commit-analyzer rule
(`{ "scope": "managed", "release": false }`) keeps any `managed`-scoped commit --
including a breaking `feat(managed)!` / `BREAKING CHANGE` -- from cutting a plugin
release. **Order matters:** commit-analyzer keeps the *last* matching rule's release
when `false` competes with a real release type, so the `release: false` rule must sit
**after** the `breaking -> minor` rule in `releaseRules`, or a breaking managed
commit would be upgraded back to a plugin minor release. It still uses the legacy
`v${version}` tag format, so it is not yet enabled for independent product releases:
the `plugin-v` rename and the release-notes filtering (so managed commits also drop
out of the plugin release notes, not just the version bump) land as one verified
unit in the release-config split slice.

**managed** (tag `managed-vX.Y.Z`, writes `managed/server/pyproject.toml` +
`managed/server/app/main.py`, updates `managed/CHANGELOG.md`, tags the container image
`managed-vX.Y.Z`) is a later rollout slice: its release config and workflow land
with the same split. The managed version-parity gate is in place first so the
boundary is governed before its automation is enabled.

### Rollout order

The migration is staged so it stays reversible until releases are enabled (design:
issue #53):

1. Land docs, the managed version-parity drift gate, and the commit-analyzer rule
   that drops `managed`-scoped commits from the plugin release. **(done)**
2. Split release configs and workflows per product: rename the plugin tag format to
   `plugin-v`, add plugin-scoped release-notes filtering, add the managed release
   config + workflow, and the release-config drift gates (product-prefixed tag
   formats, product-specific changelog paths).
3. Add the managed version apply script.
4. Add the `plugin-v0.3.0` and `managed-v0.1.0` baseline tags.
5. Dry-run release verification for both products.
6. Enable scheduled/manual releases independently.

## Release cadence

Cadence is intentional, not per-merge (`.github/workflows/release.yml`):

- **Weekly schedule** -- a cron cuts the week's release from `main` (skipped
  automatically if no releasable commits landed for that product).
- **`workflow_dispatch`** -- trigger an ad-hoc release between weeks when needed.
- Plain pushes to `main` never release.

## Branch strategy

Development is **trunk-based**: `main` is the trunk and is always releasable. Work
lands on `main` through short-lived branches and reviewed PRs (squash-merge, so the
PR title is the Conventional Commit that drives the bump). There are no long-lived
`develop`/`release` branches -- a release is a product-prefixed tag cut from `main`
on the cadence above, not a branch.

## Required setup

**Release token.** A release commits the version bump back to `main` and pushes the
tag. Pushing past the `main` ruleset (and triggering the required checks) needs a
PAT or GitHub App token with `contents` + `pull-requests` write, added as the repo
secret `RELEASE_TOKEN`. `release.yml` uses it for both checkout and semantic-release,
falling back to `GITHUB_TOKEN` (which cannot push to a protected `main`, so the
release would fail until the secret is set). This is why the release pipeline stays
inert until the token is issued.

**One-time baseline tags.** semantic-release defaults the *first* release to `1.0.0`
when no prior tag matches the product's `tagFormat`, so each product's baseline is
seeded once in the release-config split slice, before its releases are enabled:

```bash
git tag plugin-v0.3.0    # after the plugin tagFormat becomes "plugin-v${version}"
git push origin plugin-v0.3.0

git tag managed-v0.1.0   # when the managed release line is enabled
git push origin managed-v0.1.0
```

`release.yml` already refuses to run unless a matching semver tag exists (today
`v[0-9]*`, `plugin-v[0-9]*` after the rename), so a missing or wrongly-formatted
baseline fails the release loudly instead of silently cutting `1.0.0`. The next
plugin release then computes from `0.3.0` (`feat:` -> `0.4.0`, `fix:` -> `0.3.1`).

[semantic-release]: https://github.com/semantic-release/semantic-release
