# 🧠 AGENT BRAIN & REPOSITORY INSTRUCTIONS

> [!CRITICAL]
> **PRIMARY DIRECTIVE: DO NOT CHANGE TEMPLATES UNLESS ORDERED TO.**
> **Never modify, rewrite, remove, or alter existing templates (Template 1, Template 2, Template 3, Brat, YT Hindi Type) or their default visual styles unless the user explicitly requests changes to that specific template.**

---

## 📌 Architecture Overview

This project is a high-performance **Lyric Video Generation Engine** built with Node.js/Express, Python 3.10+, FFmpeg, and Pillow.

```
├── engine/                 # Core Video & Lyrics Processing Engine
│   ├── generator.py        # Main Python engine (Audio, Captions, Transliteration, Rendering)
│   ├── indicxlit_runner.py # AI4Bharat IndicXlit subprocess runner (isolated environment)
│   └── motion_blur.py      # Motion blur filters
├── services/               # Modular backend microservices
│   ├── carousel/           # Instagram Spotify-style lyric carousel generator
│   ├── instagram/          # Instagram auth session & viral hooks extractor
│   └── recognition/        # Song/audio recognition service
├── docker/                 # Containerization & Deployment configs
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
├── config/                 # Configuration & Header pools
│   └── headers/
│       ├── headers.txt     # Random pool of top header captions for YT Hindi Type
│       └── intro_headers.txt # Intro hook captions pool
├── scripts/                # Video & asset processing scripts
├── emoji_assets/           # Apple-style emoji PNGs for Pillow inline compositing
├── fonts/                  # Custom font TTFs (EB Garamond, Cormorant Garamond, Segoe UI)
├── stickers/               # Nokia/retro template stickers
├── FILM OVERLAY/           # Film burn overlay videos
├── sound effect/           # Sound effect audio clips
├── videos/
│   ├── input/              # Source background videos for cinematic stitching
│   └── output/             # Final generated MP4 videos
├── src/
│   ├── index.js            # Express server & SSE real-time streaming endpoint
│   └── ffmpeg.js           # FFmpeg utilities
└── public/
    ├── index.html          # Web Studio UI
    ├── app.js              # Frontend controller & live preview layer
    └── style.css           # UI styling & design system
```

---

## 🎯 Template Invariants

Each template serves a distinct aesthetic and must remain untouched unless explicitly instructed:

| Template Key | Name | Visual Specification | Background & Layout |
|---|---|---|---|
| `template1` | **Template 1** | Impact 62pt, uppercase, white with black border/shadow | Black canvas, portrait 9:16 |
| `template2` | **Template 2** | Montserrat 54pt, yellow accent | Black canvas, portrait 9:16 |
| `template3` | **Template 3** | Arial 48pt, clean subtitle style | Black canvas, landscape 16:9 |
| `template4_brat` | **Brat Minimal** | Arial Narrow 72pt, uppercase, dynamic word accumulation | Solid colors (`#8ACE00`, White, SWEAT Tour Blue, etc.) |
| `yt_hindi_type` | **YT Hindi Type** | **EB Garamond** (centered, natural/sentence casing, 44pt, `\fad(210,210)` fade) + **Georgia Italic** top header with Apple emojis | Centered 1080×720 rectangular video clip from `videos/input/` on 1080×1920 black canvas |


---

## 🎼 Lyrics Retrieval & Transliteration Hierarchy

1. **YouTube Manual Subtitles**: Creator-provided subtitles (preferred if available).
2. **Spotify Synced Lyrics**: Queries local API (`http://localhost:8080/?trackid=...&format=lrc`) using `SP_DC`. Must verify `syncType != "UNSYNCED"` and non-zero timestamps.
3. **LRCLIB**: Fast synced lyrics database fallback.
4. **YouTube Auto Captions**: Extracted via `yt-dlp`.
5. **Genius API**: Fallback for romanized song lyrics.

### 🔤 Indic Script Transliteration (Hinglish / Roman Punjabi)
- If lyrics contain Devanagari or Gurmukhi script (`\u0900-\u097F`, `\u0A00-\u0A7F`), the engine automatically transliterates them into Roman script using **AI4Bharat IndicXlit**.
- **No Devanagari script** should appear in the final rendered video for `yt_hindi_type`.

---

## 🎬 Rendering & FFmpeg Rules

1. **Single-Pass Rendering**: Always composite background video + top header + ASS subtitles + audio in one FFmpeg process.
2. **Hardware Acceleration**:
   - `final` mode (`1080x1920`, 30 FPS): Uses GPU encoder (`h264_mf` on Windows / `h264_nvenc`) with `libx264` fallback.
   - `fast` mode (`540x960`, 24 FPS): Uses `libx264 -preset ultrafast -crf 26`.
3. **Header & Emoji Engine**:
   - Top header is rendered via Pillow with **Georgia Italic** font.
   - Inline emojis (`🤌`, `🤍`, `❤️`, `🫶`, etc.) are composited from `emoji_assets/*.png`.
   - Header is centered horizontally `(canvas_width - text_width) / 2` in the top black letterbox above the video clip.
4. **No-Lyrics Guard**:
   - If all lyrics providers return 0 lines, exit cleanly before FFmpeg rendering.
   - Emit: `"No usable lyrics found. Video generation stopped before FFmpeg rendering."`
   - Never output a blank MP4 or corrupt video.

---

## 🛠️ Development & Execution Guidelines

- **Python Virtual Environment**: Always use `.venv310\Scripts\python.exe` (required for PyTorch and IndicXlit).
- **Node Server**: `npm run dev` (starts server on `http://localhost:3000`).
- **Do not modify `.env`** or log API keys/cookies in console logs.

<!-- BEGIN brain.md -->
## Project Brain

This project keeps a **Project Brain**: a persistent memory layer of its durable decisions, requirements, and constraints. Read `./BRAIN.md` for the full read/write contract.

The `brain` CLI is not guaranteed to be on `PATH`. From the project root, invoke it as `node <brain-page-skill-dir>/bin/brain.mjs <subcommand> [flags]`, resolving `<brain-page-skill-dir>` to the installed `brain-page` skill directory.

Maintain the brain as part of normal coding work — not as a separate task. While discussing or implementing features:
- **Start of a task:** load relevant context with the `brain` CLI (`list-pages`, `read-page`, `read-root`). Prefer a narrow read over scanning everything.
- **When a decision, requirement, constraint, or durable insight settles** (in chat or while coding): capture it immediately via the `brain` CLI. Do not wait to be asked and do not batch it for later.
- **Pure implementation with no new decision:** do not write to the brain.
- **When overturning a prior conclusion:** update the page (`update-truth` and/or `append-timeline` with `kind: reversal`, or `archive-page`).
- Only store what will still matter in six months and is hard to reconstruct from the code alone.
- Never hand-edit brain files. If a brain MCP server is connected and authenticated, prefer it; otherwise use the `brain` CLI.

The brain skills (`brain-setup`, `brain-page`, `brain-ingest`, `brain-bootstrap`) are installed in your global skills directory. To scaffold a new project, run `node <brain-page-skill-dir>/bin/brain.mjs init` from its root.

If native notes/history are available, keep relevant brain page IDs and unresolved task state in notes; search history for earlier task evidence. After context rollover, re-read relevant pages through the CLI for current project facts. Do not copy task history into the brain.
<!-- END brain.md -->
