# spec.md — CIPHER Stage 2: Operations 02-05
<!--
SCOPE: Content layer only. Four new operations on the existing Stage 1 engine.
NOT HERE: Engine changes → cipher-stage1 (complete)
NOT HERE: Operations 06+ → cipher-stage3
-->

**Module:** cipher-stage2
**Date:** 2026-04-11
**Status:** Draft
**Depends on:** cipher-stage1 (complete)
**Modifies DATA_MODEL.md:** Yes — add challenge_data field (already applied in Stage 1 hotfix)
**Modifies CONSTITUTION.md:** No

---

## 1. Purpose & Scope

### What problem does this module solve?
Stage 1 delivered a working engine with one operation. Players complete op01
and hit a dead end. Stage 2 fills the Red Team curriculum through the four
core techniques that follow initial access: encoding recon, network mapping,
log analysis, and credential attacks.

### What does this module do?
Adds four operations to the existing JSON-driven engine. No engine changes
beyond the challenge_data field already hotfixed in Stage 1.
Each op is a self-contained JSON file plus one tool function.
The registry is updated and all existing tests continue to pass.

### Success Criteria
- [ ] op02-op05 JSON files exist and pass validate_content.py
- [ ] 4 new tool functions added to utils/tools.py, check_imports.py passes
- [ ] registry.json updated — all 4 ops appear in operation menu
- [ ] All existing Stage 1 unit tests still pass
- [ ] Full op02 playthrough works end-to-end in the game

### In Scope
- [ ] content/operations/op02.json — Base64 Decoding
- [ ] content/operations/op03.json — Port Scan Enumeration
- [ ] content/operations/op04.json — Web Log Analysis
- [ ] content/operations/op05.json — MD5 Hash Cracking
- [ ] utils/tools.py — 4 new tool functions (base64_decoder, port_scanner,
      log_analyzer, hash_cracker)
- [ ] content/registry.json — updated with op02-op05 entries

### Out of Scope
- ❌ Engine changes (main.py, operation_runner.py, save_manager.py)
- ❌ Operations 06+ → cipher-stage3
- ❌ AEGIS Blue Team content

---

## 2. User Stories

### US-CS2-001: Continuing the Mission
**As** a player who completed op01, **I want** to continue the NexusCorp
infiltration, **so that** the story feels like a real escalating engagement.

**Acceptance Criteria:**
- [ ] op02 opens with a direct callback to the vault password from op01
- [ ] Each subsequent op references the outcome of the previous one
- [ ] Debrief of each op hints at what comes next

### US-CS2-002: Learning New Techniques
**As** a player, **I want** each operation to teach a distinct technique,
**so that** I build real skills progression across the track.

**Acceptance Criteria:**
- [ ] op02 teaches Base64 encoding/decoding
- [ ] op03 teaches port scanning and service enumeration
- [ ] op04 teaches web server log analysis
- [ ] op05 teaches MD5 hash identification and dictionary attacks

### US-CS2-003: Cert Alignment
**As** a player studying for PenTest+, **I want** each operation to map to
a specific exam objective, **so that** my game time counts as exam prep.

**Acceptance Criteria:**
- [ ] Each op debrief names the exact PenTest+ PT0-003 objective
- [ ] Each op debrief links to a TryHackMe or HTB practice room

---

## 3. Business Rules

All rules from cipher-stage1 spec §3 apply unchanged. Additions:

1. **Story continuity** — op02 scenario must reference "the vault password
   NEXUSCORP" from op01. Each subsequent op explicitly references the
   previous outcome (not implied — stated in the narrative text).
2. **Difficulty gates are informational only** — difficulty numbers appear
   in the operation menu but do not block access. Unlock logic (previous op
   completed or skipped) is the only gate, per CONSTITUTION §3 rule 10.
3. **All tool outputs are simulated** — no real network calls. port_scanner
   returns hardcoded simulated output matching the challenge_data IP.
   log_analyzer returns a hardcoded log snippet. hash_cracker simulates a
   dictionary attack. The target/input is always taken from challenge_data.
