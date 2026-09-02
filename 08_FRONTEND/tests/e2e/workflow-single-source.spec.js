import { expect, test } from "@playwright/test";

import { mockProcurementLinesApi } from "./helpers/apiMocks";

async function resetDemoProjects(page) {
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });
  await page.evaluate(() => {
    window.localStorage.clear();
  });
  await page.reload({ waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: /mes projets/i })).toBeVisible();
}

async function configureProject(page, projectName = "Projet source unique") {
  await resetDemoProjects(page);
  const projectCard = page.getByTestId("project-card").filter({
    has: page.getByRole("button", { name: /configurer le projet/i }),
  }).first();
  await expect(projectCard).toBeVisible();
  await projectCard.getByRole("button", { name: /configurer le projet/i }).click();

  const dialog = page.getByRole("dialog", { name: /configuration projet/i });
  await expect(dialog).toBeVisible();
  await dialog.getByLabel(/nom du projet/i).fill(projectName);
  await dialog.getByLabel(/organisation \/ client/i).fill("Client test source unique");
  await dialog.getByLabel(/ville/i).fill("Pointe-Noire");
  await dialog.getByLabel(/^pays/i).fill("Congo-Brazzaville");
  await dialog.getByLabel(/devise projet/i).fill("FCFA");
  await dialog.getByLabel(/responsable projet/i).fill("Responsable source unique");
  await dialog.getByRole("button", { name: /enregistrer la configuration/i }).click();

  const configuredCard = page.getByTestId("project-card").filter({ hasText: new RegExp(projectName, "i") }).first();
  await expect(configuredCard).toBeVisible();
  return configuredCard;
}

async function openConfiguredProjectWorkspace(page, projectName = "Projet source unique") {
  const configuredCard = await configureProject(page, projectName);
  await configuredCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await expect(page.getByTestId("workspace-header")).toBeVisible();
  return configuredCard;
}

async function patchProject(page, projectName, patch) {
  await page.evaluate(({ name, values }) => {
    const stored = window.localStorage.getItem("sp2i:projects");
    const projects = stored ? JSON.parse(stored) : [];
    const next = projects.map((project) => (
      new RegExp(name, "i").test(project.name || "")
        ? { ...project, ...values }
        : project
    ));
    window.localStorage.setItem("sp2i:projects", JSON.stringify(next));

    try {
      const persistedState = window.localStorage.getItem("sp2i:appState");
      if (persistedState) {
        const appState = JSON.parse(persistedState);
        if (appState.activeProjectDetails && new RegExp(name, "i").test(appState.activeProjectDetails.name || "")) {
          appState.activeProjectDetails = { ...appState.activeProjectDetails, ...values };
          window.localStorage.setItem("sp2i:appState", JSON.stringify(appState));
        }
      }
    } catch {
      // Ignore persisted app state sync errors during demo patching.
    }
  }, { name: projectName, values: patch });
}

async function setProjectDqeVersion(page, projectName, version = {}) {
  await page.evaluate(({ name, payload }) => {
    const stored = window.localStorage.getItem("sp2i:projects");
    const projects = stored ? JSON.parse(stored) : [];
    const target = projects.find((project) => new RegExp(name, "i").test(project.name || ""));
    if (!target) {
      return;
    }
    const workspaceKey = target.workspace_key || target.id;
    const record = {
      id: `${workspaceKey}-dqe-1`,
      version_number: 1,
      file_name: "DQE_SOURCE_UNIQUE.xlsx",
      status: "SYNCED",
      trust_score: 92,
      normalized_lines_count: 128,
      data_loss_count: 0,
      review_required_count: 0,
      is_active: true,
      synced_at: new Date().toISOString(),
      uploaded_at: new Date().toISOString(),
      uploaded_by: "automated-test",
      ...payload,
    };
    window.localStorage.setItem(`sp2i:dqeVersions:${workspaceKey}`, JSON.stringify([record]));
  }, { name: projectName, payload: version });
}

