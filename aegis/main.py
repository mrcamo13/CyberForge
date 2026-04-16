"""main.py — AEGIS CyberForge

Blue Team SOC analyst simulator for CySA+ CS0-003 preparation.
Entry point: python main.py [--dev]
"""

import json
import os
import re
import runpy
import sys

# ---------------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.terminal import (
    clear_screen,
    print_divider,
    print_error,
    print_header,
    print_info,
    print_muted,
    print_success,
    print_warning,
)
from utils.save_manager import (
    create_save,
    list_saves,
    load_with_fallback,
    write_save,
)
from engine.case_runner import run_case

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TOTAL_CASES = 31  # update if new cases are added

_AEGIS_LOGO = r"""
     _    _____ ____ ___ ____
    / \  | ____/ ___|_ _/ ___|
   / _ \ |  _|| |  _ | |\___ \
  / ___ \| |__| |_| || | ___) |
 /_/   \_\_____\____|___|____/

   VERIDIAN SYSTEMS — BLUE TEAM TERMINAL
"""

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _run_validation() -> None:
    """Run validate_content.py in-process. Exit if it fails."""
    here = os.path.dirname(os.path.abspath(__file__))
    validator = os.path.join(here, "validate_content.py")
    try:
        runpy.run_path(validator, run_name="__main__")
    except SystemExit as exc:
        if exc.code not in (None, 0):
            print_error("Content validation failed. Run validate_content.py for details.")
            sys.exit(1)


