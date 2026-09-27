from pydantic import BaseModel
from typing import Optional, List

class ReelUploadRequest(BaseModel):
    username: str
    video_path: str
    caption: str = ""
    music_query: Optional[str] = None 
    audio_cluster_id: Optional[str] = None 
    audio_start_time_sec: Optional[float] = None
    share_to_facebook: bool = False
    share_to_threads: bool = False

class PostUploadRequest(BaseModel):
    username: str
    media_paths: List[str] 
    caption: str = ""
    share_to_facebook: bool = False
    share_to_threads: bool = False

class StoryUploadRequest(BaseModel):
    username: str
    media_path: str
    caption: Optional[str] = ""

class UploadResponse(BaseModel):
    success: bool
    media_id: str
    code: str
    url: str