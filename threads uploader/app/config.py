from pathlib import Path

BASE_DIR= Path(__file__).resolve().parent.parent

SESSIONS_DIR = BASE_DIR/"sessions"

UPLOADS_DIR = BASE_DIR/"uploads"

SESSIONS_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

APP_TITLE = "Threads Automation API"
APP_DESCRIPTION = (
    "Asynchronous FastAPI microservice for Meta Threads powered by threads-api. "
    "Features multi-account encrypted token caching, text threads, "
    "image/carousel uploads, link posts, replies, and quotes."
)
APP_VERSION = "1.0.0"
