from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.security import read_session
from app.database.session import get_db
from app.models import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    uid = read_session(request.cookies.get("session", ""))
    user = db.get(User, uid) if uid else None
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
