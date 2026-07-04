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

## Why the handoff changes

Fable follows brief instructions more literally and degrades when a prompt
over-prescribes. Step-by-step scaffolding tuned for prior models reduces its
output quality, so a Fable handoff states the goal and the constraints and lets
the model choose the path, rather than enumerating micro-steps.

## Two adjustments

1. **De-prescribe the body.** Keep the factual sections verbatim - Context,
   Files to read, Verification, Acceptance criteria are evidence, not
   prescription. In Implementation, state the outcome and the constraints (the
   minimum-sufficient change, what not to touch) but drop ordered micro-steps;
   let Fable determine the path. Do not add an instruction telling the next
   session to echo, transcribe, or explain its reasoning as response text: on
   Fable that can trigger a `reasoning_extraction` refusal and fall back to
   Opus.

2. **Prepend the operating block.** Put the block below at the top of the
   handoff, above `# Handoff: [Scope]`, so the constraints load before the work.

## Operating block (paste verbatim)

```
## Operating mode (Claude Fable 5)

Run this session at `high` effort (`xhigh` only if the change proves
capability-sensitive; `medium` for routine edits).

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
