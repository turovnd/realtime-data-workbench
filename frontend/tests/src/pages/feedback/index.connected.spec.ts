import { expect } from "@playwright/test";
import {
  apiBase,
  enterDemo,
  bearer,
  disableAutomaticPaging,
  count,
  feedbackLinks,
  logout,
  test,
} from "../../../helpers/connected";

test("real cursor pages retain their view during arrivals and filters start a new cursor chain", async ({
  page,
}) => {
  await disableAutomaticPaging(page);
  const queries: URLSearchParams[] = [];
  page.on("request", request => {
    const url = new URL(request.url());
    if (url.pathname === "/api/feedback" && request.method() === "GET")
      queries.push(url.searchParams);
  });
  await enterDemo(page);
  await expect(count(page, 12, 24)).toBeVisible();
  const first = await feedbackLinks(page).evaluateAll(elements =>
    elements.map(element => element.getAttribute("aria-label"))
  );
  const inserted = await page.request.post(`${apiBase}/api/feedback`, {
    headers: { Authorization: await bearer(page) },
    data: {
      identity: crypto.randomUUID(),
      text: "The latest invoice is missing our billing address.",
      channel: "Support",
    },
  });
  expect(inserted.status()).toBe(201);
  await page.getByRole("button", { name: "Load more", exact: true }).click();
  await expect(count(page, 24, 24)).toBeVisible();
  const all = await feedbackLinks(page).evaluateAll(elements =>
    elements.map(element => element.getAttribute("aria-label"))
  );
  expect(all).toEqual(
    Array.from({ length: 24 }, (_, index) => `Open feedback ${24 - index}`)
  );
  expect(all.slice(0, 12)).toEqual(first);
  expect(new Set(all).size).toBe(24);
  expect(
    queries.some(query => query.get("cursor") && query.get("limit") === "12")
  ).toBe(true);
  queries.length = 0;
  await page.getByRole("textbox", { name: "Search feedback" }).fill("invoice");
  await expect(page).toHaveURL(/q=invoice/);
  await expect(count(page, 5, 5)).toBeVisible();
  expect(
    queries.some(
      query =>
        query.get("q") === "invoice" &&
        !query.has("cursor") &&
        query.get("limit") === "12"
    )
  ).toBe(true);
  await page.getByRole("textbox", { name: "Search feedback" }).fill("");
  await expect(count(page, 12, 25)).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Open feedback 25", exact: true })
  ).toBeVisible();
  await logout(page);
});
test("an expired cursor view has a working refresh action", async ({
  page,
}) => {
  await disableAutomaticPaging(page);
  await enterDemo(page);
  await expect(count(page, 12, 24)).toBeVisible();
  let injected = false;
  await page.route("**/api/feedback?**", async route => {
    if (
      !injected &&
      new URL(route.request().url()).searchParams.has("cursor")
    ) {
      injected = true;
      await route.fulfill({
        status: 410,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "This view expired. Refresh to open a current view.",
        }),
      });
    } else await route.continue();
  });
  await page.getByRole("button", { name: "Load more", exact: true }).click();
  await expect(
    page.getByText("This view expired. Refresh to open a current view.")
  ).toBeVisible();
  await page
    .getByRole("alert")
    .getByRole("button", { name: "Try again", exact: true })
    .click();
  await expect(
    page.getByText("This view expired. Refresh to open a current view.")
  ).not.toBeVisible();
  await expect(count(page, 12, 24)).toBeVisible();
  await page.getByRole("button", { name: "Load more", exact: true }).click();
  await expect(count(page, 24, 24)).toBeVisible();
  await logout(page);
});
