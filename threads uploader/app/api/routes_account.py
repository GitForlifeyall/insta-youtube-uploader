from fastapi import APIRouter, HTTPException
from app.schemas.account import (
    LoginRequest,
    AccountStatusResponse,
    UserProfileResponse
)
from app.core.client_manager import client_manager

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("/login", response_model=AccountStatusResponse)
async def login(req: LoginRequest):
    """
    Authenticates a Threads/Instagram account and caches an encrypted session token.
    Subsequent requests reuse this token to avoid triggering security challenges.
    """
    try:
        api = await client_manager.login_account(
            username=req.username,
            password=req.password
        )
        return AccountStatusResponse(
            username=req.username,
            is_authenticated=True,
            user_id=str(getattr(api, "user_id", None)),
            message="Successfully authenticated and saved session token."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{username}/status", response_model=AccountStatusResponse)
async def account_status(username: str):
    """
    Checks whether an account has a valid, active session available.
    """
    try:
        api = await client_manager.get_client(username)
        return AccountStatusResponse(
            username=username,
            is_authenticated=getattr(api, "is_logged_in", False),
            user_id=str(getattr(api, "user_id", None)),
            message="Active session found."
        )
    except Exception as e:
        return AccountStatusResponse(
            username=username,
            is_authenticated=False,
            user_id=None,
            message=str(e)
        )


@router.get("/{username}/profile", response_model=UserProfileResponse)
async def get_profile(username: str):
    """
    Retrieves public profile details for a given Threads user.
    """
    try:
        # Client can be any authenticated client or public session
        try:
            api = await client_manager.get_client(username)
        except Exception:
            # Fall back to any active client in the pool
            if client_manager.clients:
                api = next(iter(client_manager.clients.values()))
            else:
                from threads_api.src.threads_api import ThreadsAPI
                api = ThreadsAPI()

        user_id = await api.get_user_id_from_username(username)
        if not user_id:
            raise HTTPException(status_code=404, detail=f"User '{username}' not found on Threads.")

        user_info = await api.get_user_profile(user_id)
        return UserProfileResponse(
            username=username,
            user_id=str(user_id),
            full_name=getattr(user_info, "full_name", None),
            biography=getattr(user_info, "biography", None),
            follower_count=getattr(user_info, "follower_count", 0),
            following_count=getattr(user_info, "following_count", 0),
            is_verified=bool(getattr(user_info, "is_verified", False)),
            profile_pic_url=getattr(user_info, "profile_pic_url", None)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")


@router.post("/{username}/logout")
async def logout(username: str):
    """
    Closes client sessions and removes client from memory cache.
    """
    logged_out = await client_manager.logout_account(username)
    return {"success": logged_out, "message": f"Account '{username}' logged out."}
