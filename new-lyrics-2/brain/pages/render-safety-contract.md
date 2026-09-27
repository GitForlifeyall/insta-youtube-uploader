---
id: render-safety-contract
title: Use single-pass rendering and stop before FFmpeg when lyrics are unusable
category: decision
status: active
tags: [rendering, ffmpeg, reliability]
created: "2026-09-16T00:32:46"
updated: "2026-09-16T00:33:01"
---

<!-- compiled_truth -->
## Current understanding

The final composition of background video, top header, ASS subtitles, and audio must happen in a single FFmpeg process. Final output targets 1080x1920 at 30 FPS with a Windows Media Foundation or NVENC encoder when available and libx264 fallback. Fast output targets 540x960 at 24 FPS with libx264 ultrafast CRF 26. If every lyric provider returns zero usable lines, the engine must stop before FFmpeg and emit the documented no-lyrics message; it must never output a blank or corrupt MP4.

## Practical consequence

A rendering fix must preserve the no-lyrics guard and single-pass composition unless the user explicitly approves a new rendering architecture.

## Related context

- [[lyrics-retrieval-hierarchy]]
- [[agent-safety-and-scope]]


## Timeline

- time: 2026-09-16T00:32:46
  kind: decision
  summary: "Created this page: Use single-pass rendering and stop before FFmpeg when lyrics are unusable"
  source: AGENTS.md and repository inspection
  affects: [render-safety-contract]

- time: 2026-09-16T00:33:01
  kind: decision
  summary: Recorded the one-pass render rule and the no-lyrics stop condition.
  source: AGENTS.md and repository inspection
  affects: [render-safety-contract]
