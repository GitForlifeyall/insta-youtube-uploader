from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.core.database import (
    list_competitors, add_competitor, delete_competitor, record_competitor_metrics
)

router = APIRouter(prefix="/api/competitors", tags=["Competitor Radar"])


class CompetitorCreate(BaseModel):
    brand_id: str
    platform: str
    account_handle: str
    display_name: Optional[str] = None


@router.get("")
def get_competitors(brand_id: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    return list_competitors(brand_id=brand_id)


@router.post("")
def create_competitor(req: CompetitorCreate) -> Dict[str, Any]:
    comp = add_competitor(
        brand_id=req.brand_id,
        platform=req.platform,
        account_handle=req.account_handle,
        display_name=req.display_name
    )
    # Trigger initial scrape in background or synchronously
    try:
        from app.core.competitor_spy import scrape_competitor_youtube, scrape_competitor_instagram
        if req.platform.lower() == "youtube":
            data = scrape_competitor_youtube(req.account_handle)
        else:
            data = scrape_competitor_instagram(req.account_handle)
        if data.get("status") == "success":
            record_competitor_metrics(
                competitor_id=comp["id"],
                followers=data.get("followers", 0),
                total_posts=data.get("total_posts", 0),
                recent_avg_views=data.get("recent_avg_views", 0)
            )
    except Exception:
        pass
    return comp


@router.delete("/{competitor_id}")
def remove_competitor(competitor_id: str):
    success = delete_competitor(competitor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return {"status": "success", "message": f"Competitor {competitor_id} removed"}


@router.post("/refresh")
def refresh_all_competitors(brand_id: Optional[str] = Query(None)) -> Dict[str, Any]:
    competitors = list_competitors(brand_id=brand_id)
    updated = []

    for c in competitors:
        comp_id = c["id"]
        platform = c["platform"]
        handle = c["account_handle"]
        try:
            from app.core.competitor_spy import scrape_competitor_youtube, scrape_competitor_instagram
            if platform == "youtube":
                res = scrape_competitor_youtube(handle)
            else:
                res = scrape_competitor_instagram(handle)
            if res.get("status") == "success":
                record_competitor_metrics(
                    competitor_id=comp_id,
                    followers=res.get("followers", 0),
                    total_posts=res.get("total_posts", 0),
                    recent_avg_views=res.get("recent_avg_views", 0)
                )
                updated.append({"handle": handle, "status": "updated", "followers": res.get("followers", 0)})
            else:
                updated.append({"handle": handle, "status": "failed", "error": res.get("error")})
        except Exception as e:
            updated.append({"handle": handle, "status": "error", "error": str(e)})

    return {"status": "success", "processed_count": len(updated), "details": updated}
