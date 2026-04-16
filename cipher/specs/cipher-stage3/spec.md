# spec.md — CIPHER Stage 3: Operations 06-08
<!--
SCOPE: Content layer only. Three new operations on the existing Stage 1 engine.
NOT HERE: Engine changes → cipher-stage1 (complete)
NOT HERE: Operations beyond 08 → future spec
-->

**Module:** cipher-stage3
**Date:** 2026-04-11
**Status:** Draft
**Depends on:** cipher-stage1 (complete), cipher-stage2 (complete)
**Modifies DATA_MODEL.md:** No
**Modifies CONSTITUTION.md:** No

---

## 1. Purpose & Scope

### What problem does this module solve?
Stage 2 ended with the player cracking the admin password and reaching
`/admin/dashboard`. The Red Team track has no further operations.
Stage 3 completes the NexusCorp infiltration arc — web enumeration,
SQL injection, and privilege escalation to root.

### What does this module do?
Adds three operations to the existing JSON-driven engine. No engine changes.
Each op is a self-contained JSON file plus one tool function.
The registry is updated and all existing tests continue to pass.

### Success Criteria
- [ ] op06-op08 JSON files exist and pass validate_content.py
- [ ] 3 new tool functions added to utils/tools.py, check_imports.py passes
- [ ] registry.json updated — all 8 ops appear in operation menu
- [ ] All existing unit tests still pass
- [ ] Full op06 end-to-end check passes

### In Scope
- [ ] content/operations/op06.json — Directory Enumeration
- [ ] content/operations/op07.json — SQL Injection
- [ ] content/operations/op08.json — Privilege Escalation
- [ ] utils/tools.py — 3 new tool functions (dir_enumerator, sqli_tester,
      suid_scanner)
- [ ] content/registry.json — updated with op06-op08 entries

### Out of Scope
- ❌ Engine changes of any kind
- ❌ AEGIS Blue Team content
- ❌ Flask web UI — Stage 4

---

## 2. User Stories

### US-CS3-001: Completing the Infiltration
**As** a player who completed ops 01-05, **I want** to finish the NexusCorp
mission, **so that** the story has a satisfying conclusion.

**Acceptance Criteria:**
- [ ] op06 opens with direct reference to the admin panel from op05
- [ ] op07 references the backup endpoint discovered in op06
- [ ] op08 references the server access gained in op07
- [ ] op08 debrief closes the NexusCorp arc

### US-CS3-002: Learning Advanced Techniques
**As** a player, **I want** to learn web app attacks and post-exploitation,
**so that** I cover the full PenTest+ Domain 3 curriculum.

**Acceptance Criteria:**
- [ ] op06 teaches directory enumeration with gobuster-style output
- [ ] op07 teaches SQL injection — payload construction and output reading
- [ ] op08 teaches SUID misconfiguration — find command and exploitation

### US-CS3-003: Difficulty Progression
**As** a player, **I want** the difficulty to escalate through Stage 3,
**so that** the final operation feels like a meaningful challenge.

**Acceptance Criteria:**
- [ ] op06 and op07 are difficulty 3 — challenging but approachable
- [ ] op08 is difficulty 4 — hardest operation in the track
- [ ] XP rewards reflect the difficulty (200, 200, 250)

---

## 3. Business Rules

All rules from cipher-stage1 spec §3 and cipher-stage2 spec §3 apply.
Additions:

1. **Story closure** — op08 debrief must explicitly close the NexusCorp arc.
   The player has achieved root access. The mission is complete.
2. **SQLi is simulated only** — op07 teaches the concept and payload syntax.
   The sqli_tester tool shows simulated database output. No real DB queries.
3. **SUID is simulated only** — op08 teaches the find command and exploitation
   concept. The suid_scanner shows hardcoded simulated find output.
4. **valid_answers normalization** — same rules as Stage 2. Forward slashes
   allowed. All answers lowercase in valid_answers list.

---

## 4. Data Model

No schema changes. All ops use the existing schema.
challenge_data field is required (established in Stage 1 hotfix).

### challenge_data values per operation

| Op | challenge (question) | challenge_data (tool input) |
|----|---------------------|----------------------------|
| op06 | "What is the path of the hidden backup endpoint?" | "http://203.0.113.47:8080" |
| op07 | "What SQL injection payload unlocks the login?" | "admin' --" |
| op08 | "What is the name of the misconfigured SUID binary?" | "/usr/bin" |

