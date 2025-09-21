import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FeedbackRating(enum.Enum):
    """Rating values for user feedback on article deliveries."""

    UP = "up"
    DOWN = "down"


if TYPE_CHECKING:
    from .delivery import Delivery


class Feedback(Base):
    __tablename__ = "feedback"

    delivery_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deliveries.id"), unique=True, nullable=False
    )
    rating: Mapped[FeedbackRating] = mapped_column(Enum(FeedbackRating), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    delivery: Mapped["Delivery"] = relationship("Delivery", back_populates="feedback")
