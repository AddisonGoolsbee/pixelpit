from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agent import Agent
from app.models.agent_balance import AgentBalance

router = APIRouter()


@router.get("/")
def list_agents(db: Session = Depends(get_db)):
    balances = {
        balance.agent_id: balance.balance
        for balance in db.query(AgentBalance).all()
    }
    agents = db.query(Agent).all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "color": a.color,
            "coins": balances.get(a.id, 0),
        }
        for a in agents
    ]


@router.get("/leaderboard")
def agent_leaderboard(db: Session = Depends(get_db)):
    """Top agents by coin wealth."""
    balances = (
        db.query(Agent, AgentBalance.balance)
        .join(AgentBalance, AgentBalance.agent_id == Agent.id)
        .order_by(AgentBalance.balance.desc())
        .limit(10)
        .all()
    )
    return [
        {"rank": i + 1, "name": agent.name, "coins": balance, "id": agent.id}
        for i, (agent, balance) in enumerate(balances)
    ]
