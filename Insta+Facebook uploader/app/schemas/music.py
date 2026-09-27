from pydantic import BaseModel
from typing import Optional, List

class TrackInfo(BaseModel):
    id: str
    audio_cluster_id: str
    title: str
    display_artist: str
    duration_ms: Optional[int] = 0

class MusicSearchResponse(BaseModel):
    query: str
    tracks: List[TrackInfo]