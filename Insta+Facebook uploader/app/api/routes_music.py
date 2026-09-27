from fastapi import APIRouter, HTTPException, Query
from app.schemas.music import MusicSearchResponse, TrackInfo
from app.core.client_manager import client_manager

router = APIRouter(prefix="/music", tags=["Music"])


@router.get("/search", response_model=MusicSearchResponse)
def search_music(
    username: str = Query(..., description="Username of the authenticated account"),
    query: str = Query(..., description="Song title, artist, or keyword")
):
    try:
        cl = client_manager.get_client(username)
        results = cl.search_music(query)

        tracks = []
        for t in results:
            tracks.append(
                TrackInfo(
                    id=str(t.id),
                    audio_cluster_id=str(t.audio_cluster_id),
                    title=t.title,
                    display_artist=t.display_artist,
                    duration_ms=t.duration_in_ms or 0
                )
            )

        return MusicSearchResponse(query=query, tracks=tracks)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
