import requests
import logging
from typing import Dict, Any, Tuple
from app.config import INSTA_FB_API_URL, THREADS_API_URL, YOUTUBE_API_URL
from app.core.models import ScheduledPost, PlatformType, PostType
from app.core.database import list_brands

logger = logging.getLogger("dispatcher")


def get_profile_handle_for_brand(brand_id: str, platform: PlatformType) -> str:
    """Finds the active account handle for a brand on a specific platform."""
    brands = list_brands()
    for b in brands:
        if b.id == brand_id:
            for p in b.profiles:
                if p.platform == platform and p.is_active:
                    return p.account_handle
    return ""


def dispatch_post(post: ScheduledPost) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Executes cross-platform publishing by calling the appropriate microservices.
    Returns: (success: bool, message/error: str, published_urls: dict)
    """
    published_urls = {}
    errors = []

    for platform in post.target_platforms:
        handle = get_profile_handle_for_brand(post.brand_id, platform)
        if not handle:
            errors.append(f"No active profile found for brand on {platform.value}.")
            continue

        try:
            if platform == PlatformType.INSTAGRAM or platform == PlatformType.FACEBOOK:
                # Dispatch to Insta+Facebook uploader on port 8001
                if post.post_type == PostType.REEL or (post.media_paths and post.media_paths[0].lower().endswith(('.mp4', '.mov'))):
                    video_path = post.media_paths[0] if post.media_paths else ""
                    payload = {
                        "username": handle,
                        "video_path": video_path,
                        "caption": post.caption,
                        "music_query": post.music_query,
                        "audio_start_time_sec": getattr(post, "audio_start_sec", None),
                        "share_to_facebook": post.share_to_facebook,
                        "share_to_threads": post.share_to_threads
                    }
                    resp = requests.post(f"{INSTA_FB_API_URL}/upload/reel", json=payload, timeout=120)
                    if resp.status_code == 200:
                        data = resp.json()
                        published_urls["instagram"] = data.get("media_url") or data.get("media_pk") or "Uploaded"
                        if post.share_to_facebook:
                            published_urls["facebook"] = "Shared via Instagram"
                    else:
                        errors.append(f"Instagram/FB upload failed ({resp.status_code}): {resp.text[:300]}")

                elif post.post_type == PostType.POST or (post.media_paths and any(post.media_paths[0].lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.webp'))):
                    payload = {
                        "username": handle,
                        "media_paths": post.media_paths,
                        "caption": post.caption,
                        "share_to_facebook": post.share_to_facebook,
                        "share_to_threads": post.share_to_threads
                    }
                    resp = requests.post(f"{INSTA_FB_API_URL}/upload/post", json=payload, timeout=120)
                    if resp.status_code == 200:
                        data = resp.json()
                        published_urls["instagram"] = data.get("media_url") or data.get("media_pk") or "Uploaded"
                        if post.share_to_facebook:
                            published_urls["facebook"] = "Shared via Instagram"
                    else:
                        errors.append(f"Instagram photo post failed ({resp.status_code}): {resp.text[:300]}")

                elif post.post_type == PostType.CAROUSEL:
                    payload = {
                        "username": handle,
                        "media_paths": post.media_paths,
                        "caption": post.caption
                    }
                    resp = requests.post(f"{INSTA_FB_API_URL}/upload/carousel", json=payload, timeout=120)
                    if resp.status_code == 200:
                        data = resp.json()
                        published_urls["instagram"] = data.get("media_url") or data.get("media_pk") or "Uploaded"
                    else:
                        errors.append(f"Instagram carousel failed ({resp.status_code}): {resp.text[:300]}")

            elif platform == PlatformType.THREADS:
                # Dispatch to Threads uploader on port 8002
                if post.media_paths:
                    payload = {
                        "username": handle,
                        "image_paths": post.media_paths,
                        "text": post.caption
                    }
                    resp = requests.post(f"{THREADS_API_URL}/posts/photos", json=payload, timeout=120)
                else:
                    payload = {
                        "username": handle,
                        "text": post.caption
                    }
                    resp = requests.post(f"{THREADS_API_URL}/posts/text", json=payload, timeout=60)

                if resp.status_code == 200:
                    data = resp.json()
                    published_urls["threads"] = data.get("post_url") or data.get("id") or "Uploaded"
                else:
                    errors.append(f"Threads post failed ({resp.status_code}): {resp.text[:300]}")

            elif platform == PlatformType.YOUTUBE:
                # Dispatch to YouTube Shorts uploader on port 8003 (ReDroid + ADB)
                if post.media_paths:
                    video_path = post.media_paths[0]
                    payload = {
                        "video_path": video_path,
                        "title": post.youtube_title or post.caption[:100],
                        "description": post.caption,
                        "tags": post.youtube_tags or [],
                        "visibility": "public",
                        "brand_handle": handle or None,
                    }
                    resp = requests.post(f"{YOUTUBE_API_URL}/upload/short", json=payload, timeout=360)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("success"):
                            published_urls["youtube"] = data.get("video_url") or "Uploaded"
                        else:
                            errors.append(f"YouTube upload failed: {data.get('error_message', 'Unknown error')}")
                    else:
                        errors.append(f"YouTube upload failed ({resp.status_code}): {resp.text[:300]}")
                else:
                    errors.append("YouTube upload requires a video file.")

        except Exception as e:
            errors.append(f"Network error communicating with {platform.value} service: {str(e)}")

    success = len(errors) == 0 and len(published_urls) > 0
    err_msg = "; ".join(errors) if errors else ""
    return success, err_msg, published_urls
