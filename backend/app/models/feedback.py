from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .delivery import Delivery


class Feedback(Base):
    __tablename__ = "feedback"

    delivery_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deliveries.id"), unique=True, nullable=False
    )
    rating: Mapped[str] = mapped_column(String(10), nullable=False)  # "up" or "down"
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    delivery: Mapped["Delivery"] = relationship("Delivery", back_populates="feedback")
