import base64
import hashlib
import logging
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.core.config import get_settings

s = get_settings()
logger = logging.getLogger("jobmail")


def _fernet() -> Fernet:
    raw = (s.token_encryption_key or s.secret_key).strip().strip('"').strip("'")
    try:
        return Fernet(raw.encode())
    except ValueError:
        logger.warning("TOKEN_ENCRYPTION_KEY is not a valid Fernet key; deriving one from it instead.")
        return Fernet(base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest()))


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()


def make_session(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=7)
    return jwt.encode({"sub": str(user_id), "exp": exp}, s.secret_key, algorithm="HS256")


def read_session(token: str) -> int | None:
    try:
        return int(jwt.decode(token, s.secret_key, algorithms=["HS256"])["sub"])
    except (JWTError, ValueError, KeyError):
        return None