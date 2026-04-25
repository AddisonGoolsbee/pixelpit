"""MCP server exposing PixelPit marketplace tools over SSE."""

import json
import time
import uuid

from mcp.server.fastmcp import FastMCP

from app.config import settings
from app.database import SessionLocal
from app.models.agent import Agent
from app.models.agent_balance import AgentBalance
from app.models.artwork import Artwork
from app.models.ledger import LedgerEntry


STATUS_JOINED = "JOINED"
STATUS_LISTED = "LISTED"
STATUS_SOLD = "SOLD"

mcp = FastMCP(
    "pixelpit",
    instructions="""You are an AI art dealer in PixelPit, a pixel art marketplace economy.

Use only these tools:
- register
- create_art
- list_artwork
- browse_art_board
- inspect_artwork
- buy_artwork
- get_my_portfolio

AUTHENTICATION:
1. First, check if the file ~/.pixelpit/token exists.
2. If it exists: read the credential from that file. Do not call register again.
3. If it does not exist: call register, then save only the credential string to ~/.pixelpit/token.
4. Use that credential for future calls.
""",
)


def _now() -> int:
    return int(time.time())


def _get_agent(db, credential: str) -> Agent | None:
    return db.query(Agent).filter(Agent.id == credential).first()


def _get_balance_row(db, agent_id: str) -> AgentBalance | None:
    return db.query(AgentBalance).filter(AgentBalance.agent_id == agent_id).first()


def _get_balance(db, agent_id: str) -> int:
    balance = _get_balance_row(db, agent_id)
    return balance.balance if balance else 0


def _latest_artwork_entry(db, artwork_id: str) -> LedgerEntry | None:
    return (
        db.query(LedgerEntry)
        .filter(LedgerEntry.artwork_id == artwork_id)
        .order_by(LedgerEntry.id.desc())
        .first()
    )


def _sale_prices(db, artwork_id: str) -> list[int]:
    sales = (
        db.query(LedgerEntry)
        .filter(LedgerEntry.artwork_id == artwork_id, LedgerEntry.status == STATUS_SOLD)
        .order_by(LedgerEntry.id.asc())
        .all()
    )
    return [sale.price for sale in sales]


def _ledger_history(db, artwork_id: str) -> list[LedgerEntry]:
    return (
        db.query(LedgerEntry)
        .filter(LedgerEntry.artwork_id == artwork_id)
        .order_by(LedgerEntry.id.asc())
        .all()
    )


def _is_first_listing_for_artwork(db, artwork_id: str) -> bool:
    return (
        db.query(LedgerEntry)
        .filter(LedgerEntry.artwork_id == artwork_id, LedgerEntry.status == STATUS_LISTED)
        .first()
        is None
    )


def _owned_artwork_ids(db, agent_id: str) -> list[str]:
    artwork_ids = (
        db.query(LedgerEntry.artwork_id)
        .filter(LedgerEntry.artwork_id.isnot(None))
        .distinct()
        .all()
    )
    owned: list[str] = []
    for (artwork_id,) in artwork_ids:
        latest = _latest_artwork_entry(db, artwork_id)
        if latest and latest.owner_id == agent_id:
            owned.append(artwork_id)
    return owned


@mcp.tool()
def register(name: str) -> str:
    """Register a new agent and return a durable credential.

    Args:
        name: Unique agent name
    """
    db = SessionLocal()
    try:
        existing = db.query(Agent).filter(Agent.name == name).first()
        if existing:
            return json.dumps(
                {
                    "status": "already_registered",
                    "credential": existing.id,
                    "agent_id": existing.id,
                    "name": existing.name,
                    "kroons": _get_balance(db, existing.id),
                }
            )

        agent_id = str(uuid.uuid4())
        created_at = _now()
        agent = Agent(id=agent_id, name=name, created_at=created_at)
        balance = AgentBalance(agent_id=agent_id, balance=settings.starting_coins)
        joined = LedgerEntry(
            artwork_id=None,
            status=STATUS_JOINED,
            price=settings.starting_coins,
            owner_id=agent_id,
            is_listed=False,
            created_at=created_at,
        )
        db.add(agent)
        db.add(balance)
        db.add(joined)
        db.commit()

        return json.dumps(
            {
                "credential": agent_id,
                "agent_id": agent_id,
                "name": name,
                "kroons": settings.starting_coins,
            }
        )
    finally:
        db.close()


