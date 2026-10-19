import { expect } from "@playwright/test";
import {
  apiBase,
  expectInbox,
  enterDemo,
  bearer,
  count,
  customerMessage,
  logout,
  test,
} from "../../../helpers/connected";

test("changing sessions cannot expose a prior workspace's record through its deep link", async ({
  page,
}) => {
  await enterDemo(page);
  const privateText = `Private customer message ${crypto.randomUUID()}`;
  const authorization = await bearer(page);
  const created = await page.request.post(`${apiBase}/api/feedback`, {
    headers: { Authorization: authorization },
    data: {
      identity: crypto.randomUUID(),
      text: privateText,
      channel: "Support",
    },
  });
  expect(created.status()).toBe(201);
  const record = (await created.json()) as { id: string };
  const path = `/feedback/${record.id}`;
  await page.goto(path);
  await expect(customerMessage(page, privateText)).toBeVisible();
  await logout(page);
  await page.getByRole("button", { name: "Try the demo", exact: true }).click();
  await expectInbox(page);
  await page.goto(path);
  await expect(page.getByText(/not found/i).first()).toBeVisible();
  await expect(customerMessage(page, privateText)).not.toBeVisible();
  const foreign = await page.request.get(
    `${apiBase}/api/feedback/${record.id}`,
    { headers: { Authorization: await bearer(page) } }
  );
  expect(foreign.status()).toBe(404);
  await page.reload();
  await expect(page.getByText(/not found/i).first()).toBeVisible();
  await page
    .getByRole("link", { name: "Back to feedback", exact: true })
    .click();
  await expect(count(page, 12, 24)).toBeVisible();
  await logout(page);
});
test("a delayed create response cannot navigate or populate a later demo session", async ({
  page,
}) => {
  await enterDemo(page);
  await page
    .getByRole("link", { name: "Open feedback 24", exact: true })
    .click();
  await page
    .getByRole("link", { name: "Back to feedback", exact: true })
    .click();
  await expectInbox(page);
  const privateText =
    "This pending message belongs only to the previous customer workspace.";
  let release!: () => void;
  const gate = new Promise<void>(resolve => {
    release = resolve;
  });
  let capturedId: string | undefined;
  await page.route("**/api/feedback", async route => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    const response = await route.fetch();
    expect(response.status()).toBe(201);
    capturedId = ((await response.json()) as { id: string }).id;
    await gate;
    await route.fulfill({ response });
  });
  await page.getByRole("button", { name: "Add feedback", exact: true }).click();
  const dialog = page.getByRole("dialog", {
    name: "Add feedback",
    exact: true,
  });
  await dialog
    .getByRole("textbox", { name: "Customer feedback", exact: true })
    .fill(privateText);
  await dialog
    .getByRole("button", { name: "Save feedback", exact: true })
    .click();
  await expect.poll(() => capturedId).toBeTruthy();
  await page.goBack();
  await expect(
    page.getByRole("heading", { name: "Feedback #24", exact: true })
  ).toBeVisible();
  await logout(page);
  await page.getByRole("button", { name: "Try the demo", exact: true }).click();
  await expectInbox(page);
  const authorization = await bearer(page);
  const nextStatus = page.waitForResponse(
    response => new URL(response.url()).pathname === "/api/status"
  );
  release();
  await nextStatus;
  await expect(page).toHaveURL(/\/feedback$/);
  await expect(count(page, 12, 24)).toBeVisible();
  await expect(customerMessage(page, privateText)).not.toBeVisible();
  expect(await bearer(page)).toBe(authorization);
  const response = await page.request.get(
    `${apiBase}/api/feedback/${capturedId}`,
    { headers: { Authorization: authorization } }
  );
  expect(response.status()).toBe(404);
  await logout(page);
});
