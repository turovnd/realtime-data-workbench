import { defineConfig, devices } from "@playwright/test";
const connected = process.env.PLAYWRIGHT_CONNECTED === "1";
export default defineConfig({
  testDir: "./tests/web/src/pages",
  outputDir: "./test-results",
  fullyParallel: !connected,
  workers: connected ? 1 : undefined,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI && !connected ? 1 : 0,
  reporter: "list",
  use: {
    baseURL: connected ? "http://127.0.0.1:5174" : "http://127.0.0.1:4174",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      testMatch: "workbench.spec.ts",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "mobile",
      testMatch: "workbench.spec.ts",
      use: { ...devices["Pixel 7"] },
    },
    {
      name: "connected",
      testMatch: "connected.spec.ts",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  ...(!connected || process.env.PLAYWRIGHT_START_WEB
    ? {
        webServer: {
          command: connected
            ? "pnpm dev"
            : "pnpm build && pnpm --dir web preview",
          url: connected ? "http://127.0.0.1:5174" : "http://127.0.0.1:4174",
          reuseExistingServer: !process.env.CI,
        },
      }
    : {}),
});
