"""
Song Recognition CLI Tool
Accepts a YouTube Short / Video URL (or Channel URL / Local Video),
locates the channel, retrieves its 5 most popular Shorts, and identifies
the background song in each with its exact match timestamp and Spotify link.
"""

import os
import sys
import time
import hmac
import base64
import hashlib
import argparse
import json
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv
import requests
import yt_dlp

# Fix Windows console UTF-8 output encoding for emojis
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Load environment variables from local .env and root .env
_script_dir = Path(__file__).resolve().parent
load_dotenv(_script_dir / ".env")
load_dotenv(_script_dir.parent / ".env")
load_dotenv()

# Compatibility for moviepy v1 and v2 (for local video files)
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    try:
        from moviepy import VideoFileClip
    except ImportError:
        VideoFileClip = None

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
except ImportError:
    spotipy = None
    SpotifyClientCredentials = None

try:
    from spotapi import Public as SpotApiPublic
except ImportError:
    SpotApiPublic = None


def get_local_video_duration(video_path: str) -> float:
    """Returns the total duration in seconds of a local video file."""
    try:
        import subprocess
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0 and res.stdout.strip():
            return float(res.stdout.strip())
    except Exception:
        pass

    if VideoFileClip is not None:
        try:
            clip = VideoFileClip(video_path)
            dur = float(clip.duration or 0.0)
            clip.close()
            if dur > 0:
                return dur
        except Exception:
            pass
    return 15.0


