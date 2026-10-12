"""
📁 Multi-Brand Folder Queue Manager & Auto-Publisher
Scans local per-brand folders, manages pending content queues, extracts captions,
dispatches to Instagram, and archives processed media into posted/.
"""

import os
import sys
import shutil
import logging
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from app.config import MEDIA_QUEUE_DIR, THUMBNAILS_DIR
from app.core.database import list_brands, create_post, update_post_status, get_brand
from app.core.models import (
    Brand, ScheduledPostCreate, ScheduledPost, PlatformType, PostType, PostStatus
)
from app.core.dispatcher import dispatch_post
from app.core.thumbnail_extractor import extract_thumbnail

logger = logging.getLogger("FolderQueueManager")

SUPPORTED_VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_EXTS = SUPPORTED_VIDEO_EXTS | SUPPORTED_IMAGE_EXTS


def get_brand_folder_path(brand_name: str) -> Path:
    """Returns the dedicated media folder path for a brand."""
    exact_path = MEDIA_QUEUE_DIR / brand_name
    if exact_path.exists():
        return exact_path
    sanitized = brand_name.replace(" ", "_")
    sanitized_path = MEDIA_QUEUE_DIR / sanitized
    if sanitized_path.exists():
        return sanitized_path
    return exact_path


def ensure_brand_folders(brand_names: Optional[List[str]] = None):
    """Ensures media_queue and subfolders exist for all brands."""
    MEDIA_QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    if not brand_names:
        brands = list_brands()
        brand_names = [b.name for b in brands]
    for name in brand_names:
        brand_folder = MEDIA_QUEUE_DIR / name
        brand_folder.mkdir(parents=True, exist_ok=True)
        posted_folder = brand_folder / "posted"
        posted_folder.mkdir(parents=True, exist_ok=True)


def parse_timestamp_from_string(text: str) -> Optional[float]:
    """
    Extracts audio start seconds from text like:
    [00:30], (00:30), 00:30, 1:15, 01:25.5, 30s, 45s, 90s, 1m30s
    """
    if not text:
        return None

    # [01:25] or (01:25) or 01:25
    m = re.search(r'[\[\(]?(\d{1,2})[:\.](\d{2}(?:\.\d+)?)[\]\)]?', text)
    if m:
        try:
            mins = float(m.group(1))
            secs = float(m.group(2))
            return mins * 60 + secs
        except Exception:
            pass

    # 45s or 90s
    m_sec = re.search(r'(\d+(?:\.\d+)?)\s*s\b', text, re.IGNORECASE)
    if m_sec:
        try:
            return float(m_sec.group(1))
        except Exception:
            pass

    return None


