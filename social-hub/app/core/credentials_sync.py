"""
🔐 Automatic Credential & Multi-Brand Synchronizer
Reads root .env file on startup, auto-authenticates Instagram & Threads for each brand,
caches persistent session files, and binds accounts to their respective Social Hub Brand Workspaces.
"""

import os
import time
import logging
import requests
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

from app.config import (
    PROJECTS_ROOT,
    INSTA_FB_API_URL,
    THREADS_API_URL,
    INSTA_SESSIONS_DIR,
    THREADS_SESSIONS_DIR
)
from app.core.database import (
    list_brands,
    create_brand,
    update_brand,
    add_profile_to_brand,
    delete_profile
)
from app.core.models import BrandCreate, ProfileCreate, PlatformType

logger = logging.getLogger("CredentialsSync")
ROOT_ENV_PATH = PROJECTS_ROOT / ".env"


def _authenticate_instagram(username: str, password: str = None, session_id: str = None) -> str:
    """Attempts login if session file does not already exist."""
    session_file = INSTA_SESSIONS_DIR / f"session_{username}.json"
    if session_file.exists():
        return "session_active"

    payload = {
        "username": username,
        "password": password or None,
        "session_id": session_id or None
    }
    try:
        res = requests.post(f"{INSTA_FB_API_URL}/accounts/login", json=payload, timeout=12)
        if res.status_code == 200:
            logger.info(f"✅ Instagram session successfully saved for @{username}")
            return "connected"
        else:
            err_msg = res.text
            logger.warning(f"⚠️ Instagram login for @{username} failed ({res.status_code}): {err_msg[:150]}")
            if "user_has_logged_out" in err_msg.lower():
                if session_file.exists():
                    try:
                        session_file.unlink()
                    except Exception:
                        pass
                return "session_id_expired"
            if "out of date" in err_msg.lower() or "challenge" in err_msg.lower():
                return "session_id_required"
            return f"error: {res.status_code}"
    except Exception as e:
        logger.warning(f"Could not connect to Instagram uploader: {e}")
        return "service_unavailable"


def _authenticate_threads(username: str, password: str) -> str:
    """Attempts Threads login if token file does not already exist."""
    token_file = THREADS_SESSIONS_DIR / f"token_{username}.dat"
    if token_file.exists():
        return "session_active"

    payload = {
        "username": username,
        "password": password
    }
    try:
        res = requests.post(f"{THREADS_API_URL}/accounts/login", json=payload, timeout=6)
        if res.status_code == 200:
            logger.info(f"✅ Threads token saved for @{username}")
            return "connected"
        else:
            logger.warning(f"⚠️ Threads login for @{username} failed ({res.status_code}): {res.text[:150]}")
            return f"error: {res.status_code}"
    except Exception as e:
        logger.warning(f"Could not connect to Threads uploader: {e}")
        return "service_unavailable"




