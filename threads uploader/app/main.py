from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure threads patch is imported at application startup
import app.core.threads_patch
from app.api import routes_account, routes_posts
from app.config import APP_TITLE, APP_DESCRIPTION, APP_VERSION

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for external microservices and frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(routes_account.router)
app.include_router(routes_posts.router)


@app.get("/", tags=["Health"])
async def health_check():
    """Root health-check endpoint returning service state and documentation paths."""
    return {
        "status": "healthy",
        "service": APP_TITLE,
        "version": APP_VERSION,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