### Canonical JSON Structure

Same structure as defined in cipher-stage2 spec §4. All fields required:
id, title, track, cert_objective, xp_base, difficulty, tools_type,
challenge_data, scenario, challenge, valid_answers (list), hints (4 items),
learn, tools, debrief (object: summary, real_world, next_step, cert_link).

---

## 5. Technical Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| dir_enumerator output | Hardcoded gobuster-style results | Consistent with simulated tools pattern |
| sqli_tester input | The payload string from challenge_data | Player types payload, tool confirms result |
| suid_scanner input | Base directory path from challenge_data | Dynamic header, hardcoded results |
| op07 answer | Payload string normalized | normalize_input allows - and ' chars? — see §3 rule 4 |

### Normalization note for op07

The valid answer `admin' --` contains a single quote and spaces.
`normalize_input()` in terminal.py strips characters matching `[^\w\s\.\-\/]`.
Single quote `'` is NOT in `\w` or the allowed set, so it gets stripped.
Normalized form of `admin' --` = `admin --`.
Valid answers list must use the normalized form: `["admin --", "admin'--", "admin --"]`
covering common spacing variants after normalization.

### Tool Function Signatures

```python
def dir_enumerator(target_url: str) -> str:
    """Simulate a gobuster-style directory scan on target_url.
    target_url: base URL string from challenge_data.
    Output header includes target_url dynamically.
    Returns hardcoded simulated scan results for the NexusCorp scenario.
    """

def sqli_tester(payload: str) -> str:
    """Simulate testing an SQL injection payload against a login form.
    payload: the injection string from challenge_data.
    Shows the simulated SQL query construction and result.
    Returns formatted output showing login bypass and dumped data.
    """

def suid_scanner(search_path: str) -> str:
    """Simulate a find command scanning for SUID binaries.
    search_path: directory path from challenge_data.
    Output header includes search_path dynamically.
    Returns hardcoded simulated find output for the NexusCorp scenario.
    """
```

---

## 6. UI Screens & Navigation

No new screens. Operations appear in the existing operation menu.
op08 is the final operation in the Red Team track.

---

## 7. Edge Cases

All Stage 1 and Stage 2 edge cases apply. No new edge cases.

---

## 8. Cost & Monitoring

$0 runtime cost. No new observability needed.

---

## 9. Content — Operations 06-08

---

### Operation 06 — Directory Enumeration

**id:** op06
**title:** Hidden Paths
**track:** red
**cert_objective:** PenTest+ PT0-003 Domain 2 — Reconnaissance
**xp_base:** 200
**difficulty:** 3
**tools_type:** dir_enumerator
**challenge_data:** `"http://203.0.113.47:8080"`

#### Narrative
```
CIPHER TERMINAL v1.0 — SECURE CHANNEL ESTABLISHED

INCOMING TRANSMISSION FROM: GHOST (CIPHER Field Agent)
CLASSIFICATION: PRIORITY ALPHA

Operative. We are inside the admin panel. The dashboard shows
system status but the real prize is elsewhere on this server.

Web servers often have paths that are not linked from any page —
backup files, old admin endpoints, API routes left exposed.
A directory scan will find them by brute-forcing common names.

TARGET: http://203.0.113.47:8080

Run the enumeration. Find the hidden backup endpoint.
That is our next entry point.

GHOST OUT.
```

#### Challenge
`What is the path of the hidden backup endpoint?`

#### Valid Answers
`["/backup", "/backup/"]`

#### Hints
```
Hint 1: Go to https://github.com/OJ/gobuster
        Read the README — specifically the "dir" mode.
        Directory enumeration tries common path names against a web server.
        Type 'tools' to run the simulated scan on this target.

Hint 2: In a real engagement you would run (requires gobuster installed):
        gobuster dir -u http://203.0.113.47:8080 -w /usr/share/wordlists/dirb/common.txt
        This tries hundreds of common directory names automatically.
        In this simulation, type 'tools' to see the results.

Hint 3: Type 'tools' in the game. The directory enumerator shows
        all paths that returned a 200 or 301 status on the target.
        Look for the path that looks like a backup location.

Hint 4: SPOILER — The scan finds /backup returning HTTP 200.
        This is a common misconfiguration — backup directories left
        accessible on web servers. Type: /backup
```

