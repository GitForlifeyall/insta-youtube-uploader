"""
🔐 Connected Accounts & Real-Time Feed API Router
Provides multi-platform live verification and real-time profile/feed fetching.
"""

import logging
import requests
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Query

from app.config import INSTA_FB_API_URL, THREADS_API_URL
from app.core.database import list_brands
from app.core.competitor_spy import scrape_competitor_instagram

logger = logging.getLogger("RoutesAccounts")
router = APIRouter(tags=["Accounts & Feed"])

@router.get("/api/accounts/status")
def get_accounts_status():
    """
    Scans all registered brands and checks live session / verification status
    across Instagram (port 8001) and Threads (port 8002).
    """
    brands = list_brands()
    accounts_list: List[Dict[str, Any]] = []

    for brand in brands:
        for profile in brand.profiles:
            platform_str = profile.platform.value if hasattr(profile.platform, "value") else str(profile.platform)
            handle = profile.account_handle
            
            acc_data: Dict[str, Any] = {
                "id": profile.id,
                "brand_id": brand.id,
                "brand_name": brand.name,
                "brand_color": brand.color_badge,
                "platform": platform_str,
                "handle": handle,
                "display_name": profile.display_name or f"@{handle}",
                "is_authenticated": False,
                "status": "unverified",
                "status_label": "Checking...",
                "user_id": None,
                "avatar_url": None,
                "bio": None,
                "followers": 0,
                "following": 0,
                "posts_count": 0,
                "error_details": None,
            }

            if platform_str == "instagram":
                try:
                    res = requests.get(f"{INSTA_FB_API_URL}/accounts/{handle}/profile", timeout=4)
                    if res.status_code == 200:
                        data = res.json()
                        acc_data["is_authenticated"] = data.get("is_authenticated", False)
                        acc_data["user_id"] = data.get("user_id")
                        acc_data["avatar_url"] = data.get("profile_pic_url")
                        acc_data["bio"] = data.get("biography")
                        acc_data["followers"] = data.get("follower_count", 0)
                        acc_data["following"] = data.get("following_count", 0)
                        acc_data["posts_count"] = data.get("media_count", 0)
                        if acc_data["is_authenticated"]:
                            acc_data["status"] = "verified"
                            acc_data["status_label"] = "Verified Logged In"
                        else:
                            acc_data["status"] = "expired"
                            acc_data["status_label"] = "Session Expired"
                            acc_data["error_details"] = "Session expired. Update BRAND_IG_SESSION_ID in .env"
                    else:
                        acc_data["status"] = "error"
                        acc_data["status_label"] = f"HTTP {res.status_code}"
                except Exception as e:
                    acc_data["status"] = "offline"
                    acc_data["status_label"] = "Service Offline"
                    acc_data["error_details"] = f"Cannot reach Instagram uploader: {str(e)[:100]}"

            elif platform_str == "threads":
                try:
                    res = requests.get(f"{THREADS_API_URL}/accounts/{handle}/status", timeout=4)
                    if res.status_code == 200:
                        data = res.json()
                        acc_data["is_authenticated"] = data.get("is_authenticated", False)
                        acc_data["user_id"] = data.get("user_id")
                        if acc_data["is_authenticated"]:
                            acc_data["status"] = "verified"
                            acc_data["status_label"] = "Verified Logged In"
                        else:
                            acc_data["status"] = "disconnected"
                            acc_data["status_label"] = "Logged Out"
                    else:
                        acc_data["status"] = "error"
                        acc_data["status_label"] = f"HTTP {res.status_code}"
                except Exception as e:
                    acc_data["status"] = "offline"
                    acc_data["status_label"] = "Service Offline"
                    acc_data["error_details"] = f"Cannot reach Threads uploader: {str(e)[:100]}"

            elif platform_str == "facebook":
                acc_data["status"] = "disabled"
                acc_data["status_label"] = "Disabled in .env"
                acc_data["is_authenticated"] = False

            elif platform_str == "youtube":
                acc_data["status"] = "monitoring"
                acc_data["status_label"] = "Public Analytics Only"
                acc_data["is_authenticated"] = True

            accounts_list.append(acc_data)

    verified_only = [a for a in accounts_list if a["is_authenticated"] and a["status"] == "verified"]

    return {
        "total_brands": len(brands),
        "total_accounts": len(accounts_list),
        "total_verified": len(verified_only),
        "verified_accounts": verified_only,
        "all_accounts": accounts_list
    }


