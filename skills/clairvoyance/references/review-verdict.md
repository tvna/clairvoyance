# Review Verdict

Use this for PR, commit, branch, or working-tree reviews when the human wants a readiness judgment.

## Evidence Map

Trace the changed surface to:

- Entry points.
- Callers and callees.
- Tests and missing tests.
- Dependency contracts.
- User-facing behavior.
- Migration, rollout, or rollback concerns.

## Verdict Shape

- **Ready / Not Ready / Needs Human Decision:** pick one.
- **Findings:** order by severity, with file or URL evidence.
- **Coverage:** what was reviewed and what was not.
- **Residual Risk:** what could still fail.
- **Recommendation:** merge, fix first, investigate, defer, or close.

## Quality Bar

Do not issue a diff-only verdict. The human needs the system path from change to consequence.
