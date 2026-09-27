"""
🧪 Verification Test Suite for Folder Queue Manager & Multi-Brand Auto-Publisher
"""

import os
import shutil
import tempfile
from pathlib import Path

from app.config import MEDIA_QUEUE_DIR
from app.core.database import init_db, list_brands
from app.core.folder_queue_manager import (
    ensure_brand_folders,
    get_brand_folder_path,
    list_pending_media_for_brand,
    list_posted_media_for_brand,
    parse_sidecar_metadata,
    archive_media_file,
    get_all_brands_folder_status,
    clean_title_from_filename
)


def setup_module():
    init_db()
    ensure_brand_folders()


def test_clean_title_from_filename():
    assert clean_title_from_filename("01_Channa_Mereya_Lofi.mp4") == "Channa Mereya Lofi"
    assert clean_title_from_filename("02 - Tum Hi Ho - Hook.mp4") == "Tum Hi Ho - Hook"
    assert clean_title_from_filename("kesariya_slowed_reverb.mp4") == "kesariya slowed reverb"


def test_filename_timestamp_and_metadata_extraction():
    from app.core.folder_queue_manager import extract_metadata_from_filename, parse_timestamp_from_string

    # 1. Bracketed timestamp [00:30]
    m1 = extract_metadata_from_filename("01_Kesariya - Arijit Singh [00:30] #lofi #lyrics.mp4", "Lyrical786")
    assert m1["title"] == "Kesariya - Arijit Singh"
    assert m1["audio_start_sec"] == 30.0
    assert m1["music_query"] == "Kesariya - Arijit Singh"
    assert "00:30" in m1["caption"]
    assert "#lofi" in m1["caption"]
    assert "#lyrics" in m1["caption"]

    # 2. Parenthesis timestamp (01:15)
    m2 = extract_metadata_from_filename("Apna Bana Le (01:15).mp4", "Lyrics on lips")
    assert m2["title"] == "Apna Bana Le"
    assert m2["audio_start_sec"] == 75.0
    assert "01:15" in m2["caption"]

    # 3. Direct seconds format 45s
    m3 = extract_metadata_from_filename("Raataan Lambiyan 45s #trending.mp4", "Up To Clouds")
    assert m3["title"] == "Raataan Lambiyan"
    assert m3["audio_start_sec"] == 45.0
    assert "#trending" in m3["caption"]

    # 4. Dot timestamp (0.35)
    m4 = extract_metadata_from_filename("Tum Hi Ho - Arijit Singh (0.35).mp4", "Lyrical786")
    assert m4["title"] == "Tum Hi Ho - Arijit Singh"
    assert m4["audio_start_sec"] == 35.0

    # 5. Timestamp parsing helper directly
    assert parse_timestamp_from_string("[00:45]") == 45.0
    assert parse_timestamp_from_string("(1:30)") == 90.0
    assert parse_timestamp_from_string("start_20") == 20.0
    assert parse_timestamp_from_string("90s") == 90.0


def test_ensure_brand_folders():
    ensure_brand_folders()
    brands = list_brands()
    assert len(brands) > 0
    for b in brands:
        folder = get_brand_folder_path(b.name)
        assert folder.exists()
        assert (folder / "posted").exists()


def test_queue_detection_and_metadata_parsing(tmp_path):
    brand_name = "TestBrand"
    brand_folder = MEDIA_QUEUE_DIR / brand_name
    brand_folder.mkdir(parents=True, exist_ok=True)
    posted_folder = brand_folder / "posted"
    posted_folder.mkdir(parents=True, exist_ok=True)

    try:
        # Create test video + txt sidecar
        video1 = brand_folder / "01_Apna_Bana_Le.mp4"
        txt1 = brand_folder / "01_Apna_Bana_Le.txt"
        video1.write_bytes(b"dummy video data 1")
        txt1.write_text("Custom lyric caption for Apna Bana Le #lyrics #test", encoding="utf-8")

        # Create test video + json sidecar
        video2 = brand_folder / "02_Raataan_Lambiyan.mp4"
        json2 = brand_folder / "02_Raataan_Lambiyan.json"
        video2.write_bytes(b"dummy video data 2")
        json2.write_text('{"caption": "JSON caption", "music_query": "Raataan Lambiyan Jubin Nautiyal"}', encoding="utf-8")

        # Create test image without sidecar (tests fallback)
        img3 = brand_folder / "03_photo_cover.jpg"
        img3.write_bytes(b"dummy image data")

        # Check pending list
        pending = list_pending_media_for_brand(brand_name)
        assert len(pending) == 3

        # Test metadata parsing
        meta1 = parse_sidecar_metadata(video1, brand_name)
        assert meta1["caption"] == "Custom lyric caption for Apna Bana Le #lyrics #test"

        meta2 = parse_sidecar_metadata(video2, brand_name)
        assert meta2["caption"] == "JSON caption"
        assert meta2["music_query"] == "Raataan Lambiyan Jubin Nautiyal"

        meta3 = parse_sidecar_metadata(img3, brand_name)
        assert "photo cover" in meta3["caption"]
        assert "#reels" in meta3["caption"]

        # Test archiving
        archived = archive_media_file(video1, brand_name)
        assert archived.exists()
        assert archived.parent == posted_folder
        assert not video1.exists()
        assert not txt1.exists()
        assert (posted_folder / "01_Apna_Bana_Le.txt").exists()

        # Check pending list after archive
        pending_after = list_pending_media_for_brand(brand_name)
        assert len(pending_after) == 2

        posted_list = list_posted_media_for_brand(brand_name)
        assert len(posted_list) >= 1

    finally:
        # Cleanup test folder
        if brand_folder.exists():
            shutil.rmtree(str(brand_folder), ignore_errors=True)


def test_get_all_brands_folder_status():
    status = get_all_brands_folder_status()
    assert isinstance(status, list)
    assert len(status) > 0
    for s in status:
        assert "brand_id" in s
        assert "brand_name" in s
        assert "pending_count" in s
        assert "folder_path" in s
