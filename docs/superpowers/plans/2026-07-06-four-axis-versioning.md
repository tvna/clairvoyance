# Four-Axis Versioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update contributor-facing release documentation from the old `plugin`/`managed` model to the approved `plugin`/`server`/`ui`/`compose` versioning model.

**Architecture:** This is a documentation-only slice. `docs/versioning.md` becomes the canonical four-axis specification, while README and CONTRIBUTING summarize the same scopes and tag namespaces. Existing release automation and drift gates stay unchanged but are documented as current live state or later rollout work.

**Tech Stack:** Markdown documentation, repository Python validators, existing root pytest suite.

---

## File Structure

- Modify `docs/versioning.md`: canonical policy, boundaries, commit scopes, rollout status, automation target, setup examples.
- Modify `CONTRIBUTING.md`: contributor-facing Conventional Commit scope table and examples.
- Modify `README.md`: English release summary.
- Modify `README.ja.md`: Japanese release summary.
- Optional modify `README.zh.md` and `README.ko.md`: only if their current release summaries contain stale `managed` product-axis claims after the main docs are updated.

## Task 1: Rewrite Canonical Versioning Policy

**Files:**
- Modify: `docs/versioning.md`

- [ ] **Step 1: Replace the product table with four axes**

Edit the table near the top of `docs/versioning.md` so it contains exactly these product rows:

```markdown
| Product | Scope | Tag format | Version files | Changelog |
|---------|-------|------------|---------------|-----------|
| **plugin** | Claude Code / Codex plugin bundle at the repo root | `plugin-vX.Y.Z` | `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json` | `CHANGELOG.md` |
| **server** | FastAPI / Celery managed-mode backend under `managed/server/` | `server-vX.Y.Z` | `managed/server/pyproject.toml`, `managed/server/app/main.py` (FastAPI `version=`) | `managed/server/CHANGELOG.md` |
| **ui** | Admin UI under `managed/ui/` | `ui-vX.Y.Z` | `managed/ui/package.json` | `managed/ui/CHANGELOG.md` |
| **compose** | Managed-mode composed service topology under `managed/` | `compose-vX.Y.Z` | `managed/compose.version` | `managed/CHANGELOG.md` |
```

Completion check: `docs/versioning.md` no longer presents `managed` as a row in the product table.

- [ ] **Step 2: Update rollout status**

Replace the current rollout status bullets with text that says:

```markdown
- **Live now:** this documentation of the product-scoped model, the server version-parity CI gate that still lives at `scripts/check_managed_version.py`, and a commit-analyzer rule so a legacy `managed`-scoped commit cannot cut a plugin release (`.releaserc.json`).
- **Staged (later slices):** the plugin release line moving to `plugin-v` tags, plugin release-notes filtering, the `server`/`ui`/`compose` release workflows, axis-specific drift gates, and baseline tags. Until those land, the plugin release config still uses the legacy `v${version}` tag format described under [Release automation](#release-automation-semantic-release).
```

Completion check: the live-state wording is honest that the gate script still has the old filename.

- [ ] **Step 3: Replace product boundaries**

Replace the old `plugin`/`managed` boundary list with:

```markdown
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
```

Add one sentence immediately after the list:

```markdown
`managed` remains the repository folder for managed-mode assets; it is no longer a product version axis.
```

Completion check: product boundaries name `server`, `ui`, and `compose` separately.

- [ ] **Step 4: Update single-source-of-truth subsections**

Rename the `**managed.**` paragraph to `**server.**` and keep its existing package/FastAPI parity explanation. Then add these two paragraphs after it:

```markdown
**ui.** The UI release line writes the released version into `managed/ui/package.json` so the built admin UI image can be traced back to the `ui-vX.Y.Z` tag. A later drift gate will fail CI if the package version and release tag disagree.

**compose.** The compose release line versions the deployment topology rather than an application binary. Its version file is a small explicit marker (`managed/compose.version`) so topology-only changes can produce `compose-vX.Y.Z` releases without pretending to release the server or UI containers.
```

