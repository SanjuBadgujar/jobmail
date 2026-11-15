from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models import User

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsIn(BaseModel):
    send_delay_seconds: int = Field(alias="sendDelaySeconds", ge=5, le=600)


@router.get("")
def get_settings_(user: User = Depends(get_current_user)) -> dict:
    return {"sendDelaySeconds": user.send_delay_seconds}


@router.put("")
def put_settings(data: SettingsIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    user.send_delay_seconds = data.send_delay_seconds
    db.commit()
    return {"sendDelaySeconds": user.send_delay_seconds}
