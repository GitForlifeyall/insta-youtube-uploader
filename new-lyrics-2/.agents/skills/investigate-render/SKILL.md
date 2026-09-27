---
name: investigate-render
description: Diagnoses one specific lyric-video render failure or visual defect from bounded evidence. Use when a generation fails, produces no output, has unsynced captions, or needs a targeted visual correction.
---

# Investigate a render

Read `AGENTS.md`, `BRAIN.md`, `render-safety-contract`, and the relevant template decision.

Require at least one of:

- Exact console/SSE error excerpt.
- Named output path.
- FFmpeg command or log.
- Screenshot.
- Creator-observed timestamp and a concise description.

Then:

1. Identify whether the failure is lyric retrieval, transliteration, ASS generation, Pillow/header composition, FFmpeg, codec/accelerator, filesystem, or visual QA.
2. Inspect only directly related files.
3. Explain the most likely cause and a minimal fix.
4. Ask before changing protected template rendering behavior.
5. Verify with the smallest reproduction possible; do not batch-render or overwrite outputs without approval.
6. Capture a brain decision only if the fix creates a recurring rule or an architectural constraint.
