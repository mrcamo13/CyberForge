# spec.md — AEGIS Stage 1: Core Engine + Cases 01-05
<!--
SCOPE: Full AEGIS engine + five Blue Team cases.
NOT HERE: AEGIS Stage 2+ → future spec
NOT HERE: CIPHER → cyberforge/cipher/
-->

**Module:** aegis-stage1
**Date:** 2026-04-11
**Status:** Complete
**Depends on:** cipher-stage1 architecture (patterns only — no shared code)
**Modifies DATA_MODEL.md:** No — AEGIS schemas already defined (§1 save file, §2 case schema with exam_tip)
**Modifies CONSTITUTION.md:** No

---

## 1. Purpose & Scope

### What problem does this module solve?
CIPHER teaches the Red Team perspective. Students studying for CySA+ need
the Blue Team counterpart — the same incidents seen from the defender's
side. AEGIS Stage 1 builds the full engine and five cases covering the
core SOC analyst workflow: log analysis, IOC classification, vulnerability
management, anomaly detection, and incident response.

### What does this module do?
Builds the AEGIS game from scratch in `cyberforge/aegis/` following the
identical architecture as CIPHER. Delivers a fully playable experience
with five cases mapped to CySA+ CS0-003 Domains 1-3. The story mirrors
the NexusCorp CIPHER arc — the player sees the same attack from the
defender's side.

### Success Criteria
- [ ] `python main.py` launches AEGIS and reaches main menu
- [ ] Player can create save, choose track, reach case menu
- [ ] Player can load an existing save
- [ ] Player can complete case01 using all 9 commands
- [ ] XP calculated correctly based on hints used
- [ ] Save persists across quit and relaunch
- [ ] `validate_content.py` passes on all content files
- [ ] `check_imports.py` passes on all Python files

### In Scope
- [ ] aegis/main.py — menu router
- [ ] aegis/utils/terminal.py — ANSI colors, normalize_input, print helpers
- [ ] aegis/utils/player.py — XP calculation, badge evaluation
- [ ] aegis/utils/save_manager.py — save/load/backup/migration/corruption
- [ ] aegis/engine/case_runner.py — single generic runner, reads any case JSON
- [ ] aegis/utils/tools.py — 4 tool functions
- [ ] aegis/content/cases/case01-05.json — five case content files
- [ ] aegis/content/placement_test.json — CySA+ placement test
- [ ] aegis/content/registry.json — case registry
- [ ] aegis/validate_content.py — schema validator (AEGIS version)
- [ ] aegis/check_imports.py — stdlib import auditor
- [ ] aegis/tests/test_save_manager.py — save manager unit tests

### Out of Scope
- ❌ Cases 06+ → aegis-stage2
- ❌ Flask web UI → Stage 4
- ❌ Leaderboard → post-MVP
- ❌ Any code shared with cipher/ — fully independent

---

## 2. User Stories

### US-AG1-001: Blue Team Onboarding
**As** a student studying CySA+, **I want** to practice SOC analyst
skills in a hands-on simulator, **so that** I learn by doing instead
of just reading.

**Acceptance Criteria:**
- [ ] Main menu shows: New Game / Load Game / Placement Test / Quit
- [ ] New Game prompts for analyst name and track selection
- [ ] Player is taken to the case menu after setup

### US-AG1-002: Mirror Story Recognition
**As** a student who has played CIPHER, **I want** to recognize the
NexusCorp incidents from the defender's side, **so that** I understand
both attack and defense perspectives.

**Acceptance Criteria:**
- [ ] case01 scenario references the same web server log anomaly from op04
- [ ] Each case scenario is framed as a SOC analyst receiving an alert
- [ ] Debriefs connect the blue team action to what the attacker did

### US-AG1-003: CySA+ Exam Prep
**As** a student preparing for CySA+, **I want** every case to include
an exam tip, **so that** my game time directly prepares me for the exam.

**Acceptance Criteria:**
- [ ] Every case debrief includes an exam_tip field
- [ ] Each exam_tip describes how this topic is tested on CySA+ CS0-003
- [ ] Each debrief cert_link names the exact CS0-003 objective

---

## 3. Business Rules

Same rules as cipher-stage1 spec §3 apply. AEGIS-specific additions:

1. **exam_tip is mandatory** — every AEGIS case debrief must include an
   exam_tip field. This is the key differentiator from CIPHER ops.
   validate_content.py must check for its presence.
2. **Analyst framing** — all scenario text frames the player as a SOC
   analyst receiving an alert or ticket. Never attacker language.
3. **Track options** — AEGIS offers Blue Team and Full Stack tracks only.
   If a player selects Red Team, display:
   "CIPHER is the Red Team simulator. Run cipher/main.py to start
   your Red Team track. Returning to track selection..."
4. **Same command set** — all 9 commands (help, learn, tools, hint, notes,
   note, skip, menu, quit) work identically to CIPHER.
