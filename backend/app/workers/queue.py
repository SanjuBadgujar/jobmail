import logging
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError
from sqlalchemy import func, select

from app.core.config import get_settings
from app.database import session as dbs
from app.workers.queue import wake
from app.models import Campaign, EmailLog, GmailAccount, Recipient, Resume, User
from app.models.entities import utcnow
from app.services.gmail import build_mime, credentials_for, send_raw
from app.services.templating import render

logger = logging.getLogger("jobmail.worker")
wake = threading.Event()  # set by the API when there may be new work
DAILY_LIMIT = 450  # stay under Gmail's ~500/day consumer quota


def process_one() -> float | None:
    """Send at most one pending email. Returns seconds to wait, or None if idle."""
    with dbs.SessionLocal() as db:
        camp = db.scalar(select(Campaign).where(Campaign.status == "running").order_by(Campaign.id))
        if not camp:
            return None
        log = db.scalar(select(EmailLog).where(EmailLog.campaign_id == camp.id, EmailLog.status == "pending").order_by(EmailLog.id))
        if not log:
            camp.status = "completed"; db.commit(); return 0
        user = db.get(User, camp.user_id)
        acct = db.scalar(select(GmailAccount).where(GmailAccount.user_id == user.id))
        if not acct:
            camp.status, camp.note = "paused", "Gmail is not connected."; db.commit(); return 0
        since = utcnow() - timedelta(hours=24)
        sent24 = db.scalar(select(func.count()).select_from(EmailLog).join(Campaign).where(
            Campaign.user_id == user.id, EmailLog.status == "sent", EmailLog.sent_at > since)) or 0
        if sent24 >= DAILY_LIMIT:
            camp.status, camp.note = "paused", "Daily Gmail sending limit reached. Resume tomorrow."; db.commit(); return 0
        log.status = "processing"; db.commit()
        try:
            rec = db.get(Recipient, log.recipient_id)
            resume = db.scalar(select(Resume).where(Resume.user_id == user.id).order_by(Resume.id.desc()))
            path = Path(resume.storage_path) if resume else None
            raw = build_mime(user.email, rec.email, render(camp.subject, rec), render(camp.body, rec), path, resume.filename if resume else None)
            log.gmail_message_id = send_raw(credentials_for(db, acct), raw)
            log.status, log.sent_at, log.error_message = "sent", utcnow(), None
        except RefreshError:
            log.status, log.error_message = "failed", "Gmail authorization expired or revoked. Reconnect Gmail."
            camp.status, camp.note = "paused", log.error_message
        except HttpError as e:
            detail = str(e)[:300]
            log.status, log.error_message = "failed", detail
            if e.resp.status in (401, 403, 429):  # stop instead of failing every remaining email
                quota = e.resp.status == 429 or any(k in detail.lower() for k in ("ratelimit", "dailylimit", "quota"))
                camp.status = "paused"
                camp.note = "Gmail rate limit reached. Sending stopped." if quota else f"Gmail rejected the request: {detail}"
        except Exception as e:  # noqa: BLE001
            log.status, log.error_message = "failed", str(e)[:300]
        db.commit()
        return float(user.send_delay_seconds)


def recover() -> None:
    with dbs.SessionLocal() as db:
        for log in db.scalars(select(EmailLog).where(EmailLog.status == "processing")):
            log.status = "pending"
        db.commit()


def worker_loop(stop: threading.Event) -> None:
    recover()
    while not stop.is_set():
        try:
            wait = process_one()
        except Exception:  # noqa: BLE001
            logger.exception("worker error"); wait = 5
        if wait is None:  # idle: stop touching the database until the API signals new work
            wake.wait(timeout=3600)
            wake.clear()
            continue
        stop.wait(max(wait, 0.5))
