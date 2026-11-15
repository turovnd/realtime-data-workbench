import { expect } from "@playwright/test";

import {
  apiBase,
  bearer,
  disableAutomaticPaging,
  enterDemo,
  logout,
  test,
} from "../../../helpers/connected";

test("selected feedback is processed by the worker and its persisted result opens from Activity", async ({
  page,
}, testInfo) => {
  await disableAutomaticPaging(page);
  const demoRequest = page.waitForResponse(
    response =>
      new URL(response.url()).pathname === "/api/auth/demo" &&
      response.request().method() === "POST"
  );
  await enterDemo(page);
  const demoResponse = await demoRequest;
  expect(new URL(demoResponse.url()).origin).toBe(new URL(apiBase).origin);
  const authorization = await bearer(page);
  const response = await page.request.get(`${apiBase}/api/feedback?limit=1`, {
    headers: { Authorization: authorization },
  });
  expect(response.ok()).toBe(true);
  const firstPage = (await response.json()) as {
    records: { id: string; sequence: number; text: string }[];
  };
  const record = firstPage.records[0];
  const recordUrl = `${apiBase}/api/feedback/${record.id}`;

  await expect
    .poll(
      async () => {
        const result = await page.request.get(recordUrl, {
          headers: { Authorization: authorization },
        });
        const body = (await result.json()) as { jobs: { status: string }[] };
        return body.jobs.at(-1)?.status;
      },
      { timeout: 15000 }
    )
    .toBe("succeeded");

  await page
    .getByRole("checkbox", {
      name: `Select feedback ${record.sequence}`,
      exact: true,
    })
    .check();
  const analyze = page.getByRole("button", {
    name: "Analyze selected (1)",
    exact: true,
  });
  await expect(analyze).toBeEnabled({ timeout: 15000 });
  const admitted = page.waitForResponse(
    result =>
      new URL(result.url()).pathname === "/api/backfills" &&
      result.request().method() === "POST"
  );
  await analyze.click();
  const admission = await admitted;
  expect(admission.ok()).toBe(true);
  expect(new URL(admission.url()).origin).toBe(new URL(apiBase).origin);
  await testInfo.attach("connected-api-boundary", {
    body: JSON.stringify({
      configuredApi: apiBase,
      demoRequest: demoResponse.url(),
      backfillRequest: admission.url(),
    }),
    contentType: "application/json",
  });
  const batch = (await admission.json()) as { id: string };

  await expect
    .poll(
      async () => {
        const result = await page.request.get(
          `${apiBase}/api/backfills/${batch.id}`,
          {
            headers: { Authorization: authorization },
          }
        );
        expect(result.ok()).toBe(true);
        const body = (await result.json()) as {
          batch: { completed: number; failed: number };
        };
        expect(body.batch.failed).toBe(0);
        return body.batch.completed;
      },
      { timeout: 15000 }
    )
    .toBe(1);

  const persistedResponse = await page.request.get(recordUrl, {
    headers: { Authorization: authorization },
  });
  expect(persistedResponse.ok()).toBe(true);
  const persisted = (await persistedResponse.json()) as {
    text: string;
    jobs: {
      config: string;
      origin: string;
      status: string;
      provider: string;
    }[];
    outputs: { config: string; summary: string; provider: string }[];
  };
  const output = persisted.outputs.find(item => item.config === "v2");
  expect(persisted.text).toBe(record.text);
  expect(persisted.jobs).toEqual(
    expect.arrayContaining([
      expect.objectContaining({
        config: "v2",
        origin: "backfill",
        status: "succeeded",
      }),
    ])
  );
  expect(output).toBeDefined();

  await page.goto("/activity");
  const trigger = page.getByRole("button", {
    name: `View details for analysis run ${batch.id}`,
    exact: true,
  });
  await expect(trigger).toBeVisible();
  await trigger.focus();
  await page.keyboard.press("Enter");
  const item = page.getByRole("article", {
    name: `Feedback #${record.sequence}`,
    exact: true,
  });
  await expect(item.getByText(record.text, { exact: true })).toBeVisible();
  await expect(item.getByText(output!.summary, { exact: true })).toBeVisible();

  await page.reload();
  await page
    .getByRole("button", {
      name: `View details for analysis run ${batch.id}`,
      exact: true,
    })
    .click();
  await item
    .getByRole("link", {
      name: `Open feedback #${record.sequence}`,
      exact: true,
    })
    .click();
  await expect(page).toHaveURL(new RegExp(`/feedback/${record.id}$`));
  await expect(page.getByText(output!.summary, { exact: true })).toBeVisible();
  await logout(page);
});
