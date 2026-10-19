import { expect, test } from "@playwright/test";
import {
  enterDemo,
  feedbackLinks,
  expectCount,
  manualPaging,
  addFeedback,
} from "../../../helpers/preview";

test("manual cursor paging has no duplicate rows and changing filters resets the list", async ({
  page,
}) => {
  await manualPaging(page);
  await enterDemo(page);
  await expectCount(page, 12, 24);
  const loadMore = page.getByRole("button", { name: "Load more", exact: true });
  await loadMore.focus();
  await page.keyboard.press("Enter");
  await expectCount(page, 24, 24);
  const labels = await feedbackLinks(page).evaluateAll(elements =>
    elements.map(element => element.getAttribute("aria-label"))
  );
  expect(labels).toHaveLength(24);
  expect(new Set(labels).size).toBe(24);
  await expect(loadMore).not.toBeVisible();
  await page.getByRole("textbox", { name: "Search feedback" }).fill("invoice");
  await expect(page).toHaveURL(/q=invoice/);
  await expectCount(page, 2, 2);
  await expect(feedbackLinks(page)).toHaveCount(2);
  await page
    .getByRole("textbox", { name: "Search feedback" })
    .fill("no-results-for-this-search");
  await expect(feedbackLinks(page)).toHaveCount(0);
  await page.getByRole("textbox", { name: "Search feedback" }).fill("");
  await expectCount(page, 12, 24);
  await expect(feedbackLinks(page)).toHaveCount(12);
});
test("scrolling loads the next cursor page while manual pagination remains an alternative", async ({
  page,
}) => {
  await enterDemo(page);
  await expectCount(page, 12, 24);
  await page.getByTestId("feedback-load-more").scrollIntoViewIfNeeded();
  await expectCount(page, 24, 24);
  await expect(feedbackLinks(page)).toHaveCount(24);
});
test("a customer's own text opens as a full feedback record", async ({
  page,
}) => {
  await enterDemo(page);
  const text =
    "The monthly CSV export times out for our finance team. Please keep the date filters when we retry.";
  await addFeedback(page, text);
  await expect(
    page.getByRole("heading", { name: "Feedback #25", exact: true })
  ).toBeVisible();
  await expect(page.getByText(text, { exact: true }).first()).toBeVisible();
  await page
    .getByRole("link", { name: "Back to feedback", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Feedback", exact: true })
  ).toBeVisible();
  const created = page.getByRole("link", {
    name: "Open feedback 25",
    exact: true,
  });
  await expect(created).toBeVisible();
  await created.click();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Feedback #25", exact: true })
  ).toBeVisible();
  await expect(page.getByText(text, { exact: true }).first()).toBeVisible();
});
test("keyboard dialog dismissal restores focus and narrow pages do not overflow", async ({
  page,
}) => {
  await enterDemo(page);
  const add = page.getByRole("button", { name: "Add feedback", exact: true });
  await add.focus();
  await page.keyboard.press("Enter");
  const dialog = page.getByRole("dialog", {
    name: "Add feedback",
    exact: true,
  });
  await expect(dialog).toBeVisible();
  await dialog
    .getByRole("textbox", { name: "Customer feedback", exact: true })
    .fill("Keyboard-only review");
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(add).toBeFocused();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth
    )
  ).toBe(true);
  await feedbackLinks(page).first().click();
  await expect(
    page.getByRole("heading", { name: /^Feedback #\d+$/ })
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth
    )
  ).toBe(true);
  await expect(
    page.getByRole("button", { name: "Pause updates" })
  ).not.toBeVisible();
});
