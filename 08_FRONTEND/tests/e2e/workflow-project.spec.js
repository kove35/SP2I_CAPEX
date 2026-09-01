import { expect, test } from "@playwright/test";

import { mockProcurementLinesApi } from "./helpers/apiMocks";

async function resetDemoProjects(page) {
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });
  await page.evaluate(() => window.localStorage.clear());
  await page.reload({ waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: /mes projets/i })).toBeVisible();
}

async function openUnconfiguredProjectWorkspace(page) {
  await resetDemoProjects(page);
  const projectCard = page.getByTestId("project-card").filter({
    has: page.getByRole("button", { name: /configurer le projet/i }),
  }).first();
  await expect(projectCard).toBeVisible();
  await projectCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await expect(page.getByTestId("workspace-header")).toBeVisible();
  return projectCard;
}

async function configureFirstUnconfiguredProject(page, projectName = "Projet synthese workflow") {
  await resetDemoProjects(page);
  const projectCard = page.getByTestId("project-card").filter({
    has: page.getByRole("button", { name: /configurer le projet/i }),
  }).first();
  await expect(projectCard).toBeVisible();
  await projectCard.getByRole("button", { name: /configurer le projet/i }).click();

  const dialog = page.getByRole("dialog", { name: /configuration projet/i });
  await expect(dialog).toBeVisible();
  await dialog.getByLabel(/nom du projet/i).fill(projectName);
  await dialog.getByLabel(/organisation \/ client/i).fill("Client test SP2I");
  await dialog.getByLabel(/ville/i).fill("Pointe-Noire");
  await dialog.getByLabel(/^pays/i).fill("Congo-Brazzaville");
  await dialog.getByLabel(/devise projet/i).fill("FCFA");
  await dialog.getByLabel(/responsable projet/i).fill("Responsable test");
  await dialog.getByRole("button", { name: /enregistrer la configuration/i }).click();

  const configuredCard = page.getByTestId("project-card").filter({ hasText: new RegExp(projectName, "i") }).first();
  await expect(configuredCard).toBeVisible();
  return configuredCard;
}

async function openConfiguredProjectWorkspace(page, projectName = "Projet workflow configure") {
  const configuredCard = await configureFirstUnconfiguredProject(page, projectName);
  await configuredCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await expect(page.getByTestId("workspace-header")).toBeVisible();
  return configuredCard;
}

async function setCertifiedDqeWithoutBudget(page) {
  await page.evaluate(() => {
    window.localStorage.setItem("sp2i:dqeVersions:demo-brazza-clinic", JSON.stringify([
      {
        id: "test-certified-dqe",
        version_number: 1,
        file_name: "DQE_TEST_CERTIFIED.xlsx",
        status: "CERTIFIED",
        trust_score: 91,
        normalized_lines_count: 120,
        data_loss_count: 0,
        review_required_count: 0,
        is_active: true,
      },
    ]));
  });
}

async function setSyncedDqe(page) {
  await page.evaluate(() => {
    window.localStorage.setItem("sp2i:dqeVersions:demo-brazza-clinic", JSON.stringify([
      {
        id: "test-synced-dqe",
        version_number: 1,
        file_name: "DQE_TEST_SYNCED.xlsx",
        status: "SYNCED",
        trust_score: 93,
        normalized_lines_count: 130,
        data_loss_count: 0,
        review_required_count: 0,
        is_active: true,
      },
    ]));
  });
}

async function setSpatialSyncedDqe(page) {
  await page.evaluate(() => {
    window.localStorage.setItem("sp2i:dqeVersions:demo-brazza-clinic", JSON.stringify([
      {
        id: "test-spatial-dqe",
        version_number: 1,
        file_name: "DQE_SPATIAL_TEST.xlsx",
        status: "SYNCED",
        trust_score: 96,
        normalized_lines_count: 584,
        data_loss_count: 0,
        review_required_count: 0,
        is_active: true,
        synced_at: new Date().toISOString(),
        bim_maturity: {
          maturity: "BIM_LITE",
          mode: "BIM_LITE",
          is_bim_compatible: true,
          spatialized_lines_count: 584,
          coverage: {
            batiment: 1,
            niveau: 1,
            piece: 0.8,
          },
        },
      },
    ]));
  });
}

