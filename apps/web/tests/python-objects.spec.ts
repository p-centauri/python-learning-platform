import { test, expect } from "@playwright/test";

test("continue ownership into object design and the typed task inbox", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Inbox Learner");
  await page
    .getByLabel("Email address")
    .fill(`inbox-${Date.now()}@example.com`);
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
    page.getByRole("heading", { name: "Welcome aboard, Inbox." }),
  ).toBeVisible();
  await page.goto("/lessons/python-ownership");
  await page
    .getByRole("link", { name: "Continue: object design and typing" })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Classes, state & small interfaces",
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Mark reading complete" }).click();
  await expect(
    page.getByRole("button", { name: "Reading completed" }),
  ).toBeDisabled();
  await page.getByRole("link", { name: /Two inboxes share one list/ }).click();
  await page
    .getByRole("radio", {
      name: "B Both instances find the same class-owned list",
      exact: true,
    })
    .check();
  await page.getByRole("button", { name: "Submit answer" }).click();
  await expect(page.getByText("Well reasoned.")).toBeVisible();
  await page.goto("/lessons/python-classes");
  for (const name of [
    "Next: dataclasses and value objects",
    "Next: composition and small services",
    "Next: type hints and input validation",
    "Next: protocols and the task-inbox project",
  ]) {
    await page.getByRole("link", { name, exact: true }).click();
    await expect(
      page.getByRole("heading", { name: "Guided practice" }),
    ).toBeVisible();
  }
  await expect(
    page.getByRole("heading", {
      name: "Protocols, fakes & the typed task inbox",
    }),
  ).toBeVisible();
  const pending = page.waitForEvent("download");
  await page
    .getByRole("link", { name: "Download the typed task-inbox project" })
    .click();
  const download = await pending;
  expect(download.suggestedFilename()).toBe("task-inbox-starter.zip");
  expect(await download.failure()).toBeNull();
  await page
    .getByRole("link", { name: "project checklist", exact: true })
    .click();
  const project = page.getByRole("article", {
    name: "Typed task inbox",
    exact: true,
  });
  await project.getByRole("checkbox").first().check();
  await expect(project.getByText("1/4 milestones")).toBeVisible();
  await page.reload();
  await expect(project.getByRole("checkbox").first()).toBeChecked();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/learn");
  const module = page.getByRole("region", {
    name: "Python object design & typing",
    exact: true,
  });
  await expect(module.locator("a.lesson-row")).toHaveCount(5);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
  ).toBe(false);
  await module.screenshot({ path: "test-results/python-objects-mobile.png" });
});
