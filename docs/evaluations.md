# Evaluations

Skills are evaluated with [`waza`](https://github.com/) suites under `evals/`, one
per skill. There are two distinct commands with very different requirements.

## `waza check` — static, always available

```bash
waza check
```

Validates spec, links, schema, and the per-skill token budget. It needs no LLM
backend and no quota, so it is the dependable gate for CI and pre-PR validation.

## `waza run` — live, backend-bound

```bash
waza run                          # all suites
waza run evals/<skill>/eval.yaml  # one suite
```

`waza run` executes through an **embedded GitHub Copilot CLI** (`executor:
copilot-sdk`). Even though the suites request a Claude model
(`model: claude-sonnet-4.6`), the calls are billed against the GitHub Copilot
subscription's premium-request quota — **not** the Anthropic API. There is no
Anthropic-direct executor; `executor` accepts only `copilot-sdk` or `mock`.

### When the backend quota is exhausted

A depleted Copilot quota returns `402 quota_exceeded`, often as empty outputs
(`tools: []`, ~2s runs). Options:

1. Keep `waza check` as the gate (works without quota).
2. Validate behavior on the Claude side without `waza`: take each eval task's
   `inputs.prompt`, run it through Claude Code, and grep the output against that
   task's `expected.output_contains` / `output_not_contains`. This is a same-model
   smoke test, not the `waza` LLM grader, but it confirms the skill's output
   contract.
3. Restore the real harness: re-authenticate Copilot to an account with quota,
   wait for the monthly reset, or upgrade the plan.

## Writing assertions

Assert the **structural markers a skill reliably emits** — the bold headings its
output contract defines (`Verdict`, `Evidence`, `Premortem`, `AskUserQuestion`,
`Recommended`, …) — plus `output_not_contains` guardrails (for example, refusal
phrases a coaching skill must never produce).

Avoid asserting brittle concept keywords (`subject`, `architecture`, `future`)
that depend on the model's phrasing: they flicker at `trials_per_task: 1` even when
the output is correct. Test what the skill controls, robustly.
