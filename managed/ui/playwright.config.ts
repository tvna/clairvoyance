import { defineConfig, devices } from "@playwright/test";

// Runs against the composed e2e topology (e2e/docker-compose.e2e.yml),
// which exposes the front proxy at this fixed port -- the one browser-
// facing origin, matching production's edge path split (design §13).
const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:18080";

export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.spec.ts",
  timeout: 30_000,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL,
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
