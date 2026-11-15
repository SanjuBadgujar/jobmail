import email
from pathlib import Path
from types import SimpleNamespace

from app.core.security import encrypt
from app.database import session as dbs
from app.models import Campaign, EmailLog, GmailAccount, Recipient
from app.services.gmail import build_mime
from app.services.templating import render
from app.workers import queue
from tests.conftest import login


def test_recipients_paste_dupes_and_isolation(client):
    login(client)
    r = client.post("/api/recipients", json={"text": "a@x.com, b@x.com\nbad-email a@x.com"}).json()
    assert r["added"] == 2 and r["invalid"] == ["bad-email"] and r["duplicates"] == ["a@x.com"]
    assert len(client.get("/api/recipients").json()) == 2
    client.cookies.clear(); login(client, "other@x.com")
    assert client.get("/api/recipients").json() == []


def test_csv_import(client):
    login(client)
    csv_ = b"email,name,company,position\nr1@x.com,John,ABC,AI Engineer\nnope,X,Y,Z\n"
    r = client.post("/api/recipients/import-csv", files={"file": ("c.csv", csv_, "text/csv")}).json()
    assert r["added"] == 1 and r["invalid"] == ["nope"]


def test_render_and_mime_attachment(tmp_path: Path):
    rec = SimpleNamespace(name="John", company="ABC", position="AI Engineer")
    assert render("Hi {{name}} at {{company}} ({{ position }})", rec) == "Hi John at ABC (AI Engineer)"
    f = tmp_path / "cv.pdf"; f.write_bytes(b"%PDF-1.4 test")
    import base64
    raw = build_mime("me@x.com", "r@x.com", "Hello", "Body", f, "cv.pdf")
    msg = email.message_from_bytes(base64.urlsafe_b64decode(raw))
    assert msg["To"] == "r@x.com" and [p.get_filename() for p in msg.walk() if p.get_filename()] == ["cv.pdf"]


def test_resume_validation(client):
    login(client)
    assert client.post("/api/resume/upload", files={"file": ("a.exe", b"MZ", "application/octet-stream")}).status_code == 400
    assert client.post("/api/resume/upload", files={"file": ("a.pdf", b"not a pdf", "application/pdf")}).status_code == 400


def test_queue_sends_each_once(client, monkeypatch):
    uid = login(client)
    sent = []
    monkeypatch.setattr(queue, "credentials_for", lambda db, a: None)
    monkeypatch.setattr(queue, "send_raw", lambda c, raw: sent.append(raw) or f"id{len(sent)}")
    db = dbs.SessionLocal()
    db.add(GmailAccount(user_id=uid, encrypted_access_token=encrypt("t")))
    db.add_all([Recipient(user_id=uid, email="a@x.com"), Recipient(user_id=uid, email="b@x.com")]); db.commit()
    ids = [r.id for r in db.query(Recipient)]
    c = Campaign(user_id=uid, subject="S", body="B", status="running")
    c.logs = [EmailLog(recipient_id=i) for i in ids]; db.add(c); db.commit(); db.close()
    queue.process_one(); queue.process_one(); queue.process_one(); queue.process_one()
    assert len(sent) == 2
    st = client.get("/api/queue/status").json()["campaign"]
    assert st["status"] == "completed" and st["sent"] == 2
