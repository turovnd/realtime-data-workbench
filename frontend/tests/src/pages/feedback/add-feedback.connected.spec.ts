import { expect, test } from "@playwright/test";

import { mockSubmission } from "../../../helpers/submission";
import { enterDemo } from "../../../helpers/preview";

for (const [provider, provenance] of [
  ["openrouter/ui-test-model", "AI · ui-test-model · OpenRouter"],
  ["deepseek/deepseek-flash", "AI · deepseek-flash · DeepSeek"],
]) {
  test(`${provider} submission follows its automatic AI job through result, reload and Activity without a duplicate request`, async ({
    page,
  }) => {
    await page.clock.install();
    const fixture = await mockSubmission(page, provider);
    await enterDemo(page);
    await page
      .getByRole("button", { name: "Try an example", exact: true })
      .click();
    const dialog = page.getByRole("dialog", {
      name: "Add feedback",
      exact: true,
    });
    const input = dialog.getByRole("textbox", {
      name: "Customer feedback",
      exact: true,
    });
    const text = await input.inputValue();
    expect(text).toContain("merge the files by hand");
    await expect(
      dialog.getByText(/Submitting sends this text to our AI provider/)
    ).toBeVisible();
    await dialog
      .getByRole("button", { name: "Analyze feedback", exact: true })
      .click();
    await expect.poll(() => fixture.submissions.length).toBe(1);
    await expect(
      dialog.getByRole("button", { name: "Saving…", exact: true })
    ).toBeDisabled();
    expect(fixture.submissions[0].text).toBe(text);
    expect(fixture.submissions[0].identity).toBeTruthy();
    fixture.release();
    await expect(page).toHaveURL(
      /\/feedback\/00000000-0000-4000-8000-000000000025$/
    );
    await expect(
      page.getByRole("button", { name: "Queued…", exact: true })
    ).toBeDisabled();
    fixture.processing();
    await page.clock.runFor(3100);
    await expect(
      page
        .getByRole("status")
        .filter({ hasText: "AI is analyzing your feedback" })
    ).toBeVisible();
    const summary =
      "Full-month CSV exports fail despite fast weekly exports, forcing manual file merging before the product review.";
    const quote =
      "I now export one week at a time and merge the files by hand, which takes about half an hour.";
    expect(text).toContain(quote);
    fixture.complete(summary, [quote]);
    await page.clock.runFor(3100);
    await expect(
      page.getByRole("status").filter({ hasText: "Analysis complete" })
    ).toBeVisible();
    await expect(page.getByText(summary, { exact: true })).toBeVisible();
    await expect(page.getByText(`“${quote}”`, { exact: true })).toBeVisible();
    await expect(page.getByText(provenance, { exact: false })).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Analyze again", exact: true })
    ).toBeEnabled();
    expect(fixture.explicitAnalysisRequests).toEqual([]);
    await page.reload();
    await expect(page.getByText(summary, { exact: true })).toBeVisible();
    await page
      .getByRole("link", { name: "View activity", exact: true })
      .click();
    await expect(page).toHaveURL(/\/activity$/);
    await page
      .getByRole("button", {
        name: "View details for feedback #25, run 1",
        exact: true,
      })
      .click();
    const activity = page.getByRole("article", {
      name: "Feedback #25, run 1",
      exact: true,
    });
    await expect(activity.getByText(summary, { exact: true })).toBeVisible();
    await expect(activity.getByText(provenance, { exact: true })).toBeVisible();
    await expect(
      activity.getByText("Sample analysis", { exact: false })
    ).not.toBeVisible();
    expect(fixture.submissions).toHaveLength(1);
    expect(fixture.explicitAnalysisRequests).toEqual([]);
  });
}

test("unknown provider status blocks submission until availability is recovered", async ({
  page,
}) => {
  await page.clock.install();
  const fixture = await mockSubmission(page);
  fixture.setStatusAvailable(false);
  await enterDemo(page);
  await expect(
    page.getByRole("button", { name: "Try an example", exact: true })
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Add feedback", exact: true }).first()
  ).toBeDisabled();
  await page.clock.runFor(4100);
  await expect(
    page.getByRole("alert").filter({ hasText: "Analysis status unavailable" })
  ).toBeVisible();
  expect(fixture.submissions).toEqual([]);
  fixture.setStatusAvailable(true);
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await page
    .getByRole("button", { name: "Try an example", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Analyze feedback", exact: true })
  ).toBeEnabled();
  await expect(
    page.getByText(/Submitting sends this text to our AI provider/)
  ).toBeVisible();
});

for (const provider of ["", "unknown/model"]) {
  test(`unrecognized provider ${provider || "(empty)"} cannot offer a misleading submission`, async ({
    page,
  }) => {
    const fixture = await mockSubmission(page, provider);
    await enterDemo(page);
    await expect(
      page.getByRole("alert").filter({ hasText: "Analysis status unavailable" })
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Try an example", exact: true })
    ).toBeDisabled();
    await expect(
      page.getByRole("button", { name: "Add feedback", exact: true }).first()
    ).toBeDisabled();
    expect(fixture.submissions).toEqual([]);
  });
}
