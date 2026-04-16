# tasks.md — CIPHER Stage 3: Operations 06-08
<!--
GENERATED from specs/cipher-stage3/plan.md + spec.md
Each task: <30 min | "done when" verifiable in <1 min | one commit
-->

**Source plan:** `specs/cipher-stage3/plan.md`
**Date:** 2026-04-11
**Total tasks:** 7

---

## Phase 1: Tool Functions

### TASK-S3-01: Add dir_enumerator to utils/tools.py
- **Files:** `cipher/utils/tools.py`
- **Depends on:** None
- **Done when:** `python -c "from utils.tools import run_tool; out = run_tool('dir_enumerator', 'http://203.0.113.47:8080'); print('/backup' in out and 'http://203.0.113.47:8080' in out)"` prints `True`
- **Prompt for coding LLM:**
  ```
  Read CONSTITUTION.md §4 (stdlib allowlist) and
  specs/cipher-stage3/spec.md §5 (dir_enumerator signature) and §9
  (op06 Tools Output).
  Add to cipher/utils/tools.py:
  - Register "dir_enumerator" in the run_tool() dispatch dict
  - dir_enumerator(target_url: str) -> str
    Return hardcoded simulated gobuster-style directory scan output.
    Output HEADER must include target_url dynamically:
    "DIR ENUMERATOR — target: {target_url}"
    Path table must be hardcoded as shown in spec §9 op06.
    /backup must appear with [Status: 200].
    Final line: "Scan complete. 7 paths found. 1 potentially sensitive
    path identified."
  Type hints and docstring required. stdlib only.
  ```

---

### TASK-S3-02: Add sqli_tester to utils/tools.py
- **Files:** `cipher/utils/tools.py`
- **Depends on:** TASK-S3-01
- **Done when:** `python -c "from utils.tools import run_tool; out = run_tool('sqli_tester', \"admin' --\"); print('LOGIN BYPASSED' in out)"` prints `True`
- **Prompt for coding LLM:**
  ```
  Read specs/cipher-stage3/spec.md §5 (sqli_tester signature) and §9
  (op07 Tools Output).
  Add to cipher/utils/tools.py:
  - Register "sqli_tester" in the run_tool() dispatch dict
  - sqli_tester(payload: str) -> str
    Show the simulated SQL query construction using the payload.
    Format:
      SQL INJECTION TESTER — target: /backup/report-login

      Payload: {payload}

      Constructing query with payload in username field:
        SELECT * FROM users WHERE username='{payload}' AND password=''

      Query sent to database:
        SELECT * FROM users WHERE username='admin'
        [Everything after -- is treated as a comment and ignored]

      Result: LOGIN BYPASSED
        Returned row: {id: 1, username: 'admin', role: 'superuser'}

      Authentication bypass successful.
      Password check was never evaluated.
    The constructed query line must show the raw payload inserted.
    The "Query sent to database" line always shows the comment-stripped
    version (hardcoded for the NexusCorp scenario).
  Type hints and docstring required. stdlib only.
  ```

---

### TASK-S3-03: Add suid_scanner to utils/tools.py
- **Files:** `cipher/utils/tools.py`
- **Depends on:** TASK-S3-02
- **Done when:** `python -c "from utils.tools import run_tool; out = run_tool('suid_scanner', '/usr/bin'); print('python3.10' in out and '/usr/bin' in out and 'FLAGGED' in out)"` prints `True`
- **Prompt for coding LLM:**
  ```
  Read specs/cipher-stage3/spec.md §5 (suid_scanner signature) and §9
  (op08 Tools Output).
  Add to cipher/utils/tools.py:
  - Register "suid_scanner" in the run_tool() dispatch dict
  - suid_scanner(search_path: str) -> str
    Output header must include search_path dynamically:
    "SUID SCANNER — scanning: {search_path}"
    "Running: find {search_path} -perm -4000 -type f"
    Results table must be hardcoded as shown in spec §9 op08.
    python3.10 must be marked *** FLAGGED: in GTFOBins ***
    Final lines must include the GTFOBins URL and exploit command.
  Type hints and docstring required. stdlib only.
  ```

---

## Phase 2: Operation JSON Files

### TASK-S3-04: Create op06.json, op07.json, op08.json
- **Files:** `cipher/content/operations/op06.json`,
  `cipher/content/operations/op07.json`,
  `cipher/content/operations/op08.json`
- **Depends on:** TASK-S3-01 through TASK-S3-03
- **Done when:** `python validate_content.py` exits 0 and prints [PASS]
  for op01.json through op08.json
