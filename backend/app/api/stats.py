from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models import Campaign, EmailLog, GmailAccount, Recipient, User
from app.schemas.stats import DashboardStats

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> DashboardStats:
    total = db.scalar(select(func.count()).select_from(Recipient).where(Recipient.user_id == user.id)) or 0
    rows = db.execute(
        select(EmailLog.status, func.count())
        .join(Campaign, Campaign.id == EmailLog.campaign_id)
        .where(Campaign.user_id == user.id)
        .group_by(EmailLog.status)
    ).all()
    by_status = {status: n for status, n in rows}
    gmail = db.scalar(select(GmailAccount).where(GmailAccount.user_id == user.id))
    return DashboardStats(
        total_recipients=total,
        sent=by_status.get("sent", 0),
        pending=by_status.get("pending", 0) + by_status.get("processing", 0),
        failed=by_status.get("failed", 0),
        gmail_connected=gmail is not None,
        gmail_email=user.email if gmail else None,
    )
