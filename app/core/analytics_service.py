"""
📈 Analytics & Performance Tracking Service
Aggregates post history, published content KPIs, engagement rates, and tracked links.
"""

import sqlite3
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from app.core.database import get_connection, list_brands

logger = logging.getLogger("analytics_service")


def get_brand_analytics_summary(brand_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Total Published Posts from post_history
        cursor.execute("SELECT COUNT(*) as cnt FROM post_history;")
        total_published = cursor.fetchone()["cnt"]

        # 2. Breakdown by media_type
        cursor.execute("""
            SELECT media_type, COUNT(*) as cnt
            FROM post_history
            GROUP BY media_type;
        """)
        type_counts = {r["media_type"]: r["cnt"] for r in cursor.fetchall()}

        # 3. Scheduled / Upcoming posts count
        cursor.execute("""
            SELECT status, COUNT(*) as cnt
            FROM scheduled_posts
            GROUP BY status;
        """)
        status_counts = {r["status"]: r["cnt"] for r in cursor.fetchall()}

        # 4. Snapshots aggregation (views, likes, comments)
        cursor.execute("""
            SELECT SUM(views) as total_views, SUM(likes) as total_likes, SUM(comments) as total_comments
            FROM analytics_snapshots;
        """)
        snap_row = cursor.fetchone()
        views = snap_row["total_views"] or 0
        likes = snap_row["total_likes"] or 0
        comments = snap_row["total_comments"] or 0

        # Engagement Rate = ((likes + comments) / views) * 100
        engagement_rate = round(((likes + comments) / views) * 100.0, 2) if views > 0 else 0.0

        # 5. Recent Post History
        cursor.execute("""
            SELECT * FROM post_history
            ORDER BY id DESC
            LIMIT 10;
        """)
        recent_posts = [dict(r) for r in cursor.fetchall()]

        return {
            "summary": {
                "total_published": total_published,
                "reels_count": type_counts.get("reel", 0),
                "posts_count": type_counts.get("post", 0) + type_counts.get("carousel", 0),
                "stories_count": type_counts.get("story", 0),
                "scheduled_in_queue": status_counts.get("scheduled", 0),
                "drafts_count": status_counts.get("draft", 0),
                "total_views": views,
                "total_likes": likes,
                "total_comments": comments,
                "engagement_rate": engagement_rate
            },
            "recent_posts": recent_posts
        }


def add_tracked_link(
    brand_id: str,
    platform: str,
    url: str,
    title: Optional[str] = None,
    post_id: Optional[str] = None
) -> str:
    link_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tracked_links (id, brand_id, platform, url, title, post_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (link_id, brand_id, platform, url, title or url, post_id, now))
        conn.commit()
    return link_id


def record_snapshot(
    brand_id: str,
    platform: str,
    views: int = 0,
    likes: int = 0,
    comments: int = 0,
    tracked_link_id: Optional[str] = None
):
    snap_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analytics_snapshots (id, tracked_link_id, brand_id, platform, views, likes, comments, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (snap_id, tracked_link_id, brand_id, platform, views, likes, comments, now))
        conn.commit()


def list_tracked_links(brand_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM tracked_links WHERE 1=1"
        params = []
        if brand_id:
            query += " AND brand_id = ?"
            params.append(brand_id)
        query += " ORDER BY created_at DESC;"
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]
