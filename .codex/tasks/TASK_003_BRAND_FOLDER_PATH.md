# Task 003: Brand Folder Path Tracking in SQLite Database

- **Task Type**: Small Task (CLI Enhancement & Database Column Management)
- **Status**: COMPLETED
- **Assigned To**: Codex
- **Target File**: `cli uploader/db.py`

## Objective
Ensure the SQLite database tracks the `folder_path` for every brand, provides a dedicated `set-folder` CLI command to assign/update content folders dynamically, and ensures all current brands have verified folder paths provisioned on disk.

## Requirements
1. Verify `folder_path` column in `brands` table schema in `data/brands.db`.
2. Add `update_brand_folder(brand_id, folder_path)` function.
3. Expose `python db.py set-folder <identifier> <folder_path>` in the CLI.
4. Verify table display prints full/relative folder path cleanly.
5. Verify with automated tests.
