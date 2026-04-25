from sqlalchemy import Column, Integer, String
from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(Integer, nullable=False, index=True)
