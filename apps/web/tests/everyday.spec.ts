import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { writeFile, mkdir } from "node:fs/promises";

test.setTimeout(300000);
const PASSWORD = "a-long-browser-test-passphrase";
async function signup(page: Page, name: string) {
  await page.goto("/login");
  await page.getByLabel("Your name").fill(name);
  await page
    .getByLabel("Email address")
    .fill(`everyday-${name.toLowerCase()}-${Date.now()}@example.com`);
  await page.getByLabel("Password", { exact: true }).fill(PASSWORD);
  const request = page.waitForResponse((r) =>
    r.url().endsWith("/api/auth/register"),
  );
  await page.getByRole("button", { name: "Create workspace" }).click();
  let response = await request;
  if (response.status() === 429) {
    await new Promise((r) =>
      setTimeout(r, Number(response.headers()["retry-after"] || "60") * 1000),
    );
    const retry = page.waitForResponse((r) =>
      r.url().endsWith("/api/auth/register"),
    );
    await page.getByRole("button", { name: "Create workspace" }).click();
    response = await retry;
  }
  expect(response.status()).toBe(201);
  await expect(page.locator("h1")).toContainText("Welcome aboard");
  return (await response.json()).email as string;
}

test("offline recovery and evidence downloads work through the actual account interface", async ({
  page,
}) => {
  const email = await signup(page, "Recovery");
  await page.goto("/account");
  await expect(
    page.getByRole("heading", { name: "Keep access. Keep your work." }),
  ).toBeVisible();
  await page.getByLabel("Current password for recovery setup").fill(PASSWORD);
  await page
    .getByRole("button", { name: "Generate recovery key", exact: true })
    .click();
  const key = page.getByLabel("New recovery key");
  await expect(key).toBeVisible();
  const value = await key.inputValue();
  expect(value).toMatch(/^academy-recovery-/);
  let download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Save recovery key file" }).click();
  expect((await download).suggestedFilename()).toBe("academy-recovery-key.txt");
  await page.getByRole("button", { name: "Hide this key" }).click();
  await expect(key).toHaveCount(0);
  download = page.waitForEvent("download");
  await page.getByRole("link", { name: "Download evidence JSON" }).click();
  expect((await download).suggestedFilename()).toMatch(
    /academy-evidence-.*\.json/,
  );
  download = page.waitForEvent("download");
  await page.getByRole("link", { name: "Download evidence Markdown" }).click();
  expect((await download).suggestedFilename()).toMatch(/\.md$/);
  const exported = await (
    await page.request.get("/api/account/export?format=json")
  ).json();
  expect(exported.account.email).toBe(email);
  expect(JSON.stringify(exported)).not.toContain(value);
  expect(JSON.stringify(exported)).not.toContain("password_hash");
  await page.goto("/recover");
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Offline recovery key").fill(value);
  await page
    .getByLabel("New password", { exact: true })
    .fill("a-new-browser-test-passphrase");
  await page
    .getByLabel("Confirm new password")
    .fill("a-new-browser-test-passphrase");
  await page
    .getByRole("button", { name: "Reset password and sign out sessions" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Your password has changed." }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Return to sign in" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome back." }),
  ).toBeVisible();
  await page.getByLabel("Email address").fill(email);
  await page
    .getByLabel("Password", { exact: true })
    .fill("a-new-browser-test-passphrase");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.locator("h1")).toContainText("Welcome aboard");
  await page.goto("/account");
  await expect(
    page.getByText("The last key was used. Create a new one.", {
      exact: false,
    }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
  ).toBe(false);
  await page.screenshot({
    path: "test-results/account-mobile.png",
    fullPage: true,
  });
});

test("major learning routes have accessible desktop/mobile controls and contrast", async ({
  page,
}) => {
  const failures: unknown[] = [];
  const checks: unknown[] = [];
  for (const width of [1280, 390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    for (const route of ["/login", "/recover"]) {
      await page.goto(route);
      await expect(page.locator("h1")).toBeVisible();
      const scan = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
        .analyze();
      checks.push({ route, width, violations: scan.violations.length });
      if (scan.violations.length)
        failures.push({ route, width, issues: scan.violations });
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        ),
      ).toBe(false);
    }
  }
  await signup(page, "Access");
  const routes = [
    "/",
    "/plan",
    "/learn",
    "/lessons/python-values",
    "/practice",
    "/practice/python-alias",
    "/coding",
    "/coding/python-exact-cents",
    "/review",
    "/projects",
    "/projects/backend",
    "/exams",
    "/progress",
    "/map",
    "/bookmarks",
    "/glossary",
    "/account",
  ];
  for (const width of [1280, 390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    for (const route of routes) {
      await page.goto(route);
      await expect(page.locator("h1")).toBeVisible();
      await page.waitForTimeout(100);
      const scan = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
        .analyze();
      const issues = scan.violations.map((v) => ({
        id: v.id,
        impact: v.impact,
        help: v.help,
        nodes: v.nodes.map((n) => ({
          target: n.target,
          summary: n.failureSummary,
          data: n.any.map((a) => a.data),
        })),
      }));
      checks.push({ route, width, violations: issues.length });
      if (issues.length) failures.push({ route, width, issues });
      if (
        await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        )
      )
        failures.push({ route, width, issues: ["horizontal overflow"] });
    }
  }
  const configured = await page.request.post("/api/account/recovery-key", {
    headers: { "X-Academy-Request": "1" },
    data: { current_password: PASSWORD },
  });
  expect(configured.ok()).toBeTruthy();
  await page.goto("/account");
  const activeKey = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  checks.push({
    route: "/account",
    state: "active recovery key",
    width: 320,
    violations: activeKey.violations.length,
  });
  if (activeKey.violations.length)
    failures.push({
      route: "/account",
      state: "active recovery key",
      issues: activeKey.violations,
    });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
  ).toBe(false);
  await page.getByRole("button", { name: "Switch to dark theme" }).click();
  const dark = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  checks.push({
    route: "/account",
    theme: "dark",
    width: 320,
    violations: dark.violations.length,
  });
  if (dark.violations.length)
    failures.push({
      route: "/account",
      theme: "dark",
      issues: dark.violations.map((v) => ({
        id: v.id,
        nodes: v.nodes.map((n) => ({
          target: n.target,
          summary: n.failureSummary,
          data: n.any.map((a) => a.data),
        })),
      })),
    });
  await page.goto("/exams");
  const started = await page.request.post("/api/exams/start", {
    headers: { "X-Academy-Request": "1" },
    data: { exam_id: "engineering-knowledge-v1" },
  });
  expect(started.ok()).toBeTruthy();
  const exam = await started.json();
  await page.goto(`/exams/${exam.id}`);
  await expect(page.locator("h1")).toBeVisible();
  const active = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  checks.push({
    route: "active exam",
    theme: "dark",
    width: 320,
    violations: active.violations.length,
  });
  if (active.violations.length)
    failures.push({
      route: "active exam",
      issues: active.violations.map((v) => ({
        id: v.id,
        nodes: v.nodes.map((n) => ({
          target: n.target,
          summary: n.failureSummary,
          data: n.any.map((a) => a.data),
        })),
      })),
    });
  await mkdir("test-results", { recursive: true });
  await writeFile(
    "test-results/accessibility-report.json",
    JSON.stringify({ checks, failures }, null, 2),
  );
  expect(failures).toEqual([]);
});

