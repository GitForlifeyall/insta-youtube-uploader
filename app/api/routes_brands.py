from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.core.models import Brand, BrandCreate, Profile, ProfileCreate
from app.core.database import (
    list_brands, create_brand, delete_brand,
    add_profile_to_brand, delete_profile
)
from app.core.client_manager import client_manager

router = APIRouter(prefix="/api/brands", tags=["Brands & Workspaces"])


@router.get("", response_model=List[Brand])
def get_brands():
    return list_brands()


@router.post("", response_model=Brand)
def add_brand(brand: BrandCreate):
    return create_brand(brand)


@router.delete("/{brand_id}")
def remove_brand(brand_id: str):
    success = delete_brand(brand_id)
    if not success:
        raise HTTPException(status_code=404, detail="Brand not found")
    return {"status": "success", "message": f"Brand {brand_id} deleted"}


@router.post("/{brand_id}/profiles", response_model=Profile)
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
    """Returns detected logged-in Instagram accounts in the client manager."""
    accs = client_manager.get_active_accounts()
    return {
        "instagram": [a["username"] for a in accs]
    }
