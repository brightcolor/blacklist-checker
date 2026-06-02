"""initial schema

Revision ID: 202611200001
Revises:
Create Date: 2026-04-20 09:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "202611200001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.Enum("ADMIN", "USER", name="userrole"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("otp_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("otp_secret", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "rbl_lists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False, unique=True),
        sa.Column("list_type", sa.Enum("DNSBL", "URIBL", "WHITELIST", name="rbllisttype"), nullable=False),
        sa.Column("dns_zone", sa.String(length=255), nullable=False, unique=True),
        sa.Column("supports_ipv4", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("supports_ipv6", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("supports_domain", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("supports_hostname", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("delist_url", sa.String(length=500), nullable=True),
        sa.Column("return_code_regex", sa.String(length=200), nullable=True),
        sa.Column("severity", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("health_score", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("timeout_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_degraded", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "rbl_list_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("list_ids_csv", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "monitors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("target_type", sa.Enum("IPV4", "IPV6", "DOMAIN", "HOSTNAME", name="targettype"), nullable=False),
        sa.Column("target_value", sa.String(length=320), nullable=False),
        sa.Column("interval_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("list_ids_csv", sa.Text(), nullable=False, server_default=""),
        sa.Column("sensitivity", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("maintenance_mode", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_status", sa.Enum("OK", "LISTED", "DEGRADED", "ERROR", "UNKNOWN", name="monitorstatus"), nullable=False, server_default="UNKNOWN"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "check_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("monitor_id", sa.Integer(), sa.ForeignKey("monitors.id", ondelete="CASCADE"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_type", sa.Enum("IPV4", "IPV6", "DOMAIN", "HOSTNAME", name="targettype"), nullable=False),
        sa.Column("target_value", sa.String(length=320), nullable=False),
        sa.Column("overall_status", sa.Enum("OK", "LISTED", "DEGRADED", "ERROR", "UNKNOWN", name="monitorstatus"), nullable=False),
        sa.Column("listed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("degraded_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("diff_summary", sa.Text(), nullable=True),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "check_run_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("check_run_id", sa.Integer(), sa.ForeignKey("check_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("list_id", sa.Integer(), sa.ForeignKey("rbl_lists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("list_name", sa.String(length=150), nullable=False),
        sa.Column("dns_zone", sa.String(length=255), nullable=False),
        sa.Column("status", sa.Enum("LISTED", "CLEAN", "ERROR", "TIMEOUT", "DISABLED", "DEGRADED", name="checkstatus"), nullable=False),
        sa.Column("answer_code", sa.String(length=100), nullable=True),
        sa.Column("txt_record", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=40), nullable=True),
        sa.Column("severity", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("detail_url", sa.String(length=500), nullable=True),
        sa.Column("raw_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "alert_channels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("channel_type", sa.Enum("EMAIL", "WEBHOOK", "TELEGRAM", "SLACK", "MATRIX", "DISCORD", name="alertchanneltype"), nullable=False),
        sa.Column("target", sa.String(length=1000), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("cooldown_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "alert_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("monitor_id", sa.Integer(), sa.ForeignKey("monitors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("alert_channels.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.Enum("NEW_LISTING", "REMOVED", "LIST_COUNT_INCREASED", "LIST_DEGRADED", "CHECK_FAILED", "DAILY_SUMMARY", name="alerteventtype"), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "SENT", "FAILED", "SUPPRESSED", name="alerteventstatus"), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dedupe_key", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "global_settings",
        sa.Column("key", sa.String(length=120), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("global_settings")
    op.drop_table("alert_events")
    op.drop_table("alert_channels")
    op.drop_table("check_run_results")
    op.drop_table("check_runs")
    op.drop_table("monitors")
    op.drop_table("rbl_list_groups")
    op.drop_table("rbl_lists")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS alerteventstatus")
    op.execute("DROP TYPE IF EXISTS alerteventtype")
    op.execute("DROP TYPE IF EXISTS alertchanneltype")
    op.execute("DROP TYPE IF EXISTS checkstatus")
    op.execute("DROP TYPE IF EXISTS monitorstatus")
    op.execute("DROP TYPE IF EXISTS targettype")
    op.execute("DROP TYPE IF EXISTS rbllisttype")
    op.execute("DROP TYPE IF EXISTS userrole")
