---
slug: architecture
title: System architecture
role: system architecture
updated: "2026-09-16T00:31:50"
---

# System architecture

## Overview

The web studio is an Express application. It receives generation requests and streams progress to the browser with SSE. The Python engine owns lyrics retrieval, transliteration, subtitle generation, Pillow image composition, and FFmpeg rendering. Filesystem folders supply fonts, emoji artwork, headers, and background video clips.

## Module graph

```mermaid
graph TD
  UI[public/index.html + app.js] --> Server[src/index.js]
  Server --> Engine[generator.py]
  Engine --> Lyrics[Subtitle and lyric providers]
  Engine --> Xlit[indicxlit_runner.py]
  Engine --> Assets[fonts + emoji_assets + headers + videos/input]
  Engine --> Render[Single FFmpeg process]
  Render --> Output[videos/output]
```

## Constraints

- `.venv310\\Scripts\\python.exe` is required for the Python/IndicXlit environment.
- Existing templates are invariants; changes require explicit permission for that template.
- Rendering is one FFmpeg composition pass.
- `.env` is never edited or logged by agents.
- Missing usable lyrics must stop before FFmpeg, rather than produce a blank MP4.
