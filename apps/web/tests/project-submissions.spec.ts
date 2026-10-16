import { test, expect, type Page } from "@playwright/test";

async function register(page: Page, email: string, name: string) {
  await page.goto("/login");
  await page.getByLabel("Your name").fill(name);
  await page.getByLabel("Email address").fill(email);
  await page
    .getByLabel("Password", { exact: true })
    .fill("a-long-browser-test-passphrase");
  await page.getByRole("button", { name: "Create workspace" }).click();
  await expect(
    page.getByRole("heading", { name: `Welcome aboard, ${name}.` }),
  ).toBeVisible();
}

async function fillArtifact(page: Page) {
  await page
    .getByLabel("Repository URL", { exact: true })
    .fill("https://github.com/learner/expenses");
  await page
    .getByLabel("Revision reference", { exact: true })
    .fill("abc123fixed");
  await page
    .getByLabel("Design explanation", { exact: true })
    .fill(
      "Amounts are represented as integer cents. The CSV boundary owns its input file.",
    );
  await page
    .getByLabel("Implementation evidence", { exact: true })
    .fill(
      "expenses.py validates rows; regression tests cover excess precision, invalid CSV and repeated calls.",
    );
  await page
    .getByLabel("Local test result", { exact: true })
    .selectOption("passed");
  await page
    .getByLabel("Test command", { exact: true })
    .fill("python -m unittest discover -s tests -v");
  await page
    .getByLabel("Test output", { exact: true })
    .fill("Ran 16 tests in 0.1s\nOK");
}

async function fillReview(page: Page, score: string, summary: string) {
  const form = page.getByRole("form", {
    name: /Add a self-review|Review this submission/,
  });
  for (const title of [
    "Exact amounts",
    "Validated summaries",
    "Files and command behavior",
    "Tests and explanation",
  ]) {
    await form
      .getByLabel(`Rating for ${title}`, { exact: true })
      .selectOption(score);
    await form
      .getByLabel(`Evidence for ${title}`, { exact: true })
      .fill(
        "Inspected the exact commit and the regression cases for this behavior.",
      );
  }
  await form.getByLabel("Review summary", { exact: true }).fill(summary);
  await form
    .getByLabel("Next actions", { exact: true })
    .fill(
      "Add the missing invalid-CSV regression and explain why the file always closes.",
    );
  await form
    .getByRole("button", { name: "Record feedback", exact: true })
    .click();
  await expect(form).not.toBeVisible();
}