async function seedProjectRecord(page, projectName, values = {}) {
  await page.evaluate(({ name, payload }) => {
    const stored = window.localStorage.getItem("sp2i:projects");
    const projects = stored ? JSON.parse(stored) : [];
    const existing = projects.find((project) => new RegExp(name, "i").test(project.name || ""));
    const nextProject = {
      id: existing?.id || `local-${Math.random().toString(36).slice(2, 10)}`,
      workspace_key: existing?.workspace_key || `${name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-workspace`,
      name,
      client_name: payload.client_name || "Client test",
      city: payload.city || "Brazzaville",
      country: payload.country || "Congo-Brazzaville",
      currency: payload.currency || "FCFA",
      status: payload.status || "ACTIVE",
      trust_score: payload.trust_score ?? 72,
      last_dqe: payload.last_dqe || "DQE à importer",
      budget: payload.budget ?? 0,
      updated_at: payload.updated_at || "Workspace pret",
      setup_status: payload.setup_status || "CONFIGURED",
      workflow_status: payload.workflow_status || "ACTIVE",
      project_manager: payload.project_manager || "Responsable de test",
      setup_completion_percent: payload.setup_completion_percent ?? 100,
    };

    const next = existing ? projects.map((project) => new RegExp(name, "i").test(project.name || "") ? nextProject : project) : [...projects, nextProject];
    window.localStorage.setItem("sp2i:projects", JSON.stringify(next));
  }, { name: projectName, payload: values });
}

async function navigateSpa(page, path) {
  await page.evaluate((nextPath) => {
    window.history.pushState({}, "", nextPath);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }, path);
}

async function setSimulationResult(page, payload = {}) {
  let simulateCalls = 0;
  await page.route("**/simulation/simulate", async (route) => {
    simulateCalls += 1;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "SUCCESS",
        scenario_name: "IMPORT_OPTIMIZATION",
        kpi: {
          capex_local: 100000000,
          capex_optimise: 75000000,
          economie_nette: 25000000,
          lignes_dqe: 128,
          lignes_simulees: 128,
          lignes_importables: 28,
          lignes_retenues: 22,
          lignes_arbitrees: 128,
        },
        lignes: [
          {
            id_ligne: "line-1",
            designation: "Luminaire import",
            decision_finale: "IMPORT",
            risk_level: "MEDIUM",
            economie_nette: 25000000,
          },
        ],
        metadata: {
          line_counts: {
            dqe: 128,
            simulees: 128,
            importables: 28,
            retenues: 22,
            arbitrees: 128,
          },
        },
        ...payload,
      }),
    });
  });
  return { getCount: () => simulateCalls };
}

test("selected project stays aligned in hero, selector and sidebar", async ({ page }) => {
  const projectName = "Projet source unique affichage";
  await openConfiguredProjectWorkspace(page, projectName);

  await expect(page.locator(".project-selector")).toContainText(projectName);
  await expect(page.locator(".sidebar-project-status")).toContainText(projectName);
  await expect(page.getByTestId("workspace-header")).toContainText(projectName);
});

test("changing the active project updates the project context everywhere", async ({ page }) => {
  await openConfiguredProjectWorkspace(page, "Projet source unique switch A");
  await seedProjectRecord(page, "Clinique pilote Brazzaville", {
    city: "Brazzaville",
    country: "Congo-Brazzaville",
    trust_score: 72,
    setup_status: "CONFIGURED",
    workflow_status: "ACTIVE",
    project_manager: "Responsable BRAZZA",
  });
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });

  const secondCard = page.getByTestId("project-card").filter({ hasText: /clinique pilote brazzaville/i }).first();
  await expect(secondCard).toBeVisible();
  await secondCard.getByRole("button", { name: /ouvrir le workspace/i }).click();

  await expect(page.locator(".project-selector")).toContainText(/clinique pilote brazzaville/i);
  await expect(page.locator(".sidebar-project-status")).toContainText(/clinique pilote brazzaville/i);
});

