from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .article_summary import ArticleSummary
    from .delivery import Delivery
    from .source import Source


class Article(Base):
    __tablename__ = "articles"

    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sources.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    link: Mapped[str] = mapped_column(String(1024), nullable=False)
    summary_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index("idx_published_at", "published_at"),
        Index("idx_source_published", "source_id", "published_at"),
        Index("idx_content_hash", "content_hash"),
    )

    # Relationships
    source: Mapped["Source"] = relationship("Source", back_populates="articles")
    summaries: Mapped[list["ArticleSummary"]] = relationship(
        "ArticleSummary", back_populates="article"
    )
    deliveries: Mapped[list["Delivery"]] = relationship(
        "Delivery", back_populates="article"
    )
