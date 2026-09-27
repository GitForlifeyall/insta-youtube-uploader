"""
📁 API Routes for Folder Queue Management & 1-Click Multi-Brand Publishing
"""

import sys
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List

from app.config import MEDIA_QUEUE_DIR
from app.core.database import list_brands, get_brand
from app.core.folder_queue_manager import (
    get_all_brands_folder_status,
    publish_next_for_brand,
    publish_next_for_all_brands,
    open_brand_folder_in_os,
    ensure_brand_folders,
    get_brand_folder_path
)

router = APIRouter(prefix="/api/folder-queue", tags=["Folder Queue Auto-Publisher"])


@router.get("/status")
def get_status() -> List[Dict[str, Any]]:
    """Returns folder queue status, counts, and previews for all brands."""
    try:
        return get_all_brands_folder_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish-brand/{brand_id}")
def publish_brand(brand_id: str) -> Dict[str, Any]:
    """Publishes the next pending media item for a specific brand across all its active platforms."""
    try:
        result = publish_next_for_brand(brand_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish-all")
def publish_all() -> Dict[str, Any]:
    """Master trigger: Publishes the next pending media item for EVERY brand across all active platforms."""
    try:
        result = publish_next_for_all_brands()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/open-folder/{brand_id}")
def open_folder(brand_id: str) -> Dict[str, Any]:
    """Opens the brand's local media queue folder in File Explorer."""
    brand = get_brand(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    success = open_brand_folder_in_os(brand.name)
    folder_path = str(get_brand_folder_path(brand.name).resolve())
    return {"success": success, "folder_path": folder_path}


@router.post("/open-all-folders")
def open_root_folder() -> Dict[str, Any]:
    """Opens the parent media_queue root directory in File Explorer."""
    ensure_brand_folders()
    try:
        if sys.platform == "win32":
            os.startfile(str(MEDIA_QUEUE_DIR.resolve()))
        elif sys.platform == "darwin":
            import subprocess
            subprocess.Popen(["open", str(MEDIA_QUEUE_DIR.resolve())])
        else:
            import subprocess
            subprocess.Popen(["xdg-open", str(MEDIA_QUEUE_DIR.resolve())])
        return {"success": True, "folder_path": str(MEDIA_QUEUE_DIR.resolve())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-folders")
def init_folders() -> Dict[str, Any]:
    """Initializes and ensures all brand subdirectories exist."""
    ensure_brand_folders()
    return {"success": True, "message": "Brand folders verified."}
