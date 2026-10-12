"""
SQLite Database module for Social Hub & Instagram Uploader.
Stores:
  1. Complete Account Profiles & Credentials (accounts table)
  2. Complete log of all published posts/reels/stories (post_history table)
  3. Brand Workspaces (brands table)
  4. Platform Profiles per Brand (profiles table)
  5. Visual Content Planner & Scheduled Queue (scheduled_posts table)
  6. Evergreen Content Recycling Pool (evergreen_posts table)
  7. Analytics & Tracked Links (tracked_links, analytics_snapshots tables)
"""
import sqlite3
import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from app.config import BASE_DIR, SESSIONS_DIR
from app.core.models import (
    Brand, BrandCreate, Profile, ProfileCreate,
    ScheduledPost, ScheduledPostCreate, ScheduledPostUpdate,
    PostStatus, PlatformType, PostType
)

DB_PATH = BASE_DIR / "uploader.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Accounts Table storing username, password, session_id, proxy & profile info
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                username TEXT PRIMARY KEY,
                password TEXT,
                session_id TEXT,
                proxy TEXT,
                user_id TEXT,
                full_name TEXT,
                profile_pic_url TEXT,
                totp_secret TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)

        # 2. Post / Upload History Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS post_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                media_type TEXT NOT NULL,
                url TEXT NOT NULL,
                code TEXT,
                media_id TEXT,
                caption TEXT,
                proxy_used TEXT,
                created_at TEXT NOT NULL
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_username ON post_history(username);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_created ON post_history(created_at DESC);")

        # 3. Brands Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS brands (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                color_badge TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL
            );
        """)

        # 4. Profiles Table (Linked accounts per brand)
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

        # 5. Scheduled Posts (Planner & Auto-Publisher Queue)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id TEXT PRIMARY KEY,
                brand_id TEXT NOT NULL,
                target_platforms TEXT NOT NULL,
                post_type TEXT NOT NULL,
                media_paths TEXT NOT NULL,
                caption TEXT NOT NULL,
                first_comment TEXT,
                scheduled_time TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                music_query TEXT,
                audio_cluster_id TEXT,
                audio_start_sec REAL DEFAULT 0.0,
                music_volume REAL DEFAULT 10.0,
                error_log TEXT,
                published_urls TEXT,
                FOREIGN KEY (brand_id) REFERENCES brands (id) ON DELETE CASCADE
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_brand_time ON scheduled_posts(brand_id, scheduled_time);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_status_time ON scheduled_posts(status, scheduled_time);")

        # 6. Evergreen Recycling Pool
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

        # 7. Analytics & Tracked Links
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

        # 8. Account Activity Logs & Safe Daily Limit Tracker
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action_type TEXT NOT NULL,
                target_identifier TEXT,
                status TEXT NOT NULL,
                details TEXT,
                proxy_used TEXT,
                created_at TEXT NOT NULL
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_user_created ON account_activity_logs(username, created_at DESC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_created ON account_activity_logs(created_at DESC);")

        # Safe column additions if migrating
        for col_def in [
            "ALTER TABLE accounts ADD COLUMN totp_secret TEXT;",
            "ALTER TABLE scheduled_posts ADD COLUMN audio_cluster_id TEXT;",
            "ALTER TABLE scheduled_posts ADD COLUMN music_volume REAL DEFAULT 10.0;",
            "ALTER TABLE scheduled_posts ADD COLUMN first_comment TEXT;",
            "ALTER TABLE scheduled_posts ADD COLUMN audio_start_sec REAL DEFAULT 0.0;"
        ]:
            try:
                cursor.execute(col_def)
            except Exception:
                pass

        conn.commit()

    # Sync sessions & seed default brand
    _sync_session_files_to_db()
    _seed_default_brand_if_empty()


def _sync_session_files_to_db():
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        for f in SESSIONS_DIR.glob("session_*.json"):
            username = f.stem.replace("session_", "").strip()
            if username:
                cursor.execute("""
                    INSERT OR IGNORE INTO accounts (username, created_at, updated_at)
                    VALUES (?, ?, ?);
                """, (username, now, now))
        conn.commit()


def _seed_default_brand_if_empty():
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM brands;")
        row = cursor.fetchone()
        if row and row["cnt"] == 0:
            cursor.execute("SELECT username FROM accounts LIMIT 5;")
            accs = [r["username"] for r in cursor.fetchall()]
            
            # Create default brand
            brand_id = "default-brand-1"
            brand_name = accs[0] if accs else "Main Workspace"
            cursor.execute("""
                INSERT INTO brands (id, name, color_badge, description, created_at)
                VALUES (?, ?, ?, ?, ?);
            """, (brand_id, brand_name, "#8ACE00", "Default Brand Workspace", now))

            # Associate found accounts to this brand
            for username in accs:
                prof_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO profiles (id, brand_id, platform, account_handle, display_name, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, 1, ?);
                """, (prof_id, brand_id, "instagram", username, username, now))

            conn.commit()


