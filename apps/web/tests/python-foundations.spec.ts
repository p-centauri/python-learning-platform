import { test, expect } from "@playwright/test";

test("foundations lessons lead to practice and a downloadable local project", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Foundation Learner");
  await page
    .getByLabel("Email address")
    .fill(`foundations-${Date.now()}@example.com`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("a-long-browser-test-passphrase");
  await page.getByRole("button", { name: "Create workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome aboard, Foundation." }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Start learning" }).click();
  await expect(
    page.getByRole("heading", { name: "Run Python in your own workspace" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Independent task" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Mark reading complete" }).click();
  await expect(
    page.getByRole("button", { name: "Reading completed" }),
  ).toBeDisabled();
  await page
    .getByRole("link", { name: /The package went to another interpreter/ })
    .click();
  await page
    .getByRole("radio", { name: /\.venv\/bin\/python -m pip install example/ })
    .check();
  await page.getByRole("button", { name: "Submit answer" }).click();
  await expect(page.getByText("Well reasoned.")).toBeVisible();
  await page.goto("/learn");
  await expect(page.locator(".path-summary")).toContainText(
    "390 practice exercises",
  );
  const module = page.getByRole("region", {
    name: "Python foundations: build an expense tracker",
  });
  await expect(module.locator("a.lesson-row")).toHaveCount(9);
  await module.getByRole("link", { name: "Build the module project" }).click();
  const project = page.getByRole("article", { name: "Expense tracker CLI" });
  await expect(project).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await project
    .getByRole("link", { name: "Download starter and tests" })
    .click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("expense-tracker-starter.zip");
  expect(await download.failure()).toBeNull();
  await project.getByRole("checkbox").first().check();
  await expect(project.getByText("1/5 milestones")).toBeVisible();
  await page.reload();
  await expect(project.getByRole("checkbox").first()).toBeChecked();
  await page.route("**/api/projects/python-expenses/tasks/setup", (route) =>
    route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Simulated save failure" }),
    }),
  );
  // The rejected save can restore the checked state before uncheck() verifies it.
  await project.getByRole("checkbox").first().click();
  await expect(page.getByText("Simulated save failure")).toBeVisible();
  await expect(project.getByRole("checkbox").first()).toBeChecked();
  await page.unroute("**/api/projects/python-expenses/tasks/setup");
  await project
    .getByRole("link", { name: "Read the project instructions" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Test and build your expense tracker" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Module finish check" }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
  ).toBe(false);
  await page.goto("/learn");
  await expect(module).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
  ).toBe(false);
  await module.screenshot({
    path: "test-results/python-foundations-mobile.png",
  });
});
