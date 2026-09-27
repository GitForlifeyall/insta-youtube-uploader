import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.config import DB_PATH
from app.core.models import (
    Brand, BrandCreate, Profile, ProfileCreate,
    ScheduledPost, ScheduledPostCreate, ScheduledPostUpdate,
    PostStatus, PlatformType, PostType
)


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite database schema and seeds a default brand if empty."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS brands (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                color_badge TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                brand_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                account_handle TEXT NOT NULL,
                display_name TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (brand_id) REFERENCES brands (id) ON DELETE CASCADE
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id TEXT PRIMARY KEY,
                brand_id TEXT NOT NULL,
                target_platforms TEXT NOT NULL,
                post_type TEXT NOT NULL,
                media_paths TEXT NOT NULL,
                caption TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                music_query TEXT,
                share_to_facebook INTEGER DEFAULT 1,
                share_to_threads INTEGER DEFAULT 0,
                youtube_title TEXT,
                youtube_tags TEXT,
                error_log TEXT,
                published_urls TEXT,
                first_comment TEXT,
                FOREIGN KEY (brand_id) REFERENCES brands (id) ON DELETE CASCADE
            );
        """)
        # Safe migration for existing DB
        try:
            cursor.execute("ALTER TABLE scheduled_posts ADD COLUMN first_comment TEXT;")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE scheduled_posts ADD COLUMN audio_start_sec REAL;")
        except Exception:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitors (
                id TEXT PRIMARY KEY,
                brand_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                account_handle TEXT NOT NULL,
                display_name TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (brand_id) REFERENCES brands (id) ON DELETE CASCADE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitor_metrics (
                id TEXT PRIMARY KEY,
                competitor_id TEXT NOT NULL,
                followers INTEGER DEFAULT 0,
                total_posts INTEGER DEFAULT 0,
                recent_avg_views INTEGER DEFAULT 0,
                recorded_at TEXT NOT NULL,
                FOREIGN KEY (competitor_id) REFERENCES competitors (id) ON DELETE CASCADE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evergreen_posts (
                id TEXT PRIMARY KEY,
                brand_id TEXT NOT NULL,
                caption TEXT NOT NULL,
                media_paths TEXT NOT NULL,
                target_platforms TEXT NOT NULL,
                max_repeats INTEGER DEFAULT 3,
                times_posted INTEGER DEFAULT 0,
                last_posted_at TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (brand_id) REFERENCES brands (id) ON DELETE CASCADE
            );
        """)

        # High-Performance Database Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_brand_time ON scheduled_posts(brand_id, scheduled_time);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_status_time ON scheduled_posts(status, scheduled_time);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_competitors_brand ON competitors(brand_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evergreen_brand ON evergreen_posts(brand_id);")

        conn.commit()

        # Check if default brand should be seeded
        cursor.execute("SELECT COUNT(*) as count FROM brands")
        if cursor.fetchone()["count"] == 0:
            default_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO brands (id, name, color_badge, description, created_at) VALUES (?, ?, ?, ?, ?)",
                (default_id, "Main Brand", "#8ACE00", "Default brand workspace for lyric videos & reels", now)
            )
            # Default Instagram profile placeholder
            cursor.execute(
                "INSERT INTO profiles (id, brand_id, platform, account_handle, display_name, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), default_id, "instagram", "lulop.123", "Lulop Instagram", 1, now)
            )
            conn.commit()


# ================= BRANDS CRUD =================

def list_brands() -> List[Brand]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM brands ORDER BY created_at ASC")
        rows = cursor.fetchall()
        brands = []
        for r in rows:
            cursor.execute("SELECT * FROM profiles WHERE brand_id = ? ORDER BY created_at ASC", (r["id"],))
            p_rows = cursor.fetchall()
            profiles = [
                Profile(
                    id=p["id"],
                    brand_id=p["brand_id"],
                    platform=PlatformType(p["platform"]),
                    account_handle=p["account_handle"],
                    display_name=p["display_name"],
                    is_active=bool(p["is_active"]),
                    created_at=p["created_at"]
                )
                for p in p_rows
            ]
            brands.append(Brand(
                id=r["id"],
                name=r["name"],
                color_badge=r["color_badge"],
                description=r["description"],
                created_at=r["created_at"],
                profiles=profiles
            ))
        return brands


