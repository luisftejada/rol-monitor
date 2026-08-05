"""Integration tests for the live combat-tracking endpoints."""

from __future__ import annotations

from typing import Any

from httpx import AsyncClient

BASE = "/api/v1/characters"


async def _create(client: AsyncClient) -> str:
    response = await client.post(BASE, json={"name": "Combatiente"})
    return response.json()["id"]


def _bless() -> dict[str, Any]:
    return {
        "target": "ALL_ATTACKS",
        "value": 1,
        "bonus_type": "moral",
        "source": "Bendecir",
        "source_kind": "spell",
        "expires_in_rounds": 3,
    }


async def test_add_and_remove_modifier(client: AsyncClient) -> None:
    cid = await _create(client)

    added = await client.post(f"{BASE}/{cid}/modifiers", json=_bless())
    assert added.status_code == 201
    modifiers = added.json()["modifiers"]
    assert len(modifiers) == 1
    modifier_id = modifiers[0]["id"]
    assert modifiers[0]["source"] == "Bendecir"

    removed = await client.request("DELETE", f"{BASE}/{cid}/modifiers/{modifier_id}")
    assert removed.status_code == 200
    assert removed.json()["modifiers"] == []


async def test_remove_unknown_modifier_is_404(client: AsyncClient) -> None:
    cid = await _create(client)
    response = await client.request("DELETE", f"{BASE}/{cid}/modifiers/nope")
    assert response.status_code == 404


async def test_patch_modifier_toggles_active(client: AsyncClient) -> None:
    cid = await _create(client)
    modifier_id = (await client.post(f"{BASE}/{cid}/modifiers", json=_bless())).json()["modifiers"][
        0
    ]["id"]

    patched = await client.patch(f"{BASE}/{cid}/modifiers/{modifier_id}", json={"is_active": False})
    assert patched.status_code == 200
    assert patched.json()["modifiers"][0]["is_active"] is False


async def test_apply_and_remove_condition(client: AsyncClient) -> None:
    cid = await _create(client)

    applied = await client.post(f"{BASE}/{cid}/conditions", json={"condition": "fatigado"})
    assert applied.status_code == 200
    assert applied.json()["active_conditions"] == ["fatigado"]

    # Applying the same condition twice does not duplicate it.
    again = await client.post(f"{BASE}/{cid}/conditions", json={"condition": "fatigado"})
    assert again.json()["active_conditions"] == ["fatigado"]

    removed = await client.post(
        f"{BASE}/{cid}/conditions", json={"condition": "fatigado", "active": False}
    )
    assert removed.json()["active_conditions"] == []


async def test_condition_affects_combat_sheet(client: AsyncClient) -> None:
    cid = await _create(client)
    before = (await client.get(f"{BASE}/{cid}/combat-sheet")).json()
    await client.post(f"{BASE}/{cid}/conditions", json={"condition": "fatigado"})
    after = (await client.get(f"{BASE}/{cid}/combat-sheet")).json()
    # Fatigued applies -2 Strength and -2 Dexterity, lowering the scores.
    assert after["abilities"]["Fue"]["score"] == before["abilities"]["Fue"]["score"] - 2


async def test_tick_expires_timed_modifiers(client: AsyncClient) -> None:
    cid = await _create(client)
    await client.post(f"{BASE}/{cid}/modifiers", json=_bless())  # expires in 3 rounds

    after_two = await client.post(f"{BASE}/{cid}/tick", json={"rounds": 2})
    assert after_two.json()["modifiers"][0]["expires_in_rounds"] == 1

    after_more = await client.post(f"{BASE}/{cid}/tick", json={"rounds": 1})
    assert after_more.json()["modifiers"] == []


async def test_tick_leaves_permanent_modifiers(client: AsyncClient) -> None:
    cid = await _create(client)
    permanent = {**_bless(), "source": "Anillo", "expires_in_rounds": None}
    await client.post(f"{BASE}/{cid}/modifiers", json=permanent)

    ticked = await client.post(f"{BASE}/{cid}/tick", json={"rounds": 5})
    assert len(ticked.json()["modifiers"]) == 1


async def test_combat_endpoints_404_for_missing_character(client: AsyncClient) -> None:
    missing = "00000000-0000-0000-0000-000000000000"
    assert (await client.post(f"{BASE}/{missing}/tick", json={"rounds": 1})).status_code == 404
    assert (
        await client.post(f"{BASE}/{missing}/conditions", json={"condition": "cegado"})
    ).status_code == 404
    assert (await client.post(f"{BASE}/{missing}/modifiers", json=_bless())).status_code == 404
