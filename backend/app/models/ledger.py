from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String

from app.database import Base


class LedgerEntry(Base):
    __tablename__ = "ledger"

    id = Column(Integer, primary_key=True, index=True)
    artwork_id = Column(String, ForeignKey("artworks.id"), nullable=True)
    status = Column(String, nullable=False, index=True)
    price = Column(Integer, nullable=False)
    owner_id = Column(String, ForeignKey("agents.id"), nullable=False)
    is_listed = Column(Boolean, nullable=False, default=False)
    created_at = Column(Integer, nullable=False, index=True)

    __table_args__ = (
        Index("ix_ledger_owner_id_id", "owner_id", "id"),
        Index("ix_ledger_artwork_id_id", "artwork_id", "id"),
    )
