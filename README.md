# CyberForge

A terminal-based cybersecurity training simulator built for people studying for **CompTIA PenTest+**, **CySA+**, and **CHFI** exams. Learn by doing — every case is a real scenario you investigate step by step, the same way you would on the job.

> Open source — in active development.

---

## What is it?

CyberForge drops you into a simulated terminal and walks you through hands-on investigations. Instead of flashcards, you run tools, analyze output, and work through chained questions that build on each other — the same way real analysts actually work. Each case is a multi-step investigation, not a single question.

Four simulators ship in one repo:

| Simulator | Role | Exam |
|-----------|------|------|
| **CIPHER** | Red Team operator | CompTIA PenTest+ PT0-003 |
| **AEGIS** | Blue Team SOC analyst | CompTIA CySA+ CS0-003 |
| **LAB** | Python scripting for security | All certs (automation skills) |
| **FORENSICS** | Digital forensics investigator | CHFI / GCFE / CySA+ Domain 4 |

---

## Quick Start

### Windows — double-click to launch

Double-click **`play.bat`** in the `cyberforge/` folder. A terminal opens with a game selector.

### Any platform — run from terminal

```bash
cd cyberforge
python play.py
```

Choose a simulator:

```
[1] CIPHER    -- Red Team         (PenTest+)
[2] AEGIS     -- Blue Team        (CySA+)
[3] LAB       -- Script Lab       (Python automation)
[4] FORENSICS -- Digital Forensics (DFIR / CHFI)
```

### Requirements

- Python 3.8+
- No external libraries — pure standard library

---

## How Investigations Work

Every case in every simulator follows the same multi-step pattern:

1. **Scenario** — a realistic incident brief, SOC ticket, or evidence receipt
2. **Run the tool** — `grep`, `volatility`, `exiftool`, `nmap`, etc. to examine the evidence
3. **Answer each step in sequence** — each correct answer unlocks the next question; you can't skip ahead
4. **Wrong-answer nudges** — type a plausible wrong answer and you get specific feedback, not just "Incorrect"
5. **Debrief** — after the final step: real-world context, cert exam tip, and next steps

**Commands available in every case:**

| Command | What it does |
|---------|-------------|
| `<tool>` | Run the forensic/analyst tool for this case |
| `learn` | Read the concept explanation |
| `hint` | Reveal the next hint for the current step (reduces XP) |
| `note <text>` | Save a note for this case |
| `notes` | View your saved notes |
| `skip` | Skip this case |
| `menu` | Save and return to the case list |
| `quit` | Save and exit |

**XP per step** depends on hints used on that step:

| Hints used | XP multiplier |
|------------|---------------|
| 0 | 100% |
| 1 | 75% |
| 2 | 50% |
| 3 | 25% |
| 4 | 10% |

Progress is saved between steps — you can quit mid-case and resume exactly where you left off.

---

## CIPHER — Red Team (PenTest+)

**8 operations**, each broken into 2–4 phases that mirror real pentest workflow: Recon → Foothold → Escalation → Exfil. You play as a Red Team operator running missions against NexusCorp.

**Topics covered:**
- Cryptography (Caesar cipher, Base64, MD5)
- Network reconnaissance (`nmap` port scanning)
- Web attacks (`sqlmap` SQL injection, `gobuster` directory enumeration)
- Log analysis (`grep`)
- Privilege escalation (SUID scanning)

**Exam domains:** PT0-003 Domains 1–3 (Planning, Recon, Attacks & Exploits)

---

## AEGIS — Blue Team (CySA+)

**31 cases** across 4 stages. You play as a SOC analyst at Veridian Systems responding to the NIGHTWIRE incident and the Operation IRONCLAD remediation program.

**Topics covered:**
- Log analysis and SIEM correlation (`splunk`, `grep`)
- Threat intelligence and IOC hunting (`yara`, `threat-intel`)
- Incident response (containment, chain of custody, timeline building)
- Memory and disk forensics (`volatility`, `autopsy`)
- Vulnerability management (`tenable`, `semgrep`, `bandit`)
- Compliance gap analysis (`nist-map`)
- Security metrics, SLA tracking, and executive reporting

