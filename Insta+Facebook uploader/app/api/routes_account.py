from fastapi import APIRouter, HTTPException
from app.schemas.account import LoginRequest, AccountStatusResponse, AccountProfileResponse
from app.core.client_manager import client_manager

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.post("/login", response_model=AccountStatusResponse)
def login(req: LoginRequest):
    try:
        cl = client_manager.login_account(
            username=req.username,
            password=req.password,
            session_id=req.session_id,
            verification_code=req.verification_code
        )
        return AccountStatusResponse(
            username=req.username,
            is_authenticated=True,
            user_id=str(cl.user_id)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{username}/status", response_model=AccountStatusResponse)
def account_status(username: str):
    try:
        cl = client_manager.get_client(username)
        info = cl.account_info()
        return AccountStatusResponse(
            username=username,
            is_authenticated=True,
            user_id=str(info.pk)
        )
    except Exception as e:
        return AccountStatusResponse(
            username=username,
            is_authenticated=False,
            user_id=None
        )

@router.get("/{username}/profile", response_model=AccountProfileResponse)
def account_profile(username: str):
    try:
        cl = client_manager.get_client(username)
        acc = cl.account_info()
        follower_count = 0
        following_count = 0
        media_count = 0
        is_verified = False
        try:
            u_info = cl.user_info(acc.pk)
            follower_count = getattr(u_info, "follower_count", 0) or 0
            following_count = getattr(u_info, "following_count", 0) or 0
            media_count = getattr(u_info, "media_count", 0) or 0
            is_verified = bool(getattr(u_info, "is_verified", False))
        except Exception:
            pass

        return AccountProfileResponse(
            username=username,
            is_authenticated=True,
            user_id=str(acc.pk),
            full_name=acc.full_name or username,
            biography=acc.biography or "",
            profile_pic_url=str(acc.profile_pic_url) if getattr(acc, "profile_pic_url", None) else None,
            follower_count=follower_count,
            following_count=following_count,
            media_count=media_count,
            is_verified=is_verified
        )
    except Exception as e:
        return AccountProfileResponse(
            username=username,
            is_authenticated=False,
            user_id=None,
            biography=f"Account offline or session expired: {str(e)}"
        )

@router.get("/{username}/medias")
def account_medias(username: str, amount: int = 12):
    try:
        cl = client_manager.get_client(username)
        acc = cl.account_info()
        medias = cl.user_medias(acc.pk, amount=amount)
        results = []
        for m in medias:
            results.append({
                "id": str(m.pk),
                "code": getattr(m, "code", ""),
                "caption": getattr(m, "caption_text", "") or "",
                "media_type": getattr(m, "media_type", 1),
                "thumbnail_url": str(m.thumbnail_url) if getattr(m, "thumbnail_url", None) else None,
                "video_url": str(m.video_url) if getattr(m, "video_url", None) else None,
                "view_count": getattr(m, "view_count", 0) or 0,
                "like_count": getattr(m, "like_count", 0) or 0,
                "taken_at": m.taken_at.isoformat() if getattr(m, "taken_at", None) else None
            })
        return results
    except Exception as e:
        return []