#### Learn Text
```
Directory enumeration (also called dir busting or web fuzzing) probes
a web server for hidden paths by trying common directory and file names
from a wordlist.

The tool sends requests like:
  GET /admin HTTP/1.1
  GET /backup HTTP/1.1
  GET /config HTTP/1.1
  ... (hundreds or thousands more)

Paths that return 200 (found) or 301 (redirect) are flagged.

Common findings:
  /backup       — backup archives, often downloadable
  /admin        — admin panels not linked from the main site
  /config       — configuration files accidentally served
  /api          — undocumented API endpoints
  /.git         — exposed version control repositories

Real tools: gobuster, ffuf, dirb, feroxbuster.
This is a standard step in web application penetration testing and
maps directly to the "enumeration" phase of PenTest+ Domain 2.
```

#### Tools Field
`"Runs a simulated directory scan on the target web server and shows all paths that returned a 200 or 301 status."`

#### Tools Output
```
DIR ENUMERATOR — target: {target_url}

Starting simulated scan with common wordlist...

/              [Status: 200] [Size: 8192]
/about         [Status: 200] [Size: 3104]
/login         [Status: 200] [Size: 2048]
/admin         [Status: 301] [-> /admin/dashboard]
/backup        [Status: 200] [Size: 51204]
/assets        [Status: 200] [Size: 1024]
/favicon.ico   [Status: 200] [Size: 318]

Scan complete. 7 paths found. 1 potentially sensitive path identified.
```

#### Debrief
```
summary: You enumerated the NexusCorp web server and discovered /backup —
a directory left accessible on the server containing backup archives.
Directory enumeration is a standard recon step that reveals paths the
application never intended to expose publicly.

real_world: Directory enumeration is one of the most consistently
productive steps in web application testing. Real pentesters find exposed
backup files, configuration files, API endpoints, and admin panels this way.
Tools like gobuster and ffuf with large wordlists can find hundreds of
paths in seconds.

next_step: Practice with real tools:
TryHackMe: "Content Discovery" room
https://tryhackme.com/room/contentdiscovery

cert_link: PenTest+ PT0-003 Domain 2 — Reconnaissance:
"Given a scenario, perform active reconnaissance including web application
enumeration to identify hidden resources and attack surface."
```

---

### Operation 07 — SQL Injection

**id:** op07
**title:** Injection Point
**track:** red
**cert_objective:** PenTest+ PT0-003 Domain 3 — Attacks and Exploits
**xp_base:** 200
**difficulty:** 3
**tools_type:** sqli_tester
**challenge_data:** `"admin' --"`

#### Narrative
```
CIPHER TERMINAL v1.0 — SECURE CHANNEL ESTABLISHED

INCOMING TRANSMISSION FROM: GHOST (CIPHER Field Agent)
CLASSIFICATION: PRIORITY ALPHA

Operative. The /backup directory contains a database export and
a secondary login form for the internal reporting system.

The login form passes user input directly into an SQL query —
no sanitization. Classic injection point.

If we inject the right payload into the username field, we can
bypass the authentication entirely and access the reporting system.

TARGET FORM: http://203.0.113.47:8080/backup/report-login

Construct the payload. Bypass the login.

GHOST OUT.
```

#### Challenge
`What SQL injection payload bypasses the login? (enter the username field value)`

#### Valid Answers
`["admin --", "admin'--", "admin' --", "admin --"]`

#### Hints
```
Hint 1: Go to https://portswigger.net/web-security/sql-injection
        Read "What is SQL injection?" — specifically the section on
        bypassing login forms using a single quote and comment syntax.
        SQL comments (--) cause the database to ignore the rest of the query.

Hint 2: The login query looks like:
        SELECT * FROM users WHERE username='INPUT' AND password='INPUT'
        If you inject a single quote after the username, you break the query.
        Then use -- to comment out the password check entirely.
        Try entering: admin' --
        (single quote, space, two dashes)

Hint 3: Type 'tools' in the game. The SQL injection tester shows
        exactly how the payload is inserted into the query and what
        the database receives. Read the constructed query carefully.

Hint 4: SPOILER — The payload is: admin' --
        This constructs: SELECT * FROM users WHERE username='admin' --' AND password='...'
        The -- comments out everything after it. Password check bypassed.
        Type: admin' --
```

