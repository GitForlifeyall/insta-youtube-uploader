from fastapi import APIRouter, HTTPException
from pathlib import Path
import moviepy
try:
    import moviepy.editor
    moviepy.VideoFileClip = moviepy.editor.VideoFileClip
except ImportError:
    pass

from app.schemas.media import ReelUploadRequest, PostUploadRequest, StoryUploadRequest, UploadResponse
from app.core.client_manager import client_manager

router = APIRouter(prefix="/upload", tags=["Media Upload"])


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
            from moviepy import VideoFileClip
            from moviepy.audio.AudioClip import AudioClip
        
        clip = VideoFileClip(str(video_path))
        needs_processing = False
        
        if clip.audio is None:
            needs_processing = True
            silent = AudioClip(lambda t: 0, duration=clip.duration, fps=44100)
            clip = clip.set_audio(silent)
            
        if clip.fps and clip.fps > 30:
            needs_processing = True
            
        if needs_processing:
            out_path = Path("uploads") / f"processed_{video_path.name}"
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


def attach_audio_to_video(video_path: Path, audio_url: str, output_path: Path, start_sec: float = 0.0) -> Path:
    """Downloads official audio stream from Instagram CDN and mixes it into the video starting from start_sec."""
    import requests
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip
    except ImportError:
        from moviepy import VideoFileClip, AudioFileClip

    temp_audio = Path("uploads") / "temp_music_track.mp4"
    res = requests.get(audio_url, stream=True)
    with open(temp_audio, "wb") as f:
        for chunk in res.iter_content(chunk_size=8192):
            f.write(chunk)

    video = VideoFileClip(str(video_path))
    audio_full = AudioFileClip(str(temp_audio))

    start = max(0.0, float(start_sec or 0.0))
    end = min(audio_full.duration, start + min(video.duration, 60))

    audio = audio_full.subclip(start, end)
    final_video = video.set_audio(audio)

    final_video.write_videofile(
        str(output_path),
        codec="libx264",
        audio_codec="aac",
        fps=30,
        logger=None
    )
    video.close()
    audio.close()
    audio_full.close()
    if temp_audio.exists():
        temp_audio.unlink()
    return output_path


def cleanup_generated_artifacts(*paths: Path):
    """Deletes temporary generated video files and auto-generated thumbnail jpgs."""
    for p in paths:
        if not p:
            continue
        p = Path(p)
        # Check direct path
        if p.exists() and p.is_file():
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

        if req.music_query:
            tracks = cl.search_music(req.music_query)
            if tracks:
                selected_track = tracks[0]
                cluster_id = str(selected_track.audio_cluster_id)
                audio_url = str(getattr(selected_track, "progressive_download_url", "") or getattr(selected_track, "uri", ""))
        elif cluster_id:
            try:
                tracks = cl.search_music(str(cluster_id))
                if tracks:
                    selected_track = tracks[0]
                    audio_url = str(getattr(selected_track, "progressive_download_url", "") or getattr(selected_track, "uri", ""))
            except Exception:
                pass

        # Calculate timestamp for audio slicing and metadata (in milliseconds)
        audio_start_sec = req.audio_start_time_sec or 0.0
        audio_start_ms = int(audio_start_sec * 1000) if req.audio_start_time_sec is not None else None

        # If we have the official audio stream, mix it into the video starting from audio_start_sec!
        if audio_url:
            mixed_path = Path("uploads") / f"with_audio_{video_path.name}"
            ready_video_path = attach_audio_to_video(video_path, audio_url, mixed_path, start_sec=audio_start_sec)
        else:
            ready_video_path = ensure_reel_compliance(video_path)

        # If track was resolved, use instagrapi's official clip_upload_with_music
        if selected_track:
            media = cl.clip_upload_with_music(
                path=ready_video_path,
                caption=req.caption,
                track=selected_track,
                original_volume=0.0,
                music_volume=1.0,
                product="story_camera_clips_v2",
                audio_asset_start_time=audio_start_ms,
                share_to_facebook=req.share_to_facebook,
                share_to_threads=req.share_to_threads
            )
        else:
            media = cl.clip_upload(
                path=ready_video_path,
                caption=req.caption,
                share_to_facebook=req.share_to_facebook,
                share_to_threads=req.share_to_threads
            )

        return UploadResponse(
            success=True,
            media_id=str(media.pk),
            code=media.code,
            url=f"https://www.instagram.com/reel/{media.code}/"
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

        return UploadResponse(
            success=True,
            media_id=str(media.pk),
            code=media.code,
            url=f"https://www.instagram.com/p/{media.code}/"
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

        return UploadResponse(
            success=True,
            media_id=str(media.pk),
            code=media.code,
            url=f"https://www.instagram.com/stories/{req.username}/"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload story: {str(e)}")
    finally:
        # Clean up auto-generated thumbnail for story videos
        cleanup_generated_artifacts(Path(req.media_path))
