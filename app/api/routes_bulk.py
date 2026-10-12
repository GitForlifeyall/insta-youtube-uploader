from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.config import TEMPLATES_DIR
from app.core.database import create_post
from app.core.models import ScheduledPostCreate, PlatformType, PostType
from app.core.csv_importer import validate_csv_content, import_validated_posts

router = APIRouter(prefix="/api/posts", tags=["Bulk Scheduling & CSV Import"])


def _template_response(filename: str, download_name: str) -> FileResponse:
    template_path = TEMPLATES_DIR / filename
    if not template_path.is_file():
        raise HTTPException(status_code=404, detail="CSV template not found")
    return FileResponse(
        path=template_path,
        media_type="text/csv",
        filename=download_name,
    )


@router.get("/templates/metricool")
def download_metricool_template() -> FileResponse:
    return _template_response("metricool_template.csv", "metricool_template.csv")


@router.get("/templates/custom")
def download_custom_template() -> FileResponse:
    return _template_response("custom_social_hub_template.csv", "custom_social_hub_template.csv")


class BulkScheduleRequest(BaseModel):
    brand_id: str
    media_paths: List[str]
    caption_template: str
    first_comment: Optional[str] = None
    start_date: Optional[str] = None
    interval_days: int = 1
    preferred_time: str = "19:30"


@router.post("/bulk-schedule")
def bulk_schedule_posts(req: BulkScheduleRequest) -> Dict[str, Any]:
    if not req.media_paths:
        raise HTTPException(status_code=400, detail="No media files selected for bulk schedule")

    today = datetime.now().date()
    start_dt = datetime.strptime(req.start_date, "%Y-%m-%d").date() if req.start_date else today + timedelta(days=1)
    created = []

    for i, mpath in enumerate(req.media_paths):
        slot_date = start_dt + timedelta(days=i * req.interval_days)
        slot_date_str = slot_date.strftime("%Y-%m-%d")
        scheduled_iso = f"{slot_date_str}T{req.preferred_time}:00"

        filename = Path(mpath).stem.replace("_", " ")
        caption = req.caption_template.replace("{filename}", filename).replace("{index}", str(i + 1))

        new_post = create_post(ScheduledPostCreate(
            brand_id=req.brand_id,
            target_platforms=[PlatformType.INSTAGRAM],
            post_type=PostType.REEL,
            media_paths=[mpath],
            caption=caption,
            first_comment=req.first_comment,
            scheduled_time=scheduled_iso
        ))
        created.append({
            "id": new_post.id,
            "scheduled_time": scheduled_iso,
            "filename": filename
        })

    return {
        "status": "success",
        "total_scheduled": len(created),
        "scheduled_posts": created
    }


class CsvValidateRequest(BaseModel):
    csv_text: str
    date_format: str = "YYYY-MM-DD"
    time_format: str = "24h"
    brand_id: Optional[str] = None


class CsvImportRequest(BaseModel):
    posts: List[Dict[str, Any]]


@router.post("/csv-validate")
def csv_validate(req: CsvValidateRequest) -> Dict[str, Any]:
    if not req.csv_text or not req.csv_text.strip():
        raise HTTPException(status_code=400, detail="CSV content is empty")
    return validate_csv_content(
        csv_text=req.csv_text,
        date_format_pref=req.date_format,
        time_format_pref=req.time_format,
        default_brand_id=req.brand_id
    )


@router.post("/csv-import")
def csv_import(req: CsvImportRequest) -> Dict[str, Any]:
    if not req.posts:
        raise HTTPException(status_code=400, detail="No posts provided to import")
    return import_validated_posts(req.posts)
