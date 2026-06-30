# Repository layout

The plugin lives at the **repository root** (`source: "./"`), the layout apm
requires: it discovers and deploys skills from `skills/` and hooks from `hooks/`
at the package root, so those directories sit at the top level rather than inside
a `plugin/` subdirectory. Claude Code and Codex point their marketplace manifests
at the same root, so the same skills install through whichever path your agent
uses.

Only **skills and hooks** are deployed as runtime primitives; everything else —
contributor instructions (`AGENTS.md`), tests, dev tooling, CI, docs, and eval
suites — is carried in the repository for development but is never deployed into
a consumer's agent.

```
.claude-plugin/            marketplace.json + plugin.json (Claude Code manifests; plugin.json is the version source of truth)
.codex-plugin/             plugin.json (Codex manifest, kept in version lockstep)
.agents/plugins/           marketplace.json (Codex/agents marketplace manifest)
skills/                    one directory per skill (SKILL.md + references/) — deployed by apm/Claude/Codex
hooks/                     SessionStart hooks (hooks.json + codex-hooks.json) and entry point — deployed as a hook
evals/                     waza evaluation suites, one per skill (not deployed)
AGENTS.md                  imported agent instructions (synced; not deployed)
scripts/ tests/            validators and their pytest suite (not deployed)
codecov.yml                Codecov dashboard config (informational; not deployed)
docs/ .github/             documentation, CI, release automation (not deployed)
```

> **Why the root, not a `plugin/` subdirectory?** apm installs a dependency like
> `tvna/clairvoyance` by fetching the whole repository and discovering skills at
> the package root (`skills/<name>/SKILL.md`). A nested `plugin/skills/` is not on
> that search path, so apm would deploy nothing. Keeping the plugin at the root —
> the same structure [`obra/superpowers`](https://github.com/obra/superpowers)
> uses — makes `apm install` deploy every skill into `.claude/skills/` and record
> them in `apm.lock.yaml`, while Claude Code's `/plugin marketplace add` continues
> to work against the same root.
