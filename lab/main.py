"""main.py — LAB CyberForge (Script Lab)

Entry point for the Script Lab simulator.
All 15 challenges are always available — no locking.

Features:
  - Stage grouping: Foundation (1-5), Intermediate (6-10), Advanced (11-15)
  - Timed mode: toggle [t] from the challenge menu
  - Leaderboard: [l] — shows best times per challenge across all saves
  - Stats screen: [s] — full XP, time, streak, badges breakdown
  - Replay: [r <id>] — view your saved solution for a completed challenge
"""

import os
import sys

_LAB_DIR = os.path.dirname(os.path.abspath(__file__))
if _LAB_DIR not in sys.path:
    sys.path.insert(0, _LAB_DIR)

from utils.terminal import (
    print_success, print_error, print_warning, print_info,
    print_muted, print_header, print_divider, clear_screen,
    normalize_input,
)
from utils.save_manager import (
    create_save, write_save, load_with_fallback, list_saves, _saves_dir,
)
from utils.player import get_badge_labels
from engine.challenge_runner import load_challenge, load_registry, run_challenge

import json
import os as _os


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DIFFICULTY_STARS = {1: " * ", 2: " **", 3: "***", 4: "****"}
_TOTAL_CHALLENGES = 15
_STAGE_LABELS = {
    "stage1": "Stage 1 -- Foundation     (labs 01-05)",
    "stage2": "Stage 2 -- Intermediate   (labs 06-10)",
    "stage3": "Stage 3 -- Advanced       (labs 11-15)",
}


# ---------------------------------------------------------------------------
# Save helpers
# ---------------------------------------------------------------------------

def _pick_or_create_save() -> dict | None:
    """Ask the player to continue, create a new profile, or quit."""
    saves = list_saves()

    clear_screen()
    print_header("""
  +-----------------------------------------+
  |   LAB  --  CYBERFORGE Script Lab        |
  |   Python Automation for Cyber Analysts  |
  +-----------------------------------------+
""")

    if saves:
        print_info("  Saved profiles:")
        for i, s in enumerate(saves, 1):
            xp = s.get("xp", 0)
            done = s.get("completed_count", 0)
            print_muted(
                f"    [{i}] {s['name']:<20} XP: {xp:<6} "
                f"{done}/{_TOTAL_CHALLENGES} complete"
            )
        print()
        print_muted("    [n] New profile")
        print_muted("    [0] Back")
        print()

        while True:
            choice = input("  Select> ").strip().lower()
            if choice == "0":
                return None
            if choice == "n":
                break
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(saves):
                    name = saves[idx]["name"]
                    data = load_with_fallback(name)
                    if data is None:
                        print_error("Could not load that save. Starting fresh.")
                        data = create_save(name)
                    return data
            print_warning("Invalid choice.")
    else:
        print_info("  No saved profiles found.")
        print()

    # New profile
    while True:
        name = input("  Enter your name: ").strip()
        if not name:
            print_warning("Name cannot be empty.")
            continue
        if len(name) > 20:
            print_warning("Name must be 20 characters or fewer.")
            continue
        existing = load_with_fallback(name)
        if existing:
            print_info(f"  Welcome back, {name}!")
            return existing
        save_data = create_save(name)
        write_save(save_data)
        print_success(f"\n  Profile created: {name}")
        return save_data


# ---------------------------------------------------------------------------
# Progress bar
# ---------------------------------------------------------------------------

def _build_progress_bar(done: int, total: int, width: int = 20) -> str:
    filled = int(width * done / total) if total else 0
    bar = "#" * filled + "." * (width - filled)
    pct = int(100 * done / total) if total else 0
    return f"[{bar}] {done}/{total} ({pct}%)"


# ---------------------------------------------------------------------------
# Challenge menu
# ---------------------------------------------------------------------------

