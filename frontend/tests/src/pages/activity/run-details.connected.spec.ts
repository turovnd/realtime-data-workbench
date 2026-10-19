import { expect, test } from "@playwright/test";
import { enterActivity, mockActivity } from "../../../helpers/activity";

test("expanded run results paginate with a cursor and open the correct feedback page", async ({
  page,
}) => {
  const fixture = await mockActivity(page);
  await enterActivity(page);
  await page
    .getByRole("button", {
      name: `View details for analysis run ${fixture.firstBatchId}`,
      exact: true,
    })
    .click();
  const details = page.getByRole("region", {
    name: "Analysis run details",
    exact: true,
  });
  await expect(details.getByRole("article")).toHaveCount(10);
  expect(fixture.requests[0]).toEqual({
    batchId: fixture.firstBatchId,
    cursor: null,
    limit: 10,
  });
  const more = details.getByRole("button", {
    name: "Load more messages",
    exact: true,
  });
  await expect(more).toBeEnabled();
  // Focus without scrolling keeps the automatic observer out of this manual fallback check.
  await more.evaluate(element =>
    (element as HTMLButtonElement).focus({ preventScroll: true })
  );
  await page.keyboard.press("Enter");
  await expect(details.getByRole("article")).toHaveCount(13);
  expect(fixture.requests[1]).toEqual({
    batchId: fixture.firstBatchId,
    cursor: "fixture-batch.next",
    limit: 10,
  });
  await expect(more).not.toBeVisible();
  expect(
    await details
      .getByRole("article")
      .evaluateAll(elements =>
        elements.map(element => element.getAttribute("aria-label"))
      )
  ).toEqual(
    Array.from({ length: 13 }, (_, index) => `Feedback #${13 - index}`)
  );
  await details
    .getByRole("link", { name: "Open feedback #13", exact: true })
    .click();
  await expect(page).toHaveURL(
    new RegExp(`/feedback/${fixture.firstRecordId}$`)
  );
  await expect(
    page.getByRole("heading", { name: "Feedback #13", exact: true })
  ).toBeVisible();
  await expect(
    page.getByText(fixture.latestSummary, { exact: true })
  ).toBeVisible();
  await expect(
    page.getByText(fixture.historicalSummary, { exact: true })
  ).not.toBeVisible();
});

test("a failed run-details request keeps the card expanded and can be retried", async ({
  page,
}) => {
  const fixture = await mockActivity(page);
  fixture.setDetailsUnavailable(true);
  await enterActivity(page);
  const trigger = page.getByRole("button", {
    name: `View details for analysis run ${fixture.firstBatchId}`,
    exact: true,
  });
  await trigger.click();
  const details = page.getByRole("region", {
    name: "Analysis run details",
    exact: true,
  });
  await expect(
    details.getByRole("alert").filter({ hasText: "Couldn’t load run details" })
  ).toBeVisible({ timeout: 15000 });
  await expect(trigger).toHaveAttribute("aria-expanded", "true");
  await expect(details.getByRole("article")).toHaveCount(0);
  fixture.setDetailsUnavailable(false);
  await details.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(
    details.getByText(fixture.historicalSummary, { exact: true })
  ).toBeVisible();
  await expect(
    details.getByRole("alert").filter({ hasText: "Couldn’t load run details" })
  ).not.toBeVisible();
  await expect(trigger).toHaveAttribute("aria-expanded", "true");
  expect(
    fixture.requests.every(
      request =>
        request.batchId === fixture.firstBatchId && request.cursor === null
    )
  ).toBe(true);
});

test("an expired next-page cursor refreshes the run before continuing without duplicate messages", async ({
  page,
}) => {
  const fixture = await mockActivity(page);
  await enterActivity(page);
  await page
    .getByRole("button", {
      name: `View details for analysis run ${fixture.firstBatchId}`,
      exact: true,
    })
    .click();
  const details = page.getByRole("region", {
    name: "Analysis run details",
    exact: true,
  });
  const more = details.getByRole("button", {
    name: "Load more messages",
    exact: true,
  });
  await expect(details.getByRole("article")).toHaveCount(10);
  fixture.expireCursor();
  await more.evaluate(element =>
    (element as HTMLButtonElement).focus({ preventScroll: true })
  );
  await page.keyboard.press("Enter");
  const error = details
    .getByRole("alert")
    .filter({ hasText: "Couldn’t load run details" });
  await expect(error).toBeVisible();
  await expect(details.getByRole("article")).toHaveCount(10);
  await expect(
    details.getByText(fixture.historicalSummary, { exact: true })
  ).toBeVisible();
  await error.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(error).not.toBeVisible();
  expect(fixture.requests.slice(0, 3).map(request => request.cursor)).toEqual([
    null,
    "fixture-batch.next",
    null,
  ]);
  await more.evaluate(element =>
    (element as HTMLButtonElement).focus({ preventScroll: true })
  );
  await page.keyboard.press("Enter");
  await expect(details.getByRole("article")).toHaveCount(13);
  expect(fixture.requests.at(-1)?.cursor).toBe("fixture-batch.renewed");
  expect(
    await details
      .getByRole("article")
      .evaluateAll(elements =>
        elements.map(element => element.getAttribute("aria-label"))
      )
  ).toEqual(
    Array.from({ length: 13 }, (_, index) => `Feedback #${13 - index}`)
  );
});
