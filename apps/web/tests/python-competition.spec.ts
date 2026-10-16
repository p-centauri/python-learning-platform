import { test, expect } from "@playwright/test";

test("competition teaching connects actual failure reasoning and saved evidence", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Competition Learner");
  await page
    .getByLabel("Email address")
    .fill(`competition-${Date.now()}@example.com`);
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
    page.getByRole("heading", { name: "Welcome aboard, Competition." }),
  ).toBeVisible();
  await page.goto("/lessons/python-service-evidence");
  await page
    .getByRole("link", {
      name: "What a PostgreSQL transaction can see",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "What a PostgreSQL transaction can see",
      exact: true,
      level: 1,
    }),
  ).toBeVisible();
  const prediction = page.getByRole("article", {
    name: "Predict before checking",
    exact: true,
  });
  await prediction.getByRole("radio", { name: "True", exact: true }).check();
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
    .getByRole("link", { name: "Statement snapshot", exact: true })
    .click();
  await expect(page).toHaveURL(/\/glossary#pg-statement-snapshot$/);
  await expect(page.locator("#pg-statement-snapshot")).toBeFocused();
  await page.goto("/lessons/python-pg-snapshots");
  for (const title of [
    "Observe lock waits and bound blocked statements",
    "Deadlocks, lock order and the chosen victim",
    "Serializable decisions need fresh reads",
    "Bound retries by failure class and transaction ownership",
    "Reconcile uncertain outcomes using complete facts",
    "Competing-transaction evidence and the recovery lab",
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
    "/api/recall/topics/python-pg-retry-policy/sessions",
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
        name: "PostgreSQL competition & recovery",
        exact: true,
      })
      .locator("a.lesson-row"),
  ).toHaveCount(7);
  await page.goto("/projects#python-competing-ingestion");
  const project = page.getByRole("article", {
    name: "Competing ingestion lab",
    exact: true,
  });
  const downloading = page.waitForEvent("download");
  await project
    .getByRole("link", { name: "Download starter and tests", exact: true })
    .click();
  const download = await downloading;
  expect(download.suggestedFilename()).toBe("competing-ingestion-starter.zip");
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
    path: "test-results/competition-project-mobile.png",
  });
  await project
    .getByRole("link", { name: "Submit work and view feedback", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Start submission draft", exact: true })
    .click();
  await expect(
    page
      .getByText("Visibility, lock waits & isolation evidence", { exact: true })
      .first(),
  ).toBeVisible();
  await page
    .getByLabel("Design explanation", { exact: true })
    .fill(
      "Independent connections establish actual snapshots, waits and SQLSTATE. A fresh Session owns each permitted full retry after cleanup; copied facts stay stable. Reconciliation is scoped and read-only, and missing cannot prove rollback. Modeled response loss and manual evidence remain distinct.",
    );
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Draft saved" }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("textbox", { name: "Design explanation", exact: true }),
  ).toHaveValue(
    "Independent connections establish actual snapshots, waits and SQLSTATE. A fresh Session owns each permitted full retry after cleanup; copied facts stay stable. Reconciliation is scoped and read-only, and missing cannot prove rollback. Modeled response loss and manual evidence remain distinct.",
  );
  expect(
    (await (await page.request.get("/api/dashboard")).json()).mastery,
  ).toBe(0);
});
