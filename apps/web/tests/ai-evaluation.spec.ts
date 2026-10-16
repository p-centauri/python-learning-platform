import { test, expect } from "@playwright/test";

test("AI release practice connects versioned cases, exact metrics, adversarial boundaries and separate review", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Release Learner");
  await page
    .getByLabel("Email address")
    .fill(`release-${Date.now()}@example.com`);
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
    page.getByRole("heading", { name: "Welcome aboard, Release." }),
  ).toBeVisible();
  await page.goto("/lessons/evaluation-gates");
  await page
    .getByRole("navigation", { name: "Lesson navigation" })
    .getByRole("link", { name: /Next:/ })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Freeze release cases and candidate versions",
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
    .getByRole("link", { name: "Dataset digest", exact: true })
    .click();
  await expect(page).toHaveURL(/\/glossary#ai-dataset-digest$/);
  await expect(page.locator("#ai-dataset-digest")).toBeFocused();
  await page.goto("/lessons/ai-release-cases");
  for (const title of [
    "Measure retrieval and answer contracts honestly",
    "Test adversarial instructions at policy boundaries",
    "Save useful traces without private source text",
    "Keep human quality review separate from exact support",
    "Review the installed release and connected learning path",
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
    "/api/recall/topics/ai-human-quality/sessions",
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
        name: "Controlled release evaluation & security",
        exact: true,
      })
      .locator("a.lesson-row"),
  ).toHaveCount(6);
  await page.goto("/projects#ai-evaluation");
  const project = page.getByRole("article", {
    name: "Controlled AI release evaluation lab",
    exact: true,
  });
  const downloading = page.waitForEvent("download");
  await project
    .getByRole("link", { name: "Download starter and tests", exact: true })
    .click();
  const download = await downloading;
  expect(download.suggestedFilename()).toBe("ai-evaluation-starter.zip");
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
    path: "test-results/ai-evaluation-project-mobile.png",
  });
  await project
    .getByRole("link", { name: "Submit work and view feedback", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Start submission draft", exact: true })
    .click();
  await expect(
    page
      .getByText("Versioned cases & current observations", { exact: true })
      .first(),
  ).toBeVisible();
  await page
    .getByLabel("Design explanation", { exact: true })
    .fill(
      "Fixture design note: versioned complete case identities and candidate/source/model/prompt digests make observations reproducible. Exact requested-k precision, positive recall/MRR and separate unlabelled unwanted hits preserve denominators. Expected answer/tool/effect contracts remain separate from permission/privacy failures. Role/URL/extra-field proposals and stale authority are tested at actual boundaries. A pinned objective gate cannot fill missing human review or override a rejection; ordinary and malicious quotations need explicit semantic judgment. Installed JSON and original regressions remain reported/manual evidence, not real model quality, production authority or mastery.",
    );
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Draft saved" }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("textbox", { name: "Design explanation", exact: true }),
  ).toHaveValue(
    "Fixture design note: versioned complete case identities and candidate/source/model/prompt digests make observations reproducible. Exact requested-k precision, positive recall/MRR and separate unlabelled unwanted hits preserve denominators. Expected answer/tool/effect contracts remain separate from permission/privacy failures. Role/URL/extra-field proposals and stale authority are tested at actual boundaries. A pinned objective gate cannot fill missing human review or override a rejection; ordinary and malicious quotations need explicit semantic judgment. Installed JSON and original regressions remain reported/manual evidence, not real model quality, production authority or mastery.",
  );
  expect(
    (await (await page.request.get("/api/dashboard")).json()).mastery,
  ).toBe(0);
});
