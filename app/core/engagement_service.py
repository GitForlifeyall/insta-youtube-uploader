import asyncio
import random
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config import DOWNLOADS_DIR, UPLOADS_DIR
from app.core.client_manager import client_manager
from app.core import database

logger = logging.getLogger("engagement_service")


class EngagementService:
    def __init__(self):
        pass

    def get_any_active_client(self):
        """Finds any authenticated client to fetch public post metadata."""
        saved_accounts = client_manager.list_saved_accounts()
        for uname in saved_accounts:
            try:
                cl = client_manager.get_client(uname)
                if cl and getattr(cl, "user_id", None):
                    return cl
            except Exception:
                continue
        # Fallback to empty unauthenticated client
        from instagrapi import Client
        return Client()

    def resolve_target_post(self, target_url: str) -> Dict[str, Any]:
        """
        Resolves Instagram Post / Reel URL to media PK, author ID, thumbnail, and metadata.
        """
        if not target_url or not target_url.strip():
            raise ValueError("Target post/reel URL cannot be empty")

        clean_url = target_url.split("?")[0].strip()
        cl = self.get_any_active_client()

        try:
            media_pk = cl.media_pk_from_url(clean_url)
        except Exception as e:
            raise ValueError(f"Invalid Instagram URL or could not extract media PK: {str(e)}")

        try:
            media = cl.media_info(media_pk)
        except Exception as e:
            raise ValueError(f"Could not retrieve media details from Instagram: {str(e)}")

        author_pk = str(media.user.pk) if media.user and getattr(media.user, "pk", None) else ""
        author_username = media.user.username if media.user and getattr(media.user, "username", None) else "unknown"
        author_full_name = media.user.full_name if media.user and getattr(media.user, "full_name", None) else author_username

        thumbnail = str(media.thumbnail_url) if getattr(media, "thumbnail_url", None) else None

        return {
            "media_pk": str(media.pk),
            "media_id": str(media.id),
            "code": media.code,
            "target_url": clean_url,
            "media_type": media.media_type,  # 1=Photo, 2=Video/Reel, 8=Album
            "is_reel": media.media_type == 2,
            "author_pk": author_pk,
            "author_username": author_username,
            "author_full_name": author_full_name,
            "caption": media.caption_text or "",
            "thumbnail_url": thumbnail,
            "like_count": media.like_count or 0,
            "comment_count": media.comment_count or 0,
            "video_url": str(media.video_url) if getattr(media, "video_url", None) else None
        }

    def get_recent_published_posts(self, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Retrieves recently published reels and posts from post_history and scheduled_posts.
        """
        seen_urls = set()
        results = []

        # 1. From post_history table
        history = database.get_post_history(limit=limit)
        for h in history:
            url = (h.get("url") or "").strip()
            if url and url not in seen_urls:
                seen_urls.add(url)
                results.append({
                    "url": url,
                    "username": h.get("username", "Account"),
                    "caption": h.get("caption", ""),
                    "media_type": h.get("media_type", "reel"),
                    "created_at": h.get("created_at", ""),
                    "source": "History"
                })

        # 2. From scheduled_posts with status 'published'
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, caption, published_urls, post_type, created_at
                FROM scheduled_posts
                WHERE status = 'published' AND published_urls IS NOT NULL
                ORDER BY scheduled_time DESC
                LIMIT ?;
            """, (limit,))
            for row in cursor.fetchall():
                pub_urls_raw = row["published_urls"]
                if not pub_urls_raw:
                    continue
                try:
                    import json
                    if pub_urls_raw.startswith(("{", "[")):
                        pub_urls = json.loads(pub_urls_raw)
                        if isinstance(pub_urls, dict):
                            pub_urls = list(pub_urls.values())
                    else:
                        pub_urls = [pub_urls_raw]

                    for u in pub_urls:
                        u_str = str(u).strip()
                        if u_str.startswith("http") and u_str not in seen_urls:
                            seen_urls.add(u_str)
                            results.append({
                                "url": u_str,
                                "username": "Scheduled Post",
                                "caption": row["caption"],
                                "media_type": row["post_type"],
                                "created_at": row["created_at"],
                                "source": "Scheduled"
                            })
                except Exception:
                    pass

        return results[:limit]

    async def run_engagement_swarm(
        self,
        target_url: str,
        accounts: List[str],
        actions: List[str],
        comment_texts: Optional[List[str]] = None,
        repost_caption: Optional[str] = None,
        delay_seconds: float = 3.0
    ) -> Dict[str, Any]:
        """
        Executes Like, Comment, Save, Follow Author, and Repost across selected accounts.
        Always routes each action through that account's assigned proxy in SQLite.
        """
        if not accounts:
            raise ValueError("Select at least one Instagram account to perform engagement.")

        if not actions:
            raise ValueError("Select at least one engagement action (Like, Save, Comment, Follow, Repost).")

        # 1. Resolve Target Post
        target_meta = self.resolve_target_post(target_url)
        media_pk = target_meta["media_pk"]
        author_pk = target_meta["author_pk"]
        author_username = target_meta["author_username"]
        original_caption = target_meta["caption"]
        media_type = target_meta["media_type"]

        clean_comments = [c.strip() for c in (comment_texts or []) if c.strip()]
        if "comment" in actions and not clean_comments:
            clean_comments = ["Awesome! 🔥", "Love this 🎶", "On repeat 🎧", "Great vibe! 🙌"]

        # 2. Pre-download video if 'repost' action is requested
        downloaded_media_path = None
        if "repost" in actions:
            try:
                first_cl = client_manager.get_client(accounts[0])
                if media_type == 2:  # Video / Reel
                    downloaded_media_path = first_cl.video_download(int(media_pk), folder=DOWNLOADS_DIR)
                else:
                    downloaded_media_path = first_cl.photo_download(int(media_pk), folder=DOWNLOADS_DIR)
            except Exception as d_err:
                logger.warning("Could not pre-download post for reposting: %r", d_err)

        report = {
            "target_url": target_meta["target_url"],
            "thumbnail_url": target_meta["thumbnail_url"],
            "author_username": author_username,
            "author_pk": author_pk,
            "total_accounts": len(accounts),
            "passed_count": 0,
            "skipped_count": 0,
            "failed_count": 0,
            "account_reports": [],
            "completed_at": datetime.now(timezone.utc).isoformat()
        }

        # 3. Execute Swarm on each account
        for idx, username in enumerate(accounts):
            proxy = client_manager.get_proxy(username)
            acc_rep = {
                "username": username,
                "proxy": proxy or "Direct IP (No Proxy)",
                "actions": {},
                "overall_status": "passed",
                "errors": []
            }

            try:
                cl = client_manager.get_client(username)
            except Exception as login_err:
                err_msg = f"Session/Client error: {str(login_err)}"
                acc_rep["overall_status"] = "failed"
                acc_rep["errors"].append(err_msg)
                for act in actions:
                    acc_rep["actions"][act] = {"status": "failed", "error": err_msg}
                    report["failed_count"] += 1
                report["account_reports"].append(acc_rep)
                continue

            # --- ACTION A: LIKE ---
            if "like" in actions:
                try:
                    liked = cl.media_like(str(media_pk))
                    if liked:
                        acc_rep["actions"]["like"] = {"status": "passed", "message": "Liked post"}
                        report["passed_count"] += 1
                    else:
                        acc_rep["actions"]["like"] = {"status": "skipped", "message": "Already liked or no change"}
                        report["skipped_count"] += 1
                except Exception as le:
                    acc_rep["actions"]["like"] = {"status": "failed", "error": str(le)}
                    acc_rep["errors"].append(f"Like: {str(le)}")
                    report["failed_count"] += 1

            # --- ACTION B: SAVE ---
            if "save" in actions:
                try:
                    saved = cl.media_save(str(media_pk))
                    if saved:
                        acc_rep["actions"]["save"] = {"status": "passed", "message": "Saved post to bookmarks"}
                        report["passed_count"] += 1
                    else:
                        acc_rep["actions"]["save"] = {"status": "skipped", "message": "Already saved"}
                        report["skipped_count"] += 1
                except Exception as se:
                    acc_rep["actions"]["save"] = {"status": "failed", "error": str(se)}
                    acc_rep["errors"].append(f"Save: {str(se)}")
                    report["failed_count"] += 1

            # --- ACTION C: COMMENT ---
            if "comment" in actions:
                try:
                    comment_text = clean_comments[idx % len(clean_comments)]
                    comment_res = cl.media_comment(str(media_pk), comment_text)
                    acc_rep["actions"]["comment"] = {
                        "status": "passed",
                        "message": f'Commented: "{comment_text}"',
                        "comment_id": str(getattr(comment_res, "pk", ""))
                    }
                    report["passed_count"] += 1
                except Exception as ce:
                    acc_rep["actions"]["comment"] = {"status": "failed", "error": str(ce)}
                    acc_rep["errors"].append(f"Comment: {str(ce)}")
                    report["failed_count"] += 1

            # --- ACTION D: FOLLOW AUTHOR ---
            if "follow" in actions:
                try:
                    if str(cl.user_id) == str(author_pk) or username.lower() == author_username.lower():
                        acc_rep["actions"]["follow"] = {
                            "status": "skipped",
                            "message": "Self-post (acting account is author)"
                        }
                        report["skipped_count"] += 1
                    else:
                        already_following = False
                        try:
                            rel = cl.user_friendship_v1(str(author_pk))
                            if rel and (rel.following or rel.outgoing_request):
                                already_following = True
                        except Exception:
                            pass

                        if already_following:
                            acc_rep["actions"]["follow"] = {
                                "status": "skipped",
                                "message": f"Already following @{author_username}"
                            }
                            report["skipped_count"] += 1
                        else:
                            followed = cl.user_follow(str(author_pk))
                            if followed:
                                acc_rep["actions"]["follow"] = {
                                    "status": "passed",
                                    "message": f"Followed @{author_username}"
                                }
                                report["passed_count"] += 1
                            else:
                                acc_rep["actions"]["follow"] = {
                                    "status": "skipped",
                                    "message": f"Already followed or pending request"
                                }
                                report["skipped_count"] += 1
                except Exception as fe:
                    acc_rep["actions"]["follow"] = {"status": "failed", "error": str(fe)}
                    acc_rep["errors"].append(f"Follow: {str(fe)}")
                    report["failed_count"] += 1

            # --- ACTION E: REPOST ---
            if "repost" in actions:
                try:
                    if not downloaded_media_path or not Path(downloaded_media_path).exists():
                        raise ValueError("Media video file could not be downloaded for reposting")

                    cap = repost_caption if repost_caption else f"Repost: @{author_username}\n\n{original_caption}"
                    if media_type == 2:
                        new_media = cl.clip_upload(Path(downloaded_media_path), caption=cap)
                        new_url = f"https://www.instagram.com/reel/{new_media.code}/"
                    else:
                        new_media = cl.photo_upload(Path(downloaded_media_path), caption=cap)
                        new_url = f"https://www.instagram.com/p/{new_media.code}/"

                    database.record_post(
                        username=username,
                        media_type="reel" if media_type == 2 else "photo",
                        url=new_url,
                        code=new_media.code,
                        media_id=str(new_media.pk),
                        caption=cap,
                        proxy_used=proxy
                    )

                    acc_rep["actions"]["repost"] = {
                        "status": "passed",
                        "message": "Reposted successfully",
                        "new_url": new_url
                    }
                    report["passed_count"] += 1
                except Exception as re_err:
                    acc_rep["actions"]["repost"] = {"status": "failed", "error": str(re_err)}
                    acc_rep["errors"].append(f"Repost: {str(re_err)}")
                    report["failed_count"] += 1

            # Calculate overall status for this account
            action_statuses = [a.get("status") for a in acc_rep["actions"].values()]
            if all(s in ["passed", "skipped"] for s in action_statuses):
                acc_rep["overall_status"] = "passed"
            elif any(s == "passed" for s in action_statuses):
                acc_rep["overall_status"] = "partial"
            else:
                acc_rep["overall_status"] = "failed"

            report["account_reports"].append(acc_rep)

            # Delay before next account
            if idx < len(accounts) - 1 and delay_seconds > 0:
                await asyncio.sleep(delay_seconds)

        return report


engagement_service = EngagementService()
