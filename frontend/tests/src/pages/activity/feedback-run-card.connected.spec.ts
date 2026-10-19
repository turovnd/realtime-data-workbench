import { expect, test } from "@playwright/test";
import { enterActivity, mockActivity } from "../../../helpers/activity";

test("new feedback appears while Activity is open and updates from queued to analyzed alongside manual analysis", async ({
  page,
}) => {
  await page.clock.install();
  const fixture = await mockActivity(page);
  await enterActivity(page);
  await expect(page.getByText("Showing 2 of 2 activities")).toBeVisible();

  fixture.addFeedback();
  await page.clock.runFor(3100);
  const added = page.getByRole("article", {
    name: "Feedback #15, run 1",
    exact: true,
  });
  await expect(added.getByText("Queued", { exact: true })).toBeVisible();
  await expect(
    added.getByText("New feedback · Support", { exact: true })
  ).toBeVisible();
  const trigger = added.getByRole("button", {
    name: "View details for feedback #15, run 1",
    exact: true,
  });
  const preview = await added
    .getByText("Search resets the selected channel when I open a message.", {
      exact: true,
    })
    .boundingBox();
  expect(preview).not.toBeNull();
  await page.mouse.click(
    preview!.x + preview!.width / 2,
    preview!.y + preview!.height / 2
  );
  await expect(trigger).toHaveAttribute("aria-expanded", "true");
  await expect(trigger.getByRole("link")).toHaveCount(0);
  await expect(
    added.getByText("The result will appear here when processing finishes.")
  ).toBeVisible();

  fixture.finishFeedback();
  await page.clock.runFor(3100);
  await expect(
    added.getByText("Analyzed", { exact: true }).first()
  ).toBeVisible();
  await expect(
    added.getByText("Opening a message resets the selected channel.", {
      exact: true,
    })
  ).toBeVisible();
  await expect(added.getByText("Queued", { exact: true })).not.toBeVisible();

  fixture.addManualAnalysis();
  await page.clock.runFor(3100);
  const manual = page.getByRole("article", {
    name: "Feedback #13, run 3",
    exact: true,
  });
  await expect(
    manual.getByText("Manual analysis · Support", { exact: true })
  ).toBeVisible();
  const manualTrigger = manual.getByRole("button", {
    name: "View details for feedback #13, run 3",
    exact: true,
  });
  await manualTrigger.focus();
  await page.keyboard.press("Enter");
  await expect(
    manual.getByText(fixture.latestSummary, { exact: true })
  ).toBeVisible();
  await expect(
    manual.getByText(fixture.historicalSummary, { exact: true })
  ).not.toBeVisible();
  await page.keyboard.press("Space");
  await expect(manualTrigger).toHaveAttribute("aria-expanded", "false");
  await page.keyboard.press("Enter");
  await manual
    .getByRole("link", { name: "Open feedback #13", exact: true })
    .click();
  await expect(page).toHaveURL(
    new RegExp(`/feedback/${fixture.firstRecordId}$`)
  );
});

test("a failed individual analysis shows its safe error without claiming completion or displaying another run's result", async ({
  page,
}) => {
  await page.clock.install();
  const fixture = await mockActivity(page);
  await enterActivity(page);
  await expect(page.getByText("Showing 2 of 2 activities")).toBeVisible();
  fixture.addFeedback();
  fixture.finishFeedback(true);
  await page.clock.runFor(3100);
  const failed = page.getByRole("article", {
    name: "Feedback #15, run 1",
    exact: true,
  });
  await expect(
    failed.getByText("Needs attention", { exact: true })
  ).toBeVisible();
  await failed
    .getByRole("button", {
      name: "View details for feedback #15, run 1",
      exact: true,
    })
    .click();
  await expect(
    failed.getByText(
      "The AI quotes did not match the original message. Try again.",
      { exact: true }
    )
  ).toBeVisible();
  await expect(failed.getByText("Analyzed", { exact: true })).not.toBeVisible();
  await expect(
    failed.getByText("Opening a message resets the selected channel.", {
      exact: true,
    })
  ).not.toBeVisible();
});

