# Human harness

`human-harness` pauses a high-blast-radius, irreversible, or compliance-violating
instruction and makes the human confirm intent before the agent executes, so a
human error is caught before it lands. See the skill at
[`plugin/skills/human-harness/SKILL.md`](../plugin/skills/human-harness/SKILL.md),
the worked example at
[`plugin/skills/human-harness/references/example.md`](../plugin/skills/human-harness/references/example.md),
and the compliance judgment at
[`plugin/skills/human-harness/references/compliance.md`](../plugin/skills/human-harness/references/compliance.md).

## It is one layer, not the whole defense

The skill is a **prompt-time, agent-judgment** control: it only fires if the agent
recognizes the instruction as risky and chooses to apply it. That makes it a single
point of failure on its own — one misclassification, a truncated context, or a
prompt-injected "skip the harness" and the pause never happens.

`AGENTS.md` is explicit that this layer must not stand alone: §4 "preserve
defense-in-depth … do not collapse those layers," and §3 "if the gate is missing,
build it before the operation it guards; never substitute agent memory for an
absent gate." The measures below prevent human error but **cannot live inside the
skill** — they belong to the harness, process, and eval lanes (see
[responsibility-matrix.md](responsibility-matrix.md)). The skill should be backed
by them, not replace them.

## Measures that belong outside the skill

### Deterministic gates (harness lane)

- **Backstop the riskiest verbs in a gate, not a prompt.** A `PreToolUse` hook,
  pre-commit check, branch protection, or CI rule that blocks force-push to a
  protected branch, `DROP`/destructive migrations, and secrets in a commit still
  catches the action when the agent fails to self-invoke the skill.
- **Make detection deterministic.** The skill relies on the agent classifying an
  instruction as high-blast-radius. A denylist/classifier keyed on the §4
  irreversible-operation category (deletes, force-push, sends, payments, schema
  migrations, key rotation, DNS, bulk notification, data export) removes the
  reliance on judgment.
- **Secret-exposure floor.** The non-overridable case (a secret in a commit, log,
  or PR) must be enforced by a secret-scanning preflight, not only by the agent
  recognizing it in the moment.

### Tooling and process

- **Dry-run / preview must be produced by tools.** The skill can demand an
  inspectable preview (rows matched, samples, the revert plan), but the real
  `--dry-run` artifact is a tooling concern.
- **Prepare reversibility before acting.** Snapshot, backup, feature flag, or
  transaction must be created by tooling/runbook before the irreversible step;
  the skill can require it but cannot perform it.
- **Durable override record.** "Explicit, recorded override" needs a durable
  artifact (issue comment, commit trailer, audit log) so the authorization is
  inspectable later — chat is ephemeral.
- **Two-person rule and cool-down for the top tier.** A required second reviewer
  (branch protection), a change-freeze, or a short delay on the highest-blast-radius
  actions is a platform/process control, not a prompt.
- **Guard external and contextual side effects.** Send-allowlists, rate limits,
  payment confirmations, and verifying the active target environment (right
  command, wrong prod) live in the systems and credentials themselves.

### Calibration and compounding (eval lane)

- **Test that the harness does not over-fire.** Alert fatigue defeats the control:
  a negative/precision eval should prove a routine, reversible instruction passes
  without the full ceremony. Today the suite is all positive cases.
- **Graduate each catch into a gate.** Per `AGENTS.md` §3's retrospective, a class
  of instruction the harness catches by judgment repeatedly should become a durable
  deterministic gate, so protection compounds instead of resting on the prompt
  forever.

## Origin

The lane split (skill instruction vs harness vs doc) and the defense-in-depth and
gap-analysis discipline are adapted from
[tvna/claude-md](https://github.com/tvna/claude-md); see
[responsibility-matrix.md](responsibility-matrix.md).
