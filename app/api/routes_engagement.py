from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.engagement_service import engagement_service
from app.core import database

router = APIRouter(prefix="/api/engagement", tags=["Engagement Farming"])


class ResolvePostRequest(BaseModel):
    target_url: str = Field(..., description="Instagram Reel or Post URL")


class EngagementSwarmRequest(BaseModel):
    target_url: str = Field(..., description="Target Instagram Post or Reel URL")
    accounts: List[str] = Field(..., description="List of account usernames to perform actions")
    actions: List[str] = Field(..., description="List of actions: like, save, comment, follow, repost, story")
    comment_texts: Optional[List[str]] = Field(default=None, description="List of comment strings to rotate")
    repost_caption: Optional[str] = Field(default=None, description="Custom caption for repost action")
    delay_seconds: float = Field(default=3.0, ge=0.5, le=60.0, description="Delay between account actions")
    safe_limit: int = Field(default=30, ge=5, le=100, description="Daily safe limit for actions per account")


@router.get("/recent-posts")
def get_recent_posts(limit: int = 25):
    """
    Returns recently published reels and posts from post_history and scheduler.
    """
    return engagement_service.get_recent_published_posts(limit=limit)


@router.get("/activity-stats")
def get_activity_stats(safe_limit: int = Query(default=30, ge=5, le=100)):
    """
    Returns 24-hour activity statistics for all accounts, remaining quotas, and safety statuses.
    """
    return database.get_all_accounts_daily_activity(safe_limit=safe_limit, hours=24)


@router.get("/activity-logs")
def get_activity_logs(limit: int = Query(default=50, ge=1, le=500), username: Optional[str] = None):
    """
    Returns detailed activity logs for audit trails.
    """
    return database.get_recent_activity_logs(limit=limit, username=username)


@router.post("/resolve")
def resolve_post(req: ResolvePostRequest):
    """
    Resolves an Instagram URL to author details, media PK, thumbnail, and likes count.
    """
    try:
        data = engagement_service.resolve_target_post(req.target_url)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/run")
async def run_engagement_swarm(req: EngagementSwarmRequest):
    """
    Runs engagement farming across selected accounts:
    Like, Save, Comment, Follow Author, Repost, and Share to Story.
    Enforces safe daily limit (24-hour rolling window).
    Always uses each account's configured proxy.
    Returns a comprehensive execution report.
    """
    try:
        report = await engagement_service.run_engagement_swarm(
            target_url=req.target_url,
            accounts=req.accounts,
            actions=req.actions,
            comment_texts=req.comment_texts,
            repost_caption=req.repost_caption,
            delay_seconds=req.delay_seconds,
            safe_limit=req.safe_limit
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
