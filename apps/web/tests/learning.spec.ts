import { test, expect } from "@playwright/test";

test("complete a lesson, save notes, solve a scenario and see persistent progress", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Alex Engineer");
  await page
    .getByLabel("Email address")
    .fill(`journey-${Date.now()}@example.com`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("a-long-browser-test-passphrase");
  await page.getByRole("button", { name: "Create workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome aboard, Alex." }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/overview-desktop.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "Learning path", exact: true }).click();
  await page
    .getByRole("link", { name: /References, mutation & ownership/ })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "References, mutation & ownership",
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByLabel("Your working notes")
    .fill(
      "Shallow copies retain nested references. Test with two sequential requests.",
    );
  await page.getByRole("button", { name: "Save note" }).click();
  await expect(
    page.getByRole("status").filter({ hasText: /^Note saved$/ }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Bookmark lesson" }).click();
  await page.getByRole("button", { name: "Mark reading complete" }).click();
  await expect(
    page.getByRole("button", { name: "Reading completed" }),
  ).toBeDisabled();
  await page.reload();
  await expect(page.getByLabel("Your working notes")).toHaveValue(
    /Shallow copies/,
  );
  await expect(
    page.getByRole("button", { name: "Bookmarked", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: /A copy that still changes the original/ })
    .click();
  await page.getByRole("radio", { name: "B [7]", exact: true }).check();
  await page.getByRole("button", { name: "Submit answer" }).click();
  await expect(page.getByText("Well reasoned.")).toBeVisible();
  await expect(page.getByText("REFERENCE REASONING")).toBeVisible();
  await page.getByRole("link", { name: "Skill progress", exact: true }).click();
  await expect(
    page.getByText("1 exercises solved · 1 attempts · 1 lessons read"),
  ).toBeVisible();
  await page.goto("/review");
  await expect(page.getByText("Upcoming", { exact: true })).toBeVisible();
  await page.goto("/");
  await page.getByRole("button", { name: "Search anything" }).click();
  await page
    .getByRole("textbox", { name: "Search query" })
    .fill("Shallow copies");
  await expect(
    page.getByRole("dialog").getByText("Note", { exact: true }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Switch to dark theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.screenshot({
    path: "test-results/overview-dark.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Switch to light theme" }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "test-results/overview-mobile.png",
    fullPage: true,
  });
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth,
  );
  expect(overflow).toBe(false);
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("link", { name: "Bookmarks", exact: true }).click();
  await expect(
    page.getByRole("link", { name: /References, mutation & ownership/ }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("diagnostic saves answers, resumes and returns category feedback only after submission", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Exam Learner");
  await page.getByLabel("Email address").fill(`exam-${Date.now()}@example.com`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("a-long-browser-test-passphrase");
  await page.getByRole("button", { name: "Create workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome aboard, Exam." }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Assessments", exact: true }).click();
  await page.getByRole("button", { name: "Begin diagnostic" }).click();
  await expect(page.getByText("FOCUS MODE")).toBeVisible();
  await expect(
    page.getByRole("navigation", { name: "Main navigation" }),
  ).toHaveCount(0);
  const examURL = page.url();
  await page.getByRole("radio").nth(1).check();
  await expect(page.getByRole("status")).toHaveText("Answer saved");
  await page.reload();
  await expect(page.getByRole("radio").nth(1)).toBeChecked();
  for (let i = 1; i < 10; i++) {
    await page
      .getByRole("button", { name: `Question ${i + 1}`, exact: true })
      .click();
    await page.getByRole("radio").nth(0).check();
    await expect(page.getByRole("status")).toHaveText("Answer saved");
  }
  await page.getByRole("button", { name: "Submit diagnostic" }).click();
  await expect(
    page.getByRole("heading", { name: "Your next step is clearer." }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Performance by category" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Recommended next steps" }),
  ).toBeVisible();
  await page.goto(examURL);
  await expect(
    page.getByText("DIAGNOSTIC COMPLETE", { exact: true }),
  ).toBeVisible();
});
