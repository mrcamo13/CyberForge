"""case_runner.py — AEGIS CyberForge

Generic case runner. Supports two modes:
  - Multi-step mode: case JSON has a "steps" array — each step is its own
    question with its own hints and optional wrong-answer nudges.
  - Single mode: legacy fallback for cases without "steps".

Commands (both modes): help, learn, tools, notes, note, hint, skip, menu, quit.
"""

import json
import os
import sys
from datetime import datetime, timezone

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
# Path helpers
# ---------------------------------------------------------------------------

def _content_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "content", "cases")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _elapsed_seconds(started_at: str) -> int:
    try:
        start = datetime.fromisoformat(started_at)
        return int((datetime.now(timezone.utc) - start).total_seconds())
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_case(case_id: str) -> dict:
    filepath = os.path.join(_content_dir(), f"{case_id}.json")
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Case file not found: {filepath}\n"
            "Run validate_content.py to check your content directory."
        )
    with open(filepath, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def display_intro(case_data: dict, tool_cmds: list) -> None:
    """Clear screen and display the case header + scenario."""
    clear_screen()
    print_header(f"[ {case_data['title'].upper()} ]")
    print_divider()
    print_info(case_data["scenario"])
    print_divider()
    if tool_cmds:
        primary = tool_cmds[0]
        aliases = ", ".join(tool_cmds[1:]) if len(tool_cmds) > 1 else ""
        if aliases:
            print_muted(
                f"Run '{primary}' to examine the evidence  "
                f"(also: {aliases}, tools).  Type 'help' for all commands."
            )
        else:
            print_muted(
                f"Run '{primary}' to examine the evidence.  "
                "Type 'help' for all commands."
            )
    else:
        print_muted("Type 'help' to see available commands.")


def _print_help(tool_cmds: list, multi_step: bool = False) -> None:
    primary = tool_cmds[0] if tool_cmds else "tools"
    aliases = ", ".join(tool_cmds[1:]) if len(tool_cmds) > 1 else ""
    hint_note = "4 per step, each reduces XP for that step" if multi_step else "4 max, each reduces XP earned"
    print_info("Available commands:")
    print_info("  help        — show this command list")
    print_info("  learn       — read the concept behind this case")
    if aliases:
        print_info(f"  {primary:<10}  — run the analyst tool  (also: {aliases}, tools)")
    else:
        print_info(f"  {primary:<10}  — run the analyst tool  (also: tools)")
    print_info("  notes       — view your saved notes for this case")
    print_info("  note <text> — save a note")
    print_info(f"  hint        — reveal the next hint ({hint_note})")
    print_info("  skip        — skip this case and move on")
    print_info("  menu        — save and return to case menu")
    print_info("  quit        — save and exit the game")


def _show_step_prompt(step_idx: int, n_steps: int, step: dict) -> None:
    """Print the current step question."""
    print_divider()
    print_header(f"  Step {step_idx + 1} of {n_steps}")
    print_warning(f"  {step['question']}")
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

def _handle_tools(case_data: dict, tool_cmds: list) -> None:
    print_divider()
    tool_input = case_data.get("challenge_data", case_data.get("challenge", ""))
    result = run_tool(case_data["tools_type"], tool_input)
    print_info(result)


def _handle_notes(case_id: str, save_data: dict) -> None:
    case_notes = save_data["notes"].get(case_id, [])
    if case_notes:
        print_divider()
        for note in case_notes:
            print_info(f"  • {note}")
    else:
        print_muted("No notes yet. Type 'note <text>' to add one.")


def _handle_note_save(raw: str, case_id: str, save_data: dict) -> None:
    note_text = raw[5:].strip()
    if not note_text:
        print_muted("Usage: note <your note text>")
        return
    save_data["notes"].setdefault(case_id, []).append(note_text)
    print_success("Note saved.")


def _handle_skip(case_id: str, save_data: dict) -> None:
    if case_id not in save_data["skipped"]:
        save_data["skipped"].append(case_id)
    started = save_data["metrics"][case_id].get("started_at", _now_iso())
    save_data["metrics"][case_id]["time_spent_seconds"] += _elapsed_seconds(started)
    write_save(save_data)
    print_muted("Case skipped.")


def _handle_quit(case_id: str, save_data: dict) -> None:
    confirm = input("Save and exit? (y/n): ").strip().lower()
    if confirm == "y":
        started = save_data["metrics"][case_id].get("started_at", _now_iso())
        save_data["metrics"][case_id]["time_spent_seconds"] += _elapsed_seconds(started)
        write_save(save_data)
        print_muted("Progress saved. Goodbye.")
        sys.exit(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_case(case_id: str, save_data: dict) -> dict:
    """Load and run a case. Dispatches to step or single mode automatically."""
    case_data = load_case(case_id)
    tool_cmds = get_tool_commands(case_data.get("tools_type", "none"))
    display_intro(case_data, tool_cmds)

    save_data["metrics"].setdefault(case_id, {
        "completed": False,
        "hints_maxed": False,
        "time_spent_seconds": 0,
        "started_at": _now_iso(),
        "current_step": 0,
    })

    try:
        if case_data.get("steps"):
            return _run_step_loop(case_id, case_data, save_data, tool_cmds)
        else:
            return _run_single_loop(case_id, case_data, save_data, tool_cmds)
    except KeyboardInterrupt:
        started = save_data["metrics"][case_id].get("started_at", _now_iso())
        save_data["metrics"][case_id]["time_spent_seconds"] += _elapsed_seconds(started)
        write_save(save_data)
        print_muted("\nProgress saved.")
        return save_data


# ---------------------------------------------------------------------------
# Multi-step loop
# ---------------------------------------------------------------------------

def _run_step_loop(
    case_id: str, case_data: dict, save_data: dict, tool_cmds: list
) -> dict:
    """Run the multi-step investigation loop.

    Each step has its own question, hints (up to 4), and optional
    wrong-answer nudges. XP is awarded per step so players see progress.
    Progress is saved between steps so players can resume mid-case.
    """
    steps = case_data["steps"]
    n_steps = len(steps)
    is_replay = case_id in save_data["completed"]
    total_xp_earned = 0

    start_step = 0 if is_replay else save_data["metrics"][case_id].get("current_step", 0)

    for step_idx in range(start_step, n_steps):
        step = steps[step_idx]
        step_hints_used = 0

        _show_step_prompt(step_idx, n_steps, step)

        while True:
            try:
                raw = input("> ").strip()
            except EOFError:
                write_save(save_data)
                return save_data

            cmd = normalize_input(raw)

            if cmd == "help":
                _print_help(tool_cmds, multi_step=True)
                continue

            if cmd == "learn":
                print_divider()
                print_info(case_data["learn"])
                _show_step_prompt(step_idx, n_steps, step)
                continue

            if cmd == "tools" or cmd in tool_cmds:
                _handle_tools(case_data, tool_cmds)
                _show_step_prompt(step_idx, n_steps, step)
                continue

            if cmd == "notes":
                _handle_notes(case_id, save_data)
                continue

            if cmd == "hint":
                step_hints = step.get("hints", [])
                if step_hints_used < len(step_hints):
                    print_divider()
                    print_warning(step_hints[step_hints_used])
                    step_hints_used += 1
                    save_data["hints_used"][case_id] = (
                        save_data["hints_used"].get(case_id, 0) + 1
                    )
                    remaining = len(step_hints) - step_hints_used
                    step_xp_preview = calculate_xp(
                        case_data["xp_base"] // n_steps, step_hints_used
                    )
                    print_muted(
                        f"  Hint {step_hints_used}/{len(step_hints)} for step {step_idx + 1} "
                        f"| XP for this step if correct now: {step_xp_preview} "
                        f"| Hints left: {remaining}"
                    )
                else:
                    print_warning("No more hints for this step. Try the analyst tool.")
                continue

            if cmd == "skip":
                save_data["metrics"][case_id]["current_step"] = step_idx
                _handle_skip(case_id, save_data)
                return save_data

            if cmd == "menu":
                save_data["metrics"][case_id]["current_step"] = step_idx
                started = save_data["metrics"][case_id].get("started_at", _now_iso())
                save_data["metrics"][case_id]["time_spent_seconds"] += _elapsed_seconds(started)
                write_save(save_data)
                return save_data

            if cmd == "quit":
                save_data["metrics"][case_id]["current_step"] = step_idx
                _handle_quit(case_id, save_data)
                continue

            if raw.lower().startswith("note "):
                _handle_note_save(raw, case_id, save_data)
                continue

            if not cmd:
                continue

            # ---- Answer check ----
            valid = [normalize_input(a) for a in step["valid_answers"]]
            if cmd in valid:
                step_xp_base = case_data["xp_base"] // n_steps
                step_xp = calculate_xp(step_xp_base, step_hints_used)

                if not is_replay:
                    save_data["xp"] += step_xp
                    total_xp_earned += step_xp

                save_data["metrics"][case_id]["current_step"] = step_idx + 1
                write_save(save_data)

                if step_idx + 1 < n_steps:
                    print_divider()
                    if not is_replay:
                        print_success(f"  Correct!  +{step_xp} XP")
                    else:
                        print_success("  Correct!")
                    print()
                    break  # advance to next step
                else:
                    break  # final step — fall through to completion
            else:
                nudge = _find_nudge(cmd, step.get("wrong_answer_hints", []))
                if nudge:
                    print_warning(f"  Not quite — {nudge}")
                else:
                    print_error("  Incorrect. Try again, or type 'hint'.")

    _handle_completion(case_id, case_data, save_data, total_xp_earned, is_replay)
    return save_data


# ---------------------------------------------------------------------------
# Single-question loop (legacy / cases without steps)
# ---------------------------------------------------------------------------

def _run_single_loop(
    case_id: str, case_data: dict, save_data: dict, tool_cmds: list
) -> dict:
    """Original single-question loop. Used when no 'steps' key is present."""
    print_divider()
    print_warning(case_data["challenge"])
    print_divider()

    while True:
        try:
            raw = input("> ").strip()
        except EOFError:
            break

        cmd = normalize_input(raw)

        if cmd == "help":
            _print_help(tool_cmds)
            continue

        if cmd == "learn":
            print_divider()
            print_info(case_data["learn"])
            continue

        if cmd == "tools" or cmd in tool_cmds:
            _handle_tools(case_data, tool_cmds)
            continue

        if cmd == "notes":
            _handle_notes(case_id, save_data)
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
                print_muted(
                    f"  Hint {hints_used}/4 used | "
                    f"XP if solved now: {xp_now} | "
                    f"Remaining: {4 - hints_used}"
                )
            else:
                print_warning("No more hints available. Try 'tools'.")
            continue

        if cmd == "skip":
            _handle_skip(case_id, save_data)
            return save_data

        if cmd == "menu":
            started = save_data["metrics"][case_id].get("started_at", _now_iso())
            save_data["metrics"][case_id]["time_spent_seconds"] += _elapsed_seconds(started)
            write_save(save_data)
            return save_data

        if cmd == "quit":
            _handle_quit(case_id, save_data)
            continue

        if raw.lower().startswith("note "):
            _handle_note_save(raw, case_id, save_data)
            continue

        if not cmd:
            continue

        valid = [normalize_input(a) for a in case_data["valid_answers"]]
        if cmd in valid:
            hints_used = save_data["hints_used"].get(case_id, 0)
            is_replay = case_id in save_data["completed"]
            xp = 0 if is_replay else calculate_xp(case_data["xp_base"], hints_used)
            if not is_replay:
                save_data["xp"] += xp
            _handle_completion(case_id, case_data, save_data, xp, is_replay)
            return save_data
        else:
            nudge = _find_nudge(cmd, case_data.get("wrong_answer_hints", []))
            if nudge:
                print_warning(f"  Not quite — {nudge}")
            else:
                print_error("Incorrect. Try again, or type 'hint'.")

    return save_data


# ---------------------------------------------------------------------------
# Completion + Debrief
# ---------------------------------------------------------------------------

def _handle_completion(
    case_id: str,
    case_data: dict,
    save_data: dict,
    xp_earned: int,
    is_replay: bool,
) -> None:
    """Award XP, badges, update metrics, display debrief."""
    hints_used = save_data["hints_used"].get(case_id, 0)

    if not is_replay:
        save_data["completed"].append(case_id)
        new_badges = evaluate_badges(save_data, case_id, hints_used)
        save_data["badges"].extend(new_badges)
    else:
        new_badges = []

    started = save_data["metrics"][case_id].get("started_at", _now_iso())
    save_data["metrics"][case_id]["completed"] = True
    save_data["metrics"][case_id]["time_spent_seconds"] += _elapsed_seconds(started)

    write_save(save_data)

    clear_screen()
    n_steps = len(case_data.get("steps", []))
    if n_steps > 1:
        print_header(f"CASE COMPLETE  --  ALL {n_steps} STEPS SOLVED")
    else:
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
