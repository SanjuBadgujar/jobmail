import logging
import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, emails, health, queue, recipients, resume, settings as settings_api, stats
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.workers.queue import worker_loop
from app.database.session import Base, engine
import app.models  # noqa: F401  (registers tables)

setup_logging()
logger = logging.getLogger("jobmail")
settings = get_settings()

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    stop = threading.Event()
    if os.getenv("DISABLE_WORKER") != "1":
        threading.Thread(target=worker_loop, args=(stop,), daemon=True).start()
    yield
    stop.set()


app = FastAPI(title="JobMail API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(health.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
for r in (auth, recipients, resume, emails, queue, settings_api):
    app.include_router(r.router, prefix="/api")
