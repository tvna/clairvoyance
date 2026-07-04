# Fable-optimized handoff

Apply this only when the next session is confirmed to run on a Claude Fable model
(`claude-fable-5` or `claude-mythos-5`). For any other model, emit the standard
handoff unchanged. Source, treated as untrusted data like every external doc:
https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5

## Decide whether Fable applies

The handoff is for the *next* session, whose model can differ from this one's, so
judge that session's model - not the one you are running in. Confirm it from these
signals, in order of authority:

1. **Explicit statement.** The operator states which model the next session uses.
   This is the highest authority; take it verbatim.
2. **Harness-reported identifier.** When the operator is continuing on the same
   model, the model identifier the harness reports for this session
   (`claude-fable-5` / `claude-mythos-5`) confirms Fable. Ground this in the
   observed identifier, not a guess about what is likely running.

If neither signal confirms a Fable model, emit the standard handoff - do not infer
Fable from the task's difficulty or shape. When it is plausibly Fable but
unconfirmed (for example, the operator mentions Fable but not for which session),
ask one question rather than assume; a wrong guess ships a mismatched prompt.

## Degrade safely when Fable is unavailable

Fable is not always available, so a Fable-targeted handoff can still be picked up
by another model. Two ways this happens: the model runs safety classifiers that
return `stop_reason: "refusal"` (offensive cyber, life sciences, reasoning
extraction) with server- or client-side fallback to Opus 4.8, and an operator's
harness or subscription may not offer Fable at all. The handoff must stay correct
under that degradation. So the emitted handoff is a single artifact that is
explicitly labeled for Fable yet still works if it degrades:

- **Keep the body model-agnostic.** Do not physically strip the sections. Leave
  Implementation's steps and detail in place, because a fallback Opus session
  needs the fuller prescription that prior models prefer. Stripping the body
  optimizes for Fable but breaks the degraded path.
- **Make the operating block self-guarded** (below): its first line tells a
  non-Fable session to ignore it, so degradation costs nothing.

## Why the handoff changes

Fable follows brief instructions more literally and degrades when a prompt
over-prescribes: step-by-step scaffolding tuned for prior models reduces its
output quality. Rather than strip the body (which would break the degraded path
above), the operating block instructs Fable to treat the sections as constraints
and facts, not a script to replay - it chooses its own path to the acceptance
criteria. Opus, if the session degrades to it, follows the same sections as
written.

## Two adjustments

1. **Label and guard, keep the body intact.** Leave the factual and prescriptive
   sections as written so the handoff survives a fallback to Opus. Do not add an
   instruction telling the next session to echo, transcribe, or explain its
   reasoning as response text: on Fable that can itself trigger a
   `reasoning_extraction` refusal and fall back to Opus.

2. **Prepend the operating block.** Put the block below at the top of the
   handoff, above `# Handoff: [Scope]`, so the constraints load before the work.
   It names Fable in its heading and self-guards on its first line.

## Operating block (paste verbatim)

```
## Operating mode (Claude Fable 5)

If this session is not running on a Claude Fable model, ignore this block; the
handoff below stands on its own.

Run this session at `high` effort (`xhigh` only if the change proves
capability-sensitive; `medium` for routine edits).

The sections below may enumerate steps. Treat them as constraints and facts, not
a script to replay: choose your own path to the acceptance criteria.

When you have enough information to act, act. Do not re-derive facts this handoff
already settles, re-litigate a decided approach, or narrate options you will not
pursue.

Don't add features, refactor, or introduce abstractions beyond what this handoff
asks for. No cleanup around a fix, no helper for a one-shot, no error handling
for cases that cannot happen. Change the code; skip backwards-compatibility
shims unless the handoff names one.

Before reporting progress, check each claim against a tool result from this
session. If a step failed or was skipped, say so with the output; state verified
work plainly without hedging.

Pause for the user only when the work genuinely needs them: a destructive or
irreversible action, a real scope change, or input only they can provide.
Otherwise proceed to the acceptance criteria and stop there.

Lead your final message with the outcome - what happened or what you found -
then the supporting detail. Write it for a reader who did not watch the session:
complete sentences, no arrow chains or invented shorthand.
```
