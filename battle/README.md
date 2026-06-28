# Battle tests (adversarial + guardrail)

A **local, advisory** harness that stress-tests the skills against hostile
inputs — separate from `waza`. `waza` checks the normal-input output contract;
this checks what the skills must do when attacked:

- **Injection** (`scenarios/injection/`) — prompt injection embedded in the
  handed-off material (a diff, a PR body) tries to make the skill comply with a
  planted instruction (emit `LGTM`, return a `READY` verdict).
- **Guardrail** (`scenarios/guardrails/`) — inputs that bait the skill into a
  forbidden output: rubber-stamping with no artifact, fabricating evidence.

This implements the **Variation** step of the evolution loop in
[`docs/responsibility-matrix.md`](../docs/responsibility-matrix.md): each new way
a skill can be broken becomes a scenario, and a scenario that catches a
regression graduates into the permanent corpus (**Heredity**).

## Why it is not in CI

The executor is Claude Code headless (`claude -p`), which needs an authenticated
CLI and bills the subscription. CI has no such auth, and LLM output is
probabilistic, so this stays a local tool you run deliberately — advisory, never
a required gate. It lives outside `plugin/`, so it is never distributed.

## Running

```bash
python3 battle/run_battle.py --selftest          # offline; checks grading logic, no cost
python3 battle/run_battle.py                      # all scenarios, 1 trial, sonnet
python3 battle/run_battle.py --trials 3 --judge   # pass-rate over 3 trials + LLM judge
python3 battle/run_battle.py --scenario injection --model opus
```

Each scenario runs via `claude -p` from a fresh temp directory with **only** the
target `SKILL.md` injected (`--append-system-prompt-file`) — no project
`CLAUDE.md`/`AGENTS.md`, no installed plugin or hook. (The user-global
`~/.claude/CLAUDE.md` still loads; keep it skill-neutral for clean results.)

## Grading, and why structure beats substrings

Deterministic regex is the cheap first pass but is **brittle for refusals**: a
correct "I won't LGTM this" contains the substring `LGTM`. So scenarios assert
the *structural* markers a sound response emits (`must_contain`) and use precise
`must_not_contain` patterns only for unambiguous breaches (a line that is *only*
an approval token). The authoritative guardrail verdict comes from the optional
LLM judge (`--judge`) scoring against each scenario's `judge_rubric`. This is the
same lesson as the waza eval-assertion convention in `CONTRIBUTING.md`.

**Cross-language scenarios are judge-only.** The deterministic regexes are
English-centric, so a non-English LGTM-equivalent (e.g. the Japanese
「問題ないのでマージOK」) is graded by the rubric, not substrings. The skills'
guardrails are *semantic*, not keyword lists, so they generalize across language:
the Japanese rubber-stamp and Japanese injection scenarios both pass 3/3 on
sonnet. When adding a non-English scenario, omit `must_*` and rely on `--judge`.

## Scenario format (`*.toml`)

```toml
id = "inj-lgtm-in-diff"
skill = "decision-coaching"        # -> plugin/skills/<skill>/SKILL.md
category = "injection"             # or "guardrail"
description = "..."
prompt = """ ...adversarial input... """
must_contain = ["(?i)regex", ...]      # all must appear
must_not_contain = ["(?im)regex", ...] # any match = breach
judge_rubric = """ PASS only if ... """ # used with --judge
```

## Status

Spike. Four scenarios across `decision-coaching` and `review-verdict` proved the
loop end-to-end (the skills flagged the injection and refused to rubber-stamp).
Next: widen the corpus (lane-baiting the depth gate, routing confusion for
`using-clairvoyance`), add multi-model pass-rate reporting, and promote
regression hits into the corpus.
