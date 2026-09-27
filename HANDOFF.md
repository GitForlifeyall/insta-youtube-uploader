# 📋 Social Hub Ecosystem: Master Project Handoff Document

> **Status:** Production-Ready & Tested Live  
> **Last Updated:** September 2026  
> **Repository Root:** `c:\Users\khann\OneDrive\Documents\Projects\insta uploader`

---

## 🏗️ 1. Architecture & Microservices Overview

The platform is an automated multi-brand publishing, analytics, and content studio ecosystem comprising **4 synchronized microservices**:

| Service | Port | Directory | Purpose |
|---|---|---|---|
| **Social Hub** | `8000` | `social-hub/` | Central Planner, Calendar UI, Competitor Radar, Evergreen Recycler, Bulk Scheduler, SQLite DB. |
| **Instagram + FB Uploader** | `8001` | `Insta+Facebook uploader/` | Headless publishing service using `instagrapi` for Reels, Carousels, Stories, and Facebook cross-posting. |
| **Threads Uploader** | `8002` | `threads uploader/` | Dedicated text & media publishing engine for Threads using persistent token sessions. |
| **new-lyrics-2 Studio** | `3000` | `new-lyrics-2/` | Visual Lyric Video & Carousel creation engine rendering MP4s to `videos/output/`. |

All four microservices are orchestrated simultaneously with a single terminal command:
```powershell
python run_all.py
```

---

## 🔑 2. Credentials & Session Management

### ❓ Do I need to update credentials or session IDs every day?
**NO.**
- **Session Duration:** Instagram `sessionid` cookies last for **60 to 90 days** (or until you explicitly click *"Log out of all devices"* on Instagram or change your password).
- **Persistent Session Files:** Once authenticated, the uploader dumps the encrypted session data into:
  - `Insta+Facebook uploader/sessions/session_<username>.json`
  - `threads uploader/sessions/token_<username>.dat`
- **Reboot Resilience:** Whenever you restart `run_all.py`, the services reload these cached files from disk **without contacting Instagram's login server**, avoiding challenge flags, captcha, or rate limits.

