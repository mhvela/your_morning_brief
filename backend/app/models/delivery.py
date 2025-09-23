from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .article import Article
    from .feedback import Feedback
    from .topic import Topic
    from .user import User


class Delivery(Base):
    __tablename__ = "deliveries"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    topic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("topics.id"), nullable=False
    )
    article_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("articles.id"), nullable=False
    )
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    # Unique constraints: one article per topic per date per position
    __table_args__ = (
        UniqueConstraint(
            "topic_id", "delivery_date", "article_id", name="uq_topic_date_article"
        ),
        UniqueConstraint(
            "topic_id", "delivery_date", "position", name="uq_topic_date_position"
        ),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="deliveries")
    topic: Mapped["Topic"] = relationship("Topic", back_populates="deliveries")
    article: Mapped["Article"] = relationship("Article", back_populates="deliveries")
    feedback: Mapped[Optional["Feedback"]] = relationship(
        "Feedback", back_populates="delivery", uselist=False
    )
