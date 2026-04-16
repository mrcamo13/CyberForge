# tasks.md — CIPHER Stage 2: Operations 02-05
<!--
GENERATED from specs/cipher-stage2/plan.md + spec.md
Each task: <30 min | "done when" verifiable in <1 min | one commit
-->

**Source plan:** `specs/cipher-stage2/plan.md`
**Date:** 2026-04-11
**Total tasks:** 8

---

## Phase 1: Tool Functions

### TASK-S2-01: Add base64_decoder to utils/tools.py
- **Files:** `cipher/utils/tools.py`
- **Depends on:** None
- **Done when:** `python -c "from utils.tools import run_tool; print(run_tool('base64_decoder', 'ZGVwbG95bWFzdGVy'))"` prints `deploymaster`
- **Prompt for coding LLM:**
  ```
  Read CONSTITUTION.md §4 (stdlib allowlist) and
  specs/cipher-stage2/spec.md §5 (tool function signatures) and §9
  (op02 Tools Output).
  Add to cipher/utils/tools.py:
  - Register "base64_decoder" in the run_tool() dispatch dict
  - base64_decoder(text: str) -> str
    Decode the Base64 input string using stdlib base64 module.
    Return formatted output:
      BASE64 DECODER
      Input:  {input}
      Output: {decoded}
      
      Decoded successfully. Input was valid Base64.
    If input is invalid Base64: return error message instead of crashing.
  Type hints and docstring required.
  ```

---

### TASK-S2-02: Add port_scanner to utils/tools.py
- **Files:** `cipher/utils/tools.py`
- **Depends on:** TASK-S2-01
- **Done when:** `python -c "from utils.tools import run_tool; out = run_tool('port_scanner', '203.0.113.47'); print('8080' in out and '203.0.113.47' in out)"` prints `True`
- **Prompt for coding LLM:**
  ```
  Read specs/cipher-stage2/spec.md §5 (port_scanner signature) and §9
  (op03 Tools Output — note {target} is replaced dynamically).
  Add to cipher/utils/tools.py:
  - Register "port_scanner" in the run_tool() dispatch dict
  - port_scanner(target: str) -> str
    Return hardcoded simulated nmap -sV output.
    The output HEADER must include the target value dynamically:
    "PORT SCANNER — target: {target}"
    Port table must be hardcoded as shown in spec §9 op03.
    Port 8080/tcp must appear as open with service "http-alt".
  Type hints and docstring required. stdlib only.
  ```

---

### TASK-S2-03: Add log_analyzer to utils/tools.py
- **Files:** `cipher/utils/tools.py`
- **Depends on:** TASK-S2-02
- **Done when:** `python -c "from utils.tools import run_tool; out = run_tool('log_analyzer', '10.0.0.15 - - [test] \"GET /admin/dashboard HTTP/1.1\" 200 100'); print('[MATCH]' in out)"` prints `True`
- **Prompt for coding LLM:**
  ```
  Read specs/cipher-stage2/spec.md §5 (log_analyzer signature) and §9
  (op04 Tools Output).
  Add to cipher/utils/tools.py:
  - Register "log_analyzer" in the run_tool() dispatch dict
  - log_analyzer(log_snippet: str) -> str
    Parse the log_snippet string (newline-separated log entries).
    Split on \n to get individual lines.
    Separate lines into two groups:
      1. MATCH: lines where IP starts with "10." AND status code is "200"
      2. Other: all remaining lines
    Return formatted output:
      LOG ANALYZER — nexuscorp-access.log
      
      Scanning for 200-status requests from internal IPs (10.0.0.x)...
      
      [MATCH] {line}
      ...
      
      Other entries (external IPs or non-200):
      {line}
      ...
      
      Analysis complete. {N} unique internal path(s) with 200 status found.
    Count unique paths in MATCH lines for the summary count.
    Parse status code as the 4th space-separated token after the quoted
    request string (standard Apache/nginx log format).
  Type hints and docstring required. stdlib only.
  ```

---

### TASK-S2-04: Add hash_cracker to utils/tools.py
- **Files:** `cipher/utils/tools.py`
- **Depends on:** TASK-S2-03
- **Done when:** `python -c "from utils.tools import run_tool; out = run_tool('hash_cracker', '5f4dcc3b5aa765d61d8327deb882cf99'); print('MATCH FOUND' in out and 'password' in out)"` prints `True`
- **Prompt for coding LLM:**
  ```
  Read specs/cipher-stage2/spec.md §3 rule 4 (reveal is intentional),
  §5 (hash_cracker signature), and §9 (op05 Tools Output).
  Add to cipher/utils/tools.py:
  - Register "hash_cracker" in the run_tool() dispatch dict
  - hash_cracker(hash_value: str) -> str
    Hardcoded wordlist (at least these 20 words):
    ["admin", "letmein", "welcome", "nexuscorp", "123456",
     "password", "password1", "qwerty", "abc123", "iloveyou",
     "monkey", "dragon", "master", "shadow", "sunshine",
     "princess", "solo", "football", "charlie", "donald"]
    For each word: compute hashlib.md5(word.encode()).hexdigest()
    Print one line per attempt:
    "Testing: {word:<12} -> {hash} [no match]"  or  "[MATCH FOUND]"
    On match: print the full match block (see spec §9 op05 tools output).
    If no match found: print "Hash not found in wordlist."
  Type hints and docstring required. stdlib only.
  ```

---

## Phase 2: Operation JSON Files

