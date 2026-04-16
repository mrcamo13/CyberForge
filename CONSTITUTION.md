# CONSTITUTION.md — CyberForge
<!--
SCOPE: Immutable rules, constraints, forbidden patterns, product principles.
       Applies to EVERY operation, case, AI agent, and community contributor.
NOT HERE: Project vision/roadmap → docs/PROJECT_FOUNDATION.md
NOT HERE: Module-specific decisions → specs/[module]/spec.md
NOT HERE: Database schemas → docs/DATA_MODEL.md
UPDATE FREQUENCY: Rarely. Only when a fundamental constraint changes.
-->

**Last updated:** 2026-04-09 (rev 2)

---

## 1. Product Principles

1. **Simulate, don't execute** — every operation and case simulates real methodology. No real network calls, no real exploitation. The game teaches the thinking. Real tools are always referenced in the debrief.
2. **Research first** — Hint 1 always points to a real external tool so players learn the ecosystem before getting the answer.
3. **Zero friction** — `python main.py` and it works. No pip, no VPN, no VM, no account, no internet required.
4. **Explain the why** — every operation/case ends with a debrief that connects the mechanic to a real cert objective and real-world context.
5. **Consistency over cleverness** — CIPHER and AEGIS share the same engine patterns, hint structure, and command interface. A contributor who knows one already knows the other.
6. **Community first** — content lives in JSON. Anyone can contribute without knowing Python.

---

## 2. Environment & Infrastructure

### Runtime

| Item | Value |
|------|-------|
| Language | Python 3.8+ |
| OS | Windows / macOS / Linux |
| External dependencies | NONE — stdlib only |
| Project root | `cyberforge/` |
| CIPHER root | `cyberforge/cipher/` |
| AEGIS root | `cyberforge/aegis/` |

### Services

None. Fully local terminal application. No servers, no ports, no internet required at runtime.

---

## 3. Architecture Rules

1. **Pure Python stdlib only** — no `import` of anything outside the Python 3 standard library. Any exception must be justified in a spec and added to the stdlib allowlist in §4.
2. **JSON-driven content** — all operation/case text, hints, answers, and debriefs live in JSON files. Python engine reads JSON. Never hardcode scenario content in Python.
3. **One JSON file per operation/case** — `op01.json`, `case01.json`. No operation imports from another operation.
4. **Shared utils, not shared state** — `terminal.py`, `player.py`, `save_manager.py` are utilities. Game state lives in the save file, never in module-level globals.
5. **Simulated only** — no real network calls, no real file system manipulation outside `saves/` directory.
6. **Input always normalized** — every `input()` response passes through `normalize_input()` before any comparison. Never compare raw input directly to an answer.
7. **Graceful on bad input** — unknown commands print the help menu. Never crash. `KeyboardInterrupt` (Ctrl+C) returns to main menu cleanly. An incorrect answer attempt prints a feedback message and returns to the challenge prompt — it does NOT auto-show the help menu.
8. **Paths always OS-safe** — always use `os.path.join()`. Never hardcode forward slashes or backslashes in file paths.
9. **Centralized JSON validation** — a single `validate_content.py` script in the project root checks every JSON file in `content/` against the required schema. Contributors run it locally before submitting a PR. It must pass before any merge to `main`.
10. **Save file corruption handling** — on every load, validate the save file against the expected schema before using it. If validation fails: a) rename corrupted file to `[name].corrupted.json`, b) notify player: "Save file was corrupted. Starting fresh.", c) create a new save file. Never crash on a bad save file.
11. **Save file backup** — after every successful save, write an identical backup to `saves/[name].backup.json`. If primary save fails to load, attempt backup automatically before notifying player.
12. **Session safety** — progress is saved after every operation/case completion and on every `menu` or `quit` command. Never rely on the player to manually save.
13. **Save migration rules** — if a save file is missing fields due to a version update, migration may ONLY add missing fields with their default values. Migration must NEVER delete or overwrite existing valid data. Log any migration applied to the player at session start.
14. **Content integrity checksums** — `validate_content.py` generates a SHA-256 checksum for each JSON file in `content/` and stores them in `content/checksums.json`. On game launch in production mode, checksums are verified. If a file has been modified outside a PR, the game warns the player and flags the affected operation/case as unverified. Checksum verification is bypassed in development mode (`--dev` flag) so local edits are not flagged during development.

