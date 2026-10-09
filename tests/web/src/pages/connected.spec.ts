import { expect, test } from "@playwright/test";

test("real account registration, durable results and login after logout", async ({
  page,
}) => {
  const email = `feedback-${crypto.randomUUID()}@example.test`;
  const password = "feedback-test-password-2026";
  await page.goto("/");
  await page.getByRole("tab", { name: "Create account", exact: true }).click();
  await page.getByRole("textbox", { name: "Email", exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Feedback stream", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("No feedback in this view")).toBeVisible();
  await page.getByRole("button", { name: "Add 12 live records" }).click();
  await expect(page.getByText(/Showing 12 of 12 matching/)).toBeVisible();
  await expect(
    page.getByRole("row").filter({ hasText: "Enriched" }),
  ).toHaveCount(12, { timeout: 15000 });
  await page
    .getByRole("checkbox", { name: "Select feedback 12", exact: true })
    .check();
  await page.getByRole("button", { name: "Run backfill" }).click();
  await expect(page.getByText("1 complete · 0 failed")).toBeVisible({
    timeout: 15000,
  });
  await page
    .getByRole("button", { name: "Inspect feedback 12", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toContainText("Enrichment v2");
  await expect(page.getByRole("dialog")).toContainText("Enrichment v1");
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Save snapshot" }).click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(() =>
      Object.keys(localStorage).filter((key) =>
        key.startsWith("feedback-desk-offline:"),
      ),
    ),
  ).toEqual([]);
  await page.getByRole("textbox", { name: "Email", exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByText(/Showing 12 of 12 matching/)).toBeVisible();
  await page
    .getByRole("button", { name: "Inspect feedback 12", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toContainText("Enrichment v2");
});

test("real cursor pages remain stable while new feedback arrives", async ({
  page,
  request,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Try an isolated demo" }).click();
  await expect(page.getByText(/Showing 12 of 24 matching/)).toBeVisible();
  await page
    .getByRole("checkbox", { name: "Select feedback 24", exact: true })
    .check();
  const token = await page.evaluate(() => {
    const value = Object.keys(sessionStorage).find((key) =>
      key.startsWith("feedback-desk-auth:"),
    );
    if (!value) throw new Error("Missing test session");
    return (JSON.parse(sessionStorage.getItem(value)!) as { token: string })
      .token;
  });
  const inserted = await request.post("http://127.0.0.1:8002/api/simulations", {
    headers: { Authorization: `Bearer ${token}` },
    data: { request_id: crypto.randomUUID(), count: 12 },
  });
  expect(inserted.ok()).toBe(true);
  await expect(page.getByText("New feedback is available")).toBeVisible({
    timeout: 10000,
  });
  await page.getByTestId("feedback-load-more").scrollIntoViewIfNeeded();
  await expect(page.getByText(/Showing 24 of 24 matching/)).toBeVisible();
  const numbers = await page
    .getByRole("button", { name: /^Inspect feedback \d+$/ })
    .evaluateAll((elements) =>
      elements.map((element) =>
        Number(element.getAttribute("aria-label")?.split(" ").at(-1)),
      ),
    );
  expect(numbers).toEqual(Array.from({ length: 24 }, (_, index) => 24 - index));
  await page.getByRole("button", { name: "Show new feedback" }).click();
  await expect(page.getByText(/Showing 12 of 36 matching/)).toBeVisible();
  await expect(
    page.getByText(/1 selected across this workspace/),
  ).toBeVisible();
  await page.getByTestId("feedback-load-more").scrollIntoViewIfNeeded();
  await expect(
    page.getByRole("checkbox", { name: "Select feedback 24", exact: true }),
  ).toBeChecked();
  await page.getByRole("textbox", { name: "Search feedback" }).fill("invoice");
  await expect(page).toHaveURL(/q=invoice/);
  await expect(page.getByText(/Showing 3 of 3 matching/)).toBeVisible();
});

test("an expired API view exposes a working refresh action", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Try an isolated demo" }).click();
  await expect(page.getByText(/Showing 12 of 24 matching/)).toBeVisible();
  let injected = false;
  await page.route("**/api/feedback?**", async (route) => {
    if (
      !injected &&
      new URL(route.request().url()).searchParams.has("cursor")
    ) {
      injected = true;
      await route.fulfill({
        status: 410,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "This view expired. Refresh to open a current view.",
        }),
      });
    } else await route.continue();
  });
  await page.getByTestId("feedback-load-more").scrollIntoViewIfNeeded();
  await expect(
    page.getByText("This view expired. Refresh to open a current view."),
  ).toBeVisible();
  await page
    .getByRole("alert")
    .filter({ hasText: "Unable to update this view" })
    .getByRole("button", { name: "Refresh view" })
    .click();
  await expect(
    page.getByText("This view expired. Refresh to open a current view."),
  ).not.toBeVisible();
  await expect(
    page.getByRole("button", { name: "Inspect feedback 24", exact: true }),
  ).toBeVisible();
});
