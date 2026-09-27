from typing import List, Optional
from pydantic import BaseModel, Field


class TextPostRequest(BaseModel):
    username: str = Field(..., description="Threads username to publish from")
    text: str = Field(..., description="Post content text (caption)")
    url: Optional[str] = Field(None, description="Optional link to attach preview for")


class MediaPostRequest(BaseModel):
    username: str = Field(..., description="Threads username to publish from")
    caption: str = Field("", description="Post caption text")
    media_paths: List[str] = Field(
        ...,
        min_length=1,
        description="List of image local file paths or HTTP/HTTPS URLs (1 for single photo, 2+ for carousel album)"
    )


class ReplyPostRequest(BaseModel):
    username: str = Field(..., description="Threads username to publish from")
    text: str = Field(..., description="Reply comment text")
    parent_post_id: str = Field(..., description="Target thread post ID to reply to")


class QuotePostRequest(BaseModel):
    username: str = Field(..., description="Threads username to publish from")
    text: str = Field(..., description="Quote comment text")
    quoted_post_id: str = Field(..., description="Target thread post ID to quote repost")


class LikePostRequest(BaseModel):
    username: str = Field(..., description="Threads username to perform the action")
    post_id: str = Field(..., description="Target thread post ID")


class PostResponse(BaseModel):
    success: bool
    media_id: Optional[str] = None
    code: Optional[str] = None
    url: Optional[str] = None
    message: Optional[str] = None
