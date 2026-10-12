"""
🚀 Publishing Dispatcher Engine
Dispatches scheduled posts directly through the local Instagram publishing pipeline.
Handles Reels with music offset and volume scaling, Feed photo posts, Stories, and auto-first comments.
"""

import logging
from typing import Dict, Any, Tuple
from pathlib import Path

from app.core.models import ScheduledPost, PostType, PlatformType
from app.core.database import list_brands, get_brand
from app.core.client_manager import client_manager
from app.schemas.media import ReelUploadRequest, PostUploadRequest, StoryUploadRequest
from app.api.routes_media import upload_reel, upload_post, upload_story

logger = logging.getLogger("dispatcher")


def get_profile_handle_for_brand(brand_id: str) -> str:
    """Finds the active Instagram account handle for a brand."""
    brand = get_brand(brand_id)
    if brand:
        for p in brand.profiles:
            if p.platform == PlatformType.INSTAGRAM and p.is_active:
                return p.account_handle

    # Fallback to any account in client_manager if not explicitly linked
    accs = client_manager.get_active_accounts()
    if accs:
        return accs[0]["username"]
    return ""


def dispatch_post(post: ScheduledPost) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Executes Instagram publishing directly.
    Returns: (success: bool, message/error: str, published_urls: dict)
    """
    handle = get_profile_handle_for_brand(post.brand_id)
    if not handle:
        return False, f"No active Instagram account profile found for brand: {post.brand_id}", {}

    published_urls = {}
    try:
        # 1. Reel Upload
        if post.post_type == PostType.REEL or (post.media_paths and any(post.media_paths[0].lower().endswith(ext) for ext in ('.mp4', '.mov', '.mkv', '.webm'))):
            video_path = post.media_paths[0] if post.media_paths else ""
            req = ReelUploadRequest(
                username=handle,
                video_path=video_path,
                caption=post.caption,
                music_query=post.music_query,
                audio_cluster_id=post.audio_cluster_id,
                audio_start_time_sec=post.audio_start_sec,
                music_volume=post.music_volume if post.music_volume is not None else 10.0,
                share_to_facebook=False,
                share_to_threads=False
            )
            res = upload_reel(req)
            post_url = res.url
            media_pk = res.media_id
            published_urls["instagram"] = post_url

            # Post first comment if requested
            if post.first_comment and media_pk:
                try:
                    cl = client_manager.get_client(handle)
                    cl.media_comment(media_pk, post.first_comment)
                except Exception as c_err:
                    logger.warning(f"Failed to post first comment: {c_err}")

        # 2. Story Upload
        elif post.post_type == PostType.STORY:
            media_path = post.media_paths[0] if post.media_paths else ""
            req = StoryUploadRequest(
                username=handle,
                media_path=media_path,
                caption=post.caption or ""
            )
            res = upload_story(req)
            published_urls["instagram"] = res.url

        # 3. Photo Feed Post / Carousel
        else:
            req = PostUploadRequest(
                username=handle,
                media_paths=post.media_paths,
                caption=post.caption or "",
                share_to_facebook=False,
                share_to_threads=False
            )
            res = upload_post(req)
            post_url = res.url
            media_pk = res.media_id
            published_urls["instagram"] = post_url

            if post.first_comment and media_pk:
                try:
                    cl = client_manager.get_client(handle)
                    cl.media_comment(media_pk, post.first_comment)
                except Exception as c_err:
                    logger.warning(f"Failed to post first comment: {c_err}")

        return True, "Published successfully", published_urls

    except Exception as e:
        logger.error(f"Error publishing post {post.id}: {e}", exc_info=True)
        return False, str(e), published_urls
