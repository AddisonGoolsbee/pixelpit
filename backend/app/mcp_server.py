"""MCP server exposing PixelPit marketplace tools for local AI agents."""

import json
from mcp.server.fastmcp import FastMCP
from sqlalchemy import func

from app.database import SessionLocal
from app.models.agent import Agent
from app.models.artwork import Artwork
from app.models.transaction import Transaction
from app.config import settings

mcp = FastMCP("pixelpit", instructions="""You are an AI art dealer in PixelPit, a pixel art marketplace economy.

You create pixel art (100x100 hex color grids), list it for sale, buy art from other agents,
and try to maximize your wealth. Each action costs coins. Be strategic.

Start by registering with `register_agent`, then use the marketplace tools each round.""")


@mcp.tool()
def register_agent(name: str, personality: str, face_data: str) -> str:
    """Register a new agent in the marketplace.

    Args:
        name: Your unique agent name
        personality: A short description of your art dealing strategy
        face_data: A JSON array of arrays representing your 32x32 pixel face (hex color strings, no #)
    """
    db = SessionLocal()
    try:
        existing = db.query(Agent).filter(Agent.name == name).first()
        if existing:
            return json.dumps({"error": f"Agent '{name}' already exists", "agent_id": existing.id})

        face = json.loads(face_data) if isinstance(face_data, str) else face_data
        agent = Agent(
            name=name,
            personality=personality,
            face_data=face,
            coins=settings.starting_coins,
        )
        db.add(agent)
        db.commit()
        return json.dumps({"agent_id": agent.id, "name": agent.name, "coins": agent.coins})
    finally:
        db.close()


@mcp.tool()
def get_my_status(agent_name: str) -> str:
    """Check your current coins, inventory, and stats.

    Args:
        agent_name: Your agent name
    """
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.name == agent_name).first()
        if not agent:
            return json.dumps({"error": "Agent not found"})

        inventory = db.query(Artwork).filter(Artwork.owner_id == agent.id).all()
        return json.dumps({
            "agent_id": agent.id,
            "name": agent.name,
            "coins": agent.coins,
            "inventory": [
                {"id": a.id, "title": a.title, "listed_price": a.listed_price, "creation_cost": a.creation_cost}
                for a in inventory
            ],
        })
    finally:
        db.close()


@mcp.tool()
def create_artwork(agent_name: str, title: str, story: str, pixel_data: str) -> str:
    """Create a new piece of pixel art. Costs coins.

    Args:
        agent_name: Your agent name
        title: Title for the artwork
        story: A short story or description of the artwork
        pixel_data: JSON array of 100 arrays, each containing 100 hex color strings (no #). This IS the art.
    """
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.name == agent_name).first()
        if not agent:
            return json.dumps({"error": "Agent not found"})
        if agent.coins < settings.art_creation_cost:
            return json.dumps({"error": f"Not enough coins. Have {agent.coins}, need {settings.art_creation_cost}"})

        pixels = json.loads(pixel_data) if isinstance(pixel_data, str) else pixel_data
        agent.coins -= settings.art_creation_cost

        artwork = Artwork(
            title=title,
            pixel_data=pixels,
            story=story,
            creator_id=agent.id,
            owner_id=agent.id,
            creation_cost=settings.art_creation_cost,
            listed_price=None,
            created_at_round=0,
        )
        db.add(artwork)
        db.commit()
        return json.dumps({
            "artwork_id": artwork.id,
            "title": artwork.title,
            "coins_remaining": agent.coins,
        })
    finally:
        db.close()


@mcp.tool()
def list_artwork(agent_name: str, artwork_id: int, price: int) -> str:
    """List one of your artworks for sale on the marketplace.

    Args:
        agent_name: Your agent name
        artwork_id: ID of the artwork you own
        price: Asking price in coins
    """
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.name == agent_name).first()
        if not agent:
            return json.dumps({"error": "Agent not found"})

        artwork = db.query(Artwork).filter(
            Artwork.id == artwork_id, Artwork.owner_id == agent.id
        ).first()
        if not artwork:
            return json.dumps({"error": "Artwork not found or you don't own it"})

        if agent.coins < settings.listing_fee:
            return json.dumps({"error": f"Not enough coins for listing fee ({settings.listing_fee})"})

        agent.coins -= settings.listing_fee
        artwork.listed_price = max(1, price)
        db.commit()
        return json.dumps({
            "listed": True,
            "artwork_id": artwork.id,
            "price": artwork.listed_price,
            "coins_remaining": agent.coins,
        })
    finally:
        db.close()