4. **hash_cracker reveals the cracked password in tool output** — this is
   intentional. The tool teaches the technique by showing each word tested
   and the final match. The player must still read the output and type the
   answer at the prompt. Educational value comes from seeing the process.
5. **valid_answers normalization** — normalize_input() in terminal.py
   allows forward slashes (regex: [^\w\s\.\-\/]). Answers containing /
   (e.g., /admin/dashboard) are valid. Trailing slash variants must be
   listed explicitly in valid_answers (e.g., ["/admin/dashboard",
   "/admin/dashboard/"]).

---

## 4. Data Model

### challenge_data field (hotfixed in Stage 1)

Every operation JSON must include a `challenge_data` field containing the
primary encoded/target string the tool function will process. This is
separate from the `challenge` field (which is the question shown to the player).

The engine passes `op_data.get("challenge_data", op_data["challenge"])` to
`run_tool()`. Tool functions receive this string as their only input.

| Op | challenge (question shown) | challenge_data (tool input) |
|----|---------------------------|----------------------------|
| op01 | "What is the decoded vault password?" | "QHAXVFRUS" |
| op02 | "What is the decoded username?" | "ZGVwbG95bWFzdGVy" |
| op03 | "Which port is the web service running on?" | "203.0.113.47" |
| op04 | "What is the path of the admin panel?" | "[full log snippet — see §9]" |
| op05 | "What is the plaintext password behind the hash?" | "5f4dcc3b5aa765d61d8327deb882cf99" |

### Canonical Operation JSON Structure

All op JSON files must match this exact structure and field names:

```json
{
  "id": "op02",
  "title": "Vault Secrets",
  "track": "red",
  "cert_objective": "PenTest+ PT0-003 Domain 2 — Reconnaissance",
  "xp_base": 100,
  "difficulty": 1,
  "tools_type": "base64_decoder",
  "challenge_data": "ZGVwbG95bWFzdGVy",
  "scenario": "Multi-line narrative string shown at operation start.",
  "challenge": "What is the decoded username?",
  "valid_answers": ["deploymaster"],
  "hints": [
    "Hint 1: ...",
    "Hint 2: ...",
    "Hint 3: ...",
    "Hint 4: SPOILER — ..."
  ],
  "learn": "Concept explanation string.",
  "tools": "Description of what the tools command does for this op.",
  "debrief": {
    "summary": "What the player did and why it matters.",
    "real_world": "How this is used in real engagements.",
    "next_step": "Practice resource with URL.",
    "cert_link": "PenTest+ objective reference."
  }
}
```

Multi-line strings use `\n` within the JSON string value (no literal newlines
in the JSON file). debrief is always an object with four string subfields.
validate_content.py checks all fields listed above.

---

## 5. Technical Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Tool input | challenge_data field, not challenge field | Separates question text from tool input data |
| Tool function location | Add to existing utils/tools.py | One file, one dispatch table |
| Simulated output | Hardcoded in tool function, uses challenge_data param | Dynamic enough for reuse, no runtime data needed |
| hash_cracker reveal | Shows full cracked result in output | Educational — player sees the dictionary attack process |
| port_scanner output | Uses target parameter dynamically in header | Consistent with challenge_data pattern, future-proof |
| log_analyzer input | Full log snippet string in challenge_data | Passed directly to analyzer, no separate field needed |
| valid_answers with / | Allowed — normalize_input regex permits forward slashes | Consistent with existing normalization rules |

### Tool Function Signatures

```python
def base64_decoder(text: str) -> str:
    """Decode a Base64 string and display the result.
    text: the Base64 encoded string from challenge_data.
    """

def port_scanner(target: str) -> str:
    """Simulate an nmap -sV style port scan on target IP.
    target: IP address string from challenge_data.
    Output header must include the target value dynamically.
    """

def log_analyzer(log_snippet: str) -> str:
    """Parse a log snippet and highlight 200-status internal IP requests.
    log_snippet: full log text string from challenge_data.
    """

def hash_cracker(hash_value: str) -> str:
    """Simulate an MD5 dictionary attack against hash_value.
    hash_value: MD5 hex string from challenge_data.
    Shows each word tested and prints MATCH FOUND with plaintext on match.
    """
```

