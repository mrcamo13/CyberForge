"""main.py — FORENSICS CyberForge (Digital Investigation Lab)

Entry point for the FORENSICS simulator.
All 20 cases are always available — no locking.

Features:
  - Stage grouping: File Forensics (1-5), Memory Forensics (6-10),
    Log & Artifact Analysis (11-15), Incident Response (16-20)
  - Stats screen: [s] — XP, time, streak, badges, per-case breakdown
  - Notes viewer: [n <id>] — view notes saved during a case
"""

import json
import os
import sys

_FORENSICS_DIR = os.path.dirname(os.path.abspath(__file__))
if _FORENSICS_DIR not in sys.path:
    sys.path.insert(0, _FORENSICS_DIR)

from utils.terminal import (
    print_success, print_error, print_warning, print_info,
    print_muted, print_header, print_divider, clear_screen,
    normalize_input,
)
from utils.save_manager import (
    create_save, write_save, load_with_fallback, list_saves,
)
from utils.player import get_badge_labels
from engine.case_runner import load_registry, run_case


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DIFFICULTY_STARS = {1: " * ", 2: " **", 3: "***", 4: "****"}
_TOTAL_CASES = 20
_STAGE_LABELS = {
    "stage1": "Stage 1 -- File & Metadata Forensics  (cases 01-05)",
    "stage2": "Stage 2 -- Memory Forensics           (cases 06-10)",
    "stage3": "Stage 3 -- Log & Artifact Analysis    (cases 11-15)",
    "stage4": "Stage 4 -- Incident Response          (cases 16-20)",
}


# ---------------------------------------------------------------------------
# Save helpers
# ---------------------------------------------------------------------------

