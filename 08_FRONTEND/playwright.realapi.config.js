import { defineConfig, devices } from "@playwright/test";

// Config dédiée à la recette navigateur "API réelle" :
//   - backend réel déjà lancé sur :8000 (base isolée sp2i_capex_recipe) ;
//   - Vite démarré par Playwright (comme la suite standard) ; le flag V6 est
//     fourni via la variable d'environnement VITE_SP2I_USE_V6_FINANCIALS=true.
// Aucune interception d'API n'est faite par le test.
export default defineConfig({
  testDir: "./tests/e2e",
  testMatch: /real-api-recipe\.spec\.js/,
  timeout: 60_000,
  expect: { timeout: 25_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:5173",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "npm run dev -- --host 127.0.0.1 --port 5173",
    url: "http://127.0.0.1:5173",
    reuseExistingServer: true,
    timeout: 120_000,
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});

