import { readFileSync } from "node:fs";
import { test, expect, type Page } from "@playwright/test";

async function register(page: Page, suffix: string) {
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Planner Learner");
  await page
    .getByLabel("Email address")
    .fill(`plan-${suffix}-${Date.now()}@example.com`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("a-long-browser-test-passphrase");
  await page.getByRole("button", { name: "Create workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome aboard, Planner." }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Create my learning plan", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Your personal learning plan",
      exact: true,
    }),
  ).toBeVisible();
}

test("save and edit a personal plan, continue into practice and retain progress", async ({
  page,
}) => {
  await register(page, "journey");
  await page.getByRole("radio", { name: /Build Python confidence/ }).check();
  await page.getByLabel("Weekly study hours").fill("1");
  await page
    .getByRole("button", { name: "Create my plan", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Plan saved");
  const queue = page.getByRole("region", { name: "Weekly study queue" });
  await expect(queue.locator("li").first()).toContainText("Run Python in your own workspace");
  const response = await page.request.get("/api/learning-plan");
  const initial = await response.json();
  expect(initial.plan.scheduled_minutes).toBeLessThanOrEqual(60);
  await page.reload();
  await expect(
    page.getByRole("radio", { name: /Build Python confidence/ }),
  ).toBeChecked();
  await expect(page.getByLabel("Weekly study hours")).toHaveValue("1");
  await page
    .getByRole("link", { name: "Start next action", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Mark reading complete", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Reading completed" }),
  ).toBeDisabled();
  await page
    .getByRole("link", { name: "My learning plan", exact: true })
    .click();
  await expect(queue.locator("li").first()).toContainText("Practise");
  await page.getByRole("radio", { name: /Build applied AI systems/ }).check();
  await page.getByLabel("Weekly study hours").fill("3");
  await page.getByLabel("Starting approach").selectOption("from-start");
  await page.getByRole("button", { name: "Save changes", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Plan saved");
  await page.getByRole("button", { name: "Refresh recommendations" }).click();
  await expect(
    page.getByRole("region", { name: "Your plan summary" }),
  ).toContainText("3 hours available");
  await page.getByRole("link", { name: "Overview", exact: true }).click();
  const overview = page.getByRole("region", {
    name: "Personal learning plan",
    exact: true,
  });
  await expect(overview).toContainText("Build applied AI systems");
  await expect(
    overview.getByRole("link", { name: "Start next action" }),
  ).toHaveAttribute("href", /^\/practice\//);
  await page.getByRole("link", { name: "View or edit my plan" }).click();
  await page.screenshot({
    path: "test-results/learning-plan-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
  ).toBe(false);
  await page
    .getByRole("form", { name: "Learning preferences" })
    .screenshot({ path: "test-results/learning-plan-mobile.png" });
});

test("failed preference save keeps the saved plan and allows a retry", async ({
  page,
}) => {
  await register(page, "failure");
  await page
    .getByRole("button", { name: "Create my plan", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Plan saved");
  await page.getByLabel("Weekly study hours").fill("5");
  await page.route("**/api/learning-plan", async (route) => {
    if (route.request().method() === "PUT")
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Unable to save test plan." }),
      });
    else await route.continue();
  });
  await page.getByRole("button", { name: "Save changes", exact: true }).click();
  await expect(
    page.getByRole("alert").filter({ hasText: "Unable to save test plan." }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Your plan summary" }),
  ).toContainText("3 hours available");
  await page.unroute("**/api/learning-plan");
  await page.getByRole("button", { name: "Save changes", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Your plan summary" }),
  ).toContainText("5 hours available");
  await page.reload();
  await expect(page.getByLabel("Weekly study hours")).toHaveValue("5");
});

test("submitted assessment informs entry point and the learner can choose the beginning", async ({
  page,
}) => {
  await register(page, "assessment");
  const headers = { "X-Academy-Request": "1" };
  const started = await page.request.post("/api/exams/start", {
    headers,
    data: { exam_id: "python-beginner-v1" },
  });
  expect(started.status()).toBe(201);
  const attempt = await started.json();
  const bank = JSON.parse(
    readFileSync("../../content/assessments/python-beginner-v1.json", "utf8"),
  ) as { questions: { id: string; answer: number; options: string[] }[] };
  for (const question of bank.questions) {
    const saved = await page.request.put(
      `/api/exams/attempts/${attempt.id}/answer`,
      {
        headers,
        data: {
          question_id: question.id,
          answer: (question.answer + 1) % question.options.length,
        },
      },
    );
    expect(saved.ok()).toBeTruthy();
  }
  const submitted = await page.request.post(
    `/api/exams/attempts/${attempt.id}/submit`,
    { headers },
  );
  expect(submitted.ok()).toBeTruthy();
  await page
    .getByRole("button", { name: "Create my plan", exact: true })
    .click();
  const start = page.getByRole("region", {
    name: "Recommended starting point",
  });
  await expect(start).toContainText("0/4");
  await expect(start.getByRole("link").first()).toHaveAttribute(
    "href",
    "/lessons/python-values",
  );
  await page.getByLabel("Starting approach").selectOption("from-start");
  await page.getByRole("button", { name: "Save changes", exact: true }).click();
  await expect(start.getByRole("link").first()).toHaveAttribute(
    "href",
    "/lessons/python-start",
  );
});
