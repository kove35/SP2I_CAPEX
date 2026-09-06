import { defineConfig, devices } from "@playwright/test";

// Temporaire : spec recette contre backend :8001 (code a jour) + frontend :5174.
export default defineConfig({
  testDir: "./tests/e2e",
  testMatch: /real-api-recipe\.spec\.js/,
  timeout: 60_000,
  expect: { timeout: 25_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:5174",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
