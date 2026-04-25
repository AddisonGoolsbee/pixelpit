from sqlalchemy import Column, Integer, String, Text, JSON
from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    personality = Column(Text, nullable=False)
    face_data = Column(JSON, nullable=False)
    coins = Column(Integer, nullable=False, default=1000)
    created_at_round = Column(Integer, default=0)
