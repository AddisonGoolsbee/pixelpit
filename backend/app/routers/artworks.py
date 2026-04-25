from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.artwork import Artwork
from app.models.transaction import Transaction

router = APIRouter()


@router.get("/")
def list_artworks(db: Session = Depends(get_db)):
    artworks = db.query(Artwork).all()
    return [
        {
            "id": a.id,
            "title": a.title,
            "pixel_data": a.pixel_data,
            "story": a.story,
            "creator_id": a.creator_id,
            "owner_id": a.owner_id,
            "creation_cost": a.creation_cost,
            "listed_price": a.listed_price,
            "created_at_round": a.created_at_round,
        }
        for a in artworks
    ]


@router.get("/top")
def top_artworks(db: Session = Depends(get_db)):
    """Top 10 artworks by highest sale price ever."""
    top_txs = (
        db.query(Transaction)
        .order_by(Transaction.price.desc())
        .limit(10)
        .all()
    )
    results = []
    seen = set()
    for tx in top_txs:
        if tx.artwork_id in seen:
            continue
        seen.add(tx.artwork_id)
        artwork = db.query(Artwork).filter(Artwork.id == tx.artwork_id).first()
        if artwork:
            results.append({
                "artwork_id": artwork.id,
                "title": artwork.title,
                "pixel_data": artwork.pixel_data,
                "highest_sale_price": tx.price,
                "creator_id": artwork.creator_id,
                "current_owner_id": artwork.owner_id,
            })
    return results


@router.get("/{artwork_id}/history")
def artwork_history(artwork_id: int, db: Session = Depends(get_db)):
    """Full provenance chain for an artwork."""
    txs = (
        db.query(Transaction)
        .filter(Transaction.artwork_id == artwork_id)
        .order_by(Transaction.round_number.asc())
        .all()
    )
    return [
        {
            "seller_id": t.seller_id,
            "buyer_id": t.buyer_id,
            "price": t.price,
            "round": t.round_number,
        }
        for t in txs
    ]
