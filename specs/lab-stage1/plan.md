# plan.md — LAB Stage 1: Python Script Challenges
<!--
SDD Phase 1 of 4: Plan
Next: spec.md
-->

**Module:** lab-stage1
**Date:** 2026-04-16
**Status:** Draft

---

## What is LAB?

A third simulator alongside CIPHER and AEGIS. Instead of answering multiple-choice
questions or typing a keyword, the player *writes real Python scripts* that the game
runs and validates. Pass = your script produces the correct output.

This directly maps to every learning outcome in your Python course:

| Course Outcome | Challenge that covers it |
|---|---|
| Syntax, data types, programming structures | All 5 challenges |
| Develop scripts for system/network tasks | lab02 (IP validator), lab05 (port scanner) |
| Control and looping structures | All 5 challenges |
| Interpret program output / fix errors | All 5 (they debug their own code) |
| Process and analyze cybersecurity data | lab01 (log parser), lab03 (hash checker) |

---

## How It Works

1. Player opens a challenge in LAB
2. Terminal shows the scenario, the task, and starter code
3. Game creates a `lab/workspace/` folder with:
   - `solution.py` — starter code pre-written, player edits it in their own editor
   - Any input files the challenge needs (e.g., `access.log`)
4. Player edits `solution.py` in VS Code / Notepad / whatever they use
5. Back in the game terminal, player types `run`
6. Game runs `python solution.py` and captures stdout
7. If output matches expected: **PASS** — XP awarded, debrief shown
8. If not: game shows the diff (what you got vs what was expected) and lets them try again
9. `hint`, `learn`, `notes`, `skip` all work the same as AEGIS/CIPHER

---

## Stage 1 Challenge Map — 5 Challenges

| ID | Title | Topic | Difficulty | XP |
|---|---|---|---|---|
| lab01 | Log Parser | File I/O, loops, string methods | 1 | 100 |
| lab02 | IP Validator | Loops, string splitting, type conversion | 1 | 100 |
| lab03 | Hash Checker | hashlib, file reading, comparison | 2 | 150 |
| lab04 | Base64 Coder | base64 module, encoding/decoding | 2 | 150 |
| lab05 | Port Scanner | sockets, loops, exception handling | 3 | 200 |

**Total XP available: 700**

---

## Challenge Summaries

### lab01 — Log Parser
Read `access.log` (provided), print every line that contains a 404 status code.
One line per match, no extra formatting.

Teaches: `open()`, `for` loop, `if` + `in`, string basics.

Real-world connection: SOC analysts grep logs daily. This is the manual version
of what a SIEM does automatically.

---

### lab02 — IP Validator
Read `ip_list.txt` (provided, one IP per line), print only the valid IPv4 addresses.
An IP is valid if it has exactly 4 octets, each 0–255.

Teaches: loops, `.split()`, `int()`, range checking, conditional logic.

Real-world connection: Threat intel feeds are full of dirty data. Validating IPs
before ingesting them into a blocklist is a standard automation task.

---

### lab03 — Hash Checker
Read `suspicious.exe` (a dummy binary provided), compute its SHA-256 hash, and
compare it to a known-bad hash provided in the challenge. Print MATCH or NO MATCH.

Teaches: `hashlib`, binary file reading (`rb`), string comparison.

Real-world connection: Malware analysis step one — hash the file, check it against
VirusTotal / threat intel feeds.

---

### lab04 — Base64 Coder
Read `encoded.txt` (a file of Base64 strings, one per line), decode each one,
and print the decoded plaintext.

Teaches: `base64` module, `.decode()`, file I/O, loops.

Real-world connection: Attackers hide payloads in Base64. Analysts decode them
to read the actual command. You already saw this in CIPHER.

---

### lab05 — Port Scanner
Scan localhost (127.0.0.1) on ports 7000–7010. Print each port as OPEN or CLOSED.
A starter script creates a simple server on port 7005 so there's always one open port.

Teaches: `socket`, `try/except`, loops, f-strings, connection timeouts.

Real-world connection: `nmap` is the real tool. Understanding what it does under
the hood (TCP connect scan = exactly this) is an exam topic.

---

## Architecture

```
cyberforge/
  lab/
    main.py               -- entry point (mirrors aegis/main.py structure)
    engine/
      challenge_runner.py -- runs challenges, validates output
    content/
      challenges/         -- lab01.json ... lab05.json
      registry.json       -- challenge list
    workspace/            -- player writes scripts here (gitignored)
      solution.py         -- created fresh per challenge
      access.log          -- input files for challenges
      ...
    saves/                -- player save files (gitignored)
```

---

## Validation Logic

```
run solution.py with subprocess
capture stdout
strip trailing whitespace per line
compare line-by-line to expected_output from challenge JSON
if match: PASS
if not: show diff — "Expected: X  Got: Y"
```

Edge cases handled:
- Trailing newlines ignored
- Case-insensitive comparison for PASS/MATCH type outputs
- Timeout: 10 seconds max (catches infinite loops)
- Runtime error (exception in student code): show the traceback, let them fix it

---

## What Is NOT in Stage 1

- No function signature testing (just stdout comparison)
- No style/linting checks
- No import restrictions (player can use any stdlib module)
- No auto-grading to the instructor — this is self-study

---

## Pre-Planning Checklist

- [x] Course outcomes mapped to challenges
- [x] All 5 challenges use stdlib only (no pip installs needed)
- [x] Architecture mirrors AEGIS/CIPHER pattern
- [x] lab05 needs a local server — starter script handles this
- [x] Workspace gitignored (player code stays local)
- [x] play.py will add [3] LAB to the selector
