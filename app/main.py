from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.monitoring import init_monitoring
from app.core.error_handler import error_handler
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import rate_limit_middleware
from app.middleware.csrf import CSRFMiddleware
from app.middleware.upload import UploadMiddleware
from app.core.cache import init_cache

# Import API routers
from app.api import (
    auth as api_auth,
    media as api_media,
    jobsites as api_jobsites,
    posts as api_posts,
    email as api_email,
    ai as api_ai,
    social as api_social
)

# Import Web UI routers
from app.webui import (
    auth as webui_auth,
    dashboard as webui_dashboard,
    media as webui_media,
    jobsites as webui_jobsites,
    posts as webui_posts,
    upload as webui_upload,
    settings as webui_settings,
    social as webui_social
)

app = FastAPI(
    title="LeadMagic",
    description="Social automation tool for contractors, builders, and service pros.",
    version="1.0.0"
)

# Initialize monitoring
init_monitoring(app)

# Serve static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Add middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(UploadMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://leadmagic.app",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)
app.add_middleware(CSRFMiddleware, secret_key="your-secret-key")

# Initialize cache
@app.on_event("startup")
async def startup_event():
    await init_cache()

# Add exception handler
app.add_exception_handler(Exception, error_handler)

# Register API routers
app.include_router(api_auth.router, prefix="/api/auth", tags=["API: Authentication"])
app.include_router(api_media.router, prefix="/api/media", tags=["API: Media"])
app.include_router(api_jobsites.router, prefix="/api/jobsites", tags=["API: Jobsites"])
app.include_router(api_posts.router, prefix="/api/posts", tags=["API: Posts"])
app.include_router(api_email.router, prefix="/api/email", tags=["API: Email"])
app.include_router(api_ai.router, prefix="/api/ai", tags=["API: AI"])
app.include_router(api_social.router, prefix="/api/social", tags=["API: Social"])

# Register Web UI routers
app.include_router(webui_auth.router, tags=["Web: Authentication"])
app.include_router(webui_dashboard.router, tags=["Web: Dashboard"])
app.include_router(webui_media.router, tags=["Web: Media"])
app.include_router(webui_jobsites.router, tags=["Web: Jobsites"])
app.include_router(webui_posts.router, tags=["Web: Posts"])
app.include_router(webui_upload.router, tags=["Web: Upload"])
app.include_router(webui_settings.router, tags=["Web: Settings"])
app.include_router(webui_social.router, tags=["Web: Social"])

@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")