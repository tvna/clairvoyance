# Fable session operations

Notes for contributors driving Fable/Mythos-tier agent sessions against this
repository — design sessions, large recon sweeps, multi-agent verification.
This page is about operating the **current** session on a Fable-tier model.
The complementary concern — optimizing a handoff **for** a Fable next-session —
belongs to `session-handoff` and its `references/fable-optimization.md`; it is
referenced here by name and deliberately not repeated (drift rule, see
[responsibility-matrix.md](responsibility-matrix.md)).

Some items below are harness-general, but they matter most under Fable-tier
session limits, which is where they were learned (observed 2026-07 during the
unknowns-mapping design session, #126).

## 1. Session limits bound subagent fan-out, not inline work

A parallel recon workflow (~15 subagents: readers plus adversarial finders)
hit the session token limit twice — the second window died mid-verification
after roughly 1.3M subagent tokens. Throughout both interruptions, main-loop
work (file reads, edits, small shell checks) kept functioning.

Consequences:

- Put **load-bearing verification in the main loop**: first-hand reads of the
  cited files, with `file:line` citations. Use subagent fan-out for breadth
  (discovery, lens diversity), where a partial failure costs coverage, not
  correctness.
- Know the limit-reset time before launching a long fan-out. A run that dies
  mid-phase resumes cleanly (next section) but the wall-clock is lost.
- Small containers serialize big fan-outs: subagent concurrency is capped by
  the environment's CPU count, so a wide fan-out on a small box runs mostly
  sequentially and holds the session limit exposure open for longer.

## 2. Prefer resumable orchestration for long fan-outs

Workflow resume (same script, same run id) replayed every completed agent from
cache instantly and free; only the failed agents re-ran. In the observed run,
2 cached readers replayed and 13 previously-failed agents completed on the
second window without re-paying for the finished work.

Consequence: structure long fan-outs so each agent call is **deterministic** —
same prompt and options on re-run — because the resume cache keys on them.
Keep timestamps and randomness out of agent prompts.

## 3. Verification fallback when the machine pass dies

When an adversarial verify pass cannot run at all (session limits, backend
quota), the completion path that kept the deliverables grounded:

1. **First-hand verify every claim actually used** in a deliverable: read the
   cited file, check the quoted line. Claims that are collected but unused do
   not need this.
2. Treat independent rediscovery of the same fact by parallel finder lenses as
   **corroboration, not confirmation**.
3. **Tag anything unverifiable as speculation** inside the deliverable itself,
   next to the claim — not in a footnote the reader can miss.
4. **Route residual unknowns into the next measurable step** (for example, an
   ablation run that will answer them empirically) instead of dropping them.

This is the same fact/speculation separation the skills already mandate, and
the same genre of quota-fallback operations documented for the waza lane in
[evaluations.md](evaluations.md).

## Related knowledge (by reference only)

- Handing off **to** a Fable session, and Fable-specific degradation behavior:
  `skills/session-handoff/SKILL.md` and its `references/fable-optimization.md`.
- Handing off **from** a Fable session to another model: the standard handoff
  applies; see the model-confirmation rules in `session-handoff`.
