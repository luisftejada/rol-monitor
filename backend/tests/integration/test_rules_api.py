"""Integration tests for the /rules/* catalog endpoints."""

from __future__ import annotations

from httpx import AsyncClient

BASE = "/api/v1/rules"


async def test_meta_endpoint(client: AsyncClient) -> None:
    response = await client.get(f"{BASE}/meta")
    assert response.status_code == 200
    body = response.json()
    assert "esquiva" in body["bonus_types"]["always_stack"]
    assert len(body["abilities"]) == 6
    assert len(body["sizes"]) == 9


async def test_meta_sets_cache_headers(client: AsyncClient) -> None:
    response = await client.get(f"{BASE}/meta")
    assert response.headers["cache-control"] == "public, max-age=3600"
    assert response.headers["etag"]


async def test_conditional_request_returns_304(client: AsyncClient) -> None:
    first = await client.get(f"{BASE}/meta")
    etag = first.headers["etag"]

    cached = await client.get(f"{BASE}/meta", headers={"If-None-Match": etag})
    assert cached.status_code == 304
    assert cached.headers["etag"] == etag
    assert cached.content == b""


async def test_etag_varies_by_query(client: AsyncClient) -> None:
    plain = await client.get(f"{BASE}/classes")
    with_prestige = await client.get(f"{BASE}/classes", params={"include_prestige": "true"})
    assert plain.headers["etag"] != with_prestige.headers["etag"]


async def test_races_endpoint(client: AsyncClient) -> None:
    response = await client.get(f"{BASE}/races")
    assert response.status_code == 200
    races = response.json()
    assert len(races) == 7
    assert {"slug", "name", "ability_modifiers", "languages"} <= races[0].keys()


async def test_classes_include_prestige(client: AsyncClient) -> None:
    base = await client.get(f"{BASE}/classes")
    combined = await client.get(f"{BASE}/classes", params={"include_prestige": "true"})
    assert len(base.json()) == 11
    assert len(combined.json()) == 21


async def test_class_progression_ok(client: AsyncClient) -> None:
    response = await client.get(f"{BASE}/classes/guerrero/progression/11")
    assert response.status_code == 200
    body = response.json()
    assert body["bab"] == "+11/+6/+1"
    assert body["bab_iteratives"] == [11, 6, 1]


async def test_class_progression_unknown_class_is_404(client: AsyncClient) -> None:
    response = await client.get(f"{BASE}/classes/noexiste/progression/1")
    assert response.status_code == 404


async def test_class_progression_bad_level_is_404(client: AsyncClient) -> None:
    response = await client.get(f"{BASE}/classes/guerrero/progression/99")
    assert response.status_code == 404


async def test_skills_endpoint(client: AsyncClient) -> None:
    response = await client.get(f"{BASE}/skills")
    assert response.status_code == 200
    assert len(response.json()) == 35


async def test_feats_eligibility_query(client: AsyncClient) -> None:
    response = await client.get(
        f"{BASE}/feats",
        params={"bab": 6, "abilities": ["Fue:15"], "type": "Combate"},
    )
    assert response.status_code == 200
    feats = response.json()
    assert feats
    acometer = next(f for f in feats if f["name"] == "Acometer")
    assert acometer["is_eligible"] is True


async def test_feats_default_shows_all_annotated(client: AsyncClient) -> None:
    response = await client.get(f"{BASE}/feats")
    feats = response.json()
    assert len(feats) == 174
    assert all("is_eligible" in f for f in feats)


async def test_feats_ignores_malformed_ability_params(client: AsyncClient) -> None:
    response = await client.get(
        f"{BASE}/feats",
        params={"abilities": ["garbage", "Fue:notanumber"]},
    )
    assert response.status_code == 200
    assert len(response.json()) == 174


async def test_weapons_search(client: AsyncClient) -> None:
    response = await client.get(f"{BASE}/weapons", params={"search": "espada lar"})
    assert response.status_code == 200
    assert [w["name"] for w in response.json()] == ["Espada larga"]


async def test_armor_category_filter(client: AsyncClient) -> None:
    response = await client.get(f"{BASE}/armor", params={"category": "pesada"})
    assert response.status_code == 200
    armor = response.json()
    assert armor
    assert all(a["category"] == "pesada" for a in armor)


async def test_conditions_endpoint(client: AsyncClient) -> None:
    response = await client.get(f"{BASE}/conditions")
    assert response.status_code == 200
    assert len(response.json()) == 34


async def test_spells_class_level_filter(client: AsyncClient) -> None:
    response = await client.get(f"{BASE}/spells", params={"class": "mago", "level": 3})
    assert response.status_code == 200
    spells = response.json()
    assert spells
    assert all(3 in s["levels"].values() for s in spells)
