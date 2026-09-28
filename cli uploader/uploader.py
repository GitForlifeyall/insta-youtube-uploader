#!/usr/bin/env python3
"""
CLI Uploader for YouTube Shorts via Redroid Automation
======================================================
Automated end-to-end publishing pipeline:
1. Resolves brand container, ADB port, and designated content folder from SQLite.
2. Automatically launches the brand's Redroid container (via redroid.ps1 start).
3. Automatically launches the Scrcpy live screen mirroring window.
4. Randomly selects video(s) from the brand folder.
5. Scans JSON files (e.g. batch_manifest.json, links.json, metadata.json) inside the brand folder for:
   - Rewritten title & full caption
   - Tags (appended to title up to 95 chars)
   - Song name & artist name (combined for YouTube audio search)
   - Audio start timestamp (seconds or MM:SS)
6. Uploads the Short using upload_short.py with all resolved metadata.
7. Waits 3 minutes (with a live countdown) and automatically shuts down the container.

Usage Examples:
    # Pick a random video from Brand Alpha, auto-extract metadata from batch_manifest.json, upload & close:
    python uploader.py -b "Brand Alpha"

    # Upload for Account 01 with live Scrcpy, custom song override:
    python uploader.py -b 01 -s "Lo-Fi Beats"

    # Upload 3 random videos in batch:
    python uploader.py -b 02 --count 3

    # Upload without shutting down container afterwards:
    python uploader.py -b 01 --no-close
"""

import os
import sys
import re
import json
import time
import random
import argparse
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

# Ensure ytuploader module can be resolved
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent
YTUPLOADER_DIR = REPO_ROOT / "ytuploader"
REDROID_PS1 = YTUPLOADER_DIR / "redroid.ps1"

if str(YTUPLOADER_DIR) not in sys.path:
    sys.path.insert(0, str(YTUPLOADER_DIR))

try:
    import upload_short
except ImportError:
    sys.path.append(str(REPO_ROOT))
    from ytuploader import upload_short

try:
    from db import get_brand_by_identifier, get_all_brands
except ImportError:
    from .db import get_brand_by_identifier, get_all_brands


SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}


def load_brand_metadata(brand_folder: Path, log_fn: Optional[Any] = None) -> Dict[str, Dict[str, Any]]:
    """
    Scans all JSON files inside brand_folder (and falls back to links.json at workspace root).
    Indexes metadata by filename, stem, item index, rewritten title, and song title.
    Supports list structures, nested dicts, and batch_manifest.json formats.
    """
    def _l(msg: str):
        if log_fn:
            log_fn(msg)
        else:
            print(msg, flush=True)

    metadata_map: Dict[str, Dict[str, Any]] = {}
    json_files: List[Path] = []

    if brand_folder.exists() and brand_folder.is_dir():
        json_files.extend(sorted(brand_folder.glob("*.json")))

    # Fallback to root links.json only if brand folder has no local JSON metadata files
    if not json_files:
        root_links = REPO_ROOT / "links.json"
        if root_links.exists():
            json_files.append(root_links)

    if not json_files:
        _l("[*] No JSON metadata files found in brand folder or workspace root.")
        return metadata_map

    _l(f"[*] Scanning {len(json_files)} metadata JSON file(s)...")

    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)

            items_to_process = []
            if isinstance(data, list):
                items_to_process = data
            elif isinstance(data, dict):
                if "items" in data and isinstance(data["items"], list):
                    # Batch manifest structure (e.g. batch_manifest.json)
                    items_to_process = data["items"]
                else:
                    # Check if dict maps keys -> subdicts
                    has_nested = False
                    for k, v in data.items():
                        if isinstance(v, dict):
                            has_nested = True
                            clean_k = k.lower().strip()
                            stem_k = Path(k).stem.lower().strip()
                            metadata_map[clean_k] = v
                            metadata_map[stem_k] = v
                    if not has_nested:
                        metadata_map[jf.stem.lower().strip()] = data

            for item in items_to_process:
                if not isinstance(item, dict):
                    continue
                # Flatten any nested "metadata" dict
                merged_item = dict(item)
                if "metadata" in item and isinstance(item["metadata"], dict):
                    merged_item.update(item["metadata"])

                # Index by all known filename keys
                for k in (
                    "filename", "output_filename", "video_filename", "source_video_filename",
                    "slide_filename", "photo_filename", "media_filename", "file", "name", "video_url"
                ):
                    val = merged_item.get(k)
                    if val and isinstance(val, str):
                        clean_val = val.lower().strip()
                        stem_val = Path(val).stem.lower().strip()
                        metadata_map[clean_val] = merged_item
                        metadata_map[stem_val] = merged_item

                # Index by title / rewritten_title / track_name / song_name
                for tk in ("title", "rewritten_title", "track_name", "song_name"):
                    tval = merged_item.get(tk)
                    if tval and isinstance(tval, str):
                        metadata_map[tval.lower().strip()] = merged_item

                # Index by item_index
                if merged_item.get("item_index") is not None:
                    idx_val = str(merged_item["item_index"])
                    metadata_map[idx_val] = merged_item
                    try:
                        int_idx = int(idx_val)
                        metadata_map[f"{int_idx:03d}"] = merged_item
                        metadata_map[f"{int_idx:02d}"] = merged_item
                    except Exception:
                        pass

        except Exception as e:
            _l(f"[!] Warning reading '{jf.name}': {e}")

    _l(f"[+] Loaded {len(metadata_map)} metadata associations.")
    return metadata_map


