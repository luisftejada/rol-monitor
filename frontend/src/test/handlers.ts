import { http, HttpResponse } from "msw";

import { fighterCharacter, fighterSheet, listResponse } from "./fixtures";

const BASE = "/api/v1";

/**
 * Default MSW handlers. Fixtures are typed against the generated OpenAPI models, so
 * a mock that drifts from the backend contract fails to compile.
 */
export const handlers = [
  http.get(`${BASE}/health`, () => HttpResponse.json({ status: "ok", version: "0.1.0" })),
  http.get(`${BASE}/characters`, () => HttpResponse.json(listResponse)),
  http.get(`${BASE}/characters/:id`, () => HttpResponse.json(fighterCharacter)),
  http.get(`${BASE}/characters/:id/combat-sheet`, () => HttpResponse.json(fighterSheet)),
  http.post(`${BASE}/characters/:id/duplicate`, () =>
    HttpResponse.json(fighterCharacter, { status: 201 }),
  ),
  http.delete(`${BASE}/characters/:id`, () => new HttpResponse(null, { status: 204 })),
  http.post(`${BASE}/derive`, () => HttpResponse.json(fighterSheet)),
];
