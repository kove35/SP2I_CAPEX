// Campagne recette SP2I CAPEX — backend reel :8001, frontend :5174, sans mock API.
import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8001";

async function loginUi(page, email, password) {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.getByPlaceholder("vous@organisation.com").fill(email);
  await page.getByPlaceholder("Minimum 12 caracteres").fill(password);
  await page.locator("form.landing-login-card").getByRole("button", { name: /Se connecter/i }).click();
  await page.waitForURL(/\/app/, { timeout: 25000 });
}
async function openProject(page, name) {
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });
  const card = page.getByTestId("project-card").filter({ hasText: name });
  await expect(card).toBeVisible({ timeout: 20000 });
  await card.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await page.waitForURL(/\/app(\?|$)/, { timeout: 20000 });
}
async function kpiText(page, label) {
  const card = page.locator(".advanced-kpi-card").filter({ hasText: label }).first();
  await expect(card).toBeVisible({ timeout: 30000 });
  return (await card.innerText()).replace(/[\u00A0\u202F]/g, " ");
}
async function waitKpi(page, label, expected) {
  await expect.poll(async () => (await kpiText(page, label)).includes(expected), { timeout: 20000 }).toBe(true);
}
async function pick(page, label, value) {
  const field = page.locator(".analytics-select-field").filter({ has: page.locator("span", { hasText: label }) }).first();
  await field.locator("button.analytics-select-control").click({ timeout: 15000 });
  await field.locator("button.analytics-select-option", { hasText: value }).click({ timeout: 15000 });
}
async function clearPick(page, label) {
  const field = page.locator(".analytics-select-field").filter({ has: page.locator("span", { hasText: label }) }).first();
  await field.locator("button.analytics-select-control").click({ timeout: 15000 });
  await field.locator("button.analytics-select-option.muted").first().click({ timeout: 15000 });
}
async function softProbe(issues, label, ok, detail) { if (!ok) issues.push(`${label} :: ${detail}`); }

test("C1 prerequis : API :8001, projets, connexion admin", async ({ page }) => {
  const logs = [];
  page.on("console", (m) => { const t = m.text(); if (t.includes("API_BASE_URL")) logs.push(t); });
  await loginUi(page, "admin@recette.local", "Admin123!");
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });
  await expect(page.getByTestId("project-card").first()).toBeVisible({ timeout: 20000 });
  const names = (await page.locator('[data-testid="project-card"]').allInnerTexts()).join("\n");
  for (const p of ["Projet A synthetique", "Projet B synthetique", "Projet C vide", "Projet D geometrie non resolvable", "Projet E montants nuls"]) {
    expect(names).toContain(p);
  }
  expect(logs.join("\n")).toContain("8001");
});

test("C2 A sans filtre : KPI 3000, 4 lignes, tableau financier", async ({ page }) => {
  const issues = [];
  await loginUi(page, "admin@recette.local", "Admin123!");
  await openProject(page, "Projet A synthetique");
  await waitKpi(page, "CAPEX Direct", "3 000 FCFA");
  await softProbe(issues, "nom A", await page.getByText("Projet A synthetique").first().isVisible().catch(() => false), "absent");
  await softProbe(issues, "pas Mpemba", (await page.getByText(/Mpemba/i).count()) === 0, "present");
  await softProbe(issues, "4 lignes a analyser", (await page.getByText(/4 lignes à analyser/).count()) > 0, "absent");
  const factGrid = page.locator("[data-fact-metre-grid]");
  let grid = "";
  if (await factGrid.count()) grid = await factGrid.first().innerText().catch(() => "");
  else grid = await page.getByText(/Analyse detaillee/).first().innerText().catch(() => "");
  const gridNorm = grid.replace(/[\u00A0\u202F]/g, " ");
  await softProbe(issues, "tableau lignes financieres", gridNorm.includes("Climatiseur"), gridNorm.slice(0, 400));
  await softProbe(issues, "montants tableau", /(3 000|1 200|800|600|400)/.test(gridNorm), gridNorm.slice(0, 400));
  await softProbe(issues, "decisions import/local visibles", /IMPORT/.test(gridNorm) && /LOCAL/.test(gridNorm), gridNorm.slice(0, 400));
  console.log("C2_ISSUES", JSON.stringify(issues));
  expect(issues).toEqual([]);
});

