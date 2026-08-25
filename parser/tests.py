import json
import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from .dataset_parser import DatasetParserError, parse_dataset


class DatasetParserTests(SimpleTestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.dataset = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_parses_supported_files_and_describes_binary_files(self):
        (self.dataset / "trials.csv").write_text("name,score\nAda,3\n", encoding="utf-8-sig")
        (self.dataset / "events.trg").write_text("0.0 0\n1.25 320 8 response\n", encoding="ascii")
        (self.dataset / "project.bst").write_text(json.dumps({"version": 1}), encoding="utf-8")
        (self.dataset / "recording.cnt").write_bytes(b"binary eeg")

        result = parse_dataset(self.dataset)
        by_name = {item["name"]: item for item in result["files"]}

        self.assertEqual(result["file_count"], 4)
        self.assertEqual(by_name["trials.csv"]["data"]["rows"][0]["name"], "Ada")
        self.assertIsNone(by_name["events.trg"]["data"]["events"][0]["code"])
        self.assertEqual(by_name["events.trg"]["data"]["events"][1]["sample"], 320)
        self.assertEqual(by_name["project.bst"]["data"], {"version": 1})
        self.assertEqual(by_name["recording.cnt"]["status"], "binary")
        self.assertEqual(len(by_name["recording.cnt"]["data"]["sha256"]), 64)

    def test_bad_known_file_is_reported_without_stopping_other_files(self):
        (self.dataset / "bad.trg").write_text("not a trigger\n", encoding="ascii")
        (self.dataset / "good.json").write_text("{}", encoding="utf-8")

        result = parse_dataset(self.dataset)

        self.assertEqual(result["file_count"], 2)
        self.assertEqual(result["files"][0]["status"], "error")
        self.assertEqual(result["files"][1]["status"], "parsed")

    def test_missing_directory_raises_clear_error(self):
        with self.assertRaises(DatasetParserError):
            parse_dataset(self.dataset / "missing")
