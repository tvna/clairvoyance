# Repository layout

The marketplace points at `plugin/` (`source: "./plugin"`), so **only `plugin/` is
copied to a user's install cache**. Everything outside it — contributor
instructions (`AGENTS.md`), tests, dev tooling, CI, and docs — stays in the
repository and is never distributed.

```
.claude-plugin/            marketplace.json (Claude Code marketplace manifest)
.agents/plugins/           marketplace.json (Codex marketplace manifest)
plugin/                    the distributed plugin — only this ships
  .claude-plugin/          plugin.json (Claude Code manifest, version source of truth)
  .codex-plugin/           plugin.json (Codex manifest, kept in version lockstep)
  skills/                  one directory per skill (SKILL.md + references/)
  hooks/                   SessionStart hooks (hooks.json + codex-hooks.json) and entry point
  evals/                   waza evaluation suites, one per skill
AGENTS.md                  imported agent instructions (synced; not shipped)
scripts/ tests/            validators and their pytest suite (not shipped)
codecov.yml                Codecov dashboard config (informational; not shipped)
docs/ .github/             documentation, CI, release automation (not shipped)
```