5. **Same XP and badge rules** — calculate_xp() and evaluate_badges()
   follow identical logic to CIPHER (DATA_MODEL.md §3-4).
6. **challenge_data field required** — same as CIPHER. Engine passes
   op_data["challenge_data"] to run_tool(), not the challenge question.

---

## 4. Data Model

### AEGIS Save File
Same schema as CIPHER save file (DATA_MODEL.md §1) with these differences:
- Location: `aegis/saves/[analyst_name].json`
- `track` values: `"blue"` or `"full"` (never `"red"`)
- `completed`, `skipped`, `in_progress` reference case IDs (case01, etc.)

### AEGIS Case JSON Structure (canonical)

```json
{
  "id": "case01",
  "title": "Suspicious Access",
  "track": "blue",
  "cert_objective": "CySA+ CS0-003 Domain 1 — Security Operations",
  "xp_base": 100,
  "difficulty": 1,
  "tools_type": "log_filter",
  "challenge_data": "[log snippet or data string]",
  "scenario": "Narrative framing as SOC analyst receiving an alert.",
  "challenge": "The question the analyst must answer.",
  "valid_answers": ["answer"],
  "hints": [
    "Hint 1: Real tool URL + exact steps.",
    "Hint 2: Python one-liner — run in NEW terminal.",
    "Hint 3: Use the in-game 'tools' command.",
    "Hint 4: SPOILER — Full answer with explanation."
  ],
  "learn": "Concept explanation.",
  "tools": "Description of what the tools command does.",
  "debrief": {
    "summary": "What the analyst did and why it matters.",
    "real_world": "How this is done in real SOC environments.",
    "next_step": "Practice resource with URL.",
    "cert_link": "CySA+ CS0-003 objective reference.",
    "exam_tip": "On the exam, questions about this topic typically test..."
  }
}
```

### tools_type Allowlist (AEGIS)

| tools_type | Tool | Used in |
|-----------|------|---------|
| `log_filter` | Filters log entries by IP/status pattern | case01 |
| `ioc_classifier` | Classifies an indicator of compromise by type | case02 |
| `vuln_scorer` | Calculates CVSS-based priority score for findings | case03 |
| `process_analyzer` | Flags suspicious attributes in a process list | case04 |

Note: case05 (IR phases) uses `"none"` as tools_type — the challenge is
conceptual and requires no tool. The tools command prints a reference
table of IR phases instead.

### challenge_data values per case

| Case | challenge_data |
|------|---------------|
| case01 | Full log snippet (same format as op04, different scenario) |
| case02 | The encoded string from the config file |
| case03 | Simulated scan report snippet |
| case04 | Simulated process list output |
| case05 | IR scenario description string |

---

## 5. Technical Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Code independence | Zero imports between aegis/ and cipher/ | CONSTITUTION §3 rule 4 |
| utils/terminal.py | Identical interface to CIPHER version | Consistency — same commands |
| case_runner.py | Same command loop pattern as operation_runner.py | Proven architecture |
| tools_type "none" | case05 uses "none" — tools shows IR phase reference table | No tool needed for conceptual case |
| exam_tip | Required field in debrief for all AEGIS cases | Core AEGIS differentiator |
| AEGIS logo | Different ASCII art from CIPHER | Visual distinction |

### validate_content.py differences from CIPHER version

AEGIS validator adds one check: `debrief.exam_tip` is required.
All other checks are identical to CIPHER's validate_content.py.

### tools_type "none" handling

When `tools_type` is `"none"`, `run_tool("none", challenge_data)` must
return a formatted IR phases reference table. Register `"none"` in the
dispatch dict pointing to an `ir_reference()` function that returns
the table regardless of input.

---

## 6. UI Screens & Navigation

Same screens as CIPHER with Blue Team labeling:

| Screen | Key Differences from CIPHER |
|--------|----------------------------|
| Main Menu | ASCII AEGIS logo instead of CIPHER |
| New Game | Track options: Blue Team / Full Stack (Red Team → redirect) |
| Case Menu | Shows cases with same status icons (DONE/SKIP/OPEN/LOCK) |
| Case | Same command loop — "case" framing in prompts |
| Debrief | Includes exam_tip section after cert_link |

---

## 7. Edge Cases

All 15 edge cases from cipher-stage1 spec §7 apply with "case" substituted
for "operation" where applicable. No new edge cases.

---

## 8. Cost & Monitoring

$0 runtime cost. No new observability needed.

---

## 9. Content — Cases 01-05

---

### Case 01 — Log Analysis

**id:** case01
**title:** Suspicious Access
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 1 — Security Operations
**xp_base:** 100
**difficulty:** 1
**tools_type:** log_filter
**challenge_data:** log snippet (see below)

