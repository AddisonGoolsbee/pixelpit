from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.artwork import Artwork
from app.models.ledger import LedgerEntry

router = APIRouter()


def _latest_entry(db: Session, artwork_id: str) -> LedgerEntry | None:
    return (
        db.query(LedgerEntry)
        .filter(LedgerEntry.artwork_id == artwork_id)
        .order_by(LedgerEntry.id.desc())
        .first()
    )


@router.get("/")
def list_artworks(db: Session = Depends(get_db)):
    artworks = db.query(Artwork).all()
    results = []
    for artwork in artworks:
        latest = _latest_entry(db, artwork.id)
        results.append(
            {
                "id": artwork.id,
                "title": artwork.title,
                "pixel_data": artwork.pixel_data,
                "story": artwork.story,
                "creator_id": artwork.creator_id,
                "owner_id": latest.owner_id if latest else None,
                "listed_price": latest.price if latest and latest.is_listed else None,
                "is_listed": latest.is_listed if latest else False,
            }
        )
    return results


@router.get("/top")
def top_artworks(db: Session = Depends(get_db)):
    """Top 10 artworks by highest sale price ever."""
    top_txs = (
        db.query(LedgerEntry)
        .filter(LedgerEntry.status == "SOLD")
        .order_by(LedgerEntry.price.desc())
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
        latest = _latest_entry(db, tx.artwork_id)
        if artwork:
            results.append({
                "artwork_id": artwork.id,
                "title": artwork.title,
                "pixel_data": artwork.pixel_data,
                "highest_sale_price": tx.price,
                "creator_id": artwork.creator_id,
                "current_owner_id": latest.owner_id if latest else None,
            })
    return results


@router.get("/{artwork_id}/history")
def artwork_history(artwork_id: str, db: Session = Depends(get_db)):
    """Full provenance chain for an artwork."""
    txs = (
        db.query(LedgerEntry)
        .filter(LedgerEntry.artwork_id == artwork_id)
        .order_by(LedgerEntry.id.asc())
        .all()
    )
    return [
        {
            "id": t.id,
            "status": t.status,
            "owner_id": t.owner_id,
            "price": t.price,
            "is_listed": t.is_listed,
            "created_at": t.created_at,
        }
        for t in txs
    ]
