import { test, expect } from "@playwright/test";

test("functions and testing connect saved guidance, recall and the typed filtering project", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Policy Learner");
  await page
    .getByLabel("Email address")
    .fill(`policy-${Date.now()}@example.com`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("a-long-browser-test-passphrase");
  await page.getByRole("button", { name: "Create workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome aboard, Policy." }),
  ).toBeVisible();
  await page.goto("/lessons/python-ingestion-tests");
  await page
    .getByRole("link", {
      name: "Closures & late binding",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Closures & late binding",
      exact: true,
      level: 1,
    }),
  ).toBeVisible();
  const prediction = page.getByRole("article", {
    name: "Predict before checking",
    exact: true,
  });
  await prediction.getByRole("radio", { name: "[1, 2]", exact: true }).check();
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
    .getByRole("link", { name: "Closure", exact: true })
    .click();
  await expect(page).toHaveURL(/\/glossary#closure$/);
  await expect(page.locator("#closure")).toBeFocused();
  await page.goto("/lessons/python-closures");
  for (const title of [
    "Arguments, signatures & defaults",
    "Decorators that preserve behavior",
    "Pytest fixtures & useful case tables",
    "Test doubles & patching the lookup site",
    "Safe logging with observable outcomes",
    "Bounded regex rules & the policy lab",
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
    "/api/recall/topics/python-test-fixtures/sessions",
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
        name: "Python functions, testing & safe diagnostics",
        exact: true,
      })
      .locator("a.lesson-row"),
  ).toHaveCount(7);
  await page.goto("/projects#python-feed-policy");
  const project = page.getByRole("article", {
    name: "Feed filtering & test-design lab",
    exact: true,
  });
  const downloading = page.waitForEvent("download");
  await project
    .getByRole("link", { name: "Download starter and tests", exact: true })
    .click();
  const download = await downloading;
  expect(download.suggestedFilename()).toBe("feed-policy-starter.zip");
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
  await page.screenshot({ path: "test-results/policy-project-mobile.png" });
  await project
    .getByRole("link", { name: "Submit work and view feedback", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Start submission draft", exact: true })
    .click();
  await expect(
    page
      .getByText("Bounded grammar & independent settings", { exact: true })
      .first(),
  ).toBeVisible();
  await page
    .getByLabel("Design explanation", { exact: true })
    .fill(
      "The filter borrows input; each factory call owns its settings and the wrapper preserves reporter outcomes.",
    );
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Draft saved" }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("textbox", { name: "Design explanation", exact: true }),
  ).toHaveValue(
    "The filter borrows input; each factory call owns its settings and the wrapper preserves reporter outcomes.",
  );
  expect(
    (await (await page.request.get("/api/dashboard")).json()).mastery,
  ).toBe(0);
});
