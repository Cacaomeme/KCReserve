"""Whitelist entry model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WhitelistEntry(Base):
    """Emails allowed to self-register accounts, optionally with admin rights."""

    __tablename__ = "whitelist_entries"
    __table_args__ = (UniqueConstraint("email", name="uq_whitelist_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_admin_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    added_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    added_by_user = relationship("User", foreign_keys=[added_by_user_id])