test("submit fixed work, receive human feedback and retain prior versions after revision", async ({
  page,
  browser,
}) => {
  const stamp = Date.now();
  const reviewerContext = await browser.newContext({
    baseURL: process.env.E2E_BASE_URL || "http://127.0.0.1:3000",
  });
  const reviewer = await reviewerContext.newPage();
  try {
    await register(reviewer, `reviewer-${stamp}@example.com`, "Reviewer");
    await register(page, `submitter-${stamp}@example.com`, "Submitter");
    await page
      .getByRole("link", { name: "Portfolio projects", exact: true })
      .click();
    await page
      .getByRole("article", { name: "Expense tracker CLI", exact: true })
      .getByRole("link", { name: "Submit work and view feedback" })
      .click();
    await page
      .getByRole("button", { name: "Start submission draft", exact: true })
      .click();
    await fillArtifact(page);
    await page.getByRole("button", { name: "Save draft", exact: true }).click();
    await expect(
      page.getByRole("status").filter({ hasText: "Draft saved" }),
    ).toBeVisible();
    await page.reload();
    await expect(
      page.getByLabel("Revision reference", { exact: true }),
    ).toHaveValue("abc123fixed");
    const history = await (
      await page.request.get("/api/projects/python-expenses/submissions")
    ).json();
    const id = history.submissions[0].id;
    expect(
      (await reviewer.request.get(`/api/project-submissions/${id}`)).status(),
    ).toBe(404);
    await page
      .getByRole("button", { name: "Save and submit for review" })
      .click();
    const evidence = page.getByRole("region", {
      name: "Submitted implementation",
    });
    await expect(evidence).toContainText("abc123fixed");
    await expect(evidence).toContainText("learner-reported");
    await fillReview(
      page,
      "1",
      "My implementation needs a stronger CSV failure regression before I can defend it.",
    );
    await page
      .getByLabel("Reviewer account email", { exact: true })
      .fill(`reviewer-${stamp}@example.com`);
    await page
      .getByRole("button", { name: "Invite reviewer", exact: true })
      .click();
    await expect(
      page.getByRole("region", { name: "Reviewer access" }),
    ).toContainText("Access granted");
    await reviewer
      .getByRole("link", { name: "Review workspace", exact: true })
      .click();
    await reviewer.getByRole("link", { name: /Expense tracker CLI/ }).click();
    await expect(
      reviewer.getByRole("region", { name: "Submitted implementation" }),
    ).toContainText("abc123fixed");
    await fillReview(
      reviewer,
      "1",
      "Most behavior works, but the invalid CSV regression is missing from this exact commit.",
    );
    await page.reload();
    const feedback = page.getByRole("region", { name: "Recorded feedback" });
    await expect(feedback).toContainText("Self-review · Submitter");
    await expect(feedback).toContainText("Human review · Reviewer");
    await page
      .getByRole("button", { name: "Start next revision", exact: true })
      .click();
    await expect(
      page.getByLabel("Revision reference", { exact: true }),
    ).toHaveValue("abc123fixed");
    await page
      .getByLabel("Revision reference", { exact: true })
      .fill("def456fixed");
    await page
      .getByLabel("What changed since the previous version", { exact: true })
      .fill(
        "Added the requested invalid CSV regression and documented file ownership.",
      );
    await page
      .getByRole("button", { name: "Save and submit for review" })
      .click();
    await expect(
      page.getByRole("region", { name: "Submitted implementation" }),
    ).toContainText("def456fixed");
    await expect(
      page.getByRole("region", { name: "Recorded feedback" }),
    ).toContainText("No feedback yet");
    const revised = await (
      await page.request.get("/api/projects/python-expenses/submissions")
    ).json();
    expect(revised.submissions[0].assignments).toEqual([]);
    expect(
      (
        await reviewer.request.get(
          `/api/project-submissions/${revised.submissions[0].id}`,
        )
      ).status(),
    ).toBe(404);
    await page.getByRole("button", { name: /Version 1 · Submitted/ }).click();
    await expect(
      page.getByRole("region", { name: "Submitted implementation" }),
    ).toContainText("abc123fixed");
    await expect(
      page.getByRole("region", { name: "Recorded feedback" }),
    ).toContainText("Human review · Reviewer");
    await page
      .getByRole("button", {
        name: `Remove access for reviewer-${stamp}@example.com`,
      })
      .click();
    await expect(
      page.getByRole("region", { name: "Reviewer access" }),
    ).toContainText("Access removed");
    expect(
      (await reviewer.request.get(`/api/project-submissions/${id}`)).status(),
    ).toBe(404);
    await page.reload();
    await page.getByRole("button", { name: /Version 1 · Submitted/ }).click();
    await expect(
      page.getByRole("region", { name: "Recorded feedback" }),
    ).toContainText("Human review · Reviewer");
    expect(
      (await (await page.request.get("/api/dashboard")).json()).mastery,
    ).toBe(0);
    await page.screenshot({
      path: "test-results/project-submission-desktop.png",
      fullPage: true,
    });
    await page.setViewportSize({ width: 390, height: 844 });
    await page
      .getByRole("heading", { name: "Feedback for version 1", exact: true })
      .click();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    await page
      .getByRole("region", { name: "Recorded feedback" })
      .screenshot({ path: "test-results/project-feedback-mobile.png" });
  } finally {
    await reviewerContext.close();
  }
});

test("draft save failure preserves input and incomplete submission can be corrected", async ({
  page,
}) => {
  await register(page, `draft-retry-${Date.now()}@example.com`, "Retry");
  await page.goto("/projects/python-expenses");
  await page
    .getByRole("button", { name: "Start submission draft", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Save and submit for review" })
    .click();
  await expect(
    page.getByRole("alert").filter({ hasText: "Add a repository URL" }),
  ).toBeVisible();
  await fillArtifact(page);
  await page.route("**/api/project-submissions/*", async (route) => {
    if (route.request().method() === "PUT")
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Draft save failed for this test." }),
      });
    else await route.continue();
  });
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(
    page.getByRole("alert").filter({ hasText: "Draft save failed" }),
  ).toBeVisible();
  await expect(
    page.getByLabel("Revision reference", { exact: true }),
  ).toHaveValue("abc123fixed");
  await page.unroute("**/api/project-submissions/*");
  await page
    .getByRole("button", { name: "Save and submit for review" })
    .click();
  await expect(
    page.getByRole("region", { name: "Submitted implementation" }),
  ).toContainText("abc123fixed");
  await page.reload();
  await expect(
    page.getByRole("region", { name: "Submitted implementation" }),
  ).toContainText("abc123fixed");
});
