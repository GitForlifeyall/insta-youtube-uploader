# CLI Uploader for YouTube Shorts (Autonomous Redroid Engine)

An autonomous batch publishing pipeline for YouTube Shorts with Redroid container lifecycle management, Scrcpy mirroring, JSON metadata extraction, and automatic post-upload shutdown.

---

## 🚀 Key Features

1. **Full Container Lifecycle Management**:
   - Automatically spins up the required Redroid container (`.\redroid.ps1 start <brand>`).
   - Automatically opens the **Scrcpy** live screen mirroring window on your desktop.
   - Once all uploads finish, waits **3 minutes** (with a live terminal countdown) and automatically shuts down the container (`.\redroid.ps1 stop <brand>`).

2. **Random Video Selection**:
   - Randomly selects video(s) from the brand's designated directory in `brand folders/<Brand Name>/`.
   - Specify `--count N` to upload `N` random videos, or `--all` to upload everything.

3. **Intelligent JSON Metadata Extraction**:
   - Automatically scans JSON files in the brand folder (and falls back to `links.json` in the workspace root).
   - Matches videos by filename, stem, or item index.
   - Extracts:
     - **Caption / Description**
     - **Song Name & Artist Name** (builds an optimized search query for YouTube's music library)
     - **Audio Timestamps** (e.g. `'0:15'`, `'random'`, etc.)
     - **Hashtags**

4. **Multi-Brand SQLite Registry**:
   - Queries `data/brands.db` to automatically determine ADB targets, container names, and content folders.

---

## 💻 CLI Commands

### 1. Zero-Config Run (Pick a Random Video, Extract Metadata, Upload & Shutdown)
```powershell
python "cli uploader\uploader.py" -b 01
```
*What happens:*
1. Starts container `redroid-01` (`127.0.0.1:5801`).
2. Opens live Scrcpy desktop window.
3. Randomly picks a video from `brand folders\Account 01\`.
4. Finds its matching entry in JSON files, extracts song name, artist, timestamp, and caption.
5. Uploads to YouTube via `upload_short.py`.
6. Waits 3 minutes, then gracefully stops `redroid-01`.

### 2. Upload for a Named Brand (e.g. Brand Alpha)
```powershell
python "cli uploader\uploader.py" -b "Brand Alpha"
```

### 3. Upload 3 Random Videos in Batch
```powershell
python "cli uploader\uploader.py" -b 02 -k 3
```

### 4. Upload All Videos in the Brand Folder Sequentially
```powershell
python "cli uploader\uploader.py" -b 01 --all --no-random
```

### 5. Keep Container Running (Skip Auto-Shutdown)
```powershell
python "cli uploader\uploader.py" -b 01 --no-close
```

### 6. Custom Shutdown Wait Timer (e.g. 60 seconds instead of 180s)
```powershell
python "cli uploader\uploader.py" -b 01 --wait 60
```

### 7. Custom Manual Overrides (Override Song / Caption)
```powershell
python "cli uploader\uploader.py" -b 01 -s "Lo-Fi Beats" -t "0:15" -c "Custom Caption #shorts"
```

---

## 🛠️ Python Function Usage

```python
from uploader import upload_short_pipeline

results = upload_short_pipeline(
    brand_name="01",            # Brand or Account (01, 02, "Brand Alpha")
    content_folder=None,        # None = Auto-loads from brand folders/<Brand Name>
    random_select=True,         # Randomly select videos
    count=1,                    # Number of videos to upload
    auto_start=True,            # Auto-starts redroid container
    view=True,                  # Auto-launches Scrcpy live mirror
    auto_close=True,            # Auto-stops container after wait
    wait_close_seconds=180,     # Wait 3 mins before shutdown
    clean_before=False          # Clean emulator media first
)

for r in results:
    print(f"Video: {r['video_name']} -> Success: {r['success']}")
```

---

## 📋 Command Flags Reference

| Flag | Argument | Description | Default |
|---|---|---|---|
| `-b`, `--brand` | `NAME` | Brand or Account (`01`, `02`, `Brand Alpha`, etc.) | `01` |
| `-f`, `--folder` | `PATH` | Custom folder or video file | Brand folder in `brand folders/` |
| `-k`, `--count` | `INT` | Number of random videos to upload | `1` |
| `--all` | `FLAG` | Upload all videos in folder | `False` |
| `--no-random` | `FLAG` | Process sequentially instead of random | `False` |
| `-c`, `--caption` | `TEXT` | Title/Caption override | Auto from JSON / filename |
| `-s`, `--song` | `NAME` | Song / sound override | Auto from JSON |
| `-t`, `--timestamp` | `TIME` | Timestamp override (e.g. `'0:15'`) | Auto from JSON |
| `-m`, `--name` | `NAME` | Custom Android MediaStore filename | Auto-generated |
| `--no-scrcpy` | `FLAG` | Disable Scrcpy screen mirror | `False` (Mirror enabled) |
| `--no-start` | `FLAG` | Skip auto-starting container | `False` (Auto-start enabled) |
| `--no-close` | `FLAG` | Keep container running after upload | `False` (Auto-close enabled) |
| `--wait` | `SECS` | Seconds to wait before closing container | `180` (3 minutes) |
| `--clean` | `FLAG` | Reset YouTube drafts before upload | `False` |
