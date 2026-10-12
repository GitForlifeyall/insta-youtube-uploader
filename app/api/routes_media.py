import shutil
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pathlib import Path
import moviepy
try:
    import moviepy.editor
    moviepy.VideoFileClip = moviepy.editor.VideoFileClip
except ImportError:
    pass

from app.schemas.media import ReelUploadRequest, PostUploadRequest, StoryUploadRequest, UploadResponse
from app.core.client_manager import client_manager
from app.core import database
from app.config import UPLOADS_DIR

router = APIRouter(prefix="/upload", tags=["Media Upload"])


@router.post("/file")
async def upload_media_file(file: UploadFile = File(...)):
    """
    Receives browsed or drag-and-dropped media files from the dashboard,
    saves them to uploads/, and returns the absolute path for publishing.
    """
    safe_name = f"{uuid.uuid4().hex[:8]}_{file.filename.replace(' ', '_')}"
    target_path = UPLOADS_DIR / safe_name
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "success": True,
        "file_path": str(target_path.resolve()),
        "filename": file.filename,
        "size_bytes": target_path.stat().st_size
    }


def _slice_clip(clip, start: float, end: float):
    """Safely slices an audio or video clip across MoviePy 1.x and 2.x."""
    if hasattr(clip, "subclipped"):
        return clip.subclipped(start, end)
    return clip.subclip(start, end)


def _attach_clip_audio(clip, audio):
    """Safely attaches an audio clip to a video clip across MoviePy 1.x and 2.x."""
    if hasattr(clip, "with_audio"):
        return clip.with_audio(audio)
    return clip.set_audio(audio)


def _scale_audio_volume(clip, factor: float):
    """Safely scales audio volume across MoviePy 1.x and 2.x."""
    if hasattr(clip, "with_volume_scaled"):
        return clip.with_volume_scaled(factor)
    elif hasattr(clip, "volumex"):
        return clip.volumex(factor)
    return clip


def ensure_reel_compliance(video_path: Path) -> Path:
    """
    Ensures video has an audio track and 30fps H.264 / AAC encoding.
    Instagram strictly rejects videos without audio streams with HTTP 400.
    """
    try:
        try:
            from moviepy.editor import VideoFileClip
            from moviepy.audio.AudioClip import AudioClip
        except ImportError:
            from moviepy import VideoFileClip, AudioClip
        
        clip = VideoFileClip(str(video_path))
        needs_processing = False
        
        if clip.audio is None:
            needs_processing = True
            silent = None
            try:
                import numpy as np
                silent = AudioClip(lambda t: np.zeros((len(t) if hasattr(t, '__len__') else 1, 2)), duration=clip.duration, fps=44100)
            except Exception:
                try:
                    silent = AudioClip(lambda t: 0, duration=clip.duration, fps=44100)
                except Exception:
                    pass
            if silent is not None:
                clip = _attach_clip_audio(clip, silent)
            
        if clip.fps and clip.fps > 30:
            needs_processing = True
            
        if needs_processing:
            out_path = UPLOADS_DIR / f"processed_{video_path.name}"
            clip.write_videofile(
                str(out_path),
                codec="libx264",
                audio_codec="aac",
                fps=30,
                logger=None
            )
            clip.close()
            return out_path
        clip.close()
        return video_path
    except Exception as e:
        print(f"Warning: could not process video compliance: {e}")
        return video_path


def attach_audio_to_video(video_path: Path, audio_url: str, output_path: Path, start_sec: float = 0.0, volume: float = 1.0) -> Path:
    """Downloads official audio stream from Instagram CDN and mixes it into the video starting from start_sec with scaled volume."""
    import requests
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip
    except ImportError:
        from moviepy import VideoFileClip, AudioFileClip

    temp_audio = UPLOADS_DIR / "temp_music_track.mp4"
    res = requests.get(audio_url, stream=True)
    with open(temp_audio, "wb") as f:
        for chunk in res.iter_content(chunk_size=8192):
            f.write(chunk)

    video = VideoFileClip(str(video_path))
    audio_full = AudioFileClip(str(temp_audio))

    start = max(0.0, float(start_sec or 0.0))
    end = min(audio_full.duration, start + min(video.duration, 60))

    audio = _slice_clip(audio_full, start, end)
    if volume != 1.0:
        audio = _scale_audio_volume(audio, volume)
    final_video = _attach_clip_audio(video, audio)

    try:
        final_video.write_videofile(
            str(output_path),
            codec="libx264",
            audio_codec="aac",
            fps=30,
            logger=None
        )
    finally:
        try:
            video.close()
        except Exception:
            pass
        try:
            audio.close()
        except Exception:
            pass
        try:
            audio_full.close()
        except Exception:
            pass
        if hasattr(final_video, "close"):
            try:
                final_video.close()
            except Exception:
                pass
        if temp_audio.exists():
            try:
                temp_audio.unlink()
            except Exception:
                pass
    return output_path


