import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.services.errors import DomainError

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(
    title="SeatSync API",
    version="1.0.0",
    description=(
        "Concurrent ticket-booking backend demonstrating seat locks, payment "
        "idempotency, booking state transitions, and an outbox event pattern."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(Exception)
async def unexpected_error_handler(_: Request, exc: Exception):
    logging.exception("Unhandled application error", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(api_router, prefix=settings.api_v1_prefix)
app.mount("/demo", StaticFiles(directory="web", html=True), name="demo")


@app.get("/", tags=["root"])
def root() -> dict:
    return {
        "name": "SeatSync",
        "docs": "/docs",
        "health": f"{settings.api_v1_prefix}/health",
        "demo": "/demo",
    }
