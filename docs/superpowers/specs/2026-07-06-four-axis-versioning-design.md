# Four-Axis Versioning Design

Tracking issue: https://github.com/tvna/clairvoyance/issues/123

## Goal

Split the current two-axis versioning model (`plugin`, `managed`) into four
independent product axes: `plugin`, `server`, `ui`, and `compose`.

The change improves development experience by separating the artifacts currently
included under the broad `managed` label. The managed service is implemented by
containers, so the server container, admin UI container, and deployment topology
should be able to release independently.

## Facts

- The current versioning documentation describes `plugin` and `managed` as the
  product-scoped release lines.
- The repository already separates managed-mode implementation into
  `managed/server/`, `managed/ui/`, and compose/development deployment files under
  `managed/`.
- The current managed version drift gate checks only the server package version
  and the FastAPI advertised version.
- The plugin already has a distinct tag namespace planned as `plugin-vX.Y.Z`.

## Assumptions

- `managed` remains a repository folder and deployment area, but no longer names a
  release product axis.
- The target tag namespaces are `plugin-vX.Y.Z`, `server-vX.Y.Z`, `ui-vX.Y.Z`,
  and `compose-vX.Y.Z`.
- The target Conventional Commit scopes are `(plugin)`, `(server)`, `(ui)`, and
  `(compose)`.
- This slice updates the documented specification and contributor-facing guidance;
  release automation and drift-gate renames can land in later implementation
  slices.

## Product Boundaries

| Product | Scope | Tag format | Owns |
|---------|-------|------------|------|
| `plugin` | `(plugin)` | `plugin-vX.Y.Z` | `skills/`, `hooks/`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, plugin-facing docs and evals when they change shipped plugin behavior |
| `server` | `(server)` | `server-vX.Y.Z` | `managed/server/`, API behavior, worker behavior, scheduler behavior, database migrations, server container image |
| `ui` | `(ui)` | `ui-vX.Y.Z` | `managed/ui/`, admin frontend behavior, UI container image, UI-facing tests and docs |
| `compose` | `(compose)` | `compose-vX.Y.Z` | `managed/docker-compose*.yml`, `managed/dev/`, composed service topology, deployment wiring, service environment contracts |

Shared repository infrastructure stays unversioned unless it changes shipped
behavior for one or more products. A single PR can release multiple products when
its commit scopes or PR body explicitly identify each release impact.

## Release Semantics

Each product keeps its own SemVer line, changelog, tag namespace, and release
notes. The git tag remains the source of truth for each product version.

All products remain in initial development (`0.x.x`) until the owner deliberately
declares a stable `1.0.0` surface. While a product is below `1.0.0`, a breaking
change bumps the minor version rather than silently graduating to `1.0.0`.

The superseded `managed-vX.Y.Z` namespace is not the target release namespace for
future work. Any staged references to `managed-vX.Y.Z` should be replaced by the
specific `server`, `ui`, or `compose` namespace as the rollout proceeds.

## Rollout

1. Update `docs/versioning.md`, README release summaries, and
   `CONTRIBUTING.md` to describe the four-axis model.
2. Rename or replace the server-specific managed drift gate so its name matches
   the `server` axis.
3. Split semantic-release configuration and workflows for `plugin`, `server`,
   `ui`, and `compose`.
4. Add version apply scripts and drift gates for every product that writes a
   runtime version file.
5. Seed baseline tags for all four namespaces before enabling releases.
6. Dry-run each product release path, then enable scheduled/manual releases.

## Verification

For the documentation slice:

- Search the changed docs for stale target-state claims that present `managed` as
  a product release axis.
- Run the root test suite or at least the doc/link validator if the full suite is
  unavailable.
- Confirm `docs/versioning.md` names the four tag namespaces and commit scopes.

For later automation slices:

- Run the relevant parity gates against real product files.
- Dry-run semantic-release for each product namespace against the real repository
  history and seeded baseline tags.
- Verify generated release notes filter out commits from other product scopes.
