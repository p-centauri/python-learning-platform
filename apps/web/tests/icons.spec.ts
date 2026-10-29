import { test, expect } from "@playwright/test";

// src/app/favicon.ico, icon.svg and apple-icon.png are Next metadata files: Next links them
// from every page and serves them as images (before them, /favicon.ico was the 404 page).
test("the site icons are linked and served as images", async ({
  page,
  request,
}) => {
  await page.goto("/login");
  const links = await page
    .locator('link[rel="icon"], link[rel="apple-touch-icon"]')
    .evaluateAll((nodes) =>
      nodes.map((n) => ({
        rel: n.getAttribute("rel"),
        path: new URL(n.getAttribute("href") ?? "", location.href).pathname,
      })),
    );
  expect(links).toEqual(
    expect.arrayContaining([
      { rel: "icon", path: "/favicon.ico" },
      { rel: "icon", path: "/icon.svg" },
      { rel: "apple-touch-icon", path: "/apple-icon.png" },
    ]),
  );
  const types: Record<string, string> = {
    "/favicon.ico": "image/x-icon",
    "/icon.svg": "image/svg+xml",
    "/apple-icon.png": "image/png",
  };
  for (const [path, type] of Object.entries(types)) {
    const response = await request.get(path);
    expect(response.status(), path).toBe(200);
    expect(response.headers()["content-type"], path).toBe(type);
  }
});
