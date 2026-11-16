from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.database.session import get_db
from app.models import Resume, ResumeFile, User

router = APIRouter(prefix="/resume", tags=["resume"])
s = get_settings()
MAGIC = {".pdf": b"%PDF-", ".docx": b"PK\x03\x04"}


def info(r: Resume | None) -> dict | None:
    return {"id": r.id, "filename": r.filename, "fileSize": r.file_size} if r else None


def _current(db: Session, user: User) -> Resume | None:
    return db.scalar(select(Resume).where(Resume.user_id == user.id).order_by(Resume.id.desc()))


def _remove(db: Session, r: Resume | None) -> None:
    if r:
        db.execute(delete(ResumeFile).where(ResumeFile.resume_id == r.id))
        db.delete(r)


@router.post("/upload", status_code=201)
async def upload(file: UploadFile, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    name = Path(file.filename or "").name
    ext = Path(name).suffix.lower()
    if ext not in MAGIC:
        raise HTTPException(400, "Only PDF or DOCX files are allowed")
    data = await file.read(s.max_upload_mb * 1024 * 1024 + 1)
    if len(data) > s.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File too large (max {s.max_upload_mb} MB)")
    if not data.startswith(MAGIC[ext]):
        raise HTTPException(400, "File content does not match its extension")
    _remove(db, _current(db, user))
    r = Resume(user_id=user.id, filename=name[:255], storage_path="database", file_size=len(data))
    db.add(r); db.flush()
    db.add(ResumeFile(resume_id=r.id, data=data))  # stored privately in the database, never served publicly
    db.commit(); db.refresh(r)
    return info(r)


@router.get("")
def get_resume(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict | None:
    r = _current(db, user)
    if r and db.scalar(select(ResumeFile.id).where(ResumeFile.resume_id == r.id)) is None:
        return None  # old record whose file was lost: ask the user to upload again
    return info(r)


@router.delete("", status_code=204)
def delete_resume(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    _remove(db, _current(db, user)); db.commit()