test("DQE version metadata is stored per project workspace key", async ({ page }) => {
  const projectName = "Projet source unique dqe";
  await openConfiguredProjectWorkspace(page, projectName);
  await setProjectDqeVersion(page, projectName, { trust_score: 96, status: "CERTIFIED" });

  await page.goto("/app/dqe?tab=import", { waitUntil: "domcontentloaded" });
  await expect(page.getByTestId("dqe-empty-state").first()).not.toBeVisible();

  const storageSnapshot = await page.evaluate(() => {
    const keys = Object.keys(window.localStorage).filter((key) => key.startsWith("sp2i:dqeVersions:"));
    return keys.map((key) => ({ key, value: window.localStorage.getItem(key) }));
  });

  expect(storageSnapshot.length).toBeGreaterThan(0);
  expect(storageSnapshot.some((entry) => entry.key.includes("sp2i:dqeVersions:"))).toBeTruthy();
  const parsed = JSON.parse(storageSnapshot[0].value);
  expect(parsed[0].status).toBeTruthy();
  expect(parsed[0].version_number).toBe(1);
});

test("certified DQE keeps simulation gated until budget sync is ready", async ({ page }) => {
  const projectName = "Projet source unique gated";
  await openConfiguredProjectWorkspace(page, projectName);
  await setProjectDqeVersion(page, projectName, { status: "CERTIFIED", trust_score: 89, synced_at: null });

  await navigateSpa(page, "/app/simulation");
  await expect(page.locator(".project-selector")).toContainText(projectName);
  await expect(page.getByTestId("scenario-empty-state").first()).toBeVisible();
  await expect(page.getByTestId("scenario-empty-state").first()).toContainText(/budget non synchronise|aucun dqe actif/i);
  await expect(page.getByTestId("workflow-empty-action")).toHaveText(/synchroniser le budget|importer un dqe/i);
});

test("synced DQE enables simulation and updates project workflow state", async ({ page }) => {
  const projectName = "Projet source unique simulation";
  await openConfiguredProjectWorkspace(page, projectName);
  await setProjectDqeVersion(page, projectName, { status: "SYNCED", trust_score: 94, synced_at: new Date().toISOString() });
  await setSimulationResult(page);

  await navigateSpa(page, "/app/simulation");
  await expect(page.locator(".project-selector")).toContainText(projectName);
  await expect(page.getByRole("button", { name: /lancer simulation/i })).toBeVisible();
  await page.getByRole("button", { name: /lancer simulation/i }).click();

  await expect(page.getByText(/simulation du scénario lancée/i)).toBeVisible();
  await expect(page.getByText(/budget optimise/i)).toBeVisible();
  await expect(page.getByText(/lignes scénario/i)).toBeVisible();

  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });
  const projectCard = page.getByTestId("project-card").filter({ hasText: new RegExp(projectName, "i") }).first();
  await expect(projectCard).toBeVisible();
  await expect(projectCard.getByTestId("project-primary-action")).toHaveText(/valider les décisions import critiques/i);
});

test("simulation exposes DQE, FACT_METRE and scenario traceability labels", async ({ page }) => {
  const projectName = "Projet source unique traceability";
  await openConfiguredProjectWorkspace(page, projectName);
  await setProjectDqeVersion(page, projectName, { status: "SYNCED", trust_score: 94, normalized_lines_count: 128, synced_at: new Date().toISOString() });
  await setSimulationResult(page, {
    metadata: {
      line_counts: {
        dqe: 128,
        simulees: 96,
        importables: 24,
        retenues: 18,
        arbitrees: 96,
      },
    },
  });

  await page.goto("/app/simulation", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: /lancer simulation/i }).click();
  await expect(page.getByText(/simulation du scénario lancée/i)).toBeVisible();
  await expect(page.getByText(/Qualité de synchronisation/i)).toBeVisible();
  await expect(page.getByText(/DQE actif/i).first()).toBeVisible();
  await expect(page.getByText(/FACT_METRE/i).first()).toBeVisible();
  await expect(page.getByText(/Scénario actif/i).first()).toBeVisible();
  await expect(page.getByText(/Lignes scénario/i).first()).toBeVisible();
  await expect(page.getByTestId("synchronization-traceability-card")).toBeVisible();
});