---

## 6. UI Screens & Navigation

No new screens. Operations appear in the existing operation menu in order.
The engine handles all display via the existing command loop.

---

## 7. Edge Cases

All Stage 1 edge cases apply. No new edge cases introduced — content only.

---

## 8. Cost & Monitoring

$0 runtime cost. No new observability needed.

---

## 9. Content — Operations 02-05

---

### Operation 02 — Base64 Decoding

**id:** op02
**title:** Vault Secrets
**track:** red
**cert_objective:** PenTest+ PT0-003 Domain 2 — Reconnaissance
**xp_base:** 100
**difficulty:** 1
**tools_type:** base64_decoder
**challenge_data:** `"ZGVwbG95bWFzdGVy"`

#### Narrative
```
CIPHER TERMINAL v1.0 — SECURE CHANNEL ESTABLISHED

INCOMING TRANSMISSION FROM: GHOST (CIPHER Field Agent)
CLASSIFICATION: PRIORITY ALPHA

Operative. The vault password NEXUSCORP got us in.

The vault system contains a secondary credentials file.
NexusCorp's dev team encoded it before storing —
probably thought Base64 would hide it. Amateurs.

We need the username for the internal deployment server.
It's buried in this encoded string pulled from the file:

ENCODED STRING: "ZGVwbG95bWFzdGVy"

Decode it. Get the username. Clock is ticking.

GHOST OUT.
```

#### Challenge
`What is the decoded username?`

#### Valid Answers
`["deploymaster"]`

#### Hints
```
Hint 1: Go to https://gchq.github.io/CyberChef/
        Search "From Base64" and drag it to the Recipe box.
        Paste "ZGVwbG95bWFzdGVy" in the Input box.
        The decoded text appears in the Output box.

Hint 2: Run this in a NEW terminal (not in the game):
        python3 -c "import base64; print(base64.b64decode('ZGVwbG95bWFzdGVy').decode())"
        The output is the username.

Hint 3: Type 'tools' in the game. The Base64 decoder will
        automatically decode the string for you.
        Read the output carefully.

Hint 4: SPOILER — Base64 decodes "ZGVwbG95bWFzdGVy" to "deploymaster".
        Each group of 4 Base64 characters maps to 3 bytes of original data.
        Type: deploymaster
```

#### Learn Text
```
Base64 is an encoding scheme — not encryption.
It converts binary data into ASCII text using 64 printable characters
(A-Z, a-z, 0-9, +, /) so it can be safely transmitted as text.

Base64 is NOT secure. It adds no secrecy — anyone can decode it instantly.
It is used for transport, not protection.

Pentesters find Base64 constantly: in HTTP headers, JWT tokens,
environment variables, config files, and source code comments.
Recognizing the = padding at the end is the first clue.

Real example: the Authorization header in HTTP Basic Auth is
just Base64-encoded "username:password". Decode it and you have
credentials in plaintext.
```

#### Tools Field
`"Decodes the Base64 string from the vault file and displays the plaintext result."`

#### Tools Output
```
BASE64 DECODER
Input:  ZGVwbG95bWFzdGVy
Output: deploymaster

Decoded successfully. Input was valid Base64.
```

#### Debrief
```
summary: You decoded a Base64-encoded credential found during analysis of
NexusCorp's vault system artifacts. Base64 is encoding, not encryption —
it provides zero security and is trivially reversed. The username
"deploymaster" opens the internal deployment server.

real_world: Pentesters find Base64-encoded credentials in HTTP Basic Auth
headers, JWT tokens, environment variables, Docker configs, and source code.
Always run suspected Base64 strings through a decoder during recon —
it costs seconds and occasionally hands you credentials in plaintext.

next_step: Practice with real tools:
TryHackMe: "Encoding" room
https://tryhackme.com/room/encodedata

cert_link: PenTest+ PT0-003 Domain 2 — Reconnaissance:
"Analyze discovered artifacts and encoded data to identify credential material."
```