def extract_audio_from_local_video(video_path: str, output_audio_path: str, max_duration_sec: float = 15.0) -> bool:
    """Extracts up to the first `max_duration_sec` of audio from a local video file."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Primary: Use moviepy
    if VideoFileClip is not None:
        video_clip = None
        subclip = None
        try:
            video_clip = VideoFileClip(video_path)
            if video_clip.audio is not None:
                target_duration = min(float(video_clip.duration or max_duration_sec), max_duration_sec)
                subclip = video_clip.subclip(0, target_duration) if hasattr(video_clip, 'subclip') else video_clip.subclipped(0, target_duration)
                subclip.audio.write_audiofile(output_audio_path, logger=None)
                return True
        except Exception:
            pass
        finally:
            if subclip:
                try:
                    subclip.close()
                except Exception:
                    pass
            if video_clip:
                try:
                    video_clip.close()
                except Exception:
                    pass

    # Fallback: Use FFmpeg CLI
    import subprocess
    cmd = [
        "ffmpeg", "-y",
        "-ss", "0",
        "-t", str(max_duration_sec),
        "-i", video_path,
        "-vn",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        output_audio_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0 or not os.path.exists(output_audio_path):
        raise RuntimeError("Failed to extract audio from video using MoviePy or FFmpeg.")
    return True


def download_youtube_audio_sample(video_url: str, output_audio_path: str, max_duration_sec: float = 15.0) -> tuple:
    """Downloads up to the first `max_duration_sec` of audio directly from a YouTube video URL and returns (success, video_duration)."""
    ydl_opts = {
        "format": "ba[ext=m4a]/ba/b",
        "outtmpl": output_audio_path.replace(".mp3", "") + ".%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "postprocessor_args": ["-ss", "0", "-t", str(int(max_duration_sec))]
    }
    video_duration = 0.0
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        if info:
            video_duration = float(info.get("duration") or 0.0)

    expected_mp3 = output_audio_path if output_audio_path.endswith(".mp3") else f"{output_audio_path}.mp3"
    return os.path.exists(expected_mp3), video_duration


def get_channel_and_top_shorts(input_url: str, top_count: int = 5) -> Dict[str, Any]:
    """
    Given a YouTube video/Short URL or Channel URL, resolves the channel
    and extracts its top N most popular Shorts sorted by view count.
    """
    ydl_opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Determine if input is already a channel URL
        is_channel_url = bool(
            "/@" in input_url
            or "/channel/" in input_url
            or "/c/" in input_url
            or "/user/" in input_url
        )

        channel_url = None
        channel_name = None

        if is_channel_url:
            channel_url = input_url.split("/shorts")[0].split("/videos")[0].rstrip("/")
            channel_info = ydl.extract_info(channel_url, download=False)
            channel_name = channel_info.get("channel") or channel_info.get("uploader") or channel_info.get("title") or "Unknown Channel"
        else:
            # Extract info from the single video/Short link to get its channel URL
            print(f"🔗 Resolving channel from video link: {input_url}...")
            video_info = ydl.extract_info(input_url, download=False)
            channel_name = video_info.get("channel") or video_info.get("uploader") or "Unknown Channel"
            channel_url = video_info.get("channel_url") or video_info.get("uploader_url")
            
            if not channel_url and video_info.get("channel_id"):
                channel_url = f"https://www.youtube.com/channel/{video_info.get('channel_id')}"

        if not channel_url:
            raise RuntimeError(f"Could not determine the channel URL for: {input_url}")

        shorts_tab_url = f"{channel_url.rstrip('/')}/shorts"
        print(f"📺 Channel: \033[1m{channel_name}\033[0m ({channel_url})")
        print(f"🔎 Fetching shorts from: {shorts_tab_url}...")

        shorts_info = ydl.extract_info(shorts_tab_url, download=False)
        entries = list(shorts_info.get("entries", []))

        if not entries:
            # Fallback: try querying channel main URL if shorts tab returned empty
            print("⚠️ No entries found in /shorts tab; checking channel uploads...")
            channel_all_info = ydl.extract_info(channel_url, download=False)
            entries = list(channel_all_info.get("entries", []))

        if not entries:
            raise RuntimeError(f"No shorts or videos found on channel: {channel_name}")

        # Sort entries by view count descending to grab the most popular shorts
        def get_views(entry):
            return int(entry.get("view_count") or 0)

        sorted_entries = sorted(entries, key=get_views, reverse=True)
        top_shorts = sorted_entries[:top_count]

        parsed_shorts = []
        for rank, s in enumerate(top_shorts, 1):
            vid_id = s.get("id")
            vid_title = s.get("title", "Untitled Short")
            view_count = int(s.get("view_count") or 0)
            short_url = f"https://www.youtube.com/shorts/{vid_id}" if vid_id else (s.get("url") or s.get("webpage_url"))
            
            parsed_shorts.append({
                "rank": rank,
                "id": vid_id,
                "title": vid_title,
                "views": view_count,
                "url": short_url
            })

        return {
            "channel_name": channel_name,
            "channel_url": channel_url,
            "shorts": parsed_shorts
        }


def build_acrcloud_signature(
    http_method: str,
    http_uri: str,
    access_key: str,
    access_secret: str,
    data_type: str,
    signature_version: str,
    timestamp: str
) -> str:
    """Generates the HMAC-SHA1 signature required by the ACRCloud REST API."""
    string_to_sign = f"{http_method}\n{http_uri}\n{access_key}\n{data_type}\n{signature_version}\n{timestamp}"
    hmac_digest = hmac.new(
        access_secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha1
    ).digest()
    return base64.b64encode(hmac_digest).decode("utf-8")


def identify_song_acrcloud(audio_file_path: str) -> Optional[Dict[str, Any]]:
    """Sends audio sample to ACRCloud REST API (/v1/identify) and parses track details."""
    host = os.getenv("ACRCLOUD_HOST", "").strip().rstrip("/")
    access_key = os.getenv("ACRCLOUD_ACCESS_KEY", "").strip()
    access_secret = os.getenv("ACRCLOUD_ACCESS_SECRET", "").strip()

    if not host or not access_key or not access_secret:
        raise ValueError(
            "Missing ACRCloud credentials. Please set ACRCLOUD_HOST, ACRCLOUD_ACCESS_KEY, "
            "and ACRCLOUD_ACCESS_SECRET in your .env file."
        )

    req_url = f"https://{host}/v1/identify" if not host.startswith("http") else f"{host}/v1/identify"
    http_method = "POST"
    http_uri = "/v1/identify"
    data_type = "audio"
    signature_version = "1"
    timestamp = str(int(time.time()))

    signature = build_acrcloud_signature(
        http_method=http_method,
        http_uri=http_uri,
        access_key=access_key,
        access_secret=access_secret,
        data_type=data_type,
        signature_version=signature_version,
        timestamp=timestamp
    )

    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    sample_bytes = os.path.getsize(audio_file_path)

    data = {
        "access_key": access_key,
        "sample_bytes": sample_bytes,
        "timestamp": timestamp,
        "signature": signature,
        "data_type": data_type,
        "signature_version": signature_version,
    }

    with open(audio_file_path, "rb") as f:
        files = {"sample": (os.path.basename(audio_file_path), f, "audio/mpeg")}
        response = requests.post(req_url, data=data, files=files, timeout=15)

    if not response.ok:
        raise RuntimeError(f"ACRCloud API request failed with HTTP {response.status_code}: {response.text}")

    result_json = response.json()
    status_code = result_json.get("status", {}).get("code")

    if status_code != 0:
        msg = result_json.get("status", {}).get("msg", "Unknown error")
        if status_code in (1001, 2004, 2005):
            return None
        raise RuntimeError(f"ACRCloud recognition error [{status_code}]: {msg}")

    music_list = result_json.get("metadata", {}).get("music", [])
    if not music_list:
        return None

    top_match = music_list[0]
    title = top_match.get("title", "Unknown Title")
    artists = top_match.get("artists", [])
    singer = artists[0].get("name", "Unknown Artist") if artists else "Unknown Artist"
    
    play_offset_ms = top_match.get("play_offset_ms", 0)
    timestamp_seconds = round(float(play_offset_ms) / 1000.0, 2)

    return {
        "title": title,
        "singer": singer,
        "timestamp_seconds": timestamp_seconds,
        "play_offset_ms": play_offset_ms,
        "raw_metadata": top_match
    }


def search_spotify_track(title: str, singer: str, raw_metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Retrieves the Spotify track URL using:
    1. Direct ACRCloud external metadata (external_metadata.spotify.track.id)
    2. Spotipy Client Credentials search (if SPOTIFY_CLIENT_ID & SECRET are set)
    3. Local Spotify lyrics API service (http://localhost:8080)
    """
    # Strategy 1: Check ACRCloud direct Spotify link/ID in external_metadata
    if raw_metadata:
        spotify_meta = raw_metadata.get("external_metadata", {}).get("spotify", {})
        if spotify_meta:
            track_id = spotify_meta.get("track", {}).get("id")
            if track_id:
                return f"https://open.spotify.com/track/{track_id}"

    # Strategy 2: Spotipy Client Credentials search fallback
    client_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()

    if client_id and client_secret and spotipy:
        queries = [
            f"track:{title} artist:{singer}",
            f"{title} {singer}",
            f"{title}"
        ]
        import logging
        logging.getLogger("spotipy").setLevel(logging.CRITICAL)
        try:
            auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
            sp = spotipy.Spotify(auth_manager=auth_manager, retries=0, status_retries=0)
            for q in queries:
                try:
                    search_result = sp.search(q=q.strip(), type="track", limit=1)
                    items = search_result.get("tracks", {}).get("items", [])
                    if items and items[0].get("external_urls", {}).get("spotify"):
                        return items[0]["external_urls"]["spotify"]
                except Exception:
                    continue
        except Exception:
            pass


    # Strategy 3: Check local lyrics API service if running (http://localhost:8080)
    lyrics_api_url = os.getenv("SPOTIFY_LYRICS_API_URL", "http://localhost:8080").rstrip("/")
    query = f"{title} {singer}".strip()
    try:
        resp = requests.get(f"{lyrics_api_url}/search", params={"q": query}, timeout=4)
        if resp.ok:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0 and data[0].get("id"):
                return f"https://open.spotify.com/track/{data[0]['id']}"
    except Exception:
        pass

    # Strategy 4: SpotAPI Public Search Fallback (100% Free, No API Keys or Premium needed)
    if SpotApiPublic:
        try:
            pub = SpotApiPublic()
            for query_variant in [f"{title} {singer}".strip(), title.strip()]:
                for batch in pub.song_search(query_variant):
                    items = batch if isinstance(batch, list) else [batch]
                    for song_item in items:
                        track_data = song_item.get("item", {}).get("data", {})
                        track_id = track_data.get("id")
                        if track_id:
                            return f"https://open.spotify.com/track/{track_id}"
                    break
        except Exception:
            pass

    return None




