from sqlalchemy import Column, ForeignKey, Integer, String

from app.database import Base


class AgentBalance(Base):
    __tablename__ = "agent_balances"

    agent_id = Column(String, ForeignKey("agents.id"), primary_key=True)
    balance = Column(Integer, nullable=False)