def get_brand(brand_id: str) -> Optional[Brand]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM brands WHERE id = ?", (brand_id,))
        r = cursor.fetchone()
        if not r:
            return None
        cursor.execute("SELECT * FROM profiles WHERE brand_id = ? ORDER BY created_at ASC", (r["id"],))
        p_rows = cursor.fetchall()
        profiles = [
            Profile(
                id=p["id"],
                brand_id=p["brand_id"],
                platform=PlatformType(p["platform"]),
                account_handle=p["account_handle"],
                display_name=p["display_name"],
                is_active=bool(p["is_active"]),
                created_at=p["created_at"]
            )
            for p in p_rows
        ]
        return Brand(
            id=r["id"],
            name=r["name"],
            color_badge=r["color_badge"],
            description=r["description"],
            created_at=r["created_at"],
            profiles=profiles
        )


def create_brand(data: BrandCreate) -> Brand:
    brand_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO brands (id, name, color_badge, description, created_at) VALUES (?, ?, ?, ?, ?)",
            (brand_id, data.name, data.color_badge, data.description, now)
        )
        conn.commit()
    return Brand(id=brand_id, name=data.name, color_badge=data.color_badge, description=data.description, created_at=now, profiles=[])


def delete_brand(brand_id: str) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM profiles WHERE brand_id = ?", (brand_id,))
        cursor.execute("DELETE FROM scheduled_posts WHERE brand_id = ?", (brand_id,))
        cursor.execute("DELETE FROM brands WHERE id = ?", (brand_id,))
        conn.commit()
        return cursor.rowcount > 0


def update_brand(brand_id: str, name: str, color_badge: Optional[str] = None) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        if color_badge:
            cursor.execute("UPDATE brands SET name = ?, color_badge = ? WHERE id = ?", (name, color_badge, brand_id))
        else:
            cursor.execute("UPDATE brands SET name = ? WHERE id = ?", (name, brand_id))
        conn.commit()
        return cursor.rowcount > 0



# ================= PROFILES CRUD =================

def add_profile_to_brand(brand_id: str, data: ProfileCreate) -> Profile:
    profile_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO profiles (id, brand_id, platform, account_handle, display_name, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (profile_id, brand_id, data.platform.value, data.account_handle, data.display_name, int(data.is_active), now)
        )
        conn.commit()
    return Profile(id=profile_id, brand_id=brand_id, platform=data.platform, account_handle=data.account_handle, display_name=data.display_name, is_active=data.is_active, created_at=now)


def delete_profile(profile_id: str) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        conn.commit()
        return cursor.rowcount > 0


# ================= SCHEDULED POSTS CRUD =================

def _row_to_post(r: sqlite3.Row) -> ScheduledPost:
    return ScheduledPost(
        id=r["id"],
        brand_id=r["brand_id"],
        target_platforms=[PlatformType(p) for p in json.loads(r["target_platforms"])],
        post_type=PostType(r["post_type"]),
        media_paths=json.loads(r["media_paths"]),
        caption=r["caption"],
        scheduled_time=r["scheduled_time"],
        status=PostStatus(r["status"]),
        created_at=r["created_at"],
        music_query=r["music_query"],
        audio_start_sec=r["audio_start_sec"] if "audio_start_sec" in r.keys() else None,
        share_to_facebook=bool(r["share_to_facebook"]),
        share_to_threads=bool(r["share_to_threads"]),
        youtube_title=r["youtube_title"],
        youtube_tags=json.loads(r["youtube_tags"]) if r["youtube_tags"] else [],
        error_log=r["error_log"],
        published_urls=json.loads(r["published_urls"]) if r["published_urls"] else {},
        first_comment=r["first_comment"] if "first_comment" in r.keys() else None
    )


def list_posts(brand_id: Optional[str] = None, status: Optional[str] = None) -> List[ScheduledPost]:
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM scheduled_posts WHERE 1=1"
        params = []
        if brand_id:
            query += " AND brand_id = ?"
            params.append(brand_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY scheduled_time ASC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [_row_to_post(r) for r in rows]


def get_post(post_id: str) -> Optional[ScheduledPost]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scheduled_posts WHERE id = ?", (post_id,))
        row = cursor.fetchone()
        return _row_to_post(row) if row else None


def create_post(data: ScheduledPostCreate) -> ScheduledPost:
    post_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scheduled_posts (
                id, brand_id, target_platforms, post_type, media_paths, caption,
                scheduled_time, status, created_at, music_query, audio_start_sec, share_to_facebook,
                share_to_threads, youtube_title, youtube_tags, first_comment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            post_id,
            data.brand_id,
            json.dumps([p.value for p in data.target_platforms]),
            data.post_type.value,
            json.dumps(data.media_paths),
            data.caption,
            data.scheduled_time,
            PostStatus.SCHEDULED.value,
            now,
            data.music_query,
            data.audio_start_sec,
            int(data.share_to_facebook),
            int(data.share_to_threads),
            data.youtube_title,
            json.dumps(data.youtube_tags or []),
            data.first_comment
        ))
        conn.commit()
    return get_post(post_id)


