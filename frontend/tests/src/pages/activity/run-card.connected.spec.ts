import { expect, test } from "@playwright/test";
import { enterActivity, mockActivity } from "../../../helpers/activity";

test("run cards load details only when expanded and keyboard navigation preserves each run's history", async ({
  page,
}) => {
  const fixture = await mockActivity(page);
  await enterActivity(page);
  const first = page.getByRole("button", {
    name: `View details for analysis run ${fixture.firstBatchId}`,
    exact: true,
  });
  const second = page.getByRole("button", {
    name: `View details for analysis run ${fixture.secondBatchId}`,
    exact: true,
  });
  await expect(first).toHaveAttribute("aria-expanded", "false");
  await expect(second).toHaveAttribute("aria-expanded", "false");
  expect(fixture.requests).toEqual([]);

  const release = fixture.holdDetails();
  await first.focus();
  await page.keyboard.press("Enter");
  await expect(first).toHaveAttribute("aria-expanded", "true");
  await expect.poll(() => fixture.requests.length).toBe(1);
  await expect(
    page.getByRole("status").filter({ hasText: "Loading run details" })
  ).toBeVisible();
  release();
  const details = page.getByRole("region", {
    name: "Analysis run details",
    exact: true,
  });
  const item = details.getByRole("article", {
    name: "Feedback #13",
    exact: true,
  });
  await expect(
    item.getByText(fixture.historicalSummary, { exact: true })
  ).toBeVisible();
  await expect(
    details.getByText(fixture.latestSummary, { exact: true })
  ).not.toBeVisible();
  await expect(
    details.getByText(fixture.otherSummary, { exact: true })
  ).not.toBeVisible();
  await expect(
    details
      .getByRole("article", { name: "Feedback #12", exact: true })
      .getByText(
        "The AI response did not match the required format. Try again.",
        { exact: true }
      )
  ).toBeVisible();

  await expect(
    details.getByText(
      "Provider output schema validation failed (summary: string_too_long)",
      { exact: true }
    )
  ).not.toBeVisible();

  await first.focus();
  await page.keyboard.press("Space");
  await expect(first).toHaveAttribute("aria-expanded", "false");
  await expect(details).not.toBeVisible();
  await second.focus();
  await page.keyboard.press("Enter");
  await expect(second).toHaveAttribute("aria-expanded", "true");
  await expect(
    details.getByText(fixture.otherSummary, { exact: true })
  ).toBeVisible();
  await expect(
    details.getByText(fixture.historicalSummary, { exact: true })
  ).not.toBeVisible();
  expect(fixture.requests.map(request => request.batchId)).toEqual([
    fixture.firstBatchId,
    fixture.secondBatchId,
  ]);
});

test("the full run summary toggles details while cancellation and feedback links remain independent", async ({
  page,
}) => {
  const fixture = await mockActivity(page, { running: true });
  await enterActivity(page);
  const trigger = page.getByRole("button", {
    name: `View details for analysis run ${fixture.firstBatchId}`,
    exact: true,
  });
  const count = await page
    .getByText("13 feedback messages", { exact: true })
    .boundingBox();
  expect(count).not.toBeNull();
  await page.mouse.click(
    count!.x + count!.width / 2,
    count!.y + count!.height / 2
  );
  await expect(trigger).toHaveAttribute("aria-expanded", "true");
  const progress = await page
    .getByRole("progressbar", { name: "Analysis progress" })
    .first()
    .boundingBox();
  expect(progress).not.toBeNull();
  await page.mouse.click(
    progress!.x + progress!.width / 2,
    progress!.y + progress!.height / 2
  );
  await expect(trigger).toHaveAttribute("aria-expanded", "false");
  await trigger.click({ position: { x: 8, y: 8 } });
  await expect(trigger).toHaveAttribute("aria-expanded", "true");
  await trigger.focus();
  await page.keyboard.press("Enter");
  await expect(trigger).toHaveAttribute("aria-expanded", "false");
  await page.keyboard.press("Space");
  await expect(trigger).toHaveAttribute("aria-expanded", "true");

  await expect(
    trigger.getByRole("button", { name: "Cancel run", exact: true })
  ).toHaveCount(0);
  await expect(trigger.getByRole("link")).toHaveCount(0);
  await page.getByRole("button", { name: "Cancel run", exact: true }).click();
  await expect
    .poll(() => fixture.cancellations)
    .toEqual([fixture.firstBatchId]);
  await expect(trigger).toHaveAttribute("aria-expanded", "true");
  await expect(page.getByText("Cancelled", { exact: true })).toBeVisible();
  const details = page.getByRole("region", {
    name: "Analysis run details",
    exact: true,
  });
  await expect(
    details.getByText(fixture.historicalSummary, { exact: true })
  ).toBeVisible();
  await details
    .getByRole("link", { name: "Open feedback #13", exact: true })
    .click();
  await expect(page).toHaveURL(
    new RegExp(`/feedback/${fixture.firstRecordId}$`)
  );
  await expect(
    page.getByRole("heading", { name: "Feedback #13", exact: true })
  ).toBeVisible();
});