def parse_companion_metadata(media_file: Path) -> Dict[str, Any]:
    """
    Checks for companion .json or .txt file next to the media file.
    Extracts: caption, music_query, audio_start_sec, first_comment.
    """
    stem = media_file.stem
    parent = media_file.parent

    # 1. JSON file (highest priority)
    json_candidates = [
        parent / f"{stem}.json",
        parent / f"{stem}_metadata.json",
        parent / "metadata.json"
    ]
    for jc in json_candidates:
        if jc.exists() and jc.is_file():
            try:
                with open(jc, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return {
                    "caption": data.get("caption") or data.get("text") or "",
                    "music_query": data.get("music_query") or data.get("song_name") or data.get("audio_url") or None,
                    "audio_start_sec": float(data.get("audio_start_sec") or data.get("start_seconds") or 0.0),
                    "first_comment": data.get("first_comment") or None,
                    "music_volume": float(data.get("music_volume") or 10.0),
                    "meta_file": str(jc)
                }
            except Exception as e:
                logger.warning(f"Failed parsing companion JSON {jc.name}: {e}")

    # 2. TXT file
    txt_candidates = [
        parent / f"{stem}.txt",
        parent / f"{stem}.caption.txt",
        parent / f"{stem}_caption.txt"
    ]
    for tc in txt_candidates:
        if tc.exists() and tc.is_file():
            try:
                with open(tc, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                start_sec = parse_timestamp_from_string(content) or 0.0
                
                # Check for audio link in text: audio: https://...
                audio_link = None
                m_audio = re.search(r'(?:audio|song|music)[:=]\s*(https?://\S+)', content, re.IGNORECASE)
                if m_audio:
                    audio_link = m_audio.group(1)

                return {
                    "caption": content,
                    "music_query": audio_link,
                    "audio_start_sec": start_sec,
                    "first_comment": None,
                    "music_volume": 10.0,
                    "meta_file": str(tc)
                }
            except Exception as e:
                logger.warning(f"Failed parsing companion TXT {tc.name}: {e}")

    return {
        "caption": f"✨ {stem.replace('_', ' ')}",
        "music_query": None,
        "audio_start_sec": 0.0,
        "first_comment": None,
        "music_volume": 10.0,
        "meta_file": None
    }


def scan_brand_media_items(brand_name: str) -> List[Dict[str, Any]]:
    """Lists all valid media items currently pending in the brand folder."""
    folder = get_brand_folder_path(brand_name)
    if not folder.exists():
        return []

    items = []
    for file in sorted(folder.iterdir(), key=lambda f: f.stat().st_mtime):
        if not file.is_file():
            continue
        if file.suffix.lower() not in SUPPORTED_EXTS:
            continue
        if file.name.startswith("."):
            continue

        meta = parse_companion_metadata(file)
        thumb = extract_thumbnail(file) if file.suffix.lower() in SUPPORTED_VIDEO_EXTS else None

        items.append({
            "filename": file.name,
            "file_path": str(file.resolve()),
            "media_type": "video" if file.suffix.lower() in SUPPORTED_VIDEO_EXTS else "photo",
            "size_mb": round(file.stat().st_size / (1024 * 1024), 2),
            "thumbnail": thumb,
            "caption": meta.get("caption", ""),
            "music_query": meta.get("music_query"),
            "audio_start_sec": meta.get("audio_start_sec", 0.0),
            "music_volume": meta.get("music_volume", 10.0),
            "meta_file": meta.get("meta_file"),
            "mtime": file.stat().st_mtime
        })

    return items


def get_all_brands_folder_status() -> List[Dict[str, Any]]:
    """Returns folder queue status, counts, and previews for all brands."""
    ensure_brand_folders()
    brands = list_brands()
    results = []

    for b in brands:
        pending_items = scan_brand_media_items(b.name)
        folder_path = get_brand_folder_path(b.name)
        results.append({
            "brand_id": b.id,
            "brand_name": b.name,
            "color_badge": b.color_badge,
            "folder_path": str(folder_path.resolve()),
            "pending_count": len(pending_items),
            "items": pending_items
        })

    return results


def archive_media_files(media_path: Path, meta_file_path: Optional[str] = None):
    """Moves published media file and its companion metadata into posted/ subfolder."""
    parent = media_path.parent
    posted_dir = parent / "posted"
    posted_dir.mkdir(parents=True, exist_ok=True)

    try:
        dest_media = posted_dir / media_path.name
        shutil.move(str(media_path), str(dest_media))
    except Exception as e:
        logger.warning(f"Could not archive media file {media_path.name}: {e}")

    if meta_file_path:
        mf = Path(meta_file_path)
        if mf.exists() and mf.is_file():
            try:
                dest_meta = posted_dir / mf.name
                shutil.move(str(mf), str(dest_meta))
            except Exception as e:
                logger.warning(f"Could not archive meta file {mf.name}: {e}")


def publish_next_for_brand(brand_id: str) -> Dict[str, Any]:
    """Publishes the next pending media item for a specific brand."""
    brand = get_brand(brand_id)
    if not brand:
        return {"success": False, "error": "Brand not found"}

    items = scan_brand_media_items(brand.name)
    if not items:
        return {"success": False, "error": f"No pending media files in folder for brand '{brand.name}'"}

    target_item = items[0]
    media_path = Path(target_item["file_path"])

    # Create ScheduledPost
    now_iso = datetime.now(timezone.utc).isoformat()
    post_type = PostType.REEL if target_item["media_type"] == "video" else PostType.POST

    new_post = create_post(ScheduledPostCreate(
        brand_id=brand.id,
        target_platforms=[PlatformType.INSTAGRAM],
        post_type=post_type,
        media_paths=[str(media_path.resolve())],
        caption=target_item.get("caption", ""),
        first_comment=None,
        scheduled_time=now_iso,
        music_query=target_item.get("music_query"),
        audio_start_sec=target_item.get("audio_start_sec", 0.0),
        music_volume=target_item.get("music_volume", 10.0),
        status=PostStatus.PUBLISHING
    ))

    # Dispatch to Instagram
    success, error_msg, urls = dispatch_post(new_post)

    if success:
        update_post_status(new_post.id, PostStatus.PUBLISHED, published_urls=urls)
        archive_media_files(media_path, target_item.get("meta_file"))
        return {
            "success": True,
            "post_id": new_post.id,
            "brand_name": brand.name,
            "media_name": media_path.name,
            "urls": urls
        }
    else:
        update_post_status(new_post.id, PostStatus.FAILED, error_log=error_msg, published_urls=urls)
        return {
            "success": False,
            "post_id": new_post.id,
            "brand_name": brand.name,
            "error": error_msg
        }


def publish_next_for_all_brands() -> Dict[str, Any]:
    """Master trigger: Publishes the next pending media item for EVERY brand."""
    brands = list_brands()
    results = {}
    successful = 0
    total = len(brands)

    for b in brands:
        res = publish_next_for_brand(b.id)
        results[b.name] = res
        if res.get("success"):
            successful += 1

    return {
        "success": successful > 0,
        "total_brands": total,
        "published_count": successful,
        "brand_results": results
    }


def open_brand_folder_in_os(brand_name: str) -> bool:
    """Opens the brand's local folder in Windows File Explorer or macOS Finder."""
    folder = get_brand_folder_path(brand_name)
    folder.mkdir(parents=True, exist_ok=True)
    try:
        if sys.platform == "win32":
            os.startfile(str(folder.resolve()))
            return True
        elif sys.platform == "darwin":
            import subprocess
            subprocess.Popen(["open", str(folder.resolve())])
            return True
        else:
            import subprocess
            subprocess.Popen(["xdg-open", str(folder.resolve())])
            return True
    except Exception as e:
        logger.error(f"Failed opening folder {folder}: {e}")
        return False


def open_root_folder_in_os() -> bool:
    """Opens the root media_queue directory in Windows File Explorer."""
    MEDIA_QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if sys.platform == "win32":
            os.startfile(str(MEDIA_QUEUE_DIR.resolve()))
            return True
        elif sys.platform == "darwin":
            import subprocess
            subprocess.Popen(["open", str(MEDIA_QUEUE_DIR.resolve())])
            return True
        else:
            import subprocess
            subprocess.Popen(["xdg-open", str(MEDIA_QUEUE_DIR.resolve())])
            return True
    except Exception as e:
        logger.error(f"Failed opening root folder: {e}")
        return False
