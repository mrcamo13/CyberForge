# spec.md — CIPHER Stage 1: Core Engine + Operation 01
<!--
SCOPE: Engine infrastructure + first playable operation.
NOT HERE: Operations 02-05 → cipher-stage2 spec
NOT HERE: Operations 06-08 → cipher-stage3 spec
-->

**Module:** cipher-stage1
**Date:** 2026-04-09
**Status:** ✅ Approved
**Depends on:** Nothing — this is the foundation
**Modifies DATA_MODEL.md:** Yes — add `tools_type` field to JSON content schema (§2)

---

## 1. Purpose & Scope

### What problem does this module solve?
There is no runnable CIPHER game yet. The existing HackSim code does
not follow the new architecture. Stage 1 builds the full engine
skeleton and one complete, playable operation to prove every system
works end-to-end before content is scaled.

### What does this module do?
Builds the CIPHER game engine from scratch in the new JSON-driven
architecture. Delivers a fully playable experience: launch → menu →
new game or load game → op01 (Caesar Cipher) → complete → save → quit.
Every engine system is proven working before Stage 2 adds more content.

### Success Criteria
- [ ] Player can launch with `python main.py` and reach main menu
- [ ] Player can create a new save and choose Red Team or Full Stack track
- [ ] Player can load an existing save and resume at op01
- [ ] Player can take placement test from main menu
- [ ] Player can complete op01 using all commands
- [ ] XP is calculated correctly based on hints used
- [ ] Save persists across quit and relaunch
- [ ] `validate_content.py` passes on all content files
- [ ] `check_imports.py` passes on all Python files

### In Scope
- [ ] main.py — menu router (New Game, Load Game, Placement Test, Quit)
- [ ] utils/terminal.py — ANSI colors, normalize_input, print helpers
- [ ] utils/player.py — XP calculation, badge evaluation, progress
- [ ] utils/save_manager.py — save/load/backup/migration/corruption
- [ ] engine/operation_runner.py — single generic runner, reads ANY operation JSON by ID
- [ ] utils/tools.py — all in-game tool functions (caesar_decoder, etc.)
- [ ] content/operations/op01.json — Caesar Cipher content (NexusCorp universe)
- [ ] content/placement_test.json — placement test questions (see schema §9)
- [ ] content/registry.json — content registry (see schema DATA_MODEL.md §5)
- [ ] validate_content.py — schema validator + SHA-256 checksums
- [ ] check_imports.py — stdlib import auditor
- [ ] main.py handles `--dev` CLI flag to bypass checksum verification

### Out of Scope
- ❌ Operations 02-05 — content only, added in cipher-stage2
- ❌ Settings / About screen — post-MVP
- ❌ Flask web UI — Stage 4
- ❌ Leaderboard — post-MVP

---

## 2. User Stories

### US-CS1-001: New Player Onboarding
**As** a first-time player, **I want** to create a profile and choose
my track, **so that** the game knows where I am in the curriculum.

**Acceptance Criteria:**
- [ ] Main menu shows: New Game / Load Game / Placement Test / Quit
- [ ] New Game prompts for player name (alphanumeric + underscores, max 20 chars)
- [ ] Empty name → "Name cannot be empty." → re-prompt
- [ ] Invalid chars → "Name must be letters, numbers, or underscores only." → re-prompt
- [ ] Player selects track: Red Team / Full Stack only (Blue Team → redirect message)
- [ ] Save file is created immediately after track selection
- [ ] Player is taken to the operation menu after setup

### US-CS1-002: Placement Test
**As** a player with prior knowledge, **I want** to take a placement
test, **so that** I can skip to the right starting point.

**Acceptance Criteria:**
- [ ] Placement test is accessible from main menu
- [ ] Test asks 5 multiple-choice questions covering Red Team foundations
- [ ] Pass (4/5 or 5/5) → unlocks track entry point + awards 50 XP
- [ ] Fail (3/5 or below) → directed to start from op01 with no penalty
- [ ] Result saved to `placement_test` fields in save file
- [ ] Test is one-time only — cannot be retaken once attempted

### US-CS1-003: Playing an Operation
**As** a player, **I want** to work through op01 using real commands,
**so that** I learn the Caesar cipher technique by doing it.