test("mobile navigation and search trap focus, close with Escape and restore keyboard focus", async ({
  page,
}) => {
  await signup(page, "Keyboard");
  await page.setViewportSize({ width: 390, height: 844 });
  const menu = page.getByRole("button", {
    name: "Open navigation",
    exact: true,
  });
  await menu.focus();
  await page.keyboard.press("Enter");
  const dialog = page.getByRole("dialog", { name: "Workspace navigation" });
  await expect(dialog).toBeVisible();
  await expect(
    dialog.getByRole("button", { name: "Close navigation menu" }),
  ).toBeFocused();
  for (let i = 0; i < 22; i++) {
    await page.keyboard.press("Tab");
    expect(
      await page.evaluate(
        () =>
          !!document
            .querySelector("#academy-sidebar")
            ?.contains(document.activeElement),
      ),
    ).toBe(true);
  }
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(menu).toBeFocused();
  await page.setViewportSize({ width: 1280, height: 844 });
  const search = page.getByRole("button", { name: "Search anything" });
  await search.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByLabel("Search query")).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(search).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("button", { name: "Switch to dark theme" }),
  ).toBeFocused();
  await page.goto("/lessons/python-values");
  await expect(page.locator("h1")).toBeVisible();
  await page.keyboard.press("Tab");
  await page.getByRole("link", { name: "Skip to content" }).focus();
  await page.keyboard.press("Enter");
  expect(await page.evaluate(() => location.hash)).toBe("#main-content");
});