async function updateLocalProject(page, projectName, patch) {
  await page.evaluate(({ name, values }) => {
    const stored = window.localStorage.getItem("sp2i:projects");
    const projects = stored ? JSON.parse(stored) : [];
    const next = projects.map((project) => (
      new RegExp(name, "i").test(project.name || "")
        ? { ...project, ...values }
        : project
    ));
    window.localStorage.setItem("sp2i:projects", JSON.stringify(next));
  }, { name: projectName, values: patch });
}

async function navigateSpa(page, path) {
  await page.evaluate((nextPath) => {
    window.history.pushState({}, "", nextPath);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }, path);
}

async function expectNoHorizontalOverflow(page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(2);
}

test("SP2I landing page and project workflow smoke test", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: /sp2i/i })).toBeVisible();
  await expect(page.locator("form").getByRole("button", { name: /se connecter/i })).toBeVisible();

  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: /mes projets/i })).toBeVisible();
  await expect(page.getByText(/parcours projet/i).first()).toBeVisible();

  const workflowAction = page.getByRole("button", {
    name: /configurer le projet|importer le dqe|ouvrir le workspace/i,
  }).first();
  await expect(workflowAction).toBeVisible();

  await expect(page.getByText(/configuration/i).first()).toBeVisible();
  await expect(page.getByText(/dqe/i).first()).toBeVisible();
  await expect(page.getByText(/budget/i).first()).toBeVisible();
  await expect(page.getByText(/sc.narios/i).first()).toBeVisible();

  await page.screenshot({
    path: "test-results/screenshots/project-hub-workflow.png",
    fullPage: true,
  });
});

test("project setup persists after refresh", async ({ page }) => {
  const configuredCard = await configureFirstUnconfiguredProject(page, "Projet test workflow");
  await expect(configuredCard).toBeVisible();
  await expect(configuredCard.getByRole("button", { name: /importer le dqe/i })).toBeVisible();

  await page.reload({ waitUntil: "domcontentloaded" });

  const persistedCard = page.getByTestId("project-card").filter({
    hasText: /projet test workflow/i,
  }).first();
  await expect(persistedCard).toBeVisible();
  await expect(persistedCard.getByRole("button", { name: /importer le dqe/i })).toBeVisible();

  await page.screenshot({
    path: "test-results/screenshots/project-hub-after-setup-refresh.png",
    fullPage: true,
  });
});

test("workspace summary shows next recommended action", async ({ page }) => {
  const configuredCard = await configureFirstUnconfiguredProject(page, "Projet synthese workflow");
  await configuredCard.getByRole("button", { name: /ouvrir le workspace/i }).click();

  const summary = page.getByTestId("workspace-summary");
  await expect(summary).toBeVisible();
  await expect(summary.getByRole("heading", { name: /projet synthese workflow/i })).toBeVisible();
  await expect(summary.getByTestId("project-workflow-stepper")).toBeVisible();
  await expect(summary.getByText(/prochaine action recommandee/i)).toBeVisible();
  await expect(summary.getByTestId("workspace-next-action")).toHaveText(/importer le dqe/i);
  await expect(summary.getByTestId("project-quick-actions")).toBeVisible();
  await expect(page.getByTestId("project-workflow-breadcrumb")).toHaveCount(0);

  await page.screenshot({
    path: "test-results/screenshots/workspace-summary.png",
    fullPage: true,
  });
});

test("workspace displays the selected project instead of the default fallback", async ({ page }) => {
  await configureFirstUnconfiguredProject(page, "Projet actif synchronise");
  await page.getByTestId("project-card").filter({ hasText: /projet actif synchronise/i }).first().getByRole("button", { name: /ouvrir le workspace/i }).click();

  await expect(page.locator(".project-selector")).toContainText(/projet actif synchronise/i);
  await expect(page.locator(".sidebar-project-status")).toContainText(/projet actif synchronise/i);
});

test("pilotage analytics page shows export rapport projet button", async ({ page }) => {
  const configuredCard = await configureFirstUnconfiguredProject(page, "Projet export rapport");
  await configuredCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await page.goto("/app/analytics", { waitUntil: "domcontentloaded" });

  await expect(page.getByTestId("export-report-button")).toBeVisible();
});

