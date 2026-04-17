"""player.py — LAB CyberForge (Script Lab)

XP calculation and badge evaluation for the Script Lab simulator.
Simpler than AEGIS/CIPHER — 5 challenges, 4 badges.
"""

# ---------------------------------------------------------------------------
# Badge definitions (id -> human-readable label)
# ---------------------------------------------------------------------------
_BADGE_LABELS: dict = {
    "first_solve":   "First Solve      -- completed your first lab challenge",
    "no_hints":      "Clean Run        -- solved a challenge without any hints",
    "hint_free_3":   "Ghost Coder      -- 3 challenges solved without hints",
    "all_complete":  "Lab Graduate     -- all 5 challenges complete",
}

# ---------------------------------------------------------------------------
# XP multipliers by hint count
# ---------------------------------------------------------------------------
_XP_MULTIPLIERS: dict = {
    0: 1.0,
    1: 0.75,
    2: 0.50,
    3: 0.25,
    4: 0.10,
}


def get_badge_labels() -> dict:
    """Return the badge label dictionary (used by stats screen)."""
    return dict(_BADGE_LABELS)


def calculate_xp(xp_base: int, hints_used: int) -> int:
    """Calculate XP earned for completing a challenge.

    Args:
        xp_base: The base XP value defined in the challenge JSON.
        hints_used: Number of hints the player used (0-4).

    Returns:
        Integer XP earned after applying the hint penalty multiplier.
    """
    multiplier = _XP_MULTIPLIERS.get(hints_used, 0.10)
    return int(xp_base * multiplier)


def evaluate_badges(
    save_data: dict,
    hints_used_this_run: int = 0,
) -> list:
    """Evaluate which badges the player has newly earned.

    Must be called AFTER the completed challenge has been appended to
    save_data["completed"]. Never awards a badge already in save_data["badges"].

    Badges:
        first_solve  -- player has completed at least 1 challenge
        no_hints     -- the just-completed challenge used 0 hints
        hint_free_3  -- 3+ completed challenges each solved with 0 hints
        all_complete -- all 5 challenges complete

    Args:
        save_data: The current save dictionary.
        hints_used_this_run: Hints used during this completion run.

    Returns:
        List of newly earned badge ID strings (may be empty).
    """
    already_earned: list = save_data.get("badges", [])
    new_badges: list = []

    # first_solve: earned on the very first challenge completion
    if "first_solve" not in already_earned:
        if len(save_data.get("completed", [])) >= 1:
            new_badges.append("first_solve")

    # no_hints: earned when the just-completed challenge used zero hints
    if "no_hints" not in already_earned:
        if hints_used_this_run == 0:
            new_badges.append("no_hints")

    # hint_free_3: 3+ challenges each solved with 0 hints
    if "hint_free_3" not in already_earned:
        hint_free_count = sum(
            1 for cid in save_data.get("completed", [])
            if save_data.get("hints_used", {}).get(cid, 0) == 0
        )
        if hint_free_count >= 3:
            new_badges.append("hint_free_3")

    # all_complete: all 5 challenges done
    if "all_complete" not in already_earned:
        if len(save_data.get("completed", [])) >= 5:
            new_badges.append("all_complete")

    return new_badges
