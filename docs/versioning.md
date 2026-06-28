# Versioning

## Policy

The project uses [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`,
no `v` prefix in files). The current version is **0.1.0**.

The project is in **initial development** (`0.x.x`). `1.0.0` is reserved for the
first release we are willing to guarantee as a stable API, so until then the
version stays in the `0.x` range and is allowed to change freely (see the
[SemVer §4](https://semver.org/#spec-item-4) major-version-zero clause).

`plugin/.claude-plugin/plugin.json` `version` is the **single source of truth**. These
files must always agree, and CI fails the build if they drift:

- `plugin/.claude-plugin/plugin.json` → `$.version`
- `.claude-plugin/marketplace.json` → `$.plugins[0].version`
- `.release-please-manifest.json` → `"."`
- `version.txt`

Each eval suite (`plugin/evals/*/eval.yaml`) also carries a `version` identifying that
evaluation specification; it is kept at the package version (`0.1.0`).

External versions are out of scope for this policy and intentionally separate:
the APM instruction version in `AGENTS.md`, the `INSTRUCTIONS_TAG` in the sync
workflow, and SHA-pinned GitHub Action versions.

## Automated releases (Release Please)

Tagging is dynamic and driven by Conventional Commits — no version is bumped by
hand.

1. Commits land on `main` following Conventional Commits.
2. `.github/workflows/release.yml` runs [Release Please], which opens or updates a
   **release PR** containing the computed version bump and a generated
   `CHANGELOG.md`.
3. Merging the release PR creates the git tag and GitHub Release and writes the
   new version into every file listed above.

The release PR is review-gated, matching the repository's no-auto-merge posture.
The version bump itself is computed from commit prefixes (see
[CONTRIBUTING.md](../CONTRIBUTING.md)): `feat:` → minor, `fix:` → patch, a `!` or
`BREAKING CHANGE:` → major.

While the project is on `0.x.x`, `bump-minor-pre-major: true` in
`release-please-config.json` holds breaking changes to a **minor** bump
(`0.1.0` → `0.2.0`) instead of letting them reach `1.0.0`. The jump to `1.0.0`
is therefore deliberate: flip `bump-minor-pre-major` to `false` (or land a
breaking change once you are ready) when the API is stable enough to guarantee.

> First-run note: confirm Release Please resolves the `marketplace.json`
> `$.plugins[0].version` path on the first release PR. If it does not, the CI
> version-consistency check will fail and surface the drift immediately.

## Required setup

**Release token.** The `main` ruleset requires the `validate` and `tests` checks,
but a PR opened with the default `GITHUB_TOKEN` does not start workflows — so the
release PR's required checks would stay pending and block the merge. Create a PAT
(or GitHub App token) with `contents` + `pull-requests` write and add it as the
repo secret `RELEASE_PLEASE_TOKEN`; `release.yml` passes it to Release Please and
falls back to `GITHUB_TOKEN` when it is unset.

**version.txt invariant.** `version.txt` is bumped implicitly by Release Please's
`release-type: "simple"` (it owns a root file of that exact name), not via
`extra-files`. The version-consistency check gates on it, so do not rename it or
change `release-type` without also updating how `version.txt` is maintained, or
the `validate` check will fail on every release PR.

[Release Please]: https://github.com/googleapis/release-please
