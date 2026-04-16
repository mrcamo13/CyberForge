# tasks.md — CIPHER Stage 1: Core Engine + Operation 01
<!--
GENERATED from specs/cipher-stage1/plan.md
Each task: <30 min | "done when" verifiable in <1 min | one commit
-->

**Source plan:** `specs/cipher-stage1/plan.md`
**Date:** 2026-04-09
**Total tasks:** 18

---

## Phase 1: Utilities & Infrastructure

### TASK-01: Create folder structure
- **Files:** `cipher/utils/.gitkeep`, `cipher/engine/.gitkeep`,
  `cipher/content/operations/.gitkeep`, `cipher/saves/.gitkeep`,
  `cipher/tests/.gitkeep`
- **Depends on:** None
- **Done when:** All 5 directories exist under `cipher/`
- **Prompt for coding LLM:**
  ```
  Read CONSTITUTION.md and specs/cipher-stage1/spec.md §10 file structure.
  Create the following empty directories inside cipher/:
  utils/, engine/, content/operations/, saves/, tests/
  Add a .gitkeep file to each so they are tracked by git.
  Do not create any Python files yet.
  ```

---

### TASK-02: Build utils/terminal.py
- **Files:** `cipher/utils/terminal.py`
- **Depends on:** TASK-01
- **Done when:** `python -c "from utils.terminal import print_success,
  print_error, print_warning, print_info, print_muted, print_header,
  print_divider, clear_screen, normalize_input"` runs with no errors
- **Prompt for coding LLM:**
  ```
  Read CONSTITUTION.md §4 (normalize_input function + ANSI color rules)
  and specs/cipher-stage1/spec.md §5 (Standard terminal.py Functions).
  Build cipher/utils/terminal.py with exactly these functions:
  - print_success(msg: str) -> None      — green
  - print_error(msg: str) -> None        — red
  - print_warning(msg: str) -> None      — yellow
  - print_info(msg: str) -> None         — white
  - print_muted(msg: str) -> None        — dark gray
  - print_header(msg: str) -> None       — cyan
  - print_divider() -> None              — prints a line of dashes
  - clear_screen() -> None               — cross-platform
  - normalize_input(raw: str) -> str     — strip, lowercase, collapse
    spaces, remove non-word punctuation (see CONSTITUTION.md §4)
  All ANSI codes must be defined as module-level constants, not inline.
  Type hints and docstrings required on every function.
  stdlib only — no imports outside the allowlist.
  ```

---

### TASK-03: Build utils/player.py
- **Files:** `cipher/utils/player.py`
- **Depends on:** TASK-02
- **Done when:** `python -c "from utils.player import calculate_xp,
  evaluate_badges; print(calculate_xp(100, 0))"` prints `100`
- **Prompt for coding LLM:**
  ```
  Read CONSTITUTION.md §4, docs/DATA_MODEL.md §3 (XP system) and §4
  (badge system), and specs/cipher-stage1/spec.md §3 rule 6.
  Build cipher/utils/player.py with:
  - calculate_xp(xp_base: int, hints_used: int) -> int
    Use multipliers: {0:1.0, 1:0.75, 2:0.50, 3:0.25, 4:0.10}
    Return int(xp_base * multiplier)
  - evaluate_badges(save_data: dict) -> list
    Stage 1 checks ONLY: first_blood (completed list has 1+ entries)
    and no_hints (most recent completion had hints_used = 0).
    Returns list of newly earned badge ID strings not already in
    save_data["badges"]. Never awards a badge twice.
  Type hints and docstrings required. stdlib only.
  ```

---

### TASK-04: Build utils/save_manager.py
- **Files:** `cipher/utils/save_manager.py`
- **Depends on:** TASK-02
- **Done when:** `python -m unittest tests/test_save_manager.py` passes
  (save → load round-trip returns identical data)
