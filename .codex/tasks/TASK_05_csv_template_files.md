# Codex Task 05: CSV Template Files Creation & Download Endpoints

## Objective
Create the CSV template files and download routes so users can download both the official Metricool CSV format and the streamlined Social Hub Custom CSV format.

## Target Files
1. `social-hub/templates/metricool_template.csv`:
   - Exact Metricool CSV headers provided by the user with 1 sample row.
2. `social-hub/templates/custom_social_hub_template.csv`:
    - Streamlined CSV for our use case:
      `brand_name,text,date,time,video_path,video_url,thumbnail_url,first_comment,song_name,song_start_sec,instagram,facebook,threads,youtube,youtube_title,draft`
    - Include 2 realistic sample rows (one with local `video_path` and one with `video_url`).
3. `social-hub/app/api/routes_bulk.py`:
   - Add `GET /api/posts/templates/metricool` (returns `FileResponse` for `metricool_template.csv`).
   - Add `GET /api/posts/templates/custom` (returns `FileResponse` for `custom_social_hub_template.csv`).

## Expected Output
Both templates available in `social-hub/templates/` and downloadable via browser/API.

## Verification
Run:
```powershell
powershell -Command "Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/posts/templates/custom' -OutFile 'test_custom.csv'"
```
Verify `test_custom.csv` contains the expected columns.

## Status: Completed ✅
