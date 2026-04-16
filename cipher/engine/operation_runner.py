"""operation_runner.py — CIPHER CyberForge

Generic operation engine. Reads any operation JSON by ID.
Implements the full command loop with strict 3-step priority:
  1. Exact command match
  2. Command with arguments (note [text])
  3. Answer fallback
"""

import json
import os
import sys
import time

# Ensure cipher/ root is on the path when run directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.terminal import (
    check_answer,
    clear_screen,
    normalize_input,
    print_divider,
    print_error,
    print_header,
    print_info,
    print_muted,
    print_success,
    print_warning,
)
from utils.player import calculate_xp, evaluate_badges
from utils.save_manager import write_save
from utils.tools import run_tool, get_tool_commands


# ---------------------------------------------------------------------------
# TASK-11 — Load + Display
# ---------------------------------------------------------------------------

def _ops_dir() -> str:
    """Return path to content/operations/ relative to engine/."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "content", "operations")


def load_operation(op_id: str) -> dict:
    """Load and return operation data from content/operations/{op_id}.json."""
    path = os.path.join(_ops_dir(), f"{op_id}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Operation file not found: content/operations/{op_id}.json"
        )
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def display_intro(op_data: dict, tool_cmds: list) -> None:
    """Clear screen and display the operation intro narrative."""
    clear_screen()
    print_header(f"=== OPERATION: {op_data['title'].upper()} ===")
    print_divider()
    print_info(op_data["scenario"])
    print_divider()
    print_warning(op_data["challenge"])
    print_divider()
    if tool_cmds:
        primary = tool_cmds[0]
        print_muted(f"Type '{primary}' to run the tool.  Type 'help' for all commands.")
    else:
        print_muted("Type 'help' to see available commands.")
    print()


# ---------------------------------------------------------------------------
# TASK-12-14 — Full command loop
# ---------------------------------------------------------------------------

def _help_text(tool_cmds: list) -> str:
    """Return the help command listing, showing the real tool command."""
    primary = tool_cmds[0] if tool_cmds else "tools"
    aliases = ", ".join(tool_cmds[1:]) if len(tool_cmds) > 1 else ""
    tool_line = (
        f"  {primary:<10} — run the in-game analyzer/decoder  (also: {aliases}, tools)"
        if aliases else
        f"  {primary:<10} — run the in-game analyzer/decoder  (also: tools)"
    )
    return (
        "Available commands:\n"
        "  help       — show this list\n"
        "  learn      — display concept explanation for this operation\n"
        f"{tool_line}\n"
        "  hint       — reveal next hint (affects XP)\n"
        "  notes      — view your saved notes for this operation\n"
        "  note [text]— save a note for this operation\n"
        "  skip       — mark operation as skipped, return to menu\n"
        "  menu       — save progress and return to menu\n"
        "  quit       — save progress and exit game"
    )


def _ensure_metrics(save_data: dict, op_id: str) -> None:
    """Initialize metrics entry for op_id if not present."""
    if op_id not in save_data["metrics"]:
        save_data["metrics"][op_id] = {
            "attempts": 0,
            "hints_maxed": False,
            "completed": False,
            "time_spent_seconds": 0,
        }


def _ensure_hints_used(save_data: dict, op_id: str) -> None:
    """Initialize hints_used entry for op_id if not present."""
    if op_id not in save_data["hints_used"]:
        save_data["hints_used"][op_id] = 0


def run_operation(op_id: str, save_data: dict) -> dict:
    """Run the interactive command loop for the given operation.

    Returns updated save_data after the player exits (any way).
    Never calls sys.exit() — always returns to caller.
    """
    try:
        op_data = load_operation(op_id)
    except FileNotFoundError as exc:
        print_error(str(exc))
        return save_data

    _ensure_metrics(save_data, op_id)
    _ensure_hints_used(save_data, op_id)

    # Start metrics timer
    start_time = time.time()
    save_data["in_progress"] = op_id

    tool_cmds = get_tool_commands(op_data.get("tools_type", ""))
    display_intro(op_data, tool_cmds)

    try:
        result = _command_loop(op_id, op_data, save_data, start_time, tool_cmds)
    except KeyboardInterrupt:
        elapsed = int(time.time() - start_time)
        save_data["metrics"][op_id]["time_spent_seconds"] += elapsed
        write_save(save_data)
        print()
        print_muted("Progress saved. Returning to menu...")
        result = save_data

    return result


def _command_loop(
    op_id: str, op_data: dict, save_data: dict, start_time: float,
    tool_cmds: list = None,
) -> dict:
    """Inner command loop. Returns save_data when the player exits."""
    if tool_cmds is None:
        tool_cmds = []
    while True:
        try:
            raw = input(f"\n[{op_id.upper()}] > ")
        except KeyboardInterrupt:
            raise  # propagate to run_operation handler
        except EOFError:
            # Non-interactive environment — treat as quit
            break

        if not raw.strip():
            print_warning("Please enter a command or your answer.")
            continue

        normalized = normalize_input(raw)

        # ------------------------------------------------------------------
        # Step 1 — Exact command match
        # ------------------------------------------------------------------
        if normalized == "help":
            print_info(_help_text(tool_cmds))
            continue

        if normalized == "learn":
            print_divider()
            print_info(op_data["learn"])
            print_divider()
            continue

        if normalized == "tools" or normalized in tool_cmds:
            print_divider()
            # Use challenge_data if present (the actual encoded/target string),
            # otherwise fall back to the challenge question text.
            tool_input = op_data.get("challenge_data", op_data["challenge"])
            result_text = run_tool(op_data["tools_type"], tool_input)
            print_info(result_text)
            print_divider()
            continue

        if normalized == "hint":
            save_data = _handle_hint(op_id, op_data, save_data)
            continue

        if normalized == "notes":
            notes = save_data.get("notes", {}).get(op_id, [])
            if notes:
                print_divider()
                for i, note in enumerate(notes, 1):
                    print_info(f"  {i}. {note}")
                print_divider()
            else:
                print_muted("No notes yet.")
            continue

        if normalized == "skip":
            elapsed = int(time.time() - start_time)
            save_data["metrics"][op_id]["time_spent_seconds"] += elapsed
            if op_id not in save_data.get("skipped", []):
                save_data.setdefault("skipped", []).append(op_id)
            write_save(save_data)
            print_muted("Operation skipped.")
            return save_data

        if normalized == "menu":
            elapsed = int(time.time() - start_time)
            save_data["metrics"][op_id]["time_spent_seconds"] += elapsed
            write_save(save_data)
            return save_data

        if normalized == "quit":
            confirm = input("Save and exit? (y/n): ").strip().lower()
            if confirm == "y":
                elapsed = int(time.time() - start_time)
                save_data["metrics"][op_id]["time_spent_seconds"] += elapsed
                write_save(save_data)
                print_muted("Progress saved. Goodbye.")
                sys.exit(0)
            continue

        # ------------------------------------------------------------------
        # Step 2 — note [text]
        # ------------------------------------------------------------------
        if normalized.startswith("note "):
            note_text = raw.strip()[5:].strip()
            if not note_text:
                print_warning("Usage: note [your text here]")
            else:
                save_data.setdefault("notes", {}).setdefault(op_id, []).append(note_text)
                print_success("Note saved.")
            continue

        # Edge case: bare "note" with no text
        if normalized == "note":
            print_warning("Usage: note [your text here]")
            continue

        # ------------------------------------------------------------------
        # Step 3 — Answer fallback
        # ------------------------------------------------------------------
        if check_answer(raw, op_data["valid_answers"]):
            save_data = _handle_correct_answer(op_id, op_data, save_data, start_time)
            return save_data
        else:
            save_data["metrics"][op_id]["attempts"] += 1
            print_error("Incorrect. Try again, or type 'hint' for help.")

    return save_data


def _handle_hint(op_id: str, op_data: dict, save_data: dict) -> dict:
    """Reveal the next unrevealed hint in order. Tracks hints_used."""
    _ensure_hints_used(save_data, op_id)
    _ensure_metrics(save_data, op_id)

    count = save_data["hints_used"].get(op_id, 0)
    hints = op_data.get("hints", [])

    if count >= 4:
        print_warning("No more hints available. Try 'tools'.")
        return save_data

    count += 1
    save_data["hints_used"][op_id] = count
    print_divider()
    print_warning(f"Hint {count}:")
    print_warning(hints[count - 1])
    print_divider()

    if count == 4:
        save_data["metrics"][op_id]["hints_maxed"] = True

    return save_data


def _handle_correct_answer(
    op_id: str, op_data: dict, save_data: dict, start_time: float
) -> dict:
    """Award XP, update save, display debrief, return updated save_data."""
    # 1. Stop timer
    elapsed = int(time.time() - start_time)
    save_data["metrics"][op_id]["time_spent_seconds"] += elapsed

    # 2. Get hints used
    hints_used = save_data["hints_used"].get(op_id, 0)

    # 3. Calculate XP
    xp_earned = calculate_xp(op_data["xp_base"], hints_used)

    # 4. Award XP
    save_data["xp"] = save_data.get("xp", 0) + xp_earned

    # 5. Mark completed
    if op_id not in save_data.get("completed", []):
        save_data.setdefault("completed", []).append(op_id)

    # 6. Update metrics
    save_data["metrics"][op_id]["completed"] = True

    # 7. Evaluate badges
    new_badges = evaluate_badges(save_data)

    # 8. Extend badges
    save_data.setdefault("badges", []).extend(new_badges)

    # 9. Save
    write_save(save_data)

    # 10. Display debrief
    clear_screen()
    print_header("OPERATION COMPLETE")
    print_divider()
    print_success(f"XP AWARDED: {xp_earned}")
    for badge in new_badges:
        print_success(f"Badge unlocked: {badge}")
    print_divider()
    debrief = op_data.get("debrief", {})
    print_info(debrief.get("summary", ""))
    print_divider()
    print_info(debrief.get("real_world", ""))
    print_divider()
    print_warning(debrief.get("next_step", ""))
    print_muted(debrief.get("cert_link", ""))
    print_divider()
    input("Press Enter to continue...")

    # 11. Return
    return save_data
