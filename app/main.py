import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db.database import init_db
from app.routers import events, analytics, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting up — initializing database...")
    init_db()
    logger.info("database ready.")
    yield
    logger.info("shutting down.")


app = FastAPI(
    title="Feature Usage Analytics API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    logger.info(
        "method=%s path=%s status=%s duration=%.1fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.exception("unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(health.router, tags=["Health"])
app.include_router(events.router, prefix="/events", tags=["Events"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
