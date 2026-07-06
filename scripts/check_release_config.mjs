import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const PRODUCTS = ["plugin", "server", "ui", "compose"];
const REQUIRED_SUPPRESSIONS = [
  { type: "feat", release: false },
  { type: "fix", release: false },
  { type: "perf", release: false },
  { breaking: true, release: false },
];

function hasRule(rules, expected) {
  return rules.some((rule) =>
    Object.entries(expected).every(([key, value]) => rule[key] === value),
  );
}

for (const product of PRODUCTS) {
  process.env.CLAIRVOYANCE_RELEASE_PRODUCT = product;
  delete require.cache[require.resolve("../release.config.cjs")];
  const config = require("../release.config.cjs");

  if (!config.tagFormat || !Array.isArray(config.plugins)) {
    throw new Error(`${product}: release config missing tagFormat or plugins`);
  }

  const analyzer = config.plugins.find((plugin) =>
    Array.isArray(plugin) && plugin[0] === "@semantic-release/commit-analyzer"
  );
  const rules = analyzer?.[1]?.releaseRules;
  if (!Array.isArray(rules)) {
    throw new Error(`${product}: releaseRules missing`);
  }

  for (const rule of rules) {
    if (
      Object.prototype.hasOwnProperty.call(rule, "scope") &&
      (typeof rule.scope !== "string" || rule.scope.length === 0)
    ) {
      throw new Error(
        `${product}: release rule scope must be a non-empty string: ${JSON.stringify(rule)}`,
      );
    }
  }

  for (const suppression of REQUIRED_SUPPRESSIONS) {
    if (!hasRule(rules, suppression)) {
      throw new Error(`${product}: missing release suppression ${JSON.stringify(suppression)}`);
    }
  }

  for (const expected of [
    { scope: product, breaking: true, release: "minor" },
    { scope: product, type: "feat", release: "minor" },
    { scope: product, type: "fix", release: "patch" },
    { scope: product, type: "perf", release: "patch" },
  ]) {
    if (!hasRule(rules, expected)) {
      throw new Error(`${product}: missing product release rule ${JSON.stringify(expected)}`);
    }
  }

  console.log(`ok: ${product} ${config.tagFormat}`);
}
