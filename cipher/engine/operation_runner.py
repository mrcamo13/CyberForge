"""operation_runner.py — CIPHER CyberForge

Generic operation engine. Reads any operation JSON by ID.
Supports two modes:
  - Multi-phase mode: operation JSON has a "steps" array — each phase is its
    own objective with hints and optional wrong-answer nudges. Shows as
    "Phase 1 of 3" to match the red-team / pentest terminology.
  - Single mode: legacy fallback for operations without "steps".

Commands (both modes): help, learn, tools, notes, note, hint, skip, menu, quit.
"""

import json
import os
import sys
import time

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
# Path helpers
# ---------------------------------------------------------------------------

def _ops_dir() -> str:
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


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def display_intro(op_data: dict, tool_cmds: list) -> None:
    """Clear screen and display the operation header + scenario."""
    clear_screen()
    print_header(f"=== OPERATION: {op_data['title'].upper()} ===")
    print_divider()
    print_info(op_data["scenario"])
    print_divider()
    if tool_cmds:
        primary = tool_cmds[0]
        aliases = ", ".join(tool_cmds[1:]) if len(tool_cmds) > 1 else ""
        if aliases:
            print_muted(
                f"Run '{primary}' to execute the tool  "
                f"(also: {aliases}, tools).  Type 'help' for all commands."
            )
        else:
            print_muted(
                f"Run '{primary}' to execute the tool.  "
                "Type 'help' for all commands."
            )
    else:
        print_muted("Type 'help' to see available commands.")
    print()


def _print_help(tool_cmds: list, multi_phase: bool = False) -> None:
    primary = tool_cmds[0] if tool_cmds else "tools"
    aliases = ", ".join(tool_cmds[1:]) if len(tool_cmds) > 1 else ""
    hint_note = "4 per phase, each reduces XP for that phase" if multi_phase else "4 max, each reduces XP earned"
    tool_line = (
        f"  {primary:<10} — run the in-game tool  (also: {aliases}, tools)"
        if aliases else
        f"  {primary:<10} — run the in-game tool  (also: tools)"
    )
    print_info("Available commands:")
    print_info("  help       — show this list")
    print_info("  learn      — display concept explanation for this operation")
    print_info(tool_line)
    print_info(f"  hint       — reveal next hint ({hint_note})")
    print_info("  notes      — view your saved notes for this operation")
    print_info("  note <text>— save a note for this operation")
    print_info("  skip       — mark operation as skipped, return to menu")
    print_info("  menu       — save progress and return to menu")
    print_info("  quit       — save progress and exit game")


def _show_phase_prompt(step_idx: int, n_steps: int, step: dict) -> None:
    """Print the current phase objective."""
    print_divider()
    print_header(f"  Phase {step_idx + 1} of {n_steps}")
    print_warning(f"  Objective: {step['question']}")
    print_divider()


# ---------------------------------------------------------------------------
# Wrong-answer nudge matching
# ---------------------------------------------------------------------------

def _find_nudge(cmd: str, wrong_answer_hints: list) -> str:
    for wah in wrong_answer_hints:
        pattern = wah.get("pattern", "").lower().strip()
        if pattern and pattern in cmd:
            return wah.get("response", "")
    return ""


# ---------------------------------------------------------------------------
# Shared command handlers
# ---------------------------------------------------------------------------

def _handle_tools(op_data: dict) -> None:
    print_divider()
    tool_input = op_data.get("challenge_data", op_data.get("challenge", ""))
    result = run_tool(op_data["tools_type"], tool_input)
    print_info(result)
    print_divider()


def _handle_notes(op_id: str, save_data: dict) -> None:
    notes = save_data.get("notes", {}).get(op_id, [])
    if notes:
        print_divider()
        for i, note in enumerate(notes, 1):
            print_info(f"  {i}. {note}")
        print_divider()
    else:
        print_muted("No notes yet. Type 'note <text>' to add one.")


def _handle_note_save(raw: str, op_id: str, save_data: dict) -> None:
    note_text = raw.strip()[5:].strip()
    if not note_text:
        print_warning("Usage: note <your text here>")
        return
    save_data.setdefault("notes", {}).setdefault(op_id, []).append(note_text)
    print_success("Note saved.")


