import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager

from app.config import VIDEOS_OUTPUT_DIR, CAROUSELS_OUTPUT_DIR, THUMBNAILS_DIR
from starlette.middleware.gzip import GZipMiddleware
from app.core.database import init_db
from app.core.analytics_service import init_analytics_tables
from app.core.scheduler_worker import start_scheduler_loop, stop_scheduler_loop
from app.api.routes_brands import router as brands_router
from app.api.routes_posts import router as posts_router
from app.api.routes_media import router as media_router
from app.api.routes_analytics import router as analytics_router
from app.api.routes_best_times import router as best_times_router
from app.api.routes_competitors import router as competitors_router
from app.api.routes_evergreen import router as evergreen_router
from app.api.routes_bulk import router as bulk_router
from app.api.routes_accounts import router as accounts_router
from app.api.routes_folder_publisher import router as folder_publisher_router
from app.core.folder_queue_manager import ensure_brand_folders
from app.config import MEDIA_QUEUE_DIR
from app.core.credentials_sync import sync_credentials_from_env


import logging

logger = logging.getLogger("SocialHub")


async def auto_refresh_accounts_on_startup(delay: int = 5):
    """Waits for sibling microservices to bind, then auto-refreshes account statuses."""
    await asyncio.sleep(delay)
    try:
        from app.api.routes_accounts import get_accounts_status
        status = await asyncio.to_thread(get_accounts_status)
        logger.info(f"🔄 Account status auto-refreshed: {status.get('total_verified', 0)}/{status.get('total_accounts', 0)} accounts verified.")
    except Exception as e:
        logger.warning(f"Could not auto-refresh accounts status on startup: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    init_analytics_tables()
    ensure_brand_folders()
    worker_task = asyncio.create_task(start_scheduler_loop(interval_seconds=15))
    asyncio.create_task(asyncio.to_thread(sync_credentials_from_env, 3))
    asyncio.create_task(auto_refresh_accounts_on_startup(delay=5))
    yield
    # Shutdown
    stop_scheduler_loop()
    worker_task.cancel()



app = FastAPI(
    title="Social Hub - Multi-Brand Social Media Automation",
    description="Multi-Brand Folder-Based Auto-Publishing Engine",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(folder_publisher_router)
app.include_router(brands_router)
app.include_router(posts_router)
app.include_router(bulk_router)
app.include_router(media_router)
app.include_router(analytics_router)
app.include_router(best_times_router)
app.include_router(competitors_router)
app.include_router(evergreen_router)
app.include_router(accounts_router)


from fastapi.responses import FileResponse, Response

# Mount media paths for live preview
if THUMBNAILS_DIR.exists():
    app.mount("/media/thumbnails", StaticFiles(directory=str(THUMBNAILS_DIR)), name="media_thumbnails")
if VIDEOS_OUTPUT_DIR.exists():
    app.mount("/media/videos", StaticFiles(directory=str(VIDEOS_OUTPUT_DIR)), name="media_videos")
if CAROUSELS_OUTPUT_DIR.exists():
    app.mount("/media/carousels", StaticFiles(directory=str(CAROUSELS_OUTPUT_DIR)), name="media_carousels")
if MEDIA_QUEUE_DIR.exists():
    app.mount("/media/queue", StaticFiles(directory=str(MEDIA_QUEUE_DIR)), name="media_queue")

# Mount static files and serve dashboard at root
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        svg_favicon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">⚡</text></svg>"""
        return Response(content=svg_favicon, media_type="image/svg+xml")

    @app.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
    async def chrome_devtools():
        return Response(status_code=204)

    @app.get("/")
    async def serve_dashboard():
        """Serve Metricool Planner & Analytics UI dashboard"""
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


