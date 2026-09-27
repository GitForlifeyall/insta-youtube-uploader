from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
SESSIONS_DIR = BASE_DIR / "sessions"
UPLOADS_DIR = BASE_DIR / "uploads"

SESSIONS_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

# API Metadata
APP_TITLE = "Instagram Automation API"
APP_DESCRIPTION = (
    "Production-ready FastAPI microservice wrapping instagrapi. "
    "Features multi-account session management, official music catalogue search, "
    "and media uploads (Reels with music, Feed Posts/Carousels, and Stories)."
)
APP_VERSION = "1.0.0"
