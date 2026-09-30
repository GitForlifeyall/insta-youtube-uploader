# Codex Task: CLI Uploader Implementation

## Task Description
Create a standalone CLI tool in `cli uploader/` that provides:
- A Python function `upload_shorts_batch` / `upload_short_pipeline` accepting:
  - `brand_name` (e.g. `01`, `02`, `Brand Alpha`)
  - `content_folder` (folder containing videos or path to video)
  - `caption` / `title`
  - `song_name` / `sound`
  - `timestamp` (e.g. `0:15`, `random`, or custom)
  - `media_name` (optional custom Android storage name)
  - `view` (launch scrcpy)
  - `adb_path`, `scrcpy_path`
  - `clean_before` (cleans emulator session & MediaStore)
- A full CLI command-line interface with `argparse`.
- Clean error handling, logging, and summary reporting.

## Status: COMPLETED
- Implementation: `cli uploader/uploader.py`
- Documentation: `cli uploader/README.md`
- Verification: CLI help test passed with code 0.