---

### Operation 03 — Port Scan Enumeration

**id:** op03
**title:** Network Sweep
**track:** red
**cert_objective:** PenTest+ PT0-003 Domain 2 — Reconnaissance
**xp_base:** 150
**difficulty:** 2
**tools_type:** port_scanner
**challenge_data:** `"203.0.113.47"`

#### Narrative
```
CIPHER TERMINAL v1.0 — SECURE CHANNEL ESTABLISHED

INCOMING TRANSMISSION FROM: GHOST (CIPHER Field Agent)
CLASSIFICATION: PRIORITY ALPHA

Operative. "deploymaster" got us into the deployment server.
We found the internal network segment NexusCorp uses for their
application tier. One host on that subnet is our next target.

Before we move, we need to know what is running on it.
A port scan will tell us which services are exposed.

TARGET HOST: 203.0.113.47

Run the scan. Identify the open port running the web service.
We move on that port next.

GHOST OUT.
```

#### Challenge
`Which port is the web service running on?`

#### Valid Answers
`["8080", "port 8080"]`

#### Hints
```
Hint 1: Go to https://nmap.org/
        Read "Port Scanning Basics" under the documentation section.
        A web service typically runs on port 80, 443, or a non-standard
        port like 8080. Type 'tools' to run the simulated scan.

Hint 2: In a real engagement you would run (requires nmap installed —
        optional, not required for this exercise):
        nmap -sV 203.0.113.47
        The -sV flag probes open ports to identify the service version.
        In this simulation, type 'tools' to see the scan output.

Hint 3: Type 'tools' in the game. The port scanner will display
        all open ports on 203.0.113.47. Look for the port labeled
        "http" or "http-alt" — that is the web service.

Hint 4: SPOILER — The scan shows port 8080 open with service "http-alt".
        This is a non-standard HTTP port commonly used for dev/staging
        web servers. Type: 8080
```

#### Learn Text
```
A port scan probes a host to find which TCP/UDP ports are open
and what services are listening on them.

Common port numbers to know:
  22   — SSH (remote shell)
  80   — HTTP (web, unencrypted)
  443  — HTTPS (web, encrypted)
  3306 — MySQL database
  8080 — HTTP alternate (dev/staging web servers)
  8443 — HTTPS alternate

Tools used in real engagements:
  nmap    — the standard. Use -sV for version detection.
  masscan — faster for large ranges but noisier.

Port scanning is one of the first steps in active reconnaissance.
It builds a map of the attack surface before exploitation begins.
PenTest+ calls this "enumeration."
```

#### Tools Field
`"Runs a simulated port scan on 203.0.113.47 and displays open ports with service versions."`

#### Tools Output (port_scanner uses target parameter in header)
```
PORT SCANNER — target: {target}

Starting simulated scan...

PORT     STATE    SERVICE    VERSION
22/tcp   open     ssh        OpenSSH 8.9p1
80/tcp   closed   http       -
443/tcp  closed   https      -
3306/tcp filtered mysql      -
8080/tcp open     http-alt   nginx 1.24.0
8443/tcp closed   https-alt  -

Scan complete. 2 open ports found.
```
*Note: `{target}` is replaced with the challenge_data value at runtime.*

#### Debrief
```
summary: You ran a simulated port scan against NexusCorp host 203.0.113.47
and identified port 8080 running a web service (nginx). Port scanning is
the foundation of active reconnaissance — it tells you what doors exist
before you try to open them.

real_world: Every real penetration test begins with port scanning. Testers
use nmap with -sV to enumerate services, then pivot to vulnerability
assessment on each open port. Finding a web server on a non-standard port
like 8080 often means a dev or staging environment — these are frequently
less hardened than production.

next_step: Practice with real tools:
TryHackMe: "Nmap" room
https://tryhackme.com/room/furthernmap

cert_link: PenTest+ PT0-003 Domain 2 — Reconnaissance:
"Given a scenario, perform active reconnaissance using appropriate tools
such as port scanners and service enumeration utilities."
```

