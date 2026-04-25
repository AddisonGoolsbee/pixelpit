from sqlalchemy import Column, Integer, ForeignKey
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    artwork_id = Column(Integer, ForeignKey("artworks.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    price = Column(Integer, nullable=False)
    round_number = Column(Integer, nullable=False)
