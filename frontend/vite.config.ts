import { fileURLToPath, URL } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: false,
    // Must stay comfortably above `asyncUtilTimeout` in src/test/setup.ts. Both were
    // 5s — vitest's default and the one we raised — so a `findBy*` allowed to wait
    // the full five seconds consumed the entire budget of the test containing it,
    // and the outer cap fired before the inner wait could ever pay off. Under
    // `make check`, which runs this right after the backend suite and across every
    // core, that lost about half the runs.
    testTimeout: 20_000,
    hookTimeout: 20_000,
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/**/*.test.{ts,tsx}",
        "src/test/**",
        "src/api/schema.ts",
        "src/api/types.ts",
        "src/main.tsx",
      ],
      thresholds: { statements: 80, branches: 80, functions: 80, lines: 80 },
    },
  },
});