#### challenge_data value
```
10.0.0.99 - - [11/Apr/2026:02:14:33 +0000] "GET /admin/dashboard HTTP/1.1" 200 4821\n203.0.113.44 - - [11/Apr/2026:01:55:02 +0000] "GET / HTTP/1.1" 200 8192\n203.0.113.44 - - [11/Apr/2026:01:55:10 +0000] "GET /about HTTP/1.1" 200 3104\n10.0.0.99 - - [11/Apr/2026:02:14:41 +0000] "GET /admin/dashboard HTTP/1.1" 200 4821\n203.0.113.77 - - [11/Apr/2026:02:30:15 +0000] "GET /login HTTP/1.1" 200 2048\n10.0.0.99 - - [11/Apr/2026:03:02:17 +0000] "GET /admin/dashboard HTTP/1.1" 200 4821\n203.0.113.91 - - [11/Apr/2026:03:10:05 +0000] "GET /admin/dashboard HTTP/1.1" 404 512
```

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING ALERT — SIEM NOTIFICATION
PRIORITY: HIGH
ANALYST: YOU

Alert triggered: Repeated access to /admin/dashboard from
an internal IP outside of business hours.

The web server access log for the staging server at
203.0.113.47:8080 has been pulled. Review the log.
Identify the internal IP address that accessed the admin
panel without authorization.

Time to triage.
```

#### Challenge
`What internal IP address accessed the admin panel (/admin/dashboard) with HTTP 200?`

#### Valid Answers
`["10.0.0.99"]`

#### Hints
```
Hint 1: Go to https://www.splunk.com/en_us/blog/learn/log-analysis.html
        Read "What is log analysis?" — focus on filtering by IP and
        status code. The log format is standard Apache/nginx combined log.

Hint 2: In a real SOC you would run (in a terminal with log access):
        grep "/admin/dashboard" access.log | grep " 200 " | grep "^10\."
        This filters for successful admin panel access from internal IPs.
        Type 'tools' to run the simulated log filter.

Hint 3: Type 'tools' in the game. The log filter highlights all entries
        where an internal IP (10.0.0.x) received HTTP 200 on the admin
        path. The IP address in those lines is your answer.

Hint 4: SPOILER — IP 10.0.0.99 accessed /admin/dashboard three times
        with HTTP 200 status. External IP 203.0.113.91 tried the same
        path but got 404. Type: 10.0.0.99
```

#### Learn Text
```
Log analysis is the foundation of security operations. When a SIEM
triggers an alert, the analyst pulls the relevant logs and filters
them to understand what happened, who did it, and when.

Standard Apache/nginx log format:
  IP - - [timestamp] "METHOD /path HTTP/ver" STATUS SIZE

Key fields for triage:
  Source IP     — internal (10.x) vs external (public IP)
  Request path  — what resource was accessed
  Status code   — 200 = success, 404 = not found, 403 = blocked
  Timestamp     — when it happened (look for after-hours activity)

SOC analyst workflow:
  1. Identify the anomaly (unusual IP, path, status, or time)
  2. Determine scope (how many requests, from where, how long)
  3. Classify (authorized user? insider threat? external attacker?)
  4. Escalate or close based on severity

CySA+ Domain 1 heavily tests log analysis — it is the single most
common skill tested in Security Operations questions.
```

#### Tools Field
`"Filters the web server access log for entries where an internal IP (10.0.0.x) received HTTP 200 on the /admin/dashboard path."`

#### Tools Output
```
LOG FILTER — access log analysis

Filtering for: internal IP (10.0.0.x) + status 200 + path /admin/dashboard

[MATCH] 10.0.0.99 - - [11/Apr/2026:02:14:33] "GET /admin/dashboard HTTP/1.1" 200 4821
[MATCH] 10.0.0.99 - - [11/Apr/2026:02:14:41] "GET /admin/dashboard HTTP/1.1" 200 4821
[MATCH] 10.0.0.99 - - [11/Apr/2026:03:02:17] "GET /admin/dashboard HTTP/1.1" 200 4821

Other entries (no match):
203.0.113.44 - - [11/Apr/2026:01:55:02] "GET / HTTP/1.1" 200 8192
203.0.113.44 - - [11/Apr/2026:01:55:10] "GET /about HTTP/1.1" 200 3104
203.0.113.77 - - [11/Apr/2026:02:30:15] "GET /login HTTP/1.1" 200 2048
203.0.113.91 - - [11/Apr/2026:03:10:05] "GET /admin/dashboard HTTP/1.1" 404 512

Analysis complete. Source IP identified: 10.0.0.99 (3 requests)
```

#### Debrief
```
summary: You identified 10.0.0.99 as the internal IP accessing
/admin/dashboard outside business hours. Log analysis confirmed
three successful requests to a restricted path — a key indicator
of unauthorized internal access or a compromised internal host.

real_world: SOC analysts perform log triage like this dozens of
times per shift. SIEM alerts trigger on anomalies; the analyst
pulls the raw log, filters by relevant fields, and determines
whether it is a true positive requiring escalation or a false alarm.