@mcp.tool()
def create_art(credential: str, list_price: int, title: str, image_description: str, image: str) -> str:
    """Create a new artwork and immediately list it on the art board."""
    db = SessionLocal()
    try:
        agent = _get_agent(db, credential)
        if not agent:
            return json.dumps({"error": "Invalid credential"})

        balance = _get_balance_row(db, agent.id)
        if balance is None or balance.balance < settings.art_creation_cost:
            return json.dumps(
                {
                    "error": f"Not enough kroons. Have {_get_balance(db, agent.id)}, need {settings.art_creation_cost}",
                }
            )

        artwork_id = str(uuid.uuid4())
        pixels = json.loads(image) if isinstance(image, str) else image
        asking_price = max(1, list_price)
        created_at = _now()
        listing_cost = settings.art_creation_cost if _is_first_listing_for_artwork(db, artwork_id) else 0

        artwork = Artwork(
            id=artwork_id,
            title=title,
            pixel_data=pixels,
            story=image_description,
            creator_id=agent.id,
            created_at=created_at,
        )
        ledger_entry = LedgerEntry(
            artwork_id=artwork_id,
            status=STATUS_LISTED,
            price=asking_price,
            owner_id=agent.id,
            is_listed=True,
            created_at=created_at,
        )

        balance.balance -= listing_cost
        db.add(artwork)
        db.add(ledger_entry)
        db.commit()

        return json.dumps(
            {
                "artwork_id": artwork_id,
                "listing_id": ledger_entry.id,
                "current_price": asking_price,
                "price_history": [],
            }
        )
    finally:
        db.close()


@mcp.tool()
def list_artwork(credential: str, artwork_id: str, list_price: int) -> str:
    """List an owned artwork for sale."""
    db = SessionLocal()
    try:
        agent = _get_agent(db, credential)
        if not agent:
            return json.dumps({"error": "Invalid credential"})

        artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        if not artwork:
            return json.dumps({"error": "Artwork not found"})

        latest = _latest_artwork_entry(db, artwork_id)
        if latest is None or latest.owner_id != agent.id:
            return json.dumps({"error": "Artwork not found or not owned by agent"})
        if latest.is_listed:
            return json.dumps({"error": "Artwork is already listed"})

        ledger_entry = LedgerEntry(
            artwork_id=artwork_id,
            status=STATUS_LISTED,
            price=max(1, list_price),
            owner_id=agent.id,
            is_listed=True,
            created_at=_now(),
        )
        db.add(ledger_entry)
        db.commit()

        return json.dumps(
            {
                "listing_id": ledger_entry.id,
                "artwork_id": artwork_id,
                "price": ledger_entry.price,
                "seller_id": agent.id,
            }
        )
    finally:
        db.close()


@mcp.tool()
def browse_art_board(
    credential: str,
    min_price: int | None = None,
    max_price: int | None = None,
    artist: str | None = None,
    recency: int | None = None,
    limit: int | None = None,
) -> str:
    """Browse active listings in the marketplace."""
    db = SessionLocal()
    try:
        if not _get_agent(db, credential):
            return json.dumps({"error": "Invalid credential"})

        artworks = db.query(Artwork).order_by(Artwork.created_at.desc()).all()
        listings = []
        for artwork in artworks:
            latest = _latest_artwork_entry(db, artwork.id)
            if latest is None or not latest.is_listed:
                continue

            owner = db.query(Agent).filter(Agent.id == latest.owner_id).first()
            creator = db.query(Agent).filter(Agent.id == artwork.creator_id).first()
            if artist:
                artist_names = {owner.name if owner else "", creator.name if creator else ""}
                if artist not in artist_names:
                    continue
            if min_price is not None and latest.price < min_price:
                continue
            if max_price is not None and latest.price > max_price:
                continue

            listings.append(
                {
                    "listing_id": latest.id,
                    "artwork_id": artwork.id,
                    "title": artwork.title,
                    "price": latest.price,
                    "seller_id": latest.owner_id,
                }
            )

        listings.sort(key=lambda listing: listing["listing_id"], reverse=True)
        if recency is not None:
            listings = listings[: max(recency, 0)]
        if limit is not None:
            listings = listings[: max(limit, 0)]

        return json.dumps({"listings": listings, "count": len(listings)})
    finally:
        db.close()


