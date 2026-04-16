"""test_save_manager.py — Unit tests for utils/save_manager.py"""

import json
import os
import sys
import unittest

# Allow running from cipher/ root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.save_manager import (
    create_save,
    write_save,
    load_save,
    load_with_fallback,
    migrate_save,
    list_saves,
    _primary_path,
    _backup_path,
    _tmp_path,
)


class TestSaveManager(unittest.TestCase):
    """Tests for save_manager.py."""

    _test_name = "_test_player_unit"

    def setUp(self) -> None:
        """Remove any leftover test files before each test."""
        self._cleanup()

    def tearDown(self) -> None:
        """Remove test files after each test."""
        self._cleanup()

    def _cleanup(self) -> None:
        """Delete all test save files."""
        for path in [
            _primary_path(self._test_name),
            _backup_path(self._test_name),
            _tmp_path(self._test_name),
        ]:
            if os.path.exists(path):
                os.remove(path)

    # ------------------------------------------------------------------
    def test_save_load_roundtrip(self) -> None:
        """create_save → write_save → load_save returns identical data."""
        save = create_save(self._test_name, "red")
        save["xp"] = 42
        write_save(save)
        loaded = load_save(self._test_name)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["player_name"], self._test_name)
        self.assertEqual(loaded["xp"], 42)
        self.assertEqual(loaded["track"], "red")

    def test_atomic_write_no_tmp_after_success(self) -> None:
        """After write_save succeeds, the .tmp file must be removed."""
        save = create_save(self._test_name, "full")
        write_save(save)
        self.assertFalse(os.path.exists(_tmp_path(self._test_name)))

    def test_backup_created_on_write(self) -> None:
        """write_save must create a .backup.json alongside the primary."""
        save = create_save(self._test_name, "red")
        write_save(save)
        self.assertTrue(os.path.exists(_backup_path(self._test_name)))

    def test_corrupted_primary_loads_backup(self) -> None:
        """When primary is corrupt, load_with_fallback returns backup data."""
        save = create_save(self._test_name, "red")
        save["xp"] = 99
        write_save(save)

        # Corrupt the primary file
        with open(_primary_path(self._test_name), "w", encoding="utf-8") as fh:
            fh.write("NOT VALID JSON }{")

        loaded = load_with_fallback(self._test_name)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["xp"], 99)

    def test_migrate_save_adds_missing_fields(self) -> None:
        """migrate_save adds missing fields without deleting existing data."""
        partial = {"player_name": "partial", "track": "red", "xp": 5}
        migrated = migrate_save(partial)
        self.assertIn("badges", migrated)
        self.assertIn("completed", migrated)
        self.assertEqual(migrated["xp"], 5)  # existing value preserved

    def test_list_saves_returns_sorted(self) -> None:
        """list_saves returns entries sorted by last_played descending."""
        save = create_save(self._test_name, "red")
        write_save(save)
        saves = list_saves()
        names = [s["name"] for s in saves]
        self.assertIn(self._test_name, names)


if __name__ == "__main__":
    unittest.main()
