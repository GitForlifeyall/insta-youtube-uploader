"""
📊 CSV Bulk Importer & Validator Engine
Supports both official Metricool CSV schema and streamlined Social Hub Custom CSV schema.
Provides pre-flight verification, date formatting, brand matching, and media path/URL resolution.
"""

import csv
import io
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from app.config import UPLOADS_DIR, DOWNLOADS_DIR
from app.core.database import list_brands, create_post
from app.core.models import ScheduledPostCreate, PlatformType, PostType, PostStatus


def extract_google_drive_id(url: str) -> Optional[str]:
    """Extracts file ID from Google Drive URLs."""
    if not url:
        return None
    if "drive.google.com" in url or "docs.google.com" in url:
        m = re.search(r"/file/d/([a-zA-Z0-9_-]{20,})", url)
        if m:
            return m.group(1)
        m = re.search(r"[?&]id=([a-zA-Z0-9_-]{20,})", url)
        if m:
            return m.group(1)
    return None


def download_google_drive_file(file_id: str, dest_path: Path) -> bool:
    """Downloads a public Google Drive file."""
    import requests
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        session = requests.Session()
        res = session.get(url, stream=True, timeout=60)
        token = None
        for k, v in res.cookies.items():
            if k.startswith('download_warning'):
                token = v
                break
        if token:
            url = f"https://drive.google.com/uc?export=download&confirm={token}&id={file_id}"
            res = session.get(url, stream=True, timeout=60)

        if res.status_code == 200:
            content_type = res.headers.get("content-type", "").lower()
            if "text/html" in content_type:
                return False
            with open(dest_path, "wb") as f:
                for chunk in res.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
            return True
    except Exception as e:
        print(f"Error downloading Google Drive file {file_id}: {e}")
    return False


