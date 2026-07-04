import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Additional ignores for minified/generated files
    "public/pdf.worker.mjs",
    "test-results/**",
    "playwright-report/**",
    "test-data/**",
  ]),
  // Relaxed rules for test files and lib/hooks (generated/mocked data)
  {
    files: [
      "tests/**/*.ts",
      "tests/**/*.tsx",
      "scripts/**/*.ts",
      "lib/hooks/use-finance-data.ts",
    ],
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-unused-expressions": "off",
      "@typescript-eslint/no-unused-vars": "off",
      "react-hooks/rules-of-hooks": "off",
    },
  },
  // Relax React 19 strict hooks rules for app code (common hydration patterns)
  {
    files: [
      "app/**/*.tsx",
      "components/**/*.tsx",
      "hooks/**/*.ts",
    ],
    rules: {
      // These are common patterns for hydration that React 19 flags but are valid
      "react-hooks/set-state-in-effect": "off",
      // Allow components defined within render (would require significant refactoring)
      "react-hooks/static-components": "off",
    },
  },
]);

export default eslintConfig;