test("unconfigured project limits quick actions", async ({ page }) => {
  await openUnconfiguredProjectWorkspace(page);

  const quickActions = page.getByTestId("workspace-header").getByTestId("project-quick-actions");
  await expect(quickActions).toBeVisible();
  await expect(quickActions.getByRole("button", { name: /configurer le projet/i })).toBeVisible();
  await expect(quickActions.getByRole("button", { name: /tester un sc/i })).toHaveCount(0);
  await expect(quickActions.getByRole("button", { name: /nouveau sc/i })).toHaveCount(0);
});

test("DQE page with unconfigured project shows setup CTA", async ({ page }) => {
  await openUnconfiguredProjectWorkspace(page);
  await navigateSpa(page, "/app/dqe?tab=import");

  const emptyState = page.getByTestId("dqe-empty-state").first();
  await expect(emptyState).toBeVisible();
  await expect(emptyState).toContainText(/ce projet doit etre configure/i);
  await expect(emptyState.getByTestId("workflow-empty-action")).toHaveText(/configurer le projet/i);
});

test("scenarios page without DQE shows guided empty state", async ({ page }) => {
  await openConfiguredProjectWorkspace(page, "Projet scenarios sans DQE");
  await navigateSpa(page, "/app/simulation");

  await expect(page.getByRole("heading", { name: /simuler les sc/i })).toBeVisible();
  const emptyState = page.getByTestId("scenario-empty-state").first();
  await expect(emptyState).toBeVisible();
  await expect(emptyState).toContainText(/aucun dqe actif|importez et certifiez un dqe/i);
  await expect(emptyState.getByTestId("workflow-empty-action")).toHaveText(/importer un dqe/i);
});

test("scenarios with certified DQE but unsynced budget shows sync CTA", async ({ page }) => {
  await openConfiguredProjectWorkspace(page, "Projet DQE certifie sans budget");
  await setCertifiedDqeWithoutBudget(page);
  await navigateSpa(page, "/app/simulation");

  const emptyState = page.getByTestId("scenario-empty-state").first();
  await expect(emptyState).toBeVisible();
  await expect(emptyState).toContainText(/budget doit etre synchronise/i);
  await expect(emptyState.getByTestId("workflow-empty-action")).toHaveText(/synchroniser le budget/i);
});

test("project quick actions block simulation when budget non synchronise", async ({ page }) => {
  await openConfiguredProjectWorkspace(page, "Projet quick actions budget bloque");
  await setCertifiedDqeWithoutBudget(page);
  await navigateSpa(page, "/app");

  const testerButton = page.getByTestId("project-quick-actions").getByRole("button", { name: /simuler.*capex/i }).first();
  await expect(testerButton).toBeDisabled();
});

test("budget synchronise debloque Simuler la strategie CAPEX", async ({ page }) => {
  const projectName = "Projet budget synchronise";
  await openConfiguredProjectWorkspace(page, projectName);
  await setSyncedDqe(page);
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });

  const projectCard = page.getByTestId("project-card").filter({ hasText: new RegExp(projectName, "i") }).first();
  await expect(projectCard).toBeVisible();
  await projectCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await expect(page.getByTestId("workspace-header")).toBeVisible();

  await expect(page.getByTestId("workspace-next-action")).toHaveText(/simuler.*capex/i);
  const testerButton = page.getByTestId("project-quick-actions").getByRole("button", { name: /simuler.*capex/i }).first();
  await expect(testerButton).toBeEnabled();
});