**Exam domains:** All 4 CySA+ CS0-003 domains

### Placement Test

AEGIS includes a 5-question placement test. Pass with 4/5 and Stage 1 is automatically skipped — you jump straight to Stage 2. Useful if you already have baseline knowledge.

---

## LAB — Script Lab (Python automation)

**15 challenges** across 3 stages. Write actual Python scripts to solve security tasks. The engine runs your code, validates the output, and gives feedback.

**Topics covered:**
- File I/O, string manipulation, hashing (Stage 1 — Foundation)
- CSV parsing, regex, JSON, ciphers, hash cracking (Stage 2 — Intermediate)
- Binary/XOR operations, socket programming, log correlation, CLI tools, full pipelines (Stage 3 — Advanced)

**Features:** Timed mode, solution replay, leaderboard across save files

**Skills built:** The Python automation toolkit used by real security analysts — the same skills tested in scripting sections of security certs.

---

## FORENSICS — Digital Investigation (DFIR / CHFI)

**20 cases** across 4 stages. You play as a DFIR investigator closing cases on the Meridian Financial Group breach — a connected narrative that runs across all 20 cases.

**Stages:**

| Stage | Topic | Cases |
|-------|-------|-------|
| 1 — File Forensics | Magic bytes, metadata, hash verification, hex analysis | 01–05 |
| 2 — Memory Forensics | Volatility, process masquerade, C2 beacons, injected code | 06–10 |
| 3 — Log & Artifact Analysis | Event logs, registry, browser history, email headers, prefetch | 11–15 |
| 4 — Incident Response | Full IR: timelines, exfil analysis, lateral movement, attribution | 16–20 |

**Forensic tools simulated:** `file`, `exiftool`, `sha256sum`, `hexdump`, `strings`, `volatility`, `timeline`, `eventlog`, `registry`, `browser`, `email-trace`, `wireshark`, `prefetch`, `threat-intel`

**Exam domains:** CHFI v10, GCFE, CySA+ CS0-003 Domain 4

---

## Badges

Each simulator has its own badge set. Examples:

**AEGIS:** First Blood, No Hints, Ghost Protocol (5 hint-free cases), Halfway There, Iron Analyst, XP-1000

**FORENSICS:** First Find, Clean Read (no hints), Clean Chain (5 hint-free), Senior Investigator (10 cases), Master Investigator (all 20), XP-1000

**LAB:** First Solve, No Hints, Hint-Free 3, Lab Graduate (all 15)

---

## Project Structure

```
cyberforge/
  play.bat              <- double-click launcher (Windows)
  play.py               <- unified game selector
  aegis/                <- Blue Team simulator (CySA+)
    main.py
    engine/
    utils/
    content/cases/      <- 31 case JSON files
    validate_content.py
  cipher/               <- Red Team simulator (PenTest+)
    main.py
    engine/
    utils/
    content/operations/ <- 8 operation JSON files
    validate_content.py
  lab/                  <- Script Lab (Python automation)
    main.py
    engine/
    utils/
    content/challenges/ <- 15 challenge JSON files
    validate_content.py
    tests/
  forensics/            <- DFIR simulator (CHFI / CySA+)
    main.py
    engine/
    utils/
    content/cases/      <- 20 case JSON files
    validate_content.py
    tests/
```

---

## Adding Content

Cases are plain JSON files. To add a new case:

1. Create the JSON file in the appropriate `content/cases/` or `content/operations/` folder, following the schema of any existing case
2. Add an entry to the simulator's `registry.json`
3. Run `python validate_content.py` from inside the simulator folder to verify

No code changes needed for new content. Multi-step cases use the `steps` array — see any existing case for the schema.

---

## Content Count

| Simulator | Cases / Ops | Steps | Wrong-answer Nudges |
|-----------|------------|-------|---------------------|
| CIPHER | 8 operations | 23 phases | 62 |
| AEGIS | 31 cases | 93 steps | 107 |
| LAB | 15 challenges | — | — |
| FORENSICS | 20 cases | 59 steps | 119 |
| **Total** | **74** | **175** | **288** |

---

## License

MIT — free to use, fork, and build on.
