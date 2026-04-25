from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agent import Agent

router = APIRouter()


@router.get("/")
def list_agents(db: Session = Depends(get_db)):
    agents = db.query(Agent).all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "personality": a.personality,
            "coins": a.coins,
            "face_data": a.face_data,
        }
        for a in agents
    ]


@router.get("/leaderboard")
def agent_leaderboard(db: Session = Depends(get_db)):
    """Top agents by coin wealth."""
    agents = db.query(Agent).order_by(Agent.coins.desc()).limit(10).all()
    return [
        {"rank": i + 1, "name": a.name, "coins": a.coins, "id": a.id}
        for i, a in enumerate(agents)
    ]
