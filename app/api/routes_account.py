from typing import List
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from app.config import STATIC_DIR
from app.schemas.account import (
    LoginRequest,
    BrowserLoginRequest,
    AccountStatusResponse,
    AccountProfileResponse,
    ProxyUpdateRequest,
    ProxyResponse
)
from app.core.client_manager import client_manager
from app.core.browser_login import browser_login_manager
from app.core import database

router = APIRouter(prefix="/accounts", tags=["Accounts"])


def get_account_profile_summary(username: str) -> AccountProfileResponse:
    proxy = client_manager.get_proxy(username)
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

        full_name = acc.full_name or username
        pic_url = str(acc.profile_pic_url) if getattr(acc, "profile_pic_url", None) else None

        # Update cached profile info in SQLite database
        try:
            database.save_account_profile(
                username=username,
                user_id=str(acc.pk),
                full_name=full_name,
                profile_pic_url=pic_url
            )
        except Exception:
            pass

        return AccountProfileResponse(
            username=username,
            is_authenticated=True,
            user_id=str(acc.pk),
            full_name=full_name,
            biography=acc.biography or "",
            profile_pic_url=pic_url,
            follower_count=follower_count,
            following_count=following_count,
            media_count=media_count,
            is_verified=is_verified,
            proxy=proxy
        )
    except Exception as e:
        return AccountProfileResponse(
            username=username,
            is_authenticated=False,
            user_id=None,
            full_name=username,
            biography=f"Session expired or offline: {str(e)}",
            proxy=proxy
        )


@router.get("", response_model=List[AccountProfileResponse])
@router.get("/", response_model=List[AccountProfileResponse])
def list_accounts(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
    usernames = client_manager.list_saved_accounts()
    profiles = []
    for u in usernames:
        profiles.append(get_account_profile_summary(u))
    return profiles


@router.get("/database")
def get_database_accounts():
    """Retrieves all accounts, credentials, and attached proxies stored in SQLite database."""
    return database.get_all_db_accounts()


@router.delete("/{username}")
def delete_account(username: str):
    success = client_manager.delete_session(username)
    if not success:
        raise HTTPException(status_code=404, detail=f"Account session for '{username}' not found.")
    return {"success": True, "message": f"Account '{username}' session removed."}


@router.get("/{username}/proxy", response_model=ProxyResponse)
def get_account_proxy(username: str):
    proxy = client_manager.get_proxy(username)
    return ProxyResponse(
        username=username,
        proxy=proxy,
        has_proxy=bool(proxy),
        message=f"Proxy configured for @{username}" if proxy else f"No proxy configured for @{username}"
    )


@router.post("/{username}/proxy", response_model=ProxyResponse)
def set_account_proxy(username: str, req: ProxyUpdateRequest):
    saved_proxy = client_manager.set_proxy(username, req.proxy)
    return ProxyResponse(
        username=username,
        proxy=saved_proxy,
        has_proxy=bool(saved_proxy),
        message=f"Proxy updated for @{username}" if saved_proxy else f"Proxy removed for @{username}"
    )


@router.post("/login", response_model=AccountStatusResponse)
def login(req: LoginRequest):
    from app.core import totp
    username = req.username
    password = req.password
    totp_secret = req.totp_secret

    if req.raw_account_string:
        parsed_u, parsed_p, parsed_2fa = totp.parse_purchased_account_string(req.raw_account_string)
        if parsed_u:
            username = parsed_u
        if parsed_p:
            password = parsed_p
        if parsed_2fa:
            totp_secret = parsed_2fa

    if not username:
        raise HTTPException(status_code=400, detail="Username is required or could not be parsed from account string.")

    try:
        cl = client_manager.login_account(
            username=username,
            password=password,
            session_id=req.session_id,
            verification_code=req.verification_code,
            totp_secret=totp_secret,
            proxy=req.proxy
        )
        return AccountStatusResponse(
            username=username,
            is_authenticated=True,
            user_id=str(cl.user_id),
            proxy=client_manager.get_proxy(username)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/totp-code")
def get_totp_code_endpoint(secret: str):
    import time
    from app.core import totp
    try:
        code = totp.generate_totp_code(secret)
        remaining = 30 - int(time.time() % 30)
        return {"code": code, "seconds_remaining": remaining}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/browser-login/start")
def start_browser_login(req: BrowserLoginRequest):
    """
    Launches a real Chromium browser window (Brave, Chrome, or Edge) routed through
    the specified proxy, navigating to Instagram's login page.
    """
    try:
        res = browser_login_manager.start_login(
            proxy=req.proxy,
            username=req.username,
            password=req.password
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/browser-login/status")
def browser_login_status():
    """Returns the current status of the active browser login session."""
    return browser_login_manager.get_status()


@router.post("/browser-login/extract")
def extract_browser_login():
    """
    Called when the user clicks 'I Have Logged In'.
    Extracts the sessionid cookie, registers the account with instagrapi,
    saves the session to disk and SQLite, and closes the browser window.
    """
    res = browser_login_manager.force_extract()
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("detail", "Extraction failed"))
    return res


@router.post("/browser-login/stop")
def stop_browser_login():
    """Terminates any active browser login session."""
    browser_login_manager.stop_login()
    return {"success": True, "message": "Browser login stopped."}


@router.post("/{username}/open-browser")
def open_account_in_browser(username: str):
    """
    Opens a visible Chromium browser (Brave, Chrome, or Edge) routed through
    the account's assigned proxy, with session cookies injected so the account
    is already logged in.
    """
    try:
        return browser_login_manager.open_account_browser(username)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{username}/status", response_model=AccountStatusResponse)
def account_status(username: str):
    proxy = client_manager.get_proxy(username)
    try:
        cl = client_manager.get_client(username)
        info = cl.account_info()
        return AccountStatusResponse(
            username=username,
            is_authenticated=True,
            user_id=str(info.pk),
            proxy=proxy
        )
    except Exception as e:
        return AccountStatusResponse(
            username=username,
            is_authenticated=False,
            user_id=None,
            proxy=proxy
        )


@router.get("/{username}/profile", response_model=AccountProfileResponse)
def account_profile(username: str):
    return get_account_profile_summary(username)


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
