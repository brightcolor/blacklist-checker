from enum import Enum

from sqlalchemy import Boolean, Enum as SQLEnum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class RBLListType(str, Enum):
    DNSBL = "dnsbl"
    URIBL = "uribl"
    WHITELIST = "whitelist"


class TargetSupport(str, Enum):
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    DOMAIN = "domain"
    HOSTNAME = "hostname"


class RBLList(TimestampMixin, Base):
    __tablename__ = "rbl_lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    list_type: Mapped[RBLListType] = mapped_column(SQLEnum(RBLListType), nullable=False)
    dns_zone: Mapped[str] = mapped_column(String(255), unique=True)
    supports_ipv4: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_ipv6: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_domain: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_hostname: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    delist_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    return_code_regex: Mapped[str | None] = mapped_column(String(200), nullable=True)
    severity: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    health_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    timeout_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_degraded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class RBLListGroup(TimestampMixin, Base):
    __tablename__ = "rbl_list_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    list_ids_csv: Mapped[str] = mapped_column(Text, default="", nullable=False)