@router.get("/api/feed/profile")
def get_feed_profile(brand_id: Optional[str] = Query(None)):
    """
    Fetches real-time profile metadata and live media for the specified brand's Instagram account.
    """
    brands = list_brands()
    if not brands:
        return {"status": "error", "message": "No brands found"}

    target_brand = None
    if brand_id:
        target_brand = next((b for b in brands if b.id == brand_id), None)
    if not target_brand and brands:
        target_brand = brands[0]

    # Find Instagram profile
    ig_profile = None
    for p in target_brand.profiles:
        platform_str = p.platform.value if hasattr(p.platform, "value") else str(p.platform)
        if platform_str == "instagram":
            ig_profile = p
            break

    handle = ig_profile.account_handle if ig_profile else "lyr.ical786"

    # Query Instagram microservice for live profile
    profile_info = {
        "handle": handle,
        "brand_name": target_brand.name,
        "brand_color": target_brand.color_badge,
        "is_authenticated": False,
        "user_id": None,
        "full_name": target_brand.name,
        "biography": "",
        "profile_pic_url": None,
        "follower_count": 0,
        "following_count": 0,
        "media_count": 0,
        "is_verified": False,
        "source": "fallback"
    }
    live_medias: List[Dict[str, Any]] = []

    try:
        res = requests.get(f"{INSTA_FB_API_URL}/accounts/{handle}/profile", timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get("is_authenticated"):
                profile_info.update({
                    "is_authenticated": True,
                    "user_id": data.get("user_id"),
                    "full_name": data.get("full_name") or target_brand.name,
                    "biography": data.get("biography") or "",
                    "profile_pic_url": data.get("profile_pic_url"),
                    "follower_count": data.get("follower_count", 0),
                    "following_count": data.get("following_count", 0),
                    "media_count": data.get("media_count", 0),
                    "is_verified": data.get("is_verified", False),
                    "source": "instagrapi_live"
                })

                # Fetch live medias
                try:
                    m_res = requests.get(f"{INSTA_FB_API_URL}/accounts/{handle}/medias?amount=12", timeout=5)
                    if m_res.status_code == 200:
                        live_medias = m_res.json()
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"Could not reach Insta service for feed profile: {e}")

    # If not authenticated via instagrapi, scrape public metadata
    if not profile_info["is_authenticated"]:
        try:
            scraped = scrape_competitor_instagram(handle)
            if scraped.get("status") == "success":
                profile_info["follower_count"] = scraped.get("followers", 0)
                profile_info["media_count"] = scraped.get("total_posts", 0)
                profile_info["source"] = "public_scrape"
        except Exception:
            pass

    return {
        "status": "success",
        "profile": profile_info,
        "live_medias": live_medias
    }


@router.post("/api/accounts/{username}/harvest-session")
def harvest_session_endpoint(username: str):
    """
    Launches an isolated Chromium browser for the account so the user can log in once.
    Cookies are automatically extracted and saved to .env & sessions.
    """
    from fastapi import HTTPException
    import subprocess
    import sys
    from app.config import PROJECTS_ROOT

    clean_user = username.lstrip("@").strip()
    harvest_script = PROJECTS_ROOT / "harvest_session.py"
    if not harvest_script.exists():
        raise HTTPException(status_code=500, detail="harvest_session.py not found.")

    cmd = [sys.executable, str(harvest_script), clean_user, "--timeout", "180"]
    flags = subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    subprocess.Popen(cmd, creationflags=flags)

    return {
        "status": "launched",
        "username": clean_user,
        "message": f"Browser launched for @{clean_user}. Log in once in the opened window to save cookies permanently."
    }
