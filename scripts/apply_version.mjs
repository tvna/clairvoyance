// Write the release version into the plugin manifest — the single in-repo home
// for the version. Invoked by @semantic-release/exec's prepareCmd with the next
// version as the only argument; the git tag remains the source of truth and this
// keeps plugin.json (which Claude Code reads at the installed ref) in agreement.
//
// marketplace.json deliberately carries no version: Claude Code resolves
// plugin.json first, and the docs warn against setting it in both places.
import { readFileSync, writeFileSync } from "node:fs";

const MANIFEST = "plugin/.claude-plugin/plugin.json";
const version = process.argv[2];

if (!version || !/^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/.test(version)) {
  console.error(`apply_version: expected a semver argument, got: ${version ?? "(none)"}`);
  process.exit(1);
}

const manifest = JSON.parse(readFileSync(MANIFEST, "utf8"));
manifest.version = version;
// 2-space indent + trailing newline matches the repo's JSON style and keeps the
// release commit's diff to the single version line.
writeFileSync(MANIFEST, `${JSON.stringify(manifest, null, 2)}\n`);
console.log(`apply_version: ${MANIFEST} -> ${version}`);
