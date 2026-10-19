import { expect, test } from "@playwright/test";
import { enterDemo } from "../../../helpers/preview";

test("the browser preview identifies samples and requires a connected API for AI", async ({
  page,
}) => {
  await enterDemo(page);
  await page.goto("/feedback/feedback-24");
  await expect(
    page
      .getByRole("region", { name: "Analysis result", exact: true })
      .getByText("Sample analysis", { exact: true })
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Analyze with AI", exact: true })
  ).toBeDisabled();
  await expect(
    page.getByText("Connect the API to run AI analysis.", { exact: true })
  ).toBeVisible();
  await page.goto("/feedback/feedback-21");
  await expect(
    page.getByText("Sample analysis unavailable", { exact: true })
  ).toBeVisible();
  await expect(
    page.getByText("AI analysis failed", { exact: true })
  ).not.toBeVisible();
  const activity = page.getByRole("link", { name: "Activity", exact: true });
  if (!(await activity.isVisible()))
    await page
      .getByRole("button", { name: "Toggle Sidebar", exact: true })
      .click();
  await activity.click();
  await expect(page).toHaveURL(/\/activity$/);
  await expect(
    page.getByRole("heading", { name: "Activity", exact: true })
  ).toBeVisible();
  await expect(
    page.getByText("Sample analysis · Support", { exact: true }).first()
  ).toBeVisible();
  await expect(
    page.getByText("Manual analysis", { exact: false })
  ).not.toBeVisible();
  await page.reload();
  await expect(
    page.getByText("Sample analysis · Support", { exact: true }).first()
  ).toBeVisible();
  await expect(
    page.getByText("Manual analysis", { exact: false })
  ).not.toBeVisible();
});
