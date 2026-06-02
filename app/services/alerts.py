import asyncio
import json
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import httpx
import structlog
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.monitor import CheckRun, Monitor
from app.models.user import AlertChannel, AlertChannelType, AlertEvent, AlertEventStatus, AlertEventType

logger = structlog.get_logger(__name__)
settings = get_settings()


class AlertDispatcher:
    async def dispatch_monitor_events(self, db: Session, monitor: Monitor, run: CheckRun) -> None:
        previous = (
            db.execute(
                select(CheckRun)
                .where(CheckRun.monitor_id == monitor.id, CheckRun.id != run.id)
                .order_by(desc(CheckRun.run_at))
                .limit(1)
            )
            .scalars()
            .first()
        )

        event_types: list[AlertEventType] = []
        if previous is None:
            if run.listed_count > 0:
                event_types.append(AlertEventType.NEW_LISTING)
        else:
            if run.listed_count > previous.listed_count:
                event_types.append(AlertEventType.LIST_COUNT_INCREASED)
            if run.listed_count > 0 and previous.listed_count == 0:
                event_types.append(AlertEventType.NEW_LISTING)
            if run.listed_count == 0 and previous.listed_count > 0:
                event_types.append(AlertEventType.REMOVED)
            if run.error_count > previous.error_count:
                event_types.append(AlertEventType.CHECK_FAILED)

        if not event_types:
            return

        channels = (
            db.execute(
                select(AlertChannel).where(
                    AlertChannel.user_id == monitor.user_id, AlertChannel.is_enabled.is_(True)
                )
            )
            .scalars()
            .all()
        )
        now = datetime.now(tz=timezone.utc)

        for event_type in event_types:
            for channel in channels:
                dedupe_key = f"{monitor.id}:{event_type.value}:{channel.id}"
                latest = (
                    db.execute(
                        select(AlertEvent)
                        .where(AlertEvent.dedupe_key == dedupe_key)
                        .order_by(desc(AlertEvent.created_at))
                        .limit(1)
                    )
                    .scalars()
                    .first()
                )
                if latest and latest.created_at and latest.created_at > now - timedelta(minutes=channel.cooldown_minutes):
                    evt = AlertEvent(
                        user_id=monitor.user_id,
                        monitor_id=monitor.id,
                        channel_id=channel.id,
                        event_type=event_type,
                        status=AlertEventStatus.SUPPRESSED,
                        message="suppressed by cooldown",
                        dedupe_key=dedupe_key,
                    )
                    db.add(evt)
                    continue

                message = self._build_message(monitor, run, event_type)
                status = await self._send_to_channel(channel, message)
                evt = AlertEvent(
                    user_id=monitor.user_id,
                    monitor_id=monitor.id,
                    channel_id=channel.id,
                    event_type=event_type,
                    status=AlertEventStatus.SENT if status else AlertEventStatus.FAILED,
                    message=message,
                    sent_at=now if status else None,
                    dedupe_key=dedupe_key,
                )
                db.add(evt)

        db.commit()

    @staticmethod
    def _build_message(monitor: Monitor, run: CheckRun, event_type: AlertEventType) -> str:
        return (
            f"[{event_type.value}] {monitor.name} ({monitor.target_value}) "
            f"status={run.overall_status.value} listed={run.listed_count} errors={run.error_count}"
        )

    async def _send_to_channel(self, channel: AlertChannel, message: str) -> bool:
        if channel.channel_type == AlertChannelType.EMAIL:
            return await asyncio.to_thread(self._send_email, channel.target, message)
        if channel.channel_type in {
            AlertChannelType.WEBHOOK,
            AlertChannelType.SLACK,
            AlertChannelType.DISCORD,
            AlertChannelType.MATRIX,
            AlertChannelType.TELEGRAM,
        }:
            return await self._send_webhook(channel.target, message)
        return False

    @staticmethod
    def _send_email(recipient: str, body: str) -> bool:
        if not settings.smtp_enabled or not settings.smtp_host or not settings.smtp_from:
            logger.warning("smtp_not_configured", recipient=recipient)
            return False
        msg = EmailMessage()
        msg["Subject"] = "RBL Guard Alert"
        msg["From"] = str(settings.smtp_from)
        msg["To"] = recipient
        msg.set_content(body)
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
                if settings.smtp_starttls:
                    smtp.starttls()
                if settings.smtp_username and settings.smtp_password:
                    smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(msg)
            return True
        except Exception:
            logger.exception("email_send_failed", recipient=recipient)
            return False

    @staticmethod
    async def _send_webhook(url: str, message: str) -> bool:
        payload = {"text": message, "message": message, "source": "rbl-guard"}
        try:
            async with httpx.AsyncClient(timeout=settings.default_webhook_timeout) as client:
                res = await client.post(url, content=json.dumps(payload), headers={"Content-Type": "application/json"})
                return res.status_code < 300
        except Exception:
            logger.exception("webhook_send_failed", url=url)
            return False
