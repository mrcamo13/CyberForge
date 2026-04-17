# tasks.md — LAB Stage 1
<!--
SDD Phase 3 of 4: Tasks
Next: build
-->

**Module:** lab-stage1
**Date:** 2026-04-16

---

## Task Groups

### Group A — Directory skeleton (3 tasks)
- Task 01: Create lab/ directory tree
- Task 02: Generate suspicious.bin fixture and verify SHA-256
- Task 03: Write all fixture files (access.log, ip_list.txt, encoded.txt)

### Group B — Content JSON (6 tasks)
- Task 04: Write lab/content/challenges/lab01.json
- Task 05: Write lab/content/challenges/lab02.json
- Task 06: Write lab/content/challenges/lab03.json
- Task 07: Write lab/content/challenges/lab04.json
- Task 08: Write lab/content/challenges/lab05.json
- Task 09: Write lab/content/registry.json

### Group C — Engine (5 tasks)
- Task 10: Write lab/utils/terminal.py   (copy aegis version)
- Task 11: Write lab/utils/save_manager.py (adapted from aegis)
- Task 12: Write lab/utils/player.py     (adapted from aegis)
- Task 13: Write lab/engine/challenge_runner.py  (new — core engine)
- Task 14: Write lab/main.py

### Group D — Integration (2 tasks)
- Task 15: Update play.py to add [3] LAB
- Task 16: Write lab/validate_content.py

### Group E — Tests + smoke (2 tasks)
- Task 17: Write lab/tests/test_challenge_runner.py (unit tests)
- Task 18: Smoke test — run validate_content.py, run test suite

---

## Detailed Task Specs

---

### Task 01 — Directory skeleton

Create these directories (files added in later tasks):
```
lab/
  content/
    challenges/
    fixtures/
  engine/
  saves/
  tests/
  utils/
  workspace/
```

Add `lab/saves/.gitkeep` and `lab/workspace/.gitkeep` so git tracks the empty dirs.

---

### Task 02 — Generate suspicious.bin

Write a one-off Python script that:
1. Creates `lab/content/fixtures/suspicious.bin` with content:
   `b"NIGHTWIRE_BEACON_PAYLOAD_v2\x00" * 16`
2. Computes and prints its SHA-256 hash
3. That hash becomes the KNOWN_HASH constant in lab03.json

Run the script, capture the hash, embed it in lab03.json.
Do NOT hardcode a guess — compute then embed.

---

### Task 03 — Fixture files

**access.log** → `lab/content/fixtures/access.log`
```
203.0.113.1 - - [01/Apr/2026:08:01:12 +0000] "GET /index.html HTTP/1.1" 200 1024
203.0.113.2 - - [01/Apr/2026:08:01:45 +0000] "GET /admin HTTP/1.1" 404 512
203.0.113.3 - - [01/Apr/2026:08:02:10 +0000] "POST /login HTTP/1.1" 200 256
203.0.113.4 - - [01/Apr/2026:08:02:33 +0000] "GET /secret.txt HTTP/1.1" 404 512
203.0.113.5 - - [01/Apr/2026:08:03:01 +0000] "GET /favicon.ico HTTP/1.1" 200 128
203.0.113.6 - - [01/Apr/2026:08:03:22 +0000] "GET /.env HTTP/1.1" 404 512
203.0.113.7 - - [01/Apr/2026:08:03:55 +0000] "GET /robots.txt HTTP/1.1" 200 64
203.0.113.8 - - [01/Apr/2026:08:04:10 +0000] "GET /wp-admin HTTP/1.1" 404 512
203.0.113.9 - - [01/Apr/2026:08:04:44 +0000] "GET /index.html HTTP/1.1" 200 1024
203.0.113.10 - - [01/Apr/2026:08:05:01 +0000] "GET /shell.php HTTP/1.1" 404 512
```

**ip_list.txt** → `lab/content/fixtures/ip_list.txt`
```
192.168.1.1
10.0.0.256
MALWARE-C2-SERVER
172.16.0.1
999.999.999.999
8.8.8.8
not-an-ip
1.2.3.4
300.1.1.1
185.220.101.47
10.10.10
203.0.113.99
```