def sync_credentials_from_env(delay_seconds: int = 0) -> Dict[str, Any]:
    """
    Scans root .env for single or multi-brand configs (BRAND1_*, BRAND2_*, etc.)
    and automatically manages sessions and database profile linkages.
    """
    if delay_seconds > 0:
        time.sleep(delay_seconds)

    if not ROOT_ENV_PATH.exists():
        logger.info(f"ℹ️ No root .env file found at {ROOT_ENV_PATH}")
        return {"status": "skipped", "message": "No .env found"}

    load_dotenv(dotenv_path=ROOT_ENV_PATH, override=True)

    # Collect configured brands from .env
    brand_configs = []

    # Check BRAND1, BRAND2, BRAND3...
    for i in range(1, 10):
        prefix = f"BRAND{i}_"
        b_name = os.getenv(f"{prefix}NAME", "").strip()
        if not b_name:
            # Check if default un-prefixed values exist for Brand 1
            if i == 1 and os.getenv("INSTAGRAM_USERNAME"):
                b_name = "Lyrical786"
            else:
                continue

        ig_user = os.getenv(f"{prefix}IG_USERNAME", "").strip() or (os.getenv("INSTAGRAM_USERNAME", "").strip() if i == 1 else "")
        ig_pass = os.getenv(f"{prefix}IG_PASSWORD", "").strip() or (os.getenv("INSTAGRAM_PASSWORD", "").strip() if i == 1 else "")
        ig_session = os.getenv(f"{prefix}IG_SESSION_ID", "").strip() or (os.getenv("INSTAGRAM_SESSION_ID", "").strip() if i == 1 else "")

        th_user = os.getenv(f"{prefix}THREADS_USERNAME", "").strip() or (os.getenv("THREADS_USERNAME", "").strip() if i == 1 else ig_user)
        th_pass = os.getenv(f"{prefix}THREADS_PASSWORD", "").strip() or (os.getenv("THREADS_PASSWORD", "").strip() if i == 1 else ig_pass)

        yt_handle = os.getenv(f"{prefix}YOUTUBE_HANDLE", "").strip()
        fb_auto = os.getenv(f"{prefix}FB_AUTO_SHARE", os.getenv("FACEBOOK_AUTO_SHARE", "true")).strip().lower() in ("true", "1", "yes")
        color = os.getenv(f"{prefix}COLOR", "#8ACE00" if i == 1 else "#e7ff56")

        brand_configs.append({
            "name": b_name,
            "color": color,
            "ig_user": ig_user,
            "ig_pass": ig_pass,
            "ig_session": ig_session,
            "th_user": th_user,
            "th_pass": th_pass,
            "yt_handle": yt_handle,
            "fb_auto": fb_auto
        })

    existing_brands = list_brands()
    sync_results = []

    for cfg in brand_configs:
        target_name = cfg["name"]
        matched_brand = None

        # Try to find existing brand by name or rename default 'Main Brand'
        for b in existing_brands:
            if b.name.lower() == target_name.lower():
                matched_brand = b
                break
        
        # If not matched and this is the first config and 'Main Brand' exists, rename 'Main Brand'
        if not matched_brand and cfg == brand_configs[0]:
            for b in existing_brands:
                if b.name == "Main Brand":
                    update_brand(b.id, target_name, cfg["color"])
                    b.name = target_name
                    matched_brand = b
                    logger.info(f"Renamed 'Main Brand' -> '{target_name}'")
                    break

        # If still not found, create new brand workspace
        if not matched_brand:
            matched_brand = create_brand(BrandCreate(
                name=target_name,
                color_badge=cfg["color"],
                description=f"Auto-generated workspace for {target_name}"
            ))
            logger.info(f"Created new brand workspace: '{target_name}'")

        # Clean up legacy dummy placeholder profile 'lulop.123'
        for p in list(matched_brand.profiles):
            if p.account_handle == "lulop.123":
                try:
                    delete_profile(p.id)
                    logger.info(f"Removed dummy placeholder profile from brand '{target_name}'")
                except Exception:
                    pass

        # Re-fetch profiles for this brand
        all_brands = list_brands()
        current_brand = next((b for b in all_brands if b.id == matched_brand.id), matched_brand)
        curr_profiles = current_brand.profiles

        brand_res = {
            "brand": target_name,
            "instagram": cfg.get("ig_user", ""),
            "threads": cfg.get("th_user", ""),
            "profiles_linked": []
        }

        # 1. Instagram
        if cfg["ig_user"]:
            if cfg["ig_pass"] or cfg["ig_session"]:
                status = _authenticate_instagram(cfg["ig_user"], cfg["ig_pass"], cfg["ig_session"])
                brand_res["instagram_status"] = status

            has_ig = any(p.account_handle == cfg["ig_user"] and p.platform == PlatformType.INSTAGRAM for p in curr_profiles)
            if not has_ig:
                add_profile_to_brand(current_brand.id, ProfileCreate(
                    platform=PlatformType.INSTAGRAM,
                    account_handle=cfg["ig_user"],
                    display_name=f"@{cfg['ig_user']}"
                ))
                brand_res["profiles_linked"].append(f"Instagram: @{cfg['ig_user']}")

        # 2. Facebook
        if cfg["fb_auto"] and cfg["ig_user"]:
            has_fb = any(p.account_handle == cfg["ig_user"] and p.platform == PlatformType.FACEBOOK for p in curr_profiles)
            if not has_fb:
                add_profile_to_brand(current_brand.id, ProfileCreate(
                    platform=PlatformType.FACEBOOK,
                    account_handle=cfg["ig_user"],
                    display_name=f"{cfg['ig_user']} Facebook Page"
                ))
                brand_res["profiles_linked"].append(f"Facebook: {cfg['ig_user']} Page")

        # 3. Threads
        if cfg["th_user"]:
            if cfg["th_pass"]:
                th_status = _authenticate_threads(cfg["th_user"], cfg["th_pass"])
                brand_res["threads_status"] = th_status

            has_th = any(p.account_handle == cfg["th_user"] and p.platform == PlatformType.THREADS for p in curr_profiles)
            if not has_th:
                add_profile_to_brand(current_brand.id, ProfileCreate(
                    platform=PlatformType.THREADS,
                    account_handle=cfg["th_user"],
                    display_name=f"@{cfg['th_user']} Threads"
                ))
                brand_res["profiles_linked"].append(f"Threads: @{cfg['th_user']}")

        # 4. YouTube
        if cfg["yt_handle"]:
            has_yt = any(p.account_handle == cfg["yt_handle"] and p.platform == PlatformType.YOUTUBE for p in curr_profiles)
            if not has_yt:
                add_profile_to_brand(current_brand.id, ProfileCreate(
                    platform=PlatformType.YOUTUBE,
                    account_handle=cfg["yt_handle"],
                    display_name=f"{cfg['yt_handle']} YouTube"
                ))
                brand_res["profiles_linked"].append(f"YouTube: {cfg['yt_handle']}")

        sync_results.append(brand_res)

    return {
        "status": "success",
        "brands_synced": sync_results
    }
