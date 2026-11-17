import { expect } from "@playwright/test";
import {
  apiBase,
  password,
  expectInbox,
  enterDemo,
  bearer,
  disableAutomaticPaging,
  count,
  feedbackLinks,
  customerMessage,
  logout,
  test,
} from "../../../helpers/connected";

test("custom feedback persists through a direct reload and signing back into its account", async ({
  page,
}) => {
  const email = `feedback-${crypto.randomUUID()}@example.test`;
  const text =
    "Our finance team cannot export the monthly report. The CSV request times out after selecting the full month.";
  await page.goto("/register");
  await page.getByRole("textbox", { name: "Email", exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expectInbox(page);
  await expect(feedbackLinks(page)).toHaveCount(0);
  await page
    .getByRole("button", { name: "Add feedback", exact: true })
    .first()
    .click();
  const dialog = page.getByRole("dialog", {
    name: "Add feedback",
    exact: true,
  });
  await dialog
    .getByRole("textbox", { name: "Customer feedback", exact: true })
    .fill(text);
  await dialog.getByRole("combobox", { name: "Source", exact: true }).click();
  await page.getByRole("option", { name: "Community", exact: true }).click();
  await dialog
    .getByRole("button", { name: "Save feedback", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Feedback #1", exact: true })
  ).toBeVisible();
  await expect(customerMessage(page, text)).toBeVisible();
  const detailPath = new URL(page.url()).pathname;
  const id = detailPath.split("/").at(-1)!;
  const authorization = await bearer(page);
  await expect
    .poll(
      async () => {
        const response = await page.request.get(
          `${apiBase}/api/feedback/${id}`,
          { headers: { Authorization: authorization } }
        );
        expect(response.ok()).toBe(true);
        const result = (await response.json()) as {
          text: string;
          channel: string;
          outputs: unknown[];
        };
        expect(result.text).toBe(text);
        expect(result.channel).toBe("Community");
        return result.outputs.length;
      },
      { timeout: 15000 }
    )
    .toBeGreaterThan(0);
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Feedback #1", exact: true })
  ).toBeVisible();
  await expect(customerMessage(page, text)).toBeVisible();
  await logout(page);
  expect(
    await page.evaluate(() =>
      Object.keys(localStorage).filter(key =>
        key.startsWith("feedback-desk-offline:")
      )
    )
  ).toEqual([]);
  const revoked = await page.request.get(`${apiBase}/api/feedback/${id}`, {
    headers: { Authorization: authorization },
  });
  expect(revoked.status()).toBe(401);
  await page.goto(detailPath);
  await expect(page).toHaveURL(/\/login$/);
  await page.getByRole("textbox", { name: "Email", exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`${detailPath}$`));
  await expect(customerMessage(page, text)).toBeVisible();
  await page
    .getByRole("link", { name: "Back to feedback", exact: true })
    .click();
  await expectInbox(page);
  await expect(
    page.getByRole("link", { name: "Open feedback 1", exact: true })
  ).toBeVisible();
  await logout(page);
});
test("a record outside the loaded cursor page opens directly and survives reload", async ({
  page,
}) => {
  await disableAutomaticPaging(page);
  await enterDemo(page);
  await expect(count(page, 12, 24)).toBeVisible();
  const authorization = await bearer(page);
  const response = await page.request.get(`${apiBase}/api/feedback?limit=50`, {
    headers: { Authorization: authorization },
  });
  expect(response.ok()).toBe(true);
  const { records } = (await response.json()) as {
    records: { id: string; sequence: number; text: string }[];
  };
  const oldest = records.find(record => record.sequence === 1)!;
  expect(oldest).toBeTruthy();
  await expect(
    page.getByRole("link", { name: "Open feedback 1", exact: true })
  ).not.toBeVisible();
  await page.goto(`/feedback/${oldest.id}?q=invoice`);
  await expect(
    page.getByRole("heading", { name: "Feedback #1", exact: true })
  ).toBeVisible();
  await expect(customerMessage(page, oldest.text)).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Feedback #1", exact: true })
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Back to feedback", exact: true })
    .click();
  await expect(
    page.getByRole("textbox", { name: "Search feedback" })
  ).toHaveValue("invoice");
  await expect(count(page, 4, 4)).toBeVisible();
  await logout(page);
});
