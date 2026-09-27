# Codex Task 07: Isolated Unit Tests for CSV Importer

## Objective
Write comprehensive unit tests in `social-hub/tests/test_csv_importer.py` to verify the parsing and validation logic of `csv_importer.py`.

## Target File
`social-hub/tests/test_csv_importer.py`

## Test Cases to Cover
1. **Metricool CSV Parsing:**
   - Valid Metricool CSV row with `Text`, `Date`, `Time`, and platform booleans (`Instagram: true`, `Threads: true`).
   - Check that fields map correctly to internal post representation.
2. **Custom CSV Parsing:**
   - Valid row with `video_path` that exists on disk.
   - Valid row with `video_url` (http/https).
3. **Validation & Error Flagging:**
   - Post with non-existent brand name $\rightarrow$ marked as `error_brand`.
   - Post with past or malformed date $\rightarrow$ marked with warning/error.
   - Post with missing media path / missing file $\rightarrow$ marked with `error_media` or imported as draft.
   - Post with no platforms selected $\rightarrow$ marked as error.
4. **Date Format Variations:**
   - Test `YYYY-MM-DD`, `DD/MM/YYYY`, and `MM/DD/YYYY`.
   - Test 12-hour (`02:30 PM`) vs 24-hour (`14:30:00`) time parsing.

## Verification Command
```powershell
python -m unittest social-hub/tests/test_csv_importer.py
```

## Status: Completed ✅
