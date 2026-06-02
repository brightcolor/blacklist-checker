from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    otp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    otp_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)

    channels: Mapped[list["AlertChannel"]] = relationship(back_populates="user")


class AlertChannelType(str, Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    TELEGRAM = "telegram"
    SLACK = "slack"
    MATRIX = "matrix"
    DISCORD = "discord"


class AlertChannel(TimestampMixin, Base):
    __tablename__ = "alert_channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    channel_type: Mapped[AlertChannelType] = mapped_column(SQLEnum(AlertChannelType), nullable=False)
    target: Mapped[str] = mapped_column(String(1000))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="channels")


class AlertEventType(str, Enum):
    NEW_LISTING = "new_listing"
    REMOVED = "removed"
    LIST_COUNT_INCREASED = "list_count_increased"
    LIST_DEGRADED = "list_degraded"
    CHECK_FAILED = "check_failed"
    DAILY_SUMMARY = "daily_summary"


class AlertEventStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SUPPRESSED = "suppressed"


class AlertEvent(TimestampMixin, Base):
    __tablename__ = "alert_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    monitor_id: Mapped[int] = mapped_column(ForeignKey("monitors.id", ondelete="CASCADE"), index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("alert_channels.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[AlertEventType] = mapped_column(SQLEnum(AlertEventType), nullable=False)
    status: Mapped[AlertEventStatus] = mapped_column(SQLEnum(AlertEventStatus), nullable=False)
    message: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(200), index=True, nullable=True)
