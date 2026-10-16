import { test, expect, type Page } from "@playwright/test";
async function register(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Lesson Learner");
  await page
    .getByLabel("Email address")
    .fill(`lesson-e2e-${Date.now()}@example.com`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("a-long-browser-test-passphrase");
  await page.getByRole("button", { name: "Create workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome aboard, Lesson." }),
  ).toBeVisible();
}

test("lesson checkpoints keep fixed feedback; section links, diagrams and glossary connect the teaching", async ({
  page,
}) => {
  await register(page);
  await page.goto("/lessons/python-values");
  await page.getByText("Jump to a section", { exact: true }).click();
  const toc = page.getByRole("navigation", { name: "On this lesson" });
  await toc
    .getByRole("link", { name: "Values have types", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Values have types", exact: true }),
  ).toBeFocused();
  await toc.getByRole("link", { name: "See the idea", exact: true }).click();
  const diagram = page.getByRole("region", {
    name: "See the idea",
    exact: true,
  });
  await expect(diagram.getByRole("listitem")).toHaveCount(3);
  const prediction = page.getByRole("article", {
    name: "Predict before checking",
    exact: true,
  });
  const initial = await (
    await page.request.get("/api/lesson-activities/python-values")
  ).json();
  expect(initial.history).toEqual([]);
  for (const field of [
    "answer",
    "explanation",
    "validation",
    "definition_snapshot",
  ])
    expect(JSON.stringify(initial)).not.toContain(`"${field}"`);
  await prediction.getByRole("radio", { name: "84", exact: true }).check();
  await prediction
    .getByRole("button", { name: "Check my answer", exact: true })
    .click();
  await expect(prediction.getByRole("status")).toContainText(
    "Try tracing it once more",
  );
  await expect(prediction.getByRole("status")).toContainText("Expected: 12");
  await prediction
    .getByRole("button", { name: "Try this checkpoint again", exact: true })
    .click();
  await prediction.getByRole("radio", { name: "12", exact: true }).check();
  await prediction
    .getByRole("button", { name: "Check my answer", exact: true })
    .click();
  await expect(prediction.getByRole("status")).toContainText(
    "That matches the checkpoint",
  );
  const debug = page.getByRole("article", {
    name: "Find the smallest useful fix",
    exact: true,
  });
  await debug
    .getByRole("radio", {
      name: "chosen = 90 if limit is None else limit",
      exact: true,
    })
    .check();
  await debug
    .getByRole("button", { name: "Check my answer", exact: true })
    .click();
  await expect(debug.getByRole("status")).toContainText("preserves zero");
  await page.reload();
  await expect(prediction.getByRole("status")).toContainText(
    "That matches the checkpoint",
  );
  await prediction
    .getByText("Saved attempts (2 in recent lesson history)", { exact: true })
    .click();
  await expect(prediction).toContainText("Your choice: 84");
  await expect(prediction).toContainText("Your choice: 12");
  const dashboard = await (await page.request.get("/api/dashboard")).json();
  expect(dashboard.mastery).toBe(0);
  expect(dashboard.completed_lessons).toBe(0);
  expect(dashboard.attempts).toBe(0);
  await page.evaluate(() => (document.activeElement as HTMLElement)?.blur());
  await page
    .getByRole("region", { name: "Pause and try it", exact: true })
    .screenshot({ path: "test-results/interactive-checkpoints-desktop.png" });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await diagram.screenshot({
    path: "test-results/interactive-diagram-mobile.png",
  });
  await prediction.evaluate((element) => {
    (document.activeElement as HTMLElement)?.blur();
    window.scrollTo(
      0,
      window.scrollY + element.getBoundingClientRect().top - 20,
    );
  });
  await page.screenshot({
    path: "test-results/interactive-checkpoint-mobile.png",
  });
  await page
    .getByRole("button", { name: "Mark reading complete", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Reading completed", exact: true }),
  ).toBeDisabled();
  expect(
    (await (await page.request.get("/api/dashboard")).json()).mastery,
  ).toBe(0);
  await page
    .getByRole("navigation", { name: "Lesson navigation" })
    .getByRole("link", { name: /Previous:/ })
    .click();
  await expect(page).toHaveURL(/\/lessons\/python-start$/);
  await page
    .getByRole("navigation", { name: "Lesson navigation" })
    .getByRole("link", { name: /Next:/ })
    .click();
  await expect(page).toHaveURL(/\/lessons\/python-values(?:#.*)?$/);
  await page
    .getByRole("region", { name: "Words in this lesson", exact: true })
    .getByRole("link", { name: "None", exact: true })
    .click();
  await expect(page).toHaveURL(/\/glossary#none$/);
  await expect(page.locator("#none")).toBeFocused();
  await page.getByLabel("Find a term", { exact: true }).fill("idempotency key");
  await expect(page.getByRole("status")).toContainText(
    "Showing 1 of 390 terms",
  );
  await page
    .getByRole("link", {
      name: "When the response never arrives →",
      exact: true,
    })
    .click();
  await expect(page).toHaveURL(/\/lessons\/http-idempotency#lesson-glossary$/);
  await expect(
    page.getByRole("heading", { name: "Words in this lesson", exact: true }),
  ).toBeFocused();
});

test("checkpoint request failure preserves the selected answer; keyboard and glossary empty states work", async ({
  page,
}) => {
  await register(page);
  await page.goto("/lessons/python-values");
  const prediction = page.getByRole("article", {
    name: "Predict before checking",
    exact: true,
  });
  const radio = prediction.getByRole("radio", { name: "12", exact: true });
  await radio.check();
  await page.route(
    "**/api/lesson-activities/*/checkpoints/*/attempts",
    (route) =>
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Checkpoint save failed." }),
      }),
  );
  await prediction
    .getByRole("button", { name: "Check my answer", exact: true })
    .click();
  await expect(prediction.getByRole("alert")).toContainText(
    "Checkpoint save failed",
  );
  await expect(radio).toBeChecked();
  await expect(
    prediction.getByRole("button", { name: "Check my answer", exact: true }),
  ).toBeEnabled();
  expect(
    (
      await (
        await page.request.get("/api/lesson-activities/python-values")
      ).json()
    ).history,
  ).toEqual([]);
  await page.unroute("**/api/lesson-activities/*/checkpoints/*/attempts");
  await prediction
    .getByRole("button", { name: "Check my answer", exact: true })
    .focus();
  await page.keyboard.press("Enter");
  await expect(prediction.getByRole("status")).toContainText(
    "That matches the checkpoint",
  );
  expect(
    (
      await (
        await page.request.get("/api/lesson-activities/python-values")
      ).json()
    ).history,
  ).toHaveLength(1);
  await prediction
    .getByRole("button", { name: "Try this checkpoint again", exact: true })
    .click();
  await prediction.getByRole("radio").first().focus();
  await page.keyboard.press("ArrowRight");
  await expect(prediction.getByRole("radio").nth(1)).toBeFocused();
  await expect(prediction.getByRole("radio").nth(1)).toBeChecked();
  await page.goto("/glossary");
  await page
    .getByLabel("Find a term", { exact: true })
    .fill("not-a-real-glossary-term");
  await expect(
    page.getByText("No matching term.", { exact: true }),
  ).toBeVisible();
  await page
    .getByLabel("Find a term", { exact: true })
    .fill("Virtual environment");
  await expect(page.getByRole("status")).toContainText(
    "Showing 1 of 390 terms",
  );
  await page
    .getByRole("button", { name: "Switch to dark theme", exact: true })
    .click();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/glossary-mobile-dark.png",
    fullPage: true,
  });
  await page.keyboard.press("Control+k");
  const search = page.getByRole("dialog", { name: "Search academy" });
  await search
    .getByRole("textbox", { name: "Search query" })
    .fill("idempotency key");
  await search
    .getByRole("link")
    .filter({ hasText: "Glossary" })
    .filter({ hasText: "Idempotency key" })
    .click();
  await expect(page).toHaveURL(/\/glossary#idempotency-key$/);
  await expect(page.getByLabel("Find a term", { exact: true })).toHaveValue("");
  await expect(page.locator("#idempotency-key")).toBeFocused();
});