next_step: Practice with real tools:
TryHackMe: "Splunk: Basics" room
https://tryhackme.com/room/splunk101

cert_link: CySA+ CS0-003 Domain 1 — Security Operations:
"Given a scenario, analyze indicators of potentially malicious activity."

exam_tip: On the exam, log analysis questions often show you a
log snippet and ask you to identify the attacker's IP, the targeted
resource, or the attack technique. Focus on status codes and source
IPs. Internal IPs (RFC 1918: 10.x, 172.16-31.x, 192.168.x) accessing
sensitive paths with 200 status are always suspicious.
```

---

### Case 02 — IOC Classification

**id:** case02
**title:** Encoded Artifact
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 1 — Security Operations
**xp_base:** 100
**difficulty:** 1
**tools_type:** ioc_classifier
**challenge_data:** `"ZGVwbG95bWFzdGVy"`

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING ALERT — THREAT INTEL TEAM
PRIORITY: MEDIUM
ANALYST: YOU

Following the admin panel access from 10.0.0.99, forensics
pulled a config file from the staging server. It contains
a string that does not belong.

STRING: "ZGVwbG95bWFzdGVy"

Your task: classify this indicator of compromise.
What type of encoding was used, and what does it decode to?
The threat intel team needs the IOC type for their report.

What type of encoding is this?
```

#### Challenge
`What encoding type is the string "ZGVwbG95bWFzdGVy"?`

#### Valid Answers
`["base64", "base 64", "b64"]`

#### Hints
```
Hint 1: Go to https://gchq.github.io/CyberChef/
        Paste the string in the Input box.
        Click "Magic" — CyberChef will auto-detect the encoding type.
        The detected encoding name is your answer.

Hint 2: Run this in a NEW terminal (not in the game):
        python3 -c "import base64; print(base64.b64decode('ZGVwbG95bWFzdGVy').decode())"
        If it decodes without error, it is Base64.

Hint 3: Type 'tools' in the game. The IOC classifier will analyze
        the string and identify the encoding type automatically.

Hint 4: SPOILER — The string uses Base64 encoding. The = padding is
        absent here (padding is optional for some Base64 variants).
        It decodes to "deploymaster" — a credential artifact.
        Type: base64
```

#### Learn Text
```
An Indicator of Compromise (IOC) is a piece of evidence that a
security incident has occurred. IOCs are classified by type so
they can be shared, tracked, and acted on.

Common IOC types:
  IP address     — source of malicious traffic
  Domain name    — C2 server or phishing domain
  File hash      — MD5/SHA256 of a malicious file
  URL            — malicious link
  Encoded string — obfuscated data left by an attacker

Encoding types analysts encounter:
  Base64  — A-Z, a-z, 0-9, +, / characters. Often ends with =
  Hex     — 0-9, a-f only. Even character count.
  ROT13   — Only letters, shifted 13 positions
  URL     — %XX percent-encoded characters

Recognizing encoding on sight is a CySA+ tested skill. The key
is knowing what each encoding "looks like" so you can triage quickly
without running a tool on every artifact you encounter.
```

#### Tools Field
`"Analyzes the artifact string and identifies the encoding type, then decodes it to reveal the plaintext value."`

#### Tools Output
```
IOC CLASSIFIER — artifact analysis

Input: ZGVwbG95bWFzdGVy

Encoding detection:
  Characters: A-Z, a-z, 0-9 only (no +, / or = in this sample)
  Length: 16 characters (multiple of 4 — Base64 compatible)
  Pattern: matches Base64 alphabet

Classification: BASE64 ENCODING

Decoded value: deploymaster
IOC type: Encoded credential artifact
Severity: HIGH — decoded value appears to be a username/password
```

#### Debrief
```
summary: You classified "ZGVwbG95bWFzdGVy" as Base64 encoding and
decoded it to reveal the credential "deploymaster" — a username left
in a config file by the attacker. This is the same credential used
to access the deployment server during the attack.

real_world: Attackers frequently Base64-encode credentials, commands,
and payloads to evade simple string-matching detection. SOC analysts
learn to recognize common encoding patterns on sight and decode them
as part of triage. Finding decoded credentials triggers a mandatory
password reset and access review.

next_step: Practice with real tools:
TryHackMe: "Threat Intelligence Tools" room
https://tryhackme.com/room/threatinteltools

cert_link: CySA+ CS0-003 Domain 1 — Security Operations:
"Given a scenario, analyze indicators of potentially malicious activity
including encoded artifacts and obfuscated data."

exam_tip: On the exam, IOC classification questions give you a string
or artifact and ask you to identify the type or the appropriate
response action. Know Base64 (A-Za-z0-9+/=), hex (0-9a-f, even length),
and the difference between encoding (reversible, no key) vs encryption
(reversible, needs key) vs hashing (one-way, fixed length).
```

