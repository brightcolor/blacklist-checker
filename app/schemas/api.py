from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.monitor import CheckStatus, MonitorStatus, TargetType
from app.models.rbl import RBLListType
from app.models.user import AlertChannelType, UserRole


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10)
    role: UserRole = UserRole.USER


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: UserRole
    is_active: bool
    otp_enabled: bool


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RBLListIn(BaseModel):
    name: str
    list_type: RBLListType
    dns_zone: str
    supports_ipv4: bool = True
    supports_ipv6: bool = False
    supports_domain: bool = False
    supports_hostname: bool = False
    description: str | None = None
    url: str | None = None
    delist_url: str | None = None
    return_code_regex: str | None = None
    severity: int = 2
    priority: int = 100
    timeout_seconds: int = 3
    is_enabled: bool = True


class RBLListOut(RBLListIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    health_score: int
    success_count: int
    error_count: int
    timeout_count: int
    consecutive_failures: int
    is_degraded: bool


class MonitorIn(BaseModel):
    name: str
    target_type: TargetType
    target_value: str
    interval_minutes: int = Field(ge=15, le=1440, default=60)
    list_ids: list[int] = Field(default_factory=list)
    sensitivity: Literal["low", "normal", "high"] = "normal"
    maintenance_mode: bool = False
    is_enabled: bool = True


class MonitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    target_type: TargetType
    target_value: str
    interval_minutes: int
    list_ids: list[int]
    sensitivity: str
    maintenance_mode: bool
    is_enabled: bool
    last_status: MonitorStatus
    last_run_at: datetime | None
    next_run_at: datetime | None


class ManualCheckIn(BaseModel):
    target_type: TargetType
    target_value: str
    list_ids: list[int] | None = None


class CheckResultOut(BaseModel):
    list_id: int
    list_name: str
    dns_zone: str
    status: CheckStatus
    answer_code: str | None
    txt_record: str | None
    category: str | None
    severity: int
    detail_url: str | None
    raw_error: str | None


class RunOut(BaseModel):
    id: int
    monitor_id: int | None
    target_type: TargetType
    target_value: str
    overall_status: MonitorStatus
    listed_count: int
    error_count: int
    degraded_count: int
    duration_ms: int
    diff_summary: str | None
    run_at: datetime
    fcrdns: dict[str, str | bool | None] | None = None
    results: list[CheckResultOut]


class AlertChannelIn(BaseModel):
    name: str
    channel_type: AlertChannelType
    target: str
    cooldown_minutes: int = Field(default=30, ge=1, le=1440)
    is_enabled: bool = True


class AlertChannelOut(AlertChannelIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class DashboardOut(BaseModel):
    monitors_total: int
    currently_listed: int
    new_listings_today: int
    failed_checks_last_24h: int
    alerts_last_24h: int
