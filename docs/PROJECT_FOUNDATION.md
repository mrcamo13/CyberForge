# PROJECT_FOUNDATION.md — CyberForge
<!--
SCOPE: Vision, purpose, stack, roadmap, roles, key decisions, design system, doc registry.
NOT HERE: Implementation specs → specs/[module]/spec.md
NOT HERE: Database schemas → docs/DATA_MODEL.md
NOT HERE: API details → docs/INTEGRATIONS.md
NOT HERE: Rules/constraints → CONSTITUTION.md
NOT HERE: Failures/fixes → docs/LESSONS_LEARNED.md

TARGET LENGTH: 3-5 pages max.
-->

**Last updated:** 2026-04-09

---

## 1. What This Is

CyberForge is an open-source collection of Python terminal games that teach cybersecurity through hands-on scenario-based learning. **CIPHER** puts the player inside an underground hacking group infiltrating a fictional megacorp (NexusCorp) — covering the Red Team offensive path. **AEGIS** puts the player in a SOC analyst role at a fictional company (Veridian Systems) — covering the Blue Team defensive path. Together they cover the full CompTIA cybersecurity stack from Security+ fundamentals to Red Team and Blue Team specialization, using simulated scenarios that teach real methodology without requiring internet, VMs, or any setup beyond Python 3.

---

## 2. What Problem It Solves

Cybersecurity students have lectures, books, and videos but almost no hands-on practice that runs locally with zero setup. TryHackMe and HackTheBox require internet, paid subscriptions, VMs, and VPN configuration. CyberForge is the flight simulator that comes before the real cockpit — it teaches the thinking, the patterns, and the methodology so that when students move to real tools they already know what they are looking for.

---

## 3. What This Is NOT

1. **NOT a replacement for real tools** — it is a simulator. Debriefs explicitly point students to TryHackMe/HTB for real tool practice.
2. **NOT a web app (MVP)** — CLI only. Flask interface is post-MVP.
3. **NOT dependent on internet at runtime** — all content is local JSON files.
4. **NOT a VM or container** — runs anywhere Python 3 runs.
5. **NOT closed source** — all content and engine are open source on GitHub.

---

## 4. Who It's For

| Role | Who they are | What they need |
|------|-------------|----------------|
| CompTIA Student | Studying Security+, CySA+, PenTest+ | Hands-on scenarios that map to exam objectives |
| Beginner | No IT background, starting from zero | Foundation track from ITF+ concepts upward |
| Red Team Learner | Wants offensive security skills | CIPHER operations teaching attack methodology |
| Blue Team Learner | Wants defensive/SOC skills | AEGIS cases teaching detection and response |
| Community Contributor | Wants to add content or fix labs | JSON-driven content files, no Python needed |

---

## 5. What Makes It Different

1. **Zero setup** — `python main.py` and it works. No pip, VPN, VM, or account.
2. **Flight simulator model** — teaches methodology and pattern recognition before real tools. Explicitly designed to pair with TryHackMe/HTB.
3. **Full CompTIA pathway** — Foundation → Red Team or Blue Team → Expert, all in one place.
4. **Open source content** — community adds operations, cases, and cert objectives via JSON files. No Python knowledge required to contribute content.
5. **JSON-driven engine** — content updates never require touching game engine code.

---

## 6. Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Language | Python 3.8+ stdlib only | Zero dependencies, runs anywhere |
| UI | Terminal / ANSI codes | No libraries, cross-platform |
| Content | JSON files (content/) | Update content without code changes |
| Save system | JSON files (saves/) | Simple, portable, no DB |
| Hosting | GitHub (open source) | Community contributions via pull requests |
| Future web | Flask (post-MVP only) | Not in scope until Stage 4 |

---

## 7. Player Progression Model

```
FOUNDATION TRACK (everyone starts here)
ITF+ concepts → A+ → Network+ → Security+

              ↓ choose your path

RED TEAM (CIPHER)         BLUE TEAM (AEGIS)         FULL STACK
Operations                Cases                     Both tracks
PenTest+ aligned          CySA+ aligned             → SecurityX path
Pentester                 SOC Analyst
Red Team Operator         Incident Responder
Exploit Developer         Threat Hunter
```

### Placement Test & Skip System

- Player can take an optional knowledge check at the start of each track
- Pass Foundation check → skip to Red or Blue track entry point
- Pass Red Team check → skip to current CIPHER operation
- Pass Blue Team check → skip to current AEGIS case
- Player can also manually skip any operation or case from the main menu

### Skip Rules

- Skipped operations/cases remain visible in the menu
- Marked as ⏭ Skipped (not ✅ Complete)
- Player can return and complete them any time
- Skipped content awards full XP if completed later
- No XP penalty for skipping

