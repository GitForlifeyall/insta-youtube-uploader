# 🎬 LyricalVideo: Automated 1080p MP4 Lyric Video Generator

A full-stack, hardware-accelerated lyric video generator built with Node.js/Express, Python 3.10+, FFmpeg, and Pillow.

> [!CRITICAL]
> **AGENT DIRECTIVE**: **DO NOT CHANGE TEMPLATES UNLESS ORDERED TO.**
> See [AGENTS.md](file:///c:/Users/khann/OneDrive/Documents/Projects/New%20lyrics%202/AGENTS.md) for full agent architecture and invariant rules.

---

## 🚀 Getting Started

### 1. Install Node Dependencies
```bash
npm install
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 3. Run the Development Server
```bash
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 🎨 Supported Templates

| Template | Aesthetic | Canvas & Layout |
|---|---|---|
| **Template 1** | Bold Impact (White with black shadow) | Portrait 9:16 |
| **Template 2** | Montserrat (Yellow accents) | Portrait 9:16 |
| **Template 3** | Arial Subtitle | Landscape 16:9 |
| **Brat Minimal** | Charli XCX Aesthetic (Dynamic accumulation) | Portrait 9:16, customizable swatches |
| **YT Hindi Type** | Cinematic EB Garamond lyrics + Georgia Italic header with Apple emojis | Centered rectangular video from `videos/input/` with black letterbox top & bottom |

---

## 📁 Folder Structure

- `src/`: Express web server and API endpoints (`index.js`, `ffmpeg.js`).
- `engine/`: Core Python lyric video engine (`generator.py`, `indicxlit_runner.py`, `motion_blur.py`).
- `services/`: Modular backend microservices:
  - `services/carousel/`: Spotify-style Instagram lyric carousel generator (`renderer.py`, `lookup.py`).
  - `services/instagram/`: Instagram session authentication & viral hook extractor (`service.py`, `login_helper.py`).
  - `services/recognition/`: Audio / song recognition service.
- `docker/`: Docker containerization configs (`Dockerfile`, `docker-compose.yml`, `.dockerignore`).
- `config/headers/`: Header pools (`headers.txt`, `intro_headers.txt`).
- `scripts/`: Video and asset processing utilities (`rotate_film_overlays.py`, `process_logo.py`).
- `videos/input/`: Place your background video clips here for cinematic stitching.
- `videos/output/`: Generated final MP4 videos are saved here.
- `FILM OVERLAY/`: Film burn and cinematic overlay video clips.
- `sound effect/`: Sound effects (e.g. film burn audio).
- `stickers/`: Sticker overlays for retro/Nokia templates.
- `emoji_assets/`: Apple-style emoji PNGs for inline header compositing.
- `fonts/`: Local font files (`EB Garamond`, `Cormorant Garamond`, `Segoe UI Emoji`).

---

## 🛠️ Tech Stack & Dependencies

- **Backend**: Express.js (Node.js ES Modules) + SSE streaming
- **Engine**: Python 3.10+ with `yt-dlp`, `requests`, `Pillow`, and `AI4Bharat IndicXlit`
- **Video Renderer**: FFmpeg with GPU hardware acceleration (`h264_mf` / `h264_nvenc`)
- **Subtitle Engine**: `libass` with custom font mappings

---

## Lyric carousel renderer

`services/carousel/renderer.py` is a standalone Pillow renderer for Spotify-style
Instagram lyric carousels. It does not modify the existing video templates.
It accepts JSON or CSV, extracts a dominant album-art color, and writes one
PNG per lyric line.

```powershell
.venv310\Scripts\python.exe services\carousel\renderer.py examples\carousel_input.json output\carousel --format 4:5 --workers 4
```

Use `4:5` for 1080x1350 carousel posts or `9:16` for 1080x1920 stories/reels.
