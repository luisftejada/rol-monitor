import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { ApiError } from "@/api/client";
import {
  deleteCharacter,
  deriveCharacter,
  duplicateCharacter,
  getCharacters,
} from "@/api/characters";
import { fighterCharacter } from "@/test/fixtures";
import { server } from "@/test/server";

describe("characters API client", () => {
  it("derives a combat sheet from a draft (stateless)", async () => {
    const sheet = await deriveCharacter(fighterCharacter);
    expect(sheet.ac.total).toBe(18);
  });

  it("passes list params as query string", async () => {
    let seen = "";
    server.use(
      http.get("/api/v1/characters", ({ request }) => {
        seen = new URL(request.url).search;
        return HttpResponse.json({ items: [], total: 0, limit: 10, offset: 5 });
      }),
    );
    await getCharacters({ limit: 10, offset: 5, search: "ana" });
    expect(seen).toContain("limit=10");
    expect(seen).toContain("search=ana");
  });

  it("duplicates and deletes", async () => {
    const copy = await duplicateCharacter("char-1");
    expect(copy.id).toBe("char-1");
    await expect(deleteCharacter("char-1")).resolves.toBeUndefined();
  });

  it("raises ApiError on failure", async () => {
    server.use(http.get("/api/v1/characters", () => new HttpResponse(null, { status: 500 })));
    await expect(getCharacters()).rejects.toBeInstanceOf(ApiError);
  });
});
