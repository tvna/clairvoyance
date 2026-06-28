## Summary

<!-- What this PR does and why it matters. -->

## Changes

<!-- Skills, evals, hooks, docs, or workflows touched. -->

## Verification

- [ ] `waza check` passes (spec, links, schema, token budget)
- [ ] Affected `waza run` suites pass — or noted as blocked with the reason
      (e.g. eval backend quota exhausted; see `docs/evaluations.md`)
- [ ] CI is green (JSON manifests, version consistency, hook scripts)

## Conventional commit

The squash-merge title drives the automated version bump, so it must follow
[Conventional Commits](https://www.conventionalcommits.org/).

- [ ] Title uses a valid type (`feat:`, `fix:`, `docs:`, `chore:`, …) and marks
      breaking changes with `!` or a `BREAKING CHANGE:` footer

## Deferred / follow-ups

<!-- Anything intentionally out of scope. Design rationale and migration plans
     belong in GitHub Issues, not committed docs. -->
