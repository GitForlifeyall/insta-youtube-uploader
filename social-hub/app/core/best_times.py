"""Audience activity and best-time recommendations for social publishing.

The scores are normalized planning heuristics, not live platform telemetry.  A
score of 100 means the strongest expected audience activity in this model.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


SUPPORTED_PLATFORMS = ("instagram", "youtube", "threads")
_LEVEL_COLORS = {
    "low": "#2a2e18",
    "medium": "#5b531b",
    "high": "#9aa52f",
    "peak": "#e7ff56",
}


def _normalize_platform(platform: str) -> str:
    normalized = (platform or "").strip().lower().replace("-", "_")
    aliases = {
        "ig": "instagram",
        "yt": "youtube",
        "youtube_shorts": "youtube",
        "threads_app": "threads",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized != "all" and normalized not in SUPPORTED_PLATFORMS:
        raise ValueError(
            f"Unsupported platform {platform!r}; use instagram, youtube, threads, or all"
        )
    return normalized


def _clamp_score(value: int | float) -> int:
    return max(0, min(100, int(round(value))))


def _level(score: int) -> str:
    if score <= 40:
        return "low"
    if score <= 70:
        return "medium"
    if score <= 85:
        return "high"
    return "peak"


def _display_time(hour: int, minute: int = 0) -> str:
    suffix = "AM" if hour < 12 else "PM"
    display_hour = hour % 12 or 12
    return f"{display_hour}:{minute:02d} {suffix}" if minute else f"{display_hour} {suffix}"


def _instagram_scores(day_of_week: int) -> list[int]:
    # The core Instagram windows are stable across the week in this model.
    scores = [15, 12, 10, 12, 16, 20, 28, 48, 66, 72, 62, 76, 88, 88, 72, 58, 54, 66, 82, 96, 94, 85, 65, 40]
    return scores


def _youtube_scores(day_of_week: int) -> list[int]:
    scores = [16, 12, 10, 11, 14, 18, 24, 30, 38, 44, 50, 58, 64, 70, 76, 82, 86, 90, 94, 96, 94, 82, 62, 38]
    if day_of_week >= 5:
        # Weekend viewing starts earlier and the afternoon peak moves forward.
        scores = [18, 14, 12, 13, 16, 20, 28, 38, 48, 58, 68, 80, 86, 88, 84, 72, 68, 82, 92, 96, 94, 80, 60, 36]
    return scores


def _threads_scores(day_of_week: int) -> list[int]:
    scores = [18, 14, 12, 14, 20, 34, 58, 82, 92, 90, 74, 60, 52, 48, 46, 50, 62, 76, 88, 91, 89, 74, 52, 32]
    if day_of_week >= 5:
        scores[7:10] = [76, 84, 82]
        scores[18:21] = [84, 90, 88]
    return scores


def _scores_for(platform: str, day_of_week: int) -> list[int]:
    if platform == "instagram":
        return _instagram_scores(day_of_week)
    if platform == "youtube":
        return _youtube_scores(day_of_week)
    if platform == "threads":
        return _threads_scores(day_of_week)
    platform_scores = [_scores_for(item, day_of_week) for item in SUPPORTED_PLATFORMS]
    return [
        _clamp_score(sum(scores[hour] for scores in platform_scores) / len(platform_scores))
        for hour in range(24)
    ]


def get_hourly_heatmap(platform: str = "all", day_of_week: int = 0) -> list[dict[str, Any]]:
    """Return 24 audience-activity entries for a Monday-based weekday index."""

    normalized = _normalize_platform(platform)
    if not isinstance(day_of_week, int) or isinstance(day_of_week, bool) or not 0 <= day_of_week <= 6:
        raise ValueError("day_of_week must be an integer from 0 (Monday) to 6 (Sunday)")

    scores = _scores_for(normalized, day_of_week)
    return [
        {
            "hour": hour,
            "display_time": _display_time(hour),
            "score": score,
            "level": _level(score),
            "color": _LEVEL_COLORS[_level(score)],
        }
        for hour, score in enumerate(scores)
    ]


def _parse_target_date(target_date_str: str | None) -> date:
    if target_date_str is None:
        return date.today()
    try:
        return datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise ValueError("target_date_str must use YYYY-MM-DD format") from exc


def _recommendation_label(platform: str, hour: int, score: int) -> str:
    if score >= 94:
        return "🔥 Prime Audience Peak"
    if 11 <= hour <= 14:
        return "⚡ Lunch Rush"
    if hour >= 18:
        return "🌙 Late Evening Window"
    if platform == "threads" and 7 <= hour <= 10:
        return "☀️ Morning Conversation Peak"
    if platform == "youtube" and 14 <= hour <= 17:
        return "▶️ Afternoon Watch Window"
    return "✨ Strong Audience Window"


def _candidate_times(platform: str, day_of_week: int) -> list[tuple[int, int]]:
    if platform == "instagram":
        candidates = [(19, 30), (13, 0), (21, 0)]
    elif platform == "youtube":
        candidates = (
            [(12, 0), (13, 0), (17, 0), (18, 0), (19, 0), (20, 0)]
            if day_of_week >= 5
            else [(15, 0), (16, 0), (18, 0), (19, 0), (20, 0), (21, 0)]
        )
    else:
        candidates = [(8, 0), (8, 30), (9, 0), (18, 30), (19, 0), (20, 0), (21, 0)]
    return candidates


def get_recommended_slots(
    platform: str = "instagram", target_date_str: str | None = None
) -> list[dict[str, Any]]:
    """Return the three strongest half-hour scheduling windows for a date."""

    normalized = _normalize_platform(platform)
    if normalized == "all":
        raise ValueError("get_recommended_slots requires a specific platform")
    target_date = _parse_target_date(target_date_str)
    scores = _scores_for(normalized, target_date.weekday())

    candidates = []
    for hour, minute in _candidate_times(normalized, target_date.weekday()):
        score = scores[hour]
        candidates.append(
            {
                "time": f"{hour:02d}:{minute:02d}",
                "display": _display_time(hour, minute),
                "score": score,
                "label": _recommendation_label(normalized, hour, score),
                "datetime_iso": f"{target_date.isoformat()}T{hour:02d}:{minute:02d}:00",
                "_hour": hour,
            }
        )

    # Prefer distinct windows so three adjacent half-hours do not crowd out
    # the next meaningful audience peak.
    candidates.sort(key=lambda item: (-item["score"], item["_hour"], item["time"]))
    selected: list[dict[str, Any]] = []
    for candidate in candidates:
        if all(abs(candidate["_hour"] - item["_hour"]) >= 1 for item in selected):
            selected.append(candidate)
        if len(selected) == 3:
            break
    if len(selected) < 3:
        selected = candidates[:3]
    for item in selected:
        item.pop("_hour", None)
    return selected


def calculate_engagement_rate(views: int, likes: int, comments: int) -> float:
    """Calculate Metricool's engagement rate as a percentage."""

    if views <= 0:
        return 0.0
    return round(((likes + comments) / views) * 100.0, 2)


if __name__ == "__main__":
    slots = get_recommended_slots("instagram")
    assert len(slots) == 3
    assert slots[0]["score"] >= slots[1]["score"]
    heatmap = get_hourly_heatmap("youtube", day_of_week=5)
    assert len(heatmap) == 24
    rate = calculate_engagement_rate(10000, 450, 50)
    assert rate == 5.0
    # ASCII output keeps the standalone check runnable under Windows CP1252.
    print("All Best Times tests passed!")
