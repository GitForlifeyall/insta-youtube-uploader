from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.core.models import ScheduledPost, ScheduledPostCreate, PostStatus
from app.core.database import (
    list_posts, get_post, create_post, delete_post, update_post_status
)
from app.core.dispatcher import dispatch_post

router = APIRouter(prefix="/api/posts", tags=["Scheduled Posts"])


@router.get("", response_model=List[ScheduledPost])
def get_posts(
    brand_id: Optional[str] = Query(None, description="Filter by brand ID"),
    status: Optional[str] = Query(None, description="Filter by status (scheduled, published, failed, etc.)")
):
    return list_posts(brand_id=brand_id, status=status)


@router.post("", response_model=ScheduledPost)
def schedule_post(post_data: ScheduledPostCreate):
    return create_post(post_data)


@router.get("/{post_id}", response_model=ScheduledPost)
def get_single_post(post_id: str):
    post = get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.delete("/{post_id}")
def remove_post(post_id: str):
    success = delete_post(post_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"status": "success", "message": f"Post {post_id} deleted"}


@router.post("/{post_id}/publish-now")
def publish_immediately(post_id: str):
    post = get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    update_post_status(post.id, PostStatus.PUBLISHING)
    success, error_msg, urls = dispatch_post(post)

    if success:
        update_post_status(post.id, PostStatus.PUBLISHED, published_urls=urls)
        return {"status": "success", "message": "Post published successfully", "urls": urls}
    else:
        update_post_status(post.id, PostStatus.FAILED, error_log=error_msg, published_urls=urls)
        raise HTTPException(status_code=500, detail=f"Failed to publish post: {error_msg}")


@router.post("/{post_id}/retry")
def retry_failed_post(post_id: str):
    post = get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Set scheduled_time to right now
    now_iso = datetime.now().isoformat()
    update_post_status(post.id, PostStatus.SCHEDULED, error_log=None)
    return {"status": "success", "message": "Post reset to scheduled queue"}
