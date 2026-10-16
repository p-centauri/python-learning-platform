import { test, expect } from "@playwright/test";

test("migration teaching connects revision, preserved facts, rollback and saved evidence", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Schema Learner");
  await page
    .getByLabel("Email address")
    .fill(`schema-${Date.now()}@example.com`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("a-long-browser-test-passphrase");
  async function create() {
    const pending = page.waitForResponse(
      (response) =>
        response.url().endsWith("/api/auth/register") &&
        response.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Create workspace" }).click();
    return pending;
  }
  let registration = await create();
  if (registration.status() === 429) {
    // Respect the production signup limit as the browser suite grows.
    test.setTimeout(120000);
    const seconds = Number(registration.headers()["retry-after"] || "60");
    await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
    registration = await create();
  }
  expect(registration.status()).toBe(201);
  await expect(
    page.getByRole("heading", { name: "Welcome aboard, Schema." }),
  ).toBeVisible();
  await page.goto("/lessons/python-stream-evidence");
  await page
    .getByRole("link", {
      name: "Give delivery tables an explicit revision history",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Give delivery tables an explicit revision history",
      exact: true,
      level: 1,
    }),
  ).toBeVisible();
  const prediction = page.getByRole("article", {
    name: "Predict before checking",
    exact: true,
  });
  await prediction
    .getByRole("radio", { name: "delivery_004", exact: true })
    .check();
  await prediction
    .getByRole("button", { name: "Check my answer", exact: true })
    .click();
  await expect(prediction.getByRole("status")).toContainText(
    "That matches the checkpoint",
  );
  await page.reload();
  await expect(prediction.getByRole("status")).toContainText(
    "That matches the checkpoint",
  );
  await page
    .getByRole("region", { name: "Words in this lesson", exact: true })
    .getByRole("link", { name: "Migration revision", exact: true })
    .click();
  await expect(page).toHaveURL(/\/glossary#delivery-revision$/);
  await expect(page.locator("#delivery-revision")).toBeFocused();
  await page.goto("/lessons/python-delivery-revisions");
  for (const title of [
    "Preserve existing facts without inventing deliveries",
    "Check the schema beyond its recorded head",
    "Keep migration failure inside one transaction",
    "Name the history that a rollback deletes",
    "Rehearse and review the installed migration lab",
  ]) {
    await page
      .getByRole("navigation", { name: "Lesson navigation" })
      .getByRole("link", { name: /Next:/ })
      .click();
    await expect(
      page.getByRole("heading", { name: title, exact: true, level: 1 }),
    ).toBeVisible();
    await expect(
      page
        .getByRole("region", { name: "See the idea", exact: true })
        .getByRole("listitem"),
    ).toHaveCount(3);
  }
  const dashboard = await (await page.request.get("/api/dashboard")).json();
  expect(dashboard.mastery).toBe(0);
  expect(dashboard.completed_lessons).toBe(0);
  const recall = await page.request.post(
    "/api/recall/topics/python-schema-drift/sessions",
    {
      headers: { "X-Academy-Request": "1" },
      data: { mode: "practice" },
    },
  );
  expect(recall.status()).toBe(201);
  expect(await recall.text()).not.toContain('"accepted"');
  await page.goto("/learn");
  await expect(
    page
      .getByRole("region", {
        name: "Delivery schema & migration rehearsal",
        exact: true,
      })
      .locator("a.lesson-row"),
  ).toHaveCount(6);
  await page.goto("/projects#python-delivery-schema");
  const project = page.getByRole("article", {
    name: "Delivery migration lab",
    exact: true,
  });
  const downloading = page.waitForEvent("download");
  await project
    .getByRole("link", { name: "Download starter and tests", exact: true })
    .click();
  const download = await downloading;
  expect(download.suggestedFilename()).toBe("delivery-schema-starter.zip");
  expect(await download.failure()).toBeNull();
  await project.getByRole("checkbox").first().check();
  await expect(project).toContainText("1/4 milestones");
  await page.reload();
  await expect(project.getByRole("checkbox").first()).toBeChecked();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await project
      .locator("header h2")
      .evaluate((heading) => heading.getBoundingClientRect().width),
  ).toBeGreaterThan(200);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await project.evaluate((element) => {
    (document.activeElement as HTMLElement)?.blur();
    window.scrollTo(
      0,
      window.scrollY + element.getBoundingClientRect().top - 20,
    );
  });
  await page.screenshot({
    path: "test-results/schema-project-mobile.png",
  });
  await project
    .getByRole("link", { name: "Submit work and view feedback", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Start submission draft", exact: true })
    .click();
  await expect(
    page
      .getByText("Versioned schema & preserved facts", { exact: true })
      .first(),
  ).toBeVisible();
  await page
    .getByLabel("Design explanation", { exact: true })
    .fill(
      "The additive revisions preserve every old service fact and timestamp. Head alone does not prove no drift or valid CHECK expressions. Downgrade retains facts but loses delivery history; replay can apply again after inbox deletion. Real PostgreSQL failures and locks, installed resources and broker composition are observed separately from deployment.",
    );
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Draft saved" }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("textbox", { name: "Design explanation", exact: true }),
  ).toHaveValue(
    "The additive revisions preserve every old service fact and timestamp. Head alone does not prove no drift or valid CHECK expressions. Downgrade retains facts but loses delivery history; replay can apply again after inbox deletion. Real PostgreSQL failures and locks, installed resources and broker composition are observed separately from deployment.",
  );
  expect(
    (await (await page.request.get("/api/dashboard")).json()).mastery,
  ).toBe(0);
});
