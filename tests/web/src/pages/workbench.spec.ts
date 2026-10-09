import { expect, test, type Page } from "@playwright/test";

const enterDemo = async (page: Page) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Try an isolated demo" }).click();
  await expect(
    page.getByRole("heading", { name: "Feedback stream", exact: true }),
  ).toBeVisible();
  await expect(page.getByText(/Showing 12 of 24 matching/)).toBeVisible();
};

test("filter, inspect and retry preserves source and fixed view", async ({
  page,
}) => {
  await enterDemo(page);
  await page.getByRole("radio", { name: "Needs attention" }).click();
  await expect(page.getByText(/Showing 2 of 2 matching/)).toBeVisible();
  await page
    .getByRole("button", { name: "Inspect feedback 9", exact: true })
    .click();
  const sheet = page.getByRole("dialog");
  await expect(sheet).toContainText(
    "The invoice download button returns an empty document.",
  );
  await page.getByRole("button", { name: "Retry this version" }).click();
  await expect(sheet).toContainText("Exact source evidence");
  await page.keyboard.press("Escape");
  await expect(sheet).not.toBeVisible();
  // Updating a job does not remove a row from the current frozen view.
  await expect(page.getByText(/Showing 2 of 2 matching/)).toBeVisible();
  await page.getByRole("button", { name: "Refresh view", exact: true }).click();
  await expect(page.getByText(/Showing 1 of 1 matching/)).toBeVisible();
});

test("backfill selection keeps original version and shareable filters", async ({
  page,
}) => {
  await enterDemo(page);
  await page
    .getByRole("checkbox", { name: "Select feedback 24", exact: true })
    .check();
  await page.getByRole("button", { name: "Run backfill" }).click();
  await expect(page.getByText("1 complete · 0 failed")).toBeVisible();
  await page
    .getByRole("button", { name: "Inspect feedback 24", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toContainText("Enrichment v2");
  await expect(page.getByRole("dialog")).toContainText("Enrichment v1");
  await page.keyboard.press("Escape");
  await page
    .getByRole("textbox", { name: "Search feedback" })
    .fill("no-results");
  await expect(page).toHaveURL(/q=no-results/);
  await expect(page.getByText("No feedback in this view")).toBeVisible();
  await expect(
    page.getByText("1 selected across this workspace", { exact: false }),
  ).toBeVisible();
});

test("load more, refetch and arrivals never duplicate or skip matching rows", async ({
  page,
}) => {
  await enterDemo(page);
  await page
    .getByRole("checkbox", { name: "Select feedback 24", exact: true })
    .check();
  await page.getByTestId("feedback-load-more").scrollIntoViewIfNeeded();
  await expect(page.getByText(/Showing 24 of 24 matching/)).toBeVisible();
  await page
    .getByRole("checkbox", { name: "Select feedback 1", exact: true })
    .check();
  const checkRows = async (count: number) => {
    const labels = await page
      .getByRole("button", { name: /^Inspect feedback \d+$/ })
      .evaluateAll((elements) =>
        elements.map((element) => element.getAttribute("aria-label")),
      );
    expect(labels).toHaveLength(count);
    expect(new Set(labels).size).toBe(count);
  };
  await checkRows(24);
  await page.getByRole("button", { name: "Add 12 live records" }).click();
  await expect(page.getByText(/Showing 12 of 36 matching/)).toBeVisible();
  await expect(
    page.getByText(/2 selected across this workspace/),
  ).toBeVisible();
  await page.getByTestId("feedback-load-more").scrollIntoViewIfNeeded();
  await expect(page.getByText(/Showing 24 of 36 matching/)).toBeVisible();
  await page.getByTestId("feedback-load-more").scrollIntoViewIfNeeded();
  await expect(page.getByText(/Showing 36 of 36 matching/)).toBeVisible();
  await checkRows(36);
  await expect(
    page.getByRole("checkbox", { name: "Select feedback 24", exact: true }),
  ).toBeChecked();
  await expect(
    page.getByRole("checkbox", { name: "Select feedback 1", exact: true }),
  ).toBeChecked();
  await page.getByRole("textbox", { name: "Search feedback" }).fill("billing");
  await expect(page.getByText(/Showing 3 of 3 matching/)).toBeVisible();
  await page.getByRole("textbox", { name: "Search feedback" }).fill("");
  await expect(page.getByText(/Showing 12 of 36 matching/)).toBeVisible();
});

test("offline snapshot survives navigation and logout clears private data", async ({
  page,
  context,
  isMobile,
}) => {
  await enterDemo(page);
  await page.getByRole("button", { name: "Save snapshot" }).click();
  await expect(page.getByText(/Snapshot saved/)).toBeVisible();
  await page.evaluate(async () => {
    await navigator.serviceWorker.ready;
  });
  await page.reload();
  await page.evaluate(async () => {
    await navigator.serviceWorker.ready;
  });
  await context.setOffline(true);
  await expect(
    page.getByText("Offline · read-only saved snapshot"),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Add 12 live records" }),
  ).toBeDisabled();
  await page.reload();
  await expect(
    page.getByText("Offline · read-only saved snapshot"),
  ).toBeVisible();
  await context.setOffline(false);
  await expect(
    page.getByRole("button", { name: "Add 12 live records" }),
  ).toBeEnabled();
  if (isMobile)
    await page.getByRole("button", { name: "Toggle Sidebar" }).click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Try an isolated demo" }),
  ).toBeVisible();
  expect(
    await page.evaluate(() =>
      Object.keys(localStorage).some((key) =>
        key.startsWith("feedback-desk-offline:"),
      ),
    ),
  ).toBe(false);
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Try an isolated demo" }),
  ).toBeVisible();
});

test("keyboard access and narrow viewport keep content usable", async ({
  page,
}) => {
  await enterDemo(page);
  await page.keyboard.press("ControlOrMeta+Home");
  await page.getByRole("link", { name: "Skip to feedback" }).focus();
  await expect(
    page.getByRole("link", { name: "Skip to feedback" }),
  ).toBeFocused();
  await page.getByRole("textbox", { name: "Search feedback" }).focus();
  await page.keyboard.type("billing");
  await expect(
    page.getByRole("button", { name: "Inspect feedback 4", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});

test("accessible manual paging works without an intersection observer", async ({
  page,
}) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "IntersectionObserver", { value: undefined });
  });
  await enterDemo(page);
  const button = page.getByRole("button", { name: "Load more feedback" });
  await button.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByText(/Showing 24 of 24 matching/)).toBeVisible();
});

test("stopping a backfill retains completed versions", async ({ page }) => {
  await enterDemo(page);
  await page
    .getByRole("checkbox", { name: "Select loaded feedback", exact: true })
    .check();
  await page.getByRole("button", { name: "Run backfill" }).click();
  await page.getByRole("button", { name: "Stop unfinished work" }).click();
  await expect(page.getByText("Stopped", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Stop unfinished work" }),
  ).not.toBeVisible();
  await page
    .getByRole("button", { name: "Inspect feedback 24", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toContainText("Enrichment v1");
});
