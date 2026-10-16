import { test, expect } from "@playwright/test";

for (const [level, count] of [
  ["beginner", 20],
  ["intermediate", 24],
  ["advanced", 28],
] as const) {
  test(`${level} Python evaluates its own bank, preserves answers, and shows its library guide`, async ({
    page,
  }) => {
    await page.goto("/login");
    await page.getByLabel("Your name").fill("Python Learner");
    await page
      .getByLabel("Email address")
      .fill(`python-${level}-${Date.now()}@example.com`);
    await page
      .getByLabel("Password", { exact: true })
      .fill("a-long-browser-test-passphrase");
    await page.getByRole("button", { name: "Create workspace" }).click();
    await expect(
      page.getByRole("heading", { name: "Welcome aboard, Python." }),
    ).toBeVisible();
    await page.goto("/exams");
    const title = `Python · ${level[0].toUpperCase()}${level.slice(1)} evaluation`;
    const section = page.getByRole("region", { name: title });
    await expect(
      section.getByText(`${count} distinct questions`),
    ).toBeVisible();
    await section.locator("summary").click();
    await expect(
      section.getByText(/These are working-proficiency targets/),
    ).toBeVisible();
    await expect(
      section.getByRole("link", {
        name: level === "beginner" ? "pathlib ↗" : "typing ↗",
        exact: true,
      }),
    ).toBeVisible();
    await section.locator("summary").click();
    const started = page.waitForResponse(
      (response) =>
        response.url().endsWith("/api/exams/start") &&
        response.request().method() === "POST",
    );
    await section.getByRole("button", { name: `Begin ${level} test` }).click();
    const payload = await (await started).json();
    expect(payload.exam_id).toBe(`python-${level}-v1`);
    expect(payload.questions).toHaveLength(count);
    expect(payload.result).toBeNull();
    for (const question of payload.questions) {
      expect(question).not.toHaveProperty("answer");
      expect(question).not.toHaveProperty("explanation");
      expect(question).not.toHaveProperty("validation_output");
    }
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    await page.getByRole("radio").first().check();
    await expect(page.getByRole("status")).toHaveText("Answer saved");
    const attemptURL = page.url();
    await page.goto("/exams");
    await page.getByRole("button", { name: `Resume ${level} test` }).click();
    await expect(page).toHaveURL(attemptURL);
    await expect(page.getByRole("radio").first()).toBeChecked();
    for (let index = 1; index < count; index++) {
      await page
        .getByRole("button", { name: `Question ${index + 1}`, exact: true })
        .click();
      if (index === 1)
        await expect(page.getByLabel("Python code to analyze")).toBeVisible();
      await page.getByRole("radio").first().check();
      await expect(page.getByRole("status")).toHaveText("Answer saved");
    }
    await page.getByRole("button", { name: "Submit diagnostic" }).click();
    await expect(
      page.getByRole("heading", { name: "More practice recommended" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Performance by category" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", {
        name: "Practical follow-up · not automatically graded",
      }),
    ).toBeVisible();
    await page.reload();
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    await page.setViewportSize({ width: 390, height: 844 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      ),
    ).toBe(false);
    await page.goto("/exams");
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    await page.screenshot({
      path: `test-results/python-assessments-${level}-mobile.png`,
      fullPage: true,
    });
  });
}