---

### Case 03 — Vulnerability Scanning

**id:** case03
**title:** Scan Report
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 2 — Vulnerability Management
**xp_base:** 150
**difficulty:** 2
**tools_type:** vuln_scorer
**challenge_data:** "nginx 1.24.0 port 8080 CVE-FAKE-2024 CVSS 9.8 unauthenticated RCE"

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING ALERT — VULNERABILITY MANAGEMENT TEAM
PRIORITY: CRITICAL
ANALYST: YOU

The weekly vulnerability scan of the staging server at
203.0.113.47 has flagged multiple findings. The VM team
needs the highest-priority finding identified for immediate
patching.

SCAN RESULTS — 203.0.113.47:

Finding 1: OpenSSH 8.9p1 (port 22)
  CVE-FAKE-2022-001 | CVSS 5.3 | Medium
  Info disclosure — version banner exposed

Finding 2: nginx 1.24.0 (port 8080)
  CVE-FAKE-2024-099 | CVSS 9.8 | Critical
  Unauthenticated Remote Code Execution

Finding 3: MySQL (port 3306) — filtered
  No findings (port filtered, not reachable)

Which finding should be patched first?
```

#### Challenge
`What is the CVE ID of the highest-priority finding that should be patched first?`

#### Valid Answers
`["cve-fake-2024-099", "cve-fake-2024"]`

#### Hints
```
Hint 1: Go to https://www.first.org/cvss/calculator/3.1
        Read "Base Score Metrics" — CVSS scores range from 0.0 to 10.0.
        Critical = 9.0-10.0. High = 7.0-8.9. The highest score = highest
        priority. Type 'tools' to run the vulnerability scorer.

Hint 2: In a real SOC you would sort findings by CVSS score descending:
        sort -t'|' -k3 -rn vuln_report.txt
        The finding with the highest CVSS score and "Critical" severity
        should be patched first, especially if it allows unauthenticated access.

Hint 3: Type 'tools' in the game. The vulnerability scorer ranks
        all findings by priority. The top-ranked finding is your answer.
        Look at both CVSS score and exploitability.

Hint 4: SPOILER — CVE-FAKE-2024-099 on nginx 1.24.0 has CVSS 9.8
        (Critical) and allows unauthenticated RCE. This is the highest
        priority — it is remotely exploitable with no authentication required.
        Type: CVE-FAKE-2024-099
```

#### Learn Text
```
Vulnerability management is the continuous process of identifying,
classifying, prioritizing, and remediating security weaknesses.

CVSS (Common Vulnerability Scoring System) scores 0.0-10.0:
  Critical: 9.0-10.0 — patch immediately
  High:     7.0-8.9  — patch within 30 days
  Medium:   4.0-6.9  — patch within 90 days
  Low:      0.1-3.9  — patch at next maintenance window

Prioritization factors beyond CVSS:
  Exploitability — is there a public exploit available?
  Authentication — unauthenticated vulnerabilities are higher risk
  Asset criticality — is this a production or staging system?
  Network exposure — is the port internet-facing?

CySA+ Domain 2 tests whether you can read a scan report and identify
the correct remediation priority — not just the highest CVSS number,
but the finding most likely to be exploited in your environment.
```

#### Tools Field
`"Scores and ranks all vulnerability findings by priority using CVSS score and exploitability factors."`

#### Tools Output
```
VULNERABILITY SCORER — scan results for 203.0.113.47

Ranking findings by priority...

RANK 1 [CRITICAL] CVE-FAKE-2024-099
  Service:  nginx 1.24.0 (port 8080)
  CVSS:     9.8
  Impact:   Unauthenticated Remote Code Execution
  Action:   PATCH IMMEDIATELY — remotely exploitable, no auth required

RANK 2 [MEDIUM] CVE-FAKE-2022-001
  Service:  OpenSSH 8.9p1 (port 22)
  CVSS:     5.3
  Impact:   Information disclosure (version banner)
  Action:   Patch within 90 days — low exploitability

RANK 3 [INFO] MySQL (port 3306)
  Service:  Filtered — not reachable
  Action:   No action required

Top priority: CVE-FAKE-2024-099 — patch nginx immediately.
```

#### Debrief
```
summary: You identified CVE-FAKE-2024-099 as the highest-priority
finding — a Critical CVSS 9.8 unauthenticated RCE in nginx 1.24.0.
This is the vulnerability the attacker used to gain initial access to
the staging server. Patching this immediately closes the entry point.

real_world: Vulnerability prioritization is a daily task for security
teams. A scanner may return hundreds of findings — the analyst must
identify which ones represent real, exploitable risk in their environment.
CVSS 9.x Critical findings with unauthenticated RCE always go to the
top of the queue.

next_step: Practice with real tools:
TryHackMe: "Vulnerability Management" room
https://tryhackme.com/room/vulnerabilitymanagementkj

