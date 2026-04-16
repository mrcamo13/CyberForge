# DATA_MODEL.md — CyberForge
<!--
SCOPE: All save file schemas, JSON content schemas, and XP system.
NOT HERE: Game logic → engine/
NOT HERE: Vision/roadmap → docs/PROJECT_FOUNDATION.md
NOT HERE: Rules → CONSTITUTION.md
-->

**Last updated:** 2026-04-09 (rev 2)

---

## 1. Player Save File

One JSON file per player per game.
Location: `cipher/saves/[player_name].json`
          `aegis/saves/[player_name].json`

```json
{
  "player_name": "string",
  "track": "red | blue | full",
  "created_at": "2026-04-09T14:00:00Z",
  "last_played": "2026-04-09T14:00:00Z",
  "total_time_played_seconds": 0,
  "streak": {
    "current": 0,
    "longest": 0,
    "last_played_date": "2026-04-09"
  },
  "xp": 0,
  "placement_test": {
    "taken": false,
    "passed": false,
    "track_unlocked": "none | red | blue | full",
    "xp_awarded": 0
  },
  "badges": [],
  "completed": [],
  "skipped": [],
  "in_progress": "op01",
  "hints_used": {
    "op01": 0,
    "op02": 0
  },
  "notes": {
    "op01": ["string", "string"]
  },
  "metrics": {
    "op01": {
      "attempts": 0,
      "hints_maxed": false,
      "completed": false,
      "time_spent_seconds": 0
    }
  }
}
```

### Field Rules

| Field | Type | Rules |
|-------|------|-------|
| `player_name` | string | Alphanumeric + underscores, max 20 chars |
| `track` | string | Must be `"red"`, `"blue"`, or `"full"` |
| `created_at` | string | UTC, ISO-8601 — set once, never updated |
| `last_played` | string | UTC, ISO-8601 — updated on every session end |
| `total_time_played_seconds` | integer | Cumulative, never decremented |
| `streak.current` | integer | Days in a row with at least one completion |
| `streak.last_played_date` | string | Date only `YYYY-MM-DD` — used to calculate streak |
| `xp` | integer | Cumulative, never decremented |
| `placement_test.taken` | boolean | True once test is attempted, even if skipped |
| `badges` | array | List of badge ID strings |
| `completed` | array | List of operation/case ID strings (e.g. `"op01"`) |
| `skipped` | array | List of IDs marked ⏭ Skipped — separate from completed |
| `in_progress` | string | Current active operation/case ID |
| `hints_used` | object | Key = ID, value = integer 0-4 |
| `notes` | object | Key = ID, value = array of strings |
| `metrics.[id].attempts` | integer | Increments on every incorrect answer submission |
| `metrics.[id].hints_maxed` | boolean | Set to true when hint count reaches 4 |
| `metrics.[id].completed` | boolean | Set to true on correct answer (not on skip) |
| `metrics.[id].time_spent_seconds` | integer | Starts when operation/case loads, stops on completion or skip |

---

## 2. JSON Content Schema

### CIPHER — Operation File (`content/operations/op01.json`)

```json
{
  "id": "op01",
  "title": "Caesar Cipher",
  "track": "red",
  "cert_objective": "PenTest+ Domain 2 — Reconnaissance",
  "xp_base": 100,
  "difficulty": 1,
  "tools_type": "caesar_decoder",
  "scenario": "Narrative intro text shown at operation start.",
  "challenge": "What the player must figure out or solve.",
  "valid_answers": ["answer1", "alternate answer", "also correct"],
  "hints": [
    "Hint 1: Real tool URL + exact steps to use it for this challenge.",
    "Hint 2: Python one-liner — run this in a NEW terminal: python3 -c '...'",
    "Hint 3: Use the in-game 'tools' command — it will decode the string for you.",
    "Hint 4: SPOILER — The answer is X because Y. Here is exactly how to get it."
  ],
  "learn": "Concept explanation — what this technique is and how it works.",
  "tools": "Description of what the in-game tools command does for this operation.",
  "debrief": {
    "summary": "What you did and why it matters in a real engagement.",
    "real_world": "How this technique is used in real penetration tests.",
    "next_step": "Practice with real tools: [TryHackMe/HTB room name and URL]",
    "cert_link": "This maps to PenTest+ Objective X.X: [objective name]"
  }
}
```

### AEGIS — Case File (`content/cases/case01.json`)

Same schema as above with these differences:

```json
{
  "id": "case01",
  "track": "blue",
  "cert_objective": "CySA+ CS0-003 Objective 1.1 — ...",
  "debrief": {
    "summary": "...",
    "real_world": "...",
    "next_step": "Practice with real tools: [TryHackMe/HTB room name and URL]",
    "cert_link": "This maps to CySA+ CS0-003 Objective X.X: [objective name]",
    "exam_tip": "On the exam, questions about this topic often test whether you..."
  }
}
```

AEGIS cases include an `exam_tip` field. CIPHER operations do not.

### tools_type Allowlist

The `tools_type` field must be one of the following registered values.
New tool types require a spec update before being added.

| tools_type value | Tool | Used in |
|-----------------|------|---------|
| `caesar_decoder` | Tries all 26 Caesar shifts | op01 |
| `base64_decoder` | Decodes Base64 string | op02 |
| `port_scanner` | Simulates port scan output | op03 |
| `log_analyzer` | Parses simulated web server log | op04 |
| `hash_cracker` | MD5 dictionary attack simulator | op05 |
| `dir_enumerator` | Simulates gobuster-style directory scan | op06 |
| `sqli_tester` | Simulates SQL injection payload test | op07 |
| `suid_scanner` | Simulates find -perm -4000 SUID scan | op08 |

