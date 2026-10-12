from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.engagement_service import engagement_service

router = APIRouter(prefix="/api/engagement", tags=["Engagement Farming"])


class ResolvePostRequest(BaseModel):
    target_url: str = Field(..., description="Instagram Reel or Post URL")


class EngagementSwarmRequest(BaseModel):
    target_url: str = Field(..., description="Target Instagram Post or Reel URL")
    accounts: List[str] = Field(..., description="List of account usernames to perform actions")
    actions: List[str] = Field(..., description="List of actions: like, save, comment, follow, repost")
    comment_texts: Optional[List[str]] = Field(default=None, description="List of comment strings to rotate")
    repost_caption: Optional[str] = Field(default=None, description="Custom caption for repost action")
    delay_seconds: float = Field(default=3.0, ge=0.5, le=60.0, description="Delay between account actions")


@router.get("/recent-posts")
def get_recent_posts(limit: int = 25):
    """
    Returns recently published reels and posts from post_history and scheduler.
    """
    return engagement_service.get_recent_published_posts(limit=limit)


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
    Like, Save, Comment, Follow Author (skips if already followed), and Repost.
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
            delay_seconds=req.delay_seconds
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
