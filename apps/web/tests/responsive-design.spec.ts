import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mkdir, writeFile } from "node:fs/promises";

async function learner(page: Page) {
  const result = await page.request.post("/api/auth/register", {
    headers: { "X-Academy-Request": "1" },
    data: {
      name: "Design Learner",
      email: `design-${Date.now()}-${Math.random().toString(36).slice(2)}@example.com`,
      password: "local-responsive-test-passphrase",
    },
  });
  expect(result.status()).toBe(201);
}
async function noOverflow(page: Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
}

test("mobile authentication keeps the form reachable and password visibility accessible", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/login");
  const submit = page.getByRole("button", {
    name: "Create workspace",
    exact: true,
  });
  const box = await submit.boundingBox();
  expect(box).not.toBeNull();
  expect(box!.y + box!.height).toBeLessThan(844);
  await page
    .getByLabel("Password", { exact: true })
    .fill("a-test-only-passphrase");
  await page
    .getByRole("button", { name: "Show password", exact: true })
    .click();
  await expect(page.getByLabel("Password", { exact: true })).toHaveAttribute(
    "type",
    "text",
  );
  await page
    .getByRole("button", { name: "Hide password", exact: true })
    .click();
  await expect(page.getByLabel("Password", { exact: true })).toHaveAttribute(
    "type",
    "password",
  );
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/mode=signin/);
  await expect(page.getByLabel("Your name")).toHaveCount(0);
  await expect(page.getByLabel("Password", { exact: true })).toHaveAttribute(
    "autocomplete",
    "current-password",
  );
  await noOverflow(page);
});

