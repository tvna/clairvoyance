// Write a product release version into the runtime files that advertise it.
// Invoked by @semantic-release/exec's prepareCmd as:
//   node scripts/apply_version.mjs <product> <version>
//
// The git tag remains the source of truth; these files are release artifacts that
// let installed manifests, OpenAPI metadata, package metadata, or compose
// topology markers agree with the tag at the released ref.
import { readFileSync, writeFileSync } from "node:fs";

const [, , firstArg, secondArg] = process.argv;
const product = secondArg ? firstArg : "plugin";
const version = secondArg ?? firstArg;

if (!version) {
  console.error("apply_version: expected <product> <version>");
  process.exit(1);
}

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

function writeJson(path, data) {
  writeFileSync(path, `${JSON.stringify(data, null, 2)}\n`);
  console.log(`apply_version: ${path} -> ${version}`);
}

function updateJsonVersion(path) {
  const data = readJson(path);
  data.version = version;
  writeJson(path, data);
}

function updatePackageLock(path) {
  const data = readJson(path);
  data.version = version;
  if (data.packages?.[""]) {
    data.packages[""].version = version;
  }
  writeJson(path, data);
}

function replaceText(path, pattern, replacement) {
  const text = readFileSync(path, "utf8");
  if (!pattern.test(text)) {
    console.error(`apply_version: ${path}: expected version pattern not found`);
    process.exit(1);
  }
  writeFileSync(path, text.replace(pattern, replacement));
  console.log(`apply_version: ${path} -> ${version}`);
}

function updateServerPyproject() {
  replaceText(
    "managed/server/pyproject.toml",
    /^version = "[^"]+"$/m,
    `version = "${version}"`,
  );
}

function updateServerFastApiVersion() {
  replaceText(
    "managed/server/app/main.py",
    /(FastAPI\([\s\S]*?\bversion\s*=\s*)["'][^"']+["']/,
    `$1"${version}"`,
  );
}

const APPLY = {
  plugin() {
    updateJsonVersion(".claude-plugin/plugin.json");
    updateJsonVersion(".codex-plugin/plugin.json");
  },
  server() {
    updateServerPyproject();
    updateServerFastApiVersion();
  },
  ui() {
    updateJsonVersion("managed/ui/package.json");
    updatePackageLock("managed/ui/package-lock.json");
  },
  compose() {
    writeFileSync("managed/compose.version", `${version}\n`);
    console.log(`apply_version: managed/compose.version -> ${version}`);
  },
};

if (!APPLY[product]) {
  console.error(`apply_version: unknown product '${product}'`);
  process.exit(1);
}

APPLY[product]();
