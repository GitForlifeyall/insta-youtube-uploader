"""
Instagram Music Heatmap & Viral Hook Service
Provides music search, hook extraction from Instagram audio API,
and session validation.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from instagrapi import Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("instagram_service")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SESSION_FILE = ROOT_DIR / "ig_session.json"

class ViralHook(BaseModel):
    label: str = Field(..., description="e.g. 'Instagram Main Hook (Recommended)', 'Viral Hook 1'")
    start_ms: int
    end_ms: int
    start_seconds: float
    end_seconds: float
    start_formatted: str
    end_formatted: str
    ffmpeg_slice: str
    percentage_offset: float

class InstagramMusicService:
    def __init__(self, session_path: str = "ig_session.json"):
        self.session_path = Path(session_path)
        self.cl = Client()
        self.cl.delay_range = [1, 3]
        self._is_logged_in = False
        self._load_session()

    def _load_session(self) -> bool:
        """Loads session if saved; otherwise attempts login from env if available."""
        if self.session_path.exists():
            try:
                self.cl.load_settings(str(self.session_path))
                # Check if sessionid cookie exists or user_id is present
                auth_cookies = self.cl.get_settings().get("authorization_data", {})
                sessionid = auth_cookies.get("sessionid") or self.cl.settings.get("cookies", {}).get("sessionid")
                if self.cl.user_id or sessionid:
                    self._is_logged_in = True
                    logger.info("Loaded active Instagram session from file.")
                    return True
            except Exception as e:
                logger.warning(f"Failed to load session from {self.session_path}: {e}")

        # Fallback to .env credentials
        username = os.getenv("IG_USERNAME")
        password = os.getenv("IG_PASSWORD")
        if username and password:
            try:
                self.cl.login(username, password)
                self.cl.dump_settings(str(self.session_path))
                self._is_logged_in = True
                logger.info("Logged into Instagram via credentials and saved session.")
                return True
            except Exception as e:
                logger.error(f"Login failed with env credentials: {e}")

        self._is_logged_in = False
        return False

    def is_authenticated(self) -> bool:
        """Checks if there is an active logged-in session."""
        if not self._is_logged_in:
            return self._load_session()
        return True

    @staticmethod
    def ms_to_timestamp(ms: int) -> str:
        """Converts milliseconds to MM:SS format."""
        total_seconds = ms / 1000.0
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:04.1f}"

    @staticmethod
    def ms_to_ffmpeg_timestamp(ms: int) -> str:
        """Converts milliseconds to HH:MM:SS.mmm format for FFmpeg."""
        total_seconds = ms / 1000.0
        hours = int(total_seconds // 3600)
        remainder = total_seconds % 3600
        minutes = int(remainder // 60)
        seconds = remainder % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

    def search_music(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Searches Instagram's music catalog for tracks matching the query."""
        if not self.is_authenticated():
            raise RuntimeError("Instagram is not logged in. Please log in first.")

        results = []
        try:
            raw_response = self.cl.music_search_v2(query=query, product="story_camera_clips_v2")
            
            # music_search_v2 returns a Dict response e.g. {"items": [...]} or list of objects
            raw_items = []
            if isinstance(raw_response, dict):
                raw_items = raw_response.get("items", []) or raw_response.get("alacarte", {}).get("items", [])
            elif isinstance(raw_response, list):
                raw_items = raw_response
            
            for item in raw_items[:limit]:
                # Extract track object
                track = item
                if isinstance(item, dict):
                    track = item.get("track", item.get("audio_asset", item))
                else:
                    track = getattr(item, 'track', item)

                if isinstance(track, dict):
                    track_id = str(track.get("id") or track.get("audio_cluster_id") or "")
                    title = track.get("title") or "Unknown"
                    artist = track.get("display_artist") or track.get("artist_name") or "Unknown"
                    duration_ms = track.get("duration_in_ms") or 0
                    cover_url = track.get("cover_artwork_thumbnail_uri") or track.get("cover_artwork_uri") or ""
                    default_start = track.get("audio_asset_start_time_in_ms") or 0
                    highlights = track.get("highlight_start_times_in_ms") or []
                else:
                    track_id = str(getattr(track, 'id', getattr(track, 'audio_cluster_id', '')))
                    title = getattr(track, 'title', 'Unknown')
                    artist = getattr(track, 'display_artist', getattr(track, 'artist_name', 'Unknown'))
                    duration_ms = getattr(track, 'duration_in_ms', 0)
                    cover_url = getattr(track, 'cover_artwork_thumbnail_uri', getattr(track, 'cover_artwork_uri', ''))
                    default_start = getattr(track, 'audio_asset_start_time_in_ms', 0) or 0
                    highlights = getattr(track, 'highlight_start_times_in_ms', []) or []

                if isinstance(highlights, str):
                    highlights = [int(h) for h in highlights.split(",") if h.strip()]

                results.append({
                    "id": track_id,
                    "title": title,
                    "artist": artist,
                    "album_art_url": cover_url,
                    "duration_in_ms": duration_ms,
                    "audio_asset_start_time_in_ms": default_start,
                    "highlight_start_times_in_ms": highlights
                })
        except Exception as e:
            logger.error(f"Error during Instagram music search: {e}")
            raise e

        return results

    def build_heatpoints_response(self, track_data: Dict[str, Any], clip_length_seconds: int = 15) -> Dict[str, Any]:
        """Calculates precise hook windows and FFmpeg commands."""
        duration_ms = track_data.get("duration_in_ms", 180000)
        clip_ms = clip_length_seconds * 1000
        default_start_ms = track_data.get("audio_asset_start_time_in_ms", 0) or 0
        highlights = track_data.get("highlight_start_times_in_ms", []) or []

        all_starts = []
        if default_start_ms > 0:
            all_starts.append(default_start_ms)
        all_starts.extend(highlights)
        all_starts = sorted(list(set(all_starts)))

        hooks = []
        for idx, start_ms in enumerate(all_starts):
            end_ms = min(start_ms + clip_ms, duration_ms) if duration_ms > 0 else (start_ms + clip_ms)
            start_fmt = self.ms_to_timestamp(start_ms)
            end_fmt = self.ms_to_timestamp(end_ms)
            ffmpeg_start = self.ms_to_ffmpeg_timestamp(start_ms)
            ffmpeg_end = self.ms_to_ffmpeg_timestamp(end_ms)

            percentage = round((start_ms / duration_ms) * 100, 2) if duration_ms > 0 else 0.0
            is_default = (start_ms == default_start_ms)

            hooks.append({
                "label": "⭐ Instagram Main Hook (Recommended)" if is_default else f"🔥 Viral Hook {idx + 1}",
                "start_ms": start_ms,
                "end_ms": end_ms,
                "start_seconds": round(start_ms / 1000.0, 2),
                "end_seconds": round(end_ms / 1000.0, 2),
                "start_formatted": start_fmt,
                "end_formatted": end_fmt,
                "ffmpeg_slice": f"-ss {ffmpeg_start} -to {ffmpeg_end}",
                "percentage_offset": percentage,
                "is_recommended": is_default
            })

        default_hook = next((h for h in hooks if h["is_recommended"]), hooks[0] if hooks else None)

        return {
            "track_id": track_data.get("id"),
            "title": track_data.get("title"),
            "artist": track_data.get("artist"),
            "album_art_url": track_data.get("album_art_url"),
            "duration_in_ms": duration_ms,
            "duration_seconds": round(duration_ms / 1000.0, 2),
            "duration_formatted": self.ms_to_timestamp(duration_ms),
            "default_hook": default_hook,
            "all_hooks": hooks,
            "highlight_points_ms": highlights
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing command argument. Usage: python instagram_service.py [status|search <query>]"}))
        sys.exit(1)

    cmd = sys.argv[1].lower()
    service = InstagramMusicService()

    if cmd == "status":
        is_auth = service.is_authenticated()
        print(json.dumps({"logged_in": is_auth, "user_id": service.cl.user_id if is_auth else None}))
        sys.exit(0)

    elif cmd == "search":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing query argument"}))
            sys.exit(1)

        query = sys.argv[2]
        clip_len = int(sys.argv[3]) if len(sys.argv) > 3 else 15

        if not service.is_authenticated():
            print(json.dumps({"error": "NOT_LOGGED_IN", "message": "Instagram is not logged in. Please log in first."}))
            sys.exit(2)

        try:
            tracks = service.search_music(query, limit=5)
            if not tracks:
                print(json.dumps({"error": "NO_TRACKS", "message": f"No tracks found on Instagram for '{query}'"}))
                sys.exit(0)

            # Build response using top matched track
            top_track = tracks[0]
            response = service.build_heatpoints_response(top_track, clip_length_seconds=clip_len)
            response["candidates"] = tracks
            print(json.dumps(response))
            sys.exit(0)
        except Exception as err:
            print(json.dumps({"error": str(err)}))
            sys.exit(1)
    else:
        print(json.dumps({"error": f"Unknown command '{cmd}'"}))
        sys.exit(1)
