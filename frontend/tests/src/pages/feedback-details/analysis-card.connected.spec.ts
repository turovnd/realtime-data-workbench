import { expect, test } from "@playwright/test";
import { mockAnalysis, openAnalysis } from "../../../helpers/analysis";

for (const provider of [
  "openrouter/test-provider",
  "deepseek/deepseek-flash",
]) {
  test(`${provider} failure preserves the last result and a retry can complete a fresh run`, async ({
    page,
  }) => {
    await page.clock.install();
    const fixture = await mockAnalysis(page, provider);
    await openAnalysis(page);
    await page
      .getByRole("button", { name: "Analyze with AI", exact: true })
      .click();
    await expect.poll(() => fixture.requests.length).toBe(1);
    await expect(
      page.getByRole("button", { name: "Queued…", exact: true })
    ).toBeDisabled();
    fixture.fail(
      "Provider evidence validation failed: quotes must match the original message exactly"
    );
    await page.clock.runFor(3100);
    await expect(
      page.getByRole("alert").filter({ hasText: "AI analysis failed" })
    ).toBeVisible();
    await expect(
      page.getByText(
        "The AI quotes did not match the original message. Try again.",
        {
          exact: true,
        }
      )
    ).toBeVisible();
    await expect(
      page.getByText(
        "Provider evidence validation failed: quotes must match the original message exactly",
        { exact: true }
      )
    ).not.toBeVisible();
    await expect(
      page.getByText(fixture.previousSummary, { exact: true })
    ).toBeVisible();
    await expect(
      page.getByText("Analysis complete", { exact: true })
    ).not.toBeVisible();
    await page.getByRole("button", { name: "Try again", exact: true }).click();
    await expect.poll(() => fixture.requests.length).toBe(2);
    expect(fixture.requests[1].identity).not.toBe(fixture.requests[0].identity);
    fixture.complete("A full-month selection makes exports freeze.");
    await page.clock.runFor(3100);
    await expect(
      page.getByText("A full-month selection makes exports freeze.", {
        exact: true,
      })
    ).toBeVisible();
    await expect(
      page.getByRole("alert").filter({ hasText: "AI analysis failed" })
    ).not.toBeVisible();
    await expect(
      page.getByRole("button", { name: "Analyze again", exact: true })
    ).toBeEnabled();
  });
}

test("an admission error is recoverable without losing the previous result or duplicating the request identity", async ({
  page,
}) => {
  await page.clock.install();
  const fixture = await mockAnalysis(page);
  await openAnalysis(page);
  fixture.rejectAdmission(
    503,
    "AI analysis is temporarily unavailable. Please try again."
  );
  await page
    .getByRole("button", { name: "Analyze with AI", exact: true })
    .click();
  await expect(
    page.getByRole("alert").filter({ hasText: "Couldn’t start AI analysis" })
  ).toBeVisible();
  await expect(
    page.getByText(fixture.previousSummary, { exact: true })
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Try again", exact: true })
  ).toBeEnabled();
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await expect.poll(() => fixture.requests.length).toBe(2);
  expect(fixture.requests[1].identity).toBe(fixture.requests[0].identity);
  await expect(
    page.getByRole("button", { name: "Queued…", exact: true })
  ).toBeDisabled();
  fixture.complete(
    "The export stops when the selected range covers an entire month."
  );
  await page.clock.runFor(3100);
  await expect(
    page.getByText(
      "The export stops when the selected range covers an entire month.",
      { exact: true }
    )
  ).toBeVisible();
  await expect(
    page.getByRole("alert").filter({ hasText: "Couldn’t start AI analysis" })
  ).not.toBeVisible();
});
