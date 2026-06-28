# Clairvoyance

A force multiplier for agent-to-human handoffs, turning work into evidence-backed
decisions humans can trust.

Clairvoyance is a Claude Code plugin: a set of Agent Skills that an agent loads
when it needs to hand a decision back to a human. Each handoff makes state visible
by inspection — evidence, system context, options, risks, reversibility, and a
recommended next move — so the human can approve, reject, or safely disagree.

## Skills

| Skill | Use when |
|-------|----------|
| `using-clairvoyance` | SessionStart bootstrap router. Picks one handoff skill below; injected by the SessionStart hook. |
| `clairvoyance` | A human-owned choice blocks the agent: decision, approval, deferral, rollback, or 2–3 prepared options. |
| `review-verdict` | A PR, commit, branch, working tree, or merge candidate needs a readiness verdict with evidence. |
| `architecture-tradeoff` | A system-level architecture decision between options, boundaries, dependencies, or failure modes. |
| `decision-coaching` | A human asks for LGTM / rubber-stamp on ambiguous, noisy, or architecture-poor input. |
| `session-handoff` | A clean restart beats trusting the harness's compaction, repository gates limit what this session can change, or work is unfinished — the next session needs a paste-ready prompt to resume. |

Each handoff branches by stakes: reversible, low-risk calls get a compact
`Verdict` + `Next Move`; irreversible or contested calls get the full handoff.

`session-handoff` is different — it hands off to the next agent session, not a
human. See [docs/session-handoff.md](docs/session-handoff.md) for why it exists and
when to prefer it over the harness's automatic compaction.

## Install

Add the marketplace and install the plugin in Claude Code:

```
/plugin marketplace add tvna/clairvoyance
/plugin install clairvoyance
```

The plugin registers a `SessionStart` hook that injects the `using-clairvoyance`
bootstrap skill (and the project owner's language) at session start, clear, and
compaction. See [docs/hooks.md](docs/hooks.md).

## Repository layout

The marketplace points at `plugin/` (`source: "./plugin"`), so **only `plugin/` is
copied to a user's install cache**. Everything outside it — contributor
instructions (`AGENTS.md`), tests, dev tooling, CI, and docs — stays in the
repository and is never distributed.

```
.claude-plugin/            marketplace.json (the marketplace manifest)
plugin/                    the distributed plugin — only this ships
  .claude-plugin/          plugin.json (plugin manifest, version source of truth)
  skills/                  one directory per skill (SKILL.md + references/)
  hooks/                   SessionStart hook and cross-platform entry point
  evals/                   waza evaluation suites, one per skill
AGENTS.md                  imported agent instructions (synced; not shipped)
scripts/ tests/            validators and their pytest suite (not shipped)
docs/ .github/             documentation, CI, release automation (not shipped)
```

## Development

- **Validate skills:** `waza check` (static; no eval backend or quota required).
- **Run evals:** `waza run` — see [docs/evaluations.md](docs/evaluations.md) for
  the execution backend and what to do when its quota is exhausted.
- **CI** validates JSON manifests and hook scripts on every pull request — no
  external services needed.

## Versioning and releases

Semantic Versioning, automated with semantic-release from Conventional Commits.
The git tag is the source of truth; each release writes the version into
`plugin.json` (the manifest Claude Code reads). See
[docs/versioning.md](docs/versioning.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Commits must follow Conventional Commits —
they drive the automated version bump.

## License

MIT. See [LICENSE](LICENSE).
