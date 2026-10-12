from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
SESSIONS_DIR = BASE_DIR / "sessions"
UPLOADS_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "app" / "static"
DATA_DIR = BASE_DIR / "data"
THUMBNAILS_DIR = DATA_DIR / "thumbnails"
DOWNLOADS_DIR = DATA_DIR / "downloads"
MEDIA_QUEUE_DIR = BASE_DIR / "media_queue"
TEMPLATES_DIR = BASE_DIR / "templates"

SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_QUEUE_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# API Metadata
APP_TITLE = "Social Hub & Instagram Automation Engine"
APP_DESCRIPTION = (
    "Production-ready FastAPI social media engine and automation hub. "
    "Features multi-brand folder vault, visual planner, evergreen recycling, "
    "bulk CSV importer, and multi-account Instagram publishing."
)
APP_VERSION = "2.0.0"
