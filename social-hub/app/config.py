import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECTS_ROOT = BASE_DIR.parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "social_hub.db"

THUMBNAILS_DIR = DATA_DIR / "thumbnails"
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

DOWNLOADS_DIR = DATA_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Connected Microservices
PORT = int(os.getenv("PORT", "8000"))
INSTA_FB_API_URL = os.getenv("INSTA_FB_API_URL", "http://localhost:8001")
THREADS_API_URL = os.getenv("THREADS_API_URL", "http://localhost:8002")
YOUTUBE_API_URL = os.getenv("YOUTUBE_API_URL", "http://localhost:8003")

# Directories for Media & Content
NEW_LYRICS_DIR = PROJECTS_ROOT / "new-lyrics-2"
VIDEOS_OUTPUT_DIR = NEW_LYRICS_DIR / "videos" / "output"
CAROUSELS_OUTPUT_DIR = VIDEOS_OUTPUT_DIR / "carousels"
MEDIA_QUEUE_DIR = PROJECTS_ROOT / "media_queue"
MEDIA_QUEUE_DIR.mkdir(parents=True, exist_ok=True)

# Session directories of uploaders for account auto-discovery
INSTA_SESSIONS_DIR = PROJECTS_ROOT / "Insta+Facebook uploader" / "sessions"
THREADS_SESSIONS_DIR = PROJECTS_ROOT / "threads uploader" / "sessions"
