import os

import requests
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from google.auth.transport import requests as grequests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decrypt, encrypt, make_session, read_session
from app.database.session import get_db
from app.models import GmailAccount, User
from app.models.entities import utcnow
from app.services.gmail import SCOPES
from datetime import timezone
from fastapi import HTTPException

os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
s = get_settings()
if not s.is_production:
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # allow http://localhost in dev only

router = APIRouter(prefix="/auth", tags=["auth"])


def _flow(state: str | None = None) -> Flow:
    cfg = {"web": {"client_id": s.google_client_id, "client_secret": s.google_client_secret,
                   "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token"}}
    return Flow.from_client_config(cfg, scopes=SCOPES, state=state, redirect_uri=s.google_redirect_uri)


def _cookie(resp, key, value, age):
    resp.set_cookie(key, value, httponly=True, samesite="lax", secure=s.is_production, max_age=age)


@router.post("/google")
def start(response: Response) -> dict:
    if not s.google_client_id or not s.google_client_secret:
        raise HTTPException(500, "Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
    flow = _flow()
    url, state = flow.authorization_url(access_type="offline", prompt="consent", include_granted_scopes="true")
    _cookie(response, "oauth_state", state, 600)
    _cookie(response, "oauth_cv", flow.code_verifier or "", 600)
    return {"url": url}


@router.get("/google/callback")
def callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None, db: Session = Depends(get_db)):
    fail = RedirectResponse(f"{s.frontend_url}/?auth=failed")
    if error or not code or not state or state != request.cookies.get("oauth_state"):  # CSRF check
        return fail
    try:
        flow = _flow(state)
        if request.cookies.get("oauth_cv"):
            flow.code_verifier = request.cookies["oauth_cv"]
        flow.fetch_token(code=code)
        creds = flow.credentials
        email = id_token.verify_oauth2_token(creds.id_token, grequests.Request(), s.google_client_id)["email"].lower()
    except Exception:  # noqa: BLE001
        return fail
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(email=email); db.add(user); db.commit(); db.refresh(user)
    acct = db.scalar(select(GmailAccount).where(GmailAccount.user_id == user.id))
    refresh = creds.refresh_token or (decrypt(acct.encrypted_refresh_token) if acct and acct.encrypted_refresh_token else None)
    if not acct:
        acct = GmailAccount(user_id=user.id, encrypted_access_token="")
        db.add(acct)
    acct.encrypted_access_token = encrypt(creds.token)
    acct.encrypted_refresh_token = encrypt(refresh) if refresh else None
    acct.token_expiry = creds.expiry.replace(tzinfo=timezone.utc) if creds.expiry else None
    acct.connected_at = utcnow()
    db.commit()
    resp = RedirectResponse(f"{s.frontend_url}/settings")
    _cookie(resp, "session", make_session(user.id), 7 * 86400)
    resp.delete_cookie("oauth_state"); resp.delete_cookie("oauth_cv")
    return resp


@router.get("/status")
def status(request: Request, db: Session = Depends(get_db)) -> dict:
    uid = read_session(request.cookies.get("session", ""))
    user = db.get(User, uid) if uid else None
    acct = db.scalar(select(GmailAccount).where(GmailAccount.user_id == user.id)) if user else None
    return {"authenticated": user is not None, "gmailConnected": acct is not None, "email": user.email if user else None}


@router.post("/disconnect")
def disconnect(request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    uid = read_session(request.cookies.get("session", ""))
    acct = db.scalar(select(GmailAccount).where(GmailAccount.user_id == uid)) if uid else None
    if acct:
        try:
            tok = decrypt(acct.encrypted_refresh_token or acct.encrypted_access_token)
            requests.post("https://oauth2.googleapis.com/revoke", params={"token": tok}, timeout=10)
        except Exception:  # noqa: BLE001
            pass
        db.delete(acct); db.commit()
    response.delete_cookie("session")
    return {"ok": True}
