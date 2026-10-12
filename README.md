# Instagram Uploader & Automation API

A production-ready **FastAPI** microservice built on top of [`instagrapi`](https://github.com/subzeroid/instagrapi). Designed to act as a dedicated Instagram backend engine for your other applications and bots.

---

## Features

- 👥 **Multi-Account Management**: Supports unlimited accounts with persistent sessions (no repetitive logins or 2FA prompts).
- 🎵 **Official Music Catalogue Integration**: Search Instagram's music library and attach official tracks to your Reels automatically.
- 🎬 **Reel Uploads**: Upload vertical videos with custom captions and attached audio tracks.
- 📸 **Feed Posts & Carousels**: Upload single photos or multi-image carousels.
- ⏱️ **Stories**: Post photo and video stories directly.
- 📖 **Interactive Swagger UI**: Full interactive API documentation available out of the box.

---

## Directory Structure

```text
insta uploader/
├── app/
│   ├── api/
│   │   ├── routes_account.py  # Account login & health check endpoints
│   │   ├── routes_music.py    # Official music search endpoints
│   │   └── routes_media.py    # Reels, Posts, and Stories upload endpoints
│   ├── core/
│   │   └── client_manager.py  # Multi-account session caching & Client pool
│   ├── schemas/
│   │   ├── account.py         # Pydantic models for authentication
│   │   ├── music.py           # Pydantic models for audio tracks
│   │   └── media.py           # Pydantic models for media uploads
│   ├── config.py              # Central settings and directory paths
│   └── main.py                # FastAPI entrypoint with CORS & Routers
├── sessions/                  # Auto-generated JSON session files (one per account)
├── uploads/                   # Temporary directory for media files
├── requirements.txt           # Project dependencies
└── README.md
```

---

## Setup & Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Server
From the root project folder:
```bash
uvicorn app.main:app --reload --port 8000
```

The API will start at `http://localhost:8000`.

---

## Interactive API Docs

Once the server is running, open:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## API Endpoints Reference

### 1. Accounts

#### `POST /accounts/login`
Authenticate an account and save its session for subsequent requests.
```json
{
  "username": "my_instagram_username",
  "password": "my_secure_password",
  "verification_code": null
}
```
> *If Instagram challenges you with a 2FA/SMS code, provide the code in `verification_code`.*

#### `GET /accounts/{username}/status`
Check if the account's session is currently valid and active on Instagram.

---

### 2. Music Catalogue

#### `GET /music/search?username={username}&query={query}`
Search Instagram's official music catalogue for audio tracks.
- **Example:** `/music/search?username=my_account&query=Starboy`
- **Response:**
```json
{
  "query": "Starboy",
  "tracks": [
    {
      "id": "1234567890",
      "audio_cluster_id": "9876543210",
      "title": "Starboy",
      "display_artist": "The Weeknd, Daft Punk",
      "duration_ms": 230000
    }
  ]
}
```

---

### 3. Media Uploads

#### `POST /upload/reel`
Upload a Reel (clip) with optional music attachment, custom music start timestamp, and Facebook/Threads cross-posting.
```json
{
  "username": "my_instagram_username",
  "video_path": "C:/videos/my_reel.mp4",
  "caption": "Check out this reel! #viral #fyp",
  "music_query": "Blinding Lights",
  "audio_cluster_id": null,
  "audio_start_time_sec": 45.0,
  "share_to_facebook": true,
  "share_to_threads": false
}
```
> *Note: You can pass either a `music_query` (the server searches and attaches the top match) or an exact `audio_cluster_id`. Use `audio_start_time_sec` (e.g. `45.0` for 0:45) to start the song at a specific timestamp. Set `share_to_facebook: true` to auto-cross-post to your connected Facebook Page/Profile.*

#### `POST /upload/post`
Upload a single photo or multi-photo carousel post with optional Facebook/Threads cross-posting.
```json
{
  "username": "my_instagram_username",
  "media_paths": [
    "C:/images/photo1.jpg",
    "C:/images/photo2.jpg"
  ],
  "caption": "Our latest collection! ✨",
  "share_to_facebook": true,
  "share_to_threads": false
}
```

#### `POST /upload/story`
Upload a photo or video story.
```json
{
  "username": "my_instagram_username",
  "media_path": "C:/images/story_image.jpg",
  "caption": "Behind the scenes 🎬"
}
```

---

## How Other Projects Call This API (Python Example)

```python
import requests

API_URL = "http://localhost:8000"

# 1. Login once
requests.post(f"{API_URL}/accounts/login", json={
    "username": "my_account",
    "password": "my_password"
})

# 2. Upload a reel with music
response = requests.post(f"{API_URL}/upload/reel", json={
    "username": "my_account",
    "video_path": "C:/media/promo.mp4",
    "caption": "Exciting news dropping soon! 🔥",
    "music_query": "As It Was"
})

print(response.json())
# -> {"success": true, "media_id": "...", "code": "...", "url": "https://www.instagram.com/reel/..."}
```
