import { expect, test } from "@playwright/test";
import { enterActivity, mockActivity } from "../../../helpers/activity";

test("feedback details retains its result and lets the user retry a failed refresh", async ({
  page,
}) => {
  await page.clock.install();
  const fixture = await mockActivity(page);
  await enterActivity(page);
  await page.goto(`/feedback/${fixture.firstRecordId}`);
  await expect(
    page.getByText(fixture.latestSummary, { exact: true })
  ).toBeVisible();
  let unavailable = true;
  let failedRequests = 0;
  await page.route(`**/api/feedback/${fixture.firstRecordId}`, async route => {
    if (!unavailable) return route.fallback();
    failedRequests++;
    return route.fulfill({
      status: 503,
      json: { detail: "Feedback is temporarily unavailable" },
    });
  });

  await page.clock.runFor(10100);
  const error = page
    .getByRole("alert")
    .filter({ hasText: "Updates unavailable" });
  await expect(error).toContainText("Feedback is temporarily unavailable");
  await expect(
    page.getByText(fixture.latestSummary, { exact: true })
  ).toBeVisible();
  await page.clock.runFor(20100);
  expect(failedRequests).toBe(1);

  unavailable = false;
  await error.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(error).not.toBeVisible();
  await expect(
    page.getByText(fixture.latestSummary, { exact: true })
  ).toBeVisible();
});
