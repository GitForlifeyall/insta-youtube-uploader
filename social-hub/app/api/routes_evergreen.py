from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.core.database import (
    list_evergreen_posts, add_evergreen_post, delete_evergreen_post,
    increment_evergreen_usage, list_posts, create_post
)
from app.core.models import ScheduledPostCreate, PlatformType, PostType

router = APIRouter(prefix="/api/evergreen", tags=["Evergreen Content Recycling"])


class EvergreenCreate(BaseModel):
    brand_id: str
    caption: str
    media_paths: List[str] = []
    target_platforms: List[str] = ["instagram", "facebook"]
    max_repeats: int = 3


class AutoFillRequest(BaseModel):
    brand_id: str
    days_ahead: int = 7
    preferred_time: str = "19:30"


@router.get("")
def get_evergreen(brand_id: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    return list_evergreen_posts(brand_id=brand_id)


@router.post("")
def add_to_evergreen_pool(req: EvergreenCreate) -> Dict[str, Any]:
    return add_evergreen_post(
        brand_id=req.brand_id,
        caption=req.caption,
        media_paths=req.media_paths,
        target_platforms=req.target_platforms,
        max_repeats=req.max_repeats
    )


@router.delete("/{evergreen_id}")
def remove_evergreen_post(evergreen_id: str):
    success = delete_evergreen_post(evergreen_id)
    if not success:
        raise HTTPException(status_code=404, detail="Evergreen post not found")
    return {"status": "success", "message": "Evergreen post removed"}


@router.post("/auto-fill-queue")
def auto_fill_queue(req: AutoFillRequest) -> Dict[str, Any]:
    """Scans the next N days. For days with zero scheduled posts, schedules an eligible evergreen post."""
    existing_posts = list_posts(brand_id=req.brand_id)
    existing_dates = set(p.scheduled_time[:10] for p in existing_posts)

    pool = list_evergreen_posts(brand_id=req.brand_id)
    if not pool:
        return {"status": "skipped", "message": "Evergreen pool is empty. Add posts to evergreen pool first!"}

    # Find empty calendar days
    today = datetime.now().date()
    empty_dates = []
    for d in range(1, req.days_ahead + 1):
        target_date = (today + timedelta(days=d)).strftime("%Y-%m-%d")
        if target_date not in existing_dates:
            empty_dates.append(target_date)

    if not empty_dates:
        return {"status": "complete", "message": "Schedule is already fully booked for the next days.", "scheduled_count": 0}

    # Eligible posts (times_posted < max_repeats)
    eligible = [p for p in pool if p["is_active"] and p["times_posted"] < p["max_repeats"]]
    if not eligible:
        return {"status": "skipped", "message": "All evergreen posts have reached their max repeat limit.", "scheduled_count": 0}

    # Sort by times_posted ASC
    eligible.sort(key=lambda x: x["times_posted"])

    scheduled_results = []
    for idx, slot_date in enumerate(empty_dates):
        if idx >= len(eligible):
            break
        chosen = eligible[idx]
        scheduled_iso = f"{slot_date}T{req.preferred_time}:00"

        platforms = [PlatformType(p) for p in chosen.get("target_platforms", ["instagram"])]
        new_post = create_post(ScheduledPostCreate(
            brand_id=req.brand_id,
            target_platforms=platforms,
            post_type=PostType.REEL,
            media_paths=chosen.get("media_paths", []),
            caption=chosen.get("caption", ""),
            scheduled_time=scheduled_iso,
            share_to_facebook="facebook" in chosen.get("target_platforms", []),
            share_to_threads="threads" in chosen.get("target_platforms", [])
        ))
        increment_evergreen_usage(chosen["id"])
        scheduled_results.append({
            "post_id": new_post.id,
            "scheduled_time": scheduled_iso,
            "caption": new_post.caption
        })

    return {
        "status": "success",
        "scheduled_count": len(scheduled_results),
        "scheduled_posts": scheduled_results
    }