def cleanup_generated_artifacts(*paths: Path):
    """Deletes temporary generated video files (processed_*, with_audio_*, temp_*) and auto-generated thumbnail jpgs."""
    for p in paths:
        if not p:
            continue
        p = Path(p)
        # Only delete temporary files generated by processing, NEVER the user's original media
        if p.exists() and p.is_file() and p.name.startswith(("processed_", "with_audio_", "temp_")):
            try:
                p.unlink()
            except Exception:
                pass
        # Check instagrapi's auto-generated thumbnail convention: {video_path}.jpg
        thumb_path = Path(f"{p}.jpg")
        if thumb_path.exists() and thumb_path.is_file():
            try:
                thumb_path.unlink()
            except Exception:
                pass


@router.post("/reel", response_model=UploadResponse)
def upload_reel(req: ReelUploadRequest):
    """
    Uploads a Reel (clip) to Instagram.
    Supports attaching background audio from Instagram's catalogue with a custom start timestamp.
    Automatically cleans up generated thumbnails and temp files after upload.
    """
    ready_video_path = None
    try:
        cl = client_manager.get_client(req.username)

        video_path = Path(req.video_path)
        if not video_path.exists():
            raise HTTPException(status_code=404, detail=f"Video file not found at: {req.video_path}")

        # Resolve track audio URL, cluster ID, and asset ID
        audio_url = None
        cluster_id = req.audio_cluster_id
        selected_track = None

        if req.music_query or cluster_id:
            from app.core.music_resolver import resolve_music_track
            selected_track = resolve_music_track(cl, query=req.music_query, cluster_id=cluster_id)
            if selected_track:
                cluster_id = str(getattr(selected_track, "audio_cluster_id", "") or getattr(selected_track, "id", ""))
                audio_url = str(getattr(selected_track, "progressive_download_url", "") or getattr(selected_track, "uri", ""))

        # Calculate timestamp for audio slicing and metadata (in milliseconds)
        audio_start_sec = req.audio_start_time_sec or 0.0
        audio_start_ms = int(audio_start_sec * 1000) if req.audio_start_time_sec is not None else None

        # Normalize volume: Instagram API volume_level is 0.0 to 1.0 (where 0.10 = 10%, 1.0 = 100%)
        # Default is 10 on a 0-100 scale (10% volume), matching Instagram's 0-100 Reel editor slider
        raw_music_vol = float(req.music_volume if req.music_volume is not None else 10.0)
        norm_music_vol = min(1.0, max(0.0, raw_music_vol / 100.0 if raw_music_vol > 1.0 else raw_music_vol))

        raw_orig_vol = float(req.original_audio_volume if req.original_audio_volume is not None else 0.0)
        norm_orig_vol = min(1.0, max(0.0, raw_orig_vol / 100.0 if raw_orig_vol > 1.0 else raw_orig_vol))

        # Ensure track metadata has cluster and asset IDs populated
        if selected_track:
            if not getattr(selected_track, "audio_cluster_id", None) and cluster_id:
                selected_track.audio_cluster_id = cluster_id
            if not getattr(selected_track, "id", None) and cluster_id:
                selected_track.id = cluster_id

        # Video file preparation:
        # If official track is resolved, upload clean video with official music metadata via clip_upload_with_music.
        # Do NOT burn the audio into the video file when using official music, or it will play twice at 100%!
        if selected_track:
            ready_video_path = ensure_reel_compliance(video_path)
            media = cl.clip_upload_with_music(
                path=ready_video_path,
                caption=req.caption,
                track=selected_track,
                original_volume=norm_orig_vol,
                music_volume=norm_music_vol,
                product="story_camera_clips_v2",
                audio_asset_start_time=audio_start_ms,
                share_to_facebook=req.share_to_facebook,
                share_to_threads=req.share_to_threads
            )
        else:
            # Fallback: if no official catalogue track was resolved but audio_url exists, mix locally
            if audio_url:
                mixed_path = UPLOADS_DIR / f"with_audio_{video_path.name}"
                ready_video_path = attach_audio_to_video(video_path, audio_url, mixed_path, start_sec=audio_start_sec, volume=norm_music_vol)
            else:
                ready_video_path = ensure_reel_compliance(video_path)

            media = cl.clip_upload(
                path=ready_video_path,
                caption=req.caption,
                share_to_facebook=req.share_to_facebook,
                share_to_threads=req.share_to_threads
            )

        post_url = f"https://www.instagram.com/reel/{media.code}/"
        proxy_used = client_manager.get_proxy(req.username)
        try:
            database.record_post(
                username=req.username,
                media_type="reel",
                url=post_url,
                code=media.code,
                media_id=str(media.pk),
                caption=req.caption,
                proxy_used=proxy_used
            )
        except Exception as db_err:
            print(f"Warning: could not record post in database: {db_err}")

        return UploadResponse(
            success=True,
            media_id=str(media.pk),
            code=media.code,
            url=post_url
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload reel: {str(e)}")
    finally:
        # Automatically clean up thumbnail and temp processed files
        cleanup_generated_artifacts(ready_video_path, Path(req.video_path))


@router.post("/post", response_model=UploadResponse)
def upload_post(req: PostUploadRequest):
    """
    Uploads a regular feed post.
    Supports single photo or multiple photos (carousel album).
    Can cross-post directly to Facebook and Threads.
    """
    try:
        cl = client_manager.get_client(req.username)

        # Validate that all files exist
        media_files = [Path(p) for p in req.media_paths]
        for f in media_files:
            if not f.exists():
                raise HTTPException(status_code=404, detail=f"Media file not found at: {f}")

        # Single photo vs Carousel
        if len(media_files) == 1:
            media = cl.photo_upload(
                path=media_files[0],
                caption=req.caption,
                share_to_facebook=req.share_to_facebook,
                share_to_threads=req.share_to_threads
            )
        else:
            media = cl.album_upload(
                paths=media_files,
                caption=req.caption,
                share_to_facebook=req.share_to_facebook,
                share_to_threads=req.share_to_threads
            )

        post_url = f"https://www.instagram.com/p/{media.code}/"
        proxy_used = client_manager.get_proxy(req.username)
        try:
            database.record_post(
                username=req.username,
                media_type="post" if len(media_files) == 1 else "album",
                url=post_url,
                code=media.code,
                media_id=str(media.pk),
                caption=req.caption,
                proxy_used=proxy_used
            )
        except Exception as db_err:
            print(f"Warning: could not record post in database: {db_err}")

        return UploadResponse(
            success=True,
            media_id=str(media.pk),
            code=media.code,
            url=post_url
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload post: {str(e)}")


@router.post("/story", response_model=UploadResponse)
def upload_story(req: StoryUploadRequest):
    """
    Uploads a photo or video story.
    """
    try:
        cl = client_manager.get_client(req.username)

        media_file = Path(req.media_path)
        if not media_file.exists():
            raise HTTPException(status_code=404, detail=f"Media file not found at: {req.media_path}")

        # Check extension to decide whether to upload video or photo story
        is_video = media_file.suffix.lower() in [".mp4", ".mov"]

        if is_video:
            media = cl.video_upload_to_story(path=media_file, caption=req.caption or "")
        else:
            media = cl.photo_upload_to_story(path=media_file, caption=req.caption or "")

        post_url = f"https://www.instagram.com/stories/{req.username}/"
        proxy_used = client_manager.get_proxy(req.username)
        try:
            database.record_post(
                username=req.username,
                media_type="story",
                url=post_url,
                code=getattr(media, "code", None),
                media_id=str(media.pk),
                caption=req.caption,
                proxy_used=proxy_used
            )
        except Exception as db_err:
            print(f"Warning: could not record post in database: {db_err}")

        return UploadResponse(
            success=True,
            media_id=str(media.pk),
            code=getattr(media, "code", "") or str(media.pk),
            url=post_url
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload story: {str(e)}")
    finally:
        # Clean up auto-generated thumbnail for story videos
        cleanup_generated_artifacts(Path(req.media_path))


@router.get("/history")
def upload_history(username: Optional[str] = None, limit: int = 50):
    """
    Retrieves history of all posts published through the API from SQLite database,
    including the post URL, timestamp, and the proxy routed through.
    """
    return database.get_post_history(username=username, limit=limit)
