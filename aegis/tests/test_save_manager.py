"""test_save_manager.py — AEGIS CyberForge

Unit tests for aegis/utils/save_manager.py.
"""

import json
import os
import sys
import unittest

# Ensure we can import from aegis/utils/ when run from aegis/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.save_manager import (
    create_save,
    load_save,
    load_with_fallback,
    write_save,
    _primary_path,
    _backup_path,
    _tmp_path,
)

_TEST_NAME = "_test_aegis_analyst"


def _cleanup(name: str) -> None:
    """Remove all save files for a test analyst name."""
    for path in [_primary_path(name), _backup_path(name), _tmp_path(name)]:
        if os.path.exists(path):
            os.remove(path)


class TestSaveLoadRoundtrip(unittest.TestCase):
    """create_save → write_save → load_save returns identical data."""

    def setUp(self) -> None:
        _cleanup(_TEST_NAME)

    def tearDown(self) -> None:
        _cleanup(_TEST_NAME)

    def test_roundtrip(self) -> None:
        save = create_save(_TEST_NAME, "blue")
        write_save(save)
        loaded = load_save(_TEST_NAME)
        self.assertIsNotNone(loaded)
        # player_name and track must survive the round-trip
        self.assertEqual(loaded["player_name"], _TEST_NAME)
        self.assertEqual(loaded["track"], "blue")
        # Core schema fields must be present
        for field in ("xp", "completed", "skipped", "badges", "hints_used",
                      "notes", "metrics", "placement_test"):
            self.assertIn(field, loaded)

    def test_xp_persists(self) -> None:
        save = create_save(_TEST_NAME, "blue")
        save["xp"] = 250
        write_save(save)
        loaded = load_save(_TEST_NAME)
        self.assertEqual(loaded["xp"], 250)


class TestAtomicWrite(unittest.TestCase):
    """write_save removes .tmp after completing successfully."""

    def setUp(self) -> None:
        _cleanup(_TEST_NAME)

    def tearDown(self) -> None:
        _cleanup(_TEST_NAME)

    def test_tmp_removed_after_write(self) -> None:
        save = create_save(_TEST_NAME, "blue")
        write_save(save)
        tmp = _tmp_path(_TEST_NAME)
        self.assertFalse(os.path.exists(tmp), ".tmp file should be gone after write")

    def test_primary_exists_after_write(self) -> None:
        save = create_save(_TEST_NAME, "blue")
        write_save(save)
        self.assertTrue(os.path.exists(_primary_path(_TEST_NAME)))

    def test_backup_exists_after_write(self) -> None:
        save = create_save(_TEST_NAME, "blue")
        write_save(save)
        self.assertTrue(os.path.exists(_backup_path(_TEST_NAME)))


class TestCorruptedPrimaryLoadsBackup(unittest.TestCase):
    """When primary is corrupted, load_with_fallback returns the backup."""

    def setUp(self) -> None:
        _cleanup(_TEST_NAME)

    def tearDown(self) -> None:
        _cleanup(_TEST_NAME)

    def test_corrupt_primary_uses_backup(self) -> None:
        # Write a valid save so backup is created
        save = create_save(_TEST_NAME, "blue")
        save["xp"] = 99
        write_save(save)

        # Corrupt the primary
        with open(_primary_path(_TEST_NAME), "w", encoding="utf-8") as fh:
            fh.write("not valid json {{{")

        loaded = load_with_fallback(_TEST_NAME)
        self.assertIsNotNone(loaded, "Should load from backup when primary is corrupt")
        self.assertEqual(loaded["xp"], 99)


if __name__ == "__main__":
    unittest.main()
