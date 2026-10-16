import { test, expect } from "@playwright/test";

test("Tool practice connects strict proposals, current exact approval, stable replay and bounded effects", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Tools Learner");
  await page
    .getByLabel("Email address")
    .fill(`tools-${Date.now()}@example.com`);
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
    page.getByRole("heading", { name: "Welcome aboard, Tools." }),
  ).toBeVisible();
  await page.goto("/lessons/tool-boundaries");
  await page
    .getByRole("navigation", { name: "Lesson navigation" })
    .getByRole("link", { name: /Next:/ })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Validate tool proposals without granting authority",
      exact: true,
      level: 1,
    }),
  ).toBeVisible();
  const prediction = page.getByRole("article", {
    name: "Predict before checking",
    exact: true,
  });
  await prediction.getByRole("radio", { name: "False", exact: true }).check();
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
    .getByRole("link", { name: "Tool proposal", exact: true })
    .click();
  await expect(page).toHaveURL(/\/glossary#tools-proposal$/);
  await expect(page.locator("#tools-proposal")).toBeFocused();
  await page.goto("/lessons/tools-proposal-boundaries");
  for (const title of [
    "Approve one exact application-owned action",
    "Refresh source access before using a tool",
    "Replay a stable application operation",
    "Bound the whole tool loop and preserve uncertainty",
    "Review installed tool evidence and an original regression",
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
    "/api/recall/topics/tools-loop-budgets/sessions",
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
        name: "Authorized actions & stable replay",
        exact: true,
      })
      .locator("a.lesson-row"),
  ).toHaveCount(6);
  await page.goto("/projects#tools");
  const project = page.getByRole("article", {
    name: "Authorized local tools lab",
    exact: true,
  });
  const downloading = page.waitForEvent("download");
  await project
    .getByRole("link", { name: "Download starter and tests", exact: true })
    .click();
  const download = await downloading;
  expect(download.suggestedFilename()).toBe("tools-starter.zip");
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
    path: "test-results/tools-project-mobile.png",
  });
  await project
    .getByRole("link", { name: "Submit work and view feedback", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Start submission draft", exact: true })
    .click();
  await expect(
    page
      .getByText("Strict proposal & dispatch boundaries", { exact: true })
      .first(),
  ).toBeVisible();
  await page
    .getByLabel("Design explanation", { exact: true })
    .fill(
      "Fixture design note: strict bounded proposals cannot grant authority. The application refreshes actor/principal/source access and binds approval to one exact canonical note action. A stable application operation ID survives regenerated model call IDs. One local SQLite transaction commits note and receipt; same actions replay and changed actions conflict. One shared deadline and finite context/cost/step limits stop the loop. Timeout or cancellation after commit preserves an uncertain effect for explicit receipt reconciliation. Installed JSON and an original regression remain reported/manual evidence, not distributed exactly-once, model quality or mastery.",
    );
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Draft saved" }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("textbox", { name: "Design explanation", exact: true }),
  ).toHaveValue(
    "Fixture design note: strict bounded proposals cannot grant authority. The application refreshes actor/principal/source access and binds approval to one exact canonical note action. A stable application operation ID survives regenerated model call IDs. One local SQLite transaction commits note and receipt; same actions replay and changed actions conflict. One shared deadline and finite context/cost/step limits stop the loop. Timeout or cancellation after commit preserves an uncertain effect for explicit receipt reconciliation. Installed JSON and an original regression remain reported/manual evidence, not distributed exactly-once, model quality or mastery.",
  );
  expect(
    (await (await page.request.get("/api/dashboard")).json()).mastery,
  ).toBe(0);
});