test("procurement exposes the shared lineage card and decision traceability", async ({ page }) => {
  const projectName = "Projet source unique procurement lineage";
  await openConfiguredProjectWorkspace(page, projectName);
  await setProjectDqeVersion(page, projectName, { status: "SYNCED", trust_score: 95, normalized_lines_count: 128, synced_at: new Date().toISOString() });
  await patchProject(page, projectName, {
    scenario_ready: true,
    procurement_ready: true,
    procurement_decisions_count: 10,
    procurement_validated_decisions_count: 6,
    procurement_pending_decisions_count: 4,
    procurement_to_arbitrate_count: 4,
    procurement_review_required_count: 0,
  });

  await page.goto("/app/procurement", { waitUntil: "domcontentloaded" });
  await expect(page.getByTestId("procurement-data-lineage-card")).toBeVisible();
  await expect(page.getByTestId("procurement-data-lineage-card")).toContainText(/TRAÇABILITÉ ACHAT/i);
  await expect(page.getByTestId("procurement-data-lineage-card")).toContainText(/DQE actif/i);
  await expect(page.getByTestId("procurement-data-lineage-card")).toContainText(/FACT_METRE/i);
  await expect(page.getByTestId("procurement-data-lineage-card")).toContainText(/Scénario actif/i);
  await expect(page.getByTestId("procurement-data-lineage-card")).toContainText(/Décisions validées/i);
  await expect(page.getByTestId("procurement-data-lineage-card")).toContainText(/Désynchronisé|Synchronisé/i);
});

test("site execution exposes the shared lineage card and readiness counters", async ({ page }) => {
  const projectName = "Projet source unique site lineage";
  await openConfiguredProjectWorkspace(page, projectName);
  await setProjectDqeVersion(page, projectName, { status: "SYNCED", trust_score: 95, normalized_lines_count: 128, synced_at: new Date().toISOString() });

  await page.goto("/app/site?tab=planning", { waitUntil: "domcontentloaded" });
  await expect(page.getByTestId("site-data-lineage-card")).toBeVisible();
  await expect(page.getByTestId("site-data-lineage-card")).toContainText(/TRAÇABILITÉ CHANTIER/i);
  await expect(page.getByTestId("site-data-lineage-card")).toContainText(/DQE actif/i);
  await expect(page.getByTestId("site-data-lineage-card")).toContainText(/FACT_METRE/i);
  await expect(page.getByTestId("site-data-lineage-card")).toContainText(/Scénario actif/i);
  await expect(page.getByTestId("site-data-lineage-card")).toContainText(/Lots prêts/i);
  await expect(page.getByText(/Préparation Chantier/i).first()).toBeVisible();
});

test("refresh preserves the active project identity after simulation", async ({ page }) => {
  const projectName = "Projet source unique refresh";
  await openConfiguredProjectWorkspace(page, projectName);
  await setProjectDqeVersion(page, projectName, { status: "SYNCED", trust_score: 94, synced_at: new Date().toISOString() });
  await setSimulationResult(page);

  await page.goto("/app/simulation", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: /lancer simulation/i }).click();
  await expect(page.getByText(/simulation du scénario lancée/i)).toBeVisible();

  await page.reload({ waitUntil: "domcontentloaded" });
  await expect(page.locator(".project-selector")).toContainText(projectName);
  await expect(page.locator(".sidebar-project-status")).toContainText(projectName);
});

test("procurement page keeps the same project context and decision source", async ({ page }) => {
  const projectName = "Projet source unique procurement";
  await openConfiguredProjectWorkspace(page, projectName);
  await setProjectDqeVersion(page, projectName, { status: "SYNCED", trust_score: 95, synced_at: new Date().toISOString() });
  await page.goto("/app/procurement", { waitUntil: "domcontentloaded" });

  await expect(page.getByRole("heading", { name: /que faut-il/i })).toBeVisible();
  await expect(page.locator(".project-selector")).toContainText(projectName);
  await expect(page.locator(".sidebar-project-status")).toContainText(projectName);
  await expect(page.getByText(/source/i).first()).toBeVisible();
});

