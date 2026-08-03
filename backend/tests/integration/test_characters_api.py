"""Integration tests for the character CRUD lifecycle and derivation endpoints."""

from __future__ import annotations

from typing import Any

from httpx import AsyncClient

BASE = "/api/v1/characters"


def _fighter_body() -> dict[str, Any]:
    """A level-1 human fighter in scale mail and heavy shield (golden fixture 1)."""
    return {
        "name": "Aldous",
        "player_name": "Ana",
        "race": "humano",
        "racial_bonus_choices": {"Fue": 2},
        "base_scores": {"Fue": 15, "Des": 13, "Con": 14, "Int": 10, "Sab": 12, "Car": 8},
        "class_levels": [{"class_slug": "guerrero", "level": 1}],
        "armor": {"catalog_name": "Cota de escamas"},
        "shield": {"catalog_name": "Escudo pesado de acero"},
        "weapons": [{"catalog_name": "Espada larga", "wielding": "one_handed"}],
        "max_hp": 12,
        "current_hp": 12,
        "skill_ranks": {"intimidar": 1, "trepar": 1},
    }


async def test_crud_lifecycle(client: AsyncClient) -> None:
    created = await client.post(BASE, json=_fighter_body())
    assert created.status_code == 201
    character = created.json()
    cid = character["id"]
    assert character["name"] == "Aldous"
    assert character["created_at"] == character["updated_at"]

    fetched = await client.get(f"{BASE}/{cid}")
    assert fetched.status_code == 200
    assert fetched.json()["player_name"] == "Ana"

    replaced = await client.put(
        f"{BASE}/{cid}", json={**_fighter_body(), "name": "Aldous el Bravo"}
    )
    assert replaced.status_code == 200
    assert replaced.json()["name"] == "Aldous el Bravo"
    assert replaced.json()["id"] == cid

    deleted = await client.delete(f"{BASE}/{cid}")
    assert deleted.status_code == 204
    assert (await client.get(f"{BASE}/{cid}")).status_code == 404


async def test_create_defaults_to_level1_human_fighter(client: AsyncClient) -> None:
    created = await client.post(BASE, json={})
    assert created.status_code == 201
    body = created.json()
    assert body["race"] == "humano"
    assert body["class_levels"] == [
        {"class_slug": "guerrero", "level": 1, "is_prestige": False, "is_favored": False}
    ]


async def test_patch_is_partial(client: AsyncClient) -> None:
    cid = (await client.post(BASE, json=_fighter_body())).json()["id"]
    patched = await client.patch(f"{BASE}/{cid}", json={"current_hp": 5})
    assert patched.status_code == 200
    body = patched.json()
    assert body["current_hp"] == 5
    assert body["name"] == "Aldous"  # untouched
    assert body["max_hp"] == 12  # untouched


async def test_unknown_field_is_422(client: AsyncClient) -> None:
    response = await client.post(BASE, json={"totally_unknown": 1})
    assert response.status_code == 422


async def test_missing_character_paths_are_404(client: AsyncClient) -> None:
    missing = "00000000-0000-0000-0000-000000000000"
    assert (await client.get(f"{BASE}/{missing}")).status_code == 404
    assert (await client.put(f"{BASE}/{missing}", json=_fighter_body())).status_code == 404
    assert (await client.patch(f"{BASE}/{missing}", json={"name": "x"})).status_code == 404
    assert (await client.delete(f"{BASE}/{missing}")).status_code == 404
    assert (await client.post(f"{BASE}/{missing}/duplicate")).status_code == 404
    assert (await client.get(f"{BASE}/{missing}/combat-sheet")).status_code == 404


async def test_duplicate_creates_independent_copy(client: AsyncClient) -> None:
    cid = (await client.post(BASE, json=_fighter_body())).json()["id"]
    duplicated = await client.post(f"{BASE}/{cid}/duplicate")
    assert duplicated.status_code == 201
    copy = duplicated.json()
    assert copy["id"] != cid
    assert copy["name"] == "Aldous (copia)"


async def test_export_import_round_trip(client: AsyncClient) -> None:
    cid = (await client.post(BASE, json=_fighter_body())).json()["id"]
    exported = (await client.get(f"{BASE}/{cid}/export")).json()

    imported = await client.post(f"{BASE}/import", json=exported)
    assert imported.status_code == 201
    reimported = imported.json()

    # Same content, fresh identity.
    assert reimported["id"] != exported["id"]
    ignore = {"id", "created_at", "updated_at"}
    assert {k: v for k, v in reimported.items() if k not in ignore} == {
        k: v for k, v in exported.items() if k not in ignore
    }


async def test_list_pagination_and_search(client: AsyncClient) -> None:
    await client.post(BASE, json={**_fighter_body(), "name": "Borin"})
    await client.post(BASE, json={**_fighter_body(), "name": "Cira"})

    listing = await client.get(BASE, params={"limit": 1, "offset": 0})
    body = listing.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1
    assert body["limit"] == 1

    search = await client.get(BASE, params={"search": "Borin"})
    assert [item["name"] for item in search.json()["items"]] == ["Borin"]


async def test_combat_sheet_reproduces_known_values(client: AsyncClient) -> None:
    cid = (await client.post(BASE, json=_fighter_body())).json()["id"]
    sheet = (await client.get(f"{BASE}/{cid}/combat-sheet")).json()

    assert sheet["ac"]["total"] == 18
    assert sheet["ac"]["touch"] == 11
    assert sheet["ac"]["flat_footed"] == 17
    assert sheet["abilities"]["Fue"]["modifier"] == 3
    assert sheet["attacks"][0]["attack_line"] == "+4"
    assert sheet["attacks"][0]["damage_expression"] == "1d8+3"
    assert sheet["armor_check_penalty"] == -6
    assert sheet["warnings"] == []
    # Every AC line carries its source, so the number can be audited.
    labels = {entry["label"] for entry in sheet["ac"]["breakdown"]}
    assert {"base", "Cota de escamas", "Escudo pesado de acero"} <= labels


async def test_combat_sheet_suppression_is_surfaced(client: AsyncClient) -> None:
    body = _fighter_body()
    # Two deflection bonuses: the smaller must be reported as suppressed.
    body["modifiers"] = [
        {
            "target": "AC",
            "value": 1,
            "bonus_type": "deflexión",
            "source": "Escudo de fe",
            "source_kind": "spell",
        },
        {
            "target": "AC",
            "value": 2,
            "bonus_type": "deflexión",
            "source": "Anillo de protección +2",
            "source_kind": "item",
        },
    ]
    cid = (await client.post(BASE, json=body)).json()["id"]
    sheet = (await client.get(f"{BASE}/{cid}/combat-sheet")).json()

    suppressed = {entry["label"] for entry in sheet["ac"]["suppressed"]}
    assert "Escudo de fe" in suppressed


async def test_derive_is_stateless(client: AsyncClient) -> None:
    response = await client.post("/api/v1/derive", json=_fighter_body())
    assert response.status_code == 200
    assert response.json()["ac"]["total"] == 18
    # Nothing was persisted.
    assert (await client.get(BASE)).json()["total"] == 0
