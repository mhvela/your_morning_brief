from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .delivery import Delivery
    from .topic import Topic


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships (will be used in future milestones)
    topics: Mapped[list["Topic"]] = relationship("Topic", back_populates="user")
    deliveries: Mapped[list["Delivery"]] = relationship(
        "Delivery", back_populates="user"
    )
