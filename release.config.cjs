const product = process.env.CLAIRVOYANCE_RELEASE_PRODUCT;

const PRODUCTS = {
  plugin: {
    tagFormat: "plugin-v${version}",
    changelogFile: "CHANGELOG.md",
    prepareCmd: "node scripts/apply_version.mjs plugin ${nextRelease.version}",
    assets: [".claude-plugin/plugin.json", ".codex-plugin/plugin.json", "CHANGELOG.md"],
  },
  server: {
    tagFormat: "server-v${version}",
    changelogFile: "managed/server/CHANGELOG.md",
    prepareCmd: "node scripts/apply_version.mjs server ${nextRelease.version}",
    assets: ["managed/server/pyproject.toml", "managed/server/app/main.py", "managed/server/CHANGELOG.md"],
  },
  ui: {
    tagFormat: "ui-v${version}",
    changelogFile: "managed/ui/CHANGELOG.md",
    prepareCmd: "node scripts/apply_version.mjs ui ${nextRelease.version}",
    assets: ["managed/ui/package.json", "managed/ui/package-lock.json", "managed/ui/CHANGELOG.md"],
  },
  compose: {
    tagFormat: "compose-v${version}",
    changelogFile: "managed/CHANGELOG.md",
    prepareCmd: "node scripts/apply_version.mjs compose ${nextRelease.version}",
    assets: ["managed/compose.version", "managed/CHANGELOG.md"],
  },
};

if (!product || !PRODUCTS[product]) {
  throw new Error(
    `CLAIRVOYANCE_RELEASE_PRODUCT must be one of ${Object.keys(PRODUCTS).join(", ")}`,
  );
}

const selected = PRODUCTS[product];

function releaseNotesTransform(commit) {
  if (commit.scope !== product) {
    return false;
  }
  return commit;
}

module.exports = {
  branches: ["main"],
  tagFormat: selected.tagFormat,
  plugins: [
    [
      "@semantic-release/commit-analyzer",
      {
        preset: "conventionalcommits",
        releaseRules: [
          { scope: "*", release: false },
          { scope: null, release: false },
          { scope: "", release: false },
          { scope: product, breaking: true, release: "minor" },
          { scope: product, type: "feat", release: "minor" },
          { scope: product, type: "fix", release: "patch" },
          { scope: product, type: "perf", release: "patch" },
        ],
      },
    ],
    [
      "@semantic-release/release-notes-generator",
      {
        preset: "conventionalcommits",
        writerOpts: {
          transform: releaseNotesTransform,
        },
      },
    ],
    [
      "@semantic-release/changelog",
      { changelogFile: selected.changelogFile },
    ],
    [
      "@semantic-release/exec",
      { prepareCmd: selected.prepareCmd },
    ],
    [
      "@semantic-release/git",
      {
        assets: selected.assets,
        message: `chore(release:${product}): ${product}-v\${nextRelease.version} [skip ci]\n\n\${nextRelease.notes}`,
      },
    ],
    "@semantic-release/github",
  ],
};