---

### Operation 04 — Web Log Analysis

**id:** op04
**title:** Access Logs
**track:** red
**cert_objective:** PenTest+ PT0-003 Domain 2 — Reconnaissance
**xp_base:** 150
**difficulty:** 2
**tools_type:** log_analyzer
**challenge_data:** full log snippet string (see below — stored as single \n-delimited string)

#### challenge_data value (exact string for JSON field)
```
10.0.0.15 - - [11/Apr/2026:02:14:33 +0000] "GET /admin/dashboard HTTP/1.1" 200 4821\n203.0.113.91 - - [11/Apr/2026:01:44:12 +0000] "GET /admin/dashboard HTTP/1.1" 404 512\n203.0.113.44 - - [11/Apr/2026:02:00:05 +0000] "GET / HTTP/1.1" 200 8192\n10.0.0.15 - - [11/Apr/2026:02:14:41 +0000] "GET /admin/dashboard HTTP/1.1" 200 4821\n203.0.113.44 - - [11/Apr/2026:02:00:06 +0000] "GET /about HTTP/1.1" 200 3104\n10.0.0.15 - - [11/Apr/2026:03:02:17 +0000] "GET /admin/dashboard HTTP/1.1" 200 4821\n203.0.113.55 - - [11/Apr/2026:03:15:44 +0000] "GET /login HTTP/1.1" 200 2048
```

#### Narrative
```
CIPHER TERMINAL v1.0 — SECURE CHANNEL ESTABLISHED

INCOMING TRANSMISSION FROM: GHOST (CIPHER Field Agent)
CLASSIFICATION: PRIORITY ALPHA

Operative. Port 8080 on 203.0.113.47 leads to a staging web server.
We got read access to its access logs before the session dropped.

There is an admin panel hidden on this server — not linked from
any page, but someone has been accessing it. The logs will tell us
where it is.

Scan the log for the path that returned HTTP 200 from an internal
IP (10.0.0.x). External IPs get 404 on that path. That is the panel.

GHOST OUT.
```

#### Challenge
`What is the path of the admin panel? (include the leading /)`

#### Valid Answers
`["/admin/dashboard", "/admin/dashboard/"]`

#### Hints
```
Hint 1: Web server access logs record every HTTP request.
        Format: IP - - [timestamp] "METHOD /path HTTP/ver" STATUS SIZE
        Look for requests from internal IPs (10.0.0.x range) that returned
        HTTP status 200 (success). That path is the admin panel.

Hint 2: In a real engagement you would run:
        grep " 200 " access.log | grep "^10\."
        This filters for successful requests from internal IPs.
        Type 'tools' to run the simulated log analyzer.

Hint 3: Type 'tools' in the game. The log analyzer highlights
        all 200-status requests from internal IPs. One path
        appears only in those results — that is the admin panel.

Hint 4: SPOILER — The log shows 10.0.0.15 accessing /admin/dashboard
        with a 200 status. All external IPs get 404 on that path.
        Type: /admin/dashboard
```

#### Learn Text
```
Web server access logs record every HTTP request made to the server.
Standard Apache/nginx log format:

  IP - - [date time] "METHOD /path HTTP/version" STATUS_CODE SIZE

Status codes to know:
  200 — OK (request succeeded)
  301 — Redirect (resource moved)
  403 — Forbidden (resource exists but access blocked)
  404 — Not Found (resource does not exist or is hidden)
  500 — Server Error

During recon, log analysis reveals:
- Hidden paths that return 200 for internal IPs but 404 externally
- Admin panels accessed only from internal network addresses
- Backup files (.bak, .old) that were accidentally served
- Rate of failed logins suggesting brute force attempts

In a real engagement, access to server logs is a goldmine.
Even read-only log access can map the entire application structure.
```

#### Tools Field
`"Parses the server access log and highlights paths returning HTTP 200 from internal IPs (10.0.0.x)."`

