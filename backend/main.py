import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

try:
    from backend.config import settings
    from backend.database import init_db
    from backend.logging_config import configure_logging
    from backend.routes import auth, chat, learning, metrics
except ModuleNotFoundError:
    from config import settings
    from database import init_db
    from logging_config import configure_logging
    from routes import auth, chat, learning, metrics

logger = configure_logging()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)
init_db()

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts or ["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(learning.router)
app.include_router(chat.router)
app.include_router(auth.router)
app.include_router(metrics.router)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    logger.info("%s %s -> %s in %sms", request.method, request.url.path, response.status_code, duration_ms)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "errors": exc.errors(),
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error at %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": request.url.path},
    )


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "environment": settings.environment,
        "app": settings.app_name,
    }
