import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import moviepy

try:
    import moviepy.editor
    moviepy.VideoFileClip = moviepy.editor.VideoFileClip
except ImportError:
    pass

from app.api import (
    routes_account, routes_music, routes_media,
    routes_brands, routes_posts, routes_folder_publisher,
    routes_bulk, routes_evergreen, routes_analytics, routes_engagement
)
from app.config import (
    APP_TITLE, APP_DESCRIPTION, APP_VERSION, STATIC_DIR,
    THUMBNAILS_DIR, MEDIA_QUEUE_DIR, UPLOADS_DIR
)
from app.core import database
from app.core.folder_queue_manager import ensure_brand_folders
from app.core.scheduler_worker import start_scheduler_loop, stop_scheduler_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    database.init_db()
    ensure_brand_folders()
    worker_task = asyncio.create_task(start_scheduler_loop(interval_seconds=15))
    yield
    # Shutdown tasks
    stop_scheduler_loop()
    worker_task.cancel()
    try:
        await worker_task
    except (asyncio.CancelledError, Exception):
        pass


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Assets & Media Previews
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if THUMBNAILS_DIR.exists():
    app.mount("/media/thumbnails", StaticFiles(directory=THUMBNAILS_DIR), name="media_thumbnails")

if MEDIA_QUEUE_DIR.exists():
    app.mount("/media/queue", StaticFiles(directory=MEDIA_QUEUE_DIR), name="media_queue")

if UPLOADS_DIR.exists():
    app.mount("/media/uploads", StaticFiles(directory=UPLOADS_DIR), name="media_uploads")

# Include API Routers
app.include_router(routes_account.router)
app.include_router(routes_music.router)
app.include_router(routes_media.router)
app.include_router(routes_brands.router)
app.include_router(routes_posts.router)
app.include_router(routes_folder_publisher.router)
app.include_router(routes_bulk.router)
app.include_router(routes_evergreen.router)
app.include_router(routes_analytics.router)
app.include_router(routes_engagement.router)


@app.get("/", tags=["Dashboard"])
@app.get("/planner", tags=["Dashboard"])
@app.get("/analytics", tags=["Dashboard"])
@app.get("/folders", tags=["Dashboard"])
@app.get("/vault", tags=["Dashboard"])
@app.get("/queue", tags=["Dashboard"])
@app.get("/engagement", tags=["Dashboard"])
def dashboard():
    """Serves the unified Social Hub & Instagram Automation Dashboard."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "status": "healthy",
        "service": APP_TITLE,
        "docs_url": "/docs"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify server status."""
    return {
        "status": "healthy",
        "service": APP_TITLE,
        "version": APP_VERSION,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


@app.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
def chrome_devtools_endpoint():
    """Silently handles Chrome DevTools binding checks."""
    return {}
