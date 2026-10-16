import { test, expect, type Page } from "@playwright/test";
import { execFileSync } from "node:child_process";
import path from "node:path";
async function register(page: Page, email: string) {
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Recall Learner");
  await page.getByLabel("Email address").fill(email);
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
    // The expanded suite can reach the real per-IP signup limit. Respect it;
    // do not weaken auth or add a test-only API bypass.
    test.setTimeout(120000);
    const seconds = Number(registration.headers()["retry-after"] || "60");
    await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
    registration = await create();
  }
  expect(registration.status()).toBe(201);
  await expect(
    page.getByRole("heading", { name: "Welcome aboard, Recall." }),
  ).toBeVisible();
}

test("recurring mistakes lead to a fresh delayed short-answer check and fixed feedback", async ({
  page,
}) => {
  const email = `recall-e2e-aged-${Date.now()}@example.com`;
  await register(page, email);
  await page.goto("/practice/python-values-check-1");
  await page.getByRole("radio").nth(0).check();
  const first = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/exercises/python-values-check-1/attempts") &&
      r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Submit answer", exact: true })
    .click();
  expect((await (await first).json()).score).toBe(0);
  const second = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/exercises/python-values-check-1/attempts") &&
      r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Submit answer", exact: true })
    .click();
  expect((await (await second).json()).score).toBe(0);
  // Only this newly registered test account is aged; no test clock endpoint exists.
  execFileSync(path.resolve("../../.venv/bin/python"), [
    path.resolve("tests/fixtures/age_review_source.py"),
    email,
  ]);
  await page
    .getByRole("link", { name: "Try a different short-answer question" })
    .click();
  await expect(
    page.getByRole("region", { name: "Topic evidence" }),
  ).toContainText("Repeated errors recorded");
  await expect(
    page.getByRole("region", { name: "Topic evidence" }),
  ).toContainText("2 incorrect scenario answers across 1 question");
  const before = await (await page.request.get("/api/dashboard")).json();
  await expect(
    page.getByRole("button", { name: "Start delayed check" }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "Start delayed check" }).click();
  const answer = page.getByLabel("Your short answer", { exact: true });
  await expect(answer).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/retention-check-mobile.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 1280, height: 720 });
  await answer.fill("63");
  const id = page.url().split("/").pop();
  const active = await (
    await page.request.get(`/api/recall/sessions/${id}`)
  ).json();
  expect(active.result).toBeNull();
  for (const field of [
    "accepted",
    "explanation",
    "validation",
    "definition_snapshot",
    "options",
  ])
    expect(JSON.stringify(active)).not.toContain(`"${field}"`);
  await page.getByRole("button", { name: "Save answer", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Answer saved");
  await page.reload();
  await expect(answer).toHaveValue("63");
  await page.getByRole("button", { name: "Submit check", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Check feedback" }),
  ).toContainText("Correct short answer");
  await expect(
    page.getByRole("region", { name: "Check feedback" }),
  ).toContainText("Delayed check · unseen question");
  await expect(answer).toBeDisabled();
  await page.reload();
  await expect(
    page.getByRole("region", { name: "Check feedback" }),
  ).toContainText("Expected: 63");
  const done = await (
    await page.request.get(`/api/recall/sessions/${id}`)
  ).json();
  expect(done.result.evidence_kind).toBe("fresh-delayed");
  expect(
    (await (await page.request.get("/api/dashboard")).json()).mastery,
  ).toBe(before.mastery);
  await page.getByRole("link", { name: "Back to topic", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Start delayed check" }),
  ).toBeDisabled();
  await page.goto("/review");
  const evidence = page.getByRole("region", {
    name: "Separate review evidence",
  });
  await expect(evidence).toContainText("1/1 correct");
  await page.evaluate(() => {
    (document.activeElement as HTMLElement)?.blur();
    window.scrollTo(0, 0);
  });
  await page.screenshot({
    path: "test-results/retention-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page
    .getByRole("region", { name: "Mistake-focused topics" })
    .screenshot({ path: "test-results/retention-mobile.png" });
});

test("failed save retains input; immediate and assisted checks stay out of retention", async ({
  page,
}) => {
  await register(page, `recall-e2e-retry-${Date.now()}@example.com`);
  await page.goto("/review/python-values");
  await expect(
    page.getByRole("button", { name: "Start delayed check" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Practise now", exact: true }).click();
  const answer = page.getByLabel("Your short answer", { exact: true });
  await answer.fill("63");
  await page.route("**/api/recall/sessions/*", async (route) => {
    if (route.request().method() === "PUT")
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Save failed for this check." }),
      });
    else await route.continue();
  });
  await page.getByRole("button", { name: "Save answer", exact: true }).click();
  await expect(
    page.getByRole("alert").filter({ hasText: "Save failed" }),
  ).toBeVisible();
  await expect(answer).toHaveValue("63");
  await page.unroute("**/api/recall/sessions/*");
  await page.getByRole("button", { name: "Submit check", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Check feedback" }),
  ).toContainText("Immediate practice");
  await page.getByRole("link", { name: "Back to topic", exact: true }).click();
  await page.getByRole("button", { name: "Practise now", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Review question" }),
  ).toContainText("explicit zero");
  await answer.fill("0");
  await page
    .getByRole("checkbox", {
      name: "I used notes, hints, another answer or other help.",
    })
    .check();
  await page.getByRole("button", { name: "Submit check", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Check feedback" }),
  ).toContainText("Assisted practice");
  await page.getByRole("link", { name: "Back to topic", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Recall history" }),
  ).toContainText("Immediate practice");
  await expect(
    page.getByRole("region", { name: "Recall history" }),
  ).toContainText("Assisted practice");
  await page.getByRole("button", { name: "Practise now", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Review question" }),
  ).toContainText("Repeated question");
  await page.getByText("Leave this check", { exact: true }).click();
  await page
    .getByRole("button", { name: "Discard draft", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Draft discarded");
  const data = await (await page.request.get("/api/recall")).json();
  expect(data.summary.fresh_delayed).toEqual({ correct: 0, total: 0 });
  expect(data.summary.immediate).toEqual({ correct: 1, total: 1 });
  expect(data.summary.assisted).toEqual({ correct: 1, total: 1 });
  expect(
    (await (await page.request.get("/api/dashboard")).json()).mastery,
  ).toBe(0);
});