---

## 7B. Difficulty Tiers & Pacing

### Difficulty Tiers

| Tier | Name | Who it's for | XP Multiplier |
|------|------|-------------|---------------|
| 1 | Recruit | No prior knowledge, first time | 1.0x (base) |
| 2 | Analyst | Some IT background, cert studying | 1.25x |
| 3 | Operator | Hands-on experience, intermediate | 1.5x |
| 4 | Elite | Advanced, minimal scaffolding | 2.0x |

Tier is stored as `"difficulty": 1-4` in every JSON content file.
Higher tier = higher `xp_base`, less narrative scaffolding, more ambiguous challenge.

### Pacing Rules

- Operations and cases unlock sequentially by default
- Completing an operation/case unlocks the next one
- Skipped content does not auto-unlock the next — player must skip each individually
- Placement test pass → unlocks track entry point directly
- No time gates — players progress at their own pace

---

## 7C. UX Flow & Navigation

### Main Menu Flow

```
Launch game (python main.py)
        ↓
[New Game] → Enter name → Choose track (Red / Blue / Full Stack)
                               ↓
                     Optional: Take placement test
                               ↓
                         Operation/Case Menu
        ↓
[Load Game] → Select save file → Resume at in_progress operation/case
        ↓
[Quit] → Exit
```

### Operation/Case Menu

```
CIPHER — Operations           AEGIS — Cases
──────────────────────        ──────────────────────
✅ op01 — Caesar Cipher       ✅ case01 — Vuln Triage
✅ op02 — Base64 Decoding     ⏭ case02 — CVE Research
▶  op03 — Port Scanning       🔒 case03 — SIEM Alerts
🔒 op04 — Log Forensics

Status: ✅ Complete | ▶ In Progress | ⏭ Skipped | 🔒 Locked
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

## 8. Content Architecture

All operation/case content lives in JSON files. Python files are the game engine only. This means:

- Content update = edit a JSON file
- New operation/case = add a JSON file + register it
- Community contributions = pull requests to `content/` directory
- No Python knowledge required to add or fix content

```
content/
├── operations/           ← CIPHER (Red Team) content
│   ├── op01.json         ← scenario, hints, answer, debrief, XP
│   └── op02.json
└── cases/                ← AEGIS (Blue Team) content
    ├── case01.json
    └── case02.json