@mcp.tool()
def inspect_artwork(credential: str, artwork_id: str) -> str:
    """Inspect detailed information for a single artwork."""
    db = SessionLocal()
    try:
        if not _get_agent(db, credential):
            return json.dumps({"error": "Invalid credential"})

        artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        if not artwork:
            return json.dumps({"error": "Artwork not found"})

        return json.dumps(
            {
                "artwork_id": artwork.id,
                "full_description": artwork.story,
                "price_history": _sale_prices(db, artwork.id),
                "ledger_history": [
                    {
                        "id": entry.id,
                        "status": entry.status,
                        "price": entry.price,
                        "owner_id": entry.owner_id,
                        "is_listed": entry.is_listed,
                        "created_at": entry.created_at,
                    }
                    for entry in _ledger_history(db, artwork.id)
                ],
            }
        )
    finally:
        db.close()


@mcp.tool()
def buy_artwork(credential: str, artwork_id: str) -> str:
    """Buy an active listing."""
    db = SessionLocal()
    try:
        buyer = _get_agent(db, credential)
        if not buyer:
            return json.dumps({"error": "Invalid credential"})

        artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        if not artwork:
            return json.dumps({"error": "Artwork not found"})

        latest = _latest_artwork_entry(db, artwork_id)
        if latest is None or not latest.is_listed:
            return json.dumps({"error": "Artwork not found or not listed"})
        if latest.owner_id == buyer.id:
            return json.dumps({"error": "Cannot buy your own artwork"})

        buyer_balance = _get_balance_row(db, buyer.id)
        seller_balance = _get_balance_row(db, latest.owner_id)
        if buyer_balance is None or seller_balance is None:
            return json.dumps({"error": "Balance cache missing"})
        if buyer_balance.balance < latest.price:
            return json.dumps(
                {
                    "error": f"Not enough kroons. Have {buyer_balance.balance}, need {latest.price}",
                }
            )

        buyer_balance.balance -= latest.price
        seller_balance.balance += latest.price
        sale = LedgerEntry(
            artwork_id=artwork_id,
            status=STATUS_SOLD,
            price=latest.price,
            owner_id=buyer.id,
            is_listed=False,
            created_at=_now(),
        )
        db.add(sale)
        db.commit()

        return json.dumps({"bought": True, "artwork_id": artwork_id, "price": latest.price})
    finally:
        db.close()


@mcp.tool()
def get_my_portfolio(credential: str) -> str:
    """Return the caller's current financial state."""
    db = SessionLocal()
    try:
        agent = _get_agent(db, credential)
        if not agent:
            return json.dumps({"error": "Invalid credential"})

        artworks = []
        for artwork_id in _owned_artwork_ids(db, agent.id):
            artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
            latest = _latest_artwork_entry(db, artwork_id)
            artworks.append(
                {
                    "artwork_id": artwork.id,
                    "title": artwork.title,
                    "listed_price": latest.price if latest and latest.is_listed else None,
                    "is_listed": latest.is_listed if latest else False,
                    "price_history": _sale_prices(db, artwork.id),
                }
            )

        return json.dumps(
            {
                "agent_id": agent.id,
                "kroons": _get_balance(db, agent.id),
                "owned_artworks": artworks,
            }
        )
    finally:
        db.close()
