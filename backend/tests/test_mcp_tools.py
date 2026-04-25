"""Unit tests for PixelPit MCP server tools."""

import json
import os
import sys
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import Base, engine, SessionLocal, init_db
from app.models.agent import Agent
from app.models.artwork import Artwork
from app.models.transaction import Transaction
from app.mcp_server import (
    register_agent,
    get_my_status,
    create_artwork,
    list_artwork,
    browse_marketplace,
    buy_artwork,
    research_artwork,
    get_leaderboard,
)


@pytest.fixture(autouse=True)
def fresh_db():
    """Wipe and recreate the database for each test."""
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)


DUMMY_FACE = json.dumps([["FF0000"] * 32] * 32)
DUMMY_ART = json.dumps([["00FF00"] * 100] * 100)


# --- Registration ---

def test_register_new_agent():
    result = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    assert "token" in result
    assert result["name"] == "Alice"
    assert result["coins"] == 1000


def test_register_duplicate_name_returns_existing():
    r1 = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    r2 = json.loads(register_agent("Alice", "different personality", DUMMY_FACE))
    assert r2["status"] == "already_registered"
    assert r2["token"] == r1["token"]


def test_register_returns_valid_uuid():
    result = json.loads(register_agent("Bob", "flipper", DUMMY_FACE))
    token = result["token"]
    # UUID4 format: 8-4-4-4-12 hex chars
    parts = token.split("-")
    assert len(parts) == 5
    assert [len(p) for p in parts] == [8, 4, 4, 4, 12]


# --- Status ---

def test_get_status_valid_token():
    reg = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    status = json.loads(get_my_status(reg["token"]))
    assert status["name"] == "Alice"
    assert status["coins"] == 1000
    assert status["inventory"] == []


def test_get_status_invalid_token():
    result = json.loads(get_my_status("bad-token"))
    assert "error" in result


# --- Create Artwork ---

def test_create_artwork_success():
    reg = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    result = json.loads(create_artwork(reg["token"], "Sunset", "A beautiful sunset", DUMMY_ART))
    assert "artwork_id" in result
    assert result["title"] == "Sunset"
    assert result["coins_remaining"] == 950  # 1000 - 50


def test_create_artwork_insufficient_coins():
    reg = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    # Drain coins
    db = SessionLocal()
    agent = db.query(Agent).filter(Agent.token == reg["token"]).first()
    agent.coins = 10
    db.commit()
    db.close()

    result = json.loads(create_artwork(reg["token"], "Sunset", "A sunset", DUMMY_ART))
    assert "error" in result


def test_create_artwork_invalid_token():
    result = json.loads(create_artwork("bad-token", "Sunset", "A sunset", DUMMY_ART))
    assert "error" in result


# --- List Artwork ---

def test_list_artwork_success():
    reg = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    art = json.loads(create_artwork(reg["token"], "Sunset", "A sunset", DUMMY_ART))
    result = json.loads(list_artwork(reg["token"], art["artwork_id"], 200))
    assert result["listed"] is True
    assert result["price"] == 200


def test_list_artwork_not_owned():
    r1 = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    r2 = json.loads(register_agent("Bob", "flipper", DUMMY_FACE))
    art = json.loads(create_artwork(r1["token"], "Sunset", "A sunset", DUMMY_ART))
    result = json.loads(list_artwork(r2["token"], art["artwork_id"], 200))
    assert "error" in result


def test_list_artwork_fee_deducted():
    reg = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    art = json.loads(create_artwork(reg["token"], "Sunset", "A sunset", DUMMY_ART))
    result = json.loads(list_artwork(reg["token"], art["artwork_id"], 200))
    # 1000 - 50 (create) - 10 (listing fee) = 940
    assert result["coins_remaining"] == 940


# --- Browse Marketplace ---

def test_browse_empty_marketplace():
    reg = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    result = json.loads(browse_marketplace(reg["token"]))
    assert result["count"] == 0


def test_browse_excludes_own_listings():
    reg = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    art = json.loads(create_artwork(reg["token"], "Sunset", "A sunset", DUMMY_ART))
    list_artwork(reg["token"], art["artwork_id"], 200)
    result = json.loads(browse_marketplace(reg["token"]))
    assert result["count"] == 0  # own listing excluded


def test_browse_shows_others_listings():
    r1 = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    r2 = json.loads(register_agent("Bob", "flipper", DUMMY_FACE))
    art = json.loads(create_artwork(r1["token"], "Sunset", "A sunset", DUMMY_ART))
    list_artwork(r1["token"], art["artwork_id"], 200)
    result = json.loads(browse_marketplace(r2["token"]))
    assert result["count"] == 1
    assert result["listings"][0]["title"] == "Sunset"


# --- Buy Artwork ---

def test_buy_artwork_success():
    r1 = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    r2 = json.loads(register_agent("Bob", "flipper", DUMMY_FACE))
    art = json.loads(create_artwork(r1["token"], "Sunset", "A sunset", DUMMY_ART))
    list_artwork(r1["token"], art["artwork_id"], 200)

    result = json.loads(buy_artwork(r2["token"], art["artwork_id"]))
    assert result["bought"] is True
    assert result["price"] == 200
    assert result["coins_remaining"] == 800  # 1000 - 200


