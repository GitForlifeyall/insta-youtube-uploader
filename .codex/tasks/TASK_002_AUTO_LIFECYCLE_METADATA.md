# Codex Task: Automated Redroid Lifecycle & JSON Metadata Matching in CLI Uploader

## Task Requirements:
1. **Container Lifecycle**:
   - Auto-start container using `.\redroid.ps1 start <brand>` before upload.
   - Auto-launch `scrcpy` live mirror.
   - After upload finishes, wait 3 minutes (180s countdown) and close container using `.\redroid.ps1 stop <brand>`.
2. **Random Video Selection**:
   - Pick videos randomly from the brand's designated folder (`brand folders/<Brand Name>`).
3. **JSON Metadata Extraction**:
   - Search `.json` files in the brand folder (and fallback to root `links.json`).
   - Match video filename/stem to JSON entry.
   - Extract title, song name, artist name, caption, hashtags, timestamps.
4. **Execution**:
   - Run `upload_short_to_youtube` with all extracted & passed arguments.

## Status: COMPLETED
- Implemented in: `cli uploader/uploader.py`
- Documented in: `cli uploader/README.md`
- Verification: Metadata extraction tested successfully against `links.json` (767 associations indexed and matched).
