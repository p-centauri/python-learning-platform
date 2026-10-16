import { test, expect, type Page } from "@playwright/test";

test.setTimeout(180000);
async function signup(page: Page, name: string) {
  await page.goto("/login");
  await page.getByLabel("Your name").fill(name);
  await page
    .getByLabel("Email address")
    .fill(`portfolio-${name.toLowerCase()}-${Date.now()}@example.com`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("a-long-browser-test-passphrase");
  async function create() {
    const response = page.waitForResponse((r) =>
      r.url().endsWith("/api/auth/register"),
    );
    await page.getByRole("button", { name: "Create workspace" }).click();
    return response;
  }
  let response = await create();
  if (response.status() === 429) {
    await new Promise((r) =>
      setTimeout(r, Number(response.headers()["retry-after"] || "60") * 1000),
    );
    response = await create();
  }
  expect(response.status()).toBe(201);
  await expect(
    page.getByRole("heading", { name: `Welcome aboard, ${name}.` }),
  ).toBeVisible();
}
async function start(page: Page, title: string) {
  await page.goto("/exams");
  const waiting = page.waitForResponse((r) =>
    r.url().endsWith("/api/exams/start"),
  );
  await page
    .getByRole("region", { name: title, exact: true })
    .getByRole("button", { name: `Begin ${title}`, exact: true })
    .click();
  const row = await (await waiting).json();
  await expect(
    page.getByRole("heading", { name: title, exact: true }),
  ).toBeVisible();
  return row;
}
async function answer(page: Page, id: number, q: string, value: unknown) {
  const response = await page.request.put(`/api/exams/attempts/${id}/answer`, {
    headers: { "X-Academy-Request": "1" },
    data: { question_id: q, answer: value },
  });
  expect(response.ok()).toBeTruthy();
}
const TEXT =
  "Observed regression evidence identifies the exact boundary, expected behavior, command and remaining limitations.";

test("portfolio contracts and mixed knowledge answers save, resume and connect to fixed review", async ({
  page,
}) => {
  await signup(page, "Portfolio");
  for (const id of ["backend", "enterprise-rag", "finance"]) {
    await page.goto(`/projects/${id}`);
    await expect(
      page.getByRole("heading", { name: "Build the full portfolio product" }),
    ).toBeVisible();
    const download = page.waitForEvent("download");
    await page
      .getByRole("link", { name: "Download portfolio build pack" })
      .click();
    expect((await download).suggestedFilename()).toBe(`${id}.zip`);
    const brief = page.getByRole("region", {
      name: "Portfolio build contract",
    });
    await brief
      .getByText("Libraries and expected abilities", { exact: true })
      .scrollIntoViewIfNeeded();
    await expect(
      brief.getByText("Ordered milestones", { exact: true }),
    ).toBeVisible();
  }
  const row = await start(page, "Engineering knowledge exam");
  expect(row.questions).toHaveLength(48);
  expect(JSON.stringify(row)).not.toContain('"explanation"');
  expect(JSON.stringify(row)).not.toContain('"answer":');
  await page.getByRole("radio").first().check();
  await expect(
    page.getByRole("button", { name: "Flag for review" }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "Flag for review" }).click();
  await expect(
    page.getByRole("button", { name: "Remove review flag" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Question 3", exact: true }).click();
  await page.getByRole("checkbox").first().check();
  await expect(page.getByRole("checkbox").nth(1)).toBeEnabled();
  await page.getByRole("checkbox").nth(1).check();
  await expect(page.getByRole("checkbox").nth(1)).toBeChecked();
  await page.getByRole("button", { name: "Question 6", exact: true }).click();
  await page.getByLabel("Written response").fill(TEXT);
  await expect(page.getByRole("status")).toContainText("Saved to your account");
  await page.reload();
  await expect(page.getByLabel("Written response")).toHaveValue(TEXT);
  await expect(
    page.getByRole("button", { name: /Question 1, flagged, saved/ }),
  ).toBeVisible();
  for (const q of row.questions) {
    if (q.id === row.questions[5].id) continue;
    await answer(
      page,
      row.id,
      q.id,
      q.kind === "short" ? TEXT : q.kind === "multiple" ? [0, 1] : 0,
    );
  }
  await page.reload();
  await page
    .getByRole("button", { name: "Submit and freeze exam evidence" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Objective performance by category" }),
  ).toBeVisible();
  await expect(
    page.getByText("8 written responses saved for review.", { exact: false }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Open fixed evidence and request review" })
    .click();
  await expect(
    page.getByRole("heading", { name: /Fixed exam attachment/ }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Invite a human reviewer" }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
  ).toBe(false);
  await page.screenshot({
    path: "test-results/portfolio-knowledge-mobile.png",
    fullPage: true,
  });
});

test("senior design reveals each incident only after committing and keeps earlier responses fixed", async ({
  page,
}) => {
  await signup(page, "Design");
  const row = await start(page, "Senior system design + applied AI exam");
  expect(row.questions).toHaveLength(4);
  await expect(page.getByText(/Traffic increased 20/)).toHaveCount(0);
  for (const q of row.questions) await answer(page, row.id, q.id, TEXT);
  await page.reload();
  await page
    .getByRole("button", { name: "Commit this stage and reveal next incident" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Stage 2/8: Traffic increased 20×" }),
  ).toBeVisible();
  await page.getByLabel("Written response").fill(TEXT);
  await expect(page.getByRole("status")).toContainText("Saved to your account");
  await page
    .getByRole("button", { name: "Question 1, saved", exact: true })
    .click();
  await expect(
    page.getByText("Committed stage · response is fixed."),
  ).toBeVisible();
  await expect(page.getByLabel("Written response")).toHaveCount(0);
  for (let stage = 1; stage < 8; stage++) {
    const current = await (
      await page.request.get(`/api/exams/attempts/${row.id}`)
    ).json();
    for (const q of current.questions)
      if (!(q.id in current.answers)) await answer(page, row.id, q.id, TEXT);
    await page.reload();
    if (stage < 7) {
      await page
        .getByRole("button", {
          name: "Commit this stage and reveal next incident",
        })
        .click();
      await expect(
        page.getByText(`Stage ${stage + 2}/8:`, { exact: false }),
      ).toBeVisible();
    }
  }
  await page
    .getByRole("button", { name: "Submit and freeze exam evidence" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Manual review required" }),
  ).toBeVisible();
  await expect(
    page.getByText("11 written responses saved for review.", { exact: false }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Manual review required" }),
  ).toBeVisible();
});

test("practical draft runs in Docker and failed finite checks submit honestly as fixed evidence", async ({
  page,
}) => {
  await signup(page, "Repair");
  const row = await start(page, "Practical engineering repair exam");
  expect(JSON.stringify(row)).not.toContain('"expected"');
  const download = page.waitForEvent("download");
  await page
    .getByRole("link", { name: "Download broken application and public tests" })
    .click();
  expect((await download).suggestedFilename()).toBe("practical-repair-v1.zip");
  await page
    .getByLabel("Practical source")
    .fill(row.execution.starter + "\n# My initial repair baseline\n");
  await expect(
    page.getByRole("status").filter({ hasText: "Saving changes" }),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "Run isolated checks", exact: true })
    .click();
  await expect(
    page.locator("summary").filter({ hasText: /Run #.*passed/ }),
  ).toBeVisible({ timeout: 65000 });
  const runs = await (
    await page.request.get(`/api/exams/attempts/${row.id}/runs`)
  ).json();
  expect(runs).toHaveLength(1);
  expect(runs[0].result.status).toBe("failed");
  for (const c of runs[0].result.checks)
    if (!c.public) {
      expect(c.actual).toBeNull();
      expect(c.message).toBe("");
    }
  await page.getByLabel("Written response").fill(TEXT);
  await expect(
    page.getByRole("status").filter({ hasText: "Saved to your account" }),
  ).toHaveCount(2);
  for (const q of row.questions)
    if (q.id !== row.questions[0].id) await answer(page, row.id, q.id, TEXT);
  await page.reload();
  await page
    .getByRole("button", { name: "Submit and freeze exam evidence" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Manual review required" }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Open fixed evidence and request review" })
    .click();
  await expect(
    page.getByRole("region", { name: "Fixed exam attachment" }),
  ).toBeVisible();
  await page.getByText("Submitted source", { exact: true }).click();
  await expect(page.getByText(/My initial repair baseline/)).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
  ).toBe(false);
  await page.screenshot({
    path: "test-results/practical-exam-mobile.png",
    fullPage: true,
  });
});
