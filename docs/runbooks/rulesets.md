# Runbook: managing the `main` ruleset from CI

The `main` branch ruleset is kept as checked-in JSON at
[`.github/rulesets/main.json`](../../.github/rulesets/main.json) and applied by
the [`Apply main ruleset`](../../.github/workflows/apply-rulesets.yml) workflow,
rather than edited by hand in **Settings -> Rules -> Rulesets**. A change to the
required status checks (for example, adding `managed-ui-e2e` so a PR cannot merge
before the e2e job passes) is then reviewed as a PR and applied deterministically.

The decision logic (create-vs-update, diff rendering, retry) lives in
[`scripts/rulesets_apply.py`](../../scripts/rulesets_apply.py) and is unit-tested
against an injected HTTP boundary, so it carries no live-network dependency in CI.

## What the SoT contains

`main.json` is the **entire** ruleset. The apply step issues `PUT`, which
**replaces** the live ruleset in full -- it is not a merge. Any protection that is
live but missing from `main.json` is dropped on apply. Keep every rule you intend
to enforce in the file, not just the checks you are changing.

The shipped baseline enforces, on the default branch:

- no branch deletion, no force-push (`deletion`, `non_fast_forward`);
- a pull request before merge, with review threads resolved and code-owner
  review required (`pull_request`);
- the six CI jobs as required status checks: `validate`, `tests`,
  `managed-server`, `managed-ui`, `managed-ui-e2e`, `tests-windows`.

The status-check `context` values are the CI job names exactly as they appear as
checks. If a job is renamed in `ci.yml`, update the matching `context` here or the
requirement silently stops matching.

## Required secret: `RULESETS_PAT`

`GITHUB_TOKEN` cannot read or write rulesets, so the workflow needs a token with
repository administration rights.

- **Create**: a fine-grained personal access token (Settings -> Developer
  settings -> Fine-grained tokens), scoped to **only this repository**.
- **Permissions**: Repository permissions -> **Administration: Read and write**
  (the rulesets API lives under Administration). Nothing else is needed.
- **Store**: as an Actions secret named `RULESETS_PAT`
  (repository Settings -> Secrets and variables -> Actions). If you gate the
  `ruleset-apply` environment (below), store it as an **environment** secret on
  that environment instead, so it is only readable from an approved run.
- **Expiry / rotation**: set the shortest expiry that fits your cadence (90 days
  is a reasonable default) and rotate on that schedule; the workflow fails loudly
  with a clear error if the secret is missing or unset.
- **Verify the handoff**: run the workflow with `dry_run` checked (the default).
  A successful plan that prints the live-vs-SoT diff into the job summary proves
  the token can read rulesets, without changing anything.

The token value is never echoed. It is passed only as the `GH_TOKEN` env var to
the apply step and sent as a bearer header to `api.github.com`.

## Recommended: gate the `ruleset-apply` environment

The workflow runs in the `ruleset-apply` GitHub Environment. Add **required
reviewers** to that environment (Settings -> Environments -> `ruleset-apply`) so
a mutating apply waits for a second human approval. Until configured, the
environment exists but is unprotected, and the `dry_run` default plus manual
dispatch are the only guardrails.

## Operating procedure

1. **Edit** `.github/rulesets/main.json` and open a PR. CI syntax-checks the file
   in the `validate` job.
2. After merge to `main`, open **Actions -> Apply main ruleset -> Run workflow**,
   run from `main` with **`dry_run` checked**. Read the diff in the job summary.
   - `Action: POST` with `Matches: 0` means **no live ruleset of this name was
     found** -- applying would create a *second* ruleset rather than update the
     existing one. Confirm the `name` in `main.json` matches the live ruleset's
     name before applying (see "First-time bootstrap").
   - `Action: PUT` with `Matches: 1` shows the exact diff that will be applied.
   - `Action: abort` (`Matches: 2+`) means more than one ruleset shares the name;
     resolve that in the UI first -- the tool refuses to guess.
3. When the diff is what you intend, **Run workflow** again with **`dry_run`
   unchecked** to apply. The summary records the resulting ruleset id.

## First-time bootstrap (matching the live ruleset)

Because `PUT` replaces the whole ruleset and matching is by `name`, the very
first apply must reproduce the current protections and use the current name:

1. Run the plan (`dry_run` checked). If `Matches: 1`, the diff shows every field
   that differs between live and `main.json`.
2. Edit `main.json` so the diff shows **only** the change you intend (for the
   initial rollout, only the `managed-ui-e2e` addition to
   `required_status_checks`). If the live ruleset uses a different `name`, set
   `main.json`'s `name` to match it so the tool updates in place instead of
   creating a duplicate.
3. Re-plan until the diff is clean, then apply.
