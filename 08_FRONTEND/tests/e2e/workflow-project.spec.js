import { expect, test } from "@playwright/test";

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
  await expect(page.getByText(/scenarios/i).first()).toBeVisible();

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

  await page.screenshot({
    path: "test-results/screenshots/workspace-summary.png",
    fullPage: true,
  });
});

test("unconfigured project limits quick actions", async ({ page }) => {
  await openUnconfiguredProjectWorkspace(page);

  const quickActions = page.getByTestId("workspace-header").getByTestId("project-quick-actions");
  await expect(quickActions).toBeVisible();
  await expect(quickActions.getByRole("button", { name: /configurer le projet/i })).toBeVisible();
  await expect(quickActions.getByRole("button", { name: /tester un scenario/i })).toHaveCount(0);
  await expect(quickActions.getByRole("button", { name: /nouveau scenario/i })).toHaveCount(0);
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

  await expect(page.getByRole("heading", { name: /simuler les scenarios capex/i })).toBeVisible();
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

test("procurement page without scenario shows guided empty state", async ({ page }) => {
  await openConfiguredProjectWorkspace(page, "Projet approvisionnement sans scenario");
  await navigateSpa(page, "/app/procurement");

  await expect(page.getByRole("heading", { name: /arbitrer local, import, fournisseurs/i })).toBeVisible();
  const emptyState = page.getByTestId("procurement-empty-state").first();
  await expect(emptyState).toBeVisible();
  await expect(emptyState).toContainText(/aucun scenario actif|lancez une simulation/i);
  await expect(emptyState.getByTestId("workflow-empty-action")).toHaveText(/tester un scenario/i);
});

test("execution without procurement shows procurement CTA", async ({ page }) => {
  await openConfiguredProjectWorkspace(page, "Projet execution sans achat");
  await navigateSpa(page, "/app/site?tab=planning");

  const emptyState = page.getByTestId("execution-empty-state").first();
  await expect(emptyState).toBeVisible();
  await expect(emptyState).toContainText(/preparez les arbitrages achat/i);
  await expect(emptyState.getByTestId("workflow-empty-action")).toHaveText(/ouvrir approvisionnement/i);
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