#### Tools Output
```
LOG ANALYZER — nexuscorp-access.log

Scanning for 200-status requests from internal IPs (10.0.0.x)...

[MATCH] 10.0.0.15 - - [11/Apr/2026:02:14:33] "GET /admin/dashboard HTTP/1.1" 200 4821
[MATCH] 10.0.0.15 - - [11/Apr/2026:02:14:41] "GET /admin/dashboard HTTP/1.1" 200 4821
[MATCH] 10.0.0.15 - - [11/Apr/2026:03:02:17] "GET /admin/dashboard HTTP/1.1" 200 4821

Other entries (external IPs or non-200):
203.0.113.91 - - [11/Apr/2026:01:44:12] "GET /admin/dashboard HTTP/1.1" 404 512
203.0.113.44 - - [11/Apr/2026:02:00:05] "GET / HTTP/1.1" 200 8192
203.0.113.44 - - [11/Apr/2026:02:00:06] "GET /about HTTP/1.1" 200 3104
203.0.113.55 - - [11/Apr/2026:03:15:44] "GET /login HTTP/1.1" 200 2048

Analysis complete. 1 unique internal path with 200 status found.
```

#### Debrief
```
summary: You analyzed NexusCorp's web server access log and identified
/admin/dashboard — a hidden admin panel accessible only from internal IPs.
Log analysis during recon reveals paths, behaviors, and access patterns
that are invisible from the outside.

real_world: Pentesters review logs whenever they gain read access to a
system. Access logs expose admin panels, backup files, API endpoints,
and credential-stuffing attempts. Even a small log excerpt can
significantly narrow the attack surface before active exploitation begins.

next_step: Practice with real tools:
TryHackMe: "Web Fundamentals" room
https://tryhackme.com/room/webfundamentals

cert_link: PenTest+ PT0-003 Domain 2 — Reconnaissance:
"Given a scenario, perform passive and active reconnaissance to gather
information about targets including web application enumeration."
```

---

### Operation 05 — MD5 Hash Cracking

**id:** op05
**title:** Hash Cracker
**track:** red
**cert_objective:** PenTest+ PT0-003 Domain 3 — Attacks and Exploits
**xp_base:** 200
**difficulty:** 3
**tools_type:** hash_cracker
**challenge_data:** `"5f4dcc3b5aa765d61d8327deb882cf99"`

#### Narrative
```
CIPHER TERMINAL v1.0 — SECURE CHANNEL ESTABLISHED

INCOMING TRANSMISSION FROM: GHOST (CIPHER Field Agent)
CLASSIFICATION: PRIORITY ALPHA

Operative. We found the admin panel at /admin/dashboard.
It requires credentials. We found a config file on the deployment
server that stores the admin password as an MD5 hash. No salt.
Classic mistake.

MD5 hashes can be reversed if the original password appears
in a known wordlist. Run the hash against our dictionary.
If the password is common enough, we will have it in seconds.

HASH: 5f4dcc3b5aa765d61d8327deb882cf99

Crack it. Get the admin password.

GHOST OUT.
```

#### Challenge
`What is the plaintext password behind the hash?`

#### Valid Answers
`["password"]`

#### Hints
```
Hint 1: Go to https://crackstation.net/
        Paste the hash: 5f4dcc3b5aa765d61d8327deb882cf99
        Click "Crack Hashes". CrackStation checks the hash against
        billions of known password hashes instantly.

Hint 2: Run this in a NEW terminal (not in the game):
        python3 -c "import hashlib; words=['password','admin','nexuscorp','letmein','welcome']; h='5f4dcc3b5aa765d61d8327deb882cf99'; [print(w) for w in words if hashlib.md5(w.encode()).hexdigest()==h]"
        The matching word is the password.

Hint 3: Type 'tools' in the game. The hash cracker runs a simulated
        dictionary attack. Watch for the MATCH FOUND line — that word
        is the plaintext password.

Hint 4: SPOILER — MD5("password") = 5f4dcc3b5aa765d61d8327deb882cf99
        This is one of the most commonly cracked hashes in existence.
        Type: password
```