**encoded.txt** → `lab/content/fixtures/encoded.txt`
```
d2hvYW1p
aWZjb25maWcgL2FsbA==
bmV0IHVzZXIgYWRtaW4gUEBzc3dvcmQxMjMgL2FkZA==
cG93ZXJzaGVsbCAtZW5jb2RlZGNvbW1hbmQ=
Y21kIC9jIHdob2FtaSAmJiBuZXQgbG9jYWxncm91cA==
```

---

### Tasks 04–08 — Challenge JSON files

Each file follows this schema:
```json
{
  "id": "labXX",
  "title": "string",
  "difficulty": 1|2|3,
  "xp_base": 100|150|200,
  "fixtures": ["filename", ...],
  "scenario": "string",
  "challenge": "string",
  "starter_code": "string",
  "expected_output": "string",
  "hints": ["hint1", "hint2", "hint3", "hint4"],
  "learn": "string",
  "debrief": {
    "summary": "string",
    "real_world": "string",
    "next_step": "string",
    "cert_link": "string",
    "exam_tip": "string"
  }
}
```

See spec.md for all field values per challenge.

**lab05 special field:**
```json
"test_server_port": 7005
```
challenge_runner checks for this field and starts/stops the background
server before/after running solution.py.

---

### Task 09 — registry.json

```json
{
  "version": "1.0",
  "simulator": "lab",
  "challenges": [
    {"id": "lab01", "title": "Log Parser",   "difficulty": 1},
    {"id": "lab02", "title": "IP Validator", "difficulty": 1},
    {"id": "lab03", "title": "Hash Checker", "difficulty": 2},
    {"id": "lab04", "title": "Base64 Coder", "difficulty": 2},
    {"id": "lab05", "title": "Port Scanner", "difficulty": 3}
  ]
}
```

---

### Task 10 — lab/utils/terminal.py

Copy verbatim from `aegis/utils/terminal.py`.
No changes needed — same ANSI colors, print helpers, normalize_input.

---

### Task 11 — lab/utils/save_manager.py

Adapt from aegis version. Key changes:
- `_saves_dir()` returns `lab/saves/` (not `aegis/saves/`)
- Remove streak tracking (not needed for lab)
- Remove total_time recompute (keep simple)
- Schema:
```python
{
  "player_name": str,
  "created_at": ISO str,
  "last_played": ISO str,
  "xp": 0,
  "badges": [],
  "completed": [],
  "skipped": [],
  "in_progress": "",
  "hints_used": {},
  "notes": {},
  "metrics": {},
}
```

---

### Task 12 — lab/utils/player.py

Simplified from aegis version.

XP multipliers (same table):
```python
_XP_MULTIPLIERS = {0: 1.0, 1: 0.75, 2: 0.50, 3: 0.25, 4: 0.10}
```

Badge definitions:
```python
_BADGE_LABELS = {
    "first_solve":   "First Solve    -- completed your first script challenge",
    "no_hints":      "No Hints       -- solved a challenge without hints",
    "hint_free_3":   "Clean Coder    -- 3 challenges solved without hints",
    "all_complete":  "Script Master  -- all 5 challenges complete",
}
```

evaluate_badges checks: first_solve (1+ completed), no_hints (this run hints==0),
hint_free_3 (3+ completed with 0 hints), all_complete (5 completed).

---

### Task 13 — lab/engine/challenge_runner.py

The core new piece. Full spec:

```python
"""challenge_runner.py — LAB CyberForge Script Lab

Runs the interactive loop for a single coding challenge.
Commands: run, learn, hint, notes, note, skip, menu, quit
"""
```

**Key functions:**

`load_challenge(challenge_id)` — loads JSON from content/challenges/

`_workspace_dir()` — returns abs path to lab/workspace/

`_fixtures_dir()` — returns abs path to lab/content/fixtures/

`_setup_workspace(challenge_data)`:
  - Creates workspace/ if not exists
  - Writes solution.py with challenge_data["starter_code"]
  - Copies each file in challenge_data["fixtures"] from fixtures/ to workspace/

`_run_solution(workspace, timeout=10)` -> (stdout: str, stderr: str, returncode: int):
  - subprocess.run([sys.executable, "solution.py"], cwd=workspace, timeout=10)
  - Returns ("", traceback_str, 1) on TimeoutExpired

`_normalize(output: str)` -> list[str]:
  - splitlines(), rstrip() each, strip trailing empty lines