---

## 4. Code Standards

### Python Style

- PEP 8 compliant — enforced for all engine code
- Type hints required on all functions
- Docstrings required on all functions (one-line minimum)
- Max function length: 50 lines — split if longer
- Comments explain *why*, not *what*

### Example function signature

```python
def load_operation(op_id: str) -> dict:
    """Load and return operation data from content/operations/{op_id}.json."""
    ...
```

### Standard Command Set (MANDATORY — every operation and case)

Every operation and case must support ALL of these commands.
No operation may add commands not on this list without a spec update.

| Command | What it does |
|---------|-------------|
| `help` | Show all available commands |
| `learn` | Display concept explanation for this operation/case |
| `tools` | Run the in-game analyzer/decoder for this challenge |
| `hint` | Reveal next hint (tracks count, affects XP) |
| `notes` | View saved notes for this operation/case |
| `note [text]` | Save a note to this operation/case |
| `skip` | Mark operation/case as ⏭ Skipped, return to menu |
| `menu` | Save progress and return to main menu |
| `quit` | Save progress and exit the game |

Answer submission: player types their answer directly at the prompt.
All commands are case-insensitive and stripped before processing.
Unknown input that does not match any command → print help menu. Never crash.
Incorrect answer → print feedback message → return to challenge prompt. Do NOT auto-show help menu.

### Command Parsing Priority (STRICT ORDER — no exceptions)

```
1. Exact command match     → normalize input → check against command list
2. Command with arguments  → check if input starts with "note " (with space)
3. Answer fallback         → only if steps 1 and 2 produce no match
```

This order prevents conflicts such as:
- `help me` → matches exact command `help` at step 1, shows help menu
- `note password123` → matches `note [text]` at step 2, saves note
- `password123` → falls through to step 3, treated as answer attempt

### Input Normalization (MANDATORY — all answer checks)

All player input must pass through `normalize_input()` before comparison. This function lives in `utils/terminal.py` and is the only place input normalization is defined.

```python
def normalize_input(raw: str) -> str:
    """Normalize player input before answer comparison."""
    import re
    # Strip whitespace, lowercase, collapse internal spaces,
    # remove punctuation players commonly add or omit
    normalized = raw.strip().lower()
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r'[^\w\s\.\-\/]', '', normalized)
    return normalized

def check_answer(player_input: str, valid_answers: list) -> bool:
    """Check normalized player input against all valid answer variants."""
    normalized = normalize_input(player_input)
    return normalized in [normalize_input(a) for a in valid_answers]
```

Every JSON content file must include a `valid_answers` list (not a single string) to account for alternate correct inputs.

### Stdlib Allowlist

Only the following stdlib modules may be imported in engine and utils files. Any addition requires a spec justification and a CONSTITUTION update.

```
os, sys, json, re, datetime, pathlib, unittest, hashlib,
base64, collections, itertools, functools, string, time,
random, math, copy, io, textwrap
```

### Import Audit

A `check_imports.py` script in the project root scans all `.py` files in `engine/` and `utils/` and fails if any import is not on the stdlib allowlist above. This script runs on every pull request.

### Hint Structure (MANDATORY — every operation and case)

```python
hints = [
    "Hint 1: [Real tool URL + exact navigation steps to solve this]",
    "Hint 2: [Exact Python one-liner — run in a NEW terminal, not in game]",
    "Hint 3: Use the in-game 'tools' command — [what it reveals here]",
    "Hint 4: SPOILER — [Full answer with explanation of why it works]"
]
```

Rules:
- Hints MUST escalate — each hint reveals more than the last
- Hint 1 must be a real, free, no-login URL with exact steps
- Hint 2 must be a working Python one-liner (tested before submitting)
- Hint 4 must give the full answer — no partial spoilers

### Debrief Structure (MANDATORY — every operation and case)

Every operation/case must end with:
1. What the player did and why it matters
2. Real-world application
3. Where to practice with real tools (TryHackMe/HTB link)
4. AEGIS only: exact CySA+ objective mapped

### File Structure (per game)

