import { test, expect } from "@playwright/test";

test("Scoped retrieval connects identity, access, rankings and honest finite metrics", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Retrieval Learner");
  await page
    .getByLabel("Email address")
    .fill(`retrieval-${Date.now()}@example.com`);
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
    page.getByRole("heading", { name: "Welcome aboard, Retrieval." }),
  ).toBeVisible();
  await page.goto("/lessons/embedding-retrieval");
  await page
    .getByRole("navigation", { name: "Lesson navigation" })
    .getByRole("link", { name: /Next:/ })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Keep chunks connected to their source",
      exact: true,
      level: 1,
    }),
  ).toBeVisible();
  const prediction = page.getByRole("article", {
    name: "Predict before checking",
    exact: true,
  });
  await prediction.getByRole("radio", { name: "1", exact: true }).check();
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
    .getByRole("link", { name: "Complete chunk key", exact: true })
    .click();
  await expect(page).toHaveURL(/\/glossary#retrieval-chunk-key$/);
  await expect(page.locator("#retrieval-chunk-key")).toBeFocused();
  await page.goto("/lessons/retrieval-chunk-identities");
  for (const title of [
    "Match vector model, version and dimensions",
    "Check access before scoring or taking top results",
    "Compare exact vector ranking with a keyword baseline",
    "Name the denominator before reporting retrieval quality",
    "Review retrieval evidence without inventing model quality",
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
    "/api/recall/topics/retrieval-metric-denominators/sessions",
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
        name: "Scoped retrieval & measured ranking",
        exact: true,
      })
      .locator("a.lesson-row"),
  ).toHaveCount(6);
  await page.goto("/projects#retrieval");
  const project = page.getByRole("article", {
    name: "Scoped retrieval lab",
    exact: true,
  });
  const downloading = page.waitForEvent("download");
  await project
    .getByRole("link", { name: "Download starter and tests", exact: true })
    .click();
  const download = await downloading;
  expect(download.suggestedFilename()).toBe("retrieval-starter.zip");
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
    path: "test-results/retrieval-project-mobile.png",
  });
  await project
    .getByRole("link", { name: "Submit work and view feedback", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Start submission draft", exact: true })
    .click();
  await expect(
    page
      .getByText("Source identity & window contract", { exact: true })
      .first(),
  ).toBeVisible();
  await page
    .getByLabel("Design explanation", { exact: true })
    .fill(
      "Fixture design note: exact Unicode windows preserve full tenant/document/revision/ordinal keys, offsets and digests. Latest revisions precede trusted tenant/group/metadata filters and scoring. Compatible finite vectors and deterministic ties support exact cosine and a simple keyword baseline. Requested-k precision, labelled recall and first-relevant rank keep no-label cases separate. Installed JSON and an original regression remain reported/manual evidence; hand-supplied development vectors do not prove model quality or mastery.",
    );
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Draft saved" }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("textbox", { name: "Design explanation", exact: true }),
  ).toHaveValue(
    "Fixture design note: exact Unicode windows preserve full tenant/document/revision/ordinal keys, offsets and digests. Latest revisions precede trusted tenant/group/metadata filters and scoring. Compatible finite vectors and deterministic ties support exact cosine and a simple keyword baseline. Requested-k precision, labelled recall and first-relevant rank keep no-label cases separate. Installed JSON and an original regression remain reported/manual evidence; hand-supplied development vectors do not prove model quality or mastery.",
  );
  expect(
    (await (await page.request.get("/api/dashboard")).json()).mastery,
  ).toBe(0);
});
