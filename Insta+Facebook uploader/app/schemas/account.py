from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    username: str
    password: Optional[str] = None
    session_id: Optional[str] = None
    verification_code: Optional[str] = None 

class AccountStatusResponse(BaseModel):
    username: str
    is_authenticated: bool
    user_id: Optional[str] = None

class AccountProfileResponse(BaseModel):
    username: str
    is_authenticated: bool
    user_id: Optional[str] = None
    full_name: Optional[str] = None
    biography: Optional[str] = None
    profile_pic_url: Optional[str] = None
    follower_count: int = 0
    following_count: int = 0
    media_count: int = 0
    is_verified: bool = False