```
cipher/  (or aegis/)
├── main.py                      ← entry point, router
├── content/
│   └── operations/              ← JSON content files (or cases/)
│       └── op01.json
├── engine/
│   └── operations/              ← Python engine files
│       └── op01.py
├── utils/
│   ├── terminal.py              ← ANSI colors, print helpers, normalize_input
│   ├── player.py                ← XP, progress, placement test
│   └── save_manager.py          ← JSON save/load only
├── saves/
│   └── [player_name].json
└── tests/
    └── test_op01.py
```

### Git

- **Commits:** `[TASK-XX] short description`
- **Branches:** `feature/[operation-or-case-name]` from `main`
- **Never commit:** `.env`, `__pycache__/`, `*.pyc`, real personal data

---

## 5. CyberForge Universe — Fictional Data Standard

All content must use the approved fictional universe. No real companies, real IPs, or real personal data in any JSON content file.

### Approved Fictional Entities

| Entity | Universe | Role |
|--------|---------|------|
| NexusCorp | CIPHER | Target megacorp being infiltrated |
| CIPHER | CIPHER | Underground hacking group (player's faction) |
| Veridian Systems | AEGIS | Company the SOC analyst works for |

### Approved IP Ranges (RFC 5737 — documentation use only)

| Range | Use |
|-------|-----|
| `192.0.2.x` | Simulated external IPs |
| `198.51.100.x` | Simulated attacker IPs |
| `203.0.113.x` | Simulated target IPs |
| `10.0.0.x` | Simulated internal network |

### Fictional CVE Format

Use `CVE-FAKE-XXXX` format for invented vulnerabilities. Real CVE IDs may be referenced in debriefs for educational context but must be clearly attributed to NVD and never reproduced verbatim.

---

## 6. Testing Requirements

Every pull request that adds or modifies an operation or case must include both:

### A) Schema validation test (unittest)

```python
class TestOp01Schema(unittest.TestCase):
    def test_required_fields(self):
        """Verify op01.json contains all required fields."""
        with open("content/operations/op01.json") as f:
            data = json.load(f)
        required = [
            "id", "title", "track", "cert_objective", "xp_base",
            "difficulty", "scenario", "challenge", "valid_answers",
            "hints", "learn", "tools", "debrief"
        ]
        for field in required:
            self.assertIn(field, data)

    def test_hints_count(self):
        """Verify exactly 4 hints exist."""
        with open("content/operations/op01.json") as f:
            data = json.load(f)
        self.assertEqual(len(data["hints"]), 4)

    def test_valid_answers_is_list(self):
        """Verify valid_answers is a list, not a string."""
        with open("content/operations/op01.json") as f:
            data = json.load(f)
        self.assertIsInstance(data["valid_answers"], list)
```

### B) Manual playthrough checklist (in PR description)

- [ ] Ran the operation/case start to finish
- [ ] Tested wrong answer — feedback message shown, returned to challenge prompt, no crash
- [ ] Tested all 4 hints in order — each escalates correctly
- [ ] Tested `learn` command — displays concept explanation
- [ ] Tested `tools` command — displays in-game helper
- [ ] Tested correct answer — XP awarded, debrief displayed
- [ ] Tested Ctrl+C — returns to main menu cleanly
- [ ] Tested save/load — progress persists after quit and reload
- [ ] All fictional data uses approved universe (§5)
- [ ] Cert objective verified against official CompTIA exam objectives
- [ ] `validate_content.py` passes locally
- [ ] `check_imports.py` passes locally
- [ ] Doc registry updated in `PROJECT_FOUNDATION.md`

Tests run with: `python -m unittest discover tests/`
All tests must pass before merge to `main`.

---

## 7. Cost Guardrails

- **Runtime cost:** $0 — no external API calls
- **Future NVD API (post-MVP):** Free tier only, rate limit 5 req/30s
- No LLM API calls inside the game at runtime — ever

---

## 8. Forbidden Patterns

- ❌ **ANSI codes hardcoded outside `terminal.py`** — causes drift across 20+ files when color scheme changes
- ❌ **Hint logic copy-pasted per operation/case** — hint engine is shared, reads from JSON, never duplicated
- ❌ **Save logic outside `save_manager.py`** — all save file I/O goes through one module only
- ❌ **Global mutable state in engine files** — breaks replay and save/load; all state lives in save file
- ❌ **Functions over 50 lines** — split into single-responsibility functions
- ❌ **Hints that don't escalate** — if Hint 2 gives the answer, the system breaks; each hint must reveal more than the last
- ❌ **Single-string answer validation** — always use `valid_answers` list; always normalize before comparing
- ❌ **Raw `input()` compared directly to answer** — always pass through `normalize_input()` first
- ❌ **Unverified cert objectives** — cross-check against official CompTIA exam objectives before submitting
- ❌ **`sys.exit()` inside an operation or case** — operations return to `main.py`; they never terminate the process
- ❌ **Bare `input()` without try/except** — always catch `KeyboardInterrupt` and return to menu cleanly
- ❌ **Hardcoded file paths with slashes** — always use `os.path.join()`
- ❌ **Real CVE descriptions copy-pasted without attribution** — reference NVD with a link; do not reproduce verbatim
- ❌ **Real personal data in JSON content** — names, IPs, companies must all be from the approved fictional universe (§5)
- ❌ **Third-party imports** — any module not on the stdlib allowlist (§4) is forbidden
- ❌ **Skipping `validate_content.py` or `check_imports.py`** — both must pass locally before submitting a PR
- ❌ **Modifying content JSON files without regenerating checksums** — run `validate_content.py` after any content change; checksums.json must be committed alongside the content change
- ❌ **Treating an incorrect answer as an unknown command** — wrong answers show a feedback message and return to the challenge prompt; they never trigger the help menu

---

## 9. Documentation Rules

1. Every doc in `PROJECT_FOUNDATION.md §Doc Registry` — unregistered docs don't exist
2. Reference, never copy — use "See [DOC.md §section]" format
3. One concept, one location — if it's in two places, merge them
4. No code in docs — specs describe intent, code lives in `engine/`
5. Spec before code — no new operation/case without an approved spec
6. Lessons are mandatory — every significant issue gets a LL entry

### When to write a Lesson Learned

- Any bug that took >30 minutes to find
- Any operation/case that had to be redesigned after playtesting
- Any hint that players consistently got stuck on (balance issue)
- Any Python stdlib limitation that forced a workaround
- Any community PR that introduced a forbidden pattern

---

## 10. For AI Agents (CLAUDE.md content)

```markdown
# CLAUDE.md — CyberForge

## Before ANY implementation

1. Read CONSTITUTION.md — especially §3, §4, §5, §8
2. Read docs/PROJECT_FOUNDATION.md §7 (progression) and §10 (structure)
3. Read specs/[module]/spec.md
4. Read specs/[module]/plan.md
5. Identify which TASK-XX you are implementing — ONE task at a time

## Non-negotiable rules

- Pure Python 3.8+ stdlib only — only modules on the allowlist in §4
- ANSI colors from utils/terminal.py only — never inline
- All content in JSON files — never hardcode scenario text in Python
- All save I/O through save_manager.py only
- All answers validated via valid_answers list + normalize_input()
- Every operation/case: hints (4 tiers), learn, tools, XP, debrief
- os.path.join() for all file paths — never hardcoded slashes
- Ctrl+C always returns to menu — never crashes
- Run validate_content.py and check_imports.py before marking task done

## Forbidden (from §8)

- ❌ Third-party imports or anything outside stdlib allowlist
- ❌ ANSI codes outside terminal.py
- ❌ Save logic outside save_manager.py
- ❌ Global mutable state
- ❌ Functions over 50 lines
- ❌ sys.exit() inside operations or cases
- ❌ Bare input() without KeyboardInterrupt handling
- ❌ Raw input compared directly to answer string
- ❌ Hardcoded file paths

## Per task

- Implement ONE task at a time
- Run tests after each: python -m unittest discover tests/
- Commit: [TASK-XX] description
- Fails 2x: STOP and report — do not force it
- Ambiguous requirement: ASK, do not assume
```

---

## Change Log

| Date | Section | Change | Reason |
|------|---------|--------|--------|
| 2026-04-09 | All | Initial version | Project kickoff |
| 2026-04-09 | §3,§4,§8 | Added centralized JSON validator, import audit, enhanced input normalization | LLM review recommendations |
| 2026-04-09 | §3,§4,§8 | Added command set, command parsing priority, failure loop, save rules 10-14, checksum dev mode, metrics triggers, xp_base standardization | LLM gate check corrections |
