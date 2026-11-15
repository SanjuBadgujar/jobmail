import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["DISABLE_WORKER"] = "1"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.database import session as db_session

db_session.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
db_session.SessionLocal.configure(bind=db_session.engine)

import app.main as main  # noqa: E402
from app.core.security import make_session  # noqa: E402
from app.models import User  # noqa: E402

main.engine = db_session.engine


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    db_session.Base.metadata.drop_all(db_session.engine)
    with TestClient(main.app) as c:
        yield c


def login(client, email="me@x.com") -> int:
    db = db_session.SessionLocal()
    u = User(email=email); db.add(u); db.commit()
    uid = u.id; db.close()
    client.cookies.set("session", make_session(uid))
    return uid