test("simulation reste en attente tant que l'utilisateur ne lance pas le scenario", async ({ page }) => {
  await openConfiguredProjectWorkspace(page, "Projet simulation manuelle");
  await setSyncedDqe(page);
  let simulateRequests = 0;
  await page.route("**/simulation/simulate", async (route) => {
    simulateRequests += 1;
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
          lignes_dqe: 130,
          lignes_simulees: 130,
          lignes_importables: 24,
          lignes_retenues: 2,
          lignes_arbitrees: 130,
        },
        lignes: [
          {
            id_ligne: "test-import-1",
            designation: "Luminaire Shanghai",
            decision_finale: "IMPORT",
            risk_level: "MEDIUM",
            economie_nette: 25000000,
          },
        ],
        metadata: {
          line_counts: {
            dqe: 130,
            simulees: 130,
            importables: 24,
            retenues: 2,
            arbitrees: 130,
          },
        },
      }),
    });
  });

  await navigateSpa(page, "/app/simulation");

  await expect(page.getByText(/simulation non lanc/i).first()).toBeVisible();
  await expect(page.getByText(/roi import/i)).toHaveCount(0);
  await expect(page.getByText(/viable/i)).toHaveCount(0);
  expect(simulateRequests).toBe(0);

  await page.getByRole("button", { name: /lancer simulation/i }).click();

  await expect(page.getByText(/simulation.*lanc/i).first()).toBeVisible();
  await expect(page.getByText(/roi import/i)).toBeVisible();
  await expect(page.getByText(/viable|validation requise/i).first()).toBeVisible();
  await expect(page.getByTestId("project-workflow-breadcrumb")).toContainText(/simul/i);
  expect(simulateRequests).toBe(1);

  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });
  const projectCard = page.getByTestId("project-card").filter({ hasText: /projet simulation manuelle/i }).first();
  await expect(projectCard.getByTestId("project-primary-action")).toHaveText(/valider.*d[eé]cisions import critiques|analyser.*arbitrages achat/i);
});

test("procurement page without scenario shows guided empty state", async ({ page }) => {
  await openConfiguredProjectWorkspace(page, "Projet approvisionnement sans scenario");
  await navigateSpa(page, "/app/procurement");

  await expect(page.getByRole("heading", { name: /que faut-il/i })).toBeVisible();
  const emptyState = page.getByTestId("procurement-empty-state").first();
  await expect(emptyState).toBeVisible();
  await expect(emptyState).toContainText(/aucun|lancez une simulation/i);
  await expect(emptyState.getByTestId("workflow-empty-action")).toHaveText(/simuler.*capex/i);
  await expect(page.getByRole("button", { name: /^exporter le dossier direction$/i })).toBeVisible();
  await expect(page.getByTestId("procurement-validation-summary")).toContainText(/decisions/i);
});

test("pilotage approvisionnement cockpit orchestrates existing workflow", async ({ page }) => {
  const projectName = "Projet pilotage approvisionnement";
  await openConfiguredProjectWorkspace(page, projectName);
  await setSyncedDqe(page);
  await updateLocalProject(page, projectName, {
    workflow_status: "SCENARIO_READY",
    scenario_ready: true,
    procurement_ready: false,
  });
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });

  const projectCard = page.getByTestId("project-card").filter({ hasText: new RegExp(projectName, "i") }).first();
  await projectCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await navigateSpa(page, "/app/approvisionnement");

  await expect(page.getByRole("heading", { name: /commandes, fournisseurs, risques/i })).toBeVisible();
  await expect(page.getByText(/pilotage approvisionnement/i).first()).toBeVisible();
  await expect(page.getByText(/budget engag/i).first()).toBeVisible();
  await expect(page.getByText(/portefeuille achat consolid/i)).toBeVisible();
  await expect(page.getByText(/copilote approvisionnement sp2i/i)).toBeVisible();
});

test("procurement bulk arbitrage validates selected lines", async ({ page }) => {
  await mockProcurementLinesApi(page);
  const projectName = "Projet procurement arbitrage bulk";
  await openConfiguredProjectWorkspace(page, projectName);
  await setSyncedDqe(page);
  await updateLocalProject(page, projectName, {
    workflow_status: "SCENARIO_READY",
    scenario_ready: true,
    procurement_ready: false,
    procurement_status: "REVIEW_REQUIRED",
  });

  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });
  const projectCard = page.getByTestId("project-card").filter({ hasText: new RegExp(projectName, "i") }).first();
  await projectCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await navigateSpa(page, "/app/procurement");

  await expect(page.getByRole("heading", { name: /que faut-il/i })).toBeVisible();
  await expect(page.getByText(/arbitrage fournisseur par ligne/i)).toBeVisible();

  const rowChecks = page.getByRole("checkbox");
  await expect(rowChecks.nth(1)).toBeVisible();
  await rowChecks.nth(1).click();
  await rowChecks.nth(2).click();

  const toolbar = page.getByTestId("procurement-bulk-toolbar");
  await expect(toolbar).toBeVisible();
  await expect(toolbar).toContainText(/2 ligne/i);
  await toolbar.getByRole("button", { name: /valider import/i }).click();
  await expect(page.getByTestId("procurement-validation-summary")).toContainText(/Validees\s*:\s*[1-9]\d*/i);
  await expect(page.getByTestId("procurement-validation-summary")).not.toContainText(/Validees\s*:\s*0/i);
  await expect(page.getByTestId("procurement-decision-summary")).toContainText(/[1-9]\d* valid/i);
  await expect(page.getByText(/workflow approval/i)).toBeVisible();
  await expect(page.getByText(/import fournisseur/i).first()).toBeVisible();

  await navigateSpa(page, "/app/projects");
  await expect(projectCard.getByTestId("project-primary-action")).toHaveText(/valider/i);
});