# ==========================================
# Account & Credential Management
# ==========================================

def save_account_profile(
    username: str,
    password: Optional[str] = None,
    session_id: Optional[str] = None,
    totp_secret: Optional[str] = None,
    proxy: Optional[str] = None,
    user_id: Optional[str] = None,
    full_name: Optional[str] = None,
    profile_pic_url: Optional[str] = None
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE username = ?", (username,))
        existing = cursor.fetchone()

        if existing:
            existing_dict = dict(existing)
            new_password = password if password is not None else existing_dict.get("password")
            new_session_id = session_id if session_id is not None else existing_dict.get("session_id")
            new_totp = totp_secret if totp_secret is not None else existing_dict.get("totp_secret")
            new_proxy = proxy if proxy is not None else existing_dict.get("proxy")
            new_user_id = user_id if user_id is not None else existing_dict.get("user_id")
            new_full_name = full_name if full_name is not None else existing_dict.get("full_name")
            new_pic = profile_pic_url if profile_pic_url is not None else existing_dict.get("profile_pic_url")

            cursor.execute("""
                UPDATE accounts
                SET password = ?, session_id = ?, totp_secret = ?, proxy = ?,
                    user_id = ?, full_name = ?, profile_pic_url = ?, updated_at = ?
                WHERE username = ?;
            """, (new_password, new_session_id, new_totp, new_proxy, new_user_id, new_full_name, new_pic, now, username))
        else:
            cursor.execute("""
                INSERT INTO accounts (
                    username, password, session_id, totp_secret, proxy,
                    user_id, full_name, profile_pic_url, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (username, password, session_id, totp_secret, proxy, user_id, full_name, profile_pic_url, now, now))

        conn.commit()

    return get_account(username) or {}


def get_account(username: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE username = ?", (username,))
        row = cursor.fetchone()
        if not row:
            return None
        return dict(row)


def list_accounts() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts ORDER BY updated_at DESC;")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def delete_account(username: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM accounts WHERE username = ?", (username,))
        cursor.execute("DELETE FROM profiles WHERE account_handle = ?", (username,))
        conn.commit()
        return cursor.rowcount > 0


def get_all_db_accounts() -> List[Dict[str, Any]]:
    """Alias for list_accounts() returning all accounts registered in database."""
    return list_accounts()


def delete_account_from_db(username: str) -> bool:
    """Alias for delete_account(username)."""
    return delete_account(username)


def format_proxy_string(proxy: Optional[str]) -> Optional[str]:
    """Formats various proxy formats (ip:port:user:pass or URI) into a valid URL."""
    if not proxy or not str(proxy).strip():
        return None
    p = str(proxy).strip()
    if p.startswith(("http://", "https://", "socks5://", "socks4://")):
        return p
    parts = p.split(":")
    if len(parts) == 4:
        host, port, user, pwd = parts
        return f"http://{user}:{pwd}@{host}:{port}"
    if "@" in p:
        return f"http://{p}"
    return f"http://{p}"


def set_account_proxy(username: str, proxy: str):
    save_account_profile(username, proxy=proxy)


def get_account_proxy(username: str) -> Optional[str]:
    acc = get_account(username)
    if acc:
        return acc.get("proxy")
    return None


def record_post(
    username: str,
    media_type: str,
    url: str,
    code: Optional[str] = None,
    media_id: Optional[str] = None,
    caption: Optional[str] = None,
    proxy_used: Optional[str] = None
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO post_history (
                username, media_type, url, code, media_id, caption, proxy_used, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            username,
            media_type,
            url,
            code,
            media_id,
            caption or "",
            proxy_used,
            now
        ))
        conn.commit()
        return cursor.lastrowid


def get_post_history(username: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if username:
            cursor.execute("""
                SELECT * FROM post_history
                WHERE username = ?
                ORDER BY id DESC
                LIMIT ?;
            """, (username, limit))
        else:
            cursor.execute("""
                SELECT * FROM post_history
                ORDER BY id DESC
                LIMIT ?;
            """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# ==========================================
# Brand & Profile Management
# ==========================================

def list_brands() -> List[Brand]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM brands ORDER BY name ASC;")
        brand_rows = cursor.fetchall()
        results = []
        for b in brand_rows:
            cursor.execute("SELECT * FROM profiles WHERE brand_id = ?;", (b["id"],))
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
                ) for p in p_rows
            ]
            results.append(Brand(
                id=b["id"],
                name=b["name"],
                color_badge=b["color_badge"],
                description=b["description"],
                created_at=b["created_at"],
                profiles=profiles
            ))
        return results


def get_brand(brand_id: str) -> Optional[Brand]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM brands WHERE id = ?;", (brand_id,))
        b = cursor.fetchone()
        if not b:
            return None
        cursor.execute("SELECT * FROM profiles WHERE brand_id = ?;", (brand_id,))
        profiles = [
            Profile(
                id=p["id"],
                brand_id=p["brand_id"],
                platform=PlatformType(p["platform"]),
                account_handle=p["account_handle"],
                display_name=p["display_name"],
                is_active=bool(p["is_active"]),
                created_at=p["created_at"]
            ) for p in cursor.fetchall()
        ]
        return Brand(
            id=b["id"],
            name=b["name"],
            color_badge=b["color_badge"],
            description=b["description"],
            created_at=b["created_at"],
            profiles=profiles
        )


def create_brand(brand: BrandCreate) -> Brand:
    brand_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO brands (id, name, color_badge, description, created_at)
            VALUES (?, ?, ?, ?, ?);
        """, (brand_id, brand.name, brand.color_badge, brand.description, now))
        conn.commit()
    return Brand(
        id=brand_id,
        name=brand.name,
        color_badge=brand.color_badge,
        description=brand.description,
        created_at=now,
        profiles=[]
    )


def delete_brand(brand_id: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM brands WHERE id = ?;", (brand_id,))
        cursor.execute("DELETE FROM profiles WHERE brand_id = ?;", (brand_id,))
        cursor.execute("DELETE FROM scheduled_posts WHERE brand_id = ?;", (brand_id,))
        cursor.execute("DELETE FROM evergreen_posts WHERE brand_id = ?;", (brand_id,))
        conn.commit()
        return cursor.rowcount > 0


def add_profile_to_brand(brand_id: str, profile: ProfileCreate) -> Profile:
    prof_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO profiles (id, brand_id, platform, account_handle, display_name, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (prof_id, brand_id, profile.platform.value, profile.account_handle, profile.display_name or profile.account_handle, 1 if profile.is_active else 0, now))
        conn.commit()
    return Profile(
        id=prof_id,
        brand_id=brand_id,
        platform=profile.platform,
        account_handle=profile.account_handle,
        display_name=profile.display_name or profile.account_handle,
        is_active=profile.is_active,
        created_at=now
    )


def delete_profile(profile_id: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM profiles WHERE id = ?;", (profile_id,))
        conn.commit()
        return cursor.rowcount > 0


# ==========================================
# Scheduled Posts & Planner CRUD
# ==========================================

def _row_to_scheduled_post(row: sqlite3.Row) -> ScheduledPost:
    return ScheduledPost(
        id=row["id"],
        brand_id=row["brand_id"],
        target_platforms=[PlatformType(p) for p in json.loads(row["target_platforms"])],
        post_type=PostType(row["post_type"]),
        media_paths=json.loads(row["media_paths"]),
        caption=row["caption"],
        first_comment=row["first_comment"],
        scheduled_time=row["scheduled_time"],
        status=PostStatus(row["status"]),
        created_at=row["created_at"],
        music_query=row["music_query"],
        audio_cluster_id=row["audio_cluster_id"],
        audio_start_sec=row["audio_start_sec"],
        music_volume=row["music_volume"] if row["music_volume"] is not None else 10.0,
        error_log=row["error_log"],
        published_urls=json.loads(row["published_urls"]) if row["published_urls"] else None
    )


def create_post(post: ScheduledPostCreate) -> ScheduledPost:
    post_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    target_plats = [p.value for p in post.target_platforms]
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scheduled_posts (
                id, brand_id, target_platforms, post_type, media_paths, caption,
                first_comment, scheduled_time, status, created_at, music_query,
                audio_cluster_id, audio_start_sec, music_volume
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            post_id, post.brand_id, json.dumps(target_plats), post.post_type.value,
            json.dumps(post.media_paths), post.caption, post.first_comment,
            post.scheduled_time, post.status.value, now, post.music_query,
            post.audio_cluster_id, post.audio_start_sec, post.music_volume
        ))
        conn.commit()
    return get_post(post_id)  # type: ignore


def get_post(post_id: str) -> Optional[ScheduledPost]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scheduled_posts WHERE id = ?;", (post_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return _row_to_scheduled_post(row)


def list_posts(brand_id: Optional[str] = None, status: Optional[str] = None) -> List[ScheduledPost]:
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM scheduled_posts WHERE 1=1"
        params: List[Any] = []
        if brand_id:
            query += " AND brand_id = ?"
            params.append(brand_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY scheduled_time ASC;"
        cursor.execute(query, params)
        return [_row_to_scheduled_post(row) for row in cursor.fetchall()]


def update_post_status(
    post_id: str,
    status: PostStatus,
    error_log: Optional[str] = None,
    published_urls: Optional[Dict[str, Any]] = None
):
    with get_connection() as conn:
        cursor = conn.cursor()
        urls_json = json.dumps(published_urls) if published_urls else None
        cursor.execute("""
            UPDATE scheduled_posts
            SET status = ?, error_log = ?, published_urls = ?
            WHERE id = ?;
        """, (status.value, error_log, urls_json, post_id))
        conn.commit()


def delete_post(post_id: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scheduled_posts WHERE id = ?;", (post_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_due_posts(now_iso: Optional[str] = None) -> List[ScheduledPost]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM scheduled_posts
            WHERE status = ?
            ORDER BY scheduled_time ASC;
        """, (PostStatus.SCHEDULED.value,))
        rows = cursor.fetchall()
        now_utc = datetime.now(timezone.utc)
        now_local = datetime.now()
        due = []
        for row in rows:
            post = _row_to_scheduled_post(row)
            try:
                raw_time = post.scheduled_time.strip().replace("Z", "+00:00")
                dt = datetime.fromisoformat(raw_time)
                if dt.tzinfo is not None:
                    if dt <= now_utc:
                        due.append(post)
                else:
                    if dt <= now_local:
                        due.append(post)
            except Exception:
                if now_iso and post.scheduled_time <= now_iso:
                    due.append(post)
        return due


# ==========================================
# Evergreen Content Pool
# ==========================================

def list_evergreen_posts(brand_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM evergreen_posts WHERE 1=1"
        params = []
        if brand_id:
            query += " AND brand_id = ?"
            params.append(brand_id)
        query += " ORDER BY created_at DESC;"
        cursor.execute(query, params)
        results = []
        for r in cursor.fetchall():
            results.append({
                "id": r["id"],
                "brand_id": r["brand_id"],
                "caption": r["caption"],
                "media_paths": json.loads(r["media_paths"]),
                "target_platforms": json.loads(r["target_platforms"]),
                "max_repeats": r["max_repeats"],
                "times_posted": r["times_posted"],
                "last_posted_at": r["last_posted_at"],
                "is_active": bool(r["is_active"]),
                "created_at": r["created_at"]
            })
        return results


def add_evergreen_post(
    brand_id: str,
    caption: str,
    media_paths: List[str],
    target_platforms: List[str],
    max_repeats: int = 3
) -> Dict[str, Any]:
    post_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO evergreen_posts (
                id, brand_id, caption, media_paths, target_platforms, max_repeats, times_posted, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 0, 1, ?);
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
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM evergreen_posts WHERE id = ?;", (evergreen_id,))
        conn.commit()
        return cursor.rowcount > 0


def increment_evergreen_usage(evergreen_id: str):
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE evergreen_posts
            SET times_posted = times_posted + 1, last_posted_at = ?
            WHERE id = ?;
        """, (now, evergreen_id))
        conn.commit()


# ==========================================
# 8. ACCOUNT DAILY ACTIVITY & SAFETY LIMITS
# ==========================================

def record_account_activity(
    username: str,
    action_type: str,
    target_identifier: str = "",
    status: str = "passed",
    details: str = "",
    proxy_used: str = ""
) -> int:
    """
    Records an engagement action (like, save, comment, follow, repost, story) in SQLite.
    status can be: 'passed' (consumed an IG action), 'skipped', or 'failed'.
    """
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO account_activity_logs (
                username, action_type, target_identifier, status, details, proxy_used, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (username, action_type, target_identifier, status, details, proxy_used or "", now))
        conn.commit()
        return cursor.lastrowid


def get_account_daily_activity(
    username: str,
    safe_limit: int = 30,
    hours: int = 24
) -> Dict[str, Any]:
    """
    Calculates passed engagement actions in the last `hours` (rolling window) for an account.
    Returns whether the safe limit is reached, remaining actions, and breakdown.
    Note: Regular scheduled/manual posting is EXEMPT from this limit.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        # Only passed engagement actions count toward Instagram rate limit safety
        cursor.execute("""
            SELECT action_type, COUNT(*) as cnt
            FROM account_activity_logs
            WHERE username = ? AND status = 'passed' AND created_at >= ?
            GROUP BY action_type;
        """, (username, cutoff))
        rows = cursor.fetchall()

    breakdown = {}
    total_passed = 0
    for r in rows:
        act = r["action_type"]
        cnt = r["cnt"]
        breakdown[act] = cnt
        total_passed += cnt

    remaining = max(0, safe_limit - total_passed)
    is_limit_reached = total_passed >= safe_limit

    return {
        "username": username,
        "actions_today": total_passed,
        "safe_limit": safe_limit,
        "remaining": remaining,
        "is_limit_reached": is_limit_reached,
        "breakdown": breakdown,
        "window_hours": hours
    }


def get_all_accounts_daily_activity(
    safe_limit: int = 30,
    hours: int = 24
) -> Dict[str, Any]:
    """
    Returns daily activity statistics across all registered accounts.
    """
    accounts = list_accounts()
    account_stats = {}
    total_swarm_actions_today = 0
    accounts_at_limit_count = 0

    for acc in accounts:
        uname = acc["username"]
        stat = get_account_daily_activity(uname, safe_limit=safe_limit, hours=hours)
        account_stats[uname] = stat
        total_swarm_actions_today += stat["actions_today"]
        if stat["is_limit_reached"]:
            accounts_at_limit_count += 1

    return {
        "accounts": account_stats,
        "total_swarm_actions_today": total_swarm_actions_today,
        "accounts_at_limit_count": accounts_at_limit_count,
        "safe_limit_default": safe_limit,
        "window_hours": hours
    }


def get_recent_activity_logs(
    limit: int = 50,
    username: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves the most recent activity logs across all or a specific account.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        if username:
            cursor.execute("""
                SELECT id, username, action_type, target_identifier, status, details, proxy_used, created_at
                FROM account_activity_logs
                WHERE username = ?
                ORDER BY created_at DESC
                LIMIT ?;
            """, (username, limit))
        else:
            cursor.execute("""
                SELECT id, username, action_type, target_identifier, status, details, proxy_used, created_at
                FROM account_activity_logs
                ORDER BY created_at DESC
                LIMIT ?;
            """, (limit,))
        
        rows = cursor.fetchall()
        return [
            {
                "id": r["id"],
                "username": r["username"],
                "action_type": r["action_type"],
                "target_identifier": r["target_identifier"],
                "status": r["status"],
                "details": r["details"],
                "proxy_used": r["proxy_used"],
                "created_at": r["created_at"]
            }
            for r in rows
        ]


# Initialize schema on load
init_db()
