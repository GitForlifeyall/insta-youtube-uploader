---
slug: background
title: Project background
role: project background
updated: "2026-09-16T00:31:47"
---

# Project background

## Why

LyricalVideo turns a song URL or track into a finished lyric video without requiring the creator to hand-time captions, build subtitle files, or assemble the video layers manually.

## Goals

- Produce usable lyric videos from a browser-based studio.
- Prefer genuinely timed lyrics and stop safely when none are available.
- Support several stable visual templates without accidental style regressions.
- Render the background, header, captions, and audio in one FFmpeg pass.
- Support Hinglish and Roman Punjabi output for YT Hindi Type when source lyrics use Indic scripts.

## Non-goals

- Replacing a full professional NLE for frame-by-frame creative editing.
- Changing an existing template's default visual language without explicit user approval.
- Storing secrets, cookies, or copyrighted raw lyric archives in project memory.

## Target user

A creator who wants fast, repeatable lyric-video production while retaining control over the final song metadata, selected background clips, and visual judgment.