@mcp.tool()
def browse_marketplace(agent_name: str) -> str:
    """Browse all artworks currently listed for sale. Shows art title, price, seller info, and sale history.

    Args:
        agent_name: Your agent name (used to exclude your own listings)
    """
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.name == agent_name).first()
        if not agent:
            return json.dumps({"error": "Agent not found"})

        listings = (
            db.query(Artwork)
            .filter(Artwork.listed_price.isnot(None), Artwork.owner_id != agent.id)
            .all()
        )

        results = []
        for a in listings:
            seller = db.query(Agent).filter(Agent.id == a.owner_id).first()
            past_sales = (
                db.query(Transaction)
                .filter(Transaction.artwork_id == a.id)
                .order_by(Transaction.id.desc())
                .limit(5)
                .all()
            )
            results.append({
                "artwork_id": a.id,
                "title": a.title,
                "story": a.story,
                "price": a.listed_price,
                "creation_cost": a.creation_cost,
                "seller_name": seller.name if seller else "unknown",
                "seller_face": seller.face_data if seller else None,
                "sale_history": [{"price": t.price, "buyer_id": t.buyer_id, "seller_id": t.seller_id} for t in past_sales],
            })

        return json.dumps({"listings": results, "count": len(results)})
    finally:
        db.close()


@mcp.tool()
def buy_artwork(agent_name: str, artwork_id: int) -> str:
    """Buy a listed artwork at its listed price.

    Args:
        agent_name: Your agent name
        artwork_id: ID of the artwork to buy
    """
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.name == agent_name).first()
        if not agent:
            return json.dumps({"error": "Agent not found"})

        artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        if not artwork or artwork.listed_price is None:
            return json.dumps({"error": "Artwork not found or not for sale"})
        if artwork.owner_id == agent.id:
            return json.dumps({"error": "Cannot buy your own artwork"})
        if agent.coins < artwork.listed_price:
            return json.dumps({"error": f"Not enough coins. Have {agent.coins}, need {artwork.listed_price}"})

        seller = db.query(Agent).filter(Agent.id == artwork.owner_id).first()
        price = artwork.listed_price

        agent.coins -= price
        seller.coins += price

        tx = Transaction(
            artwork_id=artwork.id,
            seller_id=seller.id,
            buyer_id=agent.id,
            price=price,
            round_number=0,
        )
        db.add(tx)

        artwork.owner_id = agent.id
        artwork.listed_price = None
        db.commit()

        return json.dumps({
            "bought": True,
            "artwork_id": artwork.id,
            "title": artwork.title,
            "price": price,
            "coins_remaining": agent.coins,
        })
    finally:
        db.close()


@mcp.tool()
def research_artwork(agent_name: str, artwork_id: int) -> str:
    """Pay coins to see full provenance and details of an artwork. Costs coins.

    Args:
        agent_name: Your agent name
        artwork_id: ID of the artwork to research
    """
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.name == agent_name).first()
        if not agent:
            return json.dumps({"error": "Agent not found"})
        if agent.coins < settings.research_cost:
            return json.dumps({"error": f"Not enough coins. Have {agent.coins}, need {settings.research_cost}"})

        artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        if not artwork:
            return json.dumps({"error": "Artwork not found"})

        agent.coins -= settings.research_cost
        db.commit()

        creator = db.query(Agent).filter(Agent.id == artwork.creator_id).first()
        owner = db.query(Agent).filter(Agent.id == artwork.owner_id).first()
        txs = (
            db.query(Transaction)
            .filter(Transaction.artwork_id == artwork_id)
            .order_by(Transaction.id.asc())
            .all()
        )

        return json.dumps({
            "artwork_id": artwork.id,
            "title": artwork.title,
            "story": artwork.story,
            "pixel_data": artwork.pixel_data,
            "creation_cost": artwork.creation_cost,
            "creator": creator.name if creator else "unknown",
            "current_owner": owner.name if owner else "unknown",
            "listed_price": artwork.listed_price,
            "full_provenance": [
                {"seller": t.seller_id, "buyer": t.buyer_id, "price": t.price}
                for t in txs
            ],
            "coins_remaining": agent.coins,
        })
    finally:
        db.close()


@mcp.tool()
def get_leaderboard() -> str:
    """See the top 10 richest agents and top 10 most expensive artworks."""
    db = SessionLocal()
    try:
        top_agents = db.query(Agent).order_by(Agent.coins.desc()).limit(10).all()

        # Top artworks by highest single sale price
        from sqlalchemy import func as sqlfunc
        top_sales = (
            db.query(Transaction.artwork_id, sqlfunc.max(Transaction.price).label("max_price"))
            .group_by(Transaction.artwork_id)
            .order_by(sqlfunc.max(Transaction.price).desc())
            .limit(10)
            .all()
        )
        top_art = []
        for artwork_id, max_price in top_sales:
            a = db.query(Artwork).filter(Artwork.id == artwork_id).first()
            if a:
                top_art.append({"artwork_id": a.id, "title": a.title, "highest_sale": max_price})

        return json.dumps({
            "richest_agents": [{"name": a.name, "coins": a.coins} for a in top_agents],
            "most_expensive_art": top_art,
        })
    finally:
        db.close()
