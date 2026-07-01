# Clairvoyance

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/tvna/clairvoyance)
[![codecov](https://codecov.io/gh/tvna/clairvoyance/branch/main/graph/badge.svg)](https://codecov.io/gh/tvna/clairvoyance)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[English](./README.md) | [日本語](./README.ja.md) | [简体中文](./README.zh.md) | [한국어](./README.ko.md)

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
| `human-harness` | The human harness: a human gives a high-blast-radius, irreversible, or compliance-violating instruction. Instead of executing, it stops and presses the human to confirm intent one question at a time to catch human error before it lands. |
| `session-handoff` | A clean restart beats trusting the harness's compaction, repository gates limit what this session can change, or work is unfinished — the next session needs a paste-ready prompt to resume. |

Each handoff branches by stakes: reversible, low-risk calls get a compact
`Verdict` + `Next Move`; irreversible or contested calls get the full handoff.

`session-handoff` is different — it hands off to the next agent session, not a
human. See [docs/session-handoff.md](docs/session-handoff.md) for why it exists and
when to prefer it over the harness's automatic compaction.

## Install

Clairvoyance ships one plugin tree with a manifest for each runtime
(`.claude-plugin/` and `.codex-plugin/`), so the same skills install
through whichever path your agent uses.

### Claude Code

Add the marketplace and install the plugin:

```
/plugin marketplace add tvna/clairvoyance
/plugin install clairvoyance
```

### Codex

Add the repository marketplace and install the plugin with the Codex CLI:

```
codex plugin marketplace add tvna/clairvoyance
codex plugin add clairvoyance
```

The repository marketplace lives at [.agents/plugins/marketplace.json](.agents/plugins/marketplace.json),
and Codex reads the `.codex-plugin/plugin.json` manifest.

### apm (any supported agent)

[`microsoft/apm`](https://github.com/microsoft/apm) installs Clairvoyance as a
marketplace plugin and deploys its skills into every agent it detects (Claude
Code, Codex, and more):

```bash
apm install tvna/clairvoyance
```

To pin it for a project, add the dependency to your `apm.yml` and run `apm install`:

```yaml
dependencies:
  apm:
    - tvna/clairvoyance
```

### What the hook does

The plugin registers a `SessionStart` hook that injects the `using-clairvoyance`
bootstrap skill (and the project owner's language) at session start, clear, and
compaction. Claude Code reads `hooks/hooks.json` and Codex reads
`hooks/codex-hooks.json`; both route through the same
`hooks/run-hook.cmd` wrapper, differing only in the plugin-root variable each
runtime substitutes. See [docs/hooks.md](docs/hooks.md).

## Repository layout

The plugin lives at the **repository root** (`source: "./"`), the layout apm
requires — it deploys skills from `skills/` and hooks from `hooks/` at the package
root. Only those primitives are deployed into a consumer's agent; tests, tooling,
CI, docs, and eval suites are carried in the repository for development but never
deployed. See [docs/repository-layout.md](docs/repository-layout.md) for the full
tree.

## Development

- **Validate skills:** `waza check` (static; no eval backend or quota required).
- **Run evals:** `waza run` — see [docs/evaluations.md](docs/evaluations.md) for
  the execution backend and what to do when its quota is exhausted.
- **CI** validates JSON manifests and hook scripts on every pull request — no
  external services needed. The script test suite runs with coverage; the gate
  is local (`--cov-fail-under=100` in `pyproject.toml`) and results are also
  reported to [Codecov](https://codecov.io/gh/tvna/clairvoyance) for trend
  history (informational, never blocking).

## Versioning and releases

Semantic Versioning, automated with semantic-release from Conventional Commits.
The git tag is the source of truth; each release writes the version into both
the Claude Code and Codex `plugin.json` manifests, kept in lockstep. See
[docs/versioning.md](docs/versioning.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Commits must follow Conventional Commits —
they drive the automated version bump.

## License

MIT. See [LICENSE](LICENSE).