- **Prompt for coding LLM:**
  ```
  Read docs/DATA_MODEL.md §2 (full JSON content schema including
  challenge_data field and tools_type allowlist) and
  specs/cipher-stage3/spec.md §4 (canonical JSON structure) and §9
  (full content for op06-op08).

  Create all three files. Critical requirements:
  - challenge_data exact values:
      op06: "http://203.0.113.47:8080"
      op07: "admin' --"
      op08: "/usr/bin"
  - valid_answers (all lowercase, normalized):
      op06: ["/backup", "/backup/"]
      op07: ["admin --", "admin'--", "admin' --"]
      op08: ["python3", "python3.10"]
  - difficulty: op06=3, op07=3, op08=4
  - xp_base: op06=200, op07=200, op08=250
  - tools_type: op06="dir_enumerator", op07="sqli_tester",
    op08="suid_scanner"
  - hints: exactly 4 strings per op, escalating order as in spec §9
  - debrief: object with summary, real_world, next_step, cert_link
  - op08 debrief must explicitly close the NexusCorp arc
  Use \n for newlines within string values. No literal newlines in JSON.
  ```

---

## Phase 3: Registry Update

### TASK-S3-05: Update content/registry.json
- **Files:** `cipher/content/registry.json`
- **Depends on:** TASK-S3-04
- **Done when:** `python -c "import json; r=json.load(open('content/registry.json')); print(len(r['operations']))"` prints `8`
- **Prompt for coding LLM:**
  ```
  Read docs/DATA_MODEL.md §5 (registry.json schema and required fields).
  Update cipher/content/registry.json to add op06-op08 to the operations
  array in order after op05. Each entry requires:
    id, title, status, difficulty, cert_objective
  Values:
    op06: title="Hidden Paths", status="active", difficulty=3,
          cert_objective="PenTest+ PT0-003 Domain 2 — Reconnaissance"
    op07: title="Injection Point", status="active", difficulty=3,
          cert_objective="PenTest+ PT0-003 Domain 3 — Attacks and Exploits"
    op08: title="Root Access", status="active", difficulty=4,
          cert_objective="PenTest+ PT0-003 Domain 3 — Attacks and Exploits"
  Do not change the version field, existing operations, or cases array.
  ```

---

## Phase 4: Validation

### TASK-S3-06: Run full validation suite
- **Files:** None (testing only)
- **Depends on:** TASK-S3-05
- **Done when:** All three commands exit 0 with no failures
- **Prompt for coding LLM:**
  ```
  Run the following from cipher/ and report pass/fail for each:
  1. python validate_content.py
     Expected: [PASS] for op01-op08, placement_test, registry
  2. python check_imports.py
     Expected: [PASS] for all files in engine/ and utils/
  3. python -m unittest discover tests/
     Expected: all green, 0 failures
  For any failure: report the exact error and which task to revisit.
  Do NOT fix failures here — report only.
  ```

---

### TASK-S3-07: Automated end-to-end check for op06
- **Files:** None (testing only) — update tasks.md progress tracker
- **Depends on:** TASK-S3-06
- **Done when:** All assertions pass with no errors
- **Prompt for coding LLM:**
  ```
  Run the following checks from cipher/ and report pass/fail for each:

  1. load_operation('op06') returns title "Hidden Paths"
  2. op06 challenge_data == "http://203.0.113.47:8080"
  3. len(op06 hints) == 4
  4. run_tool('dir_enumerator', 'http://203.0.113.47:8080') contains
     '/backup' and 'http://203.0.113.47:8080'
  5. check_answer('/backup', op06 valid_answers) returns True
  6. check_answer('/BACKUP/', op06 valid_answers) returns True (normalized)
  7. check_answer('wrongpath', op06 valid_answers) returns False
  8. All 4 debrief subfields present in op06
  9. registry.json has 8 operations in order op01-op08
  10. calculate_xp(200, 0) == 200
  11. calculate_xp(200, 4) == 20

  Report each as PASS or FAIL with the actual value on failure.
  ```

---

## Progress Tracker

| Task | Description | Phase | Status | Commit |
|------|-------------|-------|--------|--------|
| TASK-S3-01 | dir_enumerator tool | 1 | ⬜ | |
| TASK-S3-02 | sqli_tester tool | 1 | ⬜ | |
| TASK-S3-03 | suid_scanner tool | 1 | ⬜ | |
| TASK-S3-04 | op06-op08 JSON files | 2 | ⬜ | |
| TASK-S3-05 | registry.json update | 3 | ⬜ | |
| TASK-S3-06 | Full validation suite | 4 | ⬜ | |
| TASK-S3-07 | End-to-end op06 check | 4 | ⬜ | |