# ---------------------------------------------------------------------------
# Main Menu
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse args, validate content, show main menu."""
    dev_mode = "--dev" in sys.argv

    clear_screen()
    print_header(_AEGIS_LOGO)

    if dev_mode:
        print_muted("[DEV MODE — content validation skipped]")
    else:
        _run_validation()

    while True:
        print_divider()
        print_header("AEGIS — MAIN MENU")
        print_divider()
        print_info("  [1] New Game")
        print_info("  [2] Load Game")
        print_info("  [3] Placement Test  -- already know the basics? skip Stage 1")
        print_info("  [4] Quit")
        print_divider()

        choice = input("> ").strip()
        if choice == "1":
            new_game()
        elif choice == "2":
            load_game()
        elif choice == "3":
            placement_test(save_data=None)
        elif choice == "4":
            print_muted("Goodbye.")
            sys.exit(0)
        else:
            print_warning("Enter 1, 2, 3, or 4.")


# ---------------------------------------------------------------------------
# New Game
# ---------------------------------------------------------------------------

def new_game() -> None:
    """Prompt for analyst name, then start the case menu."""
    while True:
        print_divider()
        name_raw = input("Enter analyst name: ").strip()
        if not name_raw:
            print_warning("Name cannot be empty.")
            continue
        if not re.match(r"^[A-Za-z0-9_]{1,20}$", name_raw):
            print_warning(
                "Name must be 1-20 characters: letters, numbers, underscores only."
            )
            continue
        player_name = name_raw
        break

    # Check for existing save
    from utils.save_manager import _primary_path
    if os.path.exists(_primary_path(player_name)):
        answer = input(f"Save found for '{player_name}'. Load it? (y/n): ").strip().lower()
        if answer == "y":
            save_data = load_with_fallback(player_name)
            if save_data is None:
                print_warning("Could not load save. Starting fresh.")
                save_data = _new_save(player_name)
            case_menu(save_data)
            return

    save_data = _new_save(player_name)
    case_menu(save_data)


def _new_save(player_name: str) -> dict:
    """Create, write, and return a fresh save for the given analyst name."""
    save_data = create_save(player_name, "blue")
    write_save(save_data)
    print_success(f"Save created for analyst '{player_name}'.")
    return save_data


# ---------------------------------------------------------------------------
# Load Game
# ---------------------------------------------------------------------------

def load_game() -> None:
    """List existing saves and load the selected one."""
    saves = list_saves()
    if not saves:
        print_warning("No save files found.")
        new_game()
        return

    print_divider()
    print_header("LOAD GAME — Select a save:")
    print_divider()
    for i, s in enumerate(saves, 1):
        last = s["last_played"][:10] if s["last_played"] else "unknown"
        done = s.get("completed_count", 0)
        xp = s.get("xp", 0)
        print_info(
            f"  [{i}] {s['name']:<20} "
            f"{done:>2}/{_TOTAL_CASES} cases  |  "
            f"XP: {xp:<6}  |  "
            f"last played: {last}"
        )
    print_info("  [0] Back to main menu")
    print_divider()

    while True:
        choice = input("> ").strip()
        if choice == "0":
            return
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(saves):
                save_data = load_with_fallback(saves[idx]["name"])
                if save_data is None:
                    print_error("Could not load save. It may be corrupted.")
                    return
                case_menu(save_data)
                return
        print_warning(f"Enter a number between 1 and {len(saves)}, or 0 to go back.")


# ---------------------------------------------------------------------------
# Case Menu
# ---------------------------------------------------------------------------

def _load_registry() -> list:
    """Load and return the cases list from content/registry.json."""
    here = os.path.dirname(os.path.abspath(__file__))
    reg_path = os.path.join(here, "content", "registry.json")
    with open(reg_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("cases", [])


def _case_status(case_id: str, idx: int, cases: list, save_data: dict) -> str:
    """Return the status icon for a case in the menu."""
    if case_id in save_data["completed"]:
        return "✅"
    if case_id in save_data["skipped"]:
        return "⏭ "
    if case_id == save_data.get("in_progress", ""):
        return "▶ "
    # Locked if the previous case is neither completed nor skipped
    if idx > 0:
        prev_id = cases[idx - 1]["id"]
        if prev_id not in save_data["completed"] and prev_id not in save_data["skipped"]:
            return "🔒"
    return "  "


def case_menu(save_data: dict) -> None:
    """Display the case selection menu and route to selected cases."""
    while True:
        clear_screen()
        cases = _load_registry()

        print_header("AEGIS — CASE MENU")
        print_divider()
        completed_count = len(save_data["completed"])
        total_cases = len(cases)
        pct = int(completed_count / total_cases * 100) if total_cases else 0
        bar_filled = pct // 5  # 20-block bar, each block = 5%
        bar = "[" + "#" * bar_filled + "." * (20 - bar_filled) + "]"
        badges_count = len(save_data.get("badges", []))
        print_muted(
            f"Analyst: {save_data['player_name']}  |  "
            f"XP: {save_data['xp']}  |  "
            f"Badges: {badges_count}"
        )
        print_muted(
            f"Progress: {bar} {completed_count}/{total_cases} ({pct}%)"
        )
        print_divider()

        for i, case in enumerate(cases):
            icon = _case_status(case["id"], i, cases, save_data)
            diff = "★" * case["difficulty"]
            print_info(f"  [{i+1}] {icon} {case['title']:<22} {diff}")

        print_divider()
        print_info("  [p] Placement Test  -- skip Stage 1 if you pass")
        print_info("  [s] Stats")
        print_info("  [0] Main Menu")
        print_divider()

        choice = input("> ").strip().lower()

        if choice == "0":
            return

        if choice == "p":
            placement_test(save_data)
            continue

        if choice == "s":
            stats_screen(save_data)
            continue

        if choice.isdigit():
            idx = int(choice) - 1
            if not (0 <= idx < len(cases)):
                print_warning(f"Enter a number between 1 and {len(cases)}.")
                input("Press Enter to continue...")
                continue

            case = cases[idx]
            case_id = case["id"]
            icon = _case_status(case_id, idx, cases, save_data)

            if icon == "🔒":
                print_warning("Complete the previous case first.")
                input("Press Enter to continue...")
                continue

            if case_id in save_data["completed"]:
                confirm = input(
                    f"'{case['title']}' already completed. Replay? XP will not be awarded again. (y/n): "
                ).strip().lower()
                if confirm != "y":
                    continue
                # Reset metrics for replay tracking
                save_data["metrics"].setdefault(case_id, {})
                save_data["metrics"][case_id]["completed"] = False

            was_complete = len(save_data["completed"]) >= len(cases)
            save_data["in_progress"] = case_id
            write_save(save_data)
            save_data = run_case(case_id, save_data)
            save_data["in_progress"] = ""
            write_save(save_data)
            # Show end-game screen the first time all cases are done
            if not was_complete and len(save_data["completed"]) >= len(cases):
                _end_game_screen(save_data)
            continue

        print_warning("Invalid selection.")
        input("Press Enter to continue...")


# ---------------------------------------------------------------------------
# End-Game Screen
# ---------------------------------------------------------------------------

_COMPLETE_BANNER = r"""
  ___  ____  _____ ____      _  _____ ___ ___  _   _ ____
 / _ \|  _ \| ____|  _ \    / \|_   _|_ _/ _ \| \ | / ___|
| | | | |_) |  _| | |_) |  / _ \ | |  | | | | |  \| \___ \
| |_| |  __/| |___|  _ <  / ___ \| |  | | |_| | |\  |___) |
 \___/|_|   |_____|_| \_\/_/   \_\_| |___\___/|_| \_|____/

         IRONCLAD -- COMPLETE