def _pick_or_create_save() -> dict | None:
    """Ask the player to continue, create a new profile, or quit."""
    saves = list_saves()

    clear_screen()
    print_header("""
  +------------------------------------------+
  |  FORENSICS  --  CyberForge Investigation |
  |  Digital Evidence & Incident Analysis    |
  +------------------------------------------+
""")

    if saves:
        print_info("  Saved profiles:")
        for i, s in enumerate(saves, 1):
            xp = s.get("xp", 0)
            done = s.get("completed_count", 0)
            print_muted(
                f"    [{i}] {s['name']:<20} XP: {xp:<6} "
                f"{done}/{_TOTAL_CASES} complete"
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
# Case menu
# ---------------------------------------------------------------------------

def _case_menu(save_data: dict) -> None:
    """Display the case selection menu and dispatch to run_case."""
    registry = load_registry()
    # load_registry() normalises to "cases" key; also fall back to "challenges"
    cases = registry.get("cases", [])
    if not cases:
        print_error("No cases found. Check content/registry.json.")
        return

    stages = registry.get("stages", [])

    while True:
        clear_screen()
        completed = save_data.get("completed", [])
        skipped = save_data.get("skipped", [])
        xp = save_data.get("xp", 0)
        badges = save_data.get("badges", [])
        name = save_data.get("player_name", "Investigator")

        bar = _build_progress_bar(len(completed), _TOTAL_CASES)

        print_header(f"\n  FORENSICS  --  {name}")
        print_muted(f"  Progress: {bar}")
        print_muted(f"  XP: {xp}  |  Badges: {len(badges)}")
        print()

        # Build index number -> case mapping
        idx_to_case = {}
        idx = 1
        for stage in stages:
            print_divider()
            stage_label = _STAGE_LABELS.get(stage["id"], stage.get("title", stage["id"]))
            stage_cases = stage.get("cases") or stage.get("challenges") or []
            stage_done = sum(1 for cid in stage_cases if cid in completed)
            stage_total = len(stage_cases)
            print_header(f"  {stage_label}  [{stage_done}/{stage_total}]")
            print_divider()

            for cid in stage_cases:
                entry = next((c for c in cases if c["id"] == cid), None)
                if not entry:
                    continue
                title = entry["title"]
                diff = entry.get("difficulty", 1)
                stars = _DIFFICULTY_STARS.get(diff, " * ")
                if cid in completed:
                    done_mark = "[X]"
                elif cid in skipped:
                    done_mark = "[-]"
                else:
                    done_mark = "[ ]"
                print_info(f"  [{idx}] {done_mark} {title:<26} {stars}")
                idx_to_case[str(idx)] = cid
                idx += 1

        print()
        print_muted("  [s] Stats  [0] Back")
        print()

        choice = input("  Select case> ").strip().lower()

        if choice == "0":
            break

        if choice == "s":
            _stats_screen(save_data, cases, stages)
            continue

        # Notes viewer: "n case03" or "n 3"
        if choice.startswith("n "):
            target = choice[2:].strip()
            if target.isdigit() and target in idx_to_case:
                target = idx_to_case[target]
            _notes_screen(save_data, target)
            continue

        if choice in idx_to_case:
            cid = idx_to_case[choice]
            try:
                save_data = run_case(cid, save_data)
            except FileNotFoundError:
                print_error(f"Could not load case data for {cid}.")
                input("Press Enter to continue...")
                continue

            # End-game check
            if len(save_data.get("completed", [])) >= _TOTAL_CASES:
                if "master_investigator" in save_data.get("badges", []):
                    _end_game_screen(save_data)
            continue

        print_warning("  Invalid choice.")
        input("  Press Enter to continue...")


# ---------------------------------------------------------------------------
# Stats screen
# ---------------------------------------------------------------------------

def _stats_screen(save_data: dict, cases: list, stages: list) -> None:
    """Display full stats: progress, XP, time, streak, badges, per-case."""
    clear_screen()
    completed = save_data.get("completed", [])
    skipped = save_data.get("skipped", [])
    xp = save_data.get("xp", 0)
    badges = save_data.get("badges", [])
    streak = save_data.get("streak", {})
    total_seconds = save_data.get("total_time_played_seconds", 0)
    name = save_data.get("player_name", "Investigator")

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    bar = _build_progress_bar(len(completed), _TOTAL_CASES)

    print_header("\n  STATS")
    print_divider()
    print_info(f"  Investigator: {name}")
    print_info(f"  Progress:     {bar}")
    print_info(f"  XP:           {xp}")
    print_info(f"  Time:         {hours}h {minutes}m {seconds}s")
    print_info(
        f"  Streak:       {streak.get('current', 0)} day(s) "
        f"(best: {streak.get('longest', 0)})"
    )

    print()
    print_header("  BADGES")
    print_divider()
    badge_labels = get_badge_labels()
    for badge_id, label in badge_labels.items():
        mark = "[X]" if badge_id in badges else "[ ]"
        print_info(f"  {mark} {label}")

    hints_used = save_data.get("hints_used", {})
    metrics = save_data.get("metrics", {})

    for stage in stages:
        stage_label = _STAGE_LABELS.get(stage["id"], stage["id"])
        print()
        print_header(f"  {stage_label}")
        print_divider()
        for cid in (stage.get("cases") or stage.get("challenges") or []):
            entry = next((c for c in cases if c["id"] == cid), None)
            title = entry["title"] if entry else cid
            if cid in completed:
                done = "[X]"
            elif cid in skipped:
                done = "[-]"
            else:
                done = "[ ]"
            h = hints_used.get(cid, 0)
            t = metrics.get(cid, {}).get("time_spent_seconds", 0)
            tm = f"{t // 60}m {t % 60:02d}s"
            has_notes = bool(save_data.get("notes", {}).get(cid))
            notes_mark = " [notes]" if has_notes else ""
            print_muted(
                f"  {done} {title:<26} hints: {h}  time: {tm}{notes_mark}"
            )

    print()
    input("  Press Enter to return...")


# ---------------------------------------------------------------------------
# Notes screen
# ---------------------------------------------------------------------------

def _notes_screen(save_data: dict, case_id: str) -> None:
    """Display saved notes for a case."""
    clear_screen()
    notes = save_data.get("notes", {}).get(case_id, [])
    print_header(f"\n  NOTES -- {case_id.upper()}")
    print_divider()
    if notes:
        for i, note in enumerate(notes, 1):
            print_info(f"  {i}. {note}")
    else:
        print_muted("  No notes for this case.")
    print()
    input("  Press Enter to return...")


# ---------------------------------------------------------------------------
# End-game screen
# ---------------------------------------------------------------------------

def _end_game_screen(save_data: dict) -> None:
    """Show the Master Investigator end-game screen."""
    clear_screen()
    xp = save_data.get("xp", 0)
    badges = save_data.get("badges", [])
    total_seconds = save_data.get("total_time_played_seconds", 0)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    print_success("""
  ======================================================
       MASTER INVESTIGATOR -- ALL 20 CASES CLOSED
  ======================================================
""")
    print_success(f"  Total XP:     {xp}")
    print_success(f"  Badges:       {len(badges)}/6")
    print_success(f"  Time played:  {hours}h {minutes}m")
    print()
    print_header("  You've closed every FORENSICS investigation.")
    print_info(
        "  The skills you applied here cover the full DFIR toolkit:\n\n"
        "    File signatures  |  Metadata analysis  |  Hash verification\n"
        "    Memory forensics |  Event log analysis  |  Registry forensics\n"
        "    Browser history  |  Email tracing       |  PCAP analysis\n"
        "    Prefetch         |  Threat intel        |  Incident Response\n"
    )
    print_info(
        "  Your next step: apply these skills in the AEGIS Blue Team\n"
        "  simulator for live SOC investigation scenarios."
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
    _case_menu(save_data)


if __name__ == "__main__":
    main()