def format_views(view_count: int) -> str:
    """Formats raw view count into human-readable representation (e.g. 1.2M, 450K)."""
    if view_count >= 1_000_000_000:
        return f"{view_count / 1_000_000_000:.1f}B"
    if view_count >= 1_000_000:
        return f"{view_count / 1_000_000:.1f}M"
    if view_count >= 1_000:
        return f"{view_count / 1_000:.1f}K"
    return str(view_count)


JSON_MODE = False


def emit_progress(stage: str, percent: int, message: str, extra: Optional[Dict[str, Any]] = None):
    """Emits real-time progress events formatted for Server-Sent Events (SSE)."""
    if JSON_MODE:
        payload = {"stage": stage, "percent": percent, "message": message}
        if extra:
            payload.update(extra)
        print(f"__RECOGNITION_PROGRESS__{json.dumps(payload, ensure_ascii=False)}", flush=True)


def emit_short_item(item: Dict[str, Any]):
    """Emits an individually recognized channel short in real-time."""
    if JSON_MODE:
        print(f"__SHORT_ITEM__{json.dumps(item, ensure_ascii=False)}", flush=True)


def emit_result(data: Dict[str, Any]):
    """Emits the final JSON result payload."""
    if JSON_MODE:
        print(f"__RECOGNITION_RESULT__{json.dumps(data, ensure_ascii=False)}", flush=True)


