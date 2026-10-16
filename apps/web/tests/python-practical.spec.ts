import { test, expect } from "@playwright/test";

test("continue foundations into text/time lessons and the repair lab", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Practical Learner");
  await page
    .getByLabel("Email address")
    .fill(`practical-${Date.now()}@example.com`);
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
    page.getByRole("heading", { name: "Welcome aboard, Practical." }),
  ).toBeVisible();
  await page.goto("/lessons/python-tests");
  await page
    .getByRole("link", { name: "Continue: text, time and debugging" })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Text, bytes & Unicode without surprises",
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Mark reading complete" }).click();
  await expect(
    page.getByRole("button", { name: "Reading completed" }),
  ).toBeDisabled();
  await page
    .getByRole("link", { name: /Two lengths for the same name/ })
    .click();
  await page.getByRole("radio", { name: "B 4 and 5", exact: true }).check();
  await page.getByRole("button", { name: "Submit answer" }).click();
  await expect(page.getByText("Well reasoned.")).toBeVisible();
  await page.goto("/lessons/python-text-bytes");
  for (const name of [
    "Next: collection patterns",
    "Next: dates and timestamp input",
    "Next: time zones and elapsed time",
    "Next: debugging and the repair lab",
  ]) {
    await page.getByRole("link", { name, exact: true }).click();
    await expect(
      page.getByRole("heading", { name: "Guided practice" }),
    ).toBeVisible();
  }
  await expect(
    page.getByRole("heading", { name: "Debug a broken event timeline" }),
  ).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await page
    .getByRole("link", { name: "Download the event-timeline repair lab" })
    .click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("event-timeline-starter.zip");
  expect(await download.failure()).toBeNull();
  await page
    .getByRole("link", { name: "project checklist", exact: true })
    .click();
  const project = page.getByRole("article", {
    name: "Event timeline repair lab",
  });
  await project.getByRole("checkbox").first().check();
  await expect(project.getByText("1/4 milestones")).toBeVisible();
  await page.reload();
  await expect(project.getByRole("checkbox").first()).toBeChecked();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/learn");
  const module = page.getByRole("region", {
    name: "Python in practice: text, time & debugging",
  });
  await expect(module.locator("a.lesson-row")).toHaveCount(5);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
  ).toBe(false);
  await module.screenshot({ path: "test-results/python-practical-mobile.png" });
});