**Acceptance Criteria:**
- [ ] Intro narrative displays on operation launch
- [ ] All 9 commands work: help, learn, tools, hint, notes, note, skip, menu, quit
- [ ] Command parsing follows strict priority: exact → args → answer
- [ ] Wrong answer → feedback message → return to prompt (no help menu)
- [ ] Correct answer → XP awarded → debrief displayed → return to menu
- [ ] Hints tracked — each hint used reduces XP at completion
- [ ] Ctrl+C at any point returns to main menu cleanly

### US-CS1-004: Save and Resume
**As** a player, **I want** my progress to persist, **so that** I can
quit and continue later without losing anything.

**Acceptance Criteria:**
- [ ] Progress saves automatically on `menu` and `quit` commands
- [ ] Backup save written alongside every primary save
- [ ] Load Game shows list of existing save files with last played date
- [ ] Loading a save resumes at `in_progress` operation
- [ ] Corrupted save → renamed to `.corrupted.json` → new save created
- [ ] If primary corrupted, backup loaded silently

---

## 3. Business Rules

1. **Command priority is strict** — exact command match checked first,
   then `note [text]`, then answer fallback. No exceptions.
   - Step 1 & 2 handle all recognized command patterns
   - Step 3 (answer fallback) catches ALL remaining input — there is
     no "unknown command" at step 3; everything becomes an answer attempt
   - CONSTITUTION §3 rule 7 ("unknown commands print help menu") applies
     only if future commands are added that partially match but fail —
     in Stage 1 this path does not exist; step 3 catches everything
2. **Wrong answer never shows help menu** — prints one feedback line
   ("Incorrect. Try again, or type 'hint' for help."), returns to
   challenge prompt immediately.
3. **XP calculated at completion only** — hints_used count is tracked
   during the operation but XP is not awarded until correct answer.
4. **Skipped ops earn no XP** — XP is only awarded on completion.
   If completed later, full XP awarded based on hints used at that time.
5. **Save on every exit and completion** — save is triggered: (a) on
   correct answer after XP is awarded, (b) on `skip` command, (c) on
   `menu` command, (d) on `quit` command. Player can never lose progress
   from normal use. See Component Responsibility Map in §5.
6. **Badge evaluation runs after every completion** — Stage 1 evaluates
   only badges achievable with one operation: `first_blood` (first
   completion ever) and `no_hints` (completed with 0 hints used).
   All other badges are skipped until their prerequisite operations exist.
7. **Placement test is optional, one-time** — once taken (pass or fail),
   `placement_test.taken` = true. Cannot be retaken.
8. **Player name is permanent** — set at New Game, never changeable.
9. **CIPHER only allows Red Team or Full Stack** — if a player selects
   Blue Team during New Game, display the following constant (defined
   in main.py, not in JSON):
   "AEGIS is the Blue Team simulator. Run aegis/main.py to start your
   Blue Team track. Returning to track selection..."
   Then return to track selection prompt.
13. **Foundation Track is a curriculum concept, not a Stage 1 gate** —
   PROJECT_FOUNDATION.md describes Foundation Track as the recommended
   learning order. In Stage 1, players choose Red or Full Stack directly.
   Foundation Track content (Security+ modules) is built in a separate
   spec. No Foundation prerequisite is enforced in Stage 1.
14. **`hint` never takes a number argument** — typing `hint` always
   reveals the next unrevealed hint tier in order (1→2→3→4). Players
   cannot jump to a specific hint. Only `note` accepts arguments.
10. **Operation unlock rule** — an operation is locked if the previous
    operation in registry order is not in `completed` AND not in
    `skipped`. The first operation in the registry is always unlocked.
11. **Operation lifecycle** — operation starts (metrics timer begins,
    `in_progress` set in save) when player selects it from the menu.
    Selecting a ✅ completed operation prompts: "Replay this operation?
    XP will not be awarded again. (y/n)". Replay resets `hints_used`
    and `metrics` for that operation only — does NOT remove it from
    `completed`.
12. **Ctrl+C during placement test** — discard all answers, set
    `placement_test.taken = false`, return to main menu cleanly.

---

## 4. Data Model