cert_link: CySA+ CS0-003 Domain 2 — Vulnerability Management:
"Given a scenario, analyze output from vulnerability assessment tools
and prioritize findings for remediation."

exam_tip: On the exam, vulnerability prioritization questions often
give you a list of findings and ask which should be addressed first.
Always prioritize by: (1) CVSS score, (2) unauthenticated vs
authenticated exploit, (3) network-accessible vs local-only,
(4) production vs non-production asset. An unauthenticated Critical
on an internet-facing service always wins.
```

---

### Case 04 — Malware/Anomaly Detection

**id:** case04
**title:** Rogue Process
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 1 — Security Operations
**xp_base:** 150
**difficulty:** 2
**tools_type:** process_analyzer
**challenge_data:** "PID:1001 python3.10 user:www-data SUID:yes parent:bash\nPID:1002 nginx user:www-data SUID:no parent:systemd\nPID:1003 sshd user:root SUID:no parent:systemd\nPID:1004 python3.10 user:root SUID:yes parent:python3.10\nPID:1005 mysql user:mysql SUID:no parent:systemd"

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING ALERT — EDR PLATFORM
PRIORITY: CRITICAL
ANALYST: YOU

The EDR platform on the staging server flagged an anomaly.
A process is running with elevated privileges that should not be.

PROCESS LIST — 203.0.113.47 (captured at 03:15 UTC):

PID  PROCESS      USER      SUID  PARENT
1001 python3.10   www-data  yes   bash
1002 nginx        www-data  no    systemd
1003 sshd         root      no    systemd
1004 python3.10   root      yes   python3.10
1005 mysql        mysql     no    systemd

A process spawned a root shell. Identify the malicious PID.
```

#### Challenge
`What is the PID of the malicious process running as root via SUID abuse?`

#### Valid Answers
`["1004", "pid 1004", "pid:1004"]`

#### Hints
```
Hint 1: Go to https://gtfobins.github.io/#python
        Read how python3 with the SUID bit set can spawn a root shell.
        Look for a process in the list that is running as root, has
        SUID set, and has an unusual parent process.

Hint 2: Legitimate root processes are spawned by systemd or init.
        A process running as root with a non-system parent is suspicious.
        Filter the process list: user=root AND SUID=yes AND parent != systemd
        Type 'tools' to run the process analyzer.

Hint 3: Type 'tools' in the game. The process analyzer flags
        processes with anomalous privilege combinations. Look for
        the process marked as suspicious — that PID is your answer.

Hint 4: SPOILER — PID 1004 is python3.10 running as root with SUID=yes,
        spawned by another python3.10 process (PID 1001, www-data).
        This is the SUID privilege escalation from op08 — python3.10
        was used to spawn a root shell. Type: 1004
```

#### Learn Text
```
Process analysis is used to detect malware, unauthorized tools, and
privilege escalation in progress on a live system.

Suspicious process indicators:
  Unexpected user     — web server process (www-data) spawning a shell
  SUID on interpreters — python, perl, ruby with SUID = privesc risk
  Unusual parent       — root process spawned by a non-system parent
  Known tool names     — nc, ncat, python, bash running unexpectedly

Normal parent chain for system processes:
  systemd → nginx       (expected)
  systemd → sshd        (expected)
  bash    → python3.10  (suspicious — interactive shell spawning python)
  python3 → python3.10  (root) — very suspicious

When investigating a process:
  1. Check the user — should this process run as this user?
  2. Check SUID — should this binary have the SUID bit?
  3. Check the parent — how was this process spawned?
  4. Cross-reference with EDR alerts and system baseline

Process analysis maps to CySA+ Domain 1 endpoint security and
anomaly detection objectives.
```

#### Tools Field
`"Analyzes the process list and flags processes with anomalous privilege combinations (SUID + root + non-system parent)."`

#### Tools Output
```
PROCESS ANALYZER — anomaly detection

Scanning process list for privilege anomalies...

PID  PROCESS      USER      SUID  PARENT       STATUS
1001 python3.10   www-data  yes   bash         [SUSPICIOUS] SUID interpreter, spawned by shell
1002 nginx        www-data  no    systemd      [OK] expected service
1003 sshd         root      no    systemd      [OK] expected service
1004 python3.10   root      yes   python3.10   [CRITICAL] root process, SUID, non-system parent
1005 mysql        mysql     no    systemd      [OK] expected service

CRITICAL finding: PID 1004
  python3.10 running as ROOT with SUID bit set
  Parent: python3.10 (PID 1001, www-data)
  This matches the GTFOBins SUID exploit pattern for python3.
  Likely privilege escalation in progress.
```