```

### JSON Content Schema (per operation/case)

```json
{
  "id": "op01",
  "title": "Caesar Cipher",
  "track": "red",
  "cert_objective": "PenTest+ Domain 2",
  "xp_base": 100,
  "difficulty": 1,
  "scenario": "narrative intro text",
  "challenge": "what the player must solve",
  "valid_answers": ["answer1", "alternate answer"],
  "hints": [
    "Hint 1: Real tool URL + exact steps",
    "Hint 2: Python one-liner to run in a new terminal",
    "Hint 3: Use the in-game tools command",
    "Hint 4: SPOILER — full answer with explanation"
  ],
  "learn": "concept explanation text",
  "tools": "in-game tool description and usage",
  "debrief": {
    "summary": "what you did and why it matters",
    "real_world": "how this is used in real engagements",
    "next_step": "TryHackMe/HTB link for real tool practice",
    "cert_link": "exact cert objective this maps to"
  }
}
```

---

## 9. Module Roadmap

### Foundation Track — Security+ (Priority 1)

| # | Module | Concept | Cert Objective | Status |
|---|--------|---------|---------------|--------|
| 1 | CIA Triad | Confidentiality, Integrity, Availability | Security+ Domain 1 | ⬜ |
| 2 | Authentication | MFA, tokens, certificates | Security+ Domain 1 | ⬜ |
| 3 | Threats & Attacks | Malware, phishing, social engineering | Security+ Domain 2 | ⬜ |
| 4 | Network Security | Firewalls, IDS/IPS, segmentation | Security+ Domain 3 | ⬜ |
| 5 | Incident Response | Detection, containment, recovery | Security+ Domain 4 | ⬜ |

### Red Team Track — CIPHER Operations (Existing + Planned)

| # | Operation | Concept | Cert Alignment | Status |
|---|-----------|---------|---------------|--------|
| 01 | Caesar Cipher | Brute force / ROT13 | PenTest+ | ✅ Complete |
| 02 | Base64 Decoding | Encoded credentials in logs | PenTest+ | ✅ Complete |
| 03 | Port Scanning | Service enumeration | PenTest+ | ✅ Complete |
| 04 | Log Forensics | Web server log analysis | PenTest+ | ✅ Complete |
| 05 | Hash Cracking | MD5 dictionary attack | PenTest+ | ✅ Complete |
| 06 | Web Exploitation | SQL injection, directory traversal | PenTest+ | ⬜ Planned |
| 07 | Steganography | Hidden data in files | PenTest+ | ⬜ Planned |
| 08 | Social Engineering | Phishing simulation | PenTest+ | ⬜ Planned |

### Blue Team Track — AEGIS Cases (Existing + Planned)

| # | Case | CySA+ Objective | Status |
|---|------|----------------|--------|
| 01 | Vulnerability Scan Triage | 1.1 | ✅ Complete |
| 02 | CVE Research & Patching | 1.2 | ✅ Complete |
| 03 | SIEM Alert Classification | 2.1 | ✅ Complete |
| 04 | NetFlow / C2 Detection | 2.2 | ✅ Complete |
| 05 | Incident Triage (NIST IR) | 3.1 | ✅ Complete |
| 06 | Malware + MITRE ATT&CK | 3.2 | ✅ Complete |
| 07 | Control Gap Mapping | 4.1 | ✅ Complete |
| 08 | Risk Register Response | 4.2 | ✅ Complete |
| 09-20 | Domain expansion cases | All 5 CySA+ domains | ⬜ Planned |

### Post-MVP Features

| Feature | Description | Priority |
|---------|-------------|----------|
| Placement Test | Skip system for players with prior knowledge | High |
| Exam Sim Mode | Timed, scored practice exam per cert | Medium |
| Live CVE Feed | Optional content updates from NVD API | Medium |
| Flask Web UI | Browser interface, leaderboard | Low |
| Educator Mode | Teachers create custom operations/cases | Low |
| Community Hub | In-game module browser for community content | Low |

---

## 10. Shared File Structure

```
cyberforge/
│
├── cipher/                       ← Red Team game (CIPHER)
│   ├── main.py
│   ├── content/
│   │   └── operations/           ← JSON operation files
│   ├── engine/
│   │   └── operations/           ← Python engine (reads JSON)
│   ├── utils/
│   │   ├── terminal.py
│   │   ├── player.py
│   │   └── save_manager.py
│   └── saves/
│
├── aegis/                        ← Blue Team game (AEGIS)
│   ├── main.py
│   ├── content/
│   │   └── cases/                ← JSON case files
│   ├── engine/
│   │   └── cases/                ← Python engine (reads JSON)
│   ├── utils/
│   │   ├── terminal.py
│   │   ├── player.py
│   │   └── save_manager.py
│   └── saves/
│
└── docs/                         ← All SDD documentation
```

---

## 11. Monetization

Free and open source forever. Hosted on GitHub. Community-maintained content via pull requests.

Future: GitHub Sponsors or optional Patreon for contributors who build and maintain premium content packs.

---

## 12. Design System

### Terminal Colors (ANSI)

| Role | Color | Usage |
|------|-------|-------|
| Primary | Cyan `\033[96m` | Headers, prompts, titles |
| Success | Green `\033[92m` | Correct answers, operation complete |
| Warning | Yellow `\033[93m` | Hints, notes, alerts |
| Error | Red `\033[91m` | Wrong answers, failures |
| Info | White `\033[97m` | Body text, descriptions |
| Muted | Dark Gray `\033[90m` | Secondary info, timestamps |

### Every Operation/Case Must Have

- Intro narrative (story context)
- Help menu (commands always visible)
- `learn` command — concept explanation
- `tools` command — in-game helper/analyzer
- 4-tier hint system (URL → one-liner → tool → spoiler)
- Notes system (player can save their own notes)
- XP award at completion
- End debrief (summary + real-world + next step + cert link)

### Debrief Structure (mandatory end of every operation/case)

1. What you did and why it matters
2. Real-world application ("In a real engagement, this technique...")
3. Where to practice with real tools (TryHackMe/HTB link)
4. AEGIS only: exact CySA+ objective mapped

---

## 13. Document Registry

| Document | Purpose | Location | Last Updated |
|----------|---------|----------|-------------|
| PROJECT_FOUNDATION | This file — vision, stack, roadmap | docs/ | 2026-04-09 |
| CONSTITUTION | Immutable rules + AI agent rules | ./ | 2026-04-09 |
| DATA_MODEL | Save file + JSON content schemas | docs/ | — |
| INTEGRATIONS | External tools referenced in hints | docs/ | — |
| LESSONS_LEARNED | Failures + fixes | docs/ | — |
| spec: foundation-track | Security+ foundation modules | specs/foundation-track/ | — |
| spec: cipher-stage2 | CIPHER operations 06-08 | specs/cipher-stage2/ | — |
| spec: aegis-expansion | AEGIS cases 09-20 | specs/aegis-expansion/ | — |
