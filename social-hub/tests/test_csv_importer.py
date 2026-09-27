import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch


SOCIAL_HUB_ROOT = Path(__file__).resolve().parents[1]
if str(SOCIAL_HUB_ROOT) not in sys.path:
    sys.path.insert(0, str(SOCIAL_HUB_ROOT))

from app.core import csv_importer
from app.core.models import Brand


class CsvImporterTests(unittest.TestCase):
    def setUp(self):
        self.brand = Brand(
            id="brand-1",
            name="Lyrical786",
            color_badge="#8ACE00",
            description=None,
            created_at="2026-01-01T00:00:00",
            profiles=[],
        )
        self.brands_patch = patch.object(csv_importer, "list_brands", return_value=[self.brand])
        self.brands_patch.start()
        self.addCleanup(self.brands_patch.stop)

    def future_date(self, days=30):
        return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    def test_metricool_csv_maps_caption_date_and_platforms(self):
        csv_text = (
            "Text,Date,Time,Instagram,Threads,Picture Url 1,Brand name,Draft\n"
            f'"A Metricool post",{self.future_date()},14:30:00,true,true,https://cdn.example.com/reel.mp4,Lyrical786,false\n'
        )

        report = csv_importer.validate_csv_content(csv_text)
        post = report["posts"][0]

        self.assertEqual(report["format_detected"], "metricool")
        self.assertEqual(post["caption"], "A Metricool post")
        self.assertEqual(post["platforms"], ["instagram", "threads"])
        self.assertEqual(post["video_path"], "https://cdn.example.com/reel.mp4")
        self.assertTrue(post["can_import"])

    def test_custom_csv_resolves_existing_video_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "existing-reel.mp4"
            media_path.write_bytes(b"video")
            csv_text = (
                "brand_name,text,date,time,video_path,video_url,instagram,facebook,threads,youtube,draft\n"
                f'Lyrical786,Local video,{self.future_date()},19:30,{media_path},,true,false,false,false,false\n'
            )

            report = csv_importer.validate_csv_content(csv_text)
            post = report["posts"][0]

        self.assertEqual(report["format_detected"], "custom")
        self.assertEqual(post["video_path"], str(media_path.resolve()))
        self.assertFalse(post["error_media"])
        self.assertTrue(post["can_import"])

    def test_custom_csv_accepts_http_video_url(self):
        csv_text = (
            "brand_name,text,date,time,video_path,video_url,instagram,facebook,threads,youtube,draft\n"
            f"Lyrical786,Remote video,{self.future_date()},13:00,,https://cdn.example.com/reel.mp4,true,false,false,false,false\n"
        )

        post = csv_importer.validate_csv_content(csv_text)["posts"][0]

        self.assertEqual(post["video_path"], "https://cdn.example.com/reel.mp4")
        self.assertFalse(post["error_media"])
        self.assertTrue(post["can_import"])

    def test_invalid_brand_is_non_importable_error(self):
        csv_text = (
            "brand_name,text,date,time,video_url,instagram\n"
            f"Unknown Brand,Post,{self.future_date()},13:00,https://cdn.example.com/reel.mp4,true\n"
        )

        post = csv_importer.validate_csv_content(csv_text)["posts"][0]

        self.assertTrue(post["error_brand"])
        self.assertEqual(post["status"], "error")
        self.assertFalse(post["can_import"])

    def test_missing_media_is_imported_as_draft_with_media_error(self):
        csv_text = (
            "brand_name,text,date,time,video_path,instagram\n"
            f"Lyrical786,Missing video,{self.future_date()},13:00,does-not-exist.mp4,true\n"
        )

        post = csv_importer.validate_csv_content(csv_text)["posts"][0]

        self.assertTrue(post["error_media"])
        self.assertTrue(post["import_as_draft"])
        self.assertTrue(post["can_import"])

    def test_no_platforms_is_a_non_importable_error(self):
        csv_text = (
            "brand_name,text,date,time,video_url,instagram,facebook,threads,youtube\n"
            f"Lyrical786,No target,{self.future_date()},13:00,https://cdn.example.com/reel.mp4,false,false,false,false\n"
        )

        post = csv_importer.validate_csv_content(csv_text)["posts"][0]

        self.assertTrue(post["error_platforms"])
        self.assertEqual(post["status"], "error")
        self.assertFalse(post["can_import"])

    def test_date_and_time_format_variations(self):
        yyyy, _, _, _ = csv_importer.parse_datetime_flexible("2026-10-01", "14:30:00", "YYYY-MM-DD", "24h")
        dmy, _, _, _ = csv_importer.parse_datetime_flexible("01/10/2026", "02:30 PM", "DD/MM/YYYY", "12h")
        mdy, _, _, _ = csv_importer.parse_datetime_flexible("10/01/2026", "14:30", "MM/DD/YYYY", "24h")

        self.assertEqual(yyyy.date().isoformat(), "2026-10-01")
        self.assertEqual(dmy.date().isoformat(), "2026-10-01")
        self.assertEqual(dmy.hour, 14)
        self.assertEqual(mdy.date().isoformat(), "2026-10-01")
        self.assertEqual(mdy.hour, 14)

    def test_past_and_malformed_dates_are_flagged(self):
        past = csv_importer.parse_datetime_flexible("2020-01-01", "13:00", "YYYY-MM-DD", "24h")
        malformed = csv_importer.parse_datetime_flexible("not-a-date", "13:00", "YYYY-MM-DD", "24h")

        self.assertTrue(any("past" in warning.lower() for warning in past[3]))
        self.assertTrue(any("invalid date" in warning.lower() for warning in malformed[3]))


if __name__ == "__main__":
    unittest.main()
