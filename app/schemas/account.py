from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    session_id: Optional[str] = None
    verification_code: Optional[str] = None
    totp_secret: Optional[str] = None
    raw_account_string: Optional[str] = None
    proxy: Optional[str] = None

class BrowserLoginRequest(BaseModel):
    proxy: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

class AccountStatusResponse(BaseModel):
    username: str
    is_authenticated: bool
    user_id: Optional[str] = None
    proxy: Optional[str] = None

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
    proxy: Optional[str] = None

class ProxyUpdateRequest(BaseModel):
    proxy: Optional[str] = None

class ProxyResponse(BaseModel):
    username: str
    proxy: Optional[str] = None
    has_proxy: bool = False
    message: str = "Success"