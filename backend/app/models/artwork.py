from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey
from app.database import Base


class Artwork(Base):
    __tablename__ = "artworks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    pixel_data = Column(JSON, nullable=False)  # 100x100 hex color grid
    story = Column(Text, nullable=True)
    creator_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    creation_cost = Column(Integer, nullable=False)
    listed_price = Column(Integer, nullable=True)  # null = not for sale
    created_at_round = Column(Integer, nullable=False)
