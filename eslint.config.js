import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";

const publicImports = {
  meta: {
    type: "problem",
    schema: [],
    messages: {
      deep: "Import through a public barrel with at most two segments after @/.",
    },
  },
  create(context) {
    const check = node => {
      const source = node.source;
      if (
        typeof source?.value === "string" &&
        source.value.startsWith("@/") &&
        source.value.slice(2).split("/").length > 2
      ) {
        context.report({ node: source, messageId: "deep" });
      }
    };

    return {
      ImportDeclaration: check,
      ExportNamedDeclaration: check,
      ExportAllDeclaration: check,
      ImportExpression: check,
    };
  },
};

export default tseslint.config(
  {
    ignores: [
      "**/dist/**",
      "**/node_modules/**",
      "**/playwright-report/**",
      "**/test-results/**",
      "frontend/src/api/generated.ts",
    ],
  },
  js.configs.recommended,
  {
    files: ["frontend/public/sw.js"],
    languageOptions: { globals: globals.serviceworker },
  },
  {
    files: ["tools/**/*.mjs"],
    languageOptions: { globals: globals.node },
  },
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: { globals: globals.browser },
    plugins: { "react-hooks": reactHooks, "react-refresh": reactRefresh },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
    },
  },
  {
    files: ["frontend/src/**/*.{ts,tsx}"],
    plugins: { local: { rules: { "public-imports": publicImports } } },
    rules: { "local/public-imports": "error" },
  },
  {
    files: ["frontend/src/components/ui/**/*.{ts,tsx}"],
    rules: {
      "react-refresh/only-export-components": "off",
      "local/public-imports": "off",
    },
  }
);
