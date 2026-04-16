"""case_runner.py — AEGIS CyberForge

Generic case runner. Loads any case JSON and runs the command loop.
Handles all 9 commands: help, learn, tools, notes, note, hint, skip,
menu, quit.
"""

import json
import os
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.terminal import (
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
# Helpers
# ---------------------------------------------------------------------------

def _content_dir() -> str:
    """Return absolute path to aegis/content/cases/."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "content", "cases")


def _now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def _elapsed_seconds(started_at: str) -> int:
    """Return seconds elapsed since started_at ISO string."""
    try:
        start = datetime.fromisoformat(started_at)
        delta = datetime.now(timezone.utc) - start
        return int(delta.total_seconds())
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Load + Display
# ---------------------------------------------------------------------------

def load_case(case_id: str) -> dict:
    """Load and return a case JSON file by ID.

    Args:
        case_id: The case ID (e.g. 'case01').

    Returns:
        Parsed case dict.

    Raises:
        FileNotFoundError: If the case file does not exist.
    """
    filepath = os.path.join(_content_dir(), f"{case_id}.json")
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Case file not found: {filepath}\n"
            f"Run validate_content.py to check your content directory."
        )
    with open(filepath, "r", encoding="utf-8") as fh:
        return json.load(fh)


def display_intro(case_data: dict, tool_cmds: list) -> None:
    """Display case title, scenario, and challenge.

    Args:
        case_data: Parsed case dict.
        tool_cmds: List of accepted tool command aliases (first = primary).
    """
    clear_screen()
    print_header(f"[ {case_data['title'].upper()} ]")
    print_divider()
    print_info(case_data["scenario"])
    print_divider()
    print_warning(case_data["challenge"])
    print_divider()
    if tool_cmds:
        primary = tool_cmds[0]
        print_muted(f"Type '{primary}' to run the analyst tool.  Type 'help' for all commands.")
    else:
        print_muted("Type 'help' to see available commands.")


def _print_help(tool_cmds: list) -> None:
    """Print the list of available commands.

    Args:
        tool_cmds: Accepted tool aliases for this case (first = primary).
    """
    primary = tool_cmds[0] if tool_cmds else "tools"
    aliases = ", ".join(tool_cmds[1:]) if len(tool_cmds) > 1 else ""
    print_info("Available commands:")
    print_info("  help        — show this command list")
    print_info("  learn       — read the concept behind this case")
    if aliases:
        print_info(f"  {primary:<10}  — run the analyst tool  (also: {aliases}, tools)")
    else:
        print_info(f"  {primary:<10}  — run the analyst tool  (also: tools)")
    print_info("  notes       — view your saved notes for this case")
    print_info("  note <text> — save a note")
    print_info("  hint        — reveal the next hint (4 max; each reduces XP earned)")
    print_info("  skip        — skip this case and move on")
    print_info("  menu        — save and return to case menu")
    print_info("  quit        — save and exit the game")


# ---------------------------------------------------------------------------
# Command Loop
# ---------------------------------------------------------------------------

def run_case(case_id: str, save_data: dict) -> dict:
    """Run the interactive command loop for a single case.

    Handles all 9 commands with strict 3-step input priority:
      1. Exact command match
      2. Note prefix ("note <text>")
      3. Answer fallback

    Args:
        case_id: The case ID to load and run.
        save_data: The current player save dict (mutated in place).

    Returns:
        Updated save_data dict.
    """
    case_data = load_case(case_id)
    tool_cmds = get_tool_commands(case_data.get("tools_type", "none"))
    display_intro(case_data, tool_cmds)

    # Initialize per-case metrics on first entry
    save_data["metrics"].setdefault(case_id, {
        "completed": False,
        "hints_maxed": False,
        "time_spent_seconds": 0,
        "started_at": _now_iso(),
    })

    try:
        while True:
            print_divider()
            try:
                raw = input("> ").strip()
            except EOFError:
                break

            cmd = normalize_input(raw)

            # ----------------------------------------------------------------
            # Step 1 — exact command match
            # ----------------------------------------------------------------
            if cmd == "help":
                _print_help(tool_cmds)
                continue

            if cmd == "learn":
                print_divider()
                print_info(case_data["learn"])
                continue

            if cmd == "tools" or cmd in tool_cmds:
                print_divider()
                tool_input = case_data.get("challenge_data", case_data["challenge"])
                result = run_tool(case_data["tools_type"], tool_input)
                print_info(result)
                continue

            if cmd == "notes":
                case_notes = save_data["notes"].get(case_id, [])
                if case_notes:
                    print_divider()
                    for note in case_notes:
                        print_info(f"  • {note}")
                else:
                    print_muted("No notes yet. Type 'note <text>' to add one.")
                continue

            if cmd == "hint":
                hints_used = save_data["hints_used"].get(case_id, 0)
                if hints_used < 4:
                    print_divider()
                    print_warning(case_data["hints"][hints_used])
                    hints_used += 1
                    save_data["hints_used"][case_id] = hints_used
                    if hints_used == 4:
                        save_data["metrics"][case_id]["hints_maxed"] = True
                    xp_now = calculate_xp(case_data["xp_base"], hints_used)
                    remaining = 4 - hints_used
                    print_muted(
                        f"  Hint {hints_used}/4 used | "
                        f"XP if solved now: {xp_now} | "
                        f"Hints remaining: {remaining}"
                    )
                else:
                    print_warning("No more hints available. Try 'tools'.")
                continue

            if cmd == "skip":
                if case_id not in save_data["skipped"]:
                    save_data["skipped"].append(case_id)
                started = save_data["metrics"][case_id].get("started_at", _now_iso())
                save_data["metrics"][case_id]["time_spent_seconds"] += _elapsed_seconds(started)
                write_save(save_data)
                print_muted("Case skipped.")
                return save_data

            if cmd == "menu":
                write_save(save_data)
                return save_data

            if cmd == "quit":
                confirm = input("Save and exit? (y/n): ").strip().lower()
                if confirm == "y":
                    write_save(save_data)
                    print_muted("Progress saved. Goodbye.")
                    sys.exit(0)
                continue

            # ----------------------------------------------------------------
            # Step 2 — note prefix
            # ----------------------------------------------------------------
            if raw.lower().startswith("note "):
                note_text = raw[5:].strip()
                if not note_text:
                    print_muted("Usage: note <your note text>")
                    continue
                if case_id not in save_data["notes"]:
                    save_data["notes"][case_id] = []
                save_data["notes"][case_id].append(note_text)
                print_success("Note saved.")
                continue

            # ----------------------------------------------------------------
            # Step 3 — answer fallback
            # ----------------------------------------------------------------
            if not cmd:
                continue

            valid = [normalize_input(a) for a in case_data["valid_answers"]]
            if cmd in valid:
                _handle_correct(case_id, case_data, save_data)
                return save_data
            else:
                print_error("Incorrect. Try again, or type 'hint'.")

    except KeyboardInterrupt:
        write_save(save_data)
        print_muted("\nProgress saved.")
        return save_data

    return save_data


# ---------------------------------------------------------------------------
# Correct Answer + Debrief
# ---------------------------------------------------------------------------

def _handle_correct(case_id: str, case_data: dict, save_data: dict) -> None:
    """Handle a correct answer: award XP, badges, save, show debrief.

    No XP or badge awards on replay (case already in completed list).

    Args:
        case_id: The completed case ID.
        case_data: Parsed case dict.
        save_data: Current save dict (mutated in place).
    """
    hints_used = save_data["hints_used"].get(case_id, 0)
    is_replay = case_id in save_data["completed"]

    # XP and completion tracking
    if not is_replay:
        xp_earned = calculate_xp(case_data["xp_base"], hints_used)
        save_data["xp"] += xp_earned
        save_data["completed"].append(case_id)
    else:
        xp_earned = 0

    # Update metrics
    started = save_data["metrics"][case_id].get("started_at", _now_iso())
    save_data["metrics"][case_id]["completed"] = True
    save_data["metrics"][case_id]["time_spent_seconds"] += _elapsed_seconds(started)

    # Badges (first completion only)
    if not is_replay:
        new_badges = evaluate_badges(save_data, case_id, hints_used)
        save_data["badges"].extend(new_badges)
    else:
        new_badges = []

    write_save(save_data)

    # ---- Debrief display ----
    clear_screen()
    print_header("CASE COMPLETE")
    print_divider()

    if not is_replay:
        print_success(f"XP AWARDED: {xp_earned}")
    else:
        print_muted("(Replay — XP not awarded again)")

    for badge in new_badges:
        print_success(f"Badge unlocked: {badge}")

    print_divider()
    debrief = case_data["debrief"]
    print_info(debrief["summary"])
    print_divider()
    print_info(debrief["real_world"])
    print_divider()
    print_warning(debrief["next_step"])
    print_muted(debrief["cert_link"])
    print_divider()
    print_header("EXAM TIP")
    print_info(debrief["exam_tip"])
    print_divider()
    input("Press Enter to continue...")
