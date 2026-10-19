import { expect, test as base, type Page } from "@playwright/test";

export const apiBase =
  process.env.PLAYWRIGHT_API_URL ?? "http://127.0.0.1:8002";
export const password = "feedback-test-password-2026";

export const expectInbox = async (page: Page) => {
  await expect(
    page.getByRole("heading", { name: "Feedback", exact: true })
  ).toBeVisible();
};

export const enterDemo = async (page: Page) => {
  await page.goto("/login");
  await page.getByRole("button", { name: "Try the demo", exact: true }).click();
  await expectInbox(page);
};

export const bearer = async (page: Page) =>
  page.evaluate(() => {
    const key = Object.keys(sessionStorage).find(value =>
      value.startsWith("feedback-desk-auth:")
    );
    if (!key) throw new Error("Missing test session");
    const session = JSON.parse(sessionStorage.getItem(key)!) as {
      token: string;
    };
    return `Bearer ${session.token}`;
  });

export const disableAutomaticPaging = async (page: Page) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "IntersectionObserver", { value: undefined });
  });
};

export const count = (page: Page, loaded: number, total: number) =>
  page.getByText(`Showing ${loaded} of ${total}`, { exact: true }).first();

export const feedbackLinks = (page: Page) =>
  page.getByRole("link", { name: /^Open feedback \d+$/ });

export const customerMessage = (page: Page, text: string) =>
  page.getByRole("blockquote").filter({ hasText: text }).first();

export const logout = async (page: Page) => {
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true })
  ).toBeVisible();
};

export const test = base.extend<{ sessionCleanup: void }>({
  sessionCleanup: [
    async ({ page }, use) => {
      await use();
      const authorization = await bearer(page).catch(() => null);
      if (authorization) {
        await page.request.post(`${apiBase}/api/auth/logout`, {
          headers: { Authorization: authorization },
          data: {},
        });
      }
    },
    { auto: true },
  ],
});