Completion check: this section has `plugin`, `server`, `ui`, and `compose` subsections.

- [ ] **Step 5: Update commit examples**

Replace the current commit examples block with:

```markdown
feat(plugin): ...   fix(plugin): ...   docs(plugin): ...
feat(server): ...   fix(server): ...   docs(server): ...
feat(ui): ...       fix(ui): ...       docs(ui): ...
feat(compose): ...  fix(compose): ...  docs(compose): ...
```

Completion check: `feat(managed)` no longer appears in the commit example block.

- [ ] **Step 6: Update CI drift gate language**

Replace `Managed version parity` with `Server version parity`, and explain that the current script name is a transitional name:

```markdown
- **Server version parity** -- `managed/server/pyproject.toml` and the FastAPI app
  version agree (`scripts/check_managed_version.py`, transitional name).
```

Completion check: the gate is tied to `server`, not `managed`.

- [ ] **Step 7: Update release automation and rollout order**

Rewrite the `managed` automation paragraph as separate `server`, `ui`, and `compose` target paragraphs:

```markdown
**server** (tag `server-vX.Y.Z`, writes `managed/server/pyproject.toml` +
`managed/server/app/main.py`, updates `managed/server/CHANGELOG.md`, tags the server container image `server-vX.Y.Z`) is a later rollout slice.

**ui** (tag `ui-vX.Y.Z`, writes `managed/ui/package.json`, updates `managed/ui/CHANGELOG.md`, tags the UI container image `ui-vX.Y.Z`) is a later rollout slice.

**compose** (tag `compose-vX.Y.Z`, writes `managed/compose.version`, updates `managed/CHANGELOG.md`) is a later rollout slice for deployment topology.
```

Update the rollout order so it mentions `server`, `ui`, and `compose` configs, apply scripts, gates, baseline tags, and dry-run verification.

Completion check: `managed-v0.1.0` does not appear in the target rollout order.

- [ ] **Step 8: Update baseline tag examples**

Replace the managed baseline example with:

```bash
git tag server-v0.1.0
git push origin server-v0.1.0

git tag ui-v0.1.0
git push origin ui-v0.1.0

git tag compose-v0.1.0
git push origin compose-v0.1.0
```

Completion check: required setup examples cover all four tag namespaces.

## Task 2: Update Contributor Summaries

**Files:**
- Modify: `CONTRIBUTING.md`
- Modify: `README.md`
- Modify: `README.ja.md`
- Optional modify: `README.zh.md`
- Optional modify: `README.ko.md`

- [ ] **Step 1: Update CONTRIBUTING scope table**

Replace the two-product table with:

```markdown
| Scope | Product | Releases | Owns |
|-------|---------|----------|------|
| `(plugin)` | plugin bundle | `plugin-vX.Y.Z` | `skills/`, `hooks/`, `*/plugin.json` |
| `(server)` | managed backend | `server-vX.Y.Z` | `managed/server/app/`, `managed/server/alembic/`, `managed/server/pyproject.toml` |
| `(ui)` | managed admin UI | `ui-vX.Y.Z` | `managed/ui/` |
| `(compose)` | managed deployment topology | `compose-vX.Y.Z` | `managed/docker-compose*.yml`, `managed/dev/` |
```

Then replace the examples sentence with:

```markdown
For example `feat(plugin): ...`, `fix(server): ...`, `feat(ui): ...`, or `fix(compose): ...`.
```

Completion check: `CONTRIBUTING.md` no longer says the repository ships two products.

- [ ] **Step 2: Update README.md release summary**

Replace the first paragraph under `## Versioning and releases` with:

```markdown
The repository ships more than one product, so versions are **product-scoped**:
the plugin bundle is versioned as `plugin-vX.Y.Z`, the managed backend as
`server-vX.Y.Z`, the admin UI as `ui-vX.Y.Z`, and composed deployment topology as
`compose-vX.Y.Z`. Each line is Semantic Versioning automated with
semantic-release from Conventional Commits; the git tag is the source of truth.
The plugin release writes the version into both the Claude Code and Codex
`plugin.json` manifests, kept in lockstep. Legacy bare `vX.Y.Z` tags are
historical plugin tags. This model is being rolled out in stages -- see
[docs/versioning.md](docs/versioning.md) for what is live vs. staged.
```

