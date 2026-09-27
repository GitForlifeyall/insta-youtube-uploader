---
id: yt-hindi-type-contract
title: YT Hindi Type has a protected cinematic layout and Roman-script requirement
category: decision
status: active
tags: [template, yt-hindi-type, transliteration]
created: "2026-09-16T00:32:43"
updated: "2026-09-16T00:32:59"
---

<!-- compiled_truth -->
## Current understanding

`yt_hindi_type` renders a 1080x720 rectangular input clip centered on a 1080x1920 black canvas. Main lyrics use centered, naturally cased EB Garamond at 44pt with `\\fad(210,210)`. The top header uses Georgia Italic and Apple-style emoji PNG compositing, centered in the upper black letterbox. If lyrics contain Devanagari or Gurmukhi script, IndicXlit converts them to Roman script; the final rendered video must not contain Devanagari.

## Practical consequence

Do not alter its typography, layout, header approach, fade behavior, emoji approach, or script requirement without explicit permission for YT Hindi Type.

## Related context

- [[template-invariants]]
- [[lyrics-retrieval-hierarchy]]


## Timeline

- time: 2026-09-16T00:32:43
  kind: decision
  summary: "Created this page: YT Hindi Type has a protected cinematic layout and Roman-script requirement"
  source: AGENTS.md and repository inspection
  affects: [yt-hindi-type-contract]

- time: 2026-09-16T00:32:59
  kind: decision
  summary: "Recorded the protected layout, typography, and Indic-script behavior."
  source: AGENTS.md and repository inspection
  affects: [yt-hindi-type-contract]
