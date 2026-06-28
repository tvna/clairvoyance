// Write the release version into the plugin manifests — the single in-repo home
// for the version. Invoked by @semantic-release/exec's prepareCmd with the next
// version as the only argument; the git tag remains the source of truth and this
// keeps the manifests Claude Code and Codex read at the installed ref in
// agreement. Both must move together or one runtime installs a stale version.
import { readFileSync, writeFileSync } from "node:fs";

const MANIFESTS = [
  "plugin/.claude-plugin/plugin.json",
  "plugin/.codex-plugin/plugin.json",
];
const version = process.argv[2];

// semantic-release guarantees a valid semver; guard only the misconfiguration
// case where the argument never arrives.
if (!version) {
  console.error("apply_version: expected a version argument from semantic-release");
  process.exit(1);
}

for (const manifest of MANIFESTS) {
  const data = JSON.parse(readFileSync(manifest, "utf8"));
  data.version = version;
  // 2-space indent + trailing newline matches the repo's JSON style and keeps
  // the release commit's diff to the single version line.
  writeFileSync(manifest, `${JSON.stringify(data, null, 2)}\n`);
  console.log(`apply_version: ${manifest} -> ${version}`);
}
