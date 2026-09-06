// Recette navigateur AVEC backend + frontend réels (AUCUN page.route() sur les
// API métier). Prérequis :
//   - backend uvicorn :8000 branché sur sp2i_capex_recipe (tests/recette) ;
//   - frontend vite :5173 lancé avec VITE_SP2I_USE_V6_FINANCIALS=true.
// Les URLs sont absolues car le serveur Vite local écoute sur localhost (IPv6).
import { test, expect } from "@playwright/test";

const BASE = ""; // baseURL config 127.0.0.1:5173

async function login(page) {
  await page.goto(`${BASE}/`, { waitUntil: "domcontentloaded" });
  const email = page.getByPlaceholder("vous@organisation.com");
  await expect(email).toBeVisible({ timeout: 20000 });
  await email.fill("admin@recette.local");
  await page.getByPlaceholder("Minimum 12 caracteres").fill("Admin123!");
  await page.locator("form.landing-login-card").getByRole("button", { name: /Se connecter/i }).click();
  await page.waitForURL(/\/app/, { timeout: 25000 });
}

async function openProject(page, name) {
  await page.goto(`${BASE}/app/projects`, { waitUntil: "domcontentloaded" });
  const card = page.getByTestId("project-card").filter({ hasText: name });
  await expect(card).toBeVisible({ timeout: 20000 });
  const button = card.getByRole("button", { name: /ouvrir le workspace/i });
  await button.click();
  await page.waitForURL(/\/app(\?|$)/, { timeout: 20000 });
}

async function chooseNiveau(page, value) {
  const field = page
    .locator(".analytics-select-field")
    .filter({ has: page.locator("span", { hasText: "Niveau" }) })
    .first();
  await field.locator("button.analytics-select-control").click({ timeout: 15000 });
  await field.locator("button.analytics-select-option", { hasText: value }).click({ timeout: 15000 });
}

async function chooseFilterValue(page, labelText, value) {
  const field = page
    .locator(".analytics-select-field")
    .filter({ has: page.locator("span", { hasText: labelText }) })
    .first();
  await field.locator("button.analytics-select-control").click({ timeout: 15000 });
  await field.locator("button.analytics-select-option", { hasText: value }).click({ timeout: 15000 });
}

async function clearFilterByLabel(page, labelText) {
  const field = page
    .locator(".analytics-select-field")
    .filter({ has: page.locator("span", { hasText: labelText }) })
    .first();
  await field.locator("button.analytics-select-control").click({ timeout: 15000 });
  await field.locator("button.analytics-select-option.muted").first().click({ timeout: 15000 });
}

async function cardText(page, label) {
  const card = page.locator(".advanced-kpi-card").filter({ hasText: label }).first();
  await expect(card).toBeVisible({ timeout: 30000 });
  const raw = await card.innerText();
  return raw.replace(/[\u00A0\u202F]/g, " ");
}

async function expectCardContains(page, label, expected, { timeout = 20000 } = {}) {
  await expect
    .poll(async () => (await cardText(page, label)).includes(expected), { timeout })
    .toBe(true);
}

test("recette API réelle : cockpit V6 sur backend réel", async ({ page }) => {
  console.log("STEP connexion");
  await login(page);

  console.log("STEP selection projet A");
  await openProject(page, "Projet A synthetique");
  await expectCardContains(page, "CAPEX Direct", "3 000 FCFA");
  await expect(page.getByText("Projet A synthetique").first()).toBeVisible({ timeout: 10000 });
  await expect(page.getByText(/Complexe immobilier Mpemba/i)).toHaveCount(0);

  console.log("STEP rechargement (contexte A conserve)");
  await page.reload({ waitUntil: "domcontentloaded" });
  await expectCardContains(page, "CAPEX Direct", "3 000 FCFA");
  await expect(page.getByText("Projet A synthetique").first()).toBeVisible({ timeout: 10000 });
  await expect(page.getByText(/Complexe immobilier Mpemba/i)).toHaveCount(0);

  console.log("STEP filtre niveau RDC (projet A)");
  await chooseNiveau(page, "RDC");
  await expectCardContains(page, "CAPEX Direct", "1 000 FCFA");

  console.log("STEP filtre vide RDC + LOT_CVC puis retrait LOT_CVC");
  await chooseFilterValue(page, "Lot", "LOT_CVC");
  await expect(page.getByText("Aucune donnée pour les filtres sélectionnés").first()).toBeVisible({ timeout: 15000 });
  await clearFilterByLabel(page, "Lot");
  await expectCardContains(page, "CAPEX Direct", "1 000 FCFA");

  console.log("STEP RESET apres filtre vide (reproduction exacte)");
  await chooseFilterValue(page, "Lot", "LOT_CVC");
  await expect(page.getByText("Aucune donnée pour les filtres sélectionnés").first()).toBeVisible({ timeout: 15000 });
  await page.getByRole("button", { name: /Reinitialiser/i }).click();
  await expectCardContains(page, "CAPEX Direct", "3 000 FCFA");
  await expect(page.getByText(/Aucune donnée/).first()).toHaveCount(0);
  const counterText = await page.locator("text=/lignes/i").allInnerTexts();
  console.log("RESET_COUNTERS", JSON.stringify(counterText.slice(0, 8)));
  await expect(page.getByText(/4 lignes à analyser/).first()).toBeVisible({ timeout: 15000 });
  const ap = await cardText(page, "Par appartement");
  console.log("RESET_PAR_APPART", JSON.stringify(ap));
  expect(ap).toContain("1 329 FCFA");

  console.log("STEP reset conserve le contexte apres rechargement");
  await page.reload({ waitUntil: "domcontentloaded" });
  await expectCardContains(page, "CAPEX Direct", "3 000 FCFA");
  await expect(page.getByText("Projet A synthetique").first()).toBeVisible({ timeout: 10000 });

  console.log("STEP selection projet B");
  await openProject(page, "Projet B synthetique");
  await expectCardContains(page, "CAPEX Direct", "500 FCFA");

  console.log("STEP projet C vide");
  await openProject(page, "Projet C vide");
  await page.waitForTimeout(1500);
  await expect(page.getByText("Aucune donnée pour ce projet").first()).toBeVisible({ timeout: 15000 });
  await expectCardContains(page, "CAPEX Direct", "0 FCFA", { timeout: 15000 });
  await expect(page.getByText(/Non évalué/).first()).toBeVisible({ timeout: 10000 });

  console.log("STEP ratio indisponible (projet D + niveau S1)");
  await openProject(page, "Projet D geometrie non resolvable");
  await expect(page.getByText("CAPEX Direct")).toBeVisible({ timeout: 30000 });
  await chooseNiveau(page, "S1");
  const appCard = page.locator(".advanced-kpi-card").filter({ hasText: "Par appartement" });
  await expect(appCard).toContainText("Indisponible", { timeout: 25000 });
  await expect(appCard.locator("svg.kpi-sparkline")).toHaveCount(0);
  await expect(page.getByText(/Indisponible pour ce perimetre/).first()).toBeVisible({ timeout: 25000 });
});
