from fastapi import APIRouter, HTTPException, Query
from app.schemas.music import MusicSearchResponse, TrackInfo
from app.core.client_manager import client_manager
from app.core.music_resolver import search_music_tracks

router = APIRouter(prefix="/music", tags=["Music"])


@router.get("/search", response_model=MusicSearchResponse)
def search_music(
    username: str = Query(..., description="Username of the authenticated account"),
    query: str = Query(..., description="Song title, artist, keyword, or direct Instagram audio URL")
):
    try:
        cl = client_manager.get_client(username)
        results = search_music_tracks(cl, query)

        tracks = []
        for t in results:
            tracks.append(
                TrackInfo(
                    id=str(t.id),
                    audio_cluster_id=str(getattr(t, "audio_cluster_id", "") or t.id),
                    title=getattr(t, "title", "Audio Track") or "Audio Track",
                    display_artist=getattr(t, "display_artist", "") or "",
                    duration_ms=getattr(t, "duration_in_ms", 0) or 0
                )
            )

        return MusicSearchResponse(query=query, tracks=tracks)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
