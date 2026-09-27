from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

router = APIRouter(prefix="/api/best-times", tags=["Best Times to Post"])


def _fallback_recommended_slots(platform: str, target_date_str: Optional[str] = None) -> List[Dict[str, Any]]:
    today_str = target_date_str or datetime.now().strftime("%Y-%m-%d")
    return [
        {
            "time": "19:30",
            "display": "7:30 PM",
            "score": 96,
            "label": "Prime Audience Peak",
            "datetime_iso": f"{today_str}T19:30:00"
        },
        {
            "time": "13:00",
            "display": "1:00 PM",
            "score": 88,
            "label": "Lunch Break Peak",
            "datetime_iso": f"{today_str}T13:00:00"
        },
        {
            "time": "21:00",
            "display": "9:00 PM",
            "score": 85,
            "label": "Late Evening Leisure",
            "datetime_iso": f"{today_str}T21:00:00"
        }
    ]


def _fallback_heatmap(platform: str, day_of_week: int) -> List[Dict[str, Any]]:
    # Baseline peak distribution curve
    peak_hours = {12: 85, 13: 88, 14: 82, 19: 94, 20: 97, 21: 89, 22: 70}
    hours = []
    for h in range(24):
        score = peak_hours.get(h, 20 + (h * 2 if h < 12 else (24 - h) * 3))
        score = min(max(score, 10), 100)
        level = "peak" if score >= 85 else ("high" if score >= 70 else ("medium" if score >= 40 else "low"))
        display = f"{12 if h in (0, 12) else h % 12} {'AM' if h < 12 else 'PM'}"
        hours.append({
            "hour": h,
            "display_time": display,
            "score": score,
            "level": level,
            "color": "#e7ff56" if level == "peak" else ("#8ace00" if level == "high" else "#33411a")
        })
    return hours


@router.get("/slots")
def get_slots(
    platform: str = Query("instagram", description="Target platform: instagram, youtube, threads"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
) -> List[Dict[str, Any]]:
    try:
        from app.core.best_times import get_recommended_slots
        return get_recommended_slots(platform=platform, target_date_str=date)
    except (ImportError, AttributeError):
        return _fallback_recommended_slots(platform=platform, target_date_str=date)


@router.get("/heatmap")
def get_heatmap(
    platform: str = Query("all", description="Target platform"),
    day_of_week: int = Query(0, ge=0, le=6, description="0=Monday, 6=Sunday")
) -> List[Dict[str, Any]]:
    try:
        from app.core.best_times import get_hourly_heatmap
        return get_hourly_heatmap(platform=platform, day_of_week=day_of_week)
    except (ImportError, AttributeError):
        return _fallback_heatmap(platform=platform, day_of_week=day_of_week)
