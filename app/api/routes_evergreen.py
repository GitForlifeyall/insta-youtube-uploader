from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.core.database import (
    list_evergreen_posts, add_evergreen_post, delete_evergreen_post,
    increment_evergreen_usage, list_posts, create_post
)
from app.core.models import ScheduledPostCreate, PlatformType, PostType
from app.core.evergreen_engine import (
    find_empty_calendar_slots, select_eligible_evergreen_posts, generate_recycled_schedule
)

router = APIRouter(prefix="/api/evergreen", tags=["Evergreen Content Recycling"])


class EvergreenCreate(BaseModel):
    brand_id: str
    caption: str
    media_paths: List[str] = []
    max_repeats: int = 3


class AutoFillRequest(BaseModel):
    brand_id: str
    days_ahead: int = 7
    preferred_time: str = "19:30"
    min_cooldown_days: int = 14


@router.get("")
def get_evergreen(brand_id: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    return list_evergreen_posts(brand_id=brand_id)


@router.post("")
def add_to_evergreen_pool(req: EvergreenCreate) -> Dict[str, Any]:
    return add_evergreen_post(
        brand_id=req.brand_id,
        caption=req.caption,
        media_paths=req.media_paths,
        target_platforms=["instagram"],
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
    existing_dates = [p.scheduled_time[:10] for p in existing_posts]

    empty_slots = find_empty_calendar_slots(existing_dates, days_ahead=req.days_ahead)
    if not empty_slots:
        return {"status": "complete", "message": "Schedule is already fully booked for upcoming days.", "scheduled_count": 0}

    pool = list_evergreen_posts(brand_id=req.brand_id)
    if not pool:
        return {"status": "skipped", "message": "Evergreen pool is empty. Add posts to the evergreen pool first!", "scheduled_count": 0}

    eligible = select_eligible_evergreen_posts(pool, min_cooldown_days=req.min_cooldown_days)
    if not eligible:
        return {"status": "skipped", "message": "All evergreen posts are currently in cooldown or hit repeat caps.", "scheduled_count": 0}

    plans = generate_recycled_schedule(empty_slots, eligible, preferred_time=req.preferred_time)

    scheduled_results = []
    for plan in plans:
        new_post = create_post(ScheduledPostCreate(
            brand_id=req.brand_id,
            target_platforms=[PlatformType.INSTAGRAM],
            post_type=PostType.REEL,
            media_paths=plan["media_paths"],
            caption=plan["caption"],
            scheduled_time=plan["scheduled_time"]
        ))
        increment_evergreen_usage(plan["evergreen_id"])
        scheduled_results.append({
            "post_id": new_post.id,
            "scheduled_time": new_post.scheduled_time,
            "caption": new_post.caption
        })

    return {
        "status": "success",
        "scheduled_count": len(scheduled_results),
        "scheduled_posts": scheduled_results
    }
