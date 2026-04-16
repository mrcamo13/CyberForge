"""player.py — AEGIS CyberForge

XP calculation and badge evaluation for the AEGIS Blue Team game.
"""

# ---------------------------------------------------------------------------
# Badge definitions (id -> human-readable label)
# ---------------------------------------------------------------------------
_BADGE_LABELS: dict = {
    "first_blood":  "First Blood      -- completed your first case",
    "no_hints":     "No Hints         -- solved a case without using any hints",
    "hint_free_5":  "Ghost Protocol   -- 5 cases solved without any hints",
    "halfway":      "Halfway There    -- 16 cases complete",
    "iron_analyst": "Iron Analyst     -- all 31 cases complete",
    "xp_1000":      "XP-1000          -- accumulated 1,000 XP",
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


def calculate_xp(xp_base: int, hints_used: int) -> int:
    """Calculate XP earned for completing a case.

    Args:
        xp_base: The base XP value defined in the case JSON.
        hints_used: Number of hints the player used (0-4).

    Returns:
        Integer XP earned after applying the hint penalty multiplier.
    """
    multiplier = _XP_MULTIPLIERS.get(hints_used, 0.10)
    return int(xp_base * multiplier)


def evaluate_badges(
    save_data: dict,
    just_completed_id: str = "",
    hints_used_this_run: int = 0,
) -> list:
    """Evaluate which badges the player has newly earned.

    Checks are performed AFTER the completed case has been appended to
    save_data["completed"]. Never awards a badge already in save_data["badges"].

    Stage 1 badges:
        first_blood — player has completed at least 1 case
        no_hints    — the just-completed case used 0 hints

    Args:
        save_data: The current save dictionary.
        just_completed_id: The case ID that was just completed.
        hints_used_this_run: Hints used during this completion run.

    Returns:
        List of newly earned badge ID strings (may be empty).
    """
    already_earned: list = save_data.get("badges", [])
    new_badges: list = []

    # first_blood: earned on the very first case completion
    if "first_blood" not in already_earned:
        if len(save_data.get("completed", [])) >= 1:
            new_badges.append("first_blood")

    # no_hints: earned when the just-completed case used zero hints
    if "no_hints" not in already_earned and just_completed_id:
        if hints_used_this_run == 0:
            new_badges.append("no_hints")

    # hint_free_5: 5+ completed cases each solved with 0 hints
    if "hint_free_5" not in already_earned:
        hint_free_count = sum(
            1 for cid in save_data.get("completed", [])
            if save_data.get("hints_used", {}).get(cid, 0) == 0
        )
        if hint_free_count >= 5:
            new_badges.append("hint_free_5")

    # halfway: 16+ cases complete
    if "halfway" not in already_earned:
        if len(save_data.get("completed", [])) >= 16:
            new_badges.append("halfway")

    # iron_analyst: all 31 cases complete
    if "iron_analyst" not in already_earned:
        if len(save_data.get("completed", [])) >= 31:
            new_badges.append("iron_analyst")

    # xp_1000: 1,000+ XP accumulated (XP already updated before this call)
    if "xp_1000" not in already_earned:
        if save_data.get("xp", 0) >= 1000:
            new_badges.append("xp_1000")

    return new_badges
