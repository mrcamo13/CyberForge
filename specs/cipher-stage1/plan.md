# plan.md — CIPHER Stage 1: Core Engine + Operation 01
<!--
GENERATED from specs/cipher-stage1/spec.md
Process: spec.md loaded → plan generated. Max 5 phases.
-->

**Source spec:** `specs/cipher-stage1/spec.md`
**Date:** 2026-04-09
**Status:** ✅ Approved

---

## Phase 1: Utilities & Infrastructure

**Goal:** All shared utility modules exist, are tested, and importable.
Nothing else can be built without these.
**Estimated time:** 3 hours

1. Create folder structure:
   `cipher/utils/`, `cipher/engine/`, `cipher/content/operations/`,
   `cipher/saves/`, `cipher/tests/`
2. Build `utils/terminal.py`:
   - 8 print functions: `print_success`, `print_error`, `print_warning`,
     `print_info`, `print_muted`, `print_header`, `print_divider`,
     `clear_screen`
   - `normalize_input(raw: str) -> str`
3. Build `utils/player.py`:
   - `calculate_xp(xp_base: int, hints_used: int) -> int`
   - `evaluate_badges(save_data: dict) -> list` — Stage 1 evaluates
     `first_blood` and `no_hints` only
4. Build `utils/save_manager.py`:
   - `create_save(player_name, track) -> dict`
   - `load_save(player_name) -> dict`
   - `write_save(save_data) -> None` — atomic write via .tmp file
   - `load_with_fallback(player_name) -> dict` — primary → backup → new
   - `migrate_save(save_data) -> dict` — adds missing fields, never deletes
   - `list_saves() -> list`
5. Build `utils/tools.py`:
   - `run_tool(tools_type: str, challenge_text: str) -> str`
   - `caesar_decoder(text: str) -> str` — returns all 26 shifts formatted
6. Build `check_imports.py` — scans engine/ and utils/ against stdlib allowlist

**Gate:** `python -m unittest discover tests/` passes for save_manager
(save + load round-trip) and player (XP calculation for all hint tiers).
`check_imports.py` exits 0 on utils/ files.

---

## Phase 2: Content Layer

**Goal:** All JSON content files exist and pass schema validation.
**Estimated time:** 2 hours

1. Create `content/operations/op01.json` with full Caesar Cipher content
   from spec §9 — scenario, challenge, valid_answers, hints (4),
   learn, tools_type, debrief (all fields)
2. Create `content/placement_test.json` with all 5 questions from spec §9
   using the defined schema (id, question, options[4], correct_index)
3. Create `content/registry.json` with op01 registered as active
4. Build `validate_content.py`:
   - Validate op01.json against required field schema
   - Validate placement_test.json (pass_threshold ≤ questions count,
     correct_index 0-3, exactly 4 options per question)
   - Validate registry.json (all registered IDs have matching files)
   - Generate SHA-256 checksums → write `content/checksums.json`
   - Exit code 0 = all pass, exit code 1 = failures with field-level output

**Gate:** `python validate_content.py` exits 0. Output shows
`[PASS] op01.json`, `[PASS] placement_test.json`, `[PASS] registry.json`.
`content/checksums.json` is generated.

---

## Phase 3: Operation Engine

**Goal:** A player can run op01 end-to-end from the command line
without the main menu. All 9 commands work. Save is written correctly.
**Estimated time:** 3 hours

1. Build `engine/operation_runner.py`:
   - `load_operation(op_id: str) -> dict` — reads JSON from content/
   - `run_operation(op_id: str, save_data: dict) -> dict` — returns
     updated save_data on exit
   - Command loop implementing strict priority:
     - Step 1: exact command match (help, learn, tools, hint, notes,
       skip, menu, quit)
     - Step 2: argument command (`note [text]`)
     - Step 3: answer fallback → normalize → check valid_answers
   - Wrong answer: print_error("Incorrect. Try again, or type 'hint'.")
     → return to prompt. Never show help.
   - `hint` reveals next unrevealed tier (1→2→3→4). Beyond 4:
     print_warning("No more hints. Try 'tools'.")
   - On correct answer: calculate_xp → award XP → update save →
     evaluate badges → display debrief → return save_data
   - Metrics: start timer on entry, stop on completion or skip,
     increment attempts on wrong answer, set hints_maxed at 4
   - Ctrl+C → save progress → return save_data with in_progress set

