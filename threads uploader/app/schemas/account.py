from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., description="Threads / Instagram username")
    password: str = Field(..., description="Threads / Instagram password")


class AccountStatusResponse(BaseModel):
    username: str
    is_authenticated: bool
    user_id: Optional[str] = None
    message: Optional[str] = None


class UserProfileResponse(BaseModel):
    username: str
    user_id: Optional[str] = None
    full_name: Optional[str] = None
    biography: Optional[str] = None
    follower_count: Optional[int] = 0
    following_count: Optional[int] = 0
    is_verified: Optional[bool] = False
    profile_pic_url: Optional[str] = None
