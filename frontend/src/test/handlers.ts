import { http, HttpResponse } from "msw";

import * as catalog from "./catalog";
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
  http.put(`${BASE}/characters/:id`, () => HttpResponse.json(fighterCharacter)),
  http.patch(`${BASE}/characters/:id`, () => HttpResponse.json(fighterCharacter)),
  http.post(`${BASE}/characters`, () => HttpResponse.json(fighterCharacter, { status: 201 })),
  http.post(`${BASE}/derive`, () => HttpResponse.json(fighterSheet)),

  // Combat tracking
  http.post(`${BASE}/characters/:id/modifiers`, () =>
    HttpResponse.json(fighterCharacter, { status: 201 }),
  ),
  http.patch(`${BASE}/characters/:id/modifiers/:mid`, () => HttpResponse.json(fighterCharacter)),
  http.delete(`${BASE}/characters/:id/modifiers/:mid`, () => HttpResponse.json(fighterCharacter)),
  http.post(`${BASE}/characters/:id/conditions`, () => HttpResponse.json(fighterCharacter)),
  http.post(`${BASE}/characters/:id/tick`, () => HttpResponse.json(fighterCharacter)),

  // Rules catalog
  http.get(`${BASE}/rules/meta`, () => HttpResponse.json(catalog.meta)),
  http.get(`${BASE}/rules/races`, () => HttpResponse.json(catalog.races)),
  http.get(`${BASE}/rules/classes`, () => HttpResponse.json(catalog.classes)),
  http.get(`${BASE}/rules/skills`, () => HttpResponse.json(catalog.skills)),
  http.get(`${BASE}/rules/feats`, () => HttpResponse.json(catalog.feats)),
  http.get(`${BASE}/rules/weapons`, () => HttpResponse.json(catalog.weapons)),
  http.get(`${BASE}/rules/armor`, () => HttpResponse.json(catalog.armor)),
  http.get(`${BASE}/rules/conditions`, () => HttpResponse.json(catalog.conditions)),
];
