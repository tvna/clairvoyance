---
name: human-harness
description: Prevents human error before a major incident by pausing a risky instruction to confirm intent. Use when an instruction is high-blast-radius, irreversible, or breaks a governed rule or safety gate.
---

# Human Harness

The human harness stops a risky instruction and presses the human to confirm intent instead of executing, catching human error before it lands.

**UTILITY SKILL:** invoked as `clairvoyance:human-harness` by `using-clairvoyance` for high-blast-radius or non-compliant instructions.

## Steps

1. Do not execute yet. Name what makes it high-blast-radius or non-compliant: the irreversible operation, governed rule, or safety gate.
2. Measure blast radius and reversibility: what it touches, who it affects, and whether it can be undone and at what cost.
3. Research the repository to settle your own questions first; ask the human only what evidence cannot.
4. Hand a decision-ready choice, not a raw question: prove the candidate outcomes, then offer reversible named options with a recommendation and the trade-off. Refuse a rubber-stamp - the human confirms by restating the irreversible outcome, not a bare yes, one focused question at a time.
5. Run a premortem: assume it ran and was regretted, then name the failure and its earliest warning signal.
6. For a compliance conflict, judge whether the rule is overridable. A human-owned risk decision may proceed on an explicit, recorded override; a mandatory safety gate or trusted-instruction floor (a secret, a security control) is not waivable by acknowledgment - route it to a safe alternative or refuse. Never silently do either.
7. Stay non-shaming; for an overridable risk the human keeps authority to proceed after acknowledging it.
8. Use portable question handoff: AskUserQuestion when available, else `AskUserQuestion:` text with the same choices.
9. Write in the project owner's language unless a repository rule requires another for outward-facing artifacts.

## Output

Use these headings:

- **Stop:** what the agent is holding back from doing, and why.
- **Blast Radius:** the concrete affected objects (branches, row counts, recipients) with canonical URLs and reversibility cost, so the human detects the anomaly by inspection, not prose.
- **Compliance:** the rule or gate at stake and whether it is overridable, or "None - blast radius only".
- **Premortem:** the regret scenario and its earliest warning signal.
- **Safer Path:** a prepared, proven, reversible alternative offered as a named option.
- **Confirm:** the human confirms by restating the irreversible outcome (no bare LGTM); the focused question and recommended answer.
- **Next Move:** what happens per answer - safeguarded proceed, or the safer path.

Pattern: **Stop** -> **Blast Radius** -> **Premortem** -> **Confirm** -> **Next Move**. Add Compliance and Safer Path when relevant.