- **Prompt for coding LLM:**
  ```
  Read CONSTITUTION.md §3 rules 10-13, docs/DATA_MODEL.md §1 (full
  save file schema and field rules), and specs/cipher-stage1/spec.md
  §3 rule 5, §5 (atomic save pattern), §7 edge cases 1-2, 9-10, 13-14.
  Build cipher/utils/save_manager.py with:
  - create_save(player_name: str, track: str) -> dict
    Returns new save dict with all fields from DATA_MODEL.md §1 schema.
    Creates saves/ directory if missing.
  - write_save(save_data: dict) -> None
    Atomic write: write to [name].tmp.json → verify JSON parses →
    rename to [name].json → write backup to [name].backup.json.
  - load_save(player_name: str) -> dict
    Validate schema on load. If corrupted: rename to .corrupted.json,
    notify, return None.
  - load_with_fallback(player_name: str) -> dict
    Try primary → try backup → create new save.
  - migrate_save(save_data: dict) -> dict
    Add missing fields with defaults. Never delete existing data.
  - list_saves() -> list
    Returns list of dicts: [{name, last_played}] sorted by last_played.
  Also create cipher/tests/test_save_manager.py with:
  - test_save_load_roundtrip: create → write → load → assert equal
  - test_atomic_write: write succeeds, .tmp file removed after
  - test_corrupted_primary_loads_backup
  Type hints and docstrings required. Use os.path.join() for all paths.
  ```

---

### TASK-05: Build utils/tools.py
- **Files:** `cipher/utils/tools.py`
- **Depends on:** TASK-02
- **Done when:** `python -c "from utils.tools import run_tool;
  print(run_tool('caesar_decoder', 'QHAXVFRUS'))"` prints all 26 shifts
  with shift 3 showing NEXUSCORP
- **Prompt for coding LLM:**
  ```
  Read CONSTITUTION.md §4, docs/DATA_MODEL.md §2 (tools_type allowlist),
  and specs/cipher-stage1/spec.md §9 (Tools Output format).
  Build cipher/utils/tools.py with:
  - run_tool(tools_type: str, challenge_text: str) -> str
    Dispatches to the correct tool function by tools_type string.
    If tools_type not recognized: return "Unknown tool type."
  - caesar_decoder(text: str) -> str
    Tries all 26 shifts on uppercase input.
    Returns formatted string — one line per shift:
    "Shift 01: RESULT" with a  ← marker on the shift that
    produces a recognizable result (all alpha, no numbers).
    Handles uppercase only — preserves spaces and non-alpha chars.
  Type hints and docstrings required. stdlib only.
  ```

---

### TASK-06: Build check_imports.py
- **Files:** `cipher/check_imports.py`
- **Depends on:** TASK-01
- **Done when:** `python check_imports.py` exits 0 and prints
  `[PASS]` for all files in utils/
- **Prompt for coding LLM:**
  ```
  Read CONSTITUTION.md §4 (stdlib allowlist).
  Build cipher/check_imports.py that:
  - Scans all .py files in engine/ and utils/ recursively
  - Parses import statements (import X and from X import Y)
  - Checks each top-level module name against the stdlib allowlist:
    os, sys, json, re, datetime, pathlib, unittest, hashlib,
    base64, collections, itertools, functools, string, time,
    random, math, copy, io, textwrap
  - Prints [PASS] filename or [FAIL] filename — unauthorized: module_name
  - Exits 0 if all pass, exits 1 if any fail
  Type hints and docstrings required.
  ```

---

## Phase 2: Content Layer

### TASK-07: Create op01.json
- **Files:** `cipher/content/operations/op01.json`
- **Depends on:** TASK-01
- **Done when:** File exists and `python -c "import json;
  json.load(open('content/operations/op01.json'))"` runs without error
- **Prompt for coding LLM:**
  ```
  Read docs/DATA_MODEL.md §2 (full JSON content schema including
  tools_type allowlist) and specs/cipher-stage1/spec.md §9
  (Operation 01 full content — narrative, challenge, valid_answers,
  hints, learn, tools_type, debrief).
  Create cipher/content/operations/op01.json with ALL fields from
  the schema populated using the exact content defined in the spec.
  difficulty: 1, xp_base: 100, tools_type: "caesar_decoder"
  valid_answers must be a list: ["nexuscorp"]
  hints must be exactly 4 items in the correct escalation order.
  debrief must include all required subfields.
  ```