`_validate(actual_output, expected_output)` -> (passed: bool, diff_lines: list[str]):
  - Normalize both
  - Compare line by line
  - Return passed=True if identical
  - diff_lines: up to 5 mismatched pairs formatted as:
    "  Expected: <expected line>"
    "  Got:      <actual line>"
    "+ X more lines differ" if > 5 mismatches

`_start_test_server(port)` -> threading.Event:
  - Starts a background TCP server on 127.0.0.1:port
  - Returns stop_event (call stop_event.set() to shut it down)
  - Server accepts and immediately closes connections
  - Uses SO_REUSEADDR

`_stop_test_server(stop_event)`:
  - stop_event.set()
  - Small sleep (0.1s) to let thread exit cleanly

`display_intro(challenge_data)`:
  - clear_screen()
  - Print title, difficulty stars
  - Print scenario
  - Print challenge
  - Print divider
  - Print: "Your workspace: lab/workspace/"
  - Print: "Edit solution.py in your editor, then type 'run'."

`_print_help(tool_cmd="run")`:
  - show run, learn, hint, notes, note, skip, menu, quit

`run_challenge(challenge_id, save_data)` -> save_data:
  - Main loop
  - On "run" command:
    1. Check if test_server_port in challenge_data → start server
    2. Run _run_solution()
    3. Stop server if started
    4. If returncode != 0: show stderr (traceback), prompt fix
    5. If returncode == 0: validate, show pass or diff
    6. If passed: call _handle_correct(), return save_data

`_handle_correct(challenge_id, challenge_data, save_data)`:
  - Calculate XP, award, append to completed
  - Evaluate badges
  - Write save
  - Show debrief screen (summary, real_world, next_step, cert_link, exam_tip)

---

### Task 14 — lab/main.py

Mirrors aegis/main.py structure. Key differences:
- Logo: LAB TERMINAL
- No placement test
- Challenge menu (same layout as aegis case menu)
  - Progress bar, XP, difficulty stars
  - No locking — all challenges available from the start
    (unlike AEGIS where cases are sequential — Lab challenges
     are standalone so player can do them in any order)
- Stats screen (s): XP, badges, completion count
- New game just asks for name, no track selection

---

### Task 15 — Update play.py

Change selector from:
```
[1] CIPHER  — Red Team   (PenTest+)
[2] AEGIS   — Blue Team  (CySA+)
[0] Quit
```
To:
```
[1] CIPHER  — Red Team     (PenTest+)
[2] AEGIS   — Blue Team    (CySA+)
[3] LAB     — Script Lab   (Python automation)
[0] Quit
```

Add choice == "3" → target_dir = "lab" → run lab/main.py.

---

### Task 16 — lab/validate_content.py

Validates:
1. registry.json exists, has "challenges" list
2. For each challenge in registry: JSON file exists
3. Each JSON has all required fields (id, title, difficulty, xp_base, fixtures,
   scenario, challenge, starter_code, expected_output, hints[4], learn, debrief)
4. Debrief has: summary, real_world, next_step, cert_link, exam_tip
5. For each fixture listed in challenge["fixtures"]: file exists in content/fixtures/
6. lab05 expected_output has exactly 11 lines (ports 7000–7010)
7. Print [PASS] or [FAIL] per check, exit 1 if any fail

---

### Task 17 — lab/tests/test_challenge_runner.py

Test classes and cases:

**TestNormalize (3 tests)**
- trailing whitespace stripped
- trailing blank lines stripped
- empty output returns []

**TestValidate (4 tests)**
- identical output → passed=True, no diff
- one line different → passed=False, diff shows it
- extra lines in actual → passed=False
- missing lines in actual → passed=False

**TestRunSolution (3 tests)**
- script that prints "hello" → returncode 0, stdout "hello\n"
- script with syntax error → returncode != 0, stderr contains "SyntaxError"
- script with infinite loop → TimeoutExpired caught, returncode != 0

**TestSetupWorkspace (2 tests)**
- starter_code written to solution.py correctly
- fixture files copied to workspace

Total: 12 tests

---

### Task 18 — Smoke test

Run:
```
python lab/validate_content.py     # expect all PASS
python -m unittest discover lab/tests/   # expect 12 tests OK
python play.py                     # expect [3] LAB appears in menu
```