def _ensure_metrics(save_data: dict, op_id: str) -> None:
    save_data["metrics"].setdefault(op_id, {
        "attempts": 0,
        "hints_maxed": False,
        "completed": False,
        "time_spent_seconds": 0,
        "current_step": 0,
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_operation(op_id: str, save_data: dict) -> dict:
    """Load and run an operation. Dispatches to phase or single mode."""
    try:
        op_data = load_operation(op_id)
    except FileNotFoundError as exc:
        print_error(str(exc))
        return save_data

    _ensure_metrics(save_data, op_id)
    save_data["hints_used"].setdefault(op_id, 0)
    save_data["in_progress"] = op_id

    tool_cmds = get_tool_commands(op_data.get("tools_type", ""))
    display_intro(op_data, tool_cmds)

    start_time = time.time()

    try:
        if op_data.get("steps"):
            return _run_phase_loop(op_id, op_data, save_data, tool_cmds, start_time)
        else:
            return _run_single_loop(op_id, op_data, save_data, tool_cmds, start_time)
    except KeyboardInterrupt:
        elapsed = int(time.time() - start_time)
        save_data["metrics"][op_id]["time_spent_seconds"] += elapsed
        write_save(save_data)
        print()
        print_muted("Progress saved. Returning to menu...")
        return save_data


# ---------------------------------------------------------------------------
# Multi-phase loop
# ---------------------------------------------------------------------------

def _run_phase_loop(
    op_id: str, op_data: dict, save_data: dict, tool_cmds: list, start_time: float
) -> dict:
    """Run the multi-phase operation loop.

    Each phase = one pentest objective (recon / foothold / escalation / exfil).
    XP is awarded per phase. Progress saved between phases for resume.
    """
    steps = op_data["steps"]
    n_steps = len(steps)
    is_replay = op_id in save_data.get("completed", [])
    total_xp_earned = 0

    start_step = 0 if is_replay else save_data["metrics"][op_id].get("current_step", 0)

    for step_idx in range(start_step, n_steps):
        step = steps[step_idx]
        step_hints_used = 0

        _show_phase_prompt(step_idx, n_steps, step)

        while True:
            try:
                raw = input(f"[{op_id.upper()}] > ")
            except EOFError:
                write_save(save_data)
                return save_data

            if not raw.strip():
                print_warning("Enter a command or your answer.")
                continue

            cmd = normalize_input(raw)

            if cmd == "help":
                _print_help(tool_cmds, multi_phase=True)
                continue

            if cmd == "learn":
                print_divider()
                print_info(op_data["learn"])
                print_divider()
                _show_phase_prompt(step_idx, n_steps, step)
                continue

            if cmd == "tools" or cmd in tool_cmds:
                _handle_tools(op_data)
                _show_phase_prompt(step_idx, n_steps, step)
                continue

            if cmd == "notes":
                _handle_notes(op_id, save_data)
                continue

            if cmd == "hint":
                step_hints = step.get("hints", [])
                if step_hints_used < len(step_hints):
                    print_divider()
                    print_warning(f"Hint {step_hints_used + 1}:")
                    print_warning(step_hints[step_hints_used])
                    print_divider()
                    step_hints_used += 1
                    save_data["hints_used"][op_id] = (
                        save_data["hints_used"].get(op_id, 0) + 1
                    )
                    remaining = len(step_hints) - step_hints_used
                    step_xp_preview = calculate_xp(
                        op_data["xp_base"] // n_steps, step_hints_used
                    )
                    print_muted(
                        f"  Hint {step_hints_used}/{len(step_hints)} for phase {step_idx + 1} "
                        f"| XP for this phase if correct now: {step_xp_preview} "
                        f"| Hints left: {remaining}"
                    )
                else:
                    print_warning("No more hints for this phase. Try 'tools'.")
                continue

            if cmd == "skip":
                elapsed = int(time.time() - start_time)
                save_data["metrics"][op_id]["time_spent_seconds"] += elapsed
                save_data["metrics"][op_id]["current_step"] = step_idx
                if op_id not in save_data.get("skipped", []):
                    save_data.setdefault("skipped", []).append(op_id)
                write_save(save_data)
                print_muted("Operation skipped.")
                return save_data

            if cmd == "menu":
                elapsed = int(time.time() - start_time)
                save_data["metrics"][op_id]["time_spent_seconds"] += elapsed
                save_data["metrics"][op_id]["current_step"] = step_idx
                write_save(save_data)
                return save_data

            if cmd == "quit":
                confirm = input("Save and exit? (y/n): ").strip().lower()
                if confirm == "y":
                    elapsed = int(time.time() - start_time)
                    save_data["metrics"][op_id]["time_spent_seconds"] += elapsed
                    save_data["metrics"][op_id]["current_step"] = step_idx
                    write_save(save_data)
                    print_muted("Progress saved. Goodbye.")
                    sys.exit(0)
                continue

            if cmd.startswith("note ") or raw.strip().lower().startswith("note "):
                _handle_note_save(raw, op_id, save_data)
                continue

            if cmd == "note":
                print_warning("Usage: note <your text here>")
                continue

            # ---- Answer check ----
            if check_answer(raw, step["valid_answers"]):
                step_xp_base = op_data["xp_base"] // n_steps
                step_xp = calculate_xp(step_xp_base, step_hints_used)

                if not is_replay:
                    save_data["xp"] = save_data.get("xp", 0) + step_xp
                    total_xp_earned += step_xp

                save_data["metrics"][op_id]["current_step"] = step_idx + 1
                write_save(save_data)

                if step_idx + 1 < n_steps:
                    print_divider()
                    if not is_replay:
                        print_success(f"  Phase {step_idx + 1} complete!  +{step_xp} XP")
                    else:
                        print_success(f"  Phase {step_idx + 1} complete!")
                    print()
                    break  # advance to next phase
                else:
                    break  # final phase — fall through to completion
            else:
                save_data["metrics"][op_id]["attempts"] += 1
                nudge = _find_nudge(cmd, step.get("wrong_answer_hints", []))
                if nudge:
                    print_warning(f"  Not quite — {nudge}")
                else:
                    print_error("Incorrect. Try again, or type 'hint' for help.")

    # All phases complete
    elapsed = int(time.time() - start_time)
    save_data["metrics"][op_id]["time_spent_seconds"] += elapsed
    _handle_completion(op_id, op_data, save_data, total_xp_earned, is_replay)
    return save_data


# ---------------------------------------------------------------------------
# Single-question loop (legacy / operations without steps)
# ---------------------------------------------------------------------------

def _run_single_loop(
    op_id: str, op_data: dict, save_data: dict, tool_cmds: list, start_time: float
) -> dict:
    """Original single-question loop. Used when no 'steps' key is present."""
    print_warning(op_data["challenge"])
    print_divider()

    while True:
        try:
            raw = input(f"\n[{op_id.upper()}] > ")
        except EOFError:
            break

        if not raw.strip():
            print_warning("Please enter a command or your answer.")
            continue

        normalized = normalize_input(raw)

        if normalized == "help":
            _print_help(tool_cmds)
            continue

        if normalized == "learn":
            print_divider()
            print_info(op_data["learn"])
            print_divider()
            continue

        if normalized == "tools" or normalized in tool_cmds:
            _handle_tools(op_data)
            continue

        if normalized == "hint":
            count = save_data["hints_used"].get(op_id, 0)
            hints = op_data.get("hints", [])
            if count >= 4:
                print_warning("No more hints available. Try 'tools'.")
            else:
                count += 1
                save_data["hints_used"][op_id] = count
                print_divider()
                print_warning(f"Hint {count}:")
                print_warning(hints[count - 1])
                print_divider()
                if count == 4:
                    save_data["metrics"][op_id]["hints_maxed"] = True
            continue

        if normalized == "notes":
            _handle_notes(op_id, save_data)
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

        if normalized.startswith("note "):
            _handle_note_save(raw, op_id, save_data)
            continue

        if normalized == "note":
            print_warning("Usage: note <your text here>")
            continue

        if check_answer(raw, op_data["valid_answers"]):
            elapsed = int(time.time() - start_time)
            save_data["metrics"][op_id]["time_spent_seconds"] += elapsed
            hints_used = save_data["hints_used"].get(op_id, 0)
            is_replay = op_id in save_data.get("completed", [])
            xp = 0 if is_replay else calculate_xp(op_data["xp_base"], hints_used)
            if not is_replay:
                save_data["xp"] = save_data.get("xp", 0) + xp
            _handle_completion(op_id, op_data, save_data, xp, is_replay)
            return save_data
        else:
            save_data["metrics"][op_id]["attempts"] += 1
            nudge = _find_nudge(normalized, op_data.get("wrong_answer_hints", []))
            if nudge:
                print_warning(f"  Not quite — {nudge}")
            else:
                print_error("Incorrect. Try again, or type 'hint' for help.")

    return save_data


# ---------------------------------------------------------------------------
# Completion + Debrief
# ---------------------------------------------------------------------------

def _handle_completion(
    op_id: str,
    op_data: dict,
    save_data: dict,
    xp_earned: int,
    is_replay: bool,
) -> None:
    """Award XP, badges, update metrics, display debrief."""
    hints_used = save_data["hints_used"].get(op_id, 0)

    if not is_replay:
        if op_id not in save_data.get("completed", []):
            save_data.setdefault("completed", []).append(op_id)
        new_badges = evaluate_badges(save_data)
        save_data.setdefault("badges", []).extend(new_badges)
    else:
        new_badges = []

    save_data["metrics"][op_id]["completed"] = True

    write_save(save_data)

    clear_screen()
    n_steps = len(op_data.get("steps", []))
    if n_steps > 1:
        print_header(f"OPERATION COMPLETE  --  ALL {n_steps} PHASES DONE")
    else:
        print_header("OPERATION COMPLETE")
    print_divider()

    if not is_replay:
        print_success(f"XP AWARDED: {xp_earned}")
    else:
        print_muted("(Replay — XP not awarded again)")

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