---

### TASK-08: Create placement_test.json
- **Files:** `cipher/content/placement_test.json`
- **Depends on:** TASK-01
- **Done when:** File exists and parses as valid JSON with 5 questions
- **Prompt for coding LLM:**
  ```
  Read specs/cipher-stage1/spec.md §9 (Placement Test — schema and
  all 5 questions with correct answers).
  Create cipher/content/placement_test.json using the schema:
  {
    "pass_threshold": 4,
    "xp_on_pass": 50,
    "questions": [
      {
        "id": "pt01",
        "question": "...",
        "options": ["A", "B", "C", "D"],
        "correct_index": N
      }
    ]
  }
  Populate all 5 questions exactly as defined in spec §9.
  correct_index is 0-based (player selects 1-4, engine maps to 0-3).
  ```

---

### TASK-09: Create registry.json
- **Files:** `cipher/content/registry.json`
- **Depends on:** TASK-07
- **Done when:** File exists, parses as valid JSON, contains op01
  with status "active"
- **Prompt for coding LLM:**
  ```
  Read docs/DATA_MODEL.md §5 (registry.json full schema and required
  fields per entry).
  Create cipher/content/registry.json registering op01:
  - id: "op01"
  - title: "Caesar Cipher"
  - status: "active"
  - difficulty: 1
  - cert_objective: "PenTest+ PT0-003 Domain 2 — Reconnaissance"
  Include version field: "1.0"
  cases array should be present but empty (AEGIS content not in scope).
  ```

---

### TASK-10: Build validate_content.py
- **Files:** `cipher/validate_content.py`
- **Depends on:** TASK-07, TASK-08, TASK-09
- **Done when:** `python validate_content.py` exits 0 and prints
  [PASS] for op01.json, placement_test.json, and registry.json.
  `content/checksums.json` is created.
- **Prompt for coding LLM:**
  ```
  Read docs/DATA_MODEL.md §2 (required fields table for CIPHER ops
  including tools_type and difficulty), §5 (registry required fields),
  specs/cipher-stage1/spec.md §5 (validate_content.py output format
  and exit codes) and §9 (placement_test.json validation rules).
  Build cipher/validate_content.py that:
  1. Validates content/operations/*.json — checks all required fields,
     hints is exactly 4 items, valid_answers is a non-empty list,
     difficulty is 1-4, tools_type is in the allowlist
  2. Validates content/placement_test.json — pass_threshold ≤ question
     count, each question has exactly 4 options, correct_index is 0-3
  3. Validates content/registry.json — all required fields present,
     every registered id has a matching JSON file in content/operations/
  4. Generates SHA-256 checksum for each validated file using hashlib
  5. Writes content/checksums.json: {"filename": "sha256hex", ...}
  6. Prints [PASS] or [FAIL] per file with specific failure reason
  7. Exits 0 if all pass, exits 1 if any fail
  Type hints and docstrings required. stdlib only.
  ```

---

## Phase 3: Operation Engine

### TASK-11: Build engine/operation_runner.py — load + display
- **Files:** `cipher/engine/operation_runner.py`
- **Depends on:** TASK-02, TASK-03, TASK-04, TASK-05, TASK-10
- **Done when:** `python -c "from engine.operation_runner import
  load_operation; print(load_operation('op01')['title'])"` prints
  `Caesar Cipher`
- **Prompt for coding LLM:**
  ```
  Read CONSTITUTION.md §3-4, specs/cipher-stage1/spec.md §5
  (Component Responsibility Map), and docs/DATA_MODEL.md §2.
  Build cipher/engine/operation_runner.py with:
  - load_operation(op_id: str) -> dict
    Loads and returns content/operations/{op_id}.json
    Raises FileNotFoundError with clear message if not found
  - display_intro(op_data: dict) -> None
    Clears screen, prints operation title as header,
    prints scenario text using print_info
    prints challenge using print_warning
    prints "Type 'help' to see available commands." using print_muted
  This task builds ONLY load and display. Command loop in TASK-12.
  Type hints and docstrings required. stdlib only.
  ```

