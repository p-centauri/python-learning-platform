import { test, expect, type Page } from "@playwright/test";
const python = `import re
def parse_cents(text):
    if not isinstance(text, str) or not re.fullmatch(r"[0-9]+(?:\\.[0-9]{1,2})?", text):
        raise ValueError("Use digits and up to two decimals.")
    whole, _, fraction = text.partition(".")
    return int(whole)*100 + int(fraction.ljust(2,"0"))
`;
const sql = `SELECT c.id AS customer_id, COALESCE(SUM(o.total_cents),0) AS total_cents
FROM customers c LEFT JOIN orders o ON o.customer_id=c.id AND o.status='paid'
GROUP BY c.id ORDER BY c.id;`;
async function register(page: Page, prefix: string) {
  await page.goto("/login");
  await page.getByLabel("Your name").fill("Coder");
  await page
    .getByLabel("Email address")
    .fill(`${prefix}-${Date.now()}@example.com`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("a-long-browser-test-passphrase");
  await page.getByRole("button", { name: "Create workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome aboard, Coder." }),
  ).toBeVisible();
}
test("real Python checks, saved draft, fixed history and private cases", async ({
  page,
}) => {
  test.setTimeout(90000);
  await register(page, "coding-python");
  await page.getByRole("link", { name: "Coding and SQL", exact: true }).click();
  await page
    .getByRole("link", { name: /Parse exact money without floats/ })
    .click();
  const editor = page.getByLabel("Python code", { exact: true });
  await expect(page.getByText("Starter loaded", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Run checks", exact: true }),
  ).toBeEnabled();
  await editor.focus();
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("button", { name: "Save draft", exact: true }),
  ).toBeFocused();
  await editor.focus();
  await page.keyboard.press("Control+Enter");
  const feedback = page.getByRole("region", {
    name: "Run feedback",
    exact: true,
  });
  await expect(feedback).toContainText("0/6 checks passed", { timeout: 60000 });
  await expect(feedback).toContainText("NotImplementedError");
  const first = (
    await (await page.request.get("/api/coding/python-exact-cents")).json()
  ).attempts[0];
  await editor.fill(python);
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Draft saved" }),
  ).toBeVisible();
  await page.reload();
  await expect(editor).toHaveValue(python);
  await page.getByRole("button", { name: "Run checks", exact: true }).click();
  await expect(feedback).toContainText("6/6 checks passed", { timeout: 60000 });
  const detail = await (
    await page.request.get("/api/coding/python-exact-cents")
  ).json();
  expect(detail.attempts).toHaveLength(2);
  expect(detail.attempts[1]).toEqual(first);
  expect(
    detail.attempts[0].result.checks
      .filter((c: { public: boolean }) => !c.public)
      .every(
        (c: { actual: unknown; message: string }) =>
          c.actual === null && c.message === "",
      ),
  ).toBe(true);
  expect(JSON.stringify(detail)).not.toContain("0003.07");
  await editor.fill("# new unfinished draft");
  await page
    .getByRole("button", { name: new RegExp(`Run ${first.id} · 0/6 passed`) })
    .click();
  await expect(feedback).toContainText("0/6 checks passed");
  await expect(editor).toHaveValue("# new unfinished draft");
  await page
    .getByRole("button", {
      name: new RegExp(`Run ${detail.attempts[0].id} · 6/6 passed`),
    })
    .click();
  await page
    .getByRole("heading", { name: "Your implementation", exact: true })
    .click();
  await editor.fill(python);
  await editor.blur();
  await page.evaluate(() => {
    (document.activeElement as HTMLElement)?.blur();
    window.scrollTo(0, 0);
  });
  await expect(page.locator(".skip-link")).not.toBeFocused();
  await page.screenshot({
    path: "test-results/coding-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page
    .getByRole("region", { name: "Code editor", exact: true })
    .screenshot({ path: "test-results/coding-mobile.png" });
  expect(
    (await (await page.request.get("/api/dashboard")).json()).mastery,
  ).toBe(0);
});
test("save failure and unavailable execution preserve SQL before a real PostgreSQL retry", async ({
  page,
}) => {
  test.setTimeout(90000);
  await register(page, "coding-sql");
  await page.goto("/coding/sql-paid-totals");
  const editor = page.getByLabel("SQL query", { exact: true });
  await editor.fill(sql);
  await page.route("**/api/coding/sql-paid-totals/draft", (route) =>
    route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Save failed for this test." }),
    }),
  );
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(
    page.getByRole("alert").filter({ hasText: "Save failed" }),
  ).toBeVisible();
  await expect(editor).toHaveValue(sql);
  await page.unroute("**/api/coding/sql-paid-totals/draft");
  await page.route("**/api/coding/sql-paid-totals/attempts", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Runner unavailable for this test." }),
    }),
  );
  await page.getByRole("button", { name: "Run checks", exact: true }).click();
  await expect(
    page.getByRole("alert").filter({ hasText: "Runner unavailable" }),
  ).toBeVisible();
  await expect(editor).toHaveValue(sql);
  await expect(
    page.getByRole("button", { name: "Run checks", exact: true }),
  ).toBeDisabled();
  const saved = await (
    await page.request.get("/api/coding/sql-paid-totals")
  ).json();
  expect(saved.code).toBe(sql);
  expect(saved.attempts).toEqual([]);
  await page.unroute("**/api/coding/sql-paid-totals/attempts");
  await page
    .getByRole("button", { name: "Check runner status", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Run checks", exact: true }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "Run checks", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Run feedback", exact: true }),
  ).toContainText("3/3 checks passed", { timeout: 60000 });
  await page.reload();
  await expect(editor).toHaveValue(sql);
  await expect(
    page.getByRole("region", { name: "Run feedback", exact: true }),
  ).toContainText("3/3 checks passed");
  expect(
    (await (await page.request.get("/api/dashboard")).json()).mastery,
  ).toBe(0);
});
