---
id: lyrics-retrieval-hierarchy
title: Prefer timed lyric sources in a strict fallback order
category: decision
status: active
tags: [lyrics, retrieval, timing]
created: "2026-09-16T00:32:41"
updated: "2026-09-16T00:32:56"
---

<!-- compiled_truth -->
## Current understanding

Lyrics are retrieved in this order: creator-provided YouTube manual subtitles; Spotify synced lyrics via the local API when timestamps are non-zero and `syncType` is not `UNSYNCED`; LRCLIB; YouTube auto captions through yt-dlp; then Genius for Romanized lyrics. Provider success is not enough: the engine must verify that the result contains usable timed lines before rendering.

## Why it matters

Timed lyric quality determines caption sync. The hierarchy favors authoritative or synchronized sources before weaker fallbacks. A provider failure should lead to the next provider, not a fabricated or blank caption track.

## Related context

- [[render-safety-contract]]
- [[yt-hindi-type-contract]]


## Timeline

- time: 2026-09-16T00:32:41
  kind: decision
  summary: "Created this page: Prefer timed lyric sources in a strict fallback order"
  source: AGENTS.md and repository inspection
  affects: [lyrics-retrieval-hierarchy]

- time: 2026-09-16T00:32:56
  kind: decision
  summary: Recorded the provider order and timed-lyrics validity rules.
  source: AGENTS.md and repository inspection
  affects: [lyrics-retrieval-hierarchy]
