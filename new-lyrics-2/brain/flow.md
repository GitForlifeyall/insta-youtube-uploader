---
slug: flow
title: Key flows
role: key flows
updated: "2026-09-16T00:31:53"
---

# Key flows

## End-to-end path of a typical request

```mermaid
sequenceDiagram
  participant C as Creator
  participant UI as Web Studio
  participant S as Express + SSE
  participant E as Python Engine
  participant L as Lyrics Providers
  participant R as FFmpeg
  C->>UI: Choose track, template, and options
  UI->>S: Start generation request
  S->>E: Launch generator and stream progress
  E->>L: Retrieve timed lyrics using provider hierarchy
  alt usable lyrics found
    E->>E: Transliterate Indic script when required
    E->>E: Build ASS captions and header image
    E->>R: Composite video, captions, header, and audio once
    R-->>S: Final MP4 path
    S-->>UI: Progress and completion event
  else no usable lyrics
    E-->>S: Stop with no-lyrics message
    S-->>UI: Safe failure event
  end
```

## Other important flows

- Carousel generation is a separate Pillow renderer and must not alter existing video templates.
- Fast mode targets 540x960 at 24 FPS; final targets 1080x1920 at 30 FPS.
- YT Hindi Type has a separate visual contract: centered 1080x720 video on a 1080x1920 black canvas, EB Garamond lyrics, and Georgia Italic header with Apple-style emoji assets.