def test_buy_artwork_transfers_coins():
    r1 = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    r2 = json.loads(register_agent("Bob", "flipper", DUMMY_FACE))
    art = json.loads(create_artwork(r1["token"], "Sunset", "A sunset", DUMMY_ART))
    list_artwork(r1["token"], art["artwork_id"], 200)
    buy_artwork(r2["token"], art["artwork_id"])

    alice = json.loads(get_my_status(r1["token"]))
    # 1000 - 50 (create) - 10 (list) + 200 (sale) = 1140
    assert alice["coins"] == 1140


def test_buy_own_artwork_fails():
    reg = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    art = json.loads(create_artwork(reg["token"], "Sunset", "A sunset", DUMMY_ART))
    list_artwork(reg["token"], art["artwork_id"], 200)
    result = json.loads(buy_artwork(reg["token"], art["artwork_id"]))
    assert "error" in result


def test_buy_insufficient_coins():
    r1 = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    r2 = json.loads(register_agent("Bob", "flipper", DUMMY_FACE))
    art = json.loads(create_artwork(r1["token"], "Sunset", "A sunset", DUMMY_ART))
    list_artwork(r1["token"], art["artwork_id"], 5000)
    result = json.loads(buy_artwork(r2["token"], art["artwork_id"]))
    assert "error" in result


def test_buy_unlisted_artwork_fails():
    r1 = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    r2 = json.loads(register_agent("Bob", "flipper", DUMMY_FACE))
    art = json.loads(create_artwork(r1["token"], "Sunset", "A sunset", DUMMY_ART))
    result = json.loads(buy_artwork(r2["token"], art["artwork_id"]))
    assert "error" in result


def test_buy_delists_artwork():
    r1 = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    r2 = json.loads(register_agent("Bob", "flipper", DUMMY_FACE))
    art = json.loads(create_artwork(r1["token"], "Sunset", "A sunset", DUMMY_ART))
    list_artwork(r1["token"], art["artwork_id"], 200)
    buy_artwork(r2["token"], art["artwork_id"])

    # Should no longer appear in marketplace
    result = json.loads(browse_marketplace(r1["token"]))
    assert result["count"] == 0


# --- Research Artwork ---

def test_research_artwork_success():
    r1 = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    art = json.loads(create_artwork(r1["token"], "Sunset", "A sunset", DUMMY_ART))
    result = json.loads(research_artwork(r1["token"], art["artwork_id"]))
    assert result["title"] == "Sunset"
    assert result["creator"] == "Alice"
    assert result["coins_remaining"] == 930  # 1000 - 50 - 20


def test_research_shows_provenance():
    r1 = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    r2 = json.loads(register_agent("Bob", "flipper", DUMMY_FACE))
    art = json.loads(create_artwork(r1["token"], "Sunset", "A sunset", DUMMY_ART))
    list_artwork(r1["token"], art["artwork_id"], 200)
    buy_artwork(r2["token"], art["artwork_id"])

    result = json.loads(research_artwork(r2["token"], art["artwork_id"]))
    assert len(result["full_provenance"]) == 1
    assert result["full_provenance"][0]["price"] == 200


# --- Leaderboard ---

def test_leaderboard_empty():
    result = json.loads(get_leaderboard())
    assert result["richest_agents"] == []
    assert result["most_expensive_art"] == []


def test_leaderboard_ranks_by_coins():
    r1 = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    r2 = json.loads(register_agent("Bob", "flipper", DUMMY_FACE))
    # Alice spends coins creating art, Bob doesn't
    create_artwork(r1["token"], "Sunset", "A sunset", DUMMY_ART)

    result = json.loads(get_leaderboard())
    assert result["richest_agents"][0]["name"] == "Bob"
    assert result["richest_agents"][1]["name"] == "Alice"


def test_leaderboard_tracks_sales():
    r1 = json.loads(register_agent("Alice", "loves art", DUMMY_FACE))
    r2 = json.loads(register_agent("Bob", "flipper", DUMMY_FACE))
    art = json.loads(create_artwork(r1["token"], "Sunset", "A sunset", DUMMY_ART))
    list_artwork(r1["token"], art["artwork_id"], 300)
    buy_artwork(r2["token"], art["artwork_id"])

    result = json.loads(get_leaderboard())
    assert len(result["most_expensive_art"]) == 1
    assert result["most_expensive_art"][0]["highest_sale"] == 300


# --- Resale Flow ---

def test_resale_full_flow():
    """Test create -> list -> buy -> relist -> resell."""
    r1 = json.loads(register_agent("Alice", "creator", DUMMY_FACE))
    r2 = json.loads(register_agent("Bob", "flipper", DUMMY_FACE))
    r3 = json.loads(register_agent("Carol", "collector", DUMMY_FACE))

    # Alice creates and lists
    art = json.loads(create_artwork(r1["token"], "Masterpiece", "A masterpiece", DUMMY_ART))
    list_artwork(r1["token"], art["artwork_id"], 100)

    # Bob buys and relists higher
    buy_artwork(r2["token"], art["artwork_id"])
    list_artwork(r2["token"], art["artwork_id"], 500)

    # Carol buys the resale
    result = json.loads(buy_artwork(r3["token"], art["artwork_id"]))
    assert result["bought"] is True
    assert result["price"] == 500

    # Check provenance has 2 sales
    research = json.loads(research_artwork(r3["token"], art["artwork_id"]))
    assert len(research["full_provenance"]) == 2
    assert research["full_provenance"][0]["price"] == 100
    assert research["full_provenance"][1]["price"] == 500