See `docs/DATA_MODEL.md` — all schemas defined there.

This module creates:
- `cipher/saves/[player_name].json` (player save file)
- `cipher/saves/[player_name].backup.json` (automatic backup)
- `cipher/content/operations/op01.json` (operation content)
- `cipher/content/registry.json` (content registry)
- `cipher/content/checksums.json` (generated by validate_content.py)

---

## 5. Technical Decisions

| Decision | Choice | Why | Alternatives Rejected |
|----------|--------|-----|----------------------|
| Operation runner | Single `engine/operation_runner.py` reads any op JSON by ID | One engine serves all ops — true JSON-driven | op01.py per operation — breaks reuse |
| Tool dispatch | `tools_type` field in JSON → engine calls matching function in `utils/tools.py` | JSON-driven, no hardcoding per op | Hardcoded tool per engine file — breaks Stage 2+ |
| Main menu | Simple numbered input (1/2/3/4) | Zero friction, no library needed | curses menu — adds complexity |
| Save format | JSON flat file | Human readable, debuggable | SQLite — overkill |
| Atomic save | Write to `[name].tmp.json` → verify parses → rename to `[name].json` | Prevents corruption on crash mid-write | Direct write — partial write = corrupted save |
| Checksum | SHA-256 via hashlib | stdlib, fast, reliable | MD5 — weak |
| Screen clear | `os.system('cls' if os.name == 'nt' else 'clear')` | Cross-platform, stdlib | No clear — cluttered output |
| XP calculation | See DATA_MODEL.md §3 — `calculate_xp(xp_base, hints_used)` | Canonical definition in one place | Duplicating formula in spec — risks drift |
| Placement test storage | `content/placement_test.json` — same JSON-driven pattern as operations | Consistent with architecture | Hardcoded in Python — breaks contributor model |

### Standard terminal.py Functions (MANDATORY interface)

All print operations in the game must use these functions.
No raw `print()` with ANSI codes anywhere outside `terminal.py`.

```python
def print_success(msg: str) -> None:
    """Print message in green (correct answers, completions)."""

def print_error(msg: str) -> None:
    """Print message in red (wrong answers, failures)."""

def print_warning(msg: str) -> None:
    """Print message in yellow (hints, alerts, cautions)."""

def print_info(msg: str) -> None:
    """Print message in white (body text, descriptions)."""

def print_muted(msg: str) -> None:
    """Print message in dark gray (timestamps, secondary info)."""

def print_header(msg: str) -> None:
    """Print message in cyan (titles, section headers, prompts)."""

def print_divider() -> None:
    """Print a horizontal rule for section separation."""

def clear_screen() -> None:
    """Clear the terminal. Cross-platform."""
```

### Component Responsibility Map

| Action | Owner | Trigger |
|--------|-------|---------|
| Start metrics timer | `engine/operation_runner.py` | Player selects operation from menu |
| Stop metrics timer | `engine/operation_runner.py` | Correct answer or skip command |
| Increment attempt counter | `engine/operation_runner.py` | Wrong answer submitted |
| Set `hints_maxed = true` | `engine/operation_runner.py` | hints_used reaches 4 |
| Update `in_progress` in save | `utils/save_manager.py` | Called by operation_runner on operation start |
| Award XP + update `completed` | `utils/player.py` | Called by operation_runner on correct answer |
| Evaluate badges | `utils/player.py` | Called immediately after XP is awarded |
| Write backup | `utils/save_manager.py` | Called after every successful primary save |
| Build operation menu | `main.py` | Reads registry.json + save file to compute status |
| Validate content on launch | `main.py` | On startup in production mode only |

### validate_content.py Output & Exit Codes

```
Exit code 0 = all files valid
Exit code 1 = one or more failures

Output format (one line per file):
  [PASS] op01.json
  [FAIL] op01.json — missing field: tools_type
  [FAIL] op01.json — hints must contain exactly 4 items (found 3)

On success: regenerates checksums.json and prints:
  [OK] checksums.json updated — 1 file(s) verified
```

`checksums.json` must be committed alongside any content change.

---

## 6. UI Screens & Navigation

