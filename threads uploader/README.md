# Threads Uploader & Automation API

A production-ready **FastAPI** microservice built on top of [`threads-api`](https://pypi.org/project/threads-api/). Designed to act as a dedicated Meta Threads automation engine and microservice for your applications, schedulers, and bots.

---

## Features

- 👥 **Multi-Account Management**: Supports unlimited accounts with persistent, encrypted session tokens (no repetitive logins or security checkpoint triggers).
- ✍️ **Text Threads**: Post text updates with optional rich link preview cards.
- 📸 **Photo & Carousel Posts**: Upload single photos or multi-photo carousel albums using either local file paths or HTTP/HTTPS image URLs.
- 💬 **Replies & Quotes**: Engage directly by replying to existing threads or quote-reposting them with custom commentary.
- ❤️ **Interactions**: Like, unlike, and delete posts via API.
- 👤 **Profile Lookups**: Fetch live user profiles, bio, follower count, and verification status.
- 📖 **Interactive Swagger UI**: Interactive documentation and API playground out of the box.

---

## Directory Structure

```text
threads uploader/
├── app/
│   ├── api/
│   │   ├── routes_account.py  # Account authentication & status endpoints
│   │   └── routes_posts.py    # Text, media, reply, quote, like & delete endpoints
│   ├── core/
│   │   ├── client_manager.py  # Multi-account session caching & Client pool
│   │   └── threads_patch.py   # Pydantic v2 compatibility loader
│   ├── schemas/
│   │   ├── account.py         # Pydantic models for authentication & profiles
│   │   └── post.py            # Pydantic models for posts, media & actions
│   ├── config.py              # Central settings and directory paths
│   └── main.py                # FastAPI entrypoint with CORS & Routers
├── sessions/                  # Encrypted token cache and session JSON files
├── uploads/                   # Temporary directory for media files
├── requirements.txt           # Project dependencies
├── test_api.py                # Interactive API test script
└── README.md
```

---

## Setup & Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Server
From the `threads uploader/` root directory:
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
Authenticate an account and save its encrypted session token for subsequent requests.
```json
{
  "username": "my_threads_username",
  "password": "my_threads_password"
}
```

#### `GET /accounts/{username}/status`
Check if the account has an active session.
```bash
GET http://localhost:8000/accounts/my_threads_username/status
```

#### `GET /accounts/{username}/profile`
Fetch live profile info (bio, follower count, verified status).
```bash
GET http://localhost:8000/accounts/my_threads_username/profile
```

---

### 2. Publishing Posts

#### `POST /posts/text`
Publish a text-only thread with optional link preview attachment.
```json
{
  "username": "my_threads_username",
  "text": "Excited to share our new project launch! 🚀",
  "url": "https://example.com"
}
```

#### `POST /posts/media`
Publish a single photo or multi-photo carousel album.
```json
{
  "username": "my_threads_username",
  "caption": "Photo dump from our latest trip! ✨",
  "media_paths": [
    "C:/images/photo1.jpg",
    "C:/images/photo2.jpg"
  ]
}
```
> *Note: `media_paths` accepts both local file paths and remote `https://` URLs.*

#### `POST /posts/reply`
Reply to an existing thread.
```json
{
  "username": "my_threads_username",
  "text": "Great insights, totally agree!",
  "parent_post_id": "3141592653589793"
}
```

#### `POST /posts/quote`
Quote-repost an existing thread.
```json
{
  "username": "my_threads_username",
  "text": "This is a game changer, check it out:",
  "quoted_post_id": "3141592653589793"
}
```

#### `POST /posts/like`
Like a thread post.
```json
{
  "username": "my_threads_username",
  "post_id": "3141592653589793"
}
```

#### `DELETE /posts/{username}/{post_id}`
Delete a published post.
```bash
DELETE http://localhost:8000/posts/my_threads_username/3141592653589793
```

---

## How Other Projects Call This API (Python Example)

```python
import requests

API_URL = "http://localhost:8000"

# 1. Login once (session token is encrypted and saved automatically)
requests.post(f"{API_URL}/accounts/login", json={
    "username": "my_threads_username",
    "password": "my_threads_password"
})

# 2. Publish a text post with a link
response = requests.post(f"{API_URL}/posts/text", json={
    "username": "my_threads_username",
    "text": "Automation test post! 🤖",
    "url": "https://threads.net"
})

print(response.json())
# -> {"success": true, "media_id": "...", "code": "...", "url": "https://www.threads.net/t/..."}
```
