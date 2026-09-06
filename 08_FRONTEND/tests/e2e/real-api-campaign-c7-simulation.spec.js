// SUITE C7 — SIMULATION (étiquetée) : erreurs/délais contrôlés via page.route.
// Ce n'est PAS une recette intégrale backend réel : les réponses sont
// interceptées uniquement pour ces scénarios de robustesse.
import { test, expect } from "@playwright/test";

async function loginUi(page, email, password) {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.getByPlaceholder("vous@organisation.com").fill(email);
  await page.getByPlaceholder("Minimum 12 caracteres").fill(password);
  await page.locator("form.landing-login-card").getByRole("button", { name: /Se connecter/i }).click();
  await page.waitForURL(/\/app/, { timeout: 25000 });
}

test("SIMULATION C7a : erreur API distincte du vide", async ({ page }) => {
  await page.route("**/analytics/v6/dashboard*", (route) =>
    route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ detail: "boom" }) }));
  await loginUi(page, "admin@recette.local", "Admin123!");
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });
  const card = page.getByTestId("project-card").filter({ hasText: "Projet A synthetique" });
  await card.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await page.waitForURL(/\/app(\?|$)/, { timeout: 20000 });
  await expect(page.locator(".app-error, .error-message").first()).toBeVisible({ timeout: 20000 });
  const emptyBanner = await page.getByText(/Aucune donnée pour ce projet/).count();
  expect(emptyBanner).toBe(0);
});

test("SIMULATION C7b : valeur null ratio != zero (ratio indisponible)", async ({ page }) => {
  await page.route("**/analytics/v6/dashboard*", async (route) => {
    const response = await route.fetch();
    const json = await response.json();
    if (json?.kpis) {
      json.kpis.capex_m2 = null;
      json.kpis.total_project_cost_per_m2 = null;
    }
    await route.fulfill({ response, json });
  });
  await loginUi(page, "admin@recette.local", "Admin123!");
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });
  const card = page.getByTestId("project-card").filter({ hasText: "Projet A synthetique" });
  await card.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await page.waitForURL(/\/app(\?|$)/, { timeout: 20000 });
  const m2Card = page.locator(".advanced-kpi-card").filter({ hasText: "FCFA/m2" });
  await expect(m2Card).toContainText("Indisponible", { timeout: 25000 });
  const cap = page.locator(".advanced-kpi-card").filter({ hasText: "CAPEX Direct" });
  await expect(cap).toContainText("3 000 FCFA", { timeout: 25000 });
  await expect(m2Card.locator("svg.kpi-sparkline")).toHaveCount(0);
});