| Screen | Purpose | Key Elements |
|--------|---------|-------------|
| Main Menu | Entry point | ASCII CIPHER logo, 4 options |
| New Game | Profile creation | Name input, track selection |
| Load Game | Resume session | List of save files with last played date |
| Placement Test | Knowledge check | 5 MCQ questions, result + XP |
| Operation Menu | Content selection | List with status icons ✅ ▶ ⏭ 🔒 |
| Operation | Active gameplay | Scenario, challenge prompt, command loop |
| Debrief | Completion screen | XP earned, summary, real-world, next step |

### Navigation Flow
```
Main Menu → New Game → Track Select → Operation Menu → op01 → Debrief
          → Load Game → Operation Menu
          → Placement Test → Operation Menu
          → Quit
```

### In-Operation Command Loop
```
[Intro narrative displayed]
        ↓
[Challenge prompt shown]
        ↓
Player input → normalized → command parsed (strict priority order)
        ↓
  ┌──────────────────────────────────────────┐
  │ Step 1 — Exact command match:            │
  │   help   → show command list             │
  │   learn  → show concept                  │
  │   tools  → run in-game analyzer          │
  │   hint   → reveal next hint              │
  │   notes  → view notes                    │
  │   skip   → mark skipped, go to menu      │
  │   menu   → save + return to menu         │
  │   quit   → save + exit game              │
  │                                          │
  │ Step 2 — Command with arguments:         │
  │   note [text] → save note                │
  │                                          │
  │ Step 3 — Answer fallback:                │
  │   [anything else] → check as answer      │
  │   ✅ Correct → XP + debrief + menu       │
  │   ❌ Wrong   → feedback msg + prompt     │
  └──────────────────────────────────────────┘
```

---

## 7. Edge Cases & Error Handling

| # | Scenario | Expected Behavior | Severity |
|---|----------|-------------------|----------|
| 1 | Player name already exists | "Save file found. Load it instead? (y/n)" | High |
| 2 | Save file corrupted on load | Rename + notify + new save | High |
| 3 | content/registry.json missing | Error message + exit gracefully | High |
| 4 | op01.json fails schema validation | Error message listing missing fields | High |
| 5 | Player presses Ctrl+C mid-operation | Save progress + return to main menu | High |
| 6 | Empty input at challenge prompt | "Please enter a command or your answer." | Medium |
| 7 | `note` typed with no text | "Usage: note [your text here]" | Medium |
| 8 | Player requests hint beyond 4 | "No more hints available. Try 'tools'." | Medium |
| 9 | saves/ directory missing | Create it automatically on first run | Medium |
| 10 | Both save + backup corrupted | Notify player + start fresh | High |
| 11 | Player submits empty name | "Name cannot be empty." → re-prompt | Medium |
| 12 | Player name has invalid characters | "Letters, numbers, and underscores only." → re-prompt | Medium |
| 13 | saves/ directory is read-only | "Cannot write to saves/. Check folder permissions." → exit gracefully | High |
| 14 | Load Game selected with no saves | "No save files found." → redirect to New Game | Medium |
| 15 | Ctrl+C during placement test | Discard answers, set taken = false, return to main menu | High |

---

## 8. Cost & Monitoring

### Cost
| Operation | Cost | Frequency | Monthly |
|-----------|------|-----------|---------|
| Runtime | $0 | Every session | $0 |
| Development | $0 | One-time | $0 |

### Observability
- **SLI 1:** `validate_content.py` exits 0 on every PR
- **SLI 2:** `check_imports.py` exits 0 on every PR
- No production monitoring needed — local game

---

## 9. Content — Operation 01 & Placement Test

### Operation 01 — Caesar Cipher (NexusCorp Universe)

#### Narrative
```
CIPHER TERMINAL v1.0 — SECURE CHANNEL ESTABLISHED

INCOMING TRANSMISSION FROM: GHOST (CIPHER Field Agent)
CLASSIFICATION: PRIORITY ALPHA

Operative. NexusCorp's night-shift sysadmin made a mistake.
Left an unencrypted terminal session open on the external
monitoring node. We intercepted a single string before it closed.

Looks like an encoded access password for the vault system.
Whoever sent it tried to hide it using a Caesar cipher.
Old school. Won't hold up.

Decode the string. Get the password. We move at 0300.

INTERCEPTED STRING: "QHAXVFRUS"

GHOST OUT.
```

