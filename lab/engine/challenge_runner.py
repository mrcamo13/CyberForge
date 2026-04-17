"""challenge_runner.py — LAB CyberForge (Script Lab)

Core engine for Script Lab challenges.

Responsibilities:
  - Set up the workspace (write starter_code, copy fixtures)
  - Run the player's solution.py via subprocess (single or multi test-case)
  - Normalize and validate output line-by-line
  - Manage background TCP server (lab05 port 7005, lab12 port 7012, etc.)
  - Display scenario, debrief, hint system
  - Timed mode: show elapsed seconds at the prompt
  - Replay: save solution.py content to save_data["solutions"] on completion
  - Award XP and badges on completion

The player edits workspace/solution.py in their own editor and types
'run' to execute it. The engine captures stdout, compares it to
expected_output, and reports pass or fail with a diff.

Test-case model:
  If challenge JSON has a "test_cases" list, each entry is run in order:
    {description, args, fixtures, expected_output}
  All must pass for the challenge to be marked complete.
  If no "test_cases" field, falls back to single "expected_output" mode.
"""

import json
import os
import shutil
import socket
import sys
import threading
import time
from datetime import datetime, timezone

import subprocess  # noqa

from utils.terminal import (
    print_success, print_error, print_warning, print_info,
    print_muted, print_header, print_divider, clear_screen,
    normalize_input,
)
from utils.player import calculate_xp, evaluate_badges, get_badge_labels
from utils.save_manager import write_save


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CONTENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "content")
_FIXTURES_DIR = os.path.join(_CONTENT_DIR, "fixtures")
_WORKSPACE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workspace")

_SOLUTION_FILE = "solution.py"
_RUN_TIMEOUT = 10  # seconds


# ---------------------------------------------------------------------------
# Workspace management
# ---------------------------------------------------------------------------

def _setup_workspace(challenge_data: dict, extra_fixtures: list | None = None) -> str:
    """Write starter_code and copy fixtures into the workspace directory.

    Args:
        challenge_data: The challenge JSON dict.
        extra_fixtures: Optional additional fixture list (for per-test-case overrides).

    Returns:
        Absolute path to the workspace directory.
    """
    workspace = os.path.abspath(_WORKSPACE_DIR)
    os.makedirs(workspace, exist_ok=True)

    # Write starter_code → solution.py (only if solution.py doesn't already exist
    # from a previous run in this session — don't overwrite player's edits)
    solution_path = os.path.join(workspace, _SOLUTION_FILE)
    if not os.path.exists(solution_path):
        starter = challenge_data.get("starter_code", "# Write your solution here\n")
        with open(solution_path, "w", encoding="utf-8") as fh:
            fh.write(starter)

    # Copy challenge-level fixtures
    for fixture_name in challenge_data.get("fixtures", []):
        _copy_fixture(fixture_name, workspace)

    # Copy per-test-case fixtures if provided
    if extra_fixtures:
        for fixture_name in extra_fixtures:
            _copy_fixture(fixture_name, workspace)

    return workspace


def _copy_fixture(fixture_name: str, workspace: str) -> None:
    """Copy a fixture file from content/fixtures/ into the workspace."""
    src = os.path.join(_FIXTURES_DIR, fixture_name)
    dst = os.path.join(workspace, fixture_name)
    if os.path.exists(src):
        shutil.copy2(src, dst)


def _reset_starter(challenge_data: dict) -> None:
    """Overwrite solution.py with the original starter code."""
    workspace = os.path.abspath(_WORKSPACE_DIR)
    os.makedirs(workspace, exist_ok=True)
    solution_path = os.path.join(workspace, _SOLUTION_FILE)
    starter = challenge_data.get("starter_code", "# Write your solution here\n")
    with open(solution_path, "w", encoding="utf-8") as fh:
        fh.write(starter)


# ---------------------------------------------------------------------------
# Output normalization and validation
# ---------------------------------------------------------------------------

