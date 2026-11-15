import csv
import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models import Recipient, User
from app.services.templating import normalize_email, split_addresses

router = APIRouter(prefix="/recipients", tags=["recipients"])
FIELDS = ("name", "company", "position")
MAX_CSV = 5 * 1024 * 1024


class BulkIn(BaseModel):
    text: str = Field(min_length=1, max_length=200_000)


class EditIn(BaseModel):
    name: str | None = Field(None, max_length=200)
    company: str | None = Field(None, max_length=200)
    position: str | None = Field(None, max_length=200)


def out(r: Recipient) -> dict:
    return {"id": r.id, "name": r.name, "email": r.email, "company": r.company, "position": r.position}


def add_rows(db: Session, user: User, rows: list[dict]) -> dict:
    existing = {e for (e,) in db.execute(select(Recipient.email).where(Recipient.user_id == user.id))}
    added, invalid, dups = 0, [], []
    for row in rows:
        email = normalize_email(row.get("email", ""))
        if not email:
            invalid.append(row.get("email", "")); continue
        if email in existing:
            dups.append(email); continue
        existing.add(email)
        db.add(Recipient(user_id=user.id, email=email, **{f: (row.get(f) or "").strip()[:200] or None for f in FIELDS}))
        added += 1
    db.commit()
    return {"added": added, "invalid": invalid, "duplicates": dups}


@router.post("", status_code=201)
def create(data: BulkIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return add_rows(db, user, split_addresses(data.text))


@router.get("")
def list_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    return [out(r) for r in db.scalars(select(Recipient).where(Recipient.user_id == user.id).order_by(Recipient.id))]


def _own(db: Session, user: User, rid: int) -> Recipient:
    r = db.scalar(select(Recipient).where(Recipient.id == rid, Recipient.user_id == user.id))
    if not r:
        raise HTTPException(404, "Recipient not found")
    return r


@router.put("/{rid}")
def edit(rid: int, data: EditIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    r = _own(db, user, rid)
    for f in FIELDS:
        setattr(r, f, (getattr(data, f) or "").strip() or None)
    db.commit()
    return out(r)


@router.delete("/{rid}", status_code=204)
def delete(rid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    db.delete(_own(db, user, rid)); db.commit()


@router.post("/import-csv", status_code=201)
async def import_csv(file: UploadFile, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    raw = await file.read(MAX_CSV + 1)
    if len(raw) > MAX_CSV:
        raise HTTPException(413, "CSV too large (max 5 MB)")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig", errors="replace")))
    rows = [{(k or "").strip().lower(): (v if isinstance(v, str) else "") for k, v in r.items()} for _, r in zip(range(5000), reader)]
    return add_rows(db, user, rows)