#### Challenge
`What is the decoded vault password?`

#### Valid Answers
`["nexuscorp"]`

#### Hints
```
Hint 1: Go to https://gchq.github.io/CyberChef/
        Search "ROT13" and drag it to the Recipe box.
        Paste "QHAXVFRUS" in the Input box.
        Adjust the Amount value until the output is a real word.

Hint 2: Run this in a NEW terminal (not in the game):
        python3 -c "
        msg='QHAXVFRUS'
        for shift in range(26):
            print(shift, ''.join(chr((ord(c)-65-shift)%26+65)
            if c.isupper() else c for c in msg))"
        Look for the shift that produces a recognizable word.

Hint 3: Type 'tools' in the game. The Caesar decoder will
        display all 26 shift results automatically.
        Look for the one that makes a real word.

Hint 4: SPOILER — Caesar cipher with shift 3.
        Q→N, H→E, A→X, X→U, V→S, F→C, R→O, U→R, S→P
        Decoded = NEXUSCORP
        Type: nexuscorp
```

#### Learn Text
```
A Caesar cipher is one of the oldest encryption techniques.
Each letter in the message is shifted a fixed number of
positions in the alphabet. Julius Caesar used a shift of 3.

A→D, B→E, C→F ... Z→C

To decrypt: shift backwards by the same amount.
Q(shift 3 back)=N, H=E, A=X, X=U, V=S ... → NEXUSCORP

Real attackers encounter encoded strings in config files,
environment variables, logs, and memory dumps. Recognizing
encoding schemes (Caesar, Base64, hex, ROT13) and decoding
them quickly is a core reconnaissance skill.
```

#### Tools Type
`"tools_type": "caesar_decoder"`

The engine reads `tools_type` from the JSON and calls
`utils/tools.py → run_tool("caesar_decoder", challenge_data)`.
No tool logic is hardcoded in the engine or operation JSON.

#### Tools Output
```
CAESAR DECODER — trying all 26 shifts on: QHAXVFRUS

Shift 01: PGWWUEQTR
Shift 02: OFVVTDPSQ
Shift 03: NEXUSCORP  ←
Shift 04: MDWTRBNOQ
...
[all 26 results displayed]
```

#### Debrief
```
OPERATION COMPLETE — CIPHER TERMINAL

What you did:
You identified and decoded a Caesar cipher — a substitution
cipher where each letter is shifted by a fixed amount.
Shift 3 backwards turned "QHAXVFRUS" into "NEXUSCORP."

Real world application:
Penetration testers regularly find encoded strings in config
files, environment variables, and intercepted traffic.
Recognizing and decoding these quickly is a core recon skill
that shows up in every real engagement.

Next step — practice with real tools:
TryHackMe: "Crypto 101"
https://tryhackme.com/room/cryptoaddicted

Cert link:
PenTest+ PT0-003 Domain 2 — Reconnaissance:
"Given a scenario, perform passive and active reconnaissance."

XP AWARDED: [calculated at runtime based on hints used]
```

---

### Placement Test — 5 Questions (Red Team Foundation)

#### placement_test.json Schema

```json
{
  "pass_threshold": 4,
  "xp_on_pass": 50,
  "questions": [
    {
      "id": "pt01",
      "question": "Question text here",
      "options": [
        "Option A text",
        "Option B text",
        "Option C text",
        "Option D text"
      ],
      "correct_index": 1
    }
  ]
}
```

`correct_index` is 0-based. Player selects 1-4, engine maps to index 0-3.
`validate_content.py` checks: `pass_threshold` ≤ total questions,
all questions have exactly 4 options, `correct_index` is 0-3.

Pass threshold: 4 out of 5 correct. One attempt only.
Shown in order. No skipping. No going back.

#### Result Display (shown immediately after Q5)
```
PLACEMENT TEST RESULTS
──────────────────────
Score: 4/5

✅ Q1 — Correct
✅ Q2 — Correct
✅ Q3 — Correct
❌ Q4 — Incorrect
   Your answer:    A compressed archive of the original input
   Correct answer: A fixed-length digest that uniquely represents the input
✅ Q5 — Correct

RESULT: PASSED — 50 XP awarded
You have been placed at the Red Team track entry point.

[Press Enter to continue]
```
On fail (≤3/5): same format, no XP line, message reads:
"RESULT: NOT PASSED — Starting from Operation 01. No penalty."

