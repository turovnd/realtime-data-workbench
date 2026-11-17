import { expect, test } from "@playwright/test";
import { enterActivity, mockActivity } from "../../../helpers/activity";

test("an unavailable Activity request shows recovery instead of claiming the workspace has no runs", async ({
  page,
}) => {
  const fixture = await mockActivity(page, { empty: true });
  await page.goto("/login");
  await page.getByRole("button", { name: "Try the demo", exact: true }).click();
  await expect(page).toHaveURL(/\/feedback$/);
  fixture.setStatusUnavailable(true);
  await page.goto("/activity");
  await expect(
    page.getByText("We couldn’t load activity", { exact: true })
  ).toBeVisible({ timeout: 15000 });
  await expect(
    page.getByText("No analysis runs yet", { exact: true })
  ).not.toBeVisible();
  fixture.setStatusUnavailable(false);
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(
    page.getByText("No analysis runs yet", { exact: true })
  ).toBeVisible();
  await expect(
    page.getByText("We couldn’t load activity", { exact: true })
  ).not.toBeVisible();
});

test("failed refresh preserves activity and pauses polling until a successful manual retry", async ({
  page,
}) => {
  await page.clock.install();
  const fixture = await mockActivity(page);
  await enterActivity(page);
  await expect(page.getByText("Showing 2 of 2 activities")).toBeVisible();

  fixture.setStatusUnavailable(true);
  await page.clock.runFor(3100);
  const error = page
    .getByRole("alert")
    .filter({ hasText: "Couldn’t update activity" });
  await expect(error).toContainText("Activity is temporarily unavailable");
  await expect(error).toContainText("Response status: 503");
  await expect(page.getByText("Showing 2 of 2 activities")).toBeVisible();
  await expect(error.getByRole("button", { name: "Reload page" })).toHaveCount(
    0
  );
  const failedRequests = fixture.activityRequests.length;
  await page.clock.runFor(12000);
  expect(fixture.activityRequests).toHaveLength(failedRequests);

  fixture.setStatusUnavailable(false);
  await error.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(error).not.toBeVisible();
  const recoveredRequests = fixture.activityRequests.length;
  await page.clock.runFor(3100);
  await expect
    .poll(() => fixture.activityRequests.length)
    .toBeGreaterThan(recoveredRequests);
});

test("an explicit browser challenge offers a user-controlled reload and keeps cached activity", async ({
  page,
}) => {
  await page.clock.install();
  await mockActivity(page);
  await enterActivity(page);
  await expect(page.getByText("Showing 2 of 2 activities")).toBeVisible();
  let blocked = true;
  let challenges = 0;
  await page.route("**/api/activity?*", async route => {
    if (!blocked) return route.fallback();
    challenges++;
    return route.fulfill({
      status: 429,
      headers: {
        "content-type": "text/html",
        "x-vercel-mitigated": "challenge",
        "access-control-expose-headers": "x-vercel-mitigated",
      },
      body: "<html>private challenge response</html>",
    });
  });

  await page.clock.runFor(3100);
  const error = page
    .getByRole("alert")
    .filter({ hasText: "Couldn’t update activity" });
  await expect(error).toContainText(
    "A browser security check is required. Reload the page to continue."
  );
  await expect(error).toContainText("Response status: 429");
  await expect(page.getByText("Showing 2 of 2 activities")).toBeVisible();
  await expect(page.getByText("private challenge response")).toHaveCount(0);
  await page.clock.runFor(12000);
  expect(challenges).toBe(1);

  blocked = false;
  const navigation = page.waitForEvent(
    "framenavigated",
    frame => frame === page.mainFrame()
  );
  await error.getByRole("button", { name: "Reload page", exact: true }).click();
  await navigation;
  await expect(page.getByText("Showing 2 of 2 activities")).toBeVisible();
  await expect(error).not.toBeVisible();
});
