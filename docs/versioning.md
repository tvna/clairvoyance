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
| **server** | FastAPI / Celery managed-mode backend under `managed/server/` | `server-vX.Y.Z` | `managed/server/pyproject.toml`, `managed/server/app/main.py` (FastAPI `version=`) | `managed/server/CHANGELOG.md` |
| **ui** | Admin UI under `managed/ui/` | `ui-vX.Y.Z` | `managed/ui/package.json`, `managed/ui/package-lock.json` | `managed/ui/CHANGELOG.md` |
| **compose** | Managed-mode composed service topology under `managed/` | `compose-vX.Y.Z` | `managed/compose.version` | `managed/CHANGELOG.md` |

All four products are in **initial development** (`0.x.x`). `1.0.0` is reserved
for the first release each product is willing to guarantee as a stable surface,
so until then the version stays in the `0.x` range and may change freely (see the
[SemVer §4](https://semver.org/#spec-item-4) major-version-zero clause).

### Rollout status

This is the adopted **direction**; the migration is staged so it stays reversible
(design: issue #53, reframed from the earlier `plugin`/`managed` split to the
current `plugin`/`server`/`ui`/`compose` axes). What is live today vs. staged:

- **Live now:** this documentation of the product-scoped model, the matrix release
  workflow (`.github/workflows/release.yml`), the product-aware semantic-release
  config (`release.config.cjs`), version apply support for all four axes
  (`scripts/apply_version.mjs`), and CI drift gates for plugin, server, UI, and
  compose version files.
- **Staged (operator setup):** seed the product-prefixed baseline tags before a
  product can release. Until a baseline exists, the workflow skips that product
  instead of letting semantic-release cut `1.0.0`. See the
  [required setup](#required-setup).

### Product boundaries

A change releases the product it belongs to. Shared repository infrastructure
(`.github/`, root tooling, generic docs) stays **unversioned** unless it changes
shipped behavior for a product; a change that affects multiple products can
produce multiple releases.

- **plugin** owns: `skills/`, `hooks/`, `.claude-plugin/plugin.json`,
  `.codex-plugin/plugin.json`, and the plugin-facing docs/evals when they change
  shipped plugin behavior.
- **server** owns: `managed/server/app/`, `managed/server/alembic/`,
  `managed/server/Dockerfile`, `managed/server/pyproject.toml`, API behavior,
  worker behavior, scheduler behavior, migrations, and the server container image.
- **ui** owns: `managed/ui/`, the admin frontend behavior, UI tests, UI build
  configuration, and the UI container image.
- **compose** owns: `managed/docker-compose*.yml`, `managed/dev/`, composed
  service wiring, deployment topology, and service environment contracts.

`managed` remains the repository folder for managed-mode assets; it is no longer
a product version axis.

### Legacy `vX.Y.Z` tags

Bare `vX.Y.Z` tags are **legacy plugin release tags**. They are immutable history:
they are **not rewritten or deleted**. Future plugin releases use the `plugin-v`
namespace, no new bare `vX.Y.Z` tag is created, and the plugin baseline
(`plugin-v0.3.0`) is cut at the same commit that the legacy `v0.3.0` plugin version
represents.

## Single source of truth: the git tag

For each product the **git tag is the source of truth** for the version. There is
no version file to hand-edit: the version is written into that product's runtime
manifests automatically at release time, and CI parity checks keep the manifests
from drifting.

**plugin.** The release computes the next version from commit history and creates
the `plugin-vX.Y.Z` tag. Both runtime manifests -- `.claude-plugin/plugin.json`
and `.codex-plugin/plugin.json` -- have `$.version` written **automatically** at
release time (`scripts/apply_version.mjs plugin`) so the manifest each runtime
reads at the installed ref agrees with the tag. CI fails if the two ever drift
(`.github/workflows/ci.yml`). `.claude-plugin/marketplace.json` deliberately
carries **no** `version`: Claude Code
[resolves the version](https://code.claude.com/docs/en/plugin-marketplaces) from
`plugin.json` first and warns against setting it in both places, so CI fails if a
`version` is ever re-added.

**server.** The managed server carries its version in
`managed/server/pyproject.toml` (`[project].version`) and in the FastAPI app
factory (`managed/server/app/main.py`, the `version=` the running server
advertises at `/openapi.json`). These must agree; `scripts/check_managed_version.py`
fails CI on any drift.

**ui.** The UI release line writes the released version into
`managed/ui/package.json` and the root `managed/ui/package-lock.json` entries so
the built admin UI image can be traced back to the `ui-vX.Y.Z` tag. CI fails if
the package and lockfile versions drift.

**compose.** The compose release line versions the deployment topology rather
than an application binary. Its version file is a small explicit marker
(`managed/compose.version`) so topology-only changes can produce
`compose-vX.Y.Z` releases without pretending to release the server or UI
containers.

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
feat(server): ...   fix(server): ...   docs(server): ...
feat(ui): ...       fix(ui): ...       docs(ui): ...
feat(compose): ...  fix(compose): ...  docs(compose): ...
```

These four scopes drive the four release jobs. The plugin release filters out
`server`, `ui`, `compose`, and legacy `managed` commits; each non-plugin product
release filters to its own scope. A releasable commit without a product scope is
ignored by the release config, as is any unrecognized product scope.

Infrastructure-only commits (`ci:`, `chore:`) do not release unless they alter a
shipped artifact. If one PR changes multiple products, make each release impact
explicit in the commits or PR body. See [CONTRIBUTING.md](../CONTRIBUTING.md) for
the prefix-to-bump table; this versioning policy remains the source of truth for
the product scope model and release automation behavior above.

**The `0.x` guard.** While a product is below `1.0.0`, a breaking change must
**not** silently jump to `1.0.0`. `release.config.cjs` overrides the commit
analyzer so a breaking change (`feat!:` / `BREAKING CHANGE:`) bumps **minor**
(`0.1.0` -> `0.2.0`):

```jsonc
"releaseRules": [{ "breaking": true, "release": "minor" }]
```

The jump to `1.0.0` is therefore a deliberate, manual act: when a product's surface
is stable enough to guarantee, remove that rule (restoring default breaking ->
major) and land a breaking change, or cut `1.0.0` by hand.

## CI drift gates

The live deterministic checks cover product version drift on every PR
(`.github/workflows/ci.yml`):

- **Plugin manifest parity** -- `.claude-plugin/plugin.json` and
  `.codex-plugin/plugin.json` carry the same version.
- **Marketplace carries no version** -- the version lives only in `plugin.json`.
- **Server version parity** -- `managed/server/pyproject.toml` and the FastAPI app
  version agree (`scripts/check_managed_version.py`, transitional name).
- **UI version parity** -- `managed/ui/package.json` and the root
  `managed/ui/package-lock.json` entries agree.
- **Compose version marker** -- `managed/compose.version` is a semver marker for
  topology-only releases.

CI also loads `release.config.cjs` once per product so a syntax error, missing
plugin list, or missing tag format fails before the release workflow runs.

## Release automation (semantic-release)

`release.config.cjs` builds one semantic-release config per product from
`CLAIRVOYANCE_RELEASE_PRODUCT`. Each config reads the
[Conventional Commits](https://www.conventionalcommits.org/) on `main` since
**that product's** last tag, filters release notes to that product's scope,
computes the next semver, writes it into the product's version files, updates the
product's changelog, commits them, creates the product-prefixed git tag, and
publishes a GitHub Release with generated notes.

**plugin** (tag `plugin-vX.Y.Z`) writes both plugin manifests and `CHANGELOG.md`.
Commit-analyzer rules keep `managed`, `server`, `ui`, and `compose` scoped commits
from cutting plugin releases.

**server** (tag `server-vX.Y.Z`) writes `managed/server/pyproject.toml` +
`managed/server/app/main.py` and updates `managed/server/CHANGELOG.md`.

**ui** (tag `ui-vX.Y.Z`) writes `managed/ui/package.json` +
`managed/ui/package-lock.json` and updates `managed/ui/CHANGELOG.md`.

**compose** (tag `compose-vX.Y.Z`) writes `managed/compose.version` and updates
`managed/CHANGELOG.md`.

### Rollout order

The migration is staged so it stays reversible until releases are enabled (design:
issue #53):

1. Land docs, version drift gates, product-aware release config, matrix workflow,
   and version apply support for all four axes. **(done)**
2. Add the `plugin-v0.3.0`, `server-v0.1.0`, `ui-v0.1.0`, and `compose-v0.1.0`
   baseline tags.
3. Dry-run release verification for plugin, server, ui, and compose.
4. Enable scheduled/manual releases independently once each baseline exists.

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
git tag plugin-v0.3.0
git push origin plugin-v0.3.0

git tag server-v0.1.0
git push origin server-v0.1.0

git tag ui-v0.1.0
git push origin ui-v0.1.0

git tag compose-v0.1.0
git push origin compose-v0.1.0
```

`release.yml` skips a product when no matching product-prefixed semver baseline
exists, so a missing or wrongly-formatted baseline cannot silently cut `1.0.0`.
The next plugin release then computes from `0.3.0` (`feat:` -> `0.4.0`, `fix:`
-> `0.3.1`).

[semantic-release]: https://github.com/semantic-release/semantic-release