#### Learn Text
```
SQL injection occurs when user input is inserted directly into an
SQL query without sanitization. The attacker injects SQL syntax to
change the meaning of the query.

Classic login bypass:

  Normal query:
  SELECT * FROM users WHERE username='alice' AND password='secret'

  Injected query (username = admin' --):
  SELECT * FROM users WHERE username='admin' --' AND password='...'

  The -- starts a SQL comment. Everything after it is ignored.
  The query becomes: SELECT * FROM users WHERE username='admin'
  If 'admin' exists, login succeeds regardless of password.

Why this works:
- The application trusts user input
- Input is concatenated directly into the query string
- No parameterized queries or prepared statements used

Prevention: always use parameterized queries (prepared statements).
Never concatenate user input into SQL strings.

SQLi is one of the OWASP Top 10 vulnerabilities and appears on
virtually every real web application pentest.
```

#### Tools Field
`"Tests the SQL injection payload against the simulated login form and shows the constructed query and result."`

#### Tools Output
```
SQL INJECTION TESTER — target: /backup/report-login

Payload: admin' --

Constructing query with payload in username field:
  SELECT * FROM users WHERE username='admin' --' AND password=''

Query sent to database:
  SELECT * FROM users WHERE username='admin'
  [Everything after -- is treated as a comment and ignored]

Result: LOGIN BYPASSED
  Returned row: {id: 1, username: 'admin', role: 'superuser'}

Authentication bypass successful.
Password check was never evaluated.
```

#### Debrief
```
summary: You constructed an SQL injection payload that bypassed NexusCorp's
reporting system login by turning the password check into a SQL comment.
The application concatenated your input directly into a query string —
a classic injection vulnerability that gives unauthenticated access.

real_world: SQL injection remains one of the most common critical
vulnerabilities found in web application penetration tests. Parameterized
queries (prepared statements) prevent it completely — but many legacy
applications still concatenate user input directly. Finding an SQLi point
typically means the database contents can be fully extracted.

next_step: Practice with real tools:
TryHackMe: "SQL Injection" room
https://tryhackme.com/room/sqlinjectionlm

cert_link: PenTest+ PT0-003 Domain 3 — Attacks and Exploits:
"Given a scenario, research attack vectors and perform web application
attacks including injection-based vulnerabilities."
```

---

### Operation 08 — Privilege Escalation

**id:** op08
**title:** Root Access
**track:** red
**cert_objective:** PenTest+ PT0-003 Domain 3 — Attacks and Exploits
**xp_base:** 250
**difficulty:** 4
**tools_type:** suid_scanner
**challenge_data:** `"/usr/bin"`

#### Narrative
```
CIPHER TERMINAL v1.0 — SECURE CHANNEL ESTABLISHED

INCOMING TRANSMISSION FROM: GHOST (CIPHER Field Agent)
CLASSIFICATION: PRIORITY ALPHA

Operative. The reporting system gave us a shell on the server.
We are in as the "www-data" service account. Low privileges.

To complete the mission we need root. NexusCorp's sysadmin
misconfigured file permissions — some binaries have the SUID bit
set, meaning they run as root regardless of who executes them.

Find the misconfigured binary. Use it to escalate to root.
That is the final objective.

SCAN PATH: /usr/bin

GHOST OUT.
```

#### Challenge
`What is the name of the misconfigured SUID binary (just the binary name, not the full path)?`

#### Valid Answers
`["python3", "python3.10"]`

#### Hints
```
Hint 1: Go to https://gtfobins.github.io/
        Search for binaries with the "SUID" filter.
        GTFOBins documents how common Linux binaries can be used for
        privilege escalation when the SUID bit is set.

Hint 2: In a real engagement you would run:
        find /usr/bin -perm -4000 -type f 2>/dev/null
        The -perm -4000 flag finds files with the SUID bit set.
        Any result that appears in GTFOBins is exploitable.
        Type 'tools' to run the simulated scan.

Hint 3: Type 'tools' in the game. The SUID scanner shows all
        binaries in /usr/bin with the SUID bit set. Cross-reference
        the result with GTFOBins to identify which one is dangerous.

Hint 4: SPOILER — The scan finds python3.10 with the SUID bit set.
        From GTFOBins: python3 -c 'import os; os.execl("/bin/sh", "sh", "-p")'
        This spawns a root shell. The binary name is: python3
        Type: python3
```