test("scenario pret sans approvisionnement affiche CTA arbitrages achat", async ({ page }) => {
  const projectName = "Projet scenario pret sans achat";
  await openConfiguredProjectWorkspace(page, projectName);
  await setSyncedDqe(page);
  await updateLocalProject(page, projectName, {
    workflow_status: "SCENARIO_READY",
    scenario_ready: true,
    procurement_ready: false,
  });
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });

  const projectCard = page.getByTestId("project-card").filter({ hasText: new RegExp(projectName, "i") }).first();
  await expect(projectCard).toBeVisible();
  await expect(projectCard.getByTestId("project-primary-action")).toHaveText(/analyser.*arbitrages achat/i);
});

test("approvisionnement pret sans actions chantier affiche CTA Preparation Chantier", async ({ page }) => {
  const projectName = "Projet achat pret preparation chantier";
  await openConfiguredProjectWorkspace(page, projectName);
  await setSyncedDqe(page);
  await updateLocalProject(page, projectName, {
    workflow_status: "PROCUREMENT_READY",
    scenario_ready: true,
    procurement_ready: true,
    procurement_decisions_count: 303,
    procurement_validated_decisions_count: 303,
  });
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });

  const projectCard = page.getByTestId("project-card").filter({ hasText: new RegExp(projectName, "i") }).first();
  await expect(projectCard).toBeVisible();
  await expect(projectCard.getByTestId("project-primary-action")).toHaveText(/actions chantier/i);

  await projectCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  const quickActions = page.getByTestId("workspace-header").getByTestId("project-quick-actions");
  await expect(quickActions.getByRole("button", { name: /lots chantier/i })).toBeVisible();
  await navigateSpa(page, "/app/site?tab=planning");
  await expect(page.getByRole("heading", { name: /actions chantier par lot/i })).toBeVisible();
  await expect(page.getByTestId("execution-actions-summary")).toHaveCount(0);
  await expect(page.getByText(/Actions chantier prioritaires/i)).toHaveCount(0);
});

test("page Scenarios affiche le fil d'Ariane workflow compact", async ({ page }) => {
  const projectName = "Projet breadcrumb scenarios";
  await openConfiguredProjectWorkspace(page, projectName);
  await setSyncedDqe(page);
  await updateLocalProject(page, projectName, {
    workflow_status: "PROCUREMENT_READY",
    scenario_ready: true,
    procurement_ready: true,
    procurement_decisions_count: 303,
    procurement_validated_decisions_count: 303,
  });
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });

  const projectCard = page.getByTestId("project-card").filter({ hasText: new RegExp(projectName, "i") }).first();
  await projectCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await navigateSpa(page, "/app/simulation");

  const breadcrumb = page.getByTestId("project-workflow-breadcrumb");
  await expect(breadcrumb).toBeVisible();
  await expect(breadcrumb).toContainText(/simul/i);
  await expect(breadcrumb).toContainText(/approvisionnement/i);
  await expect(breadcrumb).toContainText(/chantier/i);
  await expect(breadcrumb.getByTestId("workflow-breadcrumb-action")).toHaveText(/actions chantier/i);
});

