"""main.py — CIPHER CyberForge

Entry point and menu router.
Usage:
    python main.py          — production mode (runs content validation)
    python main.py --dev    — dev mode (skips checksum verification)
"""

import json
import os
import re
import subprocess
import sys

# Ensure cipher/ root is on the path
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
from engine.operation_runner import run_operation

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


_ASCII_LOGO = r"""
   ______  _______  _    _  _______  _______  _______
  / _____||_____  || |  | ||  _____||_____  ||  ___  |
 | |          / / || |__| || |_____     / / || |   | |
 | |         / /  ||  __  ||  _____|   / /  || |   | |
 | |_____   / /___|| |  | || |_____   / /___|| |___| |
  \_______||_______||_|  |_||_______| |______||_______|

         CYBERSECURITY TRAINING SIMULATOR v1.0
"""

# ---------------------------------------------------------------------------
# TASK-15 — Startup + main menu
# ---------------------------------------------------------------------------


def _run_validation() -> bool:
    """Run validate_content.py as subprocess. Return True if exit code 0."""
    here = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(here, "validate_content.py")
    try:
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except OSError:
        return False


def _show_main_menu(dev_mode: bool) -> None:
    """Display the ASCII logo and main menu options."""
    clear_screen()
    print_header(_ASCII_LOGO)
    if dev_mode:
        print_muted("[DEV MODE] — content validation skipped")
    print_divider()
    print_info("  [1] New Game")
    print_info("  [2] Load Game")
    print_info("  [3] Placement Test")
    print_info("  [4] Quit")
    print_divider()


def main() -> None:
    """Entry point. Parse args, validate content, show main menu loop."""
    dev_mode = "--dev" in sys.argv

    if not dev_mode:
        if not _run_validation():
            print_error("Content validation failed. Run validate_content.py for details.")
            sys.exit(1)

    while True:
        _show_main_menu(dev_mode)
        try:
            choice = input("Select option: ").strip()
        except (KeyboardInterrupt, EOFError):
            sys.exit(0)

        if choice == "1":
            new_game()
        elif choice == "2":
            load_game()
        elif choice == "3":
            placement_test_flow(save_data=None)
        elif choice == "4":
            sys.exit(0)
        else:
            print_warning("Please enter 1, 2, 3, or 4.")


# ---------------------------------------------------------------------------
# TASK-16 — New Game + Load Game
# ---------------------------------------------------------------------------

_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{1,20}$")


def _prompt_player_name() -> str:
    """Prompt for a valid player name. Re-prompts on invalid input."""
    while True:
        try:
            raw = input("Enter your name (letters, numbers, underscores, max 20): ").strip()
        except (KeyboardInterrupt, EOFError):
            return ""

        if not raw:
            print_error("Name cannot be empty.")
            continue
        if not _NAME_PATTERN.match(raw):
            print_error("Name must be letters, numbers, or underscores only.")
            continue
        return raw


def new_game() -> None:
    """New Game flow: prompt name, check existing save, start."""
    print_header("\n=== NEW GAME ===")

    name = _prompt_player_name()
    if not name:
        return

    # Check for existing save
    existing = load_with_fallback(name)
    if existing is not None:
        try:
            answer = input(
                f"Save file found for '{name}'. Load it instead? (y/n): "
            ).strip().lower()
        except (KeyboardInterrupt, EOFError):
            return
        if answer == "y":
            operation_menu(existing)
            return

    save_data = create_save(name, "red")
    write_save(save_data)
    print_success(f"Save created for {name}.")
    operation_menu(save_data)


def load_game() -> None:
    """Load Game flow: list saves, select, resume."""
    print_header("\n=== LOAD GAME ===")

    saves = list_saves()
    if not saves:
        print_warning("No save files found.")
        new_game()
        return

    print_info("Available saves:")
    for i, entry in enumerate(saves, 1):
        last = entry.get("last_played", "never")[:19].replace("T", " ")
        print_info(f"  [{i}] {entry['name']}  (last played: {last})")
    print_info(f"  [0] Back to main menu")

    while True:
        try:
            choice = input("Select save: ").strip()
        except (KeyboardInterrupt, EOFError):
            return

        if choice == "0":
            return

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(saves):
                save_data = load_with_fallback(saves[idx]["name"])
                if save_data is None:
                    save_data = create_save(saves[idx]["name"], "red")
                    write_save(save_data)
                operation_menu(save_data)
                return

        print_warning("Invalid selection. Try again.")


# ---------------------------------------------------------------------------
# TASK-17 — Operation Menu + Placement Test
# ---------------------------------------------------------------------------

