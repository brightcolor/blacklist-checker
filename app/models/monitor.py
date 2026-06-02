from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TargetType(str, Enum):
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    DOMAIN = "domain"
    HOSTNAME = "hostname"


class MonitorStatus(str, Enum):
    OK = "ok"
    LISTED = "listed"
    DEGRADED = "degraded"
    ERROR = "error"
    UNKNOWN = "unknown"


class Monitor(TimestampMixin, Base):
    __tablename__ = "monitors"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    target_type: Mapped[TargetType] = mapped_column(SQLEnum(TargetType), nullable=False)
    target_value: Mapped[str] = mapped_column(String(320), index=True)
    interval_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    list_ids_csv: Mapped[str] = mapped_column(Text, default="", nullable=False)
    sensitivity: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    last_status: Mapped[MonitorStatus] = mapped_column(SQLEnum(MonitorStatus), default=MonitorStatus.UNKNOWN)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class CheckRun(TimestampMixin, Base):
    __tablename__ = "check_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    monitor_id: Mapped[int | None] = mapped_column(ForeignKey("monitors.id", ondelete="CASCADE"), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    target_type: Mapped[TargetType] = mapped_column(SQLEnum(TargetType), nullable=False)
    target_value: Mapped[str] = mapped_column(String(320), index=True)
    overall_status: Mapped[MonitorStatus] = mapped_column(SQLEnum(MonitorStatus), nullable=False)
    listed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    degraded_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    diff_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class CheckStatus(str, Enum):
    LISTED = "listed"
    CLEAN = "clean"
    ERROR = "error"
    TIMEOUT = "timeout"
    DISABLED = "disabled"
    DEGRADED = "degraded"


class CheckRunResult(TimestampMixin, Base):
    __tablename__ = "check_run_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    check_run_id: Mapped[int] = mapped_column(ForeignKey("check_runs.id", ondelete="CASCADE"), index=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("rbl_lists.id", ondelete="CASCADE"), index=True)
    list_name: Mapped[str] = mapped_column(String(150))
    dns_zone: Mapped[str] = mapped_column(String(255))
    status: Mapped[CheckStatus] = mapped_column(SQLEnum(CheckStatus), nullable=False)
    answer_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    txt_record: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    severity: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    detail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_error: Mapped[str | None] = mapped_column(Text, nullable=True)
