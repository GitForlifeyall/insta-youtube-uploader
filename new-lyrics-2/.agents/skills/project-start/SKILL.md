---
name: project-start
description: Loads only the project instructions and durable brain context needed for a new LyricalVideo task. Use at the start of a new Antigravity session or when task context is unclear.
---

# Start a focused LyricalVideo task

1. Read `AGENTS.md` and `BRAIN.md` completely.
2. Run `npx --yes @mindmux/brain-md list-pages`.
3. Classify the task as one of: UI/API, lyrics, transliteration, rendering, template-specific, carousel, asset selection, or planning.
4. Read only the related root page(s) and durable page(s):
   - UI/API: `architecture`, `flow`, `agent-safety-and-scope`
   - Lyrics/transliteration: `flow`, `lyrics-retrieval-hierarchy`, `yt-hindi-type-contract` when relevant
   - Rendering: `architecture`, `flow`, `render-safety-contract`
   - Template-specific: `template-invariants` plus `yt-hindi-type-contract` for YT Hindi Type
   - Creator planning: `creator-workflow`, `agent-safety-and-scope`
5. State the loaded context and the smallest file set needed. Do not edit yet unless the creator requested implementation.

Avoid reading `videos/`, `emoji_assets/`, `fonts/`, `.env`, and large source files unless the task requires a named item.