def find_metadata_for_video(video_path: Path, metadata_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Finds the best matching metadata entry for a video file."""
    name_lower = video_path.name.lower().strip()
    stem_lower = video_path.stem.lower().strip()

    # 1. Exact filename or stem match
    if name_lower in metadata_map:
        return metadata_map[name_lower]
    if stem_lower in metadata_map:
        return metadata_map[stem_lower]

    # 2. Substring matching (e.g. "001_slime_you_out" in "001_slime_you_out_drake.png")
    for key, val in metadata_map.items():
        if key in name_lower or key in stem_lower or stem_lower in key:
            return val

    # 3. Match by leading number/index if filename starts with digits (e.g. "001_...", "1_...")
    m = re.match(r"^0*(\d+)", stem_lower)
    if m:
        num_str = str(int(m.group(1)))
        if num_str in metadata_map:
            return metadata_map[num_str]

    return {}


def format_tag_as_hashtag(tag: str) -> str:
    """Formats a tag into a clean #hashtag format."""
    clean = re.sub(r"[^\w\d]", "", tag)
    if not clean:
        return ""
    return f"#{clean}"


def extract_video_metadata(
    video_path: Path,
    meta: Dict[str, Any],
    default_caption: Optional[str] = None,
    default_song: Optional[str] = None,
    default_timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extracts title with tags, caption, song search query with artist, and timestamps from metadata.
    """
    # 1. Song Name & Artist Name (combined for YouTube audio search)
    raw_song = default_song
    if not raw_song:
        for sk in ("song_name", "track_name", "sound", "audio_name", "audio", "song", "track"):
            if sk in meta and meta[sk] is not None and str(meta[sk]).strip():
                raw_song = str(meta[sk]).strip()
                break

    artist = ""
    for ak in ("artist_name", "artist", "author", "singer", "artistName", "creator"):
        if ak in meta and meta[ak] is not None and str(meta[ak]).strip():
            artist = str(meta[ak]).strip()
            break

    # Build audio search query for YouTube music library: "{song_name} by {artist}"
    audio_search = raw_song
    if raw_song:
        if artist:
            # If artist is not already preceded by "by", format as "{song_name} by {artist}"
            if " by " not in raw_song.lower():
                if artist.lower() in raw_song.lower():
                    # e.g., "Song Artist" -> "Song by Artist"
                    base_song = re.sub(re.escape(artist), "", raw_song, flags=re.IGNORECASE).strip(" -—_")
                    if base_song:
                        audio_search = f"{base_song} by {artist}".strip()
                    else:
                        audio_search = raw_song.strip()
                else:
                    audio_search = f"{raw_song} by {artist}".strip()
            else:
                audio_search = raw_song.strip()
        else:
            audio_search = raw_song.strip()

    # 2. Timestamp / Start Seconds
    raw_ts = default_timestamp
    if raw_ts is None:
        for k in (
            "start_seconds", "start_time", "startTime", "start", "timeSeconds", "time_seconds",
            "audio_timestamp", "audio_start", "song_start", "start_offset",
            "timestamp", "time"
        ):
            if k in meta and meta[k] is not None and str(meta[k]).strip() != "":
                raw_ts = meta[k]
                break

    if raw_ts is None:
        # Check syncedLines or detailed_cues if available
        for cue_key in ("syncedLines", "detailed_cues", "cues"):
            cues = meta.get(cue_key)
            if isinstance(cues, list) and len(cues) > 0:
                for c in cues:
                    if isinstance(c, dict):
                        for ck in ("timestamp", "timeSeconds", "startSeconds", "start_time", "start"):
                            if ck in c and c[ck] is not None and str(c[ck]).strip() != "":
                                raw_ts = c[ck]
                                break
                    if raw_ts is not None:
                        break
            if raw_ts is not None:
                break

    timestamp_str = None
    if raw_ts is not None:
        try:
            if isinstance(raw_ts, (int, float)):
                sec_val = float(raw_ts)
                timestamp_str = f"{int(sec_val // 60)}:{int(sec_val % 60):02d}"
            else:
                str_ts = str(raw_ts).strip()
                if re.match(r"^\d+(?:\.\d+)?$", str_ts):
                    sec_val = float(str_ts)
                    timestamp_str = f"{int(sec_val // 60)}:{int(sec_val % 60):02d}"
                else:
                    timestamp_str = str_ts
        except Exception:
            timestamp_str = str(raw_ts).strip()

    # 3. Title & Caption construction
    rewritten_title = meta.get("rewritten_title")
    title = meta.get("title")
    rewritten_caption = meta.get("rewritten_caption") or meta.get("caption") or meta.get("description")
    raw_tags = meta.get("tags") or meta.get("hashtags") or []

    # Format tags
    hashtags = []
    if isinstance(raw_tags, list):
        for t in raw_tags:
            if isinstance(t, str) and t.strip():
                ht = format_tag_as_hashtag(t.strip())
                if ht and ht.lower() not in [h.lower() for h in hashtags]:
                    hashtags.append(ht)
    elif isinstance(raw_tags, str):
        for t in raw_tags.split():
            ht = format_tag_as_hashtag(t)
            if ht and ht.lower() not in [h.lower() for h in hashtags]:
                hashtags.append(ht)

    # Always ensure #shorts is available
    if "#shorts" not in [h.lower() for h in hashtags]:
        hashtags.insert(0, "#shorts")

    if default_caption:
        short_title = default_caption
    elif rewritten_title:
        base_title = rewritten_title.strip()
        # Append tags up to YouTube 95 chars limit
        current_title = base_title
        for ht in hashtags:
            if ht.lower() not in current_title.lower():
                candidate = f"{current_title} {ht}".strip()
                if len(candidate) <= 95:
                    current_title = candidate
                else:
                    break
        short_title = current_title
    elif title:
        base_title = f"{title} - {artist}".strip() if artist and artist.lower() not in title.lower() else title.strip()
        current_title = base_title
        for ht in hashtags:
            if ht.lower() not in current_title.lower():
                candidate = f"{current_title} {ht}".strip()
                if len(candidate) <= 95:
                    current_title = candidate
                else:
                    break
        short_title = current_title
    elif rewritten_caption:
        lines = [l.strip().strip('"').strip("'") for l in rewritten_caption.splitlines() if l.strip()]
        first_line = lines[0] if lines else video_path.stem
        if "#shorts" not in first_line.lower():
            short_title = f"{first_line[:80]} #shorts"
        else:
            short_title = first_line[:95]
    else:
        short_title = f"{video_path.stem.replace('_', ' ').replace('-', ' ')} #shorts"

    return {
        "title": short_title,
        "caption": rewritten_caption or short_title,
        "rewritten_title": rewritten_title,
        "song_name": audio_search,
        "raw_song_name": raw_song,
        "artist": artist,
        "timestamp": timestamp_str,
        "hashtags": hashtags
    }


def start_redroid_container(brand_account: str, ps_script: Path = REDROID_PS1, log_fn: Optional[Any] = None) -> bool:
    """Launches the Redroid container for the specified brand using redroid.ps1 start."""
    def _l(msg: str):
        if log_fn: log_fn(msg)
        else: print(msg, flush=True)

    if not ps_script.exists():
        _l(f"[!] redroid.ps1 not found at: {ps_script}")
        return False

    _l(f"[*] 🚀 Starting Redroid container for brand '{brand_account}' via redroid.ps1...")
    cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_script), "start", str(brand_account)]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="ignore",
            cwd=str(YTUPLOADER_DIR)
        )
        try:
            stdout_text, _ = proc.communicate(timeout=180)
            if stdout_text:
                for line in stdout_text.splitlines():
                    stripped = line.rstrip()
                    if stripped:
                        _l(f"    {stripped}")
        except subprocess.TimeoutExpired:
            proc.kill()
            _l("[!] Container startup timed out after 180 seconds.")
            return False

        return proc.returncode == 0
    except Exception as e:
        _l(f"[!] Failed to execute redroid.ps1 start: {e}")
        return False


def stop_redroid_container(brand_account: str, ps_script: Path = REDROID_PS1, log_fn: Optional[Any] = None) -> bool:
    """Stops the Redroid container for the specified brand using redroid.ps1 stop."""
    def _l(msg: str):
        if log_fn: log_fn(msg)
        else: print(msg, flush=True)

    if not ps_script.exists():
        return False

    _l(f"[*] 🛑 Stopping Redroid container for brand '{brand_account}' via redroid.ps1...")
    cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_script), "stop", str(brand_account)]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="ignore",
            cwd=str(YTUPLOADER_DIR)
        )
        try:
            stdout_text, _ = proc.communicate(timeout=60)
            if stdout_text:
                for line in stdout_text.splitlines():
                    stripped = line.rstrip()
                    if stripped:
                        _l(f"    {stripped}")
        except subprocess.TimeoutExpired:
            proc.kill()
            _l("[!] Container shutdown timed out after 60 seconds.")
            return False

        return proc.returncode == 0
    except Exception as e:
        _l(f"[!] Failed to execute redroid.ps1 stop: {e}")
        return False


def wait_with_countdown(seconds: int = 180, brand_account: str = "01", log_fn: Optional[Any] = None):
    """Waits for specified duration with live countdown before shutting down container."""
    def _l(msg: str):
        if log_fn: log_fn(msg)
        else: print(msg, flush=True)

    if seconds <= 0:
        return

    _l(f"\n[*] Upload sequence completed! Waiting {seconds}s ({seconds // 60}m) before closing container '{brand_account}'...")
    start = time.time()
    try:
        while time.time() - start < seconds:
            remaining = int(seconds - (time.time() - start))
            mins, secs = divmod(remaining, 60)
            sys.stdout.write(f"\r⏳ Closing container in {mins:02d}:{secs:02d}... (Press Ctrl+C to close immediately) ")
            sys.stdout.flush()
            time.sleep(1)
        print()
    except KeyboardInterrupt:
        print("\n[!] User skipped wait timer. Proceeding to shutdown.")


def upload_short_pipeline(
    brand_name: str = "01",
    content_folder: Optional[Union[str, Path]] = None,
    caption: Optional[str] = None,
    song_name: Optional[str] = None,
    timestamp: Optional[str] = None,
    media_name: Optional[str] = None,
    view: bool = True,
    auto_start: bool = True,
    auto_close: bool = True,
    wait_close_seconds: int = 180,
    random_select: bool = True,
    count: int = 1,
    adb_path: Optional[str] = None,
    scrcpy_path: Optional[str] = None,
    clean_before: bool = False,
    log_fn: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """
    Full automated upload pipeline matching user specifications:
    - Resolves brand details and folder from SQLite database
    - Starts the Redroid container via redroid.ps1 start
    - Launches Scrcpy screen mirror
    - Picks videos randomly from brand folder
    - Scans JSON files for rewritten title, tags, song, artist, and timestamps
    - Runs YouTube Shorts upload
    - Waits 3 minutes and closes the container
    """
    def _log(msg: str):
        if log_fn:
            log_fn(msg)
        else:
            print(msg, flush=True)

    # 1. Resolve Brand Details from SQLite Database
    try:
        db_brand = get_brand_by_identifier(str(brand_name))
    except Exception:
        db_brand = None

    if db_brand:
        account_arg = db_brand["brand_id"]
        raw_target = db_brand["adb_target"]
        display_name = f"{db_brand['name']} ({db_brand['container_name']})"
        brand_folder_path = Path(db_brand.get("folder_path") or REPO_ROOT / "brand folders" / db_brand["name"])
    else:
        raw_target, display_name = upload_short.resolve_target(str(brand_name))
        account_arg = str(brand_name)
        brand_folder_path = REPO_ROOT / "brand folders" / str(brand_name)

    # 2. Resolve Content Folder
    folder_to_use = Path(content_folder).resolve() if content_folder else brand_folder_path
    if not folder_to_use.exists():
        # Fallback to local upload files
        alt_folder = YTUPLOADER_DIR / "upload files"
        if alt_folder.exists():
            folder_to_use = alt_folder
        else:
            raise FileNotFoundError(f"Brand content folder not found at: {folder_to_use}")

    # 3. Discover Video Files in Folder
    video_files: List[Path] = []
    if folder_to_use.is_file():
        if folder_to_use.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"File '{folder_to_use}' is not a supported video file ({SUPPORTED_EXTENSIONS})")
        video_files = [folder_to_use]
    else:
        for f in folder_to_use.glob("*"):
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                video_files.append(f)

    if not video_files:
        raise FileNotFoundError(f"No video files found in content folder: {folder_to_use}")

    # 4. Select Videos (Random or Full Batch)
    if random_select:
        random.shuffle(video_files)

    if count > 0:
        selected_videos = video_files[:count]
    else:
        selected_videos = video_files

    _log("=" * 65)
    _log(f"  🎬 REDROID AUTONOMOUS SHORTS UPLOADER")
    _log(f"  Brand Target:   {display_name}")
    _log(f"  Content Folder: {folder_to_use}")
    _log(f"  Total Videos:   {len(video_files)} (Uploading: {len(selected_videos)})")
    _log(f"  Scrcpy Mirror:  {'Enabled' if view else 'Disabled'}")
    _log(f"  Auto-Shutdown:  {'Enabled (' + str(wait_close_seconds) + 's wait)' if auto_close else 'Disabled'}")
    _log("=" * 65)

    # 5. Resolve ADB and Scrcpy Executables
    adb_exe = adb_path or upload_short.find_tool("adb", upload_short.DEFAULT_ADB)
    scrcpy_exe = scrcpy_path or upload_short.find_tool("scrcpy", upload_short.DEFAULT_SCRCPY)

    # 6. Auto-Start Container (if requested)
    if auto_start:
        start_redroid_container(account_arg, REDROID_PS1, log_fn=_log)

    # 7. Connect ADB Target
    active_target = upload_short.connect_adb(adb_exe, raw_target, log_fn=_log)

    # 8. Launch Live Scrcpy Viewer
    if view:
        upload_short.launch_scrcpy(scrcpy_exe, active_target, log_fn=_log)

    # 9. Load Metadata from JSON files in the brand folder (and links.json)
    metadata_map = load_brand_metadata(folder_to_use if folder_to_use.is_dir() else folder_to_use.parent, log_fn=_log)

    # 10. Optional pre-clean
    if clean_before:
        yt_pkg = upload_short.get_installed_youtube_package(adb_exe, active_target)
        _log(f"[*] Pre-cleaning emulator media and {yt_pkg} upload cache...")
        upload_short.clean_emulator_media(adb_exe, active_target, log_fn=_log)
        upload_short.clean_youtube_upload_session(adb_exe, active_target, yt_pkg, log_fn=_log)

    results: List[Dict[str, Any]] = []

    try:
        for idx, video in enumerate(selected_videos, 1):
            _log(f"\n[{idx}/{len(selected_videos)}] Preparing Video: {video.name}")

            # Match JSON metadata
            meta = find_metadata_for_video(video, metadata_map)
            details = extract_video_metadata(
                video_path=video,
                meta=meta,
                default_caption=caption,
                default_song=song_name,
                default_timestamp=timestamp
            )

            _log(f"    Short Title: {details['title']}")
            if details["song_name"]:
                _log(f"    Sound Track: {details['song_name']} (Timestamp: {details['timestamp'] or 'Default'})")
            if details["artist"]:
                _log(f"    Artist:      {details['artist']}")

            start_t = time.time()
            success = False
            error_msg = None

            try:
                upload_short.upload_short_to_youtube(
                    adb_exe=adb_exe,
                    target=active_target,
                    video_path=str(video),
                    title=details["title"],
                    sound=details["song_name"],
                    timestamp=details["timestamp"],
                    media_name=media_name,
                    log_fn=_log
                )
                success = True
                _log(f"[+] Successfully uploaded '{video.name}' to {display_name}!")
            except Exception as e:
                error_msg = str(e)
                _log(f"[!] Error uploading '{video.name}': {e}")

            elapsed = round(time.time() - start_t, 2)
            results.append({
                "video_path": str(video),
                "video_name": video.name,
                "title": details["title"],
                "song_name": details["song_name"],
                "timestamp": details["timestamp"],
                "brand": display_name,
                "success": success,
                "duration_sec": elapsed,
                "error": error_msg
            })

    finally:
        # 11. Summary
        success_count = sum(1 for r in results if r["success"])
        _log("\n" + "=" * 65)
        _log(f"  🏁 BATCH RUN FINISHED: {success_count}/{len(selected_videos)} Uploads Successful")
        _log("=" * 65)

        # 12. Post-Upload: Wait 3 minutes and close container
        if auto_close:
            wait_with_countdown(seconds=wait_close_seconds, brand_account=account_arg, log_fn=_log)
            stop_redroid_container(account_arg, REDROID_PS1, log_fn=_log)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Redroid YouTube Shorts Uploader with JSON Metadata Matching & Auto-Shutdown",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-b", "--brand",
        dest="brand_name",
        default="01",
        help="Brand name or Redroid account (e.g. 01, 02, 'Brand Alpha', 5555)"
    )

    parser.add_argument(
        "-f", "--folder", "--content",
        dest="content_folder",
        default=None,
        help="Custom content folder or video path (defaults to brand's folder in 'brand folders/')"
    )

    parser.add_argument(
        "-c", "--caption", "--title",
        dest="caption",
        default=None,
        help="Custom title override (if not specified, auto-extracted from JSON or filename)"
    )

    parser.add_argument(
        "-s", "--song", "--sound",
        dest="song_name",
        default=None,
        help="Audio / song title override (if not specified, auto-extracted from JSON)"
    )

    parser.add_argument(
        "-t", "--timestamp",
        dest="timestamp",
        default=None,
        help="Audio start timestamp (e.g. '0:15', '0:30', 'random', or auto-extracted from JSON)"
    )

    parser.add_argument(
        "-m", "-n", "--name", "--media-name",
        dest="media_name",
        default=None,
        help="Custom filename to store inside Android MediaStore"
    )

    parser.add_argument(
        "-k", "--count",
        dest="count",
        type=int,
        default=1,
        help="Number of random videos to upload from brand folder (0 for all)"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Upload all videos found in the brand folder instead of picking a random one"
    )

    parser.add_argument(
        "--no-random",
        action="store_true",
        help="Process videos sequentially in alphabetical order instead of randomizing"
    )

    parser.add_argument(
        "--no-scrcpy",
        dest="no_scrcpy",
        action="store_true",
        help="Disable automatic Scrcpy screen mirror window"
    )

    parser.add_argument(
        "--no-start",
        action="store_true",
        help="Do not auto-start the container (assumes it is already running)"
    )

    parser.add_argument(
        "--no-close",
        action="store_true",
        help="Do not shut down the container after upload"
    )

    parser.add_argument(
        "--wait",
        dest="wait_seconds",
        type=int,
        default=180,
        help="Seconds to wait before shutting down container (default: 180s / 3 mins)"
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean device media and clear stale YouTube upload sessions before uploading"
    )

    parser.add_argument(
        "--adb",
        dest="adb_path",
        default=None,
        help="Custom path to adb.exe"
    )

    parser.add_argument(
        "--scrcpy",
        dest="scrcpy_path",
        default=None,
        help="Custom path to scrcpy.exe"
    )

    args = parser.parse_args()

    upload_count = 0 if args.all else args.count

    try:
        results = upload_short_pipeline(
            brand_name=args.brand_name,
            content_folder=args.content_folder,
            caption=args.caption,
            song_name=args.song_name,
            timestamp=args.timestamp,
            media_name=args.media_name,
            view=not args.no_scrcpy,
            auto_start=not args.no_start,
            auto_close=not args.no_close,
            wait_close_seconds=args.wait_seconds,
            random_select=not args.no_random,
            count=upload_count,
            adb_path=args.adb_path,
            scrcpy_path=args.scrcpy_path,
            clean_before=args.clean
        )
        failed = sum(1 for r in results if not r["success"])
        sys.exit(1 if failed > 0 else 0)
    except KeyboardInterrupt:
        print("\n[!] Upload pipeline interrupted by user.", flush=True)
        sys.exit(130)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
