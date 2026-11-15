import { expect, test } from "@playwright/test";

const identity = {
  workspace_id: "mock-auth-workspace",
  token: "mock-auth-token",
  email: "owner@example.test",
  kind: "account",
};

test("account form retains its return destination through a recoverable login error", async ({
  page,
}) => {
  const submissions: unknown[] = [];

  await page.route(
    url => url.pathname.startsWith("/api/"),
    async route => {
      const url = new URL(route.request().url());

      if (url.pathname === "/api/auth/login") {
        submissions.push(route.request().postDataJSON());
        await route.fulfill({
          status: submissions.length === 1 ? 401 : 200,
          json:
            submissions.length === 1
              ? { detail: "The email or password is incorrect." }
              : identity,
        });
        return;
      }

      if (url.pathname === "/api/auth/me") {
        await route.fulfill({ json: identity });
        return;
      }

      if (url.pathname === "/api/feedback/record-17") {
        await route.fulfill({
          json: {
            id: "record-17",
            sequence: 17,
            text: "The invoice export is missing the date range.",
            channel: "Support",
            ingested_at: "2026-10-20T10:00:00Z",
            jobs: [],
            outputs: [],
          },
        });
        return;
      }

      await route.fulfill({
        status: 404,
        json: { detail: `Unexpected route: ${url.pathname}` },
      });
    }
  );

  await page.goto("/feedback/record-17?q=invoice");
  await expect(page).toHaveURL(/\/login$/);
  await page
    .getByRole("textbox", { name: "Email", exact: true })
    .fill("OWNER@example.test");
  await page.getByLabel("Password", { exact: true }).fill("test-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText(
    "The email or password is incorrect."
  );
  await expect(
    page.getByRole("textbox", { name: "Email", exact: true })
  ).toHaveValue("OWNER@example.test");

  await page.getByRole("button", { name: "Sign in", exact: true }).click();

  await expect(page).toHaveURL(/\/feedback\/record-17\?q=invoice$/);
  await expect(
    page.getByRole("heading", { name: "Feedback #17", exact: true })
  ).toBeVisible();
  expect(submissions).toEqual([
    { email: "owner@example.test", password: "test-password" },
    { email: "owner@example.test", password: "test-password" },
  ]);
});

test("switching account mode clears the password and stale server error", async ({
  page,
}) => {
  await page.route("**/api/auth/login", route =>
    route.fulfill({
      status: 401,
      json: { detail: "The email or password is incorrect." },
    })
  );

  await page.goto("/login");
  await page
    .getByRole("textbox", { name: "Email", exact: true })
    .fill("owner@example.test");
  await page.getByLabel("Password", { exact: true }).fill("test-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText(
    "The email or password is incorrect."
  );
  await page.getByRole("link", { name: "Create account", exact: true }).click();

  await expect(page).toHaveURL(/\/register$/);
  await expect(page.getByLabel("Password", { exact: true })).toHaveValue("");
  await expect(page.getByRole("alert")).not.toBeVisible();
  await expect(
    page.getByRole("button", { name: "Create account", exact: true })
  ).toBeVisible();
});
