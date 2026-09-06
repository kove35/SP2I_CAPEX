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

test("SIMULATION C7c : reponse tardive de A n'ecrase pas B", async ({ page }) => {
  let releaseA;
  const gateA = new Promise((resolve) => { releaseA = resolve; });
  let aRequestSeen = false;
  await page.route("**/analytics/v6/dashboard*", async (route) => {
    const url = route.request().url();
    if (/projet=1|projet=PROJET_A/.test(url)) {
      aRequestSeen = true;
      await gateA;
    }
    await route.continue().catch(() => {});
  });
  await loginUi(page, "admin@recette.local", "Admin123!");
  // Ouvre A (dashboard A retenu), bascule sur B, libere A.
  const aCard = page.getByTestId("project-card").filter({ hasText: "Projet A synthetique" });
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });
  await aCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await page.waitForURL(/\/app(\?|$)/, { timeout: 20000 });
  await page.waitForFunction(() => window.__sp2i_dump_state !== undefined, { timeout: 5000 }).catch(() => {});
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });
  const bCard = page.getByTestId("project-card").filter({ hasText: "Projet B synthetique" });
  await bCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await page.waitForURL(/\/app(\?|$)/, { timeout: 20000 });
  const b500 = page.locator(".advanced-kpi-card").filter({ hasText: "CAPEX Direct" });
  await expect(b500).toContainText("500 FCFA", { timeout: 25000 });
  await expect(page.getByText("Projet B synthetique").first()).toBeVisible({ timeout: 10000 });
  // Liberation de la reponse A retardee.
  releaseA();
  await page.waitForTimeout(2500);
  await expect(page.getByText("Projet B synthetique").first()).toBeVisible({ timeout: 10000 });
  await expect(b500).toContainText("500 FCFA", { timeout: 10000 });
  expect((await page.getByText(/3 000 FCFA/).count())).toBe(0);
});

test("SIMULATION C7d : mode V5 (flag off) sans appel aux endpoints V6", async ({ page }) => {
  const v5Base = "http://127.0.0.1:5175";
  let v6Calls = 0;
  page.on("request", (req) => { if (req.url().includes("/analytics/v6/")) v6Calls += 1; });
  await page.route("**/analytics/v6/**", (route) => route.fulfill({ status: 200, contentType: "application/json", body: "{}" }));
  await page.route("**/analytics/dashboard*", (route) => route.fulfill({
    status: 200, contentType: "application/json",
    body: JSON.stringify({ status: "SUCCESS", kpis: { capex_brut: 3000, capex_optimise: 2700, economie_nette: 300, nb_lignes: 4, nb_lots: 3 }, table: [], charts: {} }),
  }));
  await page.route("**/analytics/capex*", (route) => route.fulfill({
    status: 200, contentType: "application/json",
    body: JSON.stringify({ status: "SUCCESS", kpis: { capex_brut: 3000, capex_optimise: 2700, economie_nette: 300 } }),
  }));
  await page.goto(`${v5Base}/`, { waitUntil: "domcontentloaded" });
  await page.getByPlaceholder("vous@organisation.com").fill("admin@recette.local");
  await page.getByPlaceholder("Minimum 12 caracteres").fill("Admin123!");
  await page.locator("form.landing-login-card").getByRole("button", { name: /Se connecter/i }).click();
  await page.waitForURL(/\/app/, { timeout: 25000 });
  await page.goto(`${v5Base}/app/projects`, { waitUntil: "domcontentloaded" });
  const aCard = page.getByTestId("project-card").filter({ hasText: "Projet A synthetique" });
  await aCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await page.waitForURL(/\/app(\?|$)/, { timeout: 20000 });
  const budget = page.locator(".advanced-kpi-card").filter({ hasText: "Budget initial" }).first();
  await expect(budget).toContainText("3 000 FCFA", { timeout: 25000 });
  expect(v6Calls).toBe(0);
});