#### Debrief
```
summary: You identified PID 1004 — a python3.10 process running as root
with the SUID bit set, spawned by a www-data shell. This is the attacker's
privilege escalation from op08 caught in real time. The EDR alert was a
true positive: unauthorized root access via SUID misconfiguration.

real_world: EDR platforms generate process alerts constantly. The analyst
must quickly distinguish normal system processes from malicious ones.
A SUID interpreter (python, perl) spawning a root process from a
non-privileged parent is one of the clearest signs of privilege escalation.

next_step: Practice with real tools:
TryHackMe: "Linux Process Analysis" room
https://tryhackme.com/room/linuxprocessanalysis

cert_link: CySA+ CS0-003 Domain 1 — Security Operations:
"Given a scenario, analyze indicators of potentially malicious activity
on endpoint systems including anomalous process behavior."

exam_tip: On the exam, process analysis questions often show a process
table and ask you to identify the malicious PID or explain why it is
suspicious. Key indicators: unexpected user for process type, SUID on
interpreters, unusual parent-child chains, and known attack tool names
(nc, ncat, python -c, bash -i).
```

---

### Case 05 — Incident Response

**id:** case05
**title:** Incident Phase
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 3 — Incident Response
**xp_base:** 200
**difficulty:** 3
**tools_type:** none
**challenge_data:** "The staging server has been fully compromised. Root access confirmed. Attacker tools removed. System isolated from network. Backups verified intact."

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — INCIDENT RESPONSE TEAM
PRIORITY: HIGH
ANALYST: YOU

The NexusCorp incident has been fully triaged. Here is the
current status of the affected staging server at 203.0.113.47:

STATUS REPORT:
- Root access by attacker confirmed (PID 1004 terminated)
- Attacker tools and artifacts removed from filesystem
- Server isolated from network (NIC disabled)
- Backup copies verified intact and unmodified
- No evidence of lateral movement to other hosts
- All IOCs documented and shared with threat intel team

The incident commander needs to know: given this status,
what is the CURRENT phase of the incident response lifecycle?
```

#### Challenge
`What is the current IR lifecycle phase based on the status report?`

#### Valid Answers
`["eradication", "eradication and recovery", "remediation"]`

#### Hints
```
Hint 1: Go to https://www.nist.gov/publications/computer-security-incident-handling-guide
        Read the NIST SP 800-61 IR lifecycle phases.
        The four phases are: Preparation → Detection/Analysis →
        Containment/Eradication/Recovery → Post-Incident Activity.

Hint 2: Map each status item to a phase:
        - Attacker confirmed (Detection/Analysis — already done)
        - Tools removed (this is Eradication)
        - Server isolated (this is Containment — already done)
        - Backups verified (this is Recovery preparation)
        The current action being taken tells you the phase.

Hint 3: Type 'tools' in the game. The IR reference table shows
        all phases with their defining actions. Match the status
        report items to the correct phase.

Hint 4: SPOILER — Removing attacker tools and artifacts is the
        definition of Eradication. The server is isolated (Containment
        done) and tools are being removed (Eradication in progress).
        Type: eradication
```

#### Learn Text
```
The Incident Response lifecycle (NIST SP 800-61) has four phases:

1. PREPARATION
   Build IR capabilities before an incident occurs.
   Actions: policies, playbooks, tools, training.

2. DETECTION AND ANALYSIS
   Identify and confirm an incident has occurred.
   Actions: alert triage, log analysis, IOC identification,
   scope determination, severity classification.

3. CONTAINMENT, ERADICATION, AND RECOVERY
   Stop the damage, remove the attacker, restore operations.
   - Containment: isolate affected systems (disconnect network)
   - Eradication: remove malware, tools, and attacker persistence
   - Recovery: restore from clean backups, verify integrity,
     return to production

4. POST-INCIDENT ACTIVITY
   Learn from the incident to prevent recurrence.
   Actions: lessons learned, report writing, IOC sharing,
   control improvements.

CySA+ Domain 3 tests your ability to identify the correct IR phase
given a scenario and to know which actions belong to which phase.
Eradication ≠ Containment ≠ Recovery — the exam will test the
differences between all three.
```

#### Tools Field
`"Displays the NIST SP 800-61 IR lifecycle phases with key actions for each phase."`

#### Tools Output
```
IR PHASE REFERENCE — NIST SP 800-61

PHASE 1: PREPARATION
  Build IR capability before incidents occur.
  Key actions: policies, playbooks, tools, training, IR team

PHASE 2: DETECTION AND ANALYSIS
  Identify and scope the incident.
  Key actions: alert triage, log review, IOC identification,
               severity rating, stakeholder notification

PHASE 3: CONTAINMENT, ERADICATION, AND RECOVERY
  Stop damage, remove attacker, restore operations.
  Containment:  isolate systems, block malicious IPs, disable accounts
  Eradication:  remove malware/tools, patch vulnerabilities, reset creds
  Recovery:     restore from backups, verify integrity, monitor for recurrence

PHASE 4: POST-INCIDENT ACTIVITY
  Learn and improve.
  Key actions: lessons learned meeting, final report, IOC sharing,
               control gap analysis, playbook updates

