"""terminal.py — AEGIS CyberForge

ANSI color helpers, print functions, and input normalization.
All ANSI codes are defined as module-level constants.
No raw print() with ANSI codes anywhere else in the codebase.
"""

import os
import re

# ---------------------------------------------------------------------------
# ANSI color constants
# ---------------------------------------------------------------------------
_RESET = "\033[0m"
_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_WHITE = "\033[97m"
_DARK_GRAY = "\033[90m"
_CYAN = "\033[96m"

_DIVIDER_CHAR = "-"
_DIVIDER_WIDTH = 60


# ---------------------------------------------------------------------------
# Print helpers
# ---------------------------------------------------------------------------

def print_success(msg: str) -> None:
    """Print message in green (correct answers, completions)."""
    print(f"{_GREEN}{msg}{_RESET}")


def print_error(msg: str) -> None:
    """Print message in red (wrong answers, failures)."""
    print(f"{_RED}{msg}{_RESET}")


def print_warning(msg: str) -> None:
    """Print message in yellow (hints, alerts, cautions)."""
    print(f"{_YELLOW}{msg}{_RESET}")


def print_info(msg: str) -> None:
    """Print message in white (body text, descriptions)."""
    print(f"{_WHITE}{msg}{_RESET}")


def print_muted(msg: str) -> None:
    """Print message in dark gray (timestamps, secondary info)."""
    print(f"{_DARK_GRAY}{msg}{_RESET}")


def print_header(msg: str) -> None:
    """Print message in cyan (titles, section headers, prompts)."""
    print(f"{_CYAN}{msg}{_RESET}")


def print_divider() -> None:
    """Print a horizontal rule for section separation."""
    print(_DIVIDER_CHAR * _DIVIDER_WIDTH)


def clear_screen() -> None:
    """Clear the terminal. Cross-platform."""
    os.system("cls" if os.name == "nt" else "clear")


# ---------------------------------------------------------------------------
# Input normalization
# ---------------------------------------------------------------------------

def normalize_input(raw: str) -> str:
    """Normalize player input before answer comparison.

    Strips whitespace, lowercases, collapses internal spaces,
    and removes punctuation players commonly add or omit.
    Preserves forward slashes (for path answers like /admin/dashboard).
    """
    normalized = raw.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"[^\w\s\.\-\/]", "", normalized)
    return normalized


def check_answer(player_input: str, valid_answers: list) -> bool:
    """Check normalized player input against all valid answer variants."""
    normalized = normalize_input(player_input)
    return normalized in [normalize_input(a) for a in valid_answers]
