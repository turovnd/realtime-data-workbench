import { expect, test } from "@playwright/test";
import { mockActivity } from "../../../helpers/activity";

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