def process_single_video(video_input: str, is_youtube: bool, temp_dir: str, progress_cb=None, known_duration: float = 0.0) -> Optional[Dict[str, Any]]:
    """Extracts audio and recognizes the song for a single local or remote video."""
    audio_path = os.path.join(temp_dir, f"sample_{int(time.time() * 1000)}_{os.getpid()}.mp3")
    video_duration = float(known_duration or 0.0)
    
    try:
        if progress_cb:
            progress_cb("audio_extraction", "Extracting audio track...")
        if is_youtube:
            _, ytdl_dur = download_youtube_audio_sample(video_input, audio_path, max_duration_sec=15.0)
            if not video_duration or video_duration <= 0.1:
                video_duration = ytdl_dur
        else:
            extract_audio_from_local_video(video_input, audio_path, max_duration_sec=15.0)
            if not video_duration or video_duration <= 0.1:
                video_duration = get_local_video_duration(video_input)

        if not video_duration or video_duration <= 0.1:
            video_duration = 15.0

        if progress_cb:
            progress_cb("acrcloud_identifying", "Querying ACRCloud audio recognition engine...")
        track_info = identify_song_acrcloud(audio_path)
        if track_info:
            if progress_cb:
                progress_cb("spotify_matching", f"Resolving Spotify track link for \"{track_info['title']}\"...")
            spotify_url = search_spotify_track(
                track_info["title"],
                track_info["singer"],
                raw_metadata=track_info.get("raw_metadata")
            )
            track_info["spotify_url"] = spotify_url
            start_sec = float(track_info["timestamp_seconds"])
            dur = round(video_duration, 2)
            track_info["short_duration"] = dur
            track_info["start_seconds"] = start_sec
            track_info["end_seconds"] = round(start_sec + dur, 2)
        return track_info
    finally:
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception:
                pass


