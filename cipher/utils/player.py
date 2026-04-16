"""player.py — CIPHER CyberForge

XP calculation and badge evaluation utilities.
All game state lives in the save file — no module-level globals.
"""


# ---------------------------------------------------------------------------
# XP
# ---------------------------------------------------------------------------

_XP_MULTIPLIERS: dict = {0: 1.0, 1: 0.75, 2: 0.50, 3: 0.25, 4: 0.10}


def calculate_xp(xp_base: int, hints_used: int) -> int:
    """Calculate XP awarded based on hints used during completion.

    Uses multipliers defined in DATA_MODEL.md §3.
    Returns int(xp_base * multiplier). Defaults to 0.10 for >4 hints.
    """
    multiplier = _XP_MULTIPLIERS.get(hints_used, 0.10)
    return int(xp_base * multiplier)


# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------

# Stage 1 only evaluates badges achievable with one operation.
_STAGE1_BADGES = ("first_blood", "no_hints")


def evaluate_badges(save_data: dict) -> list:
    """Evaluate and return newly earned badge IDs not already in save.

    Stage 1 checks only:
      - first_blood: player has at least 1 completion
      - no_hints: most recent completion had hints_used = 0

    Never awards a badge that is already in save_data['badges'].
    Returns list of newly earned badge ID strings.
    """
    earned = save_data.get("badges", [])
    new_badges: list = []
    completed = save_data.get("completed", [])

    # first_blood — first completion ever
    if "first_blood" not in earned and len(completed) >= 1:
        new_badges.append("first_blood")

    # no_hints — most recent completion had 0 hints used
    if "no_hints" not in earned and len(completed) >= 1:
        last_op = completed[-1]
        hints_for_last = save_data.get("hints_used", {}).get(last_op, 0)
        if hints_for_last == 0:
            new_badges.append("no_hints")

    return new_badges
