---
name: workflow-budget
description: Elicits a hard token budget from the human before launching multi-agent orchestration and threads it into the run as an enforced cap. Use when about to launch a workflow or agent fan-out that spawns multiple subagents, or when a budget gate has blocked the launch.
---

# Workflow Budget

Turns "how much will this run cost" into a human decision made before the tokens are spent, not discovered at a rate limit.

**UTILITY SKILL:** loaded directly before multi-agent orchestration; not routed by `using-clairvoyance` (a budget is not a handoff).

## Steps

1. Estimate before asking: count the planned agents per phase and multiply by a cost band per agent role (heavy readers and finders toward the top of the band, low-effort verifiers toward the bottom). State the total as a range, never a point.
2. Never ask the human to invent a number. Offer 2-3 prepared budgets via portable question handoff (AskUserQuestion when available, otherwise `AskUserQuestion:` text with the same choices): typically a reduced scope, the full plan, and defer - each naming the coverage it buys.
3. Mark the recommended choice and say why.
4. Thread the chosen budget into the launch as `args.budgetTokens`. An answer given inside a question dialog does not bind the harness's native budget ceiling - only a `+N` directive typed in a regular user message does - so the args path is the working contract.
5. Enforce inside the script: check `budget.spent()` against `args.budgetTokens` before each phase and each parallel batch, scale fleet sizes statically from the cap, and `log()` spend at phase boundaries so the human sees the burn live.
6. Split multi-phase work into separate resumable workflows at phase boundaries; a window limit then costs at most one phase, and completed agents replay from cache on resume.
7. With no human present (scheduled or autonomous runs), apply the smallest default that completes the current phase, and record that choice in the run output.

## Output

Use these headings:

- **Estimate:** planned agents x cost band, totalled as a range.
- **AskUserQuestion:** the one budget question (or its text fallback).
- **Choices:** 2-3 named budgets with the coverage each buys.
- **Recommended:** the safest default and why.
- **Enforcement:** how the cap binds: `args.budgetTokens`, the `budget.spent()` guard, and the phase split.

Pattern: **Estimate** -> **AskUserQuestion** -> **Choices** -> **Recommended** -> **Enforcement**. When no human is present, replace **AskUserQuestion**/**Choices** with the recorded default.