---

### TASK-12: Build engine/operation_runner.py — command loop
- **Files:** `cipher/engine/operation_runner.py`
- **Depends on:** TASK-11
- **Done when:** Running an operation manually shows the prompt,
  accepts `help` and prints the command list, accepts `learn` and
  prints learn text, accepts `tools` and prints Caesar decoder output
- **Prompt for coding LLM:**
  ```
  Read CONSTITUTION.md §4 (command set and parsing priority),
  specs/cipher-stage1/spec.md §3 rules 1-2 and §6 (command loop
  diagram).
  Add run_operation(op_id: str, save_data: dict) -> dict to
  cipher/engine/operation_runner.py.
  Implement the command loop with strict 3-step priority:
  Step 1 — exact match (after normalize_input):
    help   → print all 9 commands using print_info
    learn  → print op_data["learn"] using print_info
    tools  → call run_tool(op_data["tools_type"], op_data["challenge"])
              print result using print_info
    notes  → print save_data["notes"].get(op_id, []) or "No notes yet."
    hint   → handled in TASK-13
    skip   → handled in TASK-13
    menu   → handled in TASK-13
    quit   → handled in TASK-13
  Step 2 — starts with "note ":
    save the text after "note " to save_data["notes"][op_id]
    print_success("Note saved.")
  Step 3 — answer fallback:
    normalize input → check against valid_answers list
    Wrong: print_error("Incorrect. Try again, or type 'hint'.")
    Correct: handled in TASK-14
  Wrap entire loop in try/except KeyboardInterrupt → save + return.
  ```

---

### TASK-13: Build engine/operation_runner.py — hints, skip, exit
- **Files:** `cipher/engine/operation_runner.py`
- **Depends on:** TASK-12
- **Done when:** `hint` reveals hints in order 1-4, 5th hint shows
  "No more hints", `skip` returns to caller, `menu` and `quit` save
  and return
- **Prompt for coding LLM:**
  ```
  Read specs/cipher-stage1/spec.md §3 rules 3-5, 14, §7 edge case 8,
  and docs/DATA_MODEL.md §1 (hints_used, metrics fields).
  Add to run_operation in cipher/engine/operation_runner.py:
  hint command:
    Read save_data["hints_used"].get(op_id, 0)
    If < 4: increment, print next hint from op_data["hints"][count-1]
            using print_warning, update save_data hints_used
            If now = 4: set save_data metrics hints_maxed = True
    If = 4: print_warning("No more hints available. Try 'tools'.")
  skip command:
    Add op_id to save_data["skipped"] if not already there
    Stop metrics timer, update time_spent_seconds
    Call write_save(save_data) via save_manager
    print_muted("Operation skipped.")
    Return save_data
  menu command:
    Call write_save(save_data) via save_manager
    Return save_data
  quit command:
    Call write_save(save_data) via save_manager
    print_muted("Progress saved. Goodbye.")
    sys.exit(0)
  ```

---

### TASK-14: Build engine/operation_runner.py — correct answer + debrief
- **Files:** `cipher/engine/operation_runner.py`
- **Depends on:** TASK-13
- **Done when:** Typing `nexuscorp` at the prompt awards XP, prints
  debrief, and returns save_data with op01 in completed list
- **Prompt for coding LLM:**
  ```
  Read specs/cipher-stage1/spec.md §3 rules 3, 5-6, §9 (debrief
  format), docs/DATA_MODEL.md §3 (XP calculation) and §4 (badges).
  Add correct answer handling to run_operation in
  cipher/engine/operation_runner.py:
  On correct answer:
    1. Stop metrics timer → update save_data metrics time_spent_seconds
    2. Get hints_used count from save_data
    3. Call calculate_xp(op_data["xp_base"], hints_used) → xp_earned
    4. save_data["xp"] += xp_earned
    5. save_data["completed"].append(op_id) if not already there
    6. save_data["metrics"][op_id]["completed"] = True
    7. new_badges = evaluate_badges(save_data)
    8. save_data["badges"].extend(new_badges)
    9. Call write_save(save_data)
    10. Display debrief:
        clear_screen()
        print_header("OPERATION COMPLETE")
        print_divider()
        print_success(f"XP AWARDED: {xp_earned}")
        if new_badges: print_success(f"Badge unlocked: {badge}")
        print_divider()
        print_info(op_data["debrief"]["summary"])
        print_info(op_data["debrief"]["real_world"])
        print_warning(op_data["debrief"]["next_step"])
        print_muted(op_data["debrief"]["cert_link"])
        print_divider()
        input("Press Enter to continue...")
    11. Return save_data
  ```