Completion check: README names all four target tag namespaces.

- [ ] **Step 3: Update README.ja.md release summary**

Replace the paragraph under `## バージョニングとリリース` with:

```markdown
このリポジトリは複数のプロダクトを配布するため、バージョンはプロダクト単位です。
プラグインは `plugin-vX.Y.Z`、managed バックエンドは `server-vX.Y.Z`、管理 UI は
`ui-vX.Y.Z`、compose によるデプロイ構成は `compose-vX.Y.Z` として管理します。
各ラインは Conventional Commits から semantic-release で自動化され、git タグが
真実の源です。このモデルは段階的にロールアウト中です。
[docs/versioning.md](docs/versioning.md) を参照してください。
```

Completion check: Japanese README no longer describes only plugin manifests as the release target.

- [ ] **Step 4: Check other localized README summaries**

Run:

```bash
rg -n "managed-vX\\.Y\\.Z|managed server|managed.*version|plugin-vX\\.Y\\.Z|バージョン|版本|버전" README*.md
```

Expected: any README that mentions product-scoped releases either names the four axes or links to `docs/versioning.md` without stale `managed` release-axis wording.

If `README.zh.md` or `README.ko.md` contains stale product-axis prose, update only that release summary to name `plugin-vX.Y.Z`, `server-vX.Y.Z`, `ui-vX.Y.Z`, and `compose-vX.Y.Z`.

## Task 3: Verify Documentation Consistency

**Files:**
- Modify if needed: files changed in Tasks 1-2 only.

- [ ] **Step 1: Search for stale target-state managed release claims**

Run:

```bash
rg -n "managed-vX\\.Y\\.Z|feat\\(managed\\)|fix\\(managed\\)|docs\\(managed\\)|managed release line|managed-scoped|scope.:.managed|\\(managed\\)" docs README*.md CONTRIBUTING.md .releaserc.json .github/workflows scripts tests
```

Expected: remaining matches are either historical/live-state references to the existing transitional `.releaserc.json` rule or explicit statements that `managed` is superseded as a release axis.

- [ ] **Step 2: Verify four target namespaces are present**

Run:

```bash
rg -n "plugin-vX\\.Y\\.Z|server-vX\\.Y\\.Z|ui-vX\\.Y\\.Z|compose-vX\\.Y\\.Z" docs/versioning.md README.md README.ja.md CONTRIBUTING.md
```

Expected: all four tag namespace strings appear in `docs/versioning.md`, `README.md`, `README.ja.md`, and `CONTRIBUTING.md`.

- [ ] **Step 3: Run focused doc validator**

Run:

```bash
uv run --frozen pytest tests/test_check_doc_test_refs.py -q
```

Expected: tests pass. If dependency setup is unavailable, record the exact failure and run `python3 scripts/check_doc_test_refs.py` as the fallback.

- [ ] **Step 4: Run root tests if local dependencies are available**

Run:

```bash
uv run --frozen pytest -q
```

Expected: tests pass. If local dependency sync is unavailable in the sandbox, record the exact reason and do not claim full verification.

- [ ] **Step 5: Commit implementation**

Run:

```bash
git add docs/versioning.md CONTRIBUTING.md README.md README.ja.md README.zh.md README.ko.md
git commit -S -m "docs(versioning): document four release axes refs #123"
```

Expected: a signed commit containing only documentation changes required by this plan.

## Self-Review Notes

- Spec coverage: the plan updates canonical docs, contributor guidance, README summaries, and verifies the four target tag namespaces.
- Placeholder scan: no `TBD`, `TODO`, or unspecified implementation steps remain.
- Type consistency: product axis names are consistently `plugin`, `server`, `ui`, and `compose`; the old `managed` name is used only as a folder/deployment area or transitional current-state reference.