### TASK-S2-05: Create op02.json, op03.json, op04.json, op05.json
- **Files:** `cipher/content/operations/op02.json`,
  `cipher/content/operations/op03.json`,
  `cipher/content/operations/op04.json`,
  `cipher/content/operations/op05.json`
- **Depends on:** TASK-S2-01 through TASK-S2-04
- **Done when:** `python validate_content.py` exits 0 and prints [PASS] for
  op01.json through op05.json
- **Prompt for coding LLM:**
  ```
  Read docs/DATA_MODEL.md §2 (full JSON content schema including
  challenge_data field) and specs/cipher-stage2/spec.md §4 (canonical
  JSON structure) and §9 (full content for op02-op05 including exact
  challenge_data values, valid_answers, hints, learn, tools, debrief).
  
  Create all four files using the canonical structure from spec §4.
  Critical requirements:
  - challenge_data must match exactly:
      op02: "ZGVwbG95bWFzdGVy"
      op03: "203.0.113.47"
      op04: the full log snippet string from spec §9 (use \n between lines)
      op05: "5f4dcc3b5aa765d61d8327deb882cf99"
  - valid_answers must be lowercase normalized lists:
      op02: ["deploymaster"]
      op03: ["8080", "port 8080"]
      op04: ["/admin/dashboard", "/admin/dashboard/"]
      op05: ["password"]
  - hints: exactly 4 strings per op, escalating order
  - difficulty: op02=1, op03=2, op04=2, op05=3
  - xp_base: op02=100, op03=150, op04=150, op05=200
  - debrief: object with summary, real_world, next_step, cert_link
  Use \n for newlines within string values. No literal newlines in JSON.
  ```

---

## Phase 3: Registry Update

### TASK-S2-06: Update content/registry.json
- **Files:** `cipher/content/registry.json`
- **Depends on:** TASK-S2-05
- **Done when:** `python -c "import json; r=json.load(open('content/registry.json')); print(len(r['operations']))"` prints `5`
- **Prompt for coding LLM:**
  ```
  Read docs/DATA_MODEL.md §5 (registry.json schema and required fields).
  Update cipher/content/registry.json to add op02-op05 to the operations
  array in order after op01. Each entry requires:
    id, title, status, difficulty, cert_objective
  Values:
    op02: title="Vault Secrets", status="active", difficulty=1,
          cert_objective="PenTest+ PT0-003 Domain 2 — Reconnaissance"
    op03: title="Network Sweep", status="active", difficulty=2,
          cert_objective="PenTest+ PT0-003 Domain 2 — Reconnaissance"
    op04: title="Access Logs", status="active", difficulty=2,
          cert_objective="PenTest+ PT0-003 Domain 2 — Reconnaissance"
    op05: title="Hash Cracker", status="active", difficulty=3,
          cert_objective="PenTest+ PT0-003 Domain 3 — Attacks and Exploits"
  Do not change the version field or the cases array.
  ```

---

## Phase 4: Validation

### TASK-S2-07: Run full validation suite
- **Files:** None (testing only)
- **Depends on:** TASK-S2-06
- **Done when:** All three commands exit 0 with no failures
- **Prompt for coding LLM:**
  ```
  Run the following from cipher/ and report pass/fail for each:
  1. python validate_content.py
     Expected: [PASS] for op01-op05, placement_test, registry
  2. python check_imports.py
     Expected: [PASS] for all files in engine/ and utils/
  3. python -m unittest discover tests/
     Expected: all green, 0 failures
  For any failure: report the exact error. Do NOT fix failures here —
  report only and identify which task to revisit.
  ```

---

### TASK-S2-08: Manual playthrough op02 end-to-end
- **Files:** None (manual testing only) — update tasks.md progress tracker
- **Depends on:** TASK-S2-07
- **Done when:** All items in the checklist below are confirmed working
- **Prompt for coding LLM:**
  ```
  Read specs/cipher-stage2/spec.md §12 (Definition of Done).
  Launch: python main.py --dev
  Test op02 (Vault Secrets) with this checklist:
  1. New Game → create save → reach operation menu → op02 shows [OPEN]
  2. Select op02 → intro narrative displays with "NEXUSCORP" reference
  3. Type 'help' → all 9 commands shown
  4. Type 'learn' → Base64 concept text displays
  5. Type 'tools' → BASE64 DECODER output shows "deploymaster"
  6. Type 'hint' four times → hints escalate correctly, 5th shows no more
  7. Type 'note test' → Note saved
  8. Type 'notes' → note appears
  9. Type wrong answer → Incorrect feedback, returns to prompt
  10. Type 'deploymaster' → XP awarded, debrief displays, returns to menu
  11. op02 shows [DONE] in menu, op03 is now [OPEN]
  12. Quit and relaunch → load save → op02 still shows [DONE]
  Report pass/fail for each item.
  ```

---

## Progress Tracker

| Task | Description | Phase | Status | Commit |
|------|-------------|-------|--------|--------|
| TASK-S2-01 | base64_decoder tool | 1 | ⬜ | |
| TASK-S2-02 | port_scanner tool | 1 | ⬜ | |
| TASK-S2-03 | log_analyzer tool | 1 | ⬜ | |
| TASK-S2-04 | hash_cracker tool | 1 | ⬜ | |
| TASK-S2-05 | op02-op05 JSON files | 2 | ⬜ | |
| TASK-S2-06 | registry.json update | 3 | ⬜ | |
| TASK-S2-07 | Full validation suite | 4 | ⬜ | |
| TASK-S2-08 | Manual playthrough op02 | 4 | ⬜ | |