def _challenge_menu(save_data: dict) -> None:
    """Display the challenge selection menu and dispatch to run_challenge."""
    registry = load_registry()
    if not registry.get("challenges"):
        print_error("No challenges found. Check content/registry.json.")
        return

    challenges = registry["challenges"]
    stages = registry.get("stages", [])
    # Build stage → [challenge ids] map
    stage_map = {s["id"]: s["challenges"] for s in stages}

    timed_mode = False

    while True:
        clear_screen()
        completed = save_data.get("completed", [])
        xp = save_data.get("xp", 0)
        badges = save_data.get("badges", [])
        name = save_data.get("player_name", "Analyst")

        bar = _build_progress_bar(len(completed), _TOTAL_CHALLENGES)
        timed_label = " [TIMED ON]" if timed_mode else ""

        print_header(f"\n  SCRIPT LAB  --  {name}{timed_label}")
        print_muted(f"  Progress: {bar}")
        print_muted(f"  XP: {xp}  |  Badges: {len(badges)}")
        print()

        # Build index number → challenge mapping
        idx_to_challenge = {}
        idx = 1
        for stage in stages:
            print_divider()
            stage_label = _STAGE_LABELS.get(stage["id"], stage.get("title", stage["id"]))
            stage_done = sum(1 for cid in stage["challenges"] if cid in completed)
            stage_total = len(stage["challenges"])
            print_header(f"  {stage_label}  [{stage_done}/{stage_total}]")
            print_divider()

            for cid in stage["challenges"]:
                # Find challenge entry
                entry = next((c for c in challenges if c["id"] == cid), None)
                if not entry:
                    continue
                title = entry["title"]
                diff = entry.get("difficulty", 1)
                stars = _DIFFICULTY_STARS.get(diff, " * ")
                done_mark = "[X]" if cid in completed else "[ ]"
                print_info(f"  [{idx}] {done_mark} {title:<22} {stars}")
                idx_to_challenge[str(idx)] = cid
                idx += 1

        print()
        print_muted("  [s] Stats  [l] Leaderboard  [t] Timed mode  [0] Back")
        print()

        choice = input("  Select challenge> ").strip().lower()

        if choice == "0":
            break

        if choice == "s":
            _stats_screen(save_data, challenges, stages)
            continue

        if choice == "l":
            _leaderboard_screen(challenges)
            continue

        if choice == "t":
            timed_mode = not timed_mode
            state = "ON" if timed_mode else "OFF"
            print_success(f"  Timed mode {state}.")
            input("  Press Enter to continue...")
            continue

        # Replay: "r lab06" or "r 6"
        if choice.startswith("r "):
            target = choice[2:].strip()
            # Support "r 6" shorthand
            if target.isdigit() and target in idx_to_challenge:
                target = idx_to_challenge[target]
            _replay_screen(save_data, target)
            continue

        if choice in idx_to_challenge:
            cid = idx_to_challenge[choice]
            challenge_data = load_challenge(cid)
            if challenge_data is None:
                print_error(f"Could not load challenge data for {cid}.")
                input("Press Enter to continue...")
                continue
            save_data = run_challenge(cid, challenge_data, save_data,
                                      timed_mode=timed_mode)

            # End-game check
            if len(save_data.get("completed", [])) >= _TOTAL_CHALLENGES:
                if "all_complete" in save_data.get("badges", []):
                    _end_game_screen(save_data)
            continue

        print_warning("  Invalid choice.")
        input("  Press Enter to continue...")


# ---------------------------------------------------------------------------
# Stats screen
# ---------------------------------------------------------------------------

def _stats_screen(save_data: dict, challenges: list, stages: list) -> None:
    """Display full stats: progress, XP, time, streak, badges, per-challenge."""
    clear_screen()
    completed = save_data.get("completed", [])
    xp = save_data.get("xp", 0)
    badges = save_data.get("badges", [])
    streak = save_data.get("streak", {})
    total_seconds = save_data.get("total_time_played_seconds", 0)
    name = save_data.get("player_name", "Analyst")

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    bar = _build_progress_bar(len(completed), _TOTAL_CHALLENGES)

    print_header("\n  STATS")
    print_divider()
    print_info(f"  Player:   {name}")
    print_info(f"  Progress: {bar}")
    print_info(f"  XP:       {xp}")
    print_info(f"  Time:     {hours}h {minutes}m {seconds}s")
    print_info(
        f"  Streak:   {streak.get('current', 0)} day(s) "
        f"(best: {streak.get('longest', 0)})"
    )

    print()
    print_header("  BADGES")
    print_divider()
    badge_labels = get_badge_labels()
    for badge_id, label in badge_labels.items():
        mark = "[X]" if badge_id in badges else "[ ]"
        print_info(f"  {mark} {label}")

    print()
    hints_used = save_data.get("hints_used", {})
    metrics = save_data.get("metrics", {})

    for stage in stages:
        stage_label = _STAGE_LABELS.get(stage["id"], stage["id"])
        print()
        print_header(f"  {stage_label}")
        print_divider()
        for cid in stage["challenges"]:
            entry = next((c for c in challenges if c["id"] == cid), None)
            title = entry["title"] if entry else cid
            done = "[X]" if cid in completed else "[ ]"
            h = hints_used.get(cid, 0)
            t = metrics.get(cid, {}).get("time_spent_seconds", 0)
            best = metrics.get(cid, {}).get("best_time_seconds", 0)
            tm = f"{t // 60}m {t % 60:02d}s"
            best_str = f"best: {best // 60}m {best % 60:02d}s" if best else "not timed"
            has_replay = cid in save_data.get("solutions", {})
            replay_mark = " [saved]" if has_replay else ""
            print_muted(
                f"  {done} {title:<22} hints: {h}  time: {tm}  {best_str}{replay_mark}"
            )

    print()
    input("  Press Enter to return...")


