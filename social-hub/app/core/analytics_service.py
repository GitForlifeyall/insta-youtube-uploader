import sqlite3
import uuid
import json
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.config import DB_PATH, NEW_LYRICS_DIR

logger = logging.getLogger("analytics_service")

# Import Codex public_scrapers from new-lyrics-2
if str(NEW_LYRICS_DIR) not in sys.path:
    sys.path.insert(0, str(NEW_LYRICS_DIR))

try:
    from services.analytics.public_scrapers import scrape_post_metrics
except ImportError:
    scrape_post_metrics = None


def init_analytics_tables():
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracked_links (
                id TEXT PRIMARY KEY,
                brand_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                post_id TEXT,
                created_at TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_snapshots (
                id TEXT PRIMARY KEY,
                tracked_link_id TEXT,
                brand_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                recorded_at TEXT NOT NULL
            );
        """)
        conn.commit()


def add_tracked_link(brand_id: str, platform: str, url: str, title: Optional[str] = None, post_id: Optional[str] = None) -> str:
    link_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tracked_links (id, brand_id, platform, url, title, post_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (link_id, brand_id, platform, url, title or url, post_id, now))
        conn.commit()
    return link_id


def record_snapshot(brand_id: str, platform: str, views: int, likes: int, comments: int, tracked_link_id: Optional[str] = None):
    snapshot_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analytics_snapshots (id, tracked_link_id, brand_id, platform, views, likes, comments, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (snapshot_id, tracked_link_id, brand_id, platform, views, likes, comments, now))
        conn.commit()


def get_brand_analytics_summary(brand_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
    """Calculates overall metrics, platform breakdown, and daily timeline."""
    init_analytics_tables()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query recent snapshots
        query = "SELECT * FROM analytics_snapshots WHERE recorded_at >= ?"
        params = [cutoff]
        if brand_id:
            query += " AND brand_id = ?"
            params.append(brand_id)
        query += " ORDER BY recorded_at ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        total_views = sum(r["views"] for r in rows)
        total_likes = sum(r["likes"] for r in rows)
        total_comments = sum(r["comments"] for r in rows)
        engagement_rate = round(((total_likes + total_comments) / total_views) * 100.0, 2) if total_views > 0 else 0.0

        # Platform breakdown
        platforms = {"youtube": 0, "instagram": 0, "threads": 0, "facebook": 0}
        for r in rows:
            plat = r["platform"].lower()
            if plat in platforms:
                platforms[plat] += r["views"]

        # Timeline grouped by date
        timeline = {}
        for r in rows:
            date_key = r["recorded_at"][:10]  # YYYY-MM-DD
            if date_key not in timeline:
                timeline[date_key] = {"date": date_key, "views": 0, "likes": 0, "comments": 0}
            timeline[date_key]["views"] += r["views"]
            timeline[date_key]["likes"] += r["likes"]
            timeline[date_key]["comments"] += r["comments"]

        # Top content leaderboard (latest snapshot per tracked link)
        cursor.execute("""
            SELECT t.id, t.title, t.platform, t.url, s.views, s.likes, s.comments, s.recorded_at
            FROM tracked_links t
            LEFT JOIN analytics_snapshots s ON s.tracked_link_id = t.id
            WHERE s.id IN (
                SELECT id FROM analytics_snapshots
                WHERE tracked_link_id = t.id
                ORDER BY recorded_at DESC LIMIT 1
            )
            ORDER BY s.views DESC LIMIT 10
        """)
        top_rows = cursor.fetchall()
        top_posts = []
        for tr in top_rows:
            v = tr["views"] or 0
            l = tr["likes"] or 0
            c = tr["comments"] or 0
            rate = round(((l + c) / v) * 100.0, 2) if v > 0 else 0.0
            top_posts.append({
                "id": tr["id"],
                "title": tr["title"] or tr["url"],
                "platform": tr["platform"],
                "url": tr["url"],
                "views": v,
                "likes": l,
                "comments": c,
                "engagement_rate": rate,
                "recorded_at": tr["recorded_at"]
            })

        return {
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "engagement_rate": engagement_rate,
            "platform_breakdown": platforms,
            "timeline": sorted(list(timeline.values()), key=lambda x: x["date"]),
            "top_posts": top_posts,
            "days_tracked": days
        }


def list_tracked_links(brand_id: Optional[str] = None) -> List[Dict[str, Any]]:
    init_analytics_tables()
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM tracked_links WHERE 1=1"
        params = []
        if brand_id:
            query += " AND brand_id = ?"
            params.append(brand_id)
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]


def refresh_all_tracked_links() -> Dict[str, Any]:
    """Runs zero-login scrapers across all registered links and records new metric snapshots."""
    if not scrape_post_metrics:
        return {"status": "skipped", "message": "Scraper module not loaded"}

    links = list_tracked_links()
    results = []

    for item in links:
        url = item.get("url")
        if not url:
            continue
        try:
            metrics = scrape_post_metrics(url)
            if metrics.get("status") == "success":
                views = metrics.get("views", 0)
                likes = metrics.get("likes", 0)
                comments = metrics.get("comments", 0)
                record_snapshot(
                    brand_id=item["brand_id"],
                    platform=item["platform"],
                    views=views,
                    likes=likes,
                    comments=comments,
                    tracked_link_id=item["id"]
                )
                results.append({"url": url, "status": "updated", "views": views, "likes": likes})
            else:
                results.append({"url": url, "status": "failed", "error": metrics.get("error")})
        except Exception as e:
            results.append({"url": url, "status": "error", "error": str(e)})

    return {"status": "success", "processed_count": len(results), "details": results}