#### Learn Text
```
MD5 is a hashing algorithm — it produces a 128-bit (32 hex character)
fixed-length digest from any input. Hashes are one-way: you cannot
mathematically reverse them. But you can crack them.

Dictionary attack: hash every word in a wordlist and compare to the
target hash. If the password is in the list, you find it instantly.

Why MD5 is broken for passwords:
1. No salt — identical passwords produce identical hashes
2. Fast — a GPU can compute billions of MD5 hashes per second
3. Pre-computed rainbow tables exist for common passwords

The hash 5f4dcc3b5aa765d61d8327deb882cf99 has been in public hash
databases for over a decade. Any cracking tool finds it in milliseconds.

Secure alternatives: bcrypt, scrypt, Argon2 — slow by design,
salted by default. Finding MD5 in a password store is a critical
vulnerability finding in any real engagement.
```

#### Tools Field
`"Runs a simulated MD5 dictionary attack against the hash and displays each attempt with the final match."`

#### Tools Output
```
HASH CRACKER — MD5 dictionary attack
Target: 5f4dcc3b5aa765d61d8327deb882cf99

Loading wordlist... 20 words loaded.

Testing: admin        -> a87ff679a2f3e71d9181a67b7542122c [no match]
Testing: letmein      -> 0d107d09f5bbe40cade3de5c71e9e9b7 [no match]
Testing: welcome      -> 40be4e59b9a2a2b5dffb918c0e86b3d7 [no match]
Testing: nexuscorp    -> 3863d98c7db74b66b6b3ed0e1071c4be [no match]
Testing: 123456       -> e10adc3949ba59abbe56e057f20f883e [no match]
Testing: password     -> 5f4dcc3b5aa765d61d8327deb882cf99 [MATCH FOUND]

Cracked in 6 attempts.
Hash:      5f4dcc3b5aa765d61d8327deb882cf99
Password:  password
```

---

## 10. Open Questions

- [x] Story continuity — confirmed continuous NexusCorp arc (Q2=A)
- [x] Difficulty — 1, 2, 2, 3 approved
- [x] All 4 ops in one stage (Q1=A)
- [x] challenge_data field — defined and hotfixed in Stage 1
- [x] hash_cracker reveal — intentional, educationally justified (§3 rule 4)
- [x] log_analyzer input — uses challenge_data containing full log string
- [x] valid_answers with / — allowed by normalize_input regex (§3 rule 5)

---

## 11. Pre-Flight Checklist

- [x] No engine changes required (challenge_data hotfix already applied)
- [x] All tools_type values already in DATA_MODEL.md allowlist
- [x] challenge_data field defined with exact values for all 5 ops (§4)
- [x] Canonical JSON structure defined (§4)
- [x] Story arc is continuous with explicit references to prior outcomes
- [x] All cert objectives verified against PT0-003 exam domains
- [x] All fictional data uses approved NexusCorp/CIPHER universe
- [x] All valid_answers normalized (lowercase, no special chars except /)
- [x] All hints escalate correctly (URL → Python → tools → spoiler)
- [x] Hint 4 gives full answer with explanation
- [x] op03 Hint 2 notes nmap is optional, not required
- [x] All IPs use RFC 5737 approved ranges (203.0.113.x, 10.0.0.x)
- [x] hash_cracker shows full cracked result — intentional (§3 rule 4)
- [x] port_scanner uses target parameter dynamically in output header
- [x] xp_base increases with difficulty (100, 150, 150, 200)
- [x] All debrief fields present (summary, real_world, next_step, cert_link)
- [x] op04 challenge_data contains full log snippet as \n-delimited string
- [x] op04 valid_answers includes trailing slash variant

---

## 12. Definition of Done

- [ ] All tasks in tasks.md marked complete
- [ ] validate_content.py passes on all 5 ops (op01-op05)
- [ ] check_imports.py passes on all files
- [ ] python -m unittest discover tests/ — all green
- [ ] Full op02 playthrough works end-to-end
- [ ] All 4 new ops visible and unlockable in operation menu
- [ ] spec status → Complete
