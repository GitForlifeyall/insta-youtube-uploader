"""
📁 Multi-Brand Folder Queue Manager & Auto-Publisher
Scans local per-brand folders, manages pending content queues, extracts captions,
dispatches to Instagram/Facebook/Threads/YouTube, and archives processed media.
"""

import os
import sys
import shutil
import logging
import json
from pathlib import Path
from datetime import datetime
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
    # Check if exact folder exists, or sanitized version
    exact_path = MEDIA_QUEUE_DIR / brand_name
    if exact_path.exists():
        return exact_path
    
    # Check sanitized underscores or lowercase
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
    Extracts audio start seconds from timestamp formats like:
    - [00:30], (00:30), 00:30, 1:15, 01:25.5
    - [00.30], (00.30), 00.30, 1.15
    - 30s, 45s, 90s, 1m30s
    - start_30, start_00.30
    """
    import re
    if not text:
        return None

    # Pattern 1: MM:SS or HH:MM:SS (e.g. 00:30, 01:15, 1:15:30)
    m = re.search(r'(?:\[|\(|\b)(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?(?:\]|\)|\b)', text)
    if m:
        if m.group(3):  # HH:MM:SS
            return float(m.group(1)) * 3600 + float(m.group(2)) * 60 + float(m.group(3))
        else:  # MM:SS
            return float(m.group(1)) * 60 + float(m.group(2))

    # Pattern 2: MM.SS in brackets or parentheses or preceded by start/time (e.g. [00.30], (1.15), start_00.30)
    m = re.search(r'(?:\[|\(|start[\s_-]*|time[\s_-]*)(\d{1,2})\.(\d{2})(?:\]|\)|\b)', text, re.IGNORECASE)
    if m:
        return float(m.group(1)) * 60 + float(m.group(2))

    # Pattern 3: XmYs (e.g. 1m30s)
    m = re.search(r'\b(\d{1,2})m(\d{1,2})s\b', text, re.IGNORECASE)
    if m:
        return float(m.group(1)) * 60 + float(m.group(2))

    # Pattern 4: Preceded by 'start' or 'time' or followed by 's' (e.g. start_20, start 30, [30s], 45s)
    m = re.search(r'(?:start[\s_-]*|time[\s_-]*)(\d{1,3})\b', text, re.IGNORECASE)
    if m:
        return float(m.group(1))

    m = re.search(r'(?:\[|\()?\b(\d{1,3})s(?:\]|\)|\b)', text, re.IGNORECASE)
    if m:
        return float(m.group(1))

    # Pattern 5: In brackets pure number e.g. [30], [45], (30)
    m = re.search(r'[\[\(](\d{1,3})[\]\)]', text)
    if m:
        val = int(m.group(1))
        if val < 600:  # reasonable second offset
            return float(val)

    return None


def extract_metadata_from_filename(filename: str, brand_name: str) -> Dict[str, Any]:
    """
    Intelligently extracts:
    - Clean song name / title
    - Audio start timestamp (seconds)
    - Music search query
    - Hashtags and formatted social media caption
    directly from the file name.
    """
    import re
    stem = Path(filename).stem

    # 1. Extract audio start timestamp
    audio_start_sec = parse_timestamp_from_string(stem)

    # 2. Extract hashtags in filename (e.g. #reels #lofi #trending)
    hashtags = re.findall(r'#\w+', stem)
    
    # 3. Remove timestamp patterns from title
    cleaned = stem
    cleaned = re.sub(r'\[\s*\d{1,2}[:.]\d{2}\s*\]', '', cleaned)
    cleaned = re.sub(r'\(\s*\d{1,2}[:.]\d{2}\s*\)', '', cleaned)
    cleaned = re.sub(r'\[\s*\d{1,3}s?\s*\]', '', cleaned)
    cleaned = re.sub(r'\(\s*\d{1,3}s?\s*\)', '', cleaned)
    cleaned = re.sub(r'\b\d{1,2}:\d{2}\b', '', cleaned)
    cleaned = re.sub(r'\b\d{1,3}s\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bstart[\s_-]*\d+s?\b', '', cleaned, flags=re.IGNORECASE)

    # 4. Remove hashtags from title string
    cleaned = re.sub(r'#\w+', '', cleaned)

    # 5. Remove leading track numbering e.g. "01_", "01 - ", "01. "
    cleaned = re.sub(r'^\d+[\s._-]+', '', cleaned)

    # 6. Normalize separators (underscores to spaces, redundant dashes)
    cleaned = cleaned.replace("_", " ")
    cleaned = re.sub(r'\s*-\s*', ' - ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip(' -_')

    song_title = cleaned or Path(filename).stem

    # 7. Generate music search query (for Instagram music picker)
    # Remove special characters from music query
    music_query = re.sub(r'[^\w\s-]', '', song_title).strip()

    # 8. Build rich, aesthetic caption
    brand_handle = brand_name.replace(" ", "").lower()
    default_tags = ["#reels", "#lyrics", "#music", "#trending", "#viral", "#fyp", "#explore"]
    
    # Combine custom extracted hashtags + defaults without duplicates
    all_tags_set = set(t.lower() for t in hashtags)
    combined_tags = list(hashtags)
    for tag in default_tags:
        if tag.lower() not in all_tags_set:
            combined_tags.append(tag)

    tags_str = " ".join(combined_tags[:10])

    timestamp_line = ""
    if audio_start_sec is not None:
        mins = int(audio_start_sec // 60)
        secs = int(audio_start_sec % 60)
        timestamp_line = f"⏱️ Timestamp: {mins:02d}:{secs:02d}\n"

    caption = (
        f"🎶 {song_title}\n\n"
        f"{timestamp_line}"
        f"🎧 Turn on sound & feel the lyrics ✨\n"
        f"👉 Follow @{brand_handle} for more daily music & vibes!\n\n"
        f"{tags_str}"
    )

    youtube_title = f"{song_title} #Shorts"
    if len(youtube_title) > 95:
        youtube_title = f"{song_title[:85]} #Shorts"

    return {
        "title": song_title,
        "music_query": music_query or None,
        "audio_start_sec": audio_start_sec,
        "caption": caption,
        "youtube_title": youtube_title,
        "youtube_tags": [t.replace("#", "") for t in combined_tags[:8]],
        "hashtags": combined_tags
    }


def clean_title_from_filename(filename: str) -> str:
    """Derives a clean title from filename."""
    meta = extract_metadata_from_filename(filename, "Brand")
    return meta["title"]


def parse_sidecar_metadata(media_file: Path, brand_name: str) -> Dict[str, Any]:
    """
    Parses metadata by prioritizing filename info (song name, timestamps, caption),
    with optional sidecar override if .txt or .json is explicitly provided.
    """
    base_stem = media_file.stem
    parent_dir = media_file.parent

    # 1. Base metadata parsed directly from filename!
    fn_meta = extract_metadata_from_filename(media_file.name, brand_name)

    meta = {
        "title": fn_meta["title"],
        "caption": fn_meta["caption"],
        "music_query": fn_meta["music_query"],
        "audio_start_sec": fn_meta["audio_start_sec"],
        "youtube_title": fn_meta["youtube_title"],
        "youtube_tags": fn_meta["youtube_tags"],
        "first_comment": None
    }

    # 2. Check for explicit companion .json sidecar
    json_file = parent_dir / f"{base_stem}.json"
    if json_file.exists():
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    if data.get("caption"):
                        meta["caption"] = data.get("caption").strip()
                    if data.get("music_query") or data.get("music"):
                        meta["music_query"] = data.get("music_query") or data.get("music")
                    if data.get("audio_start_sec") is not None or data.get("start_sec") is not None:
                        meta["audio_start_sec"] = float(data.get("audio_start_sec") or data.get("start_sec"))
                    if data.get("youtube_title") or data.get("title"):
                        meta["youtube_title"] = data.get("youtube_title") or data.get("title")
                    if "tags" in data and isinstance(data["tags"], list):
                        meta["youtube_tags"] = data["tags"]
                    meta["first_comment"] = data.get("first_comment")
        except Exception as e:
            logger.warning(f"Failed to parse JSON sidecar {json_file.name}: {e}")

    # 3. Check for explicit companion .txt sidecar
    txt_file = parent_dir / f"{base_stem}.txt"
    if txt_file.exists():
        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                custom_txt = f.read().strip()
                if custom_txt:
                    meta["caption"] = custom_txt
        except Exception as e:
            logger.warning(f"Failed to read TXT sidecar {txt_file.name}: {e}")

    return meta


def list_pending_media_for_brand(brand_name: str) -> List[Path]:
    """
    Returns all unposted media files for a brand in FIFO order (oldest/sorted first).
    Excludes the 'posted' directory and hidden files.
    """
    folder = get_brand_folder_path(brand_name)
    if not folder.exists() or not folder.is_dir():
        return []

    files = []
    for item in folder.iterdir():
        if item.is_file() and not item.name.startswith("."):
            if item.suffix.lower() in SUPPORTED_EXTS:
                files.append(item)

    # Sort naturally by file name / mtime
    files.sort(key=lambda p: p.stat().st_mtime)
    return files


def list_posted_media_for_brand(brand_name: str) -> List[Path]:
    """Returns list of already posted media files in the brand's 'posted' folder."""
    folder = get_brand_folder_path(brand_name)
    posted_dir = folder / "posted"
    if not posted_dir.exists() or not posted_dir.is_dir():
        return []

    files = []
    for item in posted_dir.iterdir():
        if item.is_file() and item.suffix.lower() in SUPPORTED_EXTS:
            files.append(item)
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def get_item_preview_info(media_path: Path, brand_name: str) -> Dict[str, Any]:
    """Generates preview dictionary for a media item including thumbnail and metadata."""
    stat = media_path.stat()
    is_video = media_path.suffix.lower() in SUPPORTED_VIDEO_EXTS
    
    thumb_url = None
    if is_video:
        try:
            thumb_file = extract_thumbnail(media_path)
            if thumb_file:
                thumb_url = f"/media/thumbnails/{thumb_file}"
        except Exception:
            pass

    meta = parse_sidecar_metadata(media_path, brand_name)

    formatted_timestamp = None
    if meta.get("audio_start_sec") is not None:
        mins = int(meta["audio_start_sec"] // 60)
        secs = int(meta["audio_start_sec"] % 60)
        formatted_timestamp = f"{mins:02d}:{secs:02d}"

    return {
        "file_name": media_path.name,
        "file_path": str(media_path.resolve()),
        "file_size_bytes": stat.st_size,
        "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "is_video": is_video,
        "thumbnail_url": thumb_url,
        "title": meta.get("title") or clean_title_from_filename(media_path.name),
        "caption_preview": meta["caption"][:120] + ("..." if len(meta["caption"]) > 120 else ""),
        "full_caption": meta["caption"],
        "music_query": meta.get("music_query"),
        "audio_start_sec": meta.get("audio_start_sec"),
        "formatted_timestamp": formatted_timestamp,
        "youtube_title": meta.get("youtube_title"),
    }


def get_all_brands_folder_status() -> List[Dict[str, Any]]:
    """
    Returns comprehensive folder queue status for every configured brand.
    Includes queue counts, upcoming file previews, and folder status.
    """
    ensure_brand_folders()
    brands = list_brands()
    results = []

    for brand in brands:
        brand_folder = get_brand_folder_path(brand.name)
        pending_files = list_pending_media_for_brand(brand.name)
        posted_files = list_posted_media_for_brand(brand.name)

        # Active platform names
        active_platforms = [p.platform.value for p in brand.profiles if p.is_active]

        # Preview next items (up to 6)
        upcoming_previews = []
        for f in pending_files[:6]:
            upcoming_previews.append(get_item_preview_info(f, brand.name))

        next_item = upcoming_previews[0] if upcoming_previews else None

        results.append({
            "brand_id": brand.id,
            "brand_name": brand.name,
            "brand_color": brand.color_badge,
            "folder_path": str(brand_folder.resolve()),
            "folder_exists": brand_folder.exists(),
            "pending_count": len(pending_files),
            "posted_count": len(posted_files),
            "next_item": next_item,
            "upcoming_items": upcoming_previews,
            "active_platforms": active_platforms,
            "profiles_count": len(brand.profiles),
        })

    return results


def archive_media_file(media_file: Path, brand_name: str) -> Optional[Path]:
    """
    Moves a published media file (and any companion .txt / .json sidecars)
    to the brand's 'posted' directory.
    """
    folder = get_brand_folder_path(brand_name)
    posted_dir = folder / "posted"
    posted_dir.mkdir(parents=True, exist_ok=True)

    dest_file = posted_dir / media_file.name
    # Handle name collision in posted folder
    if dest_file.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_file = posted_dir / f"{media_file.stem}_{timestamp}{media_file.suffix}"

    try:
        shutil.move(str(media_file), str(dest_file))
        logger.info(f"Archived media file to: {dest_file}")

        # Also archive companion sidecars if they exist
        for ext in [".txt", ".json"]:
            sidecar = media_file.parent / f"{media_file.stem}{ext}"
            if sidecar.exists():
                sidecar_dest = posted_dir / f"{dest_file.stem}{ext}"
                try:
                    shutil.move(str(sidecar), str(sidecar_dest))
                except Exception as e:
                    logger.warning(f"Could not move sidecar {sidecar.name}: {e}")

        return dest_file
    except Exception as e:
        logger.error(f"Failed to archive media file {media_file.name}: {e}")
        return None


def publish_next_for_brand(brand_id: str) -> Dict[str, Any]:
    """
    Finds the next pending media item in the brand's queue folder,
    creates a ScheduledPost, publishes it across all active platforms,
    and archives the file into 'posted/'.
    """
    brands = list_brands()
    brand = next((b for b in brands if b.id == brand_id), None)
    if not brand:
        return {"success": False, "error": f"Brand with ID '{brand_id}' not found."}

    pending_files = list_pending_media_for_brand(brand.name)
    if not pending_files:
        return {
            "success": False,
            "error": f"No pending media found in folder for brand '{brand.name}'. Drop videos/images into 'media_queue/{brand.name}/' first.",
            "brand_name": brand.name,
            "brand_id": brand.id,
            "empty_queue": True
        }

    next_file = pending_files[0]
    is_video = next_file.suffix.lower() in SUPPORTED_VIDEO_EXTS
    post_type = PostType.REEL if is_video else PostType.POST

    # Parse metadata / caption
    meta = parse_sidecar_metadata(next_file, brand.name)

    # Determine active platforms for this brand
    target_platforms = [p.platform for p in brand.profiles if p.is_active]
    if not target_platforms:
        return {
            "success": False,
            "error": f"Brand '{brand.name}' has no active platforms configured.",
            "brand_name": brand.name,
            "brand_id": brand.id
        }

    now_iso = datetime.now().isoformat()
    post_create = ScheduledPostCreate(
        brand_id=brand.id,
        target_platforms=target_platforms,
        post_type=post_type,
        media_paths=[str(next_file.resolve())],
        caption=meta["caption"],
        first_comment=meta.get("first_comment"),
        scheduled_time=now_iso,
        music_query=meta.get("music_query"),
        audio_start_sec=meta.get("audio_start_sec"),
        share_to_facebook=PlatformType.FACEBOOK in target_platforms,
        share_to_threads=PlatformType.THREADS in target_platforms,
        youtube_title=meta.get("youtube_title"),
        youtube_tags=meta.get("youtube_tags")
    )

    # Create post in database
    created_post = create_post(post_create)
    if not created_post:
        return {"success": False, "error": "Database error creating post entry."}

    logger.info(f"🚀 Publishing next item for brand '{brand.name}': {next_file.name} to {len(target_platforms)} platforms")

    # Dispatch post
    success, err_msg, published_urls = dispatch_post(created_post)

    # Update database record
    final_status = PostStatus.PUBLISHED if (success or len(published_urls) > 0) else PostStatus.FAILED
    update_post_status(created_post.id, final_status, error_log=err_msg if err_msg else None, published_urls=published_urls)

    # Archive the file if at least one platform succeeded or upload completed
    archived_path = None
    if success or len(published_urls) > 0:
        archived_path = archive_media_file(next_file, brand.name)

    # Remaining queue count
    remaining_count = len(list_pending_media_for_brand(brand.name))

    return {
        "success": success or len(published_urls) > 0,
        "brand_id": brand.id,
        "brand_name": brand.name,
        "brand_color": brand.color_badge,
        "file_name": next_file.name,
        "post_id": created_post.id,
        "published_urls": published_urls,
        "error": err_msg if err_msg else None,
        "archived_to": str(archived_path) if archived_path else None,
        "remaining_count": remaining_count
    }


def publish_next_for_all_brands() -> Dict[str, Any]:
    """
    Master Broadcast: Iterates through all active brands and publishes
    the next media item for each brand across its configured platforms.
    """
    ensure_brand_folders()
    brands = list_brands()
    results = []
    total_posted = 0
    total_failed = 0
    total_empty = 0

    for brand in brands:
        pending = list_pending_media_for_brand(brand.name)
        if not pending:
            total_empty += 1
            results.append({
                "brand_id": brand.id,
                "brand_name": brand.name,
                "brand_color": brand.color_badge,
                "status": "empty",
                "message": "Queue folder is empty. No files to post."
            })
            continue

        res = publish_next_for_brand(brand.id)
        if res.get("success"):
            total_posted += 1
            res["status"] = "published"
        else:
            total_failed += 1
            res["status"] = "failed"
        results.append(res)

    return {
        "total_brands": len(brands),
        "total_posted": total_posted,
        "total_failed": total_failed,
        "total_empty": total_empty,
        "results": results
    }


def open_brand_folder_in_os(brand_name: str) -> bool:
    """Opens the brand's media folder in native Windows File Explorer / OS."""
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
        logger.error(f"Failed to open folder {folder}: {e}")
        return False
