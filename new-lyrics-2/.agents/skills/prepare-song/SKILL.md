---
name: prepare-song
description: Creates a structured song-production brief from creator-supplied metadata, lyric verification, visual shortlist, and chosen template. Use before generating a lyric video.
---

# Prepare a song project

The creator supplies or manually confirms:

- Song title, artist, and source URL.
- Correct lyric source and whether timing is credible.
- Chosen template.
- A shortlist of 3 to 5 background clip paths.
- Intended output mode and upload destination.

Do not browse a large asset library to select visuals. Do not copy full copyrighted lyrics into the Creator Vault.

Create or update a song brief in the Creator Vault using this format:

```markdown
# <Artist> — <Song>

## Source
- URL:
- Track metadata checked by creator: yes/no
- Lyric source:
- Timing confidence: high/medium/low

## Visual direction
- Template:
- Background shortlist:
- Creator's selected clip:
- Mood/reference:

## Language
- Indic script detected: yes/no
- Transliteration required: yes/no

## Render
- Mode: fast/final
- Output path:
- Render result:

## QA notes
- Creator review timestamps:
- Approved: yes/no
```

If the selected template is `yt_hindi_type`, read `yt-hindi-type-contract` first. If it is any existing template, read `template-invariants` first.