test("curriculum filters combine track, reading state and topics without losing planned labels", async ({
  page,
}) => {
  await learner(page);
  await page.goto("/learn");
  await expect(page.locator(".catalog-result-row")).toContainText("195 of 195");
  await expect(
    page.locator(".track-disclosure").filter({ hasText: "Planned" }).first(),
  ).toBeVisible();
  await page
    .getByRole("searchbox", { name: "Search topics" })
    .fill("iterators");
  await expect(page.locator(".catalog-result-row")).toContainText(
    "match your filters",
  );
  await expect(page.locator(".curriculum-module .lesson-row")).not.toHaveCount(
    0,
  );
  await page
    .getByLabel("Reading status", { exact: true })
    .selectOption("completed");
  await expect(
    page.getByRole("heading", { name: "No topics match yet." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Clear filters" }).click();
  await expect(page.locator(".catalog-result-row")).toContainText("195 of 195");
  await page
    .getByRole("searchbox", { name: "Search topics" })
    .fill("References, mutation");
  await page.locator(".curriculum-module .lesson-row").click();
  await page.getByRole("button", { name: "Mark reading complete" }).click();
  await expect(
    page.getByRole("button", { name: "Reading completed" }),
  ).toBeVisible();
  await page.goto("/learn");
  await page
    .getByLabel("Reading status", { exact: true })
    .selectOption("completed");
  await expect(page.locator(".catalog-result-row")).toContainText("1 of 195");
  await expect(page.locator(".curriculum-module .lesson-row")).toHaveCount(1);
  await page.goto("/practice");
  await page
    .getByRole("searchbox", { name: "Search topics" })
    .fill("no-such-topic-713");
  await expect(
    page.getByRole("heading", { name: "No practice topics found." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Clear filters" }).click();
  await expect(page.locator(".practice-card")).toHaveCount(24);
  await page.getByRole("button", { name: "Show more topics" }).click();
  await expect(page.locator(".practice-card")).toHaveCount(48);
  await page.goto("/map");
  await page
    .getByRole("searchbox", { name: "Search topics" })
    .fill("iterators");
  await expect(page.locator(".knowledge-node")).not.toHaveCount(0);
  await noOverflow(page);
});

test("tablet navigation, mobile study tools and note persistence work together", async ({
  page,
}) => {
  await learner(page);
  await page.setViewportSize({ width: 820, height: 1180 });
  await page.goto("/");
  const more = page.getByRole("button", { name: "Open all navigation" });
  await more.click();
  const menu = page.getByRole("dialog", { name: "Workspace navigation" });
  await expect(menu).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(more).toBeFocused();
  await page
    .getByRole("navigation", { name: "Quick navigation" })
    .getByRole("link", { name: "Learning path", exact: true })
    .click();
  await expect(
    page.getByRole("searchbox", { name: "Search topics" }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/lessons/python-values");
  const tools = page.getByRole("navigation", { name: "Lesson study tools" });
  await tools.getByRole("link", { name: "Notes", exact: true }).click();
  const note = page.getByLabel("Your working notes", { exact: true });
  await expect(note).toBeInViewport();
  await note.fill("A saved note from the responsive study workspace.");
  await expect(tools.getByLabel("Unsaved changes")).toBeVisible();
  await page.getByRole("button", { name: "Save note", exact: true }).click();
  await expect(
    page.getByRole("status").filter({ hasText: /^Note saved$/ }),
  ).toBeVisible();
  await page.reload();
  await expect(note).toHaveValue(
    "A saved note from the responsive study workspace.",
  );
  await tools.getByRole("link", { name: "Practice", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Test your understanding." }),
  ).toBeInViewport();
  await noOverflow(page);
});

test("responsive surfaces have no detected accessibility violations or page overflow", async ({
  page,
}) => {
  test.setTimeout(240000);
  await learner(page);
  const checks: {
    route: string;
    width: number;
    theme: string;
    violations: number;
  }[] = [];
  await mkdir("../../docs/screenshots", { recursive: true });
  for (const width of [320, 390, 820, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const route of [
      "/",
      "/learn",
      "/lessons/python-values",
      "/practice",
      "/exams",
    ]) {
      await page.goto(route);
      await expect(page.locator("main h1")).toBeVisible();
      await expect(
        page.getByText("Loading your workspace…", { exact: true }),
      ).toHaveCount(0);
      await noOverflow(page);
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze();
      checks.push({
        route,
        width,
        theme: "light",
        violations: results.violations.length,
      });
      expect(
        results.violations.map((v) => ({
          id: v.id,
          targets: v.nodes.map((n) => n.target),
        })),
        `${route} at ${width}`,
      ).toEqual([]);
      if (
        (width === 390 || width === 1440) &&
        ["/", "/learn", "/lessons/python-values"].includes(route)
      ) {
        const name =
          route === "/"
            ? "overview"
            : route === "/learn"
              ? "curriculum"
              : "lesson";
        await page.screenshot({
          path: `../../docs/screenshots/ui-ux-${name}-${width}.png`,
        });
      }
    }
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Switch to dark theme" }).click();
  for (const route of [
    "/",
    "/learn",
    "/lessons/python-values",
    "/practice",
    "/exams",
  ]) {
    await page.goto(route);
    await expect(page.locator("main h1")).toBeVisible();
    await noOverflow(page);
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
      .analyze();
    checks.push({
      route,
      width: 390,
      theme: "dark",
      violations: results.violations.length,
    });
    expect(
      results.violations.map((v) => ({
        id: v.id,
        nodes: v.nodes.map((n) => n.target),
      })),
      `${route} dark`,
    ).toEqual([]);
  }
  await page.screenshot({
    path: "../../docs/screenshots/ui-ux-assessments-dark-390.png",
  });
  await page.setViewportSize({ width: 844, height: 390 });
  await page.goto("/lessons/python-values");
  await expect(page.locator("main h1")).toBeVisible();
  await noOverflow(page);
  await page.emulateMedia({ reducedMotion: "reduce" });
  expect(
    await page
      .locator(".button")
      .first()
      .evaluate((el) => getComputedStyle(el).transitionDuration),
  ).toBe("0s");
  await mkdir("../../.local/ui-ux-20261016", { recursive: true });
  await writeFile(
    "../../.local/ui-ux-20261016/responsive-accessibility.json",
    JSON.stringify({ checks, landscape: true, reducedMotion: true }, null, 2),
  );
});
