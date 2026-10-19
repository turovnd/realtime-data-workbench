import { expect, type Page } from "@playwright/test";

export const enterDemo = async (page: Page) => {
  await page.goto("/login");
  await page.getByRole("button", { name: "Try the demo", exact: true }).click();
  await expect(page).toHaveURL(/\/feedback$/);
  await expect(
    page.getByRole("heading", { name: "Feedback", exact: true })
  ).toBeVisible();
};

export const feedbackLinks = (page: Page) =>
  page.getByRole("link", { name: /^Open feedback \d+$/ });

export const expectCount = async (
  page: Page,
  loaded: number,
  total: number
) => {
  await expect(
    page.getByText(`Showing ${loaded} of ${total}`, { exact: true }).first()
  ).toBeVisible();
};

export const manualPaging = async (page: Page) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "IntersectionObserver", { value: undefined });
  });
};

export const addFeedback = async (page: Page, text: string) => {
  await page.getByRole("button", { name: "Add feedback", exact: true }).click();
  const dialog = page.getByRole("dialog", {
    name: "Add feedback",
    exact: true,
  });
  await dialog
    .getByRole("textbox", { name: "Customer feedback", exact: true })
    .fill(text);
  await dialog
    .getByRole("button", { name: "Save feedback", exact: true })
    .click();
  await expect(page).toHaveURL(/\/feedback\/[^/?]+/);
  await expect(dialog).not.toBeVisible();
};
