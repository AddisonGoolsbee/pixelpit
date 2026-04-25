"""Unit tests for the target PixelPit MCP tool surface."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import Base, SessionLocal, engine, init_db
from app.mcp_server import (
    browse_art_board,
    buy_artwork,
    create_art,
    get_my_portfolio,
    inspect_artwork,
    list_artwork,
    register,
)
from app.models.agent_balance import AgentBalance
from app.models.ledger import LedgerEntry


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)


DUMMY_ART = json.dumps([["00FF00"] * 100] * 100)


def _register(name: str) -> dict:
    return json.loads(register(name))


def test_register_new_agent():
    result = _register("Alice")
    assert "credential" in result
    assert result["name"] == "Alice"
    assert result["kroons"] == 1000


def test_register_duplicate_name_returns_existing():
    first = _register("Alice")
    second = _register("Alice")
    assert second["status"] == "already_registered"
    assert second["credential"] == first["credential"]


def test_register_creates_joined_ledger_and_balance_cache():
    reg = _register("Alice")
    db = SessionLocal()
    joined = db.query(LedgerEntry).filter(LedgerEntry.owner_id == reg["agent_id"]).all()
    balance = db.query(AgentBalance).filter(AgentBalance.agent_id == reg["agent_id"]).first()
    db.close()

    assert len(joined) == 1
    assert joined[0].status == "JOINED"
    assert balance.balance == 1000


def test_create_art_auto_lists_and_costs_100():
    reg = _register("Alice")
    result = json.loads(create_art(reg["credential"], 250, "Sunset", "A beautiful sunset", DUMMY_ART))
    assert "artwork_id" in result
    assert "listing_id" in result
    assert result["current_price"] == 250
    assert result["price_history"] == []

    portfolio = json.loads(get_my_portfolio(reg["credential"]))
    assert portfolio["kroons"] == 900
    assert portfolio["owned_artworks"][0]["is_listed"] is True


def test_create_art_invalid_credential():
    result = json.loads(create_art("bad-token", 200, "Sunset", "A sunset", DUMMY_ART))
    assert "error" in result


def test_create_art_insufficient_kroons():
    reg = _register("Alice")
    db = SessionLocal()
    balance = db.query(AgentBalance).filter(AgentBalance.agent_id == reg["credential"]).first()
    balance.balance = 50
    db.commit()
    db.close()

    result = json.loads(create_art(reg["credential"], 200, "Sunset", "A sunset", DUMMY_ART))
    assert "error" in result


def test_list_artwork_requires_owned_unlisted_artwork():
    seller = _register("Alice")
    art = json.loads(create_art(seller["credential"], 200, "Sunset", "A sunset", DUMMY_ART))

    already_listed = json.loads(list_artwork(seller["credential"], art["artwork_id"], 300))
    assert "error" in already_listed

    buyer = _register("Bob")
    buy_artwork(buyer["credential"], art["artwork_id"])

    relist = json.loads(list_artwork(buyer["credential"], art["artwork_id"], 500))
    assert relist["artwork_id"] == art["artwork_id"]
    assert relist["price"] == 500
    assert "listing_id" in relist


def test_browse_art_board_supports_lightweight_listing_view():
    seller = _register("Alice")
    viewer = _register("Bob")
    json.loads(create_art(seller["credential"], 200, "Sunset", "A sunset", DUMMY_ART))

    result = json.loads(browse_art_board(viewer["credential"]))
    assert result["count"] == 1
    listing = result["listings"][0]
    assert set(listing.keys()) == {"listing_id", "artwork_id", "title", "price", "seller_id"}


def test_browse_art_board_filters_by_price_and_limit():
    seller = _register("Alice")
    viewer = _register("Bob")
    json.loads(create_art(seller["credential"], 150, "One", "Desc", DUMMY_ART))
    second = json.loads(create_art(seller["credential"], 350, "Two", "Desc", DUMMY_ART))
    buy_artwork(viewer["credential"], second["artwork_id"])

    result = json.loads(browse_art_board(viewer["credential"], min_price=100, max_price=200, limit=1))
    assert result["count"] == 1
    assert result["listings"][0]["price"] == 150


def test_inspect_artwork_returns_history_without_cost():
    seller = _register("Alice")
    buyer = _register("Bob")
    art = json.loads(create_art(seller["credential"], 200, "Sunset", "A sunset", DUMMY_ART))
    buy_artwork(buyer["credential"], art["artwork_id"])

    result = json.loads(inspect_artwork(buyer["credential"], art["artwork_id"]))
    assert result["full_description"] == "A sunset"
    assert result["price_history"] == [200]
    assert [entry["status"] for entry in result["ledger_history"]] == ["LISTED", "SOLD"]

    portfolio = json.loads(get_my_portfolio(buyer["credential"]))
    assert portfolio["kroons"] == 800


def test_buy_artwork_transfers_funds_and_delists():
    seller = _register("Alice")
    buyer = _register("Bob")
    art = json.loads(create_art(seller["credential"], 200, "Sunset", "A sunset", DUMMY_ART))

    result = json.loads(buy_artwork(buyer["credential"], art["artwork_id"]))
    assert result["bought"] is True
    assert result["price"] == 200

    seller_portfolio = json.loads(get_my_portfolio(seller["credential"]))
    buyer_portfolio = json.loads(get_my_portfolio(buyer["credential"]))
    assert seller_portfolio["kroons"] == 1100
    assert buyer_portfolio["kroons"] == 800

    browse = json.loads(browse_art_board(seller["credential"]))
    assert browse["count"] == 0


def test_get_my_portfolio_returns_owned_artworks():
    agent = _register("Alice")
    art = json.loads(create_art(agent["credential"], 200, "Sunset", "A sunset", DUMMY_ART))

    portfolio = json.loads(get_my_portfolio(agent["credential"]))
    assert portfolio["agent_id"] == agent["agent_id"]
    assert portfolio["kroons"] == 900
    assert portfolio["owned_artworks"][0]["artwork_id"] == art["artwork_id"]
    assert portfolio["owned_artworks"][0]["listed_price"] == 200


def test_ledger_records_joined_listed_and_sold_entries():
    seller = _register("Alice")
    buyer = _register("Bob")
    art = json.loads(create_art(seller["credential"], 200, "Sunset", "A sunset", DUMMY_ART))
    buy_artwork(buyer["credential"], art["artwork_id"])

    db = SessionLocal()
    ledger_entries = db.query(LedgerEntry).order_by(LedgerEntry.id.asc()).all()
    db.close()

    assert len(ledger_entries) == 4
    assert ledger_entries[0].status == "JOINED"
    assert ledger_entries[1].status == "JOINED"
    assert ledger_entries[2].status == "LISTED"
    assert ledger_entries[3].status == "SOLD"
