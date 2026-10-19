import { expect, test } from "@playwright/test";

test("login and registration are separate destinations with the same usable entry", async ({
  page,
}) => {
  await page.goto("/register");
  await expect(page).toHaveURL(/\/register$/);
  await expect(
    page.getByRole("textbox", { name: "Email", exact: true })
  ).toBeVisible();
  await expect(page.getByLabel("Password", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Try the demo", exact: true })
  ).toBeVisible();
  await page.goto("/login");
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true })
  ).toBeVisible();
  await page.getByRole("button", { name: "Try the demo", exact: true }).click();
  await expect(page).toHaveURL(/\/feedback$/);
});
