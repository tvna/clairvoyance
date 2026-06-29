---
name: human-harness
description: Presses a human to confirm a high-blast-radius or compliance-violating instruction before the agent acts, catching human error early. Use when an instruction is irreversible, wide-impact, or breaks a governed rule or safety gate.
---

# Human Harness

The human harness stops a risky instruction and presses the human to confirm intent instead of executing, catching human error before it lands.

**UTILITY SKILL:** invoked as `clairvoyance:human-harness` by `using-clairvoyance` for high-blast-radius or non-compliant instructions.

## Steps

1. Do not execute yet. Name what makes it high-blast-radius or non-compliant: the irreversible operation, governed rule, or safety gate.
2. Measure blast radius and reversibility: what it touches, who it affects, and whether it can be undone and at what cost.
3. Research the repository to settle your own questions first; ask the human only what evidence cannot.
4. Confirm intent one focused question at a time; recommend the safest answer or a safer reversible path, and wait for the reply before the next.
5. Run a premortem: assume it ran and was regretted, then name the failure and its earliest warning signal.
6. For a compliance conflict, surface it; proceed only on the human's explicit, recorded override, never silently complying or refusing.
7. Stay non-shaming; the human keeps authority to proceed after acknowledging the risk.
8. Use portable question handoff: AskUserQuestion when available, else `AskUserQuestion:` text with the same choices.
9. Write in the project owner's language unless a repository rule requires another for outward-facing artifacts.

## Output

Use these headings:

- **Stop:** what the agent is holding back from doing, and why.
- **Blast Radius:** scope, affected surfaces, reversibility, and cost.
- **Compliance:** the rule or gate at stake, or "None - blast radius only".
- **Premortem:** the regret scenario and its earliest warning signal.
- **Safer Path:** the recommended reversible alternative.
- **Confirm:** the single focused question (portable handoff) and recommended answer.
- **Next Move:** what happens per answer - safeguarded proceed, or the safer path.

Pattern: **Stop** -> **Blast Radius** -> **Premortem** -> **Confirm** -> **Next Move**. Add Compliance and Safer Path when relevant. Ask the smallest question that confirms intent without shaming.
