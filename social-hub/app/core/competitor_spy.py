"""Zero-login public competitor profile metrics and benchmarking helpers."""

from __future__ import annotations

from datetime import datetime, timezone
import html
import re
from typing import Any, Iterable
from urllib.parse import urlparse

import requests

try:  # Keep imports usable in environments without yt-dlp installed.
    import yt_dlp
except ImportError:  # pragma: no cover
    yt_dlp = None  # type: ignore[assignment]


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 15


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _metric(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return max(0, int(value))
    if not isinstance(value, str):
        return 0
    text = value.strip().replace(",", "")
    match = re.search(r"([\d.]+)\s*([KMB])?", text, re.IGNORECASE)
    if not match:
        return 0
    try:
        multiplier = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}.get(
            (match.group(2) or "").lower(), 1
        )
        return int(float(match.group(1)) * multiplier)
    except ValueError:
        return 0


def _extract_handle(value: str, platform: str) -> str:
    raw = (value or "").strip()
    if not raw:
        raise ValueError("A competitor handle or URL is required")
    if "://" in raw:
        parsed = urlparse(raw)
        parts = [part for part in parsed.path.split("/") if part]
        if platform == "youtube":
            if parts and parts[0].startswith("@"):
                raw = parts[0]
            elif parts and parts[0] in {"channel", "c", "user"} and len(parts) > 1:
                raw = parts[1]
            elif parts:
                raw = parts[-1]
        elif parts:
            raw = parts[0]
    raw = raw.strip().strip("/").lstrip("@")
    if not raw:
        raise ValueError("Could not determine a competitor handle")
    return raw


def _youtube_url(handle_or_url: str) -> str:
    raw = handle_or_url.strip()
    if "://" in raw:
        return raw
    return f"https://www.youtube.com/@{raw.lstrip('@')}"


def _fallback(platform: str, handle: str, error: Exception | str) -> dict[str, Any]:
    return {
        "platform": platform,
        "status": "fallback",
        "handle": handle,
        "display_name": handle,
        "followers": 0,
        "total_posts": 0,
        "recent_avg_views": 0,
        "scraped_at": _timestamp(),
        "error": str(error),
    }


def scrape_competitor_youtube(channel_handle_or_url: str) -> dict[str, Any]:
    """Read channel and recent-video metrics using yt-dlp's public extractor."""

    handle = _extract_handle(channel_handle_or_url, "youtube")
    if yt_dlp is None:
        return _fallback("youtube", handle, "yt-dlp is required for YouTube scraping")
    try:
        options = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "playlist_items": "1:5",
        }
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(_youtube_url(channel_handle_or_url), download=False) or {}
        entries = [entry for entry in (info.get("entries") or []) if entry]
        views = [_metric(entry.get("view_count")) for entry in entries]
        views = [view for view in views if view >= 0]
        average_views = round(sum(views) / len(views)) if views else 0
        title = info.get("channel_title") or info.get("uploader") or info.get("title") or handle
        return {
            "platform": "youtube",
            "status": "success",
            "handle": handle,
            "display_name": title if isinstance(title, str) else handle,
            "followers": _metric(info.get("subscriber_count")),
            "total_posts": _metric(info.get("video_count")),
            "recent_avg_views": average_views,
            "scraped_at": _timestamp(),
        }
    except Exception as exc:
        return _fallback("youtube", handle, exc)


def _meta(document: str, property_name: str) -> str:
    patterns = (
        rf'<meta[^>]+property=["\']{re.escape(property_name)}["\'][^>]+content=["\']([^"\']*)',
        rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']{re.escape(property_name)}["\']',
    )
    for pattern in patterns:
        match = re.search(pattern, document, re.IGNORECASE)
        if match:
            return html.unescape(match.group(1))
    return ""


def _labelled_metric(text: str, labels: Iterable[str]) -> int:
    label_pattern = "|".join(re.escape(label) for label in labels)
    match = re.search(
        rf"([\d,.]+\s*[KMB]?)\s*(?:{label_pattern})\b",
        text,
        re.IGNORECASE,
    )
    return _metric(match.group(1)) if match else 0


def scrape_competitor_instagram(handle_or_url: str) -> dict[str, Any]:
    """Read public Instagram profile counts from Open Graph metadata."""

    handle = _extract_handle(handle_or_url, "instagram")
    try:
        response = requests.get(
            f"https://www.instagram.com/{handle}/",
            headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        document = response.text
        description = _meta(document, "og:description")
        title = _meta(document, "og:title")
        followers = _labelled_metric(description, ("followers", "follower"))
        total_posts = _labelled_metric(description, ("posts", "post"))
        if not followers:
            followers = _labelled_metric(document, ("followers", "follower"))
        if not total_posts:
            total_posts = _labelled_metric(document, ("posts", "post"))
        display_name = title.split("(", 1)[0].strip() if title else handle
        return {
            "platform": "instagram",
            "status": "success",
            "handle": handle,
            "display_name": display_name or handle,
            "followers": followers,
            "total_posts": total_posts,
            "recent_avg_views": 0,
            "scraped_at": _timestamp(),
        }
    except Exception as exc:
        return _fallback("instagram", handle, exc)


def calculate_competitor_differential(
    my_brand_stats: dict[str, Any], competitor_stats: dict[str, Any]
) -> dict[str, Any]:
    """Compare followers and recent average views against a competitor."""

    my_followers = _metric(my_brand_stats.get("followers", 0))
    competitor_followers = _metric(competitor_stats.get("followers", 0))
    my_views = max(_metric(my_brand_stats.get("recent_avg_views", 1)), 1)
    competitor_views = _metric(competitor_stats.get("recent_avg_views", 0))
    follower_gap = competitor_followers - my_followers
    views_ratio = round(competitor_views / my_views, 2)
    verdict = "Leading" if follower_gap <= 0 and views_ratio <= 1 else "Chasing"
    return {
        "follower_gap": follower_gap,
        "views_ratio": views_ratio,
        "summary_verdict": verdict,
    }


if __name__ == "__main__":
    res = scrape_competitor_youtube("@lofigirl")
    print("Competitor YouTube result:", res)
    assert res["status"] in ("success", "fallback")
    assert "followers" in res
    diff = calculate_competitor_differential(
        {"followers": 5000, "recent_avg_views": 1200},
        {"followers": 15000, "recent_avg_views": 3600},
    )
    assert diff["follower_gap"] == 10000
    assert diff["views_ratio"] == 3.0
    print("All Competitor Spy tests passed!")