test("C3 A : RDC, vide LOT_CVC, retrait, reset, rechargement", async ({ page }) => {
  await loginUi(page, "admin@recette.local", "Admin123!");
  await openProject(page, "Projet A synthetique");
  await pick(page, "Niveau", "RDC");
  await waitKpi(page, "CAPEX Direct", "1 000 FCFA");
  await pick(page, "Lot", "LOT_CVC");
  await expect(page.getByText("Aucune donnée pour les filtres sélectionnés").first()).toBeVisible({ timeout: 15000 });
  await clearPick(page, "Lot");
  await waitKpi(page, "CAPEX Direct", "1 000 FCFA");
  await pick(page, "Lot", "LOT_CVC");
  await expect(page.getByText("Aucune donnée pour les filtres sélectionnés").first()).toBeVisible({ timeout: 15000 });
  await page.getByRole("button", { name: /Reinitialiser/i }).click();
  await waitKpi(page, "CAPEX Direct", "3 000 FCFA");
  await page.reload({ waitUntil: "domcontentloaded" });
  await waitKpi(page, "CAPEX Direct", "3 000 FCFA");
  await expect(page.getByText("Projet A synthetique").first()).toBeVisible({ timeout: 10000 });
});

test("C4 isolation : B sans residu A, retour A 3000", async ({ page }) => {
  const issues = [];
  await loginUi(page, "admin@recette.local", "Admin123!");
  await openProject(page, "Projet A synthetique");
  await waitKpi(page, "CAPEX Direct", "3 000 FCFA");
  await pick(page, "Niveau", "RDC");
  await waitKpi(page, "CAPEX Direct", "1 000 FCFA");
  await openProject(page, "Projet B synthetique");
  await waitKpi(page, "CAPEX Direct", "500 FCFA");
  await softProbe(issues, "B sans 3 000", (await page.getByText(/3 000 FCFA/).count()) === 0, "residu A");
  const batField = page.locator(".analytics-select-field").filter({ has: page.locator("span", { hasText: "Batiment" }) }).first();
  await batField.locator("button.analytics-select-control").click({ timeout: 15000 });
  const batOptions = (await batField.locator("button.analytics-select-option").allInnerTexts()).join(" | ");
  await softProbe(issues, "BAT_B option", batOptions.includes("BAT_B"), batOptions);
  await softProbe(issues, "BAT_A absent", !batOptions.includes("BAT_A"), batOptions);
  console.log("C4_ISSUES", JSON.stringify(issues));
  expect(issues).toEqual([]);
  await openProject(page, "Projet A synthetique");
  await waitKpi(page, "CAPEX Direct", "3 000 FCFA");
});

test("C5 limites : C vide, D/S1 indisponible, E zero-lignes", async ({ page }) => {
  await loginUi(page, "admin@recette.local", "Admin123!");
  await openProject(page, "Projet C vide");
  await expect(page.getByText("Aucune donnée pour ce projet").first()).toBeVisible({ timeout: 15000 });
  await expect(page.getByText(/Non évalué/).first()).toBeVisible({ timeout: 10000 });
  await openProject(page, "Projet D geometrie non resolvable");
  await pick(page, "Niveau", "S1");
  const appCard = page.locator(".advanced-kpi-card").filter({ hasText: "Par appartement" });
  await expect(appCard).toContainText("Indisponible", { timeout: 25000 });
  await expect(appCard.locator("svg.kpi-sparkline")).toHaveCount(0);
  await openProject(page, "Projet E montants nuls");
  const issues = [];
  await softProbe(issues, "E non vide", (await page.getByText(/Aucune donnée pour ce projet/).count()) === 0, "E vu vide");
  await softProbe(issues, "E CAPEX 0", (await kpiText(page, "CAPEX Direct")).includes("0 FCFA"), "valeur");
  expect(issues).toEqual([]);
});

test("C6 droits : routes metier (alice A 200, B 404, sans projet 403, sans session 401)", async ({ page }) => {
  await loginUi(page, "alice@recette.local", "Alice123!");
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const session = await page.evaluate(() => JSON.parse(window.localStorage.getItem("sp2i_session") || "null"));
  const headers = session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {};
  const a = await page.request.get(`${API}/analytics/v6/project-cost?projet=PROJET_A`, { headers });
  const b = await page.request.get(`${API}/analytics/v6/project-cost?projet=PROJET_B`, { headers });
  const noProjet = await page.request.get(`${API}/analytics/v6/project-cost`, { headers });
  const noSession = await page.request.get(`${API}/analytics/v6/project-cost?projet=PROJET_A`);
  console.log("C6_STATUS", a.status(), b.status(), noProjet.status(), noSession.status());
  expect(a.status()).toBe(200);
  expect(b.status()).toBe(404);
  expect(noProjet.status()).toBe(403);
  expect(noSession.status()).toBe(401);
});

