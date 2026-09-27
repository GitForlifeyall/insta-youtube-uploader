from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import moviepy
try:
    import moviepy.editor
    moviepy.VideoFileClip = moviepy.editor.VideoFileClip
except ImportError:
    pass

from app.api import routes_account, routes_music, routes_media
from app.config import APP_TITLE, APP_DESCRIPTION, APP_VERSION

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION
)

# Enable CORS so your other projects (frontend or external microservices) can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(routes_account.router)
app.include_router(routes_music.router)
app.include_router(routes_media.router)


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint to verify server status."""
    return {
        "status": "healthy",
        "service": APP_TITLE,
        "version": APP_VERSION,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