def main():
    global JSON_MODE

    parser = argparse.ArgumentParser(
        description="🎵 Song Recognition Engine: Identify songs from a specific YouTube Short, a channel's top N popular Shorts, or a local video file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  1. Identify a single YouTube Short or video directly:
     python main.py -s "https://www.youtube.com/shorts/v1vU5Gu4BFw"
     python main.py --short "https://www.youtube.com/shorts/v1vU5Gu4BFw"

  2. Open channel of a Short (or Channel URL) and analyze its top N popular Shorts:
     python main.py -c "https://www.youtube.com/shorts/v1vU5Gu4BFw" -n 5
     python main.py --channel "https://www.youtube.com/@EdSheeran" --top 10

  3. Identify song from a locally saved video file:
     python main.py -l "path/to/video.mp4"
     python main.py --local "videos/output/sample.mp4"
"""
    )

    # Dedicated Mode Flags
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-s", "--short",
        type=str,
        help="🚩 Flag 1: Single YouTube Short / Video link to recognize directly"
    )
    group.add_argument(
        "-c", "--channel",
        type=str,
        help="🚩 Flag 2: YouTube Short or Channel URL to open channel and inspect top N popular shorts"
    )
    group.add_argument(
        "-l", "--local",
        type=str,
        help="🚩 Flag 3: Path to a locally saved video file"
    )

    # Options
    parser.add_argument(
        "-n", "--top", "--count",
        dest="top_count",
        type=int,
        default=5,
        help="Number of most popular shorts to analyze with --channel (default: 5)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON progress and results for web studio integration"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Positional argument (auto-detects local file vs YouTube URL if no flag is specified)"
    )

    args = parser.parse_args()
    JSON_MODE = bool(args.json)
    temp_dir = tempfile.gettempdir()

    # Determine execution mode and target
    mode = None
    target_path = None

    if args.short:
        mode = "single_short"
        target_path = args.short.strip()
    elif args.channel:
        mode = "channel_top"
        target_path = args.channel.strip()
    elif args.local:
        mode = "local_video"
        target_path = args.local.strip()
    elif args.target:
        target_path = args.target.strip()
        is_yt = ("youtube.com" in target_path or "youtu.be" in target_path)
        if not is_yt and os.path.exists(target_path):
            mode = "local_video"
        elif is_yt and ("/shorts/" in target_path or "watch?v=" in target_path or "youtu.be" in target_path):
            mode = "channel_top"
        else:
            mode = "channel_top"
    else:
        parser.print_help()
        sys.exit(0)

    if not JSON_MODE:
        print("\n" + "=" * 70)
        print("  🎵 YOUTUBE SHORTS & VIDEO SONG RECOGNITION ENGINE")
        print("=" * 70 + "\n")

    # -------------------------------------------------------------
    # FLAG 1: Single YouTube Short / Video Recognition
    # -------------------------------------------------------------
    if mode == "single_short":
        if not JSON_MODE:
            print(f"🎬 [Flag 1 - Single Short] Analyzing: {target_path}...")
        emit_progress("start", 10, f"Analyzing single Short: {target_path}")

        def _short_prog(step, desc):
            pct = 30 if step == "audio_extraction" else (60 if step == "acrcloud_identifying" else 85)
            emit_progress(step, pct, desc)

        try:
            track_info = process_single_video(target_path, is_youtube=True, temp_dir=temp_dir, progress_cb=_short_prog)
        except Exception as e:
            if JSON_MODE:
                print(f"__RECOGNITION_ERROR__{json.dumps({'error': str(e)})}", flush=True)
            print(f"[Error] {e}", file=sys.stderr)
            sys.exit(1)

        emit_progress("completed", 100, "Single Short recognition completed!")
        emit_result({
            "status": "success",
            "mode": "single_short",
            "target": target_path,
            "track": track_info
        })

        if not JSON_MODE:
            print("\n" + "=" * 70)
            print("  🎵 SINGLE SHORT RECOGNITION RESULT")
            print("=" * 70)
            if track_info:
                print(f"  📌 Title:        {track_info['title']}")
                print(f"  🎤 Singer:       {track_info['singer']}")
                print(f"  ⏱️ Match Start:  {track_info['start_seconds']}s (offset: {track_info['play_offset_ms']} ms)")
                print(f"  ⏳ Reel Range:   {track_info['start_seconds']}s -> {track_info['end_seconds']}s ({track_info['short_duration']}s duration)")
                print(f"  🔗 Spotify:      {track_info.get('spotify_url') or 'No matching Spotify link found'}")
            else:
                print("  ❌ No recognizable music found in this short.")
            print("=" * 70 + "\n")
        return

    # -------------------------------------------------------------
    # FLAG 2: Channel Top N Popular Shorts Pipeline
    # -------------------------------------------------------------
    if mode == "channel_top":
        try:
            if not JSON_MODE:
                print(f"🚀 [Flag 2 - Channel Top {args.top_count}] Resolving channel from: {target_path}...")
            emit_progress("resolving_channel", 10, f"Resolving channel from: {target_path}")

            channel_data = get_channel_and_top_shorts(target_path, top_count=args.top_count)
            shorts = channel_data["shorts"]

            emit_progress("channel_resolved", 25, f"Found channel \"{channel_data['channel_name']}\" with top {len(shorts)} shorts.", {
                "channel_name": channel_data["channel_name"],
                "channel_url": channel_data["channel_url"],
                "total_shorts": len(shorts)
            })

            if not JSON_MODE:
                print(f"\n📺 Channel: \033[1m{channel_data['channel_name']}\033[0m ({channel_data['channel_url']})")
                print(f"🔥 Found top {len(shorts)} most popular shorts. Analyzing songs...\n")

            results = []
            for idx, item in enumerate(shorts):
                short_pct = int(25 + (idx / max(1, len(shorts))) * 70)
                emit_progress("processing_short", short_pct, f"Analyzing Short [{item['rank']}/{len(shorts)}]: \"{item['title'][:40]}\"...")

                if not JSON_MODE:
                    print(f"[{item['rank']}/{len(shorts)}] Analyzing Short: \"{item['title'][:45]}...\" ({format_views(item['views'])} views)")

                track_info = process_single_video(
                    item["url"],
                    is_youtube=True,
                    temp_dir=temp_dir,
                    known_duration=float(item.get("duration") or 0.0)
                )

                res_item = {
                    "short": item,
                    "track": track_info
                }
                results.append(res_item)
                emit_short_item(res_item)
                time.sleep(0.3)

            emit_progress("completed", 100, f"Completed recognizing {len(shorts)} shorts from {channel_data['channel_name']}!")
            emit_result({
                "status": "success",
                "mode": "channel_top",
                "channel_name": channel_data["channel_name"],
                "channel_url": channel_data["channel_url"],
                "results": results
            })

            if not JSON_MODE:
                # Print Final Detailed Summary Table
                print("\n" + "=" * 70)
                print(f"  📊 RECOGNITION RESULTS: {channel_data['channel_name']} (Top {len(shorts)} Popular Shorts)")
                print("=" * 70)

                for res in results:
                    short = res["short"]
                    track = res["track"]

                    print(f"\n#{short['rank']} 🎬 \"{short['title']}\"")
                    print(f"   👀 Views:      {format_views(short['views'])} views")
                    print(f"   🔗 Short:      {short['url']}")

                    if track:
                        print(f"   🎵 Song:       \033[1m{track['title']}\033[0m - \033[1m{track['singer']}\033[0m")
                        print(f"   ⏱️ Match:      {track['start_seconds']}s -> {track['end_seconds']}s ({track['short_duration']}s reel)")
                        print(f"   💚 Spotify:    {track.get('spotify_url') or 'Not found'}")
                    else:
                        print("   ❌ Song:       No recognizable music found")

                print("\n" + "=" * 70 + "\n")

        except Exception as err:
            if JSON_MODE:
                print(f"__RECOGNITION_ERROR__{json.dumps({'error': str(err)})}", flush=True)
            print(f"\n[Error] {err}", file=sys.stderr)
            sys.exit(1)
        return

    # -------------------------------------------------------------
    # FLAG 3: Local Saved Video File Recognition
    # -------------------------------------------------------------
    if mode == "local_video":
        if not os.path.exists(target_path):
            err_msg = f"The specified local video file does not exist: {target_path}"
            if JSON_MODE:
                print(f"__RECOGNITION_ERROR__{json.dumps({'error': err_msg})}", flush=True)
            print(f"[Error] {err_msg}", file=sys.stderr)
            sys.exit(1)

        if not JSON_MODE:
            print(f"💾 [Flag 3 - Local Video] Analyzing saved file: {target_path}...")
        emit_progress("start", 10, f"Analyzing local video: {os.path.basename(target_path)}")

        def _local_prog(step, desc):
            pct = 35 if step == "audio_extraction" else (65 if step == "acrcloud_identifying" else 85)
            emit_progress(step, pct, desc)

        try:
            track_info = process_single_video(target_path, is_youtube=False, temp_dir=temp_dir, progress_cb=_local_prog)
        except Exception as e:
            if JSON_MODE:
                print(f"__RECOGNITION_ERROR__{json.dumps({'error': str(e)})}", flush=True)
            print(f"[Error] {e}", file=sys.stderr)
            sys.exit(1)

        emit_progress("completed", 100, "Local video recognition completed!")
        emit_result({
            "status": "success",
            "mode": "local_video",
            "target": target_path,
            "filename": os.path.basename(target_path),
            "track": track_info
        })

        if not JSON_MODE:
            print("\n" + "=" * 70)
            print("  🎵 LOCAL VIDEO RECOGNITION RESULT")
            print("=" * 70)
            if track_info:
                print(f"  📌 Title:        {track_info['title']}")
                print(f"  🎤 Singer:       {track_info['singer']}")
                print(f"  ⏱️ Match Start:  {track_info['start_seconds']}s (offset: {track_info['play_offset_ms']} ms)")
                print(f"  ⏳ Reel Range:   {track_info['start_seconds']}s -> {track_info['end_seconds']}s ({track_info['short_duration']}s duration)")
                print(f"  🔗 Spotify:      {track_info.get('spotify_url') or 'No matching Spotify link found'}")
            else:
                print("  ❌ No recognizable music found in this video.")
            print("=" * 70 + "\n")
        return


if __name__ == "__main__":
    main()
