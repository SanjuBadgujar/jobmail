import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models import Campaign, EmailLog, GmailAccount, Recipient, User
from app.services.templating import render

router = APIRouter(prefix="/emails", tags=["emails"])


class Draft(BaseModel):
    subject: str = Field("", max_length=500)
    body: str = Field("", max_length=20000)


class SendIn(BaseModel):
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1, max_length=20000)
    recipient_ids: list[int] | None = None
    start: bool = True


class PreviewIn(BaseModel):
    subject: str = Field(max_length=500)
    body: str = Field(max_length=20000)
    recipient_id: int


@router.post("/preview")
def preview(data: PreviewIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    rec = db.scalar(select(Recipient).where(Recipient.id == data.recipient_id, Recipient.user_id == user.id))
    if not rec:
        raise HTTPException(404, "Recipient not found")
    return {"to": rec.email, "subject": render(data.subject, rec), "body": render(data.body, rec)}


@router.post("/send", status_code=201)
def send(data: SendIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    if not db.scalar(select(GmailAccount).where(GmailAccount.user_id == user.id)):
        raise HTTPException(409, "Connect Gmail first")
    q = select(Recipient).where(Recipient.user_id == user.id)
    if data.recipient_ids:
        q = q.where(Recipient.id.in_(data.recipient_ids))
    recs = db.scalars(q).all()
    if not recs:
        raise HTTPException(400, "No recipients selected")
    camp = Campaign(user_id=user.id, subject=data.subject, body=data.body, status="running" if data.start else "draft")
    camp.logs = [EmailLog(recipient_id=r.id) for r in recs]
    db.add(camp); db.commit()
    return {"campaignId": camp.id, "total": len(recs)}


@router.post("/draft")
def save_draft(data: Draft, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    d = db.scalar(select(Campaign).where(Campaign.user_id == user.id, Campaign.status == "draft", ~Campaign.logs.any()))
    if not d:
        d = Campaign(user_id=user.id, subject="", body="", status="draft"); db.add(d)
    d.subject, d.body = data.subject, data.body
    db.commit()
    return {"ok": True}


@router.get("/draft")
def get_draft(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    d = db.scalar(select(Campaign).where(Campaign.user_id == user.id, Campaign.status == "draft", ~Campaign.logs.any()))
    return {"subject": d.subject if d else "", "body": d.body if d else ""}


def _hist(cols, user: User, status: str | None, q: str | None):
    stmt = (select(*cols).select_from(EmailLog).join(Recipient, Recipient.id == EmailLog.recipient_id)
            .join(Campaign, Campaign.id == EmailLog.campaign_id).where(Campaign.user_id == user.id, Campaign.status != "draft"))
    if status:
        stmt = stmt.where(EmailLog.status == status)
    if q:
        stmt = stmt.where(or_(Recipient.email.ilike(f"%{q}%"), Campaign.subject.ilike(f"%{q}%")))
    return stmt


def _row(log: EmailLog, rec: Recipient, camp: Campaign) -> dict:
    return {"id": log.id, "recipient": rec.email, "subject": camp.subject, "time": (log.sent_at or camp.created_at).isoformat(),
            "status": log.status, "error": log.error_message, "gmailMessageId": log.gmail_message_id}


@router.get("/history")
def history(status: str | None = None, q: str | None = Query(None, max_length=100), page: int = Query(1, ge=1),
            page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    total = db.scalar(_hist([func.count(EmailLog.id)], user, status, q)) or 0
    rows = db.execute(_hist([EmailLog, Recipient, Campaign], user, status, q).order_by(EmailLog.id.desc())
                      .limit(page_size).offset((page - 1) * page_size)).all()
    return {"items": [_row(*r) for r in rows], "total": total}


def _safe(v) -> str:
    v = "" if v is None else str(v)
    return "'" + v if v[:1] in "=+-@" else v  # neutralise CSV formula injection


@router.get("/history/export.csv")
def export(status: str | None = None, q: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["Recipient", "Subject", "Time", "Status", "Error", "Gmail message ID"])
    for r in db.execute(_hist([EmailLog, Recipient, Campaign], user, status, q).order_by(EmailLog.id.desc())).all():
        d = _row(*r)
        w.writerow([_safe(d[k]) for k in ("recipient", "subject", "time", "status", "error", "gmailMessageId")])
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=history.csv"})


@router.get("/{log_id}")
def detail(log_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    row = db.execute(_hist([EmailLog, Recipient, Campaign], user, None, None).where(EmailLog.id == log_id)).first()
    if not row:
        raise HTTPException(404, "Email not found")
    return _row(*row)