# ---------------------------------------------------------------------------
# Leaderboard screen
# ---------------------------------------------------------------------------

def _leaderboard_screen(challenges: list) -> None:
    """Show best completion times per challenge across all save files."""
    clear_screen()
    saves_path = _saves_dir()
    print_header("\n  LEADERBOARD  --  Best Times Per Challenge")
    print_divider()

    if not _os.path.exists(saves_path):
        print_muted("  No saves found.")
        input("\n  Press Enter to return...")
        return

    # Collect all save files
    all_saves = []
    for fname in _os.listdir(saves_path):
        if not fname.endswith(".json"):
            continue
        if fname.endswith(".backup.json") or fname.endswith(".corrupted.json"):
            continue
        fpath = _os.path.join(saves_path, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            all_saves.append(data)
        except (json.JSONDecodeError, OSError):
            pass

    if not all_saves:
        print_muted("  No completed data yet.")
        input("\n  Press Enter to return...")
        return

    # For each challenge, find best completion time across all players
    for entry in challenges:
        cid = entry["id"]
        title = entry["title"]
        best_time = None
        best_player = None

        for sd in all_saves:
            if cid not in sd.get("completed", []):
                continue
            t = sd.get("metrics", {}).get(cid, {}).get("best_time_seconds", 0)
            player = sd.get("player_name", "?")
            if t > 0 and (best_time is None or t < best_time):
                best_time = t
                best_player = player

        if best_time is not None:
            mins = best_time // 60
            secs = best_time % 60
            print_success(f"  {title:<22} {mins}m {secs:02d}s  ({best_player})")
        else:
            print_muted(f"  {title:<22} not yet completed")

    print()
    input("  Press Enter to return...")


# ---------------------------------------------------------------------------
# Replay screen
# ---------------------------------------------------------------------------

def _replay_screen(save_data: dict, challenge_id: str) -> None:
    """Display the saved solution for a completed challenge."""
    solutions = save_data.get("solutions", {})

    if challenge_id not in save_data.get("completed", []):
        print_warning(f"\n  {challenge_id} not yet completed. No replay available.")
        input("  Press Enter to continue...")
        return

    if challenge_id not in solutions:
        print_warning(f"\n  No saved solution for {challenge_id} (completed before replay was added).")
        input("  Press Enter to continue...")
        return

    clear_screen()
    print_header(f"\n  REPLAY -- {challenge_id}")
    print_divider()
    print_muted("  Your saved solution:\n")
    for i, line in enumerate(solutions[challenge_id].splitlines(), 1):
        print_muted(f"  {i:>3} | {line}")
    print()
    input("  Press Enter to return...")


# ---------------------------------------------------------------------------
# End-game screen
# ---------------------------------------------------------------------------

def _end_game_screen(save_data: dict) -> None:
    """Show the Lab Graduate end-game screen."""
    clear_screen()
    xp = save_data.get("xp", 0)
    badges = save_data.get("badges", [])
    total_seconds = save_data.get("total_time_played_seconds", 0)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    print_success("""
  ======================================================
       LAB GRADUATE -- ALL 15 CHALLENGES COMPLETE
  ======================================================
""")
    print_success(f"  Total XP:     {xp}")
    print_success(f"  Badges:       {len(badges)}/4")
    print_success(f"  Time played:  {hours}h {minutes}m")
    print()
    print_header("  You've completed every Script Lab challenge.")
    print_info(
        "  The skills you practised here cover the full Python\n"
        "  automation toolkit for cybersecurity:\n\n"
        "    File I/O   |  Regex      |  JSON parsing\n"
        "    Hashing    |  Sockets    |  Binary / XOR\n"
        "    CSV        |  Ciphers    |  CLI scripting\n"
        "    Log correlation  |  Full triage pipelines\n"
    )
    print_info(
        "  Your next step: open the AEGIS Blue Team simulator and\n"
        "  apply these skills to real analyst scenario investigations."
    )
    print()
    input("  Press Enter to continue...")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    save_data = _pick_or_create_save()
    if save_data is None:
        return
    _challenge_menu(save_data)


if __name__ == "__main__":
    main()