Current incident status maps to: PHASE 3 — ERADICATION
(Tools removed, server isolated, backups verified)
```

#### Debrief
```
summary: You correctly identified Eradication as the current IR phase.
The server was isolated (Containment), attacker tools were removed
(Eradication), and backups are verified for Recovery. This closes the
NexusCorp incident — from the attacker's first Caesar cipher decode
to the defender's final eradication of their access.

real_world: IR phase identification is critical for communication and
escalation. Telling the CISO "we are in Eradication" tells them
exactly where you are in the process and what comes next. Confusing
phases leads to premature return-to-production before the threat is
fully removed — a common cause of re-infection.

next_step: Practice with real tools:
TryHackMe: "Incident Response Fundamentals" room
https://tryhackme.com/room/incidentresponse

cert_link: CySA+ CS0-003 Domain 3 — Incident Response:
"Given a scenario, apply the appropriate incident response procedure
and identify the current phase of the IR lifecycle."

exam_tip: On the exam, IR phase questions are very common. The most
tested distinction is Containment vs Eradication vs Recovery.
Containment = stop the spread. Eradication = remove the threat.
Recovery = restore operations. Also know that Post-Incident Activity
is sometimes called "Lessons Learned" — both terms appear on the exam.
```

---

### Placement Test — 5 Questions (CySA+ Blue Team Foundation)

```json
{
  "pass_threshold": 4,
  "xp_on_pass": 50,
  "questions": [
    {
      "id": "pt01",
      "question": "What does a SIEM do?",
      "options": [
        "Scans systems for open ports and services",
        "Aggregates and correlates log data to detect security events",
        "Encrypts network traffic between endpoints",
        "Blocks malicious traffic at the network perimeter"
      ],
      "correct_index": 1
    },
    {
      "id": "pt02",
      "question": "In the NIST IR lifecycle, which phase involves isolating an affected system?",
      "options": [
        "Preparation",
        "Detection and Analysis",
        "Containment",
        "Post-Incident Activity"
      ],
      "correct_index": 2
    },
    {
      "id": "pt03",
      "question": "What does a CVSS score of 9.8 indicate?",
      "options": [
        "Low severity — can be scheduled for next maintenance window",
        "Medium severity — patch within 90 days",
        "High severity — patch within 30 days",
        "Critical severity — patch immediately"
      ],
      "correct_index": 3
    },
    {
      "id": "pt04",
      "question": "An analyst finds the string 'ZGVwbG95bWFzdGVy' in a config file. What type of encoding is this?",
      "options": [
        "Hexadecimal",
        "ROT13",
        "Base64",
        "URL encoding"
      ],
      "correct_index": 2
    },
    {
      "id": "pt05",
      "question": "Which HTTP status code indicates a successful request?",
      "options": [
        "301 — Moved Permanently",
        "403 — Forbidden",
        "200 — OK",
        "404 — Not Found"
      ],
      "correct_index": 2
    }
  ]
}
```

---

## 10. Open Questions

- [x] Cases — log analysis, IOC, vuln scan, process analysis, IR phases (Q1 approved)
- [x] Story — mirrors NexusCorp CIPHER arc from defender side (Q2=A)
- [x] Difficulty — 1, 1, 2, 2, 3 (Q3 approved)
- [x] tools_type "none" for case05 — returns IR phase reference table
- [x] AEGIS track options — Blue Team + Full Stack only (Red Team → redirect)

---

## 11. Pre-Flight Checklist

- [x] Engine is independent — zero imports from cipher/
- [x] exam_tip field required in all AEGIS case debriefs
- [x] validate_content.py checks exam_tip presence
- [x] challenge_data defined for all 5 cases (§4)
- [x] Canonical JSON structure defined (§4)
- [x] tools_type "none" handled — returns ir_reference() output
- [x] All cert objectives verified against CySA+ CS0-003 domains
- [x] All fictional data uses Veridian Systems / AEGIS universe
- [x] All valid_answers normalized (lowercase)
- [x] All hints escalate correctly (URL → Python/CLI → tools → spoiler)
- [x] Mirror story — each case references the CIPHER op it mirrors
- [x] xp_base: 100, 100, 150, 150, 200
- [x] Placement test covers CySA+ foundation concepts
- [x] Track redirect message defined (§3 rule 3)

---

## 12. Definition of Done

- [ ] All tasks in tasks.md marked complete
- [ ] `python main.py` launches AEGIS without errors
- [ ] Full case01 playthrough works end-to-end
- [ ] All 9 commands functional in case01
- [ ] All 5 cases visible and unlockable in case menu
- [ ] Placement test runs and saves result
- [ ] Save/load/backup tested
- [ ] `validate_content.py` passes on all content
- [ ] `check_imports.py` passes on all files
- [ ] All unit tests pass
- [ ] spec status → Complete
