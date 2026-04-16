"""save_manager.py — AEGIS CyberForge

All save file I/O goes through this module only.
Implements atomic write, backup, corruption handling, and migration.
Save files live in aegis/saves/[analyst_name].json.
"""

import json
import os
from datetime import datetime, timedelta, timezone


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _saves_dir() -> str:
    """Return absolute path to the saves/ directory."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "saves")


def _primary_path(player_name: str) -> str:
    """Return path to [player_name].json."""
    return os.path.join(_saves_dir(), f"{player_name}.json")


def _backup_path(player_name: str) -> str:
    """Return path to [player_name].backup.json."""
    return os.path.join(_saves_dir(), f"{player_name}.backup.json")


def _tmp_path(player_name: str) -> str:
    """Return path to [player_name].tmp.json."""
    return os.path.join(_saves_dir(), f"{player_name}.tmp.json")


def _corrupted_path(player_name: str) -> str:
    """Return path to [player_name].corrupted.json."""
    return os.path.join(_saves_dir(), f"{player_name}.corrupted.json")


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def _default_save(player_name: str, track: str) -> dict:
    """Return a new save dict with all required fields.

    Schema:
        player_name, track, created_at, last_played,
        total_time_played_seconds, streak, xp, placement_test,
        badges, completed, skipped, in_progress, hints_used,
        notes, metrics

    metrics[case_id] entries are created on-demand via setdefault() in
    the case runner — they are NOT pre-populated here.
    """
    now = datetime.now(timezone.utc).isoformat()
    return {
        "player_name": player_name,
        "track": track,
        "created_at": now,
        "last_played": now,
        "total_time_played_seconds": 0,
        "streak": {
            "current": 0,
            "longest": 0,
            "last_played_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        },
        "xp": 0,
        "placement_test": {
            "taken": False,
            "score": 0,
            "passed": False,
        },
        "badges": [],
        "completed": [],
        "skipped": [],
        "in_progress": "",
        "hints_used": {},
        "notes": {},
        "metrics": {},
    }


_REQUIRED_FIELDS = (
    "player_name", "track", "created_at", "last_played",
    "total_time_played_seconds", "streak", "xp", "placement_test",
    "badges", "completed", "skipped", "in_progress", "hints_used",
    "notes", "metrics",
)


def _validate_schema(data: dict) -> bool:
    """Return True if save data contains all required top-level fields."""
    return all(field in data for field in _REQUIRED_FIELDS)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_save(player_name: str, track: str) -> dict:
    """Return new save dict and ensure the saves/ directory exists."""
    saves = _saves_dir()
    try:
        os.makedirs(saves, exist_ok=True)
    except OSError as exc:
        raise OSError(
            f"Cannot write to saves/. Check folder permissions. ({exc})"
        ) from exc
    return _default_save(player_name, track)


def write_save(save_data: dict) -> None:
    """Atomically write save_data to saves/[player_name].json.

    Pattern: write to .tmp → verify JSON parses → rename to .json →
    write backup to .backup.json.
    Windows-safe: removes destination before rename if it exists.
    """
    name = save_data["player_name"]
    saves = _saves_dir()
    os.makedirs(saves, exist_ok=True)

    # Update last_played on every write
    save_data["last_played"] = datetime.now(timezone.utc).isoformat()

    # Recompute total time from case metrics
    save_data["total_time_played_seconds"] = sum(
        m.get("time_spent_seconds", 0)
        for m in save_data.get("metrics", {}).values()
    )

    # Update daily streak
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    streak = save_data.setdefault(
        "streak", {"current": 0, "longest": 0, "last_played_date": ""}
    )
    last_date = streak.get("last_played_date", "")
    if last_date != today:
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        if last_date == yesterday:
            streak["current"] = streak.get("current", 0) + 1
        else:
            streak["current"] = 1
        streak["longest"] = max(streak.get("longest", 0), streak["current"])
        streak["last_played_date"] = today

    primary = _primary_path(name)
    tmp = _tmp_path(name)
    backup = _backup_path(name)

    payload = json.dumps(save_data, indent=2)

    # Step 1 — write to .tmp
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(payload)
    except OSError as exc:
        raise OSError(
            f"Cannot write to saves/. Check folder permissions. ({exc})"
        ) from exc

    # Step 2 — verify the .tmp parses cleanly
    with open(tmp, "r", encoding="utf-8") as fh:
        json.load(fh)  # raises if corrupt

    # Step 3 — rename .tmp → .json (Windows-safe: remove first)
    if os.path.exists(primary):
        os.remove(primary)
    os.rename(tmp, primary)

    # Step 4 — write backup
    with open(backup, "w", encoding="utf-8") as fh:
        fh.write(payload)


def load_save(player_name: str) -> dict | None:
    """Load and validate primary save. Returns None if missing or corrupt."""
    primary = _primary_path(player_name)

    if not os.path.exists(primary):
        return None

    try:
        with open(primary, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError):
        if os.path.exists(primary):
            corrupted = _corrupted_path(player_name)
            if os.path.exists(corrupted):
                os.remove(corrupted)
            os.rename(primary, corrupted)
        print("Save file was corrupted. Starting fresh.")
        return None

    if not _validate_schema(data):
        data = migrate_save(data)

    return data


def load_with_fallback(player_name: str) -> dict | None:
    """Try primary → try backup → return None (caller creates a new save).

    Returns None only when both files are absent or corrupt.
    """
    data = load_save(player_name)
    if data is not None:
        return data

    # Try backup
    backup = _backup_path(player_name)
    if os.path.exists(backup):
        try:
            with open(backup, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if _validate_schema(data):
                print("Primary save was corrupted. Loaded from backup.")
                return data
        except (json.JSONDecodeError, OSError):
            pass

    print("No valid save found. Starting fresh.")
    return None


def migrate_save(save_data: dict) -> dict:
    """Add any missing fields with defaults. Never deletes existing data."""
    defaults = _default_save(
        save_data.get("player_name", "unknown"),
        save_data.get("track", "blue"),
    )
    migrated = False
    for key, value in defaults.items():
        if key not in save_data:
            save_data[key] = value
            migrated = True
    if migrated:
        print("Save file was updated to the latest version.")
    return save_data


def list_saves() -> list:
    """Return list of dicts [{name, last_played}] sorted by last_played desc."""
    saves = _saves_dir()
    if not os.path.exists(saves):
        return []

    result = []
    for filename in os.listdir(saves):
        if not filename.endswith(".json"):
            continue
        if filename.endswith(".backup.json") or filename.endswith(".corrupted.json"):
            continue
        name = filename[:-5]  # strip .json
        path = os.path.join(saves, filename)
        last_played = ""
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            last_played = data.get("last_played", "")
        except (json.JSONDecodeError, OSError):
            pass
        result.append({
            "name": name,
            "last_played": last_played,
            "xp": data.get("xp", 0),
            "completed_count": len(data.get("completed", [])),
        })

    result.sort(key=lambda x: x["last_played"], reverse=True)
    return result
