"""Best-effort public social-media metrics scrapers.

These scrapers intentionally use public page metadata and yt-dlp. They do not
accept or manage cookies, sessions, API keys, or login credentials.
"""

from __future__ import annotations

from datetime import datetime, timezone
import html
import json
import re
from typing import Any, Iterable
from urllib.parse import urlparse

import requests

try:  # Keep the module importable when yt-dlp is not installed.
    import yt_dlp
except ImportError:  # pragma: no cover - exercised only in minimal installs
    yt_dlp = None  # type: ignore[assignment]


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 15


def _timestamp() -> str:
    """Return a timezone-aware ISO 8601 timestamp."""

    return datetime.now(timezone.utc).isoformat()


def _metric(value: Any) -> int:
    """Normalize a numeric metric from JSON or human-readable text."""

    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return max(0, int(value))
    if isinstance(value, str):
        digits = re.sub(r"[^0-9]", "", value)
        return int(digits) if digits else 0
    return 0


def _successful(platform: str, **metrics: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"platform": platform, "status": "success"}
    result.update(metrics)
    result["scraped_at"] = _timestamp()
    return result


def _meta_description(document: str) -> str:
    patterns = (
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']*)',
        r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']og:description["\']',
    )
    for pattern in patterns:
        match = re.search(pattern, document, re.IGNORECASE)
        if match:
            return html.unescape(match.group(1))
    return ""


def _count_from_text(text: str, labels: Iterable[str]) -> int:
    label_pattern = "|".join(re.escape(label) for label in labels)
    match = re.search(
        rf"([\d,.\s]+)\s*(?:[KkMm])?\s*(?:{label_pattern})\b",
        text,
        re.IGNORECASE,
    )
    if not match:
        return 0
    number = match.group(1).strip().replace(" ", "")
    suffix_match = re.search(rf"{re.escape(number)}\s*([KkMm])", text, re.IGNORECASE)
    multiplier = {"k": 1_000, "m": 1_000_000}.get(
        suffix_match.group(1).lower(), 1
    ) if suffix_match else 1
    try:
        return int(float(number.replace(",", "")) * multiplier)
    except ValueError:
        return 0


def _walk_json(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _embedded_metric(document: str, keys: Iterable[str]) -> int:
    key_pattern = "|".join(re.escape(key) for key in keys)
    for match in re.finditer(
        rf"[\"'](?:{key_pattern})[\"']\s*:\s*(\d+)", document, re.IGNORECASE
    ):
        value = _metric(match.group(1))
        if value:
            return value

    for script in re.findall(
        r"<script[^>]*type=[\"']application/json[\"'][^>]*>(.*?)</script>",
        document,
        re.IGNORECASE | re.DOTALL,
    ):
        try:
            payload = json.loads(html.unescape(script))
        except (TypeError, ValueError):
            continue
        for item in _walk_json(payload):
            for key in keys:
                if key in item and _metric(item[key]):
                    return _metric(item[key])
    return 0


def scrape_youtube(url: str) -> dict[str, Any]:
    """Extract public metrics for a YouTube video or Short with yt-dlp."""

    if yt_dlp is None:
        raise RuntimeError("yt-dlp is required for YouTube scraping")
    options = {"quiet": True, "no_warnings": True, "extract_flat": True}
    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(url, download=False) or {}
    return _successful(
        "youtube",
        views=_metric(info.get("view_count")),
        likes=_metric(info.get("like_count")),
        comments=_metric(info.get("comment_count")),
        title=info.get("title") if isinstance(info.get("title"), str) else "",
    )


def _get_public_page(url: str) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.text


def scrape_instagram_reel(url: str) -> dict[str, Any]:
    """Extract public Instagram Reel/Post metrics from metadata or JSON."""

    document = _get_public_page(url)
    description = _meta_description(document)
    likes = _count_from_text(description, ("likes", "like"))
    comments = _count_from_text(description, ("comments", "comment"))
    likes = likes or _embedded_metric(document, ("like_count", "likeCount"))
    comments = comments or _embedded_metric(
        document, ("comment_count", "commentCount", "comments")
    )
    views = _embedded_metric(document, ("play_count", "playCount", "video_view_count"))
    return _successful("instagram", views=views or likes, likes=likes, comments=comments)


def scrape_threads_post(url: str) -> dict[str, Any]:
    """Extract public Threads likes and replies; Threads has no public views."""

    document = _get_public_page(url)
    description = _meta_description(document)
    likes = _count_from_text(description, ("likes", "like"))
    comments = _count_from_text(description, ("replies", "reply", "comments", "comment"))
    likes = likes or _embedded_metric(document, ("like_count", "likeCount", "likes"))
    comments = comments or _embedded_metric(
        document, ("reply_count", "replyCount", "comment_count", "commentCount", "replies")
    )
    return _successful("threads", views=0, likes=likes, comments=comments)


def _platform_for_url(url: str) -> str:
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    if host == "youtube.com" or host.endswith(".youtube.com") or host == "youtu.be":
        return "youtube"
    if host == "instagram.com" or host.endswith(".instagram.com"):
        return "instagram"
    if host == "threads.net" or host.endswith(".threads.net"):
        return "threads"
    return "unknown"


_SCRAPER_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
CACHE_TTL_SECONDS = 900  # 15 minutes TTL


def scrape_post_metrics(url: str, force_refresh: bool = False) -> dict[str, Any]:
    """Route a supported public URL to the appropriate scraper with 15-minute TTL cache."""
    import time

    if not force_refresh and url in _SCRAPER_CACHE:
        cached_time, cached_res = _SCRAPER_CACHE[url]
        if time.time() - cached_time < CACHE_TTL_SECONDS:
            return cached_res

    platform = _platform_for_url(url)
    try:
        if platform == "youtube":
            res = scrape_youtube(url)
        elif platform == "instagram":
            res = scrape_instagram_reel(url)
        elif platform == "threads":
            res = scrape_threads_post(url)
        else:
            raise ValueError("Unsupported social-media URL")
        
        if res.get("status") == "success":
            _SCRAPER_CACHE[url] = (time.time(), res)
        return res
    except Exception as exc:
        return {
            "platform": platform,
            "status": "error",
            "error": str(exc),
            "scraped_at": _timestamp(),
        }


if __name__ == "__main__":
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    ]
    for u in test_urls:
        print(f"Testing {u}:", scrape_post_metrics(u))
