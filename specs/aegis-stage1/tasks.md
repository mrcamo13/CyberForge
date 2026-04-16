# tasks.md — AEGIS Stage 1: Core Engine + Cases 01-05
<!--
GENERATED from specs/aegis-stage1/plan.md + spec.md
Each task: <30 min | "done when" verifiable in <1 min | one commit
-->

**Source plan:** `specs/aegis-stage1/plan.md`
**Date:** 2026-04-11
**Total tasks:** 22

---

## Phase 1: Engine Infrastructure

### TASK-AG-01: Create folder structure
- **Files:** `aegis/utils/.gitkeep`, `aegis/engine/.gitkeep`,
  `aegis/content/cases/.gitkeep`, `aegis/saves/.gitkeep`,
  `aegis/tests/.gitkeep`
- **Depends on:** None
- **Done when:** All 5 directories exist under `aegis/`
- **Prompt for coding LLM:**
  ```
  Read specs/aegis-stage1/plan.md §Engine Components to Build.
  Create the following empty directories inside cyberforge/aegis/:
  utils/, engine/, content/cases/, saves/, tests/
  Add a .gitkeep file to each so they are tracked.
  Do not create any Python files yet.
  aegis/ is completely independent from cipher/ — no shared files.
  ```

---

### TASK-AG-02: Build utils/terminal.py
- **Files:** `aegis/utils/terminal.py`
- **Depends on:** TASK-AG-01
- **Done when:** `python -c "from utils.terminal import print_success,
  print_error, print_warning, print_info, print_muted, print_header,
  print_divider, clear_screen, normalize_input"` runs with no errors
  (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read cyberforge/cipher/utils/terminal.py as the reference implementation.
  Build aegis/utils/terminal.py — identical interface and behavior.
  Required functions:
  - print_success(msg: str) -> None      — green
  - print_error(msg: str) -> None        — red
  - print_warning(msg: str) -> None      — yellow
  - print_info(msg: str) -> None         — white
  - print_muted(msg: str) -> None        — dark gray
  - print_header(msg: str) -> None       — cyan
  - print_divider() -> None              — prints a line of dashes
  - clear_screen() -> None               — cross-platform (os.system)
  - normalize_input(raw: str) -> str     — strip, lowercase, collapse
    spaces, keep \w + space + . - / (allows forward slashes for path answers)
  All ANSI codes must be module-level constants, not inline strings.
  This is a NEW file — do NOT import from cipher/. stdlib only.
  Type hints and docstrings required on every function.
  ```

---

### TASK-AG-03: Build utils/player.py
- **Files:** `aegis/utils/player.py`
- **Depends on:** TASK-AG-02
- **Done when:** `python -c "from utils.player import calculate_xp,
  evaluate_badges; print(calculate_xp(100, 0)); print(evaluate_badges({}, '', 0))"` prints `100`
  then `[]` (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read cyberforge/cipher/utils/player.py as the reference implementation.
  Build aegis/utils/player.py — identical logic.
  Required functions:
  - calculate_xp(xp_base: int, hints_used: int) -> int
    XP multipliers: {0: 1.0, 1: 0.75, 2: 0.50, 3: 0.25, 4: 0.10}
    Return int(xp_base * multiplier)
  - evaluate_badges(save_data: dict, just_completed_id: str = "",
                    hints_used_this_run: int = 0) -> list
    Stage 1 checks ONLY:
      first_blood: award if len(save_data["completed"]) == 1 (exactly after
                   first completion — check AFTER appending the new case_id)
      no_hints: award if hints_used_this_run == 0 for the just-completed case
    Returns list of newly earned badge ID strings not already in
    save_data["badges"]. Never awards a badge twice.
  Do NOT import from cipher/. stdlib only.
  Type hints and docstrings required.
  ```

---

### TASK-AG-04: Build utils/save_manager.py + tests
- **Files:** `aegis/utils/save_manager.py`, `aegis/tests/test_save_manager.py`
- **Depends on:** TASK-AG-02
- **Done when:** `python -m unittest tests/test_save_manager.py` passes
  (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read cyberforge/cipher/utils/save_manager.py as the reference.
  Build aegis/utils/save_manager.py — identical atomic save pattern.
  Key difference: save files live in aegis/saves/ (not cipher/saves/).
  Track values for AEGIS: "blue" or "full" (never "red").
  
  Required functions:
  - create_save(player_name: str, track: str) -> dict
    Returns new save dict with this exact schema — all keys must be present:
    {
      "player_name": player_name,
      "track": track,
      "xp": 0,
      "completed": [],
      "skipped": [],
      "in_progress": null,
      "badges": [],
      "notes": {},
      "hints_used": {},
      "metrics": {},
      "placement_test": {"taken": false, "score": 0, "passed": false},
      "last_played": "<ISO datetime string>"
    }
    metrics[case_id] entries are created on-demand using setdefault() —
    do NOT pre-populate them in create_save().
    Creates saves/ directory if missing.
  - write_save(save_data: dict) -> None
    Atomic write: [name].tmp.json → verify JSON → rename → backup.
    Windows-safe: if destination exists, os.remove() before os.rename().
  - load_save(player_name: str) -> dict | None
    Validate schema on load. If corrupted: rename to .corrupted.json,
    notify user, return None.
  - load_with_fallback(player_name: str) -> dict | None
    Try primary → try backup → return None if neither exists.
    Do NOT create a new save here — caller (new_game) handles the None case.
  - migrate_save(save_data: dict) -> dict
    Add missing fields with defaults. Never delete existing data.
  - list_saves() -> list
    Returns [{name, last_played}] sorted by last_played descending.

  migrate_save() must add any missing top-level keys with their defaults
  (using the schema above) without deleting existing data.
  
  Also create aegis/tests/test_save_manager.py with:
  - test_save_load_roundtrip: create → write → load → assert equal
  - test_atomic_write: write succeeds, .tmp file is removed after
  - test_corrupted_primary_loads_backup
  
  Do NOT import from cipher/. stdlib only.
  Type hints and docstrings required. Use os.path.join() for all paths.
  ```

---

### TASK-AG-05: Build check_imports.py
- **Files:** `aegis/check_imports.py`
- **Depends on:** TASK-AG-01
- **Done when:** `python check_imports.py` exits 0 and prints
  `[PASS]` for all files in utils/ (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read cyberforge/cipher/check_imports.py as the reference implementation.
  Build aegis/check_imports.py — identical logic.
  Scans all .py files in aegis/engine/ and aegis/utils/ recursively.
  Parses import statements (import X and from X import Y).
  Checks each top-level module against the stdlib allowlist:
    os, sys, json, re, datetime, pathlib, unittest, hashlib,
    base64, collections, itertools, functools, string, time,
    random, math, copy, io, textwrap, runpy
  Local packages exempt from check: utils, engine
  Prints [PASS] filename or [FAIL] filename — unauthorized: module_name
  Exits 0 if all pass, exits 1 if any fail.
  Do NOT import from cipher/. stdlib only.
  Type hints and docstrings required.
  ```

---

## Phase 2: Tool Functions

### TASK-AG-06: Build utils/tools.py
- **Files:** `aegis/utils/tools.py`
- **Depends on:** TASK-AG-02
- **Done when:**
  ```
  python -c "from utils.tools import run_tool; print(run_tool('log_filter', '10.0.0.99 - - [11/Apr/2026:02:14:33 +0000] \"GET /admin/dashboard HTTP/1.1\" 200 4821'))"
  ```
  prints a LOG FILTER result showing [MATCH] lines (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Build aegis/utils/tools.py with these functions. Do NOT import from cipher/.
  
  run_tool(tools_type: str, challenge_text: str) -> str
    Dispatches to the correct tool function by tools_type string.
    If tools_type not recognized: return "Unknown tool type."
    tools_type "none" → calls ir_reference() (ignore challenge_text)
  
  log_filter(challenge_text: str) -> str
    Input: multi-line log string (\\n-separated Apache/nginx access log entries).
    Split on \\n. Filter for entries where:
      - IP starts with "10." (internal RFC 1918)
      - Path contains "/admin/dashboard"
      - Status code is "200"
    Output format (see spec §9 case01 Tools Output):
      "LOG FILTER — access log analysis\n\n"
      "Filtering for: internal IP (10.0.0.x) + status 200 + path /admin/dashboard\n\n"
      "[MATCH] <line>" for each matching entry
      "Other entries (no match):" then non-matching entries
      "Analysis complete. Source IP identified: <ip> (<n> requests)"
  
  ioc_classifier(challenge_text: str) -> str
    Input: a string artifact to classify.
    Detect encoding type by pattern matching:
      Base64: matches ^[A-Za-z0-9+/]+=*$ and len % 4 == 0 or no padding
      Hex: matches ^[0-9a-fA-F]+$ and even length
      ROT13: all alpha characters
    Attempt base64 decode. Output format (see spec §9 case02 Tools Output):
      "IOC CLASSIFIER — artifact analysis\n\n"
      "Input: <string>\n\n"
      "Encoding detection:" with character analysis
      "Classification: BASE64 ENCODING\n\n"
      "Decoded value: <decoded>"
      "IOC type: Encoded credential artifact"
      "Severity: HIGH — decoded value appears to be a credential or deployment key"
  
  vuln_scorer(challenge_text: str) -> str
    Input: a scan description string (not used for logic — output is hardcoded
    to match the scan findings defined in case03).
    Output format (see spec §9 case03 Tools Output):
      "VULNERABILITY SCORER — scan results for 203.0.113.47\n\n"
      "Ranking findings by priority...\n\n"
      RANK 1 [CRITICAL] CVE-FAKE-2024-099 — nginx 1.24.0, CVSS 9.8, Unauth RCE
      RANK 2 [MEDIUM] CVE-FAKE-2022-001 — OpenSSH 8.9p1, CVSS 5.3
      RANK 3 [INFO] MySQL — filtered, no action
      "Top priority: CVE-FAKE-2024-099 — patch nginx immediately."
  
  process_analyzer(challenge_text: str) -> str
    Input: newline-separated process list string.
    Parse each line: "PID:<n> <name> user:<u> SUID:<yes/no> parent:<p>"
    Flag as [CRITICAL] if: user=root AND SUID=yes AND parent not in
      ("systemd", "init", "launchd")
    Flag as [SUSPICIOUS] if: SUID=yes AND user != root AND name in
      ("python3.10", "python3", "python", "perl", "ruby", "bash")
    Flag as [OK] otherwise.
    Output format (see spec §9 case04 Tools Output):
      "PROCESS ANALYZER — anomaly detection\n\n"
      "Scanning process list for privilege anomalies...\n\n"
      Table with columns: PID PROCESS USER SUID PARENT STATUS
      "CRITICAL finding: PID <n>" with explanation
  
  ir_reference(challenge_text: str = "") -> str
    Returns the hardcoded IR phase reference table regardless of input.
    Output format (see spec §9 case05 Tools Output):
      "IR PHASE REFERENCE — NIST SP 800-61\n\n"
      All 4 phases with key actions listed
      "Current incident status maps to: PHASE 3 — ERADICATION"
  
  Dispatch dict in run_tool():
    "log_filter":       log_filter,
    "ioc_classifier":   ioc_classifier,
    "vuln_scorer":      vuln_scorer,
    "process_analyzer": process_analyzer,
    "none":             ir_reference,
  
  stdlib only. Type hints and docstrings required.
  ```

---

## Phase 3: Content Layer

### TASK-AG-07: Create content/cases/case01.json
- **Files:** `aegis/content/cases/case01.json`
- **Depends on:** TASK-AG-01
- **Done when:** File parses as valid JSON with all required fields
- **Prompt for coding LLM:**
  ```
  Read specs/aegis-stage1/spec.md §9 Case 01 — Log Analysis (full content).
  Read specs/aegis-stage1/spec.md §4 (canonical AEGIS case JSON structure).
  Create aegis/content/cases/case01.json with ALL fields populated exactly
  as defined in the spec:
    id: "case01", title: "Suspicious Access", track: "blue"
    cert_objective: "CySA+ CS0-003 Domain 1 — Security Operations"
    xp_base: 100, difficulty: 1, tools_type: "log_filter"
    challenge_data: the full log snippet string (\\n-separated, one string)
    scenario, challenge, valid_answers, hints (exactly 4), learn, tools
    debrief with 5 subfields: summary, real_world, next_step, cert_link, exam_tip
  valid_answers: ["10.0.0.99"]
  ```

---

### TASK-AG-08: Create content/cases/case02.json
- **Files:** `aegis/content/cases/case02.json`
- **Depends on:** TASK-AG-01
- **Done when:** File parses as valid JSON with all required fields
- **Prompt for coding LLM:**
  ```
  Read specs/aegis-stage1/spec.md §9 Case 02 — IOC Classification (full content).
  Read specs/aegis-stage1/spec.md §4 (canonical AEGIS case JSON structure).
  Create aegis/content/cases/case02.json with ALL fields populated:
    id: "case02", title: "Encoded Artifact", track: "blue"
    cert_objective: "CySA+ CS0-003 Domain 1 — Security Operations"
    xp_base: 100, difficulty: 1, tools_type: "ioc_classifier"
    challenge_data: "ZGVwbG95bWFzdGVy"
    scenario, challenge, valid_answers, hints (exactly 4), learn, tools
    debrief with 5 subfields including exam_tip
  valid_answers: ["base64", "base 64", "b64"]
  ```

---

### TASK-AG-09: Create content/cases/case03.json
- **Files:** `aegis/content/cases/case03.json`
- **Depends on:** TASK-AG-01
- **Done when:** File parses as valid JSON with all required fields
- **Prompt for coding LLM:**
  ```
  Read specs/aegis-stage1/spec.md §9 Case 03 — Vulnerability Scanning (full content).
  Read specs/aegis-stage1/spec.md §4 (canonical AEGIS case JSON structure).
  Create aegis/content/cases/case03.json with ALL fields populated:
    id: "case03", title: "Scan Report", track: "blue"
    cert_objective: "CySA+ CS0-003 Domain 2 — Vulnerability Management"
    xp_base: 150, difficulty: 2, tools_type: "vuln_scorer"
    challenge_data: "nginx 1.24.0 port 8080 CVE-FAKE-2024 CVSS 9.8 unauthenticated RCE"
    scenario, challenge, valid_answers, hints (exactly 4), learn, tools
    debrief with 5 subfields including exam_tip
  valid_answers: ["cve-fake-2024-099", "cve-fake-2024"]
  ```

---

### TASK-AG-10: Create content/cases/case04.json
- **Files:** `aegis/content/cases/case04.json`
- **Depends on:** TASK-AG-01
- **Done when:** File parses as valid JSON with all required fields
- **Prompt for coding LLM:**
  ```
  Read specs/aegis-stage1/spec.md §9 Case 04 — Malware/Anomaly Detection (full content).
  Read specs/aegis-stage1/spec.md §4 (canonical AEGIS case JSON structure).
  Create aegis/content/cases/case04.json with ALL fields populated:
    id: "case04", title: "Rogue Process", track: "blue"
    cert_objective: "CySA+ CS0-003 Domain 1 — Security Operations"
    xp_base: 150, difficulty: 2, tools_type: "process_analyzer"
    challenge_data: "PID:1001 python3.10 user:www-data SUID:yes parent:bash\nPID:1002 nginx user:www-data SUID:no parent:systemd\nPID:1003 sshd user:root SUID:no parent:systemd\nPID:1004 python3.10 user:root SUID:yes parent:python3.10\nPID:1005 mysql user:mysql SUID:no parent:systemd"
    scenario, challenge, valid_answers, hints (exactly 4), learn, tools
    debrief with 5 subfields including exam_tip
  valid_answers: ["1004", "pid 1004", "pid:1004"]
  ```

---

### TASK-AG-11: Create content/cases/case05.json
- **Files:** `aegis/content/cases/case05.json`
- **Depends on:** TASK-AG-01
- **Done when:** File parses as valid JSON with all required fields
- **Prompt for coding LLM:**
  ```
  Read specs/aegis-stage1/spec.md §9 Case 05 — Incident Response (full content).
  Read specs/aegis-stage1/spec.md §4 (canonical AEGIS case JSON structure).
  Create aegis/content/cases/case05.json with ALL fields populated:
    id: "case05", title: "Incident Phase", track: "blue"
    cert_objective: "CySA+ CS0-003 Domain 3 — Incident Response"
    xp_base: 200, difficulty: 3, tools_type: "none"
    challenge_data: "The staging server has been fully compromised. Root access confirmed. Attacker tools removed. System isolated from network. Backups verified intact."
    scenario, challenge, valid_answers, hints (exactly 4), learn, tools
    debrief with 5 subfields including exam_tip
  valid_answers: ["eradication", "eradication and recovery"]
  Note: "remediation" dropped — not a NIST SP 800-61 phase name.
  Note: tools_type is the string "none" — this is valid per spec §4.
  ```

---

### TASK-AG-12: Create content/placement_test.json
- **Files:** `aegis/content/placement_test.json`
- **Depends on:** TASK-AG-01
- **Done when:** File parses as valid JSON with 5 questions
- **Prompt for coding LLM:**
  ```
  Read specs/aegis-stage1/spec.md §9 Placement Test (full JSON already defined).
  Create aegis/content/placement_test.json using exactly the content in the spec:
  - pass_threshold: 4
  - xp_on_pass: 50
  - 5 questions (pt01-pt05) covering: SIEM, IR phases, CVSS, Base64, HTTP status codes
  correct_index values: pt01=1, pt02=2, pt03=3, pt04=2, pt05=2
  Copy the question text and options exactly as written in spec §9.
  ```

---

### TASK-AG-13: Create content/registry.json
- **Files:** `aegis/content/registry.json`
- **Depends on:** TASK-AG-07 through TASK-AG-11
- **Done when:** File parses as valid JSON and all 5 case IDs are registered
  with status "active"
- **Prompt for coding LLM:**
  ```
  Create aegis/content/registry.json registering all 5 cases.
  Schema:
  {
    "version": "1.0",
    "cases": [
      {
        "id": "case01",
        "title": "Suspicious Access",
        "status": "active",
        "difficulty": 1,
        "cert_objective": "CySA+ CS0-003 Domain 1 — Security Operations"
      },
      ... (case02-05 following same pattern)
    ]
  }
  Cases in order: case01 (diff 1), case02 (diff 1), case03 (diff 2),
  case04 (diff 2), case05 (diff 3).
  cert_objectives: case01/02/04 = Domain 1, case03 = Domain 2, case05 = Domain 3.
  No "operations" key — AEGIS uses "cases" only.
  ```

---

### TASK-AG-14: Build validate_content.py
- **Files:** `aegis/validate_content.py`
- **Depends on:** TASK-AG-07 through TASK-AG-13
- **Done when:** `python validate_content.py` exits 0 and prints [PASS]
  for all 5 cases, placement_test.json, and registry.json.
  `content/checksums.json` is created. (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read cyberforge/cipher/validate_content.py as the reference.
  Build aegis/validate_content.py — same structure with AEGIS-specific changes.
  
  Key differences from cipher/validate_content.py:
  1. Scans content/cases/ (not content/operations/)
  2. tools_type allowlist is AEGIS-specific:
     {"log_filter", "ioc_classifier", "vuln_scorer", "process_analyzer", "none"}
  3. Debrief required fields add "exam_tip":
     ("summary", "real_world", "next_step", "cert_link", "exam_tip")
  4. Registry validator checks "cases" key (not "operations" key)
  5. Registry file path check: content/cases/{id}.json
  6. Add track field validation: each case JSON must have track in {"blue", "full"}
  
  Same as cipher version:
  - _CASE_REQUIRED_FIELDS same as _OP_REQUIRED_FIELDS
  - validate_placement_test() — identical logic
  - write_checksums() — identical logic
  - SHA-256 checksums written to content/checksums.json
  - Exit 0 if all pass, exit 1 if any fail
  
  Do NOT import from cipher/. stdlib only. Type hints and docstrings required.
  ```

---

## Phase 4: Case Engine + Main Menu

### TASK-AG-15: Build engine/case_runner.py — load + display
- **Files:** `aegis/engine/case_runner.py`
- **Depends on:** TASK-AG-02, TASK-AG-03, TASK-AG-04, TASK-AG-06, TASK-AG-14
- **Done when:** `python -c "from engine.case_runner import load_case;
  print(load_case('case01')['title'])"` prints `Suspicious Access`
  (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read cyberforge/cipher/engine/operation_runner.py as the reference.
  Build aegis/engine/case_runner.py — same pattern, AEGIS terminology.
  
  Required:
  - load_case(case_id: str) -> dict
    Loads and returns content/cases/{case_id}.json
    Raises FileNotFoundError with clear message if not found.
  - display_intro(case_data: dict) -> None
    clear_screen()
    print_header(case_data["title"])
    print_info(case_data["scenario"])
    print_divider()
    print_warning(case_data["challenge"])
    print_muted("Type 'help' to see available commands.")
  
  This task builds ONLY load and display. Command loop in TASK-AG-16.
  Do NOT import from cipher/. stdlib only. Type hints and docstrings required.
  ```

---

### TASK-AG-16: Build engine/case_runner.py — command loop
- **Files:** `aegis/engine/case_runner.py`
- **Depends on:** TASK-AG-15
- **Done when:** Running a case manually shows the prompt, accepts `help`
  and prints command list, accepts `learn` and prints learn text,
  accepts `tools` and prints tool output
- **Prompt for coding LLM:**
  ```
  Read cyberforge/cipher/engine/operation_runner.py run_operation() as reference.
  Add run_case(case_id: str, save_data: dict) -> dict to aegis/engine/case_runner.py.
  
  Implement the command loop with strict 3-step priority:
  
  Before entering the loop, initialize per-case metrics using setdefault:
    save_data["metrics"].setdefault(case_id, {
        "completed": False, "hints_maxed": False,
        "time_spent_seconds": 0, "started_at": <ISO datetime>
    })
  
  Step 1 — exact match (after normalize_input):
    help   → print exactly these 9 commands using print_info:
               help, learn, tools, notes, note <text>, hint, skip, menu, quit
    learn  → print case_data["learn"] using print_info
    tools  → call run_tool(case_data["tools_type"], case_data["challenge_data"])
              print result using print_info
    notes  → print save_data["notes"].get(case_id, []) or "No notes yet."
    hint   → handled in TASK-AG-17
    skip   → handled in TASK-AG-17
    menu   → handled in TASK-AG-17
    quit   → handled in TASK-AG-17
  
  Step 2 — starts with "note ":
    Save text after "note " to save_data["notes"][case_id]
    print_success("Note saved.")
  
  Step 3 — answer fallback:
    normalize input → check against valid_answers list
    Wrong: print_error("Incorrect. Try again, or type 'hint'.")
    Correct: handled in TASK-AG-18
  
  Wrap entire loop in try/except KeyboardInterrupt → save + return.
  Call display_intro(case_data) before entering the loop.
  Do NOT import from cipher/. stdlib only. Type hints and docstrings required.
  ```

---

### TASK-AG-17: Build engine/case_runner.py — hints, skip, exit
- **Files:** `aegis/engine/case_runner.py`
- **Depends on:** TASK-AG-16
- **Done when:** `hint` reveals hints in order 1-4, 5th hint shows
  "No more hints available.", `skip` returns to caller, `menu` and
  `quit` save and return/exit
- **Prompt for coding LLM:**
  ```
  Read cyberforge/cipher/engine/operation_runner.py hints/skip/exit handling.
  Add to run_case() in aegis/engine/case_runner.py:
  
  hint command:
    hints_used = save_data["hints_used"].get(case_id, 0)
    If < 4: print case_data["hints"][hints_used] using print_warning  ← use BEFORE increment
            increment hints_used → save to save_data["hints_used"][case_id]
            If now = 4: save_data["metrics"][case_id]["hints_maxed"] = True
    If = 4: print_warning("No more hints available. Try 'tools'.")
  
  skip command:
    Add case_id to save_data["skipped"] if not already there
    Update time_spent_seconds in metrics
    write_save(save_data)
    print_muted("Case skipped.")
    Return save_data
  
  menu command:
    write_save(save_data)
    Return save_data
  
  quit command:
    write_save(save_data)
    print_muted("Progress saved. Goodbye.")
    sys.exit(0)
  
  Do NOT import from cipher/. stdlib only.
  ```

---

### TASK-AG-18: Build engine/case_runner.py — correct answer + debrief
- **Files:** `aegis/engine/case_runner.py`
- **Depends on:** TASK-AG-17
- **Done when:** Typing `10.0.0.99` in case01 awards XP, prints debrief
  with exam_tip, and returns save_data with case01 in completed list
- **Prompt for coding LLM:**
  ```
  Read cyberforge/cipher/engine/operation_runner.py correct answer handling.
  Add correct answer handling to run_case() in aegis/engine/case_runner.py.
  
  On correct answer:
    1. hints_used = save_data["hints_used"].get(case_id, 0)
    2. is_replay = case_id in save_data["completed"]
    3. xp_earned = calculate_xp(case_data["xp_base"], hints_used) if not is_replay else 0
    4. If not is_replay: save_data["xp"] += xp_earned; append case_id to completed
    5. save_data["metrics"][case_id]["completed"] = True
    6. Update time_spent_seconds in metrics
    7. new_badges = evaluate_badges(save_data, case_id, hints_used) if not is_replay else []
    8. save_data["badges"].extend(new_badges)
    9. write_save(save_data)
    10. Display debrief:
        clear_screen()
        print_header("CASE COMPLETE")
        print_divider()
        if not is_replay: print_success(f"XP AWARDED: {xp_earned}")
        else: print_muted("(Replay — XP not awarded again)")
        for badge in new_badges: print_success(f"Badge unlocked: {badge}")
        print_divider()
        print_info(case_data["debrief"]["summary"])
        print_info(case_data["debrief"]["real_world"])
        print_warning(case_data["debrief"]["next_step"])
        print_muted(case_data["debrief"]["cert_link"])
        print_divider()
        print_header("EXAM TIP")
        print_info(case_data["debrief"]["exam_tip"])
        print_divider()
        input("Press Enter to continue...")
    11. Return save_data
  
  Do NOT import from cipher/. stdlib only. Type hints and docstrings required.
  ```

---

### TASK-AG-19: Build main.py — startup + main menu
- **Files:** `aegis/main.py`
- **Depends on:** TASK-AG-14, TASK-AG-18
- **Done when:** `python main.py` (from inside aegis/) shows ASCII AEGIS
  logo and 4-option menu. `python main.py --dev` skips content validation.
- **Prompt for coding LLM:**
  ```
  Read cyberforge/cipher/main.py as the reference implementation.
  Build aegis/main.py — same structure with AEGIS labeling.
  
  - Parse sys.argv for --dev flag
  - Production mode: run validate_content.py in-process using runpy only:
      import runpy
      try:
          runpy.run_path("validate_content.py", run_name="__main__")
      except SystemExit as e:
          if e.code != 0:
              print_error("Content validation failed.")
              sys.exit(1)
    Do NOT use subprocess, importlib, or exec.
  - Dev mode: skip validation, print_muted("[DEV MODE — content validation skipped]")
  - Display ASCII AEGIS logo in cyan (design a distinct logo — NOT same as CIPHER)
  - Print main menu:
    [1] New Game
    [2] Load Game
    [3] Placement Test
    [4] Quit
  - Input loop: accept 1-4, invalid input re-prompts
  - Route to: new_game(), load_game(), placement_test(save_data=None), sys.exit(0)
  - Placement test from main menu (no save loaded): runs in GUEST MODE —
    results are displayed but NOT persisted. No save file is created.
  - Stub new_game(), load_game(), placement_test() as pass — implemented TASK-AG-20/21
  
  Note: subprocess is not in the stdlib allowlist. Use runpy to run
  validate_content.py in-process. Example:
    import runpy
    result = runpy.run_path('validate_content.py', run_name='__main__')
  Catch SystemExit to capture the exit code.
  
  Do NOT import from cipher/. Type hints and docstrings required.
  ```

---

### TASK-AG-20: Build main.py — New Game + Load Game flows
- **Files:** `aegis/main.py`
- **Depends on:** TASK-AG-19
- **Done when:** New Game creates a save and reaches the case menu.
  Load Game lists saves and loads the selected one.
- **Prompt for coding LLM:**
  ```
  Read cyberforge/cipher/main.py new_game() and load_game() as reference.
  Implement in aegis/main.py — same logic with AEGIS-specific changes.
  
  new_game():
    - Prompt: "Enter analyst name:" — validate alphanumeric+underscore,
      max 20 chars, non-empty. Re-prompt on invalid.
    - If save file already exists: "Save found. Load it? (y/n)"
      y → save_data = load_with_fallback(name)
          if save_data is None: create_save(name, track) (fallback, should not happen)
          → case_menu(save_data)
      n → call create_save(name, track) + write_save() to overwrite the primary
          save. The old backup file is also overwritten on the next write_save call.
          No explicit delete needed — write_save replaces it atomically.
    - Track selection:
      "Select track:"
      "  [1] Blue Team"
      "  [2] Full Stack"
      Any other input (including "3", "red", "r"):
        print_warning("CIPHER is the Red Team simulator. Run cipher/main.py
        to start your Red Team track. Returning to track selection...")
        Re-prompt.
      Map 1 → "blue", 2 → "full"
    - create_save(name, track) → write_save → case_menu(save_data)
  
  load_game():
    - saves = list_saves()
    - If empty: print_warning("No save files found.") → new_game()
    - Display numbered list with last_played dates
    - Player selects number → load_with_fallback(name) → case_menu(save_data)
  
  Stub case_menu(save_data) as pass — implemented in TASK-AG-21.
  Do NOT import from cipher/. stdlib only.
  ```

---

### TASK-AG-21: Build main.py — Case Menu + Placement Test
- **Files:** `aegis/main.py`
- **Depends on:** TASK-AG-20
- **Done when:** Full end-to-end works: launch → new game → case01 →
  complete → menu → quit → relaunch → load → case01 shows as completed
- **Prompt for coding LLM:**
  ```
  Read cyberforge/cipher/main.py operation_menu() and placement_test() as reference.
  Implement in aegis/main.py — same logic with "case" terminology.
  
  case_menu(save_data: dict):
    - Load content/registry.json
    - For each case in registry["cases"] order, compute status:
      ✅  if case_id in save_data["completed"]
      ⏭   if case_id in save_data["skipped"]
      ▶  if case_id == save_data["in_progress"]
      🔒  if previous case not in completed AND not in skipped
      (unlocked otherwise — no icon)
    - Display numbered list with status icons and titles
    - Display total XP in header: "ANALYST: {name} | XP: {xp}"
    - Player selects number:
      🔒 → print_warning("Complete the previous case first.")
      ✅ → "Replay this case? XP will not be awarded again. (y/n)"
             y → reset hints_used and metrics for that case → run_case
             n → return to menu
      others → save_data["in_progress"] = case_id → write_save →
               run_case(case_id, save_data) → update save_data → loop
    - Option to return to main menu (add [0] Main Menu or 'm' input)
  
  placement_test(save_data: dict = None):
    - GUEST MODE (save_data is None): run test, display results, return to main menu.
      Do NOT create a save file. Do NOT persist anything.
    - SAVE MODE (save_data provided):
      If save_data["placement_test"]["taken"]:
        print_warning("Placement test already completed.") → return to case_menu
      Load content/placement_test.json
      For each question: display with options 1-4, get input, validate 1-4.
        Wrap in try/except KeyboardInterrupt:
          if save_data: save_data["placement_test"]["taken"] = False → write_save
          return
      Score and display results (pass/fail, score, XP if passed)
      If save_data:
        update save_data["placement_test"]: taken=True, score=N, passed=bool
        If passed: save_data["xp"] += placement_test["xp_on_pass"]
        write_save(save_data)
        → case_menu(save_data)
      Else: → main menu loop (return)
  
  Do NOT import from cipher/. stdlib only.
  ```

---

## Phase 5: Validation

### TASK-AG-22: Final validation pass
- **Files:** None (testing only) — updates spec.md status to Complete
- **Depends on:** TASK-AG-21
- **Done when:** All items in spec §12 Definition of Done are checked off
- **Prompt for coding LLM:**
  ```
  Read specs/aegis-stage1/spec.md §1 (Success Criteria) and §12
  (Definition of Done). Run the following and report pass/fail for each:
  
  All commands run from inside aegis/ directory.
  
  1. python main.py — launches, shows AEGIS logo and menu
  2. python main.py --dev — launches with [DEV MODE] message
  3. python validate_content.py — exits 0, [PASS] for all 7 files
  4. python check_imports.py — exits 0, [PASS] for all files
  5. python -m unittest discover tests/ — all tests green
  6. New Game flow — create save, choose Blue Team, reach case menu
  7. Case01 all 9 commands: help, learn, tools, hint (x4), notes,
     note test, skip (on second save), menu, quit
  8. Correct answer (10.0.0.99) → XP awarded → debrief + exam_tip shown
  9. Load Game → save appears → case01 shows ✅ status
  10. Test: 5th hint shows "No more hints available."
  11. Test: empty analyst name re-prompts
  12. Test: Red Team track selection shows redirect message
  13. Verify all 5 cases visible in case menu with correct lock status
  14. Verify Ctrl+C during case saves and exits gracefully
  
  For any failure: report the exact error and which task to revisit.
  Do NOT fix failures in this task — report only.
  After all pass: update specs/aegis-stage1/spec.md status field to "Complete".
  ```

---

## Progress Tracker

| Task | Description | Phase | Status | Commit |
|------|-------------|-------|--------|--------|
| TASK-AG-01 | Folder structure | 1 | ⬜ | |
| TASK-AG-02 | utils/terminal.py | 1 | ⬜ | |
| TASK-AG-03 | utils/player.py | 1 | ⬜ | |
| TASK-AG-04 | utils/save_manager.py + tests | 1 | ⬜ | |
| TASK-AG-05 | check_imports.py | 1 | ⬜ | |
| TASK-AG-06 | utils/tools.py | 2 | ⬜ | |
| TASK-AG-07 | content/cases/case01.json | 3 | ⬜ | |
| TASK-AG-08 | content/cases/case02.json | 3 | ⬜ | |
| TASK-AG-09 | content/cases/case03.json | 3 | ⬜ | |
| TASK-AG-10 | content/cases/case04.json | 3 | ⬜ | |
| TASK-AG-11 | content/cases/case05.json | 3 | ⬜ | |
| TASK-AG-12 | content/placement_test.json | 3 | ⬜ | |
| TASK-AG-13 | content/registry.json | 3 | ⬜ | |
| TASK-AG-14 | validate_content.py | 3 | ⬜ | |
| TASK-AG-15 | case_runner — load + display | 4 | ⬜ | |
| TASK-AG-16 | case_runner — command loop | 4 | ⬜ | |
| TASK-AG-17 | case_runner — hints, skip, exit | 4 | ⬜ | |
| TASK-AG-18 | case_runner — correct answer + debrief | 4 | ⬜ | |
| TASK-AG-19 | main.py — startup + menu | 4 | ⬜ | |
| TASK-AG-20 | main.py — New Game + Load Game | 4 | ⬜ | |
| TASK-AG-21 | main.py — Case Menu + Placement Test | 4 | ⬜ | |
| TASK-AG-22 | Final validation pass | 5 | ⬜ | |
