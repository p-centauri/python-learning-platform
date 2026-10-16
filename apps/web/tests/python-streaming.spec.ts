import { test, expect } from "@playwright/test";

test("continue protocols into generators and the streaming log project", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Streaming Learner");
  await page
    .getByLabel("Email address")
    .fill(`streaming-${Date.now()}@example.com`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("a-long-browser-test-passphrase");
  await page.getByRole("button", { name: "Create workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome aboard, Streaming." }),
  ).toBeVisible();
  await page.goto("/lessons/python-protocols");
  await page
    .getByRole("link", { name: "generators and resource cleanup" })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Iterables, iterators & one-pass input",
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Mark reading complete" }).click();
  await expect(
    page.getByRole("button", { name: "Reading completed" }),
  ).toBeDisabled();
  await page.getByRole("link", { name: /The second pass is empty/ }).click();
  await page
    .getByRole("radio", {
      name: "B An empty list",
      exact: true,
    })
    .check();
  await page.getByRole("button", { name: "Submit answer" }).click();
  await expect(page.getByText("Well reasoned.")).toBeVisible();
  await page.goto("/lessons/python-iterators");
  for (const name of [
    "Next: generators and deferred work",
    "Next: streaming pipelines and limits",
    "Next: exceptions with useful context",
    "Next: context managers and the streaming lab",
  ]) {
    await page.getByRole("link", { name, exact: true }).click();
    await expect(
      page.getByRole("heading", { name: "Guided practice" }),
    ).toBeVisible();
  }
  await expect(
    page.getByRole("heading", {
      name: "Context managers & the streaming log lab",
    }),
  ).toBeVisible();
  const pending = page.waitForEvent("download");
  await page
    .getByRole("link", { name: "Download the streaming service-log lab" })
    .click();
  const download = await pending;
  expect(download.suggestedFilename()).toBe("log-stream-starter.zip");
  expect(await download.failure()).toBeNull();
  await page
    .getByRole("link", { name: "project checklist", exact: true })
    .click();
  const project = page.getByRole("article", {
    name: "Streaming service-log lab",
    exact: true,
  });
  await project.getByRole("checkbox").first().check();
  await expect(project.getByText("1/4 milestones")).toBeVisible();
  await page.reload();
  await expect(project.getByRole("checkbox").first()).toBeChecked();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/learn");
  const module = page.getByRole("region", {
    name: "Python generators & resource cleanup",
    exact: true,
  });
  await expect(module.locator("a.lesson-row")).toHaveCount(5);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
  ).toBe(false);
  await module.screenshot({ path: "test-results/python-streaming-mobile.png" });
});
