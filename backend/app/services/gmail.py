import base64
import mimetypes
from datetime import timezone
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request as GRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import get_settings
from app.core.security import decrypt, encrypt

SCOPES = ["https://www.googleapis.com/auth/gmail.send", "openid", "https://www.googleapis.com/auth/userinfo.email"]
s = get_settings()


def build_mime(sender: str, to: str, subject: str, body: str, attachment: bytes | Path | None = None, filename: str | None = None) -> str:
    msg = EmailMessage()  # raises ValueError on header injection (newlines)
    msg["To"], msg["From"], msg["Subject"] = to, sender, subject
    msg.set_content(body)
    if attachment is not None:
        content = attachment if isinstance(attachment, bytes) else attachment.read_bytes()
        name = filename or (attachment.name if isinstance(attachment, Path) else "attachment")
        main, sub = (mimetypes.guess_type(name)[0] or "application/octet-stream").split("/", 1)
        msg.add_attachment(content, maintype=main, subtype=sub, filename=name)
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def credentials_for(db, acct) -> Credentials:
    creds = Credentials(
        token=decrypt(acct.encrypted_access_token),
        refresh_token=decrypt(acct.encrypted_refresh_token) if acct.encrypted_refresh_token else None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=s.google_client_id, client_secret=s.google_client_secret, scopes=SCOPES,
    )
    if acct.token_expiry:
        creds.expiry = acct.token_expiry.replace(tzinfo=None)
    if not creds.valid:
        creds.refresh(GRequest())  # RefreshError if revoked/expired
        acct.encrypted_access_token = encrypt(creds.token)
        acct.token_expiry = creds.expiry.replace(tzinfo=timezone.utc) if creds.expiry else None
        db.commit()
    return creds


def send_raw(creds: Credentials, raw: str) -> str:
    svc = build("gmail", "v1", credentials=creds, cache_discovery=False)
    return svc.users().messages().send(userId="me", body={"raw": raw}).execute()["id"]
