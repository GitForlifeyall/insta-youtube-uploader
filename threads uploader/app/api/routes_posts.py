from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException

from app.schemas.post import (
    TextPostRequest,
    MediaPostRequest,
    ReplyPostRequest,
    QuotePostRequest,
    LikePostRequest,
    PostResponse
)
from app.core.client_manager import client_manager

router = APIRouter(prefix="/posts", tags=["Posts & Interaction"])


def _extract_post_details(res) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Helper to extract media_id, code, and threads web URL from post response."""
    media = getattr(res, "media", None)
    if not media:
        return None, None, None

    media_id = str(getattr(media, "pk", "") or getattr(media, "id", ""))
    code = getattr(media, "code", None)
    url = f"https://www.threads.net/t/{code}" if code else None
    return media_id, code, url


@router.post("/text", response_model=PostResponse)
async def create_text_post(req: TextPostRequest):
    """
    Publishes a text-only thread post, with an optional link preview attachment.
    """
    try:
        api = await client_manager.get_client(req.username)
        res = await api.post(
            caption=req.text,
            url=req.url
        )

        media_id, code, post_url = _extract_post_details(res)
        return PostResponse(
            success=True,
            media_id=media_id,
            code=code,
            url=post_url,
            message="Text thread published successfully."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish text post: {str(e)}")


@router.post("/media", response_model=PostResponse)
async def create_media_post(req: MediaPostRequest):
    """
    Publishes an image post (single image) or carousel album (2+ images).
    Paths can be local absolute paths on the server or public HTTP/HTTPS URLs.
    """
    try:
        api = await client_manager.get_client(req.username)

        # Validate local files exist if they are not remote URLs
        for path_str in req.media_paths:
            if not path_str.startswith("http://") and not path_str.startswith("https://"):
                local_path = Path(path_str)
                if not local_path.exists():
                    raise HTTPException(
                        status_code=404,
                        detail=f"Local media file not found: {path_str}"
                    )

        # threads-api expects a single string for 1 image, or a list of 2+ strings for carousel
        if len(req.media_paths) == 1:
            image_arg = req.media_paths[0]
        else:
            image_arg = req.media_paths

        res = await api.post(
            caption=req.caption,
            image_path=image_arg
        )

        media_id, code, post_url = _extract_post_details(res)
        return PostResponse(
            success=True,
            media_id=media_id,
            code=code,
            url=post_url,
            message=f"Media post ({len(req.media_paths)} item(s)) published successfully."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish media post: {str(e)}")


@router.post("/reply", response_model=PostResponse)
async def create_reply_post(req: ReplyPostRequest):
    """
    Publishes a reply to an existing Thread.
    """
    try:
        api = await client_manager.get_client(req.username)
        res = await api.post(
            caption=req.text,
            parent_post_id=req.parent_post_id
        )

        media_id, code, post_url = _extract_post_details(res)
        return PostResponse(
            success=True,
            media_id=media_id,
            code=code,
            url=post_url,
            message="Reply published successfully."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reply to post: {str(e)}")


@router.post("/quote", response_model=PostResponse)
async def create_quote_post(req: QuotePostRequest):
    """
    Publishes a quote-repost of an existing Thread with commentary.
    """
    try:
        api = await client_manager.get_client(req.username)
        res = await api.post(
            caption=req.text,
            quoted_post_id=req.quoted_post_id
        )

        media_id, code, post_url = _extract_post_details(res)
        return PostResponse(
            success=True,
            media_id=media_id,
            code=code,
            url=post_url,
            message="Quote thread published successfully."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to quote post: {str(e)}")


@router.post("/like")
async def like_post(req: LikePostRequest):
    """
    Likes a Thread post by ID.
    """
    try:
        api = await client_manager.get_client(req.username)
        success = await api.like_post(req.post_id)
        return {"success": success, "post_id": req.post_id, "action": "like"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to like post: {str(e)}")


@router.delete("/{username}/{post_id}")
async def delete_post(username: str, post_id: str):
    """
    Deletes a Thread post published by the account.
    """
    try:
        api = await client_manager.get_client(username)
        success = await api.delete_post(post_id)
        return {"success": success, "deleted_post_id": post_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete post: {str(e)}")
