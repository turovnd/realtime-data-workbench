import { expect, test } from "@playwright/test";
import { mockActivity } from "../../../helpers/activity";

test("a failed status refresh remains actionable with cached status and pauses automatic paging", async ({
  page,
}) => {
  await page.clock.install();
  await mockActivity(page);
  await page.goto("/login");
  await page.getByRole("button", { name: "Try the demo", exact: true }).click();
  await expect(page).toHaveURL(/\/feedback$/);
  await expect(
    page.getByText("Showing 12 of 14", { exact: true })
  ).toBeVisible();
  let unavailable = true;
  let failedRequests = 0;
  await page.route("**/api/status", async route => {
    if (!unavailable) return route.fallback();
    failedRequests++;
    return route.fulfill({
      status: 503,
      json: { detail: "Analysis status is temporarily unavailable" },
    });
  });

  await page.clock.runFor(3100);
  const error = page
    .getByRole("alert")
    .filter({ hasText: "Couldn’t update analysis status" });
  await expect(error).toContainText(
    "Analysis status is temporarily unavailable"
  );
  await expect(
    page.getByRole("button", { name: "Load more", exact: true })
  ).toBeDisabled();
  await page.clock.runFor(12100);
  expect(failedRequests).toBe(1);

  unavailable = false;
  await error.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(error).not.toBeVisible();
  await expect(
    page.getByRole("button", { name: "Load more", exact: true })
  ).toBeEnabled();
});