test("preparation chantier prete affiche CTA preparation des lots", async ({ page }) => {
  const projectName = "Projet preparation chantier prete";
  await openConfiguredProjectWorkspace(page, projectName);
  await setSyncedDqe(page);
  await updateLocalProject(page, projectName, {
    workflow_status: "EXECUTION_READY",
    scenario_ready: true,
    procurement_ready: true,
    execution_ready: true,
    procurement_decisions_count: 303,
    procurement_validated_decisions_count: 303,
    execution_actions_count: 5,
    execution_critical_lots_count: 1,
    execution_deliveries_to_watch_count: 3,
  });
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });

  const projectCard = page.getByTestId("project-card").filter({ hasText: new RegExp(projectName, "i") }).first();
  await expect(projectCard).toBeVisible();
  await expect(projectCard.getByTestId("project-primary-action")).toHaveText(/suivre.*lots/i);

  await projectCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  const quickActions = page.getByTestId("workspace-header").getByTestId("project-quick-actions");
  await expect(quickActions.getByRole("button", { name: /lots chantier/i })).toBeVisible();
});

test("preparation chantier without scenario shows simulation CTA", async ({ page }) => {
  await openConfiguredProjectWorkspace(page, "Projet preparation chantier sans scenario");
  await navigateSpa(page, "/app/site?tab=planning");

  const emptyState = page.getByTestId("execution-empty-state").first();

  await expect(emptyState).toBeVisible();
  await expect(emptyState).toContainText(/simulation|lancez une simulation/i);
  await expect(emptyState.getByTestId("workflow-empty-action")).toHaveText(
    /simuler.*capex/i
  );

  await expect(emptyState).not.toContainText(/arbitrages achat/i);
});

test("preparation chantier avec approvisionnement pret demande readiness chantier", async ({ page }) => {
  const projectName = "Projet preparation chantier a preparer";
  await openConfiguredProjectWorkspace(page, projectName);
  await setSyncedDqe(page);
  await updateLocalProject(page, projectName, {
    workflow_status: "PROCUREMENT_READY",
    scenario_ready: true,
    procurement_ready: true,
    execution_ready: false,
  });
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });

  const projectCard = page.getByTestId("project-card").filter({ hasText: new RegExp(projectName, "i") }).first();
  await projectCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await navigateSpa(page, "/app/site?tab=planning");

  const emptyState = page.getByTestId("execution-empty-state").first();
  await expect(emptyState).toBeVisible();
  await expect(emptyState).toContainText(/approvisionnement est|actions chantier/i);
  await expect(page.getByRole("button", { name: /actions chantier/i }).first()).toBeVisible();
  await expect(page.getByTestId("execution-actions-summary")).toHaveCount(0);
  await expect(emptyState.getByTestId("workflow-empty-action")).toHaveText(/actions chantier/i);
});

test("preparation chantier BIM-lite shows spatial drilldown and spatial tab", async ({ page }) => {
  const projectName = "Projet execution spatial";
  await openConfiguredProjectWorkspace(page, projectName);
  await setSpatialSyncedDqe(page);
  await updateLocalProject(page, projectName, {
    workflow_status: "EXECUTION_READY",
    scenario_ready: true,
    procurement_ready: true,
    execution_ready: true,
    execution_status: "READY",
    execution_actions_count: 3,
  });
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });

  const projectCard = page.getByTestId("project-card").filter({ hasText: new RegExp(projectName, "i") }).first();
  await expect(projectCard).toBeVisible();
  await projectCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await navigateSpa(page, "/app/site?tab=planning");

  await expect(page.getByTestId("spatial-drilldown-panel")).toBeVisible();
  await expect(page.getByTestId("spatial-kpi-band")).toContainText(/bim-lite/i);
  await expect(page.getByTestId("execution-tab-spatial")).toBeVisible();
  await page.getByTestId("execution-tab-spatial").click();
  await expect(page.getByTestId("spatial-timeline-board")).toBeVisible();
  await expect(page.getByTestId("spatial-timeline-board")).toContainText(/timeline spatiale/i);
  await expect(page.getByTestId("spatial-event-feed")).toContainText(/event engine|timeline spatiale/i);
  await expect(page.getByTestId("spatial-critical-path-panel")).toContainText(/impact chantier|propagation spatiale/i);
  await expect(page.getByTestId("spatial-execution-board")).toBeVisible();
});

