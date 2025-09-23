from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .article import Article


class ArticleSummary(Base):
    __tablename__ = "article_summaries"

    article_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("articles.id"), nullable=False
    )
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False)

    # Unique constraint: one summary per article per model
    __table_args__ = (UniqueConstraint("article_id", "model", name="uq_article_model"),)

    # Relationships
    article: Mapped["Article"] = relationship("Article", back_populates="summaries")