### Required Fields (validated by `validate_content.py`)

| Field | Required in CIPHER | Required in AEGIS |
|-------|-------------------|-------------------|
| `id` | ✅ | ✅ |
| `title` | ✅ | ✅ |
| `track` | ✅ | ✅ |
| `cert_objective` | ✅ | ✅ |
| `xp_base` | ✅ | ✅ |
| `scenario` | ✅ | ✅ |
| `challenge` | ✅ | ✅ |
| `valid_answers` | ✅ list, min 1 item | ✅ list, min 1 item |
| `hints` | ✅ exactly 4 items | ✅ exactly 4 items |
| `learn` | ✅ | ✅ |
| `tools` | ✅ | ✅ |
| `debrief.summary` | ✅ | ✅ |
| `debrief.real_world` | ✅ | ✅ |
| `debrief.next_step` | ✅ | ✅ |
| `difficulty` | ✅ integer 1–4 | ✅ integer 1–4 |
| `tools_type` | ✅ string (see allowlist) | ✅ string (see allowlist) |
| `debrief.cert_link` | ✅ | ✅ |
| `debrief.exam_tip` | ❌ | ✅ |

### Save Error Handling

| Scenario | Behavior |
|----------|---------|
| Save file not found | Create new save, start fresh |
| Save file corrupted (invalid JSON) | Rename to `[name].corrupted.json`, create new save, notify player |
| Save file missing required fields | Run migration — add missing fields with defaults only, never delete existing data, notify player |
| Backup exists, primary corrupted | Load backup silently, notify player |
| Both files corrupted | Create new save, notify player |

---

## 3. XP System

### XP Award Table

| Event | XP Awarded |
|-------|-----------|
| Complete with 0 hints used | 100 XP |
| Complete with 1 hint used | 75 XP |
| Complete with 2 hints used | 50 XP |
| Complete with 3 hints used | 25 XP |
| Complete with 4 hints used (spoiler) | 10 XP |
| Skipped → completed later | Full XP based on hints used at completion |
| Placement test passed | 50 XP per track unlocked |

### XP Calculation

```python
def calculate_xp(xp_base: int, hints_used: int) -> int:
    """Calculate XP awarded based on hints used during completion."""
    multipliers = {0: 1.0, 1: 0.75, 2: 0.50, 3: 0.25, 4: 0.10}
    return int(xp_base * multipliers.get(hints_used, 0.10))
```

`xp_base` comes from the JSON content file. Default is 100.
Advanced operations/cases may have higher `xp_base` values.

---

## 4. Badge System

| Badge ID | Awarded When |
|----------|-------------|
| `first_blood` | Complete first operation/case |
| `no_hints` | Complete any single operation/case with 0 hints |
| `ghost` | Complete an entire track with 0 hints across all operations/cases |
| `ghost_red` | Complete Red Team track with 0 hints |
| `ghost_blue` | Complete Blue Team track with 0 hints |
| `ghost_full` | Complete both tracks with 0 hints |
| `perfect_run` | Complete 5 in a row with 0 hints |
| `streak_7` | 7-day streak |
| `streak_30` | 30-day streak |
| `red_team` | Complete Red Team track |
| `blue_team` | Complete Blue Team track |
| `full_stack` | Complete both tracks |
| `placement_ace` | Pass placement test for a track |

### Badge Evaluation Rules

- Badges are evaluated at the end of every operation/case completion
- `ghost_red` / `ghost_blue` / `ghost_full` require ALL operations/cases
  in that track to have `hints_used = 0` — checked across entire save file
- A badge is never awarded twice — check `badges` array before awarding
- Badges are stored as strings in the player save file `badges` array

---

## 5. Content Registry File

A single `content/registry.json` tracks all available operations and cases.
The engine reads this to build the menu — never hardcode the list in Python.

```json
{
  "version": "1.0",
  "operations": [
    {
      "id": "op01",
      "title": "Caesar Cipher",
      "status": "active",
      "difficulty": 1,
      "cert_objective": "PenTest+ Domain 2"
    },
    {
      "id": "op02",
      "title": "Base64 Decoding",
      "status": "active",
      "difficulty": 1,
      "cert_objective": "PenTest+ Domain 2"
    }
  ],
  "cases": [
    {
      "id": "case01",
      "title": "Vulnerability Scan Triage",
      "status": "active",
      "difficulty": 1,
      "cert_objective": "CySA+ CS0-003 Objective 1.1"
    }
  ]
}
```

### Registry Required Fields (validated by `validate_content.py`)

| Field | Type | Rules |
|-------|------|-------|
| `version` | string | Semantic version string |
| `operations` | array | Min 0 items, each must have all required fields |
| `operations[].id` | string | Must match an existing JSON file in `content/operations/` |
| `operations[].title` | string | Non-empty |
| `operations[].status` | string | Must be `"active"`, `"coming_soon"`, or `"deprecated"` |
| `operations[].difficulty` | integer | 1–4 |
| `operations[].cert_objective` | string | Non-empty |
| `cases` | array | Same rules as operations, files in `content/cases/` |

`status` values: `"active"` | `"coming_soon"` | `"deprecated"`

Unlock logic: operations are displayed in registry order.
An operation is locked if the previous operation is not in
`completed` AND not in `skipped` in the player save file.
The first operation in the registry is always unlocked.

---

## 6. Placement Test File

`content/placement_test.json` — one file per game, defines all
placement test questions. See `specs/cipher-stage1/spec.md §9`
for full schema definition and validation rules.