def parse_timestamp_seconds(val: Any) -> Optional[float]:
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    if ":" in s:
        parts = s.split(":")
        try:
            if len(parts) == 2:
                return float(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:
                return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def detect_csv_format(headers: List[str]) -> str:
    clean_headers = [h.strip().lower() for h in headers]
    if "picture url 1" in clean_headers or "twitter/x" in clean_headers or "instagram post type" in clean_headers:
        return "metricool"
    return "custom"


def parse_datetime_flexible(
    date_str: str,
    time_str: str,
    date_format_pref: str = "YYYY-MM-DD",
    time_format_pref: str = "24h"
) -> Tuple[Optional[datetime], str, str, List[str]]:
    warnings = []
    clean_date = (date_str or "").strip()
    clean_time = (time_str or "").strip()

    if not clean_date:
        now = datetime.now()
        return now, now.strftime("%b %d, %Y"), now.strftime("%I:%M %p"), ["Missing date; scheduled for today"]

    date_formats_to_try = [
        "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"
    ]
    parsed_date = None
    for fmt in date_formats_to_try:
        try:
            parsed_date = datetime.strptime(clean_date, fmt).date()
            break
        except ValueError:
            continue

    if not parsed_date:
        now = datetime.now()
        warnings.append(f"Invalid date format '{clean_date}'. Scheduled for today.")
        parsed_date = now.date()

    parsed_time = None
    if clean_time:
        for tfmt in ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p", "%I:%M%p"]:
            try:
                parsed_time = datetime.strptime(clean_time, tfmt).time()
                break
            except ValueError:
                continue

    if not parsed_time:
        parsed_time = datetime.now().time()
        if clean_time:
            warnings.append(f"Invalid time format '{clean_time}'. Defaulted to current time.")

    dt_obj = datetime.combine(parsed_date, parsed_time)
    formatted_date_str = dt_obj.strftime("%b %d, %Y")
    formatted_time_str = dt_obj.strftime("%I:%M %p" if time_format_pref == "12h" else "%H:%M")
    return dt_obj, formatted_date_str, formatted_time_str, warnings


def resolve_media_path(raw_path: str) -> Tuple[Optional[str], bool, Optional[str]]:
    if not raw_path or not raw_path.strip():
        return None, False, "Missing media path"
    p = Path(raw_path.strip())
    if p.exists() and p.is_file():
        return str(p.resolve()), True, None
    uploads_p = UPLOADS_DIR / raw_path.strip()
    if uploads_p.exists() and uploads_p.is_file():
        return str(uploads_p.resolve()), True, None
    return raw_path.strip(), False, "File not found locally"


def validate_csv_content(
    csv_text: str,
    date_format_pref: str = "YYYY-MM-DD",
    time_format_pref: str = "24h",
    default_brand_id: Optional[str] = None
) -> Dict[str, Any]:
    brands = list_brands()
    brand_name_map = {b.name.lower(): b for b in brands}
    default_brand = None
    if default_brand_id:
        for b in brands:
            if b.id == default_brand_id:
                default_brand = b
                break
    if not default_brand and brands:
        default_brand = brands[0]

    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    headers = reader.fieldnames or []
    detected_format = detect_csv_format(headers)

    posts_report = []
    has_any_errors = False
    has_brand_errors = False
    has_unidentified_urls = False

    for row_idx, row in enumerate(reader, start=1):
        row_errors = []
        row_warnings = []
        can_import = True
        import_as_draft = False

        if detected_format == "metricool":
            text = (row.get("Text") or "").strip()
            date_str = (row.get("Date") or "").strip()
            time_str = (row.get("Time") or "").strip()
            is_draft = str(row.get("Draft", "false")).strip().lower() in ("true", "1", "yes")
            first_comment = (row.get("First Comment Text") or "").strip()
            brand_name_raw = (row.get("Brand name") or "").strip()
            video_url = (row.get("Picture Url 1") or "").strip()
            video_path = ""
            thumbnail_url = (row.get("Video Thumbnail Url") or "").strip()
            song_name = ""
            audio_start_sec = 0.0
            pt_raw = (row.get("Instagram Post Type") or "").strip().upper()
            post_type = PostType.REEL if pt_raw in ("REEL", "VIDEO") else PostType.POST
        else:
            text = (row.get("text") or row.get("caption") or "").strip()
            date_str = (row.get("date") or "").strip()
            time_str = (row.get("time") or "").strip()
            is_draft = str(row.get("draft", "false")).strip().lower() in ("true", "1", "yes")
            first_comment = (row.get("first_comment") or "").strip()
            brand_name_raw = (row.get("brand_name") or "").strip()
            video_path = (row.get("video_path") or "").strip()
            video_url = (row.get("video_url") or "").strip()
            thumbnail_url = (row.get("thumbnail_url") or "").strip()
            song_name = (row.get("song_name") or row.get("music_query") or "").strip()
            song_start_raw = row.get("song_start_sec") or row.get("audio_start_sec") or ""
            audio_start_sec = parse_timestamp_seconds(song_start_raw) or 0.0
            pt_raw = (row.get("post_type") or "").strip().lower()
            post_type = PostType.POST if pt_raw in ("post", "photo") else PostType.REEL

        # Brand resolution
        assigned_brand = None
        if brand_name_raw:
            matched = brand_name_map.get(brand_name_raw.lower())
            if matched:
                assigned_brand = matched
            else:
                row_errors.append(f"Brand '{brand_name_raw}' does not exist.")
                can_import = False
                has_brand_errors = True
        else:
            assigned_brand = default_brand

        # Date & Time
        dt_obj, formatted_date, formatted_time, dt_warnings = parse_datetime_flexible(
            date_str, time_str, date_format_pref, time_format_pref
        )
        row_warnings.extend(dt_warnings)

        # Media resolution
        resolved_media_path = None
        if video_path:
            res_path, exists, err = resolve_media_path(video_path)
            if exists:
                resolved_media_path = res_path
            else:
                row_warnings.append(f"Video file not found locally: '{video_path}'. Will import as draft.")
                import_as_draft = True
        elif video_url:
            resolved_media_path = video_url
        else:
            row_warnings.append("Missing media path or URL.")
            import_as_draft = True

        status = "error" if row_errors else ("warning" if row_warnings else "success")
        if status == "error":
            has_any_errors = True

        posts_report.append({
            "row_index": row_idx,
            "status": status,
            "can_import": can_import,
            "import_as_draft": import_as_draft or is_draft,
            "brand_id": assigned_brand.id if assigned_brand else None,
            "brand_name": assigned_brand.name if assigned_brand else brand_name_raw,
            "brand_color": assigned_brand.color_badge if assigned_brand else "#94a3b8",
            "date": formatted_date,
            "time": formatted_time,
            "datetime_iso": dt_obj.strftime("%Y-%m-%dT%H:%M:%S") if dt_obj else None,
            "post_type": post_type.value,
            "media_path": resolved_media_path,
            "thumbnail_url": thumbnail_url,
            "caption": text,
            "first_comment": first_comment,
            "music_query": song_name,
            "audio_start_sec": audio_start_sec,
            "errors": row_errors,
            "warnings": row_warnings
        })

    return {
        "detected_format": detected_format,
        "total_rows": len(posts_report),
        "valid_rows": sum(1 for p in posts_report if p["can_import"]),
        "has_any_errors": has_any_errors,
        "has_brand_errors": has_brand_errors,
        "posts": posts_report
    }


def import_validated_posts(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    created_posts = []
    skipped_count = 0

    for p in posts:
        if not p.get("can_import") or not p.get("brand_id"):
            skipped_count += 1
            continue

        raw_media = p.get("media_path")
        media_paths = []
        if raw_media:
            drive_id = extract_google_drive_id(raw_media)
            if drive_id:
                dest = DOWNLOADS_DIR / f"drive_{drive_id[:10]}.mp4"
                if dest.exists() or download_google_drive_file(drive_id, dest):
                    media_paths = [str(dest.resolve())]
                else:
                    media_paths = [raw_media]
            else:
                media_paths = [raw_media]

        is_draft = p.get("import_as_draft", False)
        status = PostStatus.DRAFT if is_draft else PostStatus.SCHEDULED

        post = create_post(ScheduledPostCreate(
            brand_id=p["brand_id"],
            target_platforms=[PlatformType.INSTAGRAM],
            post_type=PostType(p.get("post_type", "reel")),
            media_paths=media_paths,
            caption=p.get("caption", ""),
            first_comment=p.get("first_comment"),
            scheduled_time=p.get("datetime_iso") or datetime.now().strftime("%Y-%m-%dT19:30:00"),
            music_query=p.get("music_query"),
            audio_start_sec=p.get("audio_start_sec", 0.0),
            status=status
        ))
        created_posts.append({
            "id": post.id,
            "brand_id": post.brand_id,
            "scheduled_time": post.scheduled_time,
            "status": post.status.value
        })

    return {
        "success": True,
        "imported_count": len(created_posts),
        "skipped_count": skipped_count,
        "posts": created_posts
    }
