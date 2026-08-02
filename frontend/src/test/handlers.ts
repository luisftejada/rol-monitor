import { http, HttpResponse } from "msw";

/**
 * Default MSW handlers. In later phases these are generated from the OpenAPI
 * schema so mocks cannot drift from the contract; for now the health probe is
 * enough to exercise the shell.
 */
export const handlers = [
  http.get("/api/v1/health", () => HttpResponse.json({ status: "ok", version: "0.1.0" })),
];
