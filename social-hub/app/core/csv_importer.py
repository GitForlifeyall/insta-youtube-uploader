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
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from app.config import PROJECTS_ROOT, VIDEOS_OUTPUT_DIR, DOWNLOADS_DIR
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
    """Downloads a public Google Drive file (shared with 'Anyone with the link')."""
    import requests
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        session = requests.Session()
        res = session.get(url, stream=True, timeout=60)
        
        # Check for Google Drive virus confirmation token for files > 100MB
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
    """Parses timestamp strings like '00:30', '1:15', '45', '45.5' into float seconds."""
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    if ":" in s:
        parts = s.split(":")
        try:
            if len(parts) == 2:  # MM:SS
                return float(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:  # HH:MM:SS
                return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def detect_csv_format(headers: List[str]) -> str:
    """Detects whether headers represent Metricool CSV format or Social Hub Custom CSV."""
    clean_headers = [h.strip().lower() for h in headers]
    if "picture url 1" in clean_headers or "twitter/x" in clean_headers or "instagram post type" in clean_headers:
        return "metricool"
    if "video_path" in clean_headers or "video_url" in clean_headers or "brand_name" in clean_headers:
        return "custom"
    # If generic 'Text', 'Date', 'Time'
    if "text" in clean_headers and "date" in clean_headers and "time" in clean_headers:
        if "instagram" in clean_headers and "draft" in clean_headers:
            return "metricool"
    return "custom"


def parse_datetime_flexible(
    date_str: str,
    time_str: str,
    date_format_pref: str = "YYYY-MM-DD",
    time_format_pref: str = "24h"
) -> Tuple[Optional[datetime], str, str, List[str]]:
    """
    Parses date and time strings into a datetime object and formatted strings.
    Returns: (dt_obj, formatted_date_str, formatted_time_str, warnings)
    """
    warnings = []
    clean_date = (date_str or "").strip()
    clean_time = (time_str or "").strip()

    if not clean_date:
        now = datetime.now()
        return now, now.strftime("%b %d, %Y"), now.strftime("%I:%M %p"), ["Missing date; scheduled for today"]

    # Candidate date formats
    date_formats_to_try = []
    pref_upper = date_format_pref.upper()
    if "DD/MM" in pref_upper or "DD-MM" in pref_upper:
        date_formats_to_try = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"]
    elif "MM/DD" in pref_upper or "MM-DD" in pref_upper:
        date_formats_to_try = ["%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"]
    else:
        date_formats_to_try = ["%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]

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

    # Time parsing
    parsed_time = None
    if clean_time:
        time_formats = ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p", "%I:%M%p"]
        for tfmt in time_formats:
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

    # Check if in past
    if dt_obj < datetime.now() - timedelta(minutes=5):
        warnings.append("Post date is in the past. It will be scheduled today at current time or saved as draft.")

    formatted_date = dt_obj.strftime("%b %d, %Y")
    formatted_time = dt_obj.strftime("%I:%M %p")

    return dt_obj, formatted_date, formatted_time, warnings


def resolve_media_path(raw_path: str) -> Tuple[Optional[str], bool, Optional[str]]:
    """
    Checks if a given local file path or video name exists.
    Returns: (resolved_path_str, exists_bool, error_msg)
    """
    if not raw_path:
        return None, False, None

    cleaned = raw_path.strip().strip('"').strip("'")
    if not cleaned:
        return None, False, None

    # Check 1: Direct absolute or relative path
    p = Path(cleaned)
    if p.is_file():
        return str(p.resolve()), True, None

    # Check 2: Relative to PROJECTS_ROOT
    p_root = PROJECTS_ROOT / cleaned
    if p_root.is_file():
        return str(p_root.resolve()), True, None

    # Check 3: Inside VIDEOS_OUTPUT_DIR by filename
    filename = Path(cleaned).name
    p_videos = VIDEOS_OUTPUT_DIR / filename
    if p_videos.is_file():
        return str(p_videos.resolve()), True, None

    return cleaned, False, f"Video file not found at '{cleaned}'"


def validate_csv_content(
    csv_text: str,
    date_format_pref: str = "YYYY-MM-DD",
    time_format_pref: str = "24h",
    default_brand_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parses and verifies CSV content.
    Returns validation report matching the Metricool UI layout.
    """
    stream = io.StringIO(csv_text.strip())
    reader = csv.DictReader(stream)

    if not reader.fieldnames:
        return {
            "format_detected": "unknown",
            "total_rows": 0,
            "can_import_count": 0,
            "errors_count": 0,
            "warnings_count": 0,
            "has_errors": True,
            "has_brand_errors": False,
            "has_unidentified_urls": False,
            "banner_errors": {
                "some_posts_have_errors": True,
                "wrong_brand_names": False,
                "unidentified_urls": False
            },
            "posts": [],
            "error_detail": "CSV file has no headers or is empty."
        }

    detected_format = detect_csv_format(reader.fieldnames)
    brands = list_brands()
    brand_name_map = {b.name.lower(): b for b in brands}

    default_brand = None
    if default_brand_id:
        default_brand = next((b for b in brands if b.id == default_brand_id), None)
    if not default_brand and brands:
        default_brand = brands[0]

    posts_report: List[Dict[str, Any]] = []
    has_any_errors = False
    has_brand_errors = False
    has_unidentified_urls = False

    for idx, row in enumerate(reader, start=1):
        row_errors: List[str] = []
        row_warnings: List[str] = []
        can_import = True
        import_as_draft = False
        error_brand = False
        error_media = False
        error_platforms = False

        # 1. Extract fields according to format
        if detected_format == "metricool":
            caption = row.get("Text", "").strip()
            date_str = row.get("Date", "").strip()
            time_str = row.get("Time", "").strip()
            is_draft = str(row.get("Draft", "")).strip().lower() in ("true", "1", "yes")
            first_comment = row.get("First Comment Text", "").strip()
            youtube_title = row.get("Youtube Video Title", "").strip()
            brand_name_raw = row.get("Brand name", "").strip()

            platforms = []
            if str(row.get("Instagram", "")).strip().lower() in ("true", "1", "yes"):
                platforms.append(PlatformType.INSTAGRAM)
            if str(row.get("Facebook", "")).strip().lower() in ("true", "1", "yes"):
                platforms.append(PlatformType.FACEBOOK)
            if str(row.get("Threads", "")).strip().lower() in ("true", "1", "yes"):
                platforms.append(PlatformType.THREADS)
            if str(row.get("Youtube", "")).strip().lower() in ("true", "1", "yes"):
                platforms.append(PlatformType.YOUTUBE)

            # Media URLs in Metricool
            video_url = row.get("Picture Url 1", "").strip()
            video_path = ""
            thumbnail_url = row.get("Video Thumbnail Url", "").strip()

            song_name = (row.get("TikTok music title") or row.get("song_name") or row.get("music_query") or "").strip()
            song_start_raw = row.get("TikTok music startMillis") or row.get("song_start_sec") or row.get("timestamp") or ""
            audio_start_sec = parse_timestamp_seconds(song_start_raw)
            # If startMillis was given in milliseconds, convert to seconds
            if audio_start_sec and audio_start_sec > 1000 and "startMillis" in str(row):
                audio_start_sec = audio_start_sec / 1000.0

            ig_type = (row.get("Instagram Post Type") or "REEL").strip().upper()
            if ig_type == "POST":
                post_type = PostType.POST
            elif ig_type == "STORY":
                post_type = PostType.STORY
            else:
                post_type = PostType.REEL

        else:  # Custom Social Hub Format
            caption = (row.get("text") or row.get("caption") or "").strip()
            date_str = (row.get("date") or "").strip()
            time_str = (row.get("time") or "").strip()
            is_draft = str(row.get("draft", "false")).strip().lower() in ("true", "1", "yes")
            first_comment = (row.get("first_comment") or "").strip()
            youtube_title = (row.get("youtube_title") or "").strip()
            brand_name_raw = (row.get("brand_name") or "").strip()

            video_path = (row.get("video_path") or "").strip()
            video_url = (row.get("video_url") or "").strip()
            thumbnail_url = (row.get("thumbnail_url") or "").strip()

            song_name = (row.get("song_name") or row.get("music_query") or row.get("song") or "").strip()
            song_start_raw = row.get("song_start_sec") or row.get("timestamp") or row.get("audio_start_sec") or ""
            audio_start_sec = parse_timestamp_seconds(song_start_raw)

            pt_raw = (row.get("post_type") or row.get("type") or "").strip().lower()
            if pt_raw in ("post", "photo", "image"):
                post_type = PostType.POST
            elif pt_raw in ("story",):
                post_type = PostType.STORY
            elif pt_raw in ("reel", "video", "short"):
                post_type = PostType.REEL
            else:
                # Auto-detect from media file extension
                media_c = (video_path or video_url).lower()
                if any(media_c.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")):
                    post_type = PostType.POST
                else:
                    post_type = PostType.REEL

            platforms = []
            if str(row.get("instagram", "true")).strip().lower() in ("true", "1", "yes"):
                platforms.append(PlatformType.INSTAGRAM)
            if str(row.get("facebook", "false")).strip().lower() in ("true", "1", "yes"):
                platforms.append(PlatformType.FACEBOOK)
            if str(row.get("threads", "false")).strip().lower() in ("true", "1", "yes"):
                platforms.append(PlatformType.THREADS)
            if str(row.get("youtube", "false")).strip().lower() in ("true", "1", "yes"):
                platforms.append(PlatformType.YOUTUBE)

        # 2. Brand Resolution & Verification
        assigned_brand = None
        if brand_name_raw:
            matched = brand_name_map.get(brand_name_raw.lower())
            if matched:
                assigned_brand = matched
            else:
                row_errors.append(f"Brand '{brand_name_raw}' does not match any registered workspace.")
                can_import = False
                has_brand_errors = True
                error_brand = True
        else:
            assigned_brand = default_brand

        # 3. Date & Time Verification
        dt_obj, formatted_date, formatted_time, dt_warnings = parse_datetime_flexible(
            date_str, time_str, date_format_pref, time_format_pref
        )
        row_warnings.extend(dt_warnings)

        # 4. Media Resolution & Verification
        resolved_media_path = None
        has_valid_media = False

        if video_path:
            res_path, exists, err = resolve_media_path(video_path)
            if exists:
                resolved_media_path = res_path
                has_valid_media = True
            else:
                row_warnings.append(f"Local video file not found: '{video_path}'. Will be imported as draft.")
                import_as_draft = True
                has_any_errors = True
                error_media = True
        elif video_url:
            drive_id = extract_google_drive_id(video_url)
            if drive_id:
                has_valid_media = True
                resolved_media_path = video_url
                row_warnings.append(f"Google Drive link detected. Ensure file sharing is set to 'Anyone with the link'.")
            elif video_url.startswith("http://") or video_url.startswith("https://"):
                has_valid_media = True
                resolved_media_path = video_url
            else:
                row_warnings.append(f"Unrecognized URL: '{video_url}'. Preview unavailable.")
                has_unidentified_urls = True
                import_as_draft = True
                has_any_errors = True
                error_media = True
        else:
            row_warnings.append("Missing video path or URL. Post will be saved as draft.")
            import_as_draft = True
            has_any_errors = True
            error_media = True

        # 5. Target Platforms Check
        if not platforms:
            row_errors.append("No target platforms selected.")
            can_import = False
            has_any_errors = True
            error_platforms = True

        if is_draft:
            import_as_draft = True

        # Determine Row Status
        if row_errors:
            row_status = "error"
            has_any_errors = True
        elif row_warnings or import_as_draft:
            row_status = "warning"
            has_any_errors = True
        else:
            row_status = "valid"

        posts_report.append({
            "row_index": idx,
            "status": row_status,
            "can_import": can_import,
            "import_as_draft": import_as_draft,
            "brand_id": assigned_brand.id if assigned_brand else None,
            "brand_name": assigned_brand.name if assigned_brand else (brand_name_raw or "Unknown"),
            "brand_color": assigned_brand.color_badge if assigned_brand else "#ef4444",
            "error_brand": error_brand,
            "error_media": error_media,
            "error_platforms": error_platforms,
            "date_formatted": formatted_date,
            "time_formatted": formatted_time,
            "scheduled_iso": dt_obj.strftime("%Y-%m-%dT%H:%M:%S"),
            "caption": caption or "(No caption)",
            "post_type": post_type.value,
            "first_comment": first_comment or None,
            "youtube_title": youtube_title or None,
            "music_query": song_name or None,
            "audio_start_sec": audio_start_sec,
            "platforms": [p.value for p in platforms],
            "video_path": resolved_media_path or video_path or None,
            "video_url": video_url or None,
            "thumbnail_url": thumbnail_url or None,
            "errors": row_errors,
            "warnings": row_warnings
        })

    can_import_count = sum(1 for p in posts_report if p["can_import"])
    errors_count = sum(1 for p in posts_report if p["status"] == "error")
    warnings_count = sum(1 for p in posts_report if p["status"] == "warning")

    return {
        "format_detected": detected_format,
        "total_rows": len(posts_report),
        "can_import_count": can_import_count,
        "errors_count": errors_count,
        "warnings_count": warnings_count,
        "has_errors": has_any_errors,
        "has_brand_errors": has_brand_errors,
        "has_unidentified_urls": has_unidentified_urls,
        "banner_errors": {
            "some_posts_have_errors": has_any_errors or warnings_count > 0,
            "wrong_brand_names": has_brand_errors,
            "unidentified_urls": has_unidentified_urls
        },
        "posts": posts_report
    }


def import_validated_posts(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Creates ScheduledPost records in SQLite database for all valid posts.
    """
    imported = []
    drafts = []
    skipped = []

    for post_data in posts:
        if not post_data.get("can_import", True):
            skipped.append(post_data)
            continue

        brand_id = post_data.get("brand_id")
        if not brand_id:
            skipped.append(post_data)
            continue

        platforms = [PlatformType(p) for p in post_data.get("platforms", ["instagram"])]
        media_list = []
        if post_data.get("video_path"):
            media_list.append(post_data["video_path"])
        elif post_data.get("video_url"):
            media_list.append(post_data["video_url"])

        # Determine Scheduled Time
        scheduled_iso = post_data.get("scheduled_iso")
        try:
            dt = datetime.fromisoformat(scheduled_iso)
            if dt < datetime.now():
                scheduled_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            scheduled_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        is_draft = post_data.get("import_as_draft", False) or post_data.get("status") in ("warning", "error")

        # Check if media is a Google Drive URL and download it locally
        final_media_list = []
        for m in media_list:
            gdrive_id = extract_google_drive_id(m)
            if gdrive_id:
                dest = DOWNLOADS_DIR / f"gdrive_{gdrive_id}.mp4"
                if not dest.exists() or dest.stat().st_size == 0:
                    ok = download_google_drive_file(gdrive_id, dest)
                    if ok and dest.exists():
                        final_media_list.append(str(dest.resolve()))
                    else:
                        final_media_list.append(m)
                else:
                    final_media_list.append(str(dest.resolve()))
            else:
                final_media_list.append(m)

        post_type_str = post_data.get("post_type", "reel")
        try:
            post_type_enum = PostType(post_type_str)
        except Exception:
            post_type_enum = PostType.REEL

        created = create_post(ScheduledPostCreate(
            brand_id=brand_id,
            target_platforms=platforms,
            post_type=post_type_enum,
            media_paths=final_media_list,
            caption=post_data.get("caption", ""),
            first_comment=post_data.get("first_comment"),
            scheduled_time=scheduled_iso,
            music_query=post_data.get("music_query"),
            audio_start_sec=post_data.get("audio_start_sec"),
            share_to_facebook=PlatformType.FACEBOOK in platforms,
            share_to_threads=PlatformType.THREADS in platforms,
            youtube_title=post_data.get("youtube_title")
        ))

        if is_draft:
            drafts.append(created.id)
        else:
            imported.append(created.id)

    return {
        "status": "success",
        "total_imported": len(imported) + len(drafts),
        "scheduled_count": len(imported),
        "draft_count": len(drafts),
        "skipped_count": len(skipped),
        "post_ids": imported + drafts
    }
