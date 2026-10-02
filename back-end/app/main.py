from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes_admin import router as admin_router
from app.api.routes_download import router as download_router
from app.api.routes_extract import router as extract_router
from app.api.routes_health import router as health_router
from app.api.routes_jobs import router as jobs_router
from app.config import get_settings
from app.core.errors import DownloaderException

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure ephemeral storage directory exists
    _ = settings.storage_path
    yield


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DownloaderException)
async def downloader_exception_handler(request: Request, exc: DownloaderException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": exc.code,
            "error_message": exc.message,
            "details": exc.details,
        },
    )


# Register Routers
app.include_router(health_router)
app.include_router(extract_router)
app.include_router(jobs_router)
app.include_router(download_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs",
    }
