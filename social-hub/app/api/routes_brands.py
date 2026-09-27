from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pathlib import Path
from app.core.models import Brand, BrandCreate, Profile, ProfileCreate
from app.core.database import (
    list_brands, create_brand, delete_brand,
    add_profile_to_brand, delete_profile
)
from app.config import INSTA_SESSIONS_DIR, THREADS_SESSIONS_DIR

router = APIRouter(prefix="/api", tags=["Brands & Profiles"])


@router.get("/brands", response_model=List[Brand])
def get_brands():
    return list_brands()


@router.post("/brands", response_model=Brand)
def add_brand(brand: BrandCreate):
    return create_brand(brand)


@router.delete("/brands/{brand_id}")
def remove_brand(brand_id: str):
    success = delete_brand(brand_id)
    if not success:
        raise HTTPException(status_code=404, detail="Brand not found")
    return {"status": "success", "message": f"Brand {brand_id} deleted"}


@router.post("/brands/{brand_id}/profiles", response_model=Profile)
def add_profile(brand_id: str, profile: ProfileCreate):
    return add_profile_to_brand(brand_id, profile)


@router.delete("/profiles/{profile_id}")
def remove_profile(profile_id: str):
    success = delete_profile(profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "success", "message": f"Profile {profile_id} deleted"}


@router.get("/detected-sessions")
def get_detected_sessions() -> Dict[str, Any]:
    """Scans sessions/ folders in uploaders to auto-discover existing logged-in accounts."""
    insta_accounts = []
    threads_accounts = []

    if INSTA_SESSIONS_DIR.exists():
        for f in INSTA_SESSIONS_DIR.glob("session_*.json"):
            # e.g. session_lulop.123.json -> lulop.123
            name = f.stem.replace("session_", "")
            if name:
                insta_accounts.append(name)

    if THREADS_SESSIONS_DIR.exists():
        for f in THREADS_SESSIONS_DIR.glob("session_*.json"):
            name = f.stem.replace("session_", "")
            if name:
                threads_accounts.append(name)
        for f in THREADS_SESSIONS_DIR.glob("token_*.dat"):
            name = f.stem.replace("token_", "")
            if name:
                threads_accounts.append(name)

    return {
        "instagram": sorted(list(set(insta_accounts))),
        "threads": sorted(list(set(threads_accounts)))
    }


@router.post("/sync-credentials")
def sync_credentials_now() -> Dict[str, Any]:
    """Manually triggers a credential sync from .env into brand profiles and sessions."""
    from app.core.credentials_sync import sync_credentials_from_env
    res = sync_credentials_from_env(delay_seconds=0)
    return {"status": "success", "result": res}