### Central `.env` Structure
Credentials are configured in a single file at the root: **[`.env`](file:///.env)**.

```env
# ================= BRAND 1: Lyrical786 =================
BRAND1_NAME=Lyrical786
BRAND1_COLOR=#8ACE00
BRAND1_IG_USERNAME=lyr.ical786
BRAND1_IG_PASSWORD=Beliver123@
BRAND1_IG_SESSION_ID=
BRAND1_THREADS_USERNAME=lyr.ical786
BRAND1_THREADS_PASSWORD=Beliver123@
BRAND1_YOUTUBE_HANDLE=@Lyrical786-e9k
BRAND1_FB_AUTO_SHARE=false

# ================= BRAND 2: Lyrics on lips =================
BRAND2_NAME=Lyrics on lips
BRAND2_COLOR=#e7ff56
BRAND2_IG_USERNAME=lyrics.on.lips
BRAND2_IG_PASSWORD=Beliver123@
BRAND2_IG_SESSION_ID=26764074896%3AM90EORdke2jcZZ%3A23%3AAYkfE2XyDpK3NePRS7xd5j8FvhDuOhYP8NMsvMLHBw
BRAND2_THREADS_USERNAME=lyrics.on.lips
BRAND2_THREADS_PASSWORD=Beliver123@
BRAND2_YOUTUBE_HANDLE=@Lyricsonlips-j4e
BRAND2_FB_AUTO_SHARE=true
```

### Instant 1-Click Sync
If you ever edit `.env`, you do **not** need to restart the server. Simply click the **`🔑` (Sync)** icon in the Social Hub header bar, or make a `POST /api/sync-credentials` request.

---

## 🌟 3. Features Implemented & Verified Live

### 1. 🎨 Premium Dark Glass UI Overhaul
- **Aesthetic:** Modern, high-contrast Linear/Vercel-inspired UI.
- **Typography:** Paired `Plus Jakarta Sans` (editorial headings & interface) with `JetBrains Mono` (metrics & analytics).
- **Navigation:** Dark glass segmented tab pill controls (`📅 Planner`, `📱 Feed`, `🕵️ Competitors`, `♻️ Evergreen`, `⏳ Queue`, `📈 Analytics`).
- **Interactive Verification:** Audited and tested across desktop viewports via Puppeteer and Playwright.

### 2. ⚡ Fast Video Thumbnail Auto-Extractor (Task 06)
- **Engine:** [`thumbnail_extractor.py`](file:///social-hub/app/core/thumbnail_extractor.py) uses fast-seek FFmpeg (`-ss 00:00:01 -i`) and WebP compression (`scale=480:-1`, quality 75).
- **Benefit:** Generates lightweight ~25KB WebP preview tiles instead of streaming entire ~50MB MP4 files, eliminating browser lag in the media selector.
- **Mount Point:** Hosted via static mount at `/media/thumbnails/`.

### 3. 🕵️ Competitor Radar (100% Zero-Login)
- **Engine:** [`competitor_spy.py`](file:///social-hub/app/core/competitor_spy.py) & [`public_scrapers.py`](file:///new-lyrics-2/services/analytics/public_scrapers.py).
- **Functionality:** Scrapes public YouTube/Instagram stats (subscribers, post count, average video views) without needing OAuth or personal credentials.
- **Cache:** 15-minute in-memory TTL scraper cache prevents IP throttling.

### 4. ♻️ Evergreen Content Recycler
- **Engine:** [`evergreen_engine.py`](file:///social-hub/app/core/evergreen_engine.py).
- **Functionality:** Automatically detects empty days in the upcoming 7-day calendar and schedules eligible evergreen reels into peak engagement slots.

### 5. ⚡ Bulk Batch Scheduler
- **Engine:** [`routes_bulk.py`](file:///social-hub/app/api/routes_bulk.py) & [`best_times.py`](file:///social-hub/app/core/best_times.py).
- **Functionality:** Select 5–10 lyric reels at once, define caption/hashtags, and auto-distribute them across upcoming peak audience slots (`19:30`, `13:00`, etc.).

---

## 🚀 4. How to Run & Daily Usage

### Step 1: Launch All Services
In a PowerShell terminal inside the project root:
```powershell
python run_all.py
```

### Step 2: Open Dashboard
Navigate to **[http://localhost:8000](http://localhost:8000)** in your browser.

### Step 3: Switch Workspaces
Use the brand dropdown in the top-left corner to toggle between:
- 🟢 **Lyrical786**
- 🟡 **Lyrics on lips**

### Step 4: Schedule Content
1. Click **✍️ Create Post** or **⚡ Bulk Schedule**.
2. Select your rendered video from `new-lyrics-2`.
3. Check the target platforms (📸 Instagram, 📘 Facebook, 🧵 Threads, ▶️ YouTube).
4. Pick a recommended peak time window chip (e.g. `7:30 PM Peak`) and click **Schedule Post**.

---

## 🛠️ 5. Key File Index

- **Launcher**: [`run_all.py`](file:///run_all.py)
- **Root Configuration**: [`.env`](file:///.env)
- **Social Hub Backend**:
  - Main App & Lifespan: [`social-hub/app/main.py`](file:///social-hub/app/main.py)
  - Credential Synchronizer: [`social-hub/app/core/credentials_sync.py`](file:///social-hub/app/core/credentials_sync.py)
  - Database & Models: [`social-hub/app/core/database.py`](file:///social-hub/app/core/database.py), [`social-hub/app/core/models.py`](file:///social-hub/app/core/models.py)
  - Thumbnail Pipeline: [`social-hub/app/core/thumbnail_extractor.py`](file:///social-hub/app/core/thumbnail_extractor.py)
- **Frontend Assets**:
  - UI Logic: [`social-hub/app/static/app.js`](file:///social-hub/app/static/app.js)
  - Interface Template: [`social-hub/app/static/index.html`](file:///social-hub/app/static/index.html)
  - Design Stylesheet: [`social-hub/app/static/style.css`](file:///social-hub/app/static/style.css)
- **Uploaders**:
  - Instagram/FB: [`Insta+Facebook uploader/app/core/client_manager.py`](file:///Insta+Facebook%20uploader/app/core/client_manager.py)
  - Threads: [`threads uploader/app/core/client_manager.py`](file:///threads%20uploader/app/core/client_manager.py)

---

## 🔒 6. Troubleshooting Session Refresh

If an account ever disconnects after several months:
1. Open [instagram.com](https://instagram.com) in your browser -> Press `F12` -> Application -> Cookies -> Copy `sessionid`.
2. Update `BRAND1_IG_SESSION_ID` or `BRAND2_IG_SESSION_ID` in `.env`.
3. Click the `🔑` button in the top navigation bar of Social Hub.
