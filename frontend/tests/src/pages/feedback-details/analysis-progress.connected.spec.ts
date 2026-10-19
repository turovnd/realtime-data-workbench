import { expect, test } from "@playwright/test";
import { mockAnalysis, openAnalysis } from "../../../helpers/analysis";

test("analysis responds immediately, preserves old results and can continue beyond ten runs", async ({
  page,
}) => {
  await page.clock.install();
  const fixture = await mockAnalysis(page);
  await openAnalysis(page);
  await expect(
    page
      .getByRole("region", { name: "Analysis result", exact: true })
      .getByText("Sample analysis", { exact: true })
  ).toBeVisible();
  const release = fixture.holdAdmission();
  await page
    .getByRole("button", { name: "Analyze with AI", exact: true })
    .click();
  await expect.poll(() => fixture.requests.length).toBe(1);
  await expect(
    page.getByRole("button", { name: "Starting…", exact: true })
  ).toBeDisabled();
  await expect(
    page.getByRole("status").filter({ hasText: "Starting AI analysis" })
  ).toBeVisible();
  await expect(
    page.getByText("Previous result", { exact: true })
  ).toBeVisible();
  await expect(
    page.getByText(fixture.previousSummary, { exact: true })
  ).toBeVisible();
  await expect(
    page.getByText("Analysis complete", { exact: true })
  ).not.toBeVisible();
  await page.clock.runFor(2100);
  await expect(page.getByText(/[1-9]\d* s elapsed/)).toBeVisible();
  expect(fixture.requests).toHaveLength(1);

  const admitted = page.waitForResponse(response =>
    new URL(response.url()).pathname.endsWith("/analysis")
  );
  release();
  await admitted;
  await expect(
    page.getByRole("button", { name: "Queued…", exact: true })
  ).toBeDisabled();
  await expect(
    page.getByRole("status").filter({ hasText: "Waiting for AI" })
  ).toBeVisible();
  await expect(
    page.getByText("Previous result", { exact: true })
  ).toBeVisible();

  fixture.processing();
  await page.clock.runFor(3100);
  await expect(
    page.getByRole("button", { name: "Analyzing…", exact: true })
  ).toBeDisabled();
  await expect(
    page
      .getByRole("status")
      .filter({ hasText: "AI is analyzing your feedback" })
  ).toBeVisible();
  await expect(
    page.getByText(fixture.previousSummary, { exact: true })
  ).toBeVisible();

  const summary =
    "Monthly exports freeze when the customer includes a full month of feedback.";
  fixture.complete(summary);
  await page.clock.runFor(3100);
  await expect(
    page.getByRole("status").filter({ hasText: "Analysis complete" })
  ).toBeVisible();
  await expect(page.getByText(summary, { exact: true })).toBeVisible();
  await expect(
    page.getByText(fixture.previousSummary, { exact: true })
  ).not.toBeVisible();
  await expect(
    page.getByText("Previous result", { exact: true })
  ).not.toBeVisible();
  await expect(
    page
      .getByRole("region", { name: "Analysis result", exact: true })
      .getByText("AI analysis", { exact: true })
  ).toBeVisible();

  await page
    .getByRole("button", { name: "Analyze again", exact: true })
    .click();
  await expect.poll(() => fixture.requests.length).toBe(2);
  expect(fixture.requests[1].identity).not.toBe(fixture.requests[0].identity);
  await expect(
    page.getByText("Previous result", { exact: true })
  ).toBeVisible();
  await expect(page.getByText(summary, { exact: true })).toBeVisible();
  fixture.complete(
    "The customer reports that full-month exports cannot finish."
  );
  await page.clock.runFor(3100);
  await expect(
    page.getByRole("button", { name: "Analyze again", exact: true })
  ).toBeEnabled();

  for (let run = 5; run <= 11; run++) {
    const admitted = page.waitForResponse(response =>
      new URL(response.url()).pathname.endsWith("/analysis")
    );
    await page
      .getByRole("button", { name: "Analyze again", exact: true })
      .click();
    const response = await admitted;
    if (run === 11) {
      const body = await response.json();
      expect(body.jobs).toHaveLength(10);
      expect(body.jobs.at(-1).run).toBe(11);
      expect(body.outputs).toHaveLength(10);
      expect(body.outputs.at(-1).run).toBe(10);
    }
    const summary = `Analysis ${run}: full-month exports cannot finish.`;
    fixture.complete(summary);
    await page.clock.runFor(3100);
    await expect(page.getByText(summary, { exact: true })).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Analyze again", exact: true })
    ).toBeEnabled();
  }
  expect(fixture.requests).toHaveLength(9);
  expect(new Set(fixture.requests.map(request => request.identity)).size).toBe(
    9
  );
});

test("a delayed analysis response cannot replace another session's inbox or result", async ({
  page,
}) => {
  await page.clock.install();
  const fixture = await mockAnalysis(page);
  await openAnalysis(page);
  const privateText = fixture.originalText();
  const release = fixture.holdAdmission();
  await page
    .getByRole("button", { name: "Analyze with AI", exact: true })
    .click();
  await expect.poll(() => fixture.requests.length).toBe(1);
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.getByRole("button", { name: "Try the demo", exact: true }).click();
  await expect(page).toHaveURL(/\/feedback$/);
  const secondId = fixture.id();
  const admitted = page.waitForResponse(response =>
    new URL(response.url()).pathname.endsWith("/analysis")
  );
  release();
  await admitted;
  await page.clock.runFor(3100);
  await expect(page).toHaveURL(/\/feedback$/);
  await expect(page.getByText(privateText, { exact: true })).not.toBeVisible();
  await page
    .getByRole("link", { name: "Open feedback 1", exact: true })
    .click();
  await expect(page).toHaveURL(new RegExp(`/feedback/${secondId}$`));
  await expect(
    page.getByRole("button", { name: "Analyze with AI", exact: true })
  ).toBeEnabled();
  await expect(
    page.getByText("Previous result", { exact: true })
  ).not.toBeVisible();
  await expect(page.getByText(privateText, { exact: true })).not.toBeVisible();
});