test("procurement validation updates persisted project state and summary counters", async ({ page }) => {
  await mockProcurementLinesApi(page);
  const projectName = "Projet source unique validation";
  await openConfiguredProjectWorkspace(page, projectName);
  await setProjectDqeVersion(page, projectName, { status: "SYNCED", trust_score: 95, synced_at: new Date().toISOString() });
  await patchProject(page, projectName, {
    scenario_ready: true,
    procurement_ready: false,
    procurement_decisions_count: 3,
    procurement_validated_decisions_count: 0,
    procurement_pending_decisions_count: 3,
    procurement_to_arbitrate_count: 3,
    procurement_review_required_count: 3,
  });

  await page.goto("/app/procurement", { waitUntil: "domcontentloaded" });
  const summary = page.getByTestId("procurement-validation-summary");
  await expect(summary).toBeVisible();
  await expect(summary).toContainText(/Validees/i);
  await expect(summary).toContainText(/En attente/i);

  const rowChecks = page.getByRole("checkbox");
  await expect(rowChecks.nth(1)).toBeVisible();
  await rowChecks.nth(1).click();
  await rowChecks.nth(2).click();

  const toolbar = page.getByTestId("procurement-bulk-toolbar");
  await expect(toolbar).toBeVisible();
  await toolbar.getByRole("button", { name: /valider import/i }).click();

  await expect(page.getByTestId("procurement-validation-summary")).toContainText(/Validees\s*:\s*[1-9]\d*/i);
});

test("navigation across DQE, simulation, procurement and site keeps the same active project", async ({ page }) => {
  const projectName = "Projet source unique navigation";
  await openConfiguredProjectWorkspace(page, projectName);
  await setProjectDqeVersion(page, projectName, { status: "SYNCED", trust_score: 95, synced_at: new Date().toISOString() });

  await page.goto("/app/dqe?tab=import", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("button", { name: /analyser excel/i }).first()).toBeVisible();

  await page.goto("/app/simulation", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: /simuler les scenarios capex/i })).toBeVisible();
  await expect(page.locator(".project-selector")).toContainText(projectName);

  await page.goto("/app/procurement", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: /que faut-il/i })).toBeVisible();
  await expect(page.locator(".sidebar-project-status")).toContainText(projectName);

  await page.goto("/app/site?tab=planning", { waitUntil: "domcontentloaded" });
  await expect(page.getByTestId("execution-empty-state")).toBeVisible();
  await expect(page.locator(".project-selector")).toContainText(projectName);
});

test("workflow timeline keeps the expected operational sequence", async ({ page }) => {
  const projectName = "Projet source unique timeline";
  await openConfiguredProjectWorkspace(page, projectName);
  await setProjectDqeVersion(page, projectName, { status: "SYNCED", trust_score: 95, synced_at: new Date().toISOString() });
  await patchProject(page, projectName, {
    scenario_ready: true,
    procurement_ready: true,
    procurement_decisions_count: 4,
    procurement_validated_decisions_count: 4,
    execution_ready: true,
    execution_actions_count: 3,
  });

  await page.goto("/app/simulation", { waitUntil: "domcontentloaded" });
  const workflowPanel = page.getByTestId("smart-workflow-actions");
  await expect(workflowPanel).toBeVisible();
  const timelineLabels = await workflowPanel.locator(".smart-timeline li span").allTextContents();
  expect(timelineLabels).toEqual([
    "Simulation",
    "Arbitrage",
    "Validation",
    "Commande",
    "Transport",
    "Reception",
    "Préparation Chantier",
  ]);
});

test("simulation-ready project offers procurement actions from the project hub", async ({ page }) => {
  const projectName = "Projet source unique hub";
  await openConfiguredProjectWorkspace(page, projectName);
  await setProjectDqeVersion(page, projectName, { status: "SYNCED", trust_score: 95, synced_at: new Date().toISOString() });
  await patchProject(page, projectName, {
    scenario_ready: true,
    procurement_ready: false,
    procurement_decisions_count: 12,
    procurement_validated_decisions_count: 0,
    procurement_pending_decisions_count: 12,
    procurement_to_arbitrate_count: 12,
  });

  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });
  const projectCard = page.getByTestId("project-card").filter({ hasText: new RegExp(projectName, "i") }).first();
  await expect(projectCard).toBeVisible();
  await expect(projectCard.getByTestId("project-primary-action")).toHaveText(/valider les décisions import critiques/i);
});

