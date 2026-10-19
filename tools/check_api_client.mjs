import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";

const files = ["openapi.json", "frontend/src/api/generated.ts"];
const expected = files.map(file => readFileSync(file, "utf8"));
const result = spawnSync("pnpm", ["api:generate"], { stdio: "inherit" });

if (result.error) throw result.error;
if (result.status !== 0) process.exit(result.status ?? 1);

files.forEach((file, index) => {
  assert.equal(
    readFileSync(file, "utf8"),
    expected[index],
    `${file} changed during generation. Regenerate and review the contract.`
  );
});

console.log("OpenAPI schema and generated client are reproducible.");
