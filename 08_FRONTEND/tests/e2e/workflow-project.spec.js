import { expect, test } from "@playwright/test";

test("SP2I landing page and project workflow smoke test", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /sp2i/i })).toBeVisible();
  await expect(page.locator("form").getByRole("button", { name: /se connecter/i })).toBeVisible();

  await page.goto("/app/projects");
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
  await page.goto("/app/projects");
  await page.evaluate(() => window.localStorage.clear());
  await page.reload();

  await expect(page.getByRole("heading", { name: /mes projets/i })).toBeVisible();

  const projectCard = page.locator(".project-card").filter({
    has: page.getByRole("button", { name: /configurer le projet/i }),
  }).first();
  await expect(projectCard).toBeVisible();

  await projectCard.getByRole("button", { name: /configurer le projet/i }).click();

  const dialog = page.getByRole("dialog", { name: /configuration projet/i });
  await expect(dialog).toBeVisible();

  await dialog.getByLabel(/nom du projet/i).fill("Projet test workflow");
  await dialog.getByLabel(/organisation \/ client/i).fill("Client test SP2I");
  await dialog.getByLabel(/ville/i).fill("Pointe-Noire");
  await dialog.getByLabel(/^pays/i).fill("Congo-Brazzaville");
  await dialog.getByLabel(/devise projet/i).fill("FCFA");
  await dialog.getByLabel(/responsable projet/i).fill("Responsable test");
  await dialog.getByRole("button", { name: /enregistrer la configuration/i }).click();

  const configuredCard = page.locator(".project-card").filter({
    hasText: /projet test workflow/i,
  }).first();
  await expect(configuredCard).toBeVisible();
  await expect(configuredCard.getByRole("button", { name: /importer le dqe/i })).toBeVisible();

  await page.reload();

  const persistedCard = page.locator(".project-card").filter({
    hasText: /projet test workflow/i,
  }).first();
  await expect(persistedCard).toBeVisible();
  await expect(persistedCard.getByRole("button", { name: /importer le dqe/i })).toBeVisible();

  await page.screenshot({
    path: "test-results/screenshots/project-hub-after-setup-refresh.png",
    fullPage: true,
  });
});