test("ready procurement and execution status drives chantier CTA", async ({ page }) => {
  const projectName = "Projet source unique chantier";
  await openConfiguredProjectWorkspace(page, projectName);
  await setProjectDqeVersion(page, projectName, { status: "SYNCED", trust_score: 95, synced_at: new Date().toISOString() });
  await patchProject(page, projectName, {
    scenario_ready: true,
    procurement_ready: true,
    procurement_decisions_count: 18,
    procurement_validated_decisions_count: 18,
    execution_ready: true,
    execution_actions_count: 5,
    execution_critical_lots_count: 1,
    execution_deliveries_to_watch_count: 3,
  });

  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });
  const projectCard = page.getByTestId("project-card").filter({ hasText: new RegExp(projectName, "i") }).first();
  await expect(projectCard).toBeVisible();
  await expect(projectCard.getByTestId("project-primary-action")).toHaveText(/suivre.*lots|lots chantier/i);
});

test("legacy localStorage keys are not introduced during workflow navigation", async ({ page }) => {
  const projectName = "Projet source unique legacy";
  await openConfiguredProjectWorkspace(page, projectName);
  await setProjectDqeVersion(page, projectName, { status: "SYNCED", trust_score: 95, synced_at: new Date().toISOString() });

  await page.goto("/app/simulation", { waitUntil: "domcontentloaded" });
  await page.goto("/app/procurement", { waitUntil: "domcontentloaded" });
  await page.goto("/app/site?tab=planning", { waitUntil: "domcontentloaded" });

  const legacyKeys = await page.evaluate(() => {
    return Object.keys(window.localStorage).filter((key) => /^workflow$/i.test(key) || /^projectworkflow$/i.test(key) || /^workflowstate$/i.test(key));
  });

  expect(legacyKeys).toEqual([]);
});

test("analytics primary action follows the workflow state for the active project", async ({ page }) => {
  const projectName = "Projet source unique pilotage";
  await openConfiguredProjectWorkspace(page, projectName);
  await setProjectDqeVersion(page, projectName, { status: "SYNCED", trust_score: 95, synced_at: new Date().toISOString() });
  await patchProject(page, projectName, {
    workflow_status: "PROCUREMENT_REVIEW_REQUIRED",
    scenario_ready: true,
    procurement_ready: false,
    procurement_decisions_count: 12,
    procurement_validated_decisions_count: 0,
    procurement_pending_decisions_count: 12,
    procurement_to_arbitrate_count: 12,
    procurement_review_required_count: 12,
  });

  await page.reload({ waitUntil: "domcontentloaded" });
  await page.goto("/app/analytics", { waitUntil: "domcontentloaded" });
  const summary = page.getByTestId("pilotage-summary");
  await expect(summary).toBeVisible();
  await expect(summary.getByTestId("pilotage-primary-action")).toHaveText(/valider les décisions import critiques/i);
});

test("project switching resets procurement context and carries the new project name", async ({ page }) => {
  await openConfiguredProjectWorkspace(page, "Projet source unique switch final");
  await seedProjectRecord(page, "Clinique pilote Brazzaville", {
    city: "Brazzaville",
    country: "Congo-Brazzaville",
    trust_score: 72,
    setup_status: "CONFIGURED",
    workflow_status: "ACTIVE",
    project_manager: "Responsable BRAZZA",
  });
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });

  const secondCard = page.getByTestId("project-card").filter({ hasText: /clinique pilote brazzaville/i }).first();
  await expect(secondCard).toBeVisible();
  await secondCard.getByRole("button", { name: /ouvrir le workspace/i }).click();

  await expect(page.locator(".project-selector")).toContainText(/clinique pilote brazzaville/i);
  await page.goto("/app/procurement", { waitUntil: "domcontentloaded" });
  await expect(page.locator(".project-selector")).toContainText(/clinique pilote brazzaville/i);
});
