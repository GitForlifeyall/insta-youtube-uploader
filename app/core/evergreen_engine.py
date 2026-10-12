"""
♻️ Evergreen Content Recycling Engine
Filters active posts by cooldown and repeat caps, detects unoccupied schedule slots,
and refills the queue with high-performing evergreen content.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import re
from typing import Any, List, Dict


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid ISO date: {value!r}") from exc


def find_empty_calendar_slots(
    existing_scheduled_dates: list[str], days_ahead: int = 7
) -> list[str]:
    """Return unoccupied dates from tomorrow through days_ahead days out."""
    if not isinstance(days_ahead, int) or isinstance(days_ahead, bool) or days_ahead < 0:
        raise ValueError("days_ahead must be a non-negative integer")
    existing = {_parse_date(value[:10]) for value in existing_scheduled_dates if value}
    today = date.today()
    return [
        (today + timedelta(days=offset)).isoformat()
        for offset in range(1, days_ahead + 1)
        if today + timedelta(days=offset) not in existing
    ]


def _parse_timestamp(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def select_eligible_evergreen_posts(
    evergreen_pool: list[dict[str, Any]], min_cooldown_days: int = 14
) -> list[dict[str, Any]]:
    """Filter active posts by repeat limit and elapsed cooldown."""
    if not isinstance(min_cooldown_days, int) or isinstance(min_cooldown_days, bool) or min_cooldown_days < 0:
        raise ValueError("min_cooldown_days must be a non-negative integer")
    now = datetime.now(timezone.utc)
    eligible = []
    for post in evergreen_pool:
        if post.get("is_active") is not True:
            continue
        times_posted = int(post.get("times_posted", 0) or 0)
        max_repeats = int(post.get("max_repeats", 0) or 0)
        if times_posted >= max_repeats:
            continue
        last_posted_at = post.get("last_posted_at")
        if last_posted_at:
            try:
                elapsed = now - _parse_timestamp(last_posted_at)
            except (TypeError, ValueError):
                continue
            if elapsed < timedelta(days=min_cooldown_days):
                continue
        eligible.append(post)
    return sorted(eligible, key=lambda post: int(post.get("times_posted", 0) or 0))


def generate_recycled_schedule(
    empty_slots: list[str], eligible_posts: list[dict[str, Any]], preferred_time: str = "19:30"
) -> list[dict[str, Any]]:
    """Pair empty dates with eligible posts, using each post at most once."""
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", preferred_time):
        raise ValueError("preferred_time must use HH:MM format")
    hour, minute = (int(value) for value in preferred_time.split(":"))
    plans = []
    for slot, post in zip(empty_slots, eligible_posts):
        scheduled_date = _parse_date(slot)
        scheduled = datetime.combine(scheduled_date, time(hour, minute))
        plans.append({
            "evergreen_id": post.get("id"),
            "scheduled_time": scheduled.strftime("%Y-%m-%dT%H:%M:%S"),
            "caption": post.get("caption", ""),
            "media_paths": list(post.get("media_paths") or []),
        })
    return plans
