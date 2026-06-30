# Versioning

## Policy

The project uses [Semantic Versioning](https://semver.org/). Version strings in
files carry the bare `MAJOR.MINOR.PATCH` (no `v` prefix); git tags use the
conventional `v` prefix (e.g. `v0.1.0`). The current version is **0.1.0**.

The project is in **initial development** (`0.x.x`). `1.0.0` is reserved for the
first release we are willing to guarantee as a stable API, so until then the
version stays in the `0.x` range and is allowed to change freely (see the
[SemVer §4](https://semver.org/#spec-item-4) major-version-zero clause).

## Single source of truth: the git tag

The **git tag is the source of truth** for the version. There is no version file
to hand-edit: the version is written into the runtime manifests automatically, and
a CI parity check keeps the two manifests from drifting:

- The release computes the next version from commit history and creates the tag.
- Both runtime manifests — `.claude-plugin/plugin.json` and
  `.codex-plugin/plugin.json` — have `$.version` written **automatically**
  at release time (`scripts/apply_version.mjs`) so the manifest each runtime reads
  at the installed ref agrees with the tag. CI fails if the two ever drift
  (`.github/workflows/ci.yml`).
- `.claude-plugin/marketplace.json` deliberately carries **no** `version`. Claude
  Code [resolves the version](https://code.claude.com/docs/en/plugin-marketplaces)
  from `plugin.json` first and explicitly warns against setting it in both places
  (a stale marketplace value would be silently masked). Omitting it makes
  `plugin.json` the unambiguous manifest, and CI fails if a `version` is ever
  re-added (`.github/workflows/ci.yml`).

Each eval suite (`evals/*/eval.yaml`) carries its own `version` that
identifies that **evaluation specification**. It is independent of the package
version — bumping a release does not touch it, and changing an eval spec does not
require a release.

External versions remain out of scope and intentionally separate: the APM
instruction version in `AGENTS.md`, the upstream release the sync workflow
tracks (the latest published release of `tvna/claude-md`, resolved at run time
rather than pinned), and SHA-pinned GitHub Action versions.

## Automated releases (semantic-release)

Releases are driven by [semantic-release] reading the
[Conventional Commits](https://www.conventionalcommits.org/) on `main` since the
last tag. On each release it: computes the next semver, writes it into both
runtime `plugin.json` manifests, updates `CHANGELOG.md`, commits them, creates the
git tag, and publishes a GitHub Release with generated notes.

The bump is computed from commit prefixes (see
[CONTRIBUTING.md](../CONTRIBUTING.md)): `feat:` → minor, `fix:` → patch.

**The `0.x` guard.** While the project is below `1.0.0`, a breaking change must
**not** silently jump the version to `1.0.0`. `.releaserc.json` overrides the
commit analyzer so a breaking change (`feat!:` / `BREAKING CHANGE:`) bumps
**minor** (`0.1.0` → `0.2.0`):

```jsonc
"releaseRules": [{ "breaking": true, "release": "minor" }]
```

The jump to `1.0.0` is therefore a deliberate, manual act: when the API is stable
enough to guarantee, **remove that release rule** (restoring the default
breaking → major) and land a breaking change, or cut `1.0.0` by hand.

## Release cadence

Cadence is intentional, not per-merge (`.github/workflows/release.yml`):

- **Weekly schedule** — a cron cuts the week's release from `main` (skipped
  automatically if no releasable commits landed).
- **`workflow_dispatch`** — trigger an ad-hoc release between weeks when needed.
- Plain pushes to `main` never release.

## Branch strategy

Development is **trunk-based**: `main` is the trunk and is always releasable.
Work lands on `main` through short-lived branches and reviewed PRs (squash-merge,
so the PR title is the Conventional Commit that drives the bump). There are no
long-lived `develop`/`release` branches — the release is a tag cut from `main` on
the cadence above, not a branch.

## Required setup

**Release token.** The release commits the version bump back to `main` and pushes
the tag. Pushing past the `main` ruleset (and triggering the required checks)
needs a PAT or GitHub App token with `contents` + `pull-requests` write, added as
the repo secret `RELEASE_TOKEN`. `release.yml` uses it for both checkout and
semantic-release, falling back to `GITHUB_TOKEN` (which cannot push to a protected
`main`, so the release would fail until the secret is set). This is why the
release pipeline stays inert until the token is issued.

**One-time baseline tag.** semantic-release defaults the *first* release to
`1.0.0` when no prior tag exists. To start in the `0.x` range, seed the baseline
once after this lands on `main`:

```bash
git tag v0.1.0           # tagFormat is "v${version}"
git push origin v0.1.0
```

`release.yml` refuses to run unless a v-prefixed semver tag exists, so a missing
or wrongly-formatted baseline fails the release loudly instead of silently cutting
`1.0.0`. The next release then computes from `0.1.0` (`feat:` → `0.2.0`,
`fix:` → `0.1.1`).

[semantic-release]: https://github.com/semantic-release/semantic-release
