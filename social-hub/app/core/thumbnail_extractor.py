"""
🎬 High-Speed Video Thumbnail Auto-Extractor & Optimization Pipeline
Extracts high-res poster frames at 00:00:01 using fast input seeking in FFmpeg.
Caches WebP/JPEG thumbnails in social-hub/data/thumbnails/ to drop DOM network payload
from ~50MB video streams to ~25KB per tile.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict
import logging

from app.config import THUMBNAILS_DIR

logger = logging.getLogger("ThumbnailExtractor")


def extract_thumbnail(
    video_path: str | Path,
    target_dir: Path = THUMBNAILS_DIR,
    time_offset: str = "00:00:01",
    width: int = 480
) -> Optional[str]:
    """
    Extracts a 480px-wide poster frame from an MP4 video at time_offset.
    Uses input-level seek (-ss before -i) for sub-second extraction.
    Returns the filename of the cached thumbnail (e.g. 'reel_1_1726750000.webp').
    """
    video_file = Path(video_path).resolve()
    if not video_file.exists() or video_file.suffix.lower() != ".mp4":
        return None

    target_dir.mkdir(parents=True, exist_ok=True)
    mtime = int(video_file.stat().st_mtime)
    base_name = f"{video_file.stem}_{mtime}"
    webp_filename = f"{base_name}.webp"
    jpg_filename = f"{base_name}.jpg"

    webp_path = target_dir / webp_filename
    jpg_path = target_dir / jpg_filename

    # 1. Instant Cache Hit Check
    if webp_path.exists() and webp_path.stat().st_size > 500:
        return webp_filename
    if jpg_path.exists() and jpg_path.stat().st_size > 500:
        return jpg_filename

    # 2. Extract with WebP encoding (Ultra-lightweight ~25KB)
    cmd_webp = [
        "ffmpeg",
        "-y",
        "-ss", time_offset,
        "-i", str(video_file),
        "-frames:v", "1",
        "-vf", f"scale={width}:-1",
        "-c:v", "libwebp",
        "-quality", "75",
        str(webp_path)
    ]

    try:
        res = subprocess.run(cmd_webp, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8)
        if res.returncode == 0 and webp_path.exists() and webp_path.stat().st_size > 0:
            return webp_filename
    except Exception as err:
        logger.warning(f"WebP extraction failed for {video_file.name}: {err}. Trying JPEG fallback.")

    # 3. Fallback to standard JPEG if libwebp fails
    cmd_jpg = [
        "ffmpeg",
        "-y",
        "-ss", time_offset,
        "-i", str(video_file),
        "-frames:v", "1",
        "-vf", f"scale={width}:-1",
        "-q:v", "3",
        str(jpg_path)
    ]

    try:
        res_jpg = subprocess.run(cmd_jpg, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8)
        if res_jpg.returncode == 0 and jpg_path.exists() and jpg_path.stat().st_size > 0:
            return jpg_filename
    except Exception as err:
        logger.error(f"Thumbnail extraction failed completely for {video_file.name}: {err}")

    return None


def batch_extract_thumbnails(video_paths: List[str | Path]) -> Dict[str, Optional[str]]:
    """
    Extracts thumbnails for a batch of video paths.
    Returns mapping {str(video_path): thumbnail_filename_or_None}.
    """
    results = {}
    for p in video_paths:
        try:
            results[str(p)] = extract_thumbnail(p)
        except Exception as e:
            logger.warning(f"Failed to extract thumbnail for {p}: {e}")
            results[str(p)] = None
    return results
