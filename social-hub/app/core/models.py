from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PlatformType(str, Enum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    THREADS = "threads"
    YOUTUBE = "youtube"


class PostType(str, Enum):
    REEL = "reel"
    CAROUSEL = "carousel"
    POST = "post"
    STORY = "story"
    TEXT = "text"


class PostStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class ProfileBase(BaseModel):
    platform: PlatformType
    account_handle: str
    is_active: bool = True
    display_name: Optional[str] = None


class ProfileCreate(ProfileBase):
    pass


class Profile(ProfileBase):
    id: str
    brand_id: str
    created_at: str


class BrandBase(BaseModel):
    name: str
    color_badge: str = "#8ACE00"
    description: Optional[str] = None


class BrandCreate(BrandBase):
    pass


class Brand(BrandBase):
    id: str
    created_at: str
    profiles: List[Profile] = []


class ScheduledPostCreate(BaseModel):
    brand_id: str
    target_platforms: List[PlatformType]
    post_type: PostType = PostType.REEL
    media_paths: List[str] = []
    caption: str
    first_comment: Optional[str] = None
    scheduled_time: str  # ISO string e.g. "2026-09-20T18:00:00"
    music_query: Optional[str] = None
    audio_start_sec: Optional[float] = None
    share_to_facebook: bool = True
    share_to_threads: bool = False
    youtube_title: Optional[str] = None
    youtube_tags: Optional[List[str]] = None


class ScheduledPostUpdate(BaseModel):
    target_platforms: Optional[List[PlatformType]] = None
    post_type: Optional[PostType] = None
    media_paths: Optional[List[str]] = None
    caption: Optional[str] = None
    first_comment: Optional[str] = None
    scheduled_time: Optional[str] = None
    status: Optional[PostStatus] = None
    music_query: Optional[str] = None
    audio_start_sec: Optional[float] = None
    share_to_facebook: Optional[bool] = None
    share_to_threads: Optional[bool] = None


class ScheduledPost(BaseModel):
    id: str
    brand_id: str
    target_platforms: List[PlatformType]
    post_type: PostType
    media_paths: List[str]
    caption: str
    first_comment: Optional[str] = None
    scheduled_time: str
    status: PostStatus
    created_at: str
    music_query: Optional[str] = None
    audio_start_sec: Optional[float] = None
    share_to_facebook: bool = True
    share_to_threads: bool = False
    youtube_title: Optional[str] = None
    youtube_tags: Optional[List[str]] = None
    error_log: Optional[str] = None
    published_urls: Optional[Dict[str, Any]] = None

