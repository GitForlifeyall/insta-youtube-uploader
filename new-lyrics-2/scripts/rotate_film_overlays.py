"""
Rotates all horizontal video clips in FILM OVERLAY/ to vertical 1080x1920 (9:16).
"""

import os
import sys
import subprocess
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERLAY_DIR = os.path.join(ROOT_DIR, "FILM OVERLAY")


def probe_video(file_path: str):
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        file_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)
    stream = data["streams"][0]
    return int(stream["width"]), int(stream["height"])


def rotate_and_scale_video(file_path: str, width: int, height: int):
    ext = os.path.splitext(file_path)[1]
    tmp_path = file_path + f".vertical_tmp{ext}"

    # Rotate 90 degrees clockwise (transpose=1) and ensure 1080x1920
    vf_filter = "transpose=1,scale=1080:1920"

    cmd = [
        "ffmpeg", "-y",
        "-i", file_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "17",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        tmp_path
    ]

    print(f"Processing: {os.path.basename(file_path)} ({width}x{height} -> 1080x1920)...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        # If copy audio fails, retry re-encoding audio
        cmd_fallback = [
            "ffmpeg", "-y",
            "-i", file_path,
            "-vf", vf_filter,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "17",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            tmp_path
        ]
        res = subprocess.run(cmd_fallback, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"ERROR rotating {file_path}: {res.stderr}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return False

    if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 1000:
        os.replace(tmp_path, file_path)
        print(f"Successfully replaced: {os.path.basename(file_path)}")
        return True
    else:
        print(f"Failed to generate valid output for: {file_path}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False


def main():
    if not os.path.exists(OVERLAY_DIR):
        print(f"Directory not found: {OVERLAY_DIR}")
        return

    files = [
        os.path.join(OVERLAY_DIR, f)
        for f in os.listdir(OVERLAY_DIR)
        if f.lower().endswith((".mp4", ".mov", ".mkv", ".webm")) and not f.startswith(".")
    ]

    print(f"Found {len(files)} total video files in FILM OVERLAY/")
    rotated_count = 0
    skipped_count = 0

    for f in files:
        try:
            w, h = probe_video(f)
            if w > h:
                success = rotate_and_scale_video(f, w, h)
                if success:
                    rotated_count += 1
            else:
                print(f"Skipping (already vertical): {os.path.basename(f)} ({w}x{h})")
                skipped_count += 1
        except Exception as e:
            print(f"Error checking {os.path.basename(f)}: {e}")

    print(f"\nDone! Rotated: {rotated_count}, Already vertical: {skipped_count}")


if __name__ == "__main__":
    main()
