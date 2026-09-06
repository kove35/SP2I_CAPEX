import { defineConfig, devices } from "@playwright/test";

// Campagne recette : backend reel :8001 + frontend :5174 (deja actifs).
export default defineConfig({
  testDir: "./tests/e2e",
  testMatch: /real-api-campaign(-c7-simulation)?\.spec\.js/,
  timeout: 90_000,
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
