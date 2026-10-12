from fastapi import APIRouter, Query
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.core.analytics_service import (
    get_brand_analytics_summary, add_tracked_link, record_snapshot, list_tracked_links
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics & KPIs"])


class TrackLinkRequest(BaseModel):
    brand_id: str
    platform: str = "instagram"
    url: str
    title: Optional[str] = None
    post_id: Optional[str] = None


class RecordSnapshotRequest(BaseModel):
    brand_id: str
    platform: str = "instagram"
    views: int = 0
    likes: int = 0
    comments: int = 0
    tracked_link_id: Optional[str] = None


@router.get("/summary")
@router.get("/overview")
def get_analytics(
    brand_id: Optional[str] = Query(None, description="Brand ID to filter analytics"),
    days: int = Query(30, ge=1, le=365, description="Number of days to summarize")
) -> Dict[str, Any]:
    return get_brand_analytics_summary(brand_id=brand_id, days=days)


@router.post("/track-link")
def track_link(req: TrackLinkRequest):
    link_id = add_tracked_link(
        brand_id=req.brand_id,
        platform=req.platform,
        url=req.url,
        title=req.title,
        post_id=req.post_id
    )
    return {"status": "success", "link_id": link_id}


@router.post("/record")
def record_metric(req: RecordSnapshotRequest):
    record_snapshot(
        brand_id=req.brand_id,
        platform=req.platform,
        views=req.views,
        likes=req.likes,
        comments=req.comments,
        tracked_link_id=req.tracked_link_id
    )
    return {"status": "success", "message": "Snapshot recorded"}


@router.get("/links")
def get_links(brand_id: Optional[str] = Query(None)):
    return list_tracked_links(brand_id=brand_id)
