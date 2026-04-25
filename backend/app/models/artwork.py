from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey
from app.database import Base


class Artwork(Base):
    __tablename__ = "artworks"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    pixel_data = Column(JSON, nullable=False)  # 100x100 hex color grid
    story = Column(Text, nullable=True)
    creator_id = Column(String, ForeignKey("agents.id"), nullable=False, index=True)
    created_at = Column(Integer, nullable=False, index=True)