test("Pilotage with incomplete workflow shows next action", async ({ page }) => {
  await openUnconfiguredProjectWorkspace(page);
  await navigateSpa(page, "/app/analytics");

  const summary = page.getByTestId("pilotage-summary");
  await expect(summary).toBeVisible();
  await expect(summary.getByTestId("pilotage-primary-action")).toHaveText(/configurer le projet/i);
  await expect(page.getByTestId("pilotage-alerts")).toContainText(/configuration projet incomplete/i);
});

test("Pilotage with budget synced but no scenario shows Simuler strategie CAPEX", async ({ page }) => {
  const projectName = "Projet pilotage budget pret";
  await openConfiguredProjectWorkspace(page, projectName);
  await setSyncedDqe(page);
  await navigateSpa(page, "/app/analytics");

  const summary = page.getByTestId("pilotage-summary");
  await expect(summary).toBeVisible();
  await expect(summary.getByTestId("pilotage-primary-action")).toHaveText(/simuler.*capex/i);
  await expect(page.getByTestId("pilotage-alerts")).toContainText(/aucun/i);
});

test("Pilotage with scenario ready shows arbitrages achat", async ({ page }) => {
  const projectName = "Projet pilotage scenario pret";
  await openConfiguredProjectWorkspace(page, projectName);
  await setSyncedDqe(page);
  await updateLocalProject(page, projectName, {
    workflow_status: "SCENARIO_READY",
    scenario_ready: true,
    procurement_ready: false,
  });
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });
  const projectCard = page.getByTestId("project-card").filter({ hasText: new RegExp(projectName, "i") }).first();
  await projectCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await navigateSpa(page, "/app/analytics");

  const summary = page.getByTestId("pilotage-summary");
  await expect(summary).toBeVisible();
  await expect(summary.getByTestId("pilotage-primary-action")).toHaveText(/analyser.*arbitrages achat/i);
  await expect(page.getByTestId("pilotage-alerts")).toContainText(/approvisionnement/i);
});

test("Pilotage with preparation chantier at risk shows alert", async ({ page }) => {
  const projectName = "Projet pilotage preparation chantier risque";
  await openConfiguredProjectWorkspace(page, projectName);
  await setSyncedDqe(page);
  await updateLocalProject(page, projectName, {
    workflow_status: "EXECUTION_READY",
    scenario_ready: true,
    procurement_ready: true,
    execution_ready: true,
    execution_status: "AT_RISK",
    execution_actions_count: 5,
    execution_critical_lots_count: 1,
    execution_deliveries_to_watch_count: 3,
    execution_eta_to_watch_count: 2,
  });
  await page.goto("/app/projects", { waitUntil: "domcontentloaded" });
  const projectCard = page.getByTestId("project-card").filter({ hasText: new RegExp(projectName, "i") }).first();
  await projectCard.getByRole("button", { name: /ouvrir le workspace/i }).click();
  await navigateSpa(page, "/app/analytics");

  const summary = page.getByTestId("pilotage-summary");
  await expect(summary).toBeVisible();
  await expect(summary.getByTestId("pilotage-primary-action")).toHaveText(/traiter.*lots chantier/i);
  await expect(page.getByTestId("pilotage-alerts")).toContainText(/chantier.*risque/i);
});

test("responsive project workflow minimal layout", async ({ page }) => {
  const viewports = [
    { name: "desktop", width: 1440, height: 900 },
    { name: "mobile", width: 390, height: 844 },
  ];

  for (const viewport of viewports) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await resetDemoProjects(page);
    await expect(page.getByTestId("project-card").first()).toBeVisible();
    await expect(page.getByTestId("project-primary-action").first()).toBeVisible();
    await expect(page.getByTestId("project-workflow-stepper").first()).toBeVisible();
    await expectNoHorizontalOverflow(page);

    await page.goto("/app", { waitUntil: "domcontentloaded" });
    await expect(page.getByTestId("workspace-header")).toBeVisible();
    await expect(page.getByTestId("workspace-header").getByTestId("project-quick-actions")).toBeVisible();
    await expect(page.getByTestId("project-workflow-stepper").first()).toBeVisible();
    await expectNoHorizontalOverflow(page);

    await page.screenshot({
      path: `test-results/screenshots/project-workflow-${viewport.name}.png`,
      fullPage: true,
    });
  }
});
