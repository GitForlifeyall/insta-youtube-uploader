from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class PlatformType(str, Enum):
    INSTAGRAM = "instagram"


class PostType(str, Enum):
    REEL = "reel"
    CAROUSEL = "carousel"
    POST = "post"
    STORY = "story"


class PostStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class ProfileBase(BaseModel):
    platform: PlatformType = PlatformType.INSTAGRAM
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
    target_platforms: List[PlatformType] = [PlatformType.INSTAGRAM]
    post_type: PostType = PostType.REEL
    media_paths: List[str] = []
    caption: str = ""
    first_comment: Optional[str] = None
    scheduled_time: str  # ISO string e.g. "2026-10-15T18:00:00"
    music_query: Optional[str] = None
    audio_cluster_id: Optional[str] = None
    audio_start_sec: Optional[float] = 0.0
    music_volume: float = 10.0
    status: PostStatus = PostStatus.SCHEDULED


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
    music_volume: Optional[float] = None


class ScheduledPost(BaseModel):
    id: str
    brand_id: str
    target_platforms: List[PlatformType] = [PlatformType.INSTAGRAM]
    post_type: PostType
    media_paths: List[str]
    caption: str
    first_comment: Optional[str] = None
    scheduled_time: str
    status: PostStatus
    created_at: str
    music_query: Optional[str] = None
    audio_cluster_id: Optional[str] = None
    audio_start_sec: Optional[float] = None
    music_volume: Optional[float] = 10.0
    error_log: Optional[str] = None
    published_urls: Optional[Dict[str, Any]] = None


class EvergreenPost(BaseModel):
    id: str
    brand_id: str
    caption: str
    media_paths: List[str]
    target_platforms: List[PlatformType] = [PlatformType.INSTAGRAM]
    max_repeats: int = 3
    times_posted: int = 0
    last_posted_at: Optional[str] = None
    is_active: bool = True
    created_at: str