---

## Phase 4: Main Menu & Full Navigation

### TASK-15: Build main.py — startup + main menu
- **Files:** `cipher/main.py`
- **Depends on:** TASK-10, TASK-14
- **Done when:** `python main.py` shows ASCII CIPHER logo and 4-option
  menu. `python main.py --dev` skips checksum verification.
- **Prompt for coding LLM:**
  ```
  Read CONSTITUTION.md §4 (file structure), specs/cipher-stage1/spec.md
  §1 (--dev flag in scope), §5 (validate_content.py exit codes),
  §6 (main menu screen).
  Build cipher/main.py with:
  - Parse sys.argv for --dev flag
  - In production mode: run validate_content.py as subprocess,
    if exit code 1: print_error("Content validation failed.") + sys.exit(1)
    In --dev mode: skip validation, print_muted("[DEV MODE]")
  - Display ASCII CIPHER logo in cyan (design the logo — block letters
    or simple banner, your choice)
  - Print main menu:
    [1] New Game
    [2] Load Game
    [3] Placement Test
    [4] Quit
  - Input loop: accept 1-4, invalid input re-prompts
  - Route to: new_game(), load_game(), placement_test(), sys.exit(0)
  - Stub new_game(), load_game(), placement_test() as pass for now —
    implemented in TASK-16 and TASK-17
  Type hints and docstrings required. stdlib only.
  ```

---

### TASK-16: Build main.py — New Game + Load Game flows
- **Files:** `cipher/main.py`
- **Depends on:** TASK-15
- **Done when:** New Game creates a save file and reaches operation
  menu. Load Game lists saves and loads the selected one.
- **Prompt for coding LLM:**
  ```
  Read specs/cipher-stage1/spec.md §2 US-CS1-001, US-CS1-004,
  §3 rules 8-9, §7 edge cases 1, 11-14.
  Implement in cipher/main.py:
  new_game():
    - Prompt for name: validate alphanumeric+underscore, max 20,
      non-empty. Re-prompt on invalid. (edge cases 11, 12)
    - If save exists: "Save found. Load it? (y/n)" (edge case 1)
    - Track selection: "1) Red Team  2) Full Stack"
      If player types anything else including "3" or "blue":
      print the redirect constant:
      "AEGIS is the Blue Team simulator. Run aegis/main.py to start
      your Blue Team track. Returning to track selection..."
      Re-prompt. (§3 rule 9)
    - create_save(name, track) → write_save → operation_menu(save_data)
  load_game():
    - saves = list_saves()
    - If empty: print_warning("No save files found.") → new_game()
      (edge case 14)
    - Display numbered list with last_played dates
    - Player selects number → load_with_fallback(name) →
      operation_menu(save_data)
  Stub operation_menu(save_data) as pass — implemented in TASK-17.
  ```

---

### TASK-17: Build main.py — Operation Menu + Placement Test
- **Files:** `cipher/main.py`
- **Depends on:** TASK-16
- **Done when:** Full end-to-end works: launch → new game → op01 →
  complete → menu → quit → relaunch → load → op01 shows ✅
