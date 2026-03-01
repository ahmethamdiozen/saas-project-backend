from fastapi import FastAPI, Request, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as user_router
from app.modules.jobs.router import router as jobs_router
from app.modules.subscriptions.router import router as subscriptions_router
from app.modules.admin.router import router as admin_router
from app.modules.rag.router import router as rag_router
from app.core.config import settings
from app.core.logging import logger
from app.core.rate_limit import rate_limiter
from app.db import models

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    dependencies=[Depends(rate_limiter)]
)

# CORS Middleware Setup - SHOULD BE FIRST
origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
if "http://localhost:5173" not in origins:
    origins.append("http://localhost:5173")
if "http://127.0.0.1:5173" not in origins:
    origins.append("http://127.0.0.1:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Exception: {exc}", exc_info=True)
    
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact support."},
    )
    origin = request.headers.get("origin")
    if origin in origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response

# Health Check Endpoint
@app.get("/health", tags=["Infrastructure"])
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}

# Include Routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(user_router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(jobs_router, prefix=f"{settings.API_V1_STR}/jobs", tags=["Jobs"])
app.include_router(subscriptions_router, prefix=f"{settings.API_V1_STR}/subscriptions", tags=["Subscriptions"])
app.include_router(rag_router, prefix=f"{settings.API_V1_STR}/rag", tags=["RAG / Documents"])
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}/admin", tags=["Admin Dashboard"])