```
Q1. What does a Caesar cipher do?

  1) Encrypts data using a public/private key pair
  2) Shifts each letter a fixed number of positions in the alphabet
  3) Converts text to binary representation
  4) Hashes a password for secure storage

  Correct: 2

──────────────────────────────────────────────────

Q2. What does Base64 encoding do?

  1) Encrypts data so it cannot be read without a key
  2) Compresses data to reduce file size
  3) Converts binary data into ASCII text for safe transport
  4) Hashes data to verify file integrity

  Correct: 3

──────────────────────────────────────────────────

Q3. When a port scan shows a port as "open", what does that mean?

  1) A firewall is actively blocking traffic on that port
  2) A service is listening and accepting connections on that port
  3) The host is offline and not responding to probes
  4) The port has been flagged by an intrusion detection system

  Correct: 2

──────────────────────────────────────────────────

Q4. What does an MD5 hash produce?

  1) An encrypted version of the original data, reversible with a key
  2) A compressed archive of the original input
  3) A fixed-length digest that uniquely represents the input
  4) A Base64-encoded copy of the original input

  Correct: 3

──────────────────────────────────────────────────

Q5. In a web server access log, what does HTTP status 200 mean?

  1) The requested resource was permanently redirected
  2) The client was forbidden from accessing the resource
  3) The request was successful and content was returned
  4) The server encountered an internal processing error

  Correct: 3
```

---

## 10. Open Questions

- [x] Track selection scope — Red Team + Full Stack only in CIPHER
- [x] Placement test in Stage 1 — confirmed: include with defined questions
- [x] op01 content — fresh NexusCorp universe, single-word password answer
- [x] Valid answers — normalized to `["nexuscorp"]`

---

## 11. Pre-Flight Checklist

- [x] Data flow is clear: JSON → engine → terminal output → save
- [x] Component responsibilities assigned (§5 Component Responsibility Map)
- [x] All schemas defined in DATA_MODEL.md including registry + placement_test
- [x] tools_type field defined + allowlist in DATA_MODEL.md
- [x] terminal.py standard functions defined (§5)
- [x] Edge cases documented (§7) — 15 cases covered
- [x] Open questions all resolved (§10)
- [x] No external dependencies introduced
- [x] Content uses approved fictional universe (NexusCorp, CIPHER)
- [x] Valid answers account for normalization via normalize_input()
- [x] XP math references DATA_MODEL.md §3 — no duplication
- [x] Placement test JSON schema defined (§9)
- [x] Placement test result display defined (§9)
- [x] hint command behavior explicit: always next tier, no argument (§3 rule 14)
- [x] Track restriction + Blue Team message defined (§3 rule 9)
- [x] Foundation Track clarified as curriculum concept, not Stage 1 gate (§3 rule 13)
- [x] Operation unlock rule defined (§3 rule 10)
- [x] Operation lifecycle + replay defined (§3 rule 11)
- [x] Save triggers: completion + skip + menu + quit (§3 rule 5)
- [x] Atomic save pattern defined (§5)
- [x] validate_content.py output and exit codes defined (§5)
- [x] --dev flag in scope (§1)
- [x] Badge scope locked to Stage 1 achievable badges (§3 rule 6)
- [x] Unknown command vs wrong answer distinction clarified (§3 rule 1-2)

---

## 12. Definition of Done

- [ ] All tasks in tasks.md marked complete
- [ ] `python main.py` launches without errors on Win/Mac/Linux
- [ ] Full op01 playthrough works end-to-end
- [ ] All 9 commands functional
- [ ] Placement test runs and saves result correctly
- [ ] Save/load/backup/corruption handling all tested
- [ ] `validate_content.py` passes
- [ ] `check_imports.py` passes
- [ ] DATA_MODEL.md unchanged (schemas already defined)
- [ ] PROJECT_FOUNDATION.md doc registry updated
- [ ] This spec status → ✅ Complete