def operation_menu(save_data: dict) -> None:
    """Display the operation menu and handle navigation."""
    here = os.path.dirname(os.path.abspath(__file__))
    registry_path = os.path.join(here, "content", "registry.json")

    if not os.path.exists(registry_path):
        print_error("content/registry.json missing. Cannot load operation menu.")
        return

    try:
        with open(registry_path, "r", encoding="utf-8") as fh:
            registry = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        print_error(f"Failed to load registry.json: {exc}")
        return

    operations = registry.get("operations", [])

    while True:
        clear_screen()
        print_header(f"=== OPERATION MENU === [{save_data['player_name']}]")
        print_muted(f"  XP: {save_data.get('xp', 0)}")
        print_divider()

        completed = save_data.get("completed", [])
        skipped = save_data.get("skipped", [])
        in_progress = save_data.get("in_progress", "")

        for i, op in enumerate(operations):
            op_id = op["id"]
            title = op["title"]
            diff = op.get("difficulty", 1)

            # Compute status icon
            if op_id in completed:
                icon = "[DONE]"
            elif op_id in skipped:
                icon = "[SKIP]"
            elif op_id == in_progress and op_id not in completed:
                icon = "[ >> ]"
            elif i == 0:
                icon = "[OPEN]"
            else:
                prev_id = operations[i - 1]["id"]
                if prev_id in completed or prev_id in skipped:
                    icon = "[OPEN]"
                else:
                    icon = "[LOCK]"

            print_info(f"  [{i + 1}] {icon} {title}  (Difficulty: {diff})")

        print_divider()
        print_info("  [p] Placement Test")
        print_info("  [0] Back to main menu")
        print_divider()

        try:
            choice = input("Select operation: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            write_save(save_data)
            return

        if choice == "0":
            write_save(save_data)
            return

        if choice == "p":
            placement_test_flow(save_data)
            continue

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(operations):
                op = operations[idx]
                op_id = op["id"]

                # Check if locked
                is_locked = False
                if idx > 0:
                    prev_id = operations[idx - 1]["id"]
                    if prev_id not in completed and prev_id not in skipped:
                        is_locked = True

                if is_locked:
                    print_warning("Complete or skip the previous operation first.")
                    input("Press Enter to continue...")
                    continue

                # Replay prompt for completed ops
                if op_id in completed:
                    try:
                        answer = input(
                            "Replay this operation? XP will not be awarded again. (y/n): "
                        ).strip().lower()
                    except (KeyboardInterrupt, EOFError):
                        continue
                    if answer != "y":
                        continue
                    # Reset hints and metrics for replay
                    save_data["hints_used"][op_id] = 0
                    save_data["metrics"][op_id] = {
                        "attempts": 0,
                        "hints_maxed": False,
                        "completed": False,
                        "time_spent_seconds": 0,
                    }

                save_data["in_progress"] = op_id
                write_save(save_data)
                save_data = run_operation(op_id, save_data)
                continue

        print_warning("Invalid selection. Try again.")
        input("Press Enter to continue...")


def placement_test_flow(save_data: dict | None) -> None:
    """Run the placement test and update save_data with results.

    If save_data is None (called from main menu before new game),
    prompt the user to create a save first.
    """
    if save_data is None:
        print_warning(
            "You need to start or load a game before taking the placement test."
        )
        input("Press Enter to continue...")
        return

    # Already taken check
    pt = save_data.get("placement_test", {})
    if pt.get("taken", False):
        print_warning("You have already completed the placement test.")
        input("Press Enter to continue...")
        return

    here = os.path.dirname(os.path.abspath(__file__))
    pt_path = os.path.join(here, "content", "placement_test.json")

    try:
        with open(pt_path, "r", encoding="utf-8") as fh:
            pt_data = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        print_error(f"Failed to load placement test: {exc}")
        return

    questions = pt_data.get("questions", [])
    threshold = pt_data.get("pass_threshold", 4)
    xp_on_pass = pt_data.get("xp_on_pass", 50)

    results: list = []
    score = 0

    clear_screen()
    print_header("=== PLACEMENT TEST ===")
    print_info("5 questions. Answer with 1, 2, 3, or 4.")
    print_info("Ctrl+C at any time to cancel.")
    print_divider()

    try:
        for i, q in enumerate(questions, 1):
            print_info(f"\nQ{i}. {q['question']}\n")
            for j, opt in enumerate(q["options"], 1):
                print_info(f"  {j}) {opt}")

            while True:
                try:
                    ans = input(f"\nYour answer (1-4): ").strip()
                except KeyboardInterrupt:
                    raise
                if ans in ("1", "2", "3", "4"):
                    break
                print_warning("Please enter 1, 2, 3, or 4.")

            chosen_idx = int(ans) - 1
            correct_idx = q["correct_index"]
            correct = chosen_idx == correct_idx
            if correct:
                score += 1
            results.append({
                "q_num": i,
                "correct": correct,
                "chosen": chosen_idx,
                "correct_idx": correct_idx,
                "options": q["options"],
            })
            print_divider()

    except KeyboardInterrupt:
        # Discard all answers, mark test as not taken
        save_data.setdefault("placement_test", {})["taken"] = False
        write_save(save_data)
        print()
        print_muted("Placement test cancelled. Returning to menu...")
        input("Press Enter to continue...")
        return

    # Display results
    clear_screen()
    print_header("PLACEMENT TEST RESULTS")
    print_divider()
    print_info(f"Score: {score}/{len(questions)}")
    print_divider()

    for r in results:
        q_num = r["q_num"]
        if r["correct"]:
            print_success(f"  Q{q_num} — Correct")
        else:
            print_error(f"  Q{q_num} — Incorrect")
            print_muted(f"     Your answer:    {r['options'][r['chosen']]}")
            print_muted(f"     Correct answer: {r['options'][r['correct_idx']]}")

    print_divider()

    passed = score >= threshold
    if passed:
        print_success(f"RESULT: PASSED — {xp_on_pass} XP awarded")
        print_info("Starting from Operation 01.")
        save_data["xp"] = save_data.get("xp", 0) + xp_on_pass
    else:
        print_info("RESULT: NOT PASSED — Starting from Operation 01. No penalty.")

    # Update save
    save_data.setdefault("placement_test", {}).update({
        "taken": True,
        "passed": passed,
        "xp_awarded": xp_on_pass if passed else 0,
    })
    write_save(save_data)

    print_divider()
    input("Press Enter to continue...")

    operation_menu(save_data)


if __name__ == "__main__":
    main()