test("mixed activity pages remain complete and duplicate-free when new feedback arrives after loading another page", async ({
  page,
}) => {
  await page.clock.install();
  const fixture = await mockActivity(page, { standalone: true });
  await enterActivity(page);
  const triggers = page.getByRole("button", { name: /^View details for / });
  await expect(triggers).toHaveCount(10);
  const more = page.getByRole("button", {
    name: "Load more activity",
    exact: true,
  });
  await more.evaluate(element =>
    (element as HTMLButtonElement).focus({ preventScroll: true })
  );
  await page.keyboard.press("Enter");
  await expect(triggers).toHaveCount(15);
  await expect(page.getByText("Showing 15 of 15 activities")).toBeVisible();
  expect(fixture.activityRequests[0]).toEqual({ cursor: null, limit: 10 });
  expect(fixture.activityRequests[1].cursor).not.toBeNull();
  fixture.addFeedback();
  await page.clock.runFor(3100);
  await expect(triggers).toHaveCount(16);
  await expect(page.getByText("Showing 16 of 16 activities")).toBeVisible();
  const names = await triggers.evaluateAll(elements =>
    elements.map(element => element.getAttribute("aria-label"))
  );
  expect(new Set(names).size).toBe(16);
  expect(fixture.activityRequests.at(-2)?.cursor).toBeNull();
  expect(fixture.activityRequests.at(-1)?.cursor).not.toBe(
    fixture.activityRequests[1].cursor
  );
});

for (const status of [400, 410]) {
  test(`Activity recovers from a ${status} continuation by opening a fresh head`, async ({
    page,
  }) => {
    await page.clock.install();
    const fixture = await mockActivity(page, { standalone: true });
    await enterActivity(page);
    const triggers = page.getByRole("button", { name: /^View details for / });
    await expect(triggers).toHaveCount(10);
    fixture.expireActivityCursor(status);
    const more = page.getByRole("button", {
      name: "Load more activity",
      exact: true,
    });
    await more.evaluate(element =>
      (element as HTMLButtonElement).focus({ preventScroll: true })
    );
    await page.keyboard.press("Enter");
    const error = page
      .getByRole("alert")
      .filter({ hasText: "Couldn’t update activity" });
    await expect(error).toBeVisible();
    await expect(triggers).toHaveCount(10);
    await error.getByRole("button", { name: "Try again", exact: true }).click();
    await expect(error).not.toBeVisible();
    await expect(triggers).toHaveCount(10);
    expect(fixture.activityRequests.at(-1)?.cursor).toBeNull();
    await more.evaluate(element =>
      (element as HTMLButtonElement).focus({ preventScroll: true })
    );
    await page.keyboard.press("Enter");
    await expect(triggers).toHaveCount(15);
    expect(fixture.activityRequests.at(-1)?.cursor).not.toBe(
      fixture.activityRequests[1].cursor
    );
  });
}

test("a delayed Activity response cannot populate another workspace after sign-out", async ({
  page,
}) => {
  await page.clock.install();
  const fixture = await mockActivity(page, { standalone: true });
  const release = fixture.holdActivity();
  await enterActivity(page);
  await expect.poll(() => fixture.activityRequests.length).toBe(1);
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.getByRole("button", { name: "Try the demo", exact: true }).click();
  await expect(page).toHaveURL(/\/feedback$/);
  await page.goto("/activity");
  await expect(
    page.getByText("No analysis runs yet", { exact: true })
  ).toBeVisible();
  release();
  await page.clock.runFor(3100);
  await expect(
    page.getByText("No analysis runs yet", { exact: true })
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /^View details for / })
  ).toHaveCount(0);
  await expect(
    page.getByText(fixture.firstText, { exact: true })
  ).not.toBeVisible();
});
