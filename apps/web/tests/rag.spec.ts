import { test, expect } from "@playwright/test";

test("RAG connects document lifecycle, scoped context, citations and fresh authority", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Evidence Learner");
  await page.getByLabel("Email address").fill(`rag-${Date.now()}@example.com`);
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
    page.getByRole("heading", { name: "Welcome aboard, Evidence." }),
  ).toBeVisible();
  await page.goto("/lessons/rag-evidence");
  await page
    .getByRole("navigation", { name: "Lesson navigation" })
    .getByRole("link", { name: /Next:/ })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Publish document updates and retain deletion markers",
      exact: true,
      level: 1,
    }),
  ).toBeVisible();
  const prediction = page.getByRole("article", {
    name: "Predict before checking",
    exact: true,
  });
  await prediction.getByRole("radio", { name: "True", exact: true }).check();
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
    .getByRole("link", { name: "Deletion marker", exact: true })
    .click();
  await expect(page).toHaveURL(/\/glossary#rag-deletion-marker$/);
  await expect(page.locator("#rag-deletion-marker")).toBeFocused();
  await page.goto("/lessons/rag-source-lifecycle");
  for (const title of [
    "Select and pack whole authorized evidence",
    "Bind citations to selected source excerpts",
    "Abstain when evidence or generation is unusable",
    "Refresh permissions and sources after generation",
    "Review RAG evidence with honest quality limits",
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
    "/api/recall/topics/rag-fresh-permissions/sessions",
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
        name: "Document lifecycle & evidence answers",
        exact: true,
      })
      .locator("a.lesson-row"),
  ).toHaveCount(6);
  await page.goto("/projects#rag");
  const project = page.getByRole("article", {
    name: "Evidence answering lab",
    exact: true,
  });
  const downloading = page.waitForEvent("download");
  await project
    .getByRole("link", { name: "Download starter and tests", exact: true })
    .click();
  const download = await downloading;
  expect(download.suggestedFilename()).toBe("rag-starter.zip");
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
    path: "test-results/rag-project-mobile.png",
  });
  await project
    .getByRole("link", { name: "Submit work and view feedback", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Start submission draft", exact: true })
    .click();
  await expect(
    page
      .getByText("Document revisions & deletion lifecycle", { exact: true })
      .first(),
  ).toBeVisible();
  await page
    .getByLabel("Design explanation", { exact: true })
    .fill(
      "Fixture design note: atomic complete document revisions and retained deletion markers preserve source lifecycle. Scoped candidates, an explicitly limited task-term gate, keyword reranking and whole UTF-8 evidence budgets produce a pinned context. One configured controlled call can propose only selected whole excerpts. Current application authority and source state are refreshed before visible citations; missing or changed evidence causes abstention. Installed JSON and an original regression remain reported/manual evidence, not source truth, real model quality or mastery.",
    );
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Draft saved" }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("textbox", { name: "Design explanation", exact: true }),
  ).toHaveValue(
    "Fixture design note: atomic complete document revisions and retained deletion markers preserve source lifecycle. Scoped candidates, an explicitly limited task-term gate, keyword reranking and whole UTF-8 evidence budgets produce a pinned context. One configured controlled call can propose only selected whole excerpts. Current application authority and source state are refreshed before visible citations; missing or changed evidence causes abstention. Installed JSON and an original regression remain reported/manual evidence, not source truth, real model quality or mastery.",
  );
  expect(
    (await (await page.request.get("/api/dashboard")).json()).mastery,
  ).toBe(0);
});