"""


def _end_game_screen(save_data: dict) -> None:
    """Show the game completion celebration after all cases are done."""
    clear_screen()
    print_header(_COMPLETE_BANNER)
    print_divider()
    print_success("All 31 cases complete. Veridian Systems is protected.")
    print_divider()

    # Final stats
    total_secs = save_data.get("total_time_played_seconds", 0)
    hours, rem = divmod(total_secs, 3600)
    minutes = rem // 60
    badges = save_data.get("badges", [])

    print_info(f"  Analyst:   {save_data['player_name']}")
    print_info(f"  Final XP:  {save_data['xp']}")
    print_info(f"  Badges:    {len(badges)}")
    print_info(f"  Time:      {hours}h {minutes}m")
    print_divider()
    print_warning("Type 's' from the case menu to view your full analyst profile.")
    print_divider()
    input("Press Enter to continue...")


# ---------------------------------------------------------------------------
# Stats Screen
# ---------------------------------------------------------------------------


def stats_screen(save_data: dict) -> None:
    """Display player statistics and badge collection."""
    from utils.player import _BADGE_LABELS

    clear_screen()
    cases = _load_registry()
    total_cases = len(cases)
    completed = len(save_data["completed"])
    skipped = len(save_data["skipped"])
    xp = save_data["xp"]
    badges_earned = save_data.get("badges", [])
    total_secs = save_data.get("total_time_played_seconds", 0)
    hours, rem = divmod(total_secs, 3600)
    minutes = rem // 60
    streak = save_data.get("streak", {})

    pct = int(completed / total_cases * 100) if total_cases else 0
    bar_filled = pct // 5
    bar = "[" + "#" * bar_filled + "." * (20 - bar_filled) + "]"

    print_header("AEGIS -- ANALYST PROFILE")
    print_divider()
    print_info(f"  Analyst : {save_data['player_name']}")
    print_info(f"  Created : {save_data['created_at'][:10]}")
    print_divider()
    print_header("PROGRESS")
    print_divider()
    print_info(f"  Cases   : {bar} {completed}/{total_cases} ({pct}%)")
    print_info(f"  Skipped : {skipped}")
    print_info(f"  XP      : {xp}")
    print_info(f"  Time    : {hours}h {minutes}m")
    print_info(
        f"  Streak  : {streak.get('current', 0)} day(s) current  |  "
        f"{streak.get('longest', 0)} day(s) best"
    )
    print_divider()
    print_header("BADGES")
    print_divider()
    if badges_earned:
        for badge_id in badges_earned:
            label = _BADGE_LABELS.get(badge_id, badge_id)
            print_success(f"  [X] {label}")
    else:
        print_muted("  No badges yet. Complete cases to earn badges.")

    locked = [b for b in _BADGE_LABELS if b not in badges_earned]
    if locked:
        print_divider()
        for badge_id in locked:
            label = _BADGE_LABELS.get(badge_id, badge_id)
            print_muted(f"  [ ] {label}")
    print_divider()
    input("Press Enter to continue...")


# ---------------------------------------------------------------------------
# Placement Test
# ---------------------------------------------------------------------------

def placement_test(save_data: dict = None) -> None:
    """Run the CySA+ foundation placement test.

    Guest mode (save_data=None): results displayed, not persisted.
    Save mode: results persisted to save file.
    """
    if save_data is not None and save_data["placement_test"].get("taken"):
        print_warning("Placement test already completed.")
        input("Press Enter to continue...")
        return

    here = os.path.dirname(os.path.abspath(__file__))
    pt_path = os.path.join(here, "content", "placement_test.json")
    with open(pt_path, "r", encoding="utf-8") as fh:
        pt_data = json.load(fh)

    questions = pt_data["questions"]
    threshold = pt_data["pass_threshold"]
    xp_on_pass = pt_data.get("xp_on_pass", 0)
    score = 0

    clear_screen()
    print_header("AEGIS — PLACEMENT TEST")
    print_muted("CySA+ CS0-003 Foundation Assessment — 5 questions")
    print_divider()

    try:
        for i, q in enumerate(questions, 1):
            print_info(f"\nQuestion {i}: {q['question']}")
            for j, opt in enumerate(q["options"], 1):
                print_info(f"  [{j}] {opt}")

            while True:
                ans = input("> ").strip()
                if ans in ("1", "2", "3", "4"):
                    break
                print_warning("Enter 1, 2, 3, or 4.")

            if int(ans) - 1 == q["correct_index"]:
                print_success("Correct!")
                score += 1
            else:
                correct_opt = q["options"][q["correct_index"]]
                print_error(f"Incorrect. Answer: {correct_opt}")

    except KeyboardInterrupt:
        if save_data is not None:
            save_data["placement_test"]["taken"] = False
            write_save(save_data)
        print_muted("\nPlacement test interrupted. Progress not saved.")
        return

    # Results
    passed = score >= threshold
    _STAGE1_CASES = ["case01", "case02", "case03", "case04", "case05"]

    print_divider()
    print_header("PLACEMENT TEST RESULTS")
    print_divider()
    print_info(f"Score: {score}/{len(questions)}")

    if passed:
        print_success(f"PASSED — {xp_on_pass} XP awarded!")
        print_success("Stage 1 skipped — you start at Case 06.")
    else:
        print_warning(f"FAILED — {threshold}/{len(questions)} required to pass.")
        print_warning("Starting from Case 01. Work through Stage 1 to unlock Stage 2.")

    print_divider()

    if save_data is not None:
        save_data["placement_test"]["taken"] = True
        save_data["placement_test"]["score"] = score
        save_data["placement_test"]["passed"] = passed
        if passed:
            save_data["xp"] += xp_on_pass
            # Auto-skip Stage 1 cases so Case 06 is unlocked
            for cid in _STAGE1_CASES:
                if cid not in save_data["skipped"] and cid not in save_data["completed"]:
                    save_data["skipped"].append(cid)
        write_save(save_data)
        input("Press Enter to continue...")
        case_menu(save_data)
    else:
        # Guest mode — no save
        if passed:
            print_info("Create a save (New Game) to apply your placement result.")
        input("Press Enter to return to main menu...")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
