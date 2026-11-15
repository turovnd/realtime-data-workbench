import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import type { Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const offlineShell = (): Plugin => ({
  name: "offline-shell",
  apply: "build",
  writeBundle: async (options, bundle) => {
    const assets = Object.keys(bundle)
      .filter(file => file.startsWith("assets/"))
      .sort();
    const hash = createHash("sha256")
      .update(JSON.stringify(assets))
      .digest("hex")
      .slice(0, 16);
    const template = await readFile(
      new URL("./public/sw.js", import.meta.url),
      "utf8"
    );
    const serviceWorker = template
      .replace("__BUILD_HASH__", hash)
      .replace(
        '"__BUILD_ASSETS__"',
        assets.map(file => JSON.stringify(`/${file}`)).join(",")
      );
    const output = resolve(
      fileURLToPath(new URL(".", import.meta.url)),
      options.dir ?? "dist",
      "sw.js"
    );

    await writeFile(output, serviceWorker);
  },
});

export default defineConfig({
  plugins: [react(), tailwindcss(), offlineShell()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
});