def normalize_output(raw: str) -> list:
    """Split output into lines, rstrip each, strip trailing blank lines."""
    lines = [line.rstrip() for line in raw.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def validate_output(actual_raw: str, expected_raw: str) -> tuple:
    """Compare actual output to expected after normalization.

    Returns:
        (passed: bool, diff_lines: list[str])
    """
    actual = normalize_output(actual_raw)
    expected = normalize_output(expected_raw)

    if actual == expected:
        return True, []

    diff = []
    max_lines = max(len(actual), len(expected))
    for i in range(max_lines):
        a_line = actual[i] if i < len(actual) else "<missing>"
        e_line = expected[i] if i < len(expected) else "<extra>"
        if a_line != e_line:
            diff.append(f"  Line {i + 1}:")
            diff.append(f"    expected: {e_line!r}")
            diff.append(f"    got:      {a_line!r}")

    return False, diff


# ---------------------------------------------------------------------------
# Solution runner
# ---------------------------------------------------------------------------

def _run_solution(workspace: str, args: list | None = None,
                  timeout: int = _RUN_TIMEOUT) -> tuple:
    """Run workspace/solution.py and capture stdout/stderr.

    Args:
        workspace: Absolute path to workspace directory.
        args: Optional list of strings passed as sys.argv[1:].
        timeout: Maximum seconds before the process is killed.

    Returns:
        (stdout: str, stderr: str, error_msg: str | None)
    """
    solution_path = os.path.join(workspace, _SOLUTION_FILE)
    if not os.path.exists(solution_path):
        return "", "", "solution.py not found in workspace."

    cmd = [sys.executable, _SOLUTION_FILE] + (args or [])

    try:
        result = subprocess.run(
            cmd,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout, result.stderr, None
    except subprocess.TimeoutExpired:
        return "", "", f"Script timed out after {timeout} seconds."
    except OSError as exc:
        return "", "", f"Could not run solution.py: {exc}"


# ---------------------------------------------------------------------------
# Background TCP servers
# ---------------------------------------------------------------------------

def _make_banner_server(banner: str):
    """Return a server factory that sends *banner* on each connection."""
    def _serve(port: int, stop_event: threading.Event) -> None:
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("127.0.0.1", port))
            srv.listen(5)
            srv.settimeout(0.5)
            while not stop_event.is_set():
                try:
                    conn, _ = srv.accept()
                    conn.sendall((banner + "\n").encode())
                    conn.close()
                except socket.timeout:
                    pass
            srv.close()
        except OSError:
            pass
    return _serve


def _start_test_server(port: int, banner: str | None = None) -> threading.Event:
    """Start a background TCP server on *port*.

    If *banner* is provided the server sends it to each connecting client
    (used for lab12 banner grabber). Otherwise it just accepts connections
    and closes them (used for lab05 port scanner).

    Returns:
        stop_event — set this to shut the server down.
    """
    stop_event = threading.Event()

    if banner:
        target = _make_banner_server(banner)

        def _thread():
            target(port, stop_event)
    else:
        def _thread():
            try:
                srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                srv.bind(("127.0.0.1", port))
                srv.listen(5)
                srv.settimeout(0.5)
                while not stop_event.is_set():
                    try:
                        conn, _ = srv.accept()
                        conn.close()
                    except socket.timeout:
                        pass
                srv.close()
            except OSError:
                pass

    t = threading.Thread(target=_thread, daemon=True)
    t.start()
    time.sleep(0.15)  # give the socket time to bind
    return stop_event


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _display_intro(challenge_data: dict, timed_mode: bool = False) -> None:
    """Print the scenario text and challenge description."""
    clear_screen()
    print_header(challenge_data.get("scenario", ""))
    print()
    print_divider()
    print_info(challenge_data.get("challenge", ""))
    print_divider()
    print()

    test_cases = challenge_data.get("test_cases")
    if test_cases:
        print_muted(f"  This challenge has {len(test_cases)} test case(s) — all must pass.")
        print()

    timed_note = "  [TIMED MODE]" if timed_mode else ""
    print_muted(f"Commands: run | hint | learn | status | reset | quit{timed_note}")
    print_muted(f"Your script: workspace/{_SOLUTION_FILE}")
    print()


def _display_hint(challenge_data: dict, hint_index: int, hints_used: int) -> None:
    """Print a hint and XP cost summary."""
    hints = challenge_data.get("hints", [])
    xp_base = challenge_data.get("xp_base", 100)
    remaining = len(hints) - hints_used

    if hint_index < len(hints):
        print_warning(f"\n[HINT {hint_index + 1}/{len(hints)}]")
        print_warning(hints[hint_index])
    else:
        print_warning("No more hints available.")

    xp_now = calculate_xp(xp_base, hints_used)
    print_muted(
        f"\nHints used: {hints_used}/{len(hints)} | "
        f"XP if solved now: {xp_now} | "
        f"Hints remaining: {max(0, remaining - 1)}"
    )
    print()


def _display_debrief(challenge_data: dict, xp_earned: int, new_badges: list,
                     elapsed_seconds: int) -> None:
    """Print the post-solve debrief screen."""
    debrief = challenge_data.get("debrief", {})
    badge_labels = get_badge_labels()
    mins = elapsed_seconds // 60
    secs = elapsed_seconds % 60

    clear_screen()
    print_success("=" * 60)
    print_success("  CHALLENGE COMPLETE")
    print_success("=" * 60)
    print()
    print_success(f"  +{xp_earned} XP  |  Time: {mins}m {secs}s")

    if new_badges:
        print()
        for b in new_badges:
            label = badge_labels.get(b, b)
            print_success(f"  [BADGE] {label}")

    print()
    print_divider()
    print_header("  DEBRIEF")
    print_divider()

    if debrief.get("summary"):
        print_info(f"\n{debrief['summary']}")

    if debrief.get("real_world"):
        print()
        print_header("  REAL-WORLD APPLICATION")
        print_info(debrief["real_world"])

    if debrief.get("next_step"):
        print()
        print_header("  NEXT STEPS")
        print_info(debrief["next_step"])

    if debrief.get("cert_link"):
        print()
        print_header("  CERT RELEVANCE")
        print_muted(debrief["cert_link"])

    if debrief.get("exam_tip"):
        print()
        print_header("  EXAM TIP")
        print_warning(debrief["exam_tip"])

    print()
    print_divider()
    print()
    input("Press Enter to return to the challenge menu...")


def _display_learn(challenge_data: dict) -> None:
    """Print the learn / reference section."""
    learn = challenge_data.get("learn", "No additional reference available.")
    print()
    print_divider()
    print_header("  LEARN")
    print_divider()
    print_info(learn)
    print()


def _display_run_result(
    passed: bool,
    stdout: str,
    stderr: str,
    error_msg: str | None,
    diff_lines: list,
    expected_output: str,
    case_description: str = "",
) -> None:
    """Print the result of a single run attempt."""
    label = f" [{case_description}]" if case_description else ""

    if error_msg:
        print_error(f"\n[ERROR]{label} {error_msg}")
        if stderr:
            print_error("--- stderr ---")
            print_error(stderr.strip())
        return

    if passed:
        print_success(f"\n[PASS]{label} Output matches expected!")
        return

    print_error(f"\n[FAIL]{label} Output does not match expected.")

    if stderr.strip():
        print_error("--- error output ---")
        print_error(stderr.strip())

    if stdout.strip():
        print_muted("--- your output ---")
        print_muted(stdout.strip())

    if diff_lines:
        print_warning("--- diff ---")
        for line in diff_lines:
            print_warning(line)

    print()
    print_muted("--- expected ---")
    for line in normalize_output(expected_output):
        print_muted(f"  {line}")
    print()


# ---------------------------------------------------------------------------
# Multi-test-case runner
# ---------------------------------------------------------------------------

def _run_all_test_cases(workspace: str, test_cases: list) -> tuple:
    """Run solution.py against each test case in order.

    Args:
        workspace: Absolute path to workspace.
        test_cases: List of {description, args, fixtures, expected_output} dicts.

    Returns:
        (all_passed: bool, results: list of (passed, case))
    """
    results = []
    all_passed = True

    for case in test_cases:
        desc = case.get("description", "")
        args = case.get("args", [])
        extra_fixtures = case.get("fixtures", [])
        expected = case.get("expected_output", "")

        # Copy any per-case fixtures
        for fname in extra_fixtures:
            _copy_fixture(fname, workspace)

        stdout, stderr, error_msg = _run_solution(workspace, args=args)

        if error_msg:
            passed = False
            _display_run_result(False, stdout, stderr, error_msg, [], expected, desc)
        else:
            passed, diff = validate_output(stdout, expected)
            _display_run_result(passed, stdout, stderr, None, diff, expected, desc)

        results.append((passed, case))
        if not passed:
            all_passed = False

    return all_passed, results


# ---------------------------------------------------------------------------
# Elapsed time helper
# ---------------------------------------------------------------------------

def _elapsed_str(start: datetime) -> str:
    secs = int((datetime.now(timezone.utc) - start).total_seconds())
    return f"{secs // 60}m{secs % 60:02d}s"


# ---------------------------------------------------------------------------
# Main challenge loop
# ---------------------------------------------------------------------------

def run_challenge(challenge_id: str, challenge_data: dict, save_data: dict,
                  timed_mode: bool = False) -> dict:
    """Run a single lab challenge session.

    Sets up the workspace, enters the command loop, handles hints,
    runs the solution, validates output, and awards XP/badges on success.

    Args:
        challenge_id: e.g. "lab06"
        challenge_data: Loaded challenge JSON dict.
        save_data: The player's current save dict (mutated in place).
        timed_mode: If True, elapsed time is shown at the prompt.

    Returns:
        Updated save_data dict.
    """
    workspace = _setup_workspace(challenge_data)

    # Initialise per-challenge metrics
    metrics = save_data.setdefault("metrics", {})
    metrics.setdefault(challenge_id, {
        "attempts": 0,
        "time_spent_seconds": 0,
        "hints_used": 0,
        "completed": False,
        "best_time_seconds": 0,
    })

    hints_used_this_session = 0
    all_hints = challenge_data.get("hints", [])
    xp_base = challenge_data.get("xp_base", 100)
    expected_output = challenge_data.get("expected_output", "")
    test_cases = challenge_data.get("test_cases")  # None = single-case mode
    already_complete = challenge_id in save_data.get("completed", [])

    # Background server(s)
    stop_events = []
    test_server_port = challenge_data.get("test_server_port")
    if test_server_port:
        # lab05: plain accept-and-close server
        # lab12: banner-sending server
        banner = challenge_data.get("test_server_banner")
        stop_events.append(_start_test_server(test_server_port, banner=banner))

    start_time = datetime.now(timezone.utc)

    _display_intro(challenge_data, timed_mode=timed_mode)

    if already_complete:
        print_success("[Already completed — practising in free-run mode]")
        print_muted("XP and badges will not be re-awarded.\n")

    try:
        while True:
            # Build prompt: show timer in timed mode
            if timed_mode:
                prompt = f"lab [{_elapsed_str(start_time)}]> "
            else:
                prompt = "lab> "

            try:
                raw = input(prompt).strip()
            except (EOFError, KeyboardInterrupt):
                raw = "quit"

            cmd = normalize_input(raw)

            # ----------------------------------------------------------------
            if cmd == "run":
                metrics[challenge_id]["attempts"] += 1
                print_muted("\nRunning solution.py ...")

                if test_cases:
                    # Multi-test-case mode
                    all_passed, results = _run_all_test_cases(workspace, test_cases)
                    n_pass = sum(1 for p, _ in results if p)
                    n_total = len(results)
                    print()
                    if all_passed:
                        print_success(f"[ALL TESTS PASSED] {n_pass}/{n_total}")
                    else:
                        print_error(f"[{n_pass}/{n_total} tests passed]")
                    passed = all_passed
                else:
                    # Single test-case mode
                    stdout, stderr, error_msg = _run_solution(workspace)
                    passed, diff = validate_output(stdout, expected_output)
                    _display_run_result(passed, stdout, stderr, error_msg, diff,
                                        expected_output)

                if passed and not already_complete:
                    elapsed = int(
                        (datetime.now(timezone.utc) - start_time).total_seconds()
                    )
                    metrics[challenge_id]["time_spent_seconds"] += elapsed
                    metrics[challenge_id]["completed"] = True

                    # Best time tracking
                    prev_best = metrics[challenge_id].get("best_time_seconds", 0)
                    if prev_best == 0 or elapsed < prev_best:
                        metrics[challenge_id]["best_time_seconds"] = elapsed

                    # Hints
                    prev_hints = save_data.get("hints_used", {}).get(challenge_id, 0)
                    total_hints = prev_hints + hints_used_this_session
                    save_data.setdefault("hints_used", {})[challenge_id] = total_hints
                    metrics[challenge_id]["hints_used"] = total_hints

                    # XP
                    xp_earned = calculate_xp(xp_base, total_hints)
                    save_data["xp"] = save_data.get("xp", 0) + xp_earned

                    # Mark complete
                    if challenge_id not in save_data.get("completed", []):
                        save_data.setdefault("completed", []).append(challenge_id)

                    # Badges
                    new_badges = evaluate_badges(save_data, total_hints)
                    save_data["badges"].extend(new_badges)

                    # Replay: save solution source
                    solution_path = os.path.join(workspace, _SOLUTION_FILE)
                    try:
                        with open(solution_path, "r", encoding="utf-8") as fh:
                            save_data.setdefault("solutions", {})[challenge_id] = fh.read()
                    except OSError:
                        pass

                    write_save(save_data)
                    _display_debrief(challenge_data, xp_earned, new_badges, elapsed)
                    break

                elif passed and already_complete:
                    print_success("\n[PASS] Great practice! Type 'quit' to exit.\n")

            # ----------------------------------------------------------------
            elif cmd == "hint":
                if hints_used_this_session >= len(all_hints):
                    print_warning("No more hints available.")
                else:
                    _display_hint(
                        challenge_data,
                        hint_index=hints_used_this_session,
                        hints_used=hints_used_this_session + 1,
                    )
                    hints_used_this_session += 1

            # ----------------------------------------------------------------
            elif cmd == "learn":
                _display_learn(challenge_data)

            # ----------------------------------------------------------------
            elif cmd == "reset":
                confirm = input("Reset solution.py to starter code? (y/n): ").strip().lower()
                if confirm == "y":
                    _reset_starter(challenge_data)
                    print_success("solution.py reset to starter code.")
                print()

            # ----------------------------------------------------------------
            elif cmd == "status":
                completed = save_data.get("completed", [])
                xp = save_data.get("xp", 0)
                elapsed = int(
                    (datetime.now(timezone.utc) - start_time).total_seconds()
                )
                print()
                print_header(f"  XP: {xp}")
                status_label = "complete" if already_complete else "in progress"
                print_info(f"  This challenge: {challenge_id} [{status_label}]")
                print_muted(f"  Challenges completed: {len(completed)}/15")
                print_muted(f"  Hints used this session: {hints_used_this_session}")
                print_muted(f"  Time this session: {elapsed // 60}m {elapsed % 60}s")
                print()

            # ----------------------------------------------------------------
            elif cmd in ("quit", "exit", "q"):
                elapsed = int(
                    (datetime.now(timezone.utc) - start_time).total_seconds()
                )
                metrics[challenge_id]["time_spent_seconds"] += elapsed
                write_save(save_data)

                print()
                confirm = input("Exit challenge? Progress is saved. (y/n): ").strip().lower()
                if confirm == "y":
                    break
                # Reset timer after cancelled quit
                metrics[challenge_id]["time_spent_seconds"] -= elapsed
                start_time = datetime.now(timezone.utc)

            # ----------------------------------------------------------------
            else:
                print_muted("Commands: run | hint | learn | status | reset | quit")

    finally:
        for stop_event in stop_events:
            stop_event.set()

    return save_data


# ---------------------------------------------------------------------------
# Challenge loader
# ---------------------------------------------------------------------------

def load_challenge(challenge_id: str) -> dict | None:
    """Load a challenge JSON by ID. Returns None if not found or invalid."""
    path = os.path.join(_CONTENT_DIR, "challenges", f"{challenge_id}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data
    except (json.JSONDecodeError, OSError):
        return None


def load_registry() -> dict:
    """Load the challenge registry. Returns the full registry dict."""
    path = os.path.join(_CONTENT_DIR, "registry.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {"stages": [], "challenges": []}
