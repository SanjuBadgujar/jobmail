from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models import Campaign, EmailLog, User

router = APIRouter(prefix="/queue", tags=["queue"])


class CampaignRef(BaseModel):
    campaign_id: int | None = None


def _camp(db: Session, user: User, cid: int | None) -> Campaign:
    q = select(Campaign).where(Campaign.user_id == user.id)
    q = q.where(Campaign.id == cid) if cid else q.where(Campaign.status != "draft").order_by(Campaign.id.desc())
    c = db.scalar(q)
    if not c:
        raise HTTPException(404, "Campaign not found")
    return c


def _set(db: Session, user: User, cid: int | None, allowed: set[str], new: str) -> dict:
    c = _camp(db, user, cid)
    if c.status not in allowed:
        raise HTTPException(409, f"Cannot change a {c.status} campaign")
    c.status, c.note = new, None
    db.commit()
    if new == "running":
        wake.set()
    return {"status": c.status}


@router.post("/start")
def start(data: CampaignRef, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return _set(db, user, data.campaign_id, {"draft"}, "running")


@router.post("/pause")
def pause(data: CampaignRef, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return _set(db, user, data.campaign_id, {"running"}, "paused")


@router.post("/resume")
def resume(data: CampaignRef, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return _set(db, user, data.campaign_id, {"paused"}, "running")


@router.post("/cancel")
def cancel(data: CampaignRef, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    c = _camp(db, user, data.campaign_id)
    db.execute(update(EmailLog).where(EmailLog.campaign_id == c.id, EmailLog.status == "pending").values(status="cancelled"))
    c.status = "cancelled"
    db.commit()
    return {"status": c.status}


@router.post("/retry/{log_id}")
def retry(log_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    log = db.scalar(select(EmailLog).join(Campaign).where(EmailLog.id == log_id, Campaign.user_id == user.id))
    if not log or log.status not in ("failed", "cancelled"):
        raise HTTPException(404, "Only failed or cancelled emails can be retried")
    log.status, log.error_message = "pending", None
    log.campaign.status, log.campaign.note = "running", None
    db.commit()
    wake.set()
    return {"status": "pending"}


@router.get("/status")
def status(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    c = db.scalar(select(Campaign).where(Campaign.user_id == user.id, Campaign.status != "draft").order_by(Campaign.id.desc()))
    if not c:
        return {"campaign": None}
    n = dict(db.execute(select(EmailLog.status, func.count()).where(EmailLog.campaign_id == c.id).group_by(EmailLog.status)).all())
    return {"campaign": {"id": c.id, "subject": c.subject, "status": c.status, "note": c.note, "total": sum(n.values()),
                         "sent": n.get("sent", 0), "failed": n.get("failed", 0), "cancelled": n.get("cancelled", 0),
                         "pending": n.get("pending", 0) + n.get("processing", 0), "delaySeconds": user.send_delay_seconds}}
