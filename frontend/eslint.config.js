import { FlatCompat } from "@eslint/eslintrc";
import { dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const config = [
  // Ignore Next.js build output and dependencies
  {
    ignores: [".next/**", "node_modules/**", "out/**"],
  },
  // Apply config to JS/TS files
  ...compat.extends("next/core-web-vitals").map((config) => ({
    ...config,
    files: ["**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx"],
  })),
  {
    files: ["**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx"],
    rules: {
      "no-console": "warn",
    },
  },
];

export default config;
