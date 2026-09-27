import asyncio
import logging
from datetime import datetime
from app.core.database import get_due_posts, update_post_status
from app.core.models import PostStatus
from app.core.dispatcher import dispatch_post

logger = logging.getLogger("scheduler_worker")
_is_running = False


async def start_scheduler_loop(interval_seconds: int = 15):
    """Asynchronous background loop checking for due posts and publishing them."""
    global _is_running
    _is_running = True
    logger.info(f"🚀 Social Hub Scheduler Worker started (checking every {interval_seconds}s)")

    while _is_running:
        try:
            now_iso = datetime.now().isoformat()
            due_posts = get_due_posts(now_iso)

            for post in due_posts:
                logger.info(f"⏳ Processing scheduled post: {post.id} for brand: {post.brand_id}")
                update_post_status(post.id, PostStatus.PUBLISHING)

                # Dispatch in a thread pool so it does not block the async event loop
                success, error_msg, urls = await asyncio.to_thread(dispatch_post, post)

                if success:
                    logger.info(f"✅ Successfully published post {post.id} to: {list(urls.keys())}")
                    update_post_status(post.id, PostStatus.PUBLISHED, published_urls=urls)
                else:
                    logger.error(f"❌ Failed to publish post {post.id}: {error_msg}")
                    update_post_status(post.id, PostStatus.FAILED, error_log=error_msg, published_urls=urls)

        except Exception as e:
            logger.error(f"Scheduler worker error: {e}", exc_info=True)

        await asyncio.sleep(interval_seconds)


def stop_scheduler_loop():
    global _is_running
    _is_running = False