**Gate:** Running `python -c "from engine.operation_runner import
run_operation"` imports cleanly. Manual test: all 9 commands produce
correct output. Correct answer triggers debrief and XP award.
Wrong answer shows feedback and returns to prompt. Save file written
correctly after quit.

---

## Phase 4: Main Menu & Full Navigation

**Goal:** `python main.py` delivers the complete player experience
from launch to quit, including all menu flows.
**Estimated time:** 3 hours

1. Build `main.py` with:
   - `--dev` flag detection via `sys.argv` — bypasses checksum verification
   - Startup validation: load registry.json, verify checksums (prod mode)
   - ASCII CIPHER logo display
   - Main menu loop: New Game (1) / Load Game (2) / Placement Test (3) /
     Quit (4)
2. Implement New Game flow:
   - Name prompt with validation (alphanumeric + underscore, max 20,
     non-empty, no existing save conflict)
   - Track selection: Red Team (1) / Full Stack (2)
   - Blue Team input → display redirect constant → re-prompt
   - Create save → write → navigate to operation menu
3. Implement Load Game flow:
   - List save files with last_played date
   - No saves found → "No save files found." → redirect to New Game
   - Select save → load with fallback → navigate to operation menu
4. Implement Placement Test flow:
   - Load placement_test.json
   - Display questions one at a time (1-4 input only)
   - Ctrl+C → discard, set taken=false, return to main menu
   - Display result screen (score, per-question feedback, pass/fail,
     XP if passed)
   - Save result → navigate to operation menu
5. Implement Operation Menu:
   - Build from registry.json + save_data (completed, skipped)
   - Status icons: ✅ Complete | ▶ In Progress | ⏭ Skipped | 🔒 Locked
   - Locked operation selected → "Complete the previous operation first."
   - Completed operation selected → replay prompt (y/n)
   - Active/skipped → launch via operation_runner.run_operation()

**Gate:** Full end-to-end walkthrough passes:
- Launch → New Game → name → Red Team → Operation Menu → op01 →
  complete → debrief → Operation Menu → quit
- Relaunch → Load Game → select save → Operation Menu shows op01 ✅
- `python main.py --dev` bypasses checksum verification on launch

---

## Phase 5: Validation & Hardening

**Goal:** All 15 edge cases from spec §7 tested and handled.
All success criteria in spec §1 verified. Ready to merge.
**Estimated time:** 2 hours

1. Test all 15 edge cases from spec §7 manually — document pass/fail
2. Run `validate_content.py` — must exit 0
3. Run `check_imports.py` — must exit 0
4. Run `python -m unittest discover tests/` — all tests green
5. Test on at least 2 of: Windows / macOS / Linux
6. Verify save/backup/corruption flow:
   - Corrupt primary save → backup loads silently
   - Corrupt both → new save created with notification
7. Update `PROJECT_FOUNDATION.md` §Doc Registry — mark cipher-stage1 spec ✅
8. Update `docs/LESSONS_LEARNED.md` if any issues were hit during build
9. Set spec.md status → ✅ Complete

**Gate:** All success criteria in spec §1 are checked off. All 15 edge
cases pass. Both validation scripts exit 0. All unittest tests green.
`python main.py` launches cleanly on target OS.

---

## Dependencies

```
Phase 1 (Utils) → Phase 2 (Content) → Phase 3 (Engine)
                                             ↓
                                       Phase 4 (Menu)
                                             ↓
                                       Phase 5 (Validate)
```

Phase 2 can begin as soon as Phase 1 utils are importable.
Phase 3 requires Phase 1 (utils) and Phase 2 (content files).
Phase 4 requires Phase 1, 2, and 3 complete.
Phase 5 requires all prior phases complete.

---

## Cost Estimate

| Phase | Dev Time | API Cost |
|-------|---------|---------|
| Phase 1 | ~3 hours | $0 |
| Phase 2 | ~2 hours | $0 |
| Phase 3 | ~3 hours | $0 |
| Phase 4 | ~3 hours | $0 |
| Phase 5 | ~2 hours | $0 |
| **Total** | **~13 hours** | **$0** |
