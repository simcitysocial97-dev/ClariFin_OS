import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import eslintConfigPrettier from "eslint-config-prettier";

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
  ]),
  // 🔥 Enterprise Strict Rule Set & Prettier Integration
  {
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": ["error", {
        "argsIgnorePattern": "^_",
        "varsIgnorePattern": "^_"
      }],
      "@typescript-eslint/consistent-type-imports": ["error", {
        "prefer": "type-imports"
      }],
      "no-console": ["warn", { "allow": ["warn", "error"] }],
      "react-hooks/exhaustive-deps": "error"
    }
  },
  // Must be the last item in the array to safely override formatting rules
  eslintConfigPrettier,
]);

export default eslintConfig;