#### Learn Text
```
Privilege escalation means moving from a low-privilege account to a
higher-privilege one — typically from a service account to root.

SUID (Set User ID) is a Linux file permission flag. When set on a
binary, the binary executes with the file owner's permissions (often
root) regardless of who runs it.

Finding SUID binaries:
  find / -perm -4000 -type f 2>/dev/null

If a SUID binary is in GTFOBins (gtfobins.github.io), it can likely
be used to spawn a root shell or read privileged files.

Example — python3 with SUID set:
  python3 -c 'import os; os.execl("/bin/sh", "sh", "-p")'
  This spawns /bin/sh running as root.

Other common privesc vectors:
  sudo misconfigurations  — sudo -l shows what you can run as root
  writable cron jobs      — scripts run by root that you can modify
  weak file permissions   — config files writable by low-priv users
  kernel exploits         — unpatched kernel vulnerabilities

Privilege escalation is a core post-exploitation skill covered
heavily in PenTest+ Domain 3 and every real engagement report.
```

#### Tools Field
`"Scans the target directory for binaries with the SUID bit set and flags any that appear in GTFOBins."`

#### Tools Output
```
SUID SCANNER — scanning: {search_path}

Running: find {search_path} -perm -4000 -type f

Results:
  /usr/bin/passwd       [SUID] owner: root  — expected, low risk
  /usr/bin/sudo         [SUID] owner: root  — expected, low risk
  /usr/bin/python3.10   [SUID] owner: root  — *** FLAGGED: in GTFOBins ***
  /usr/bin/mount        [SUID] owner: root  — expected, low risk
  /usr/bin/su           [SUID] owner: root  — expected, low risk

Scan complete. 5 SUID binaries found. 1 flagged as potentially exploitable.

GTFOBins entry: https://gtfobins.github.io/gtfobins/python/
Exploit: python3 -c 'import os; os.execl("/bin/sh", "sh", "-p")'
```

#### Debrief
```
summary: You identified python3.10 with the SUID bit misconfigured on
NexusCorp's server and used it to escalate privileges to root. This is
the final objective — the NexusCorp infiltration is complete. From Caesar
cipher to root shell: recon, enumeration, credential attacks, web app
exploitation, and privilege escalation.

real_world: Privilege escalation findings are critical severity in every
real pentest report. SUID misconfigurations are common on systems where
admins install interpreters (Python, Perl, Ruby) without checking the
permission implications. GTFOBins is the go-to reference for exploiting
these in real engagements.

next_step: Practice with real tools:
TryHackMe: "Linux Privilege Escalation" room
https://tryhackme.com/room/linprivesc

cert_link: PenTest+ PT0-003 Domain 3 — Attacks and Exploits:
"Given a scenario, perform post-exploitation techniques including
privilege escalation to achieve objectives on a target system."
```

---

## 10. Open Questions

- [x] Techniques — dir enumeration, SQLi, SUID privesc (Q1=A)
- [x] Difficulty — 3, 3, 4 (Q2 approved)
- [x] Story — continues deeper into NexusCorp (Q3=A)
- [x] op07 normalization — single quote stripped by normalize_input,
      valid_answers covers normalized variants
- [x] op08 answer — "python3" and "python3.10" both accepted

---

## 11. Pre-Flight Checklist

- [x] No engine changes required
- [x] tools_type values not yet in DATA_MODEL.md allowlist — must add
      dir_enumerator, sqli_tester, suid_scanner before building
- [x] challenge_data values defined for all 3 ops (§4)
- [x] Canonical JSON structure defined (inherited from Stage 2 §4)
- [x] Story arc closes NexusCorp mission in op08 debrief
- [x] All cert objectives verified against PT0-003 domains
- [x] All fictional data uses approved NexusCorp/CIPHER universe
- [x] All valid_answers account for normalize_input behavior
- [x] op07 single-quote normalization handled in valid_answers list
- [x] All hints escalate correctly (URL → Python/CLI → tools → spoiler)
- [x] Hint 4 gives full answer with explanation
- [x] All IPs use RFC 5737 approved ranges (203.0.113.x)
- [x] xp_base: op06=200, op07=200, op08=250
- [x] All debrief fields present (summary, real_world, next_step, cert_link)
- [x] op08 debrief explicitly closes the NexusCorp arc

---

## 12. Definition of Done

- [ ] All tasks in tasks.md marked complete
- [ ] validate_content.py passes on all 8 ops (op01-op08)
- [ ] check_imports.py passes on all files
- [ ] python -m unittest discover tests/ — all green
- [ ] Full op06 end-to-end check passes
- [ ] All 3 new ops visible and unlockable in operation menu
- [ ] spec status → Complete
