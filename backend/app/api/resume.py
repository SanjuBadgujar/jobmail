import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.database.session import get_db
from app.models import Resume, User

router = APIRouter(prefix="/resume", tags=["resume"])
s = get_settings()
MAGIC = {".pdf": b"%PDF-", ".docx": b"PK\x03\x04"}


def info(r: Resume | None) -> dict | None:
    return {"id": r.id, "filename": r.filename, "fileSize": r.file_size} if r else None


def _current(db: Session, user: User) -> Resume | None:
    return db.scalar(select(Resume).where(Resume.user_id == user.id).order_by(Resume.id.desc()))


def _remove(db: Session, r: Resume | None) -> None:
    if r:
        Path(r.storage_path).unlink(missing_ok=True); db.delete(r)


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
    folder = Path(s.upload_dir) / str(user.id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid.uuid4().hex}{ext}"  # random name; never served publicly
    path.write_bytes(data)
    _remove(db, _current(db, user))
    r = Resume(user_id=user.id, filename=name[:255], storage_path=str(path), file_size=len(data))
    db.add(r); db.commit(); db.refresh(r)
    return info(r)


@router.get("")
def get_resume(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict | None:
    return info(_current(db, user))


@router.delete("", status_code=204)
def delete_resume(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    _remove(db, _current(db, user)); db.commit()
