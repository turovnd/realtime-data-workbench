import { expect, test } from "@playwright/test";
import { enterDemo, feedbackLinks } from "../../../helpers/preview";

test("a filtered record has a reloadable detail page and both back paths preserve filters", async ({
  page,
}) => {
  await enterDemo(page);
  await page.goto("/feedback?q=billing&topic=billing&status=succeeded");
  const first = feedbackLinks(page).first();
  await expect(first).toBeVisible();
  const href = await first.getAttribute("href");
  expect(href).toBeTruthy();
  await first.focus();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/feedback\/[^/?]+/);
  await expect(
    page.getByRole("heading", { name: /^Feedback #\d+$/ })
  ).toBeVisible();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: /^Feedback #\d+$/ })
  ).toBeVisible();
  const detailUrl = new URL(page.url());
  expect(detailUrl.searchParams.get("q")).toBe("billing");
  expect(detailUrl.searchParams.get("topic")).toBe("billing");
  expect(detailUrl.searchParams.get("status")).toBe("succeeded");
  await page.goBack();
  await expect(page).toHaveURL(/\/feedback\?/);
  await expect(
    page.getByRole("textbox", { name: "Search feedback" })
  ).toHaveValue("billing");
  await page.goto(href!);
  await page
    .getByRole("link", { name: "Back to feedback", exact: true })
    .click();
  await expect(
    page.getByRole("textbox", { name: "Search feedback" })
  ).toHaveValue("billing");
  expect(new URL(page.url()).searchParams.get("topic")).toBe("billing");
  expect(new URL(page.url()).searchParams.get("status")).toBe("succeeded");
});
test("an unknown direct link offers a route back instead of an empty inspector", async ({
  page,
}) => {
  await enterDemo(page);
  await page.goto("/feedback/00000000-0000-4000-8000-000000000000");
  await expect(page.getByText(/not found/i).first()).toBeVisible();
  await page
    .getByRole("link", { name: "Back to feedback", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Feedback", exact: true })
  ).toBeVisible();
});
test("saved feedback remains readable offline while changes are disabled", async ({
  page,
  context,
}) => {
  await enterDemo(page);
  await page
    .getByRole("button", { name: "Save for offline", exact: true })
    .click();
  await page.evaluate(async () => {
    await navigator.serviceWorker.ready;
  });
  await expect
    .poll(() =>
      page.evaluate(() => navigator.serviceWorker.controller !== null)
    )
    .toBe(true);
  await context.setOffline(true);
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Feedback", exact: true })
  ).toBeVisible();
  await expect(page.getByText("You’re offline", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Add feedback", exact: true })
  ).toBeDisabled();
  await feedbackLinks(page).first().click();
  await expect(
    page.getByRole("heading", { name: /^Feedback #\d+$/ })
  ).toBeVisible();
  await expect(page.getByText("You’re offline", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Analyze with AI", exact: true })
  ).toBeDisabled();
  await context.setOffline(false);
  await expect(
    page.getByRole("button", { name: "Analyze with AI", exact: true })
  ).toBeDisabled();
  await expect(
    page.getByText("Connect the API to run AI analysis.", { exact: true })
  ).toBeVisible();
});
