"""Reservation-related ORM models."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReservationStatus(str, enum.Enum):
    """Workflow status for reservation approvals."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    CANCELLATION_REQUESTED = "cancellation_requested"


class ReservationVisibility(str, enum.Enum):
    """Controls how much information is shown on the public calendar."""

    PUBLIC = "public"
    ANONYMOUS = "anonymous"


class Reservation(Base):
    """Mountain hut reservation request."""

    __tablename__ = "reservations"
    __table_args__ = (Index("ix_reservations_time_range", "start_time", "end_time"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus), default=ReservationStatus.PENDING, nullable=False
    )
    visibility: Mapped[ReservationVisibility] = mapped_column(
        Enum(ReservationVisibility), default=ReservationVisibility.PUBLIC, nullable=False
    )
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    display_message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    approval_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attendee_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    allow_additional_members: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_notification_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="reservations")