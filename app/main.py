from fastapi import FastAPI, Request, status, Depends, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from sqlalchemy import text
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as user_router
from app.modules.jobs.router import router as jobs_router
from app.modules.subscriptions.router import router as subscriptions_router
from app.modules.admin.router import router as admin_router
from app.modules.rag.router import router as rag_router
from app.modules.ws.router import router as ws_router
from app.modules.webhooks.stripe import router as stripe_webhook_router
from app.core.config import settings
from app.core.logging import logger
from app.core.rate_limit import rate_limiter
from app.db import models  # noqa: F401
from app.db.session import get_db

# ---------------------------------------------------------------------------
# OpenAPI tag metadata
# ---------------------------------------------------------------------------
openapi_tags = [
    {
        "name": "Authentication",
        "description": "Register, login, logout, token refresh, email verification, and password reset.",
    },
    {
        "name": "Users",
        "description": "Read and update the authenticated user's profile, change password, delete account.",
    },
    {
        "name": "Subscriptions",
        "description": "List plans, create Stripe checkout sessions, access the billing portal.",
    },
    {
        "name": "Jobs",
        "description": "Submit background jobs, poll status, cancel or retry.",
    },
    {
        "name": "RAG / Documents",
        "description": "Upload documents, trigger ingestion, and run retrieval-augmented queries.",
    },
    {
        "name": "Admin Dashboard",
        "description": "User management (ban/unban), subscription overrides, platform statistics. Requires **admin** role.",
    },
    {
        "name": "WebSocket",
        "description": "Real-time job-progress updates over WebSocket.",
    },
    {
        "name": "Webhooks",
        "description": "Stripe event ingestion. Called by Stripe, not by clients.",
    },
    {
        "name": "Infrastructure",
        "description": "Health check and liveness probes.",
    },
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "A production-ready SaaS backend.\n\n"
        "## Authentication\n"
        "All protected routes require an `access_token` **httpOnly cookie** set by `POST /auth/login`.\n\n"
        "## Rate limiting\n"
        "Global rate limit applies to all endpoints. Exceeding it returns **429 Too Many Requests**.\n\n"
        "## Error format\n"
        "All errors follow `{\"error\": \"<message>\", \"code\": \"<SNAKE_CASE_CODE>\"}`."
    ),
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=None,   # replaced with custom dark-theme route below
    redoc_url=None,  # replaced below
    openapi_tags=openapi_tags,
    dependencies=[Depends(rate_limiter)],
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
if settings.ENVIRONMENT != "production":
    for local in ("http://localhost:5173", "http://127.0.0.1:5173"):
        if local not in origins:
            origins.append(local)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Custom docs — dark theme via swagger_ui_parameters
# ---------------------------------------------------------------------------
_SWAGGER_FAVICON = "https://fastapi.tiangolo.com/img/favicon.png"

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=f"{settings.PROJECT_NAME} — API Docs",
        swagger_favicon_url=_SWAGGER_FAVICON,
        swagger_ui_parameters={
            "syntaxHighlight.theme": "obsidian",
            "tryItOutEnabled": True,
            "displayRequestDuration": True,
            "filter": True,
            "persistAuthorization": True,
        },
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_ui():
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=f"{settings.PROJECT_NAME} — ReDoc",
        redoc_favicon_url=_SWAGGER_FAVICON,
    )

# ---------------------------------------------------------------------------
# Exception handlers — unified error envelope
# ---------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code = _status_to_code(exc.status_code, exc.detail)
    response = JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "code": code},
    )
    origin = request.headers.get("origin")
    if origin in origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", exc_info=True)
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An internal server error occurred.", "code": "INTERNAL_SERVER_ERROR"},
    )
    origin = request.headers.get("origin")
    if origin in origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


def _status_to_code(status_code: int, detail: str) -> str:
    """Derive a SCREAMING_SNAKE_CASE code from status + detail."""
    if isinstance(detail, str):
        slug = detail.upper().replace(" ", "_").replace("-", "_")
        import re
        slug = re.sub(r"[^A-Z0-9_]", "", slug)[:64]
        if slug:
            return slug
    _defaults = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    return _defaults.get(status_code, "ERROR")

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["Infrastructure"],
    summary="Liveness / readiness probe",
    response_description="Service health status",
)
async def health_check(db=Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "version": settings.VERSION, "db": "ok"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "version": settings.VERSION, "db": "error"},
        )

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(user_router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(jobs_router, prefix=f"{settings.API_V1_STR}/jobs", tags=["Jobs"])
app.include_router(subscriptions_router, prefix=f"{settings.API_V1_STR}/subscriptions", tags=["Subscriptions"])
app.include_router(rag_router, prefix=f"{settings.API_V1_STR}/rag", tags=["RAG / Documents"])
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}/admin", tags=["Admin Dashboard"])
app.include_router(ws_router, prefix=f"{settings.API_V1_STR}", tags=["WebSocket"])
app.include_router(stripe_webhook_router, prefix="/webhooks", tags=["Webhooks"])
