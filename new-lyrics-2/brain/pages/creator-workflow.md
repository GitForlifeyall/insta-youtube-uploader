---
id: creator-workflow
title: Creator workflow keeps human creative judgment and automates structured follow-through
category: project
status: active
tags: [creator, workflow, token-efficiency]
created: "2026-09-16T00:32:51"
updated: "2026-09-16T00:33:06"
---

<!-- compiled_truth -->
## Current understanding

The creator manually chooses song metadata, lyric correctness, background-video shortlist, final visual taste, upload permissions, and time-coded render feedback. The agent turns those inputs into structured song briefs, checklists, diagnostics, research synthesis, and durable decisions. This keeps creative judgment with the creator and avoids spending model context on raw media browsing or reconstructing choices later.

## Minimum operating loop

1. Capture a song or idea in the creator vault Inbox.
2. Manually shortlist backgrounds and verify the song/lyrics.
3. Invoke `prepare-song` for a structured brief.
4. Generate and watch the render manually.
5. Record timestamped issues or a short approval note.
6. Invoke `save-decision` only when the outcome creates a lasting rule or preference.

## Related context

- [[agent-safety-and-scope]]
- [[yt-hindi-type-contract]]


## Timeline

- time: 2026-09-16T00:32:51
  kind: decision
  summary: "Created this page: Creator workflow keeps human creative judgment and automates structured follow-through"
  source: AGENTS.md and repository inspection
  affects: [creator-workflow]

- time: 2026-09-16T00:33:06
  kind: decision
  summary: Recorded the division between human creative choices and agent synthesis.
  source: AGENTS.md and repository inspection
  affects: [creator-workflow]