def update_post_status(post_id: str, status: PostStatus, error_log: Optional[str] = None, published_urls: Optional[Dict[str, Any]] = None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE scheduled_posts SET status = ?, error_log = ?, published_urls = ? WHERE id = ?",
            (status.value, error_log, json.dumps(published_urls or {}), post_id)
        )
        conn.commit()


def delete_post(post_id: str) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scheduled_posts WHERE id = ?", (post_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_due_posts(current_iso: str) -> List[ScheduledPost]:
    """Finds all posts whose scheduled_time <= current_iso and status == 'scheduled'."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM scheduled_posts WHERE status = ? AND scheduled_time <= ? ORDER BY scheduled_time ASC",
            (PostStatus.SCHEDULED.value, current_iso)
        )
        rows = cursor.fetchall()
        return [_row_to_post(r) for r in rows]


# ================= COMPETITOR CRUD =================

def list_competitors(brand_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT c.*,
                   COALESCE(m.followers, 0) as followers,
                   COALESCE(m.total_posts, 0) as total_posts,
                   COALESCE(m.recent_avg_views, 0) as recent_avg_views,
                   m.recorded_at as last_scraped_at
            FROM competitors c
            LEFT JOIN competitor_metrics m ON m.id = (
                SELECT id FROM competitor_metrics
                WHERE competitor_id = c.id
                ORDER BY recorded_at DESC LIMIT 1
            )
            WHERE 1=1
        """
        params = []
        if brand_id:
            query += " AND c.brand_id = ?"
            params.append(brand_id)
        query += " ORDER BY c.created_at DESC"
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]


def add_competitor(brand_id: str, platform: str, account_handle: str, display_name: Optional[str] = None) -> Dict[str, Any]:
    comp_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    clean_handle = account_handle.strip().replace("https://", "").replace("www.", "").rstrip("/")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO competitors (id, brand_id, platform, account_handle, display_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (comp_id, brand_id, platform.lower(), clean_handle, display_name or clean_handle, now))
        conn.commit()
    return {
        "id": comp_id,
        "brand_id": brand_id,
        "platform": platform.lower(),
        "account_handle": clean_handle,
        "display_name": display_name or clean_handle,
        "created_at": now
    }


def delete_competitor(competitor_id: str) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM competitors WHERE id = ?", (competitor_id,))
        conn.commit()
        return cursor.rowcount > 0


def record_competitor_metrics(competitor_id: str, followers: int, total_posts: int, recent_avg_views: int):
    metric_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO competitor_metrics (id, competitor_id, followers, total_posts, recent_avg_views, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (metric_id, competitor_id, followers, total_posts, recent_avg_views, now))
        conn.commit()


# ================= EVERGREEN POSTS CRUD =================

def list_evergreen_posts(brand_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM evergreen_posts WHERE 1=1"
        params = []
        if brand_id:
            query += " AND brand_id = ?"
            params.append(brand_id)
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        res = []
        for r in cursor.fetchall():
            d = dict(r)
            d["media_paths"] = json.loads(d["media_paths"]) if d["media_paths"] else []
            d["target_platforms"] = json.loads(d["target_platforms"]) if d["target_platforms"] else []
            res.append(d)
        return res


def add_evergreen_post(brand_id: str, caption: str, media_paths: List[str], target_platforms: List[str], max_repeats: int = 3) -> Dict[str, Any]:
    post_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO evergreen_posts (
                id, brand_id, caption, media_paths, target_platforms, max_repeats, times_posted, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 0, 1, ?)
        """, (post_id, brand_id, caption, json.dumps(media_paths), json.dumps(target_platforms), max_repeats, now))
        conn.commit()
    return {
        "id": post_id,
        "brand_id": brand_id,
        "caption": caption,
        "media_paths": media_paths,
        "target_platforms": target_platforms,
        "max_repeats": max_repeats,
        "times_posted": 0,
        "is_active": True,
        "created_at": now
    }


def delete_evergreen_post(evergreen_id: str) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM evergreen_posts WHERE id = ?", (evergreen_id,))
        conn.commit()
        return cursor.rowcount > 0


def increment_evergreen_usage(evergreen_id: str):
    now = datetime.now().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE evergreen_posts
            SET times_posted = times_posted + 1, last_posted_at = ?
            WHERE id = ?
        """, (now, evergreen_id))
        conn.commit()

