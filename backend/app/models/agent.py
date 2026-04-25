from sqlalchemy import Column, Integer, String, Text, JSON
from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    personality = Column(Text, nullable=False)  # system prompt / strategy
    face_data = Column(JSON, nullable=False)  # 32x32 hex color grid
    coins = Column(Integer, nullable=False, default=1000)
    created_at_round = Column(Integer, default=0)