- **Prompt for coding LLM:**
  ```
  Read specs/cipher-stage1/spec.md §2 US-CS1-002, US-CS1-003,
  §3 rules 10-12, §6 (operation menu layout, navigation flow),
  §9 (placement test result display format), docs/DATA_MODEL.md §5
  (registry unlock logic).
  Implement in cipher/main.py:
  operation_menu(save_data: dict):
    - Load content/registry.json
    - For each operation in registry order, compute status:
      ✅ if in save_data["completed"]
      ⏭  if in save_data["skipped"]
      ▶  if op_id == save_data["in_progress"]
      🔒 if previous op not in completed AND not in skipped
      (unlocked otherwise)
    - Display numbered list with status icons and titles
    - Player selects number:
      🔒 → print_warning("Complete the previous operation first.")
      ✅ → "Replay? XP will not be awarded again. (y/n)"
             y → reset hints_used + metrics for that op → run_operation
             n → return to menu
      others → save_data["in_progress"] = op_id → write_save →
               run_operation(op_id, save_data) → update save_data →
               loop back to menu
  placement_test(save_data: dict):
    - If save_data["placement_test"]["taken"]: print_warning
      ("Already completed.") → return
    - Load content/placement_test.json
    - For each question: display with options 1-4, get input,
      validate 1-4 only. Track score.
      Wrap in try/except KeyboardInterrupt:
        save_data["placement_test"]["taken"] = False → write_save →
        return (edge case from §3 rule 12)
    - Display result screen (spec §9 result display format)
    - Update save_data placement_test fields → write_save
    - → operation_menu(save_data)
  ```

---

## Phase 5: Validation & Hardening

### TASK-18: Final validation pass
- **Files:** None (testing only) — updates `docs/LESSONS_LEARNED.md`
  and `docs/PROJECT_FOUNDATION.md` if needed
- **Depends on:** TASK-17
- **Done when:** All items in spec §12 Definition of Done are checked off
- **Prompt for coding LLM:**
  ```
  Read specs/cipher-stage1/spec.md §1 (Success Criteria) and §7
  (all 15 edge cases) and §12 (Definition of Done).
  Run the following and report pass/fail for each:
  1. python main.py — launches, shows menu
  2. python main.py --dev — launches with [DEV MODE] message
  3. python validate_content.py — exits 0
  4. python check_imports.py — exits 0
  5. python -m unittest discover tests/ — all green
  6. New Game flow — create save, choose Red Team, reach op01
  7. All 9 commands in op01: help, learn, tools, hint (x4), notes,
     note test, skip (on a new save), menu, quit
  8. Correct answer (nexuscorp) → XP awarded → debrief shown
  9. Load Game → save appears → op01 shows correct status
  10. Test edge cases 5 (Ctrl+C), 6 (empty input), 7 (note no text),
      8 (5th hint), 11 (empty name), 12 (invalid name chars)
  For any failure: report the exact error and which task to revisit.
  Do NOT fix failures in this task — report only.
  ```

---

## Progress Tracker

| Task | Description | Phase | Status | Commit |
|------|-------------|-------|--------|--------|
| TASK-01 | Folder structure | 1 | ⬜ | |
| TASK-02 | utils/terminal.py | 1 | ⬜ | |
| TASK-03 | utils/player.py | 1 | ⬜ | |
| TASK-04 | utils/save_manager.py | 1 | ⬜ | |
| TASK-05 | utils/tools.py | 1 | ⬜ | |
| TASK-06 | check_imports.py | 1 | ⬜ | |
| TASK-07 | content/op01.json | 2 | ⬜ | |
| TASK-08 | content/placement_test.json | 2 | ⬜ | |
| TASK-09 | content/registry.json | 2 | ⬜ | |
| TASK-10 | validate_content.py | 2 | ⬜ | |
| TASK-11 | operation_runner — load + display | 3 | ⬜ | |
| TASK-12 | operation_runner — command loop | 3 | ⬜ | |
| TASK-13 | operation_runner — hints, skip, exit | 3 | ⬜ | |
| TASK-14 | operation_runner — correct answer + debrief | 3 | ⬜ | |
| TASK-15 | main.py — startup + menu | 4 | ⬜ | |
| TASK-16 | main.py — New Game + Load Game | 4 | ⬜ | |
| TASK-17 | main.py — Operation Menu + Placement Test | 4 | ⬜ | |
| TASK-18 | Final validation pass | 5 | ⬜ | |
