# CyberForge

A terminal-based cybersecurity training simulator built for people studying for **CompTIA PenTest+** and **CySA+** exams. Learn by doing — every case is a real scenario with real tooling logic behind it.

> Open source — in active development.

---

## What is it?

CyberForge drops you into a simulated SOC/Red Team terminal and walks you through hands-on scenarios. Instead of flashcards, you run tools, analyze output, and answer the same kinds of questions that appear on the certification exams.

Two simulators ship in one repo:

| Simulator | Role | Exam |
|-----------|------|------|
| **CIPHER** | Red Team operator | CompTIA PenTest+ PT0-003 |
| **AEGIS** | Blue Team SOC analyst | CompTIA CySA+ CS0-003 |

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
[1] CIPHER  — Red Team   (PenTest+)
[2] AEGIS   — Blue Team  (CySA+)
```

### Requirements

- Python 3.8+
- No external libraries — pure standard library

---

## CIPHER — Red Team (PenTest+)

8 operations across 3 stages. You play as a Red Team operator running missions against a fictional target corp (NexusCorp).

**Topics covered:**
- Cryptography (Caesar cipher, Base64 encoding, MD5 hashing)
- Network reconnaissance (port scanning with `nmap`)
- Web application attacks (`sqlmap`, directory enumeration with `gobuster`)
- Log analysis (`grep`)
- Privilege escalation (SUID scanning with `find-suid`)

**Exam domains:** PT0-003 Domain 1 (Planning), Domain 2 (Recon), Domain 3 (Attacks & Exploits)

---

## AEGIS — Blue Team (CySA+)

31 cases across 4 stages. You play as a SOC analyst at Veridian Systems responding to the NIGHTWIRE incident and the Operation IRONCLAD remediation program.

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

AEGIS includes a 5-question placement test. **Pass with 4/5 and Stage 1 is automatically skipped** — you jump straight to Stage 2 (Case 06). Useful if you already have baseline CySA+ knowledge and want to start on harder material.

---

## How Cases Work

Each case follows the same structure:

1. **Scenario** — a realistic SOC ticket or incident brief
2. **Challenge** — a specific question to answer
3. **Commands you type:**
   - `nmap` / `volatility` / `semgrep` / etc. — runs the simulated tool for this case
   - `learn` — explains the concept behind the case
   - `hint` — reveals a progressive hint (reduces XP earned)
   - `note <text>` — saves a note for this case
   - `skip` — skip the case and move on
4. **Debrief** — after a correct answer: real-world context, exam tip, and a link to practice further

XP earned per case depends on hints used:

| Hints used | XP multiplier |
|------------|---------------|
| 0 | 100% |
| 1 | 75% |
| 2 | 50% |
| 3 | 25% |
| 4 | 10% |

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
  cipher/               <- Red Team simulator (PenTest+)
    main.py
    engine/
    utils/
    content/operations/ <- 8 operation JSON files
  specs/                <- design documents per stage
  docs/                 <- architecture and project docs
```

---

## Adding Content

Cases and operations are plain JSON files. To add a new case to AEGIS:

1. Create `aegis/content/cases/caseNN.json` following the schema in any existing case
2. Add an entry to `aegis/content/registry.json`
3. Run `python aegis/validate_content.py` to verify

No code changes needed for new content.

---

## Badges

AEGIS awards badges as you progress:

| Badge | Condition |
|-------|-----------|
| First Blood | Complete your first case |
| No Hints | Solve any case without hints |
| Ghost Protocol | 5 cases solved without hints |
| Halfway There | 16 cases complete |
| Iron Analyst | All 31 cases complete |
| XP-1000 | Accumulate 1,000 XP |

---

## License

MIT — free to use, fork, and build on.

---

## Status

Active development. Content and engine are both evolving.

- CIPHER: 8 operations (PenTest+ Domains 1–3)
- AEGIS: 31 cases (all 4 CySA+ domains)
