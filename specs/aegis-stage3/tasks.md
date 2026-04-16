# tasks.md — AEGIS Stage 3: Cases 14-21
<!--
SDD Phase 3 of 4: Tasks
Prev: plan.md → spec.md
Next: build
-->

**Module:** aegis-stage3
**Date:** 2026-04-12
**Status:** Ready to build

---

## Phase 1 — validate_content.py allowlist update

### Task 01 — Add Stage 3 tools_type values to allowlist

**File:** `aegis/validate_content.py`
**Change:** Add 8 new entries to `_TOOLS_TYPE_ALLOWLIST`.

Final allowlist (append to existing set):
```python
_TOOLS_TYPE_ALLOWLIST = {
    "log_filter", "ioc_classifier", "vuln_scorer", "process_analyzer", "none",
    "traffic_analyzer", "ioc_hunter", "attack_mapper", "rule_analyzer",
    "risk_scorer", "remediation_planner", "exec_reference", "notification_reference",
    "siem_correlator", "log_classifier", "hunt_analyzer", "mem_analyzer",
    "disk_analyzer", "coc_reference", "containment_advisor", "timeline_builder",
}
```

No other changes to validate_content.py.

---

## Phase 2 — tools.py: 8 new tool functions

**File:** `aegis/utils/tools.py`

All functions follow the existing pattern: `def tool_name(challenge_text: str) -> str`.
Use `->` not `→` everywhere in output strings (Windows CP1252 terminal safety).
Add all 8 to `_DISPATCH` at the bottom of the file.

---

### Task 02 — siem_correlator

**Purpose:** Evaluates log events against correlation rules; ALL matching rules fire per event.

**Input format:** `challenge_text` split on `"|||"` → `rules_block` (left) and `events_block` (right).

**Rules parsing** (one rule per `\n`-separated line, skip blank):
```
RULE_ID|CONDITION:field=value [AND field=value]|SEVERITY:level
```
- Strip `"CONDITION:"` prefix from the condition segment.
- Split on `" AND "` to get a list of condition tokens, each `field=value`.

**Events parsing** (one event per `\n`-separated line, skip blank):
```
timestamp|source|event_type|details
```
- Parse into 4 named fields: `timestamp`, `source`, `event_type`, `details`.

**Condition matching logic — for each `field=value` token:**
- If `field == "event_type"`: check `event_type == value` (exact, case-sensitive).
- For all other fields: check if `field=value` (the whole string, e.g. `"source=external"`) appears as a substring in the event's `details` field.
- A rule fires on an event only if ALL its condition tokens match.
- Evaluate ALL rules against EACH event — collect ALL matches (not first-match).

**Output format:**
```
SIEM CORRELATOR — alert correlation engine

Rules loaded: N
Events to process: N

Evaluating events...

[ALERT — SEVERITY] RULE_ID fired on event: TIMESTAMP
  Rule: rule description line from rule name
  Event: source | event_type | details
  Conditions matched: field=value [check] | field=value [check]

No alert fired on: TIMESTAMP
  [reason why no rule matched]

Summary: N alerts fired | Highest severity: SEVERITY (RULE_ID)
```

Severity ordering (for highest-severity display): CRITICAL > HIGH > MEDIUM > LOW.
If no alerts fired at all: output `"Summary: 0 alerts fired"`.

**Done-when:** For challenge_data in case14 (4 rules, 6 events), `siem_correlator(data)` output contains:
- `"[ALERT — CRITICAL] R002 fired"`
- `"[ALERT — HIGH] R001 fired"` (twice — events 22:14:01 and 22:14:03)
- `"[ALERT — MEDIUM] R003 fired"`
- `"[ALERT — HIGH] R004 fired"`
- No alert on 22:18:00 (source=internal)
- `"Highest severity: CRITICAL"`

---

### Task 03 — log_classifier

**Purpose:** Maps each event description line to its primary log source.

**Input format:** `challenge_text` split on `"\n"`, one event description per line, skip blank.

**Matching logic:**
- Lowercase each event description line.
- For each entry in the embedded reference table, check if any keyword phrase for that entry appears as a substring in the lowercased line.
- Use the FIRST matching entry (table order).
- If no entry matches: return `"Unknown — manual investigation required"`.

**Embedded reference table** (hardcoded, checked in order):
```python
_LOG_SOURCE_TABLE = [
    {"keywords": ["failed login", "authentication failure", "invalid password", "logon failure"],
     "source": "Windows Security Log (Event 4625) / Linux /var/log/auth.log"},
    {"keywords": ["successful login", "accepted password", "logon success", "auth_success"],
     "source": "Windows Security Log (Event 4624) / Linux /var/log/auth.log"},
    {"keywords": ["account created", "new user", "useradd"],
     "source": "Windows Security Log (Event 4720) / Linux /var/log/auth.log"},
    {"keywords": ["privilege escalation", "sudo", "elevated"],
     "source": "Linux /var/log/auth.log / Windows Security Log (Event 4672)"},
    {"keywords": ["process created", "new process", "cmd.exe", "powershell"],
     "source": "Windows Security Log (Event 4688) / Sysmon (Event 1)"},
    {"keywords": ["network connection", "outbound connection", "outbound traffic", "port scan"],
     "source": "Firewall logs / Windows Security Log (Event 5156)"},
    {"keywords": ["dns query", "domain lookup", "nslookup"],
     "source": "DNS server logs / Sysmon (Event 22)"},
    {"keywords": ["file created", "file modified", "file deleted"],
     "source": "Windows Security Log (Event 4663) / Sysmon (Event 11)"},
    {"keywords": ["web request", "http", "get /", "post /", "nginx", "apache"],
     "source": "Web server access logs (nginx/apache access.log)"},
    {"keywords": ["email sent", "email received", "smtp", "phishing"],
     "source": "Email gateway logs / Exchange logs"},
    {"keywords": ["usb inserted", "usb device", "removable media", "device inserted", "device connected"],
     "source": "Windows Security Log (Event 6416) / udev logs"},
    {"keywords": ["firewall blocked", "connection denied", "dropped packet"],
     "source": "Firewall logs / Windows Filtering Platform (Event 5157)"},
    {"keywords": ["vpn connected", "remote access", "tunnel established"],
     "source": "VPN gateway logs / RADIUS logs"},
    {"keywords": ["scheduled task", "schtasks", "task created"],
     "source": "Windows Security Log (Event 4698) / Linux /var/log/syslog"},
    {"keywords": ["registry modified", "reg add", "regedit"],
     "source": "Windows Security Log (Event 4657) / Sysmon (Event 13)"},
]
```

**Output format:**
```
LOG CLASSIFIER — event source mapping

Classifying N event descriptions...

[1] original event description text
    Primary source: Windows Security Log (Event 4625) / Linux /var/log/auth.log
    Reason: Authentication failure event

[2] ...

Classification complete. N/N events mapped to log sources.
```

Reason line: use a short human-readable description of the matched category
(e.g., "Authentication failure event", "Network connection event",
"Scheduled task creation event", "Device connection event").
If no match: `"Reason: No matching log source found — manual investigation required"`.

**Done-when:** For challenge_data in case15 (6 lines), `log_classifier(data)` output:
- Line 1 "failed login" → `"Event 4625"`
- Line 2 "outbound connection" → `"Firewall logs"`
- Line 3 "DNS query" → `"DNS server logs"`
- Line 4 "scheduled task created" → `"Event 4698"`
- Line 5 "powershell.exe spawned" → `"Event 4688"`
- Line 6 "USB device inserted" → `"Event 6416"`

---

### Task 04 — hunt_analyzer

**Purpose:** Scores evidence items against a threat hunting hypothesis.

**Input format:** `challenge_text` split on `"|||"` → `hypothesis` (left), `evidence_block` (right).
Evidence: one item per `"\n"`-separated line in format `source:value`. Skip blank lines.
For each item, `source` is the part before the first `:`, `value` is everything after.

**Classification logic for each evidence item:**
1. Lowercase the `value`.
2. Check against embedded LOLBAS reference (below): if any keyword phrase from the table
   appears as a substring in the lowercased value → classify as `[SUPPORTS]`.
3. If no LOLBAS match: check against embedded normal process list (below):
   if any pattern matches → classify as `[REFUTES]`.
4. Otherwise → classify as `[NEUTRAL]`.

**Embedded LOLBAS reference** (hardcoded):
```python
_LOLBAS_TABLE = [
    {"keywords": ["powershell -enc", "powershell -encodedcommand", "-nop -w hidden", "powershell -nop"],
     "technique": "T1059.001 — PowerShell encoded command (-enc/-EncodedCommand)"},
    {"keywords": ["certutil -decode", "certutil -urlcache"],
     "technique": "T1105 — Ingress Tool Transfer via certutil"},
    {"keywords": ["wmic process call create"],
     "technique": "T1047 — Windows Management Instrumentation"},
    {"keywords": ["regsvr32 /s", "regsvr32 /u"],
     "technique": "T1218.010 — Regsvr32 bypass"},
    {"keywords": ["mshta vbscript", "mshta javascript"],
     "technique": "T1218.005 — Mshta bypass"},
    {"keywords": ["bitsadmin /transfer"],
     "technique": "T1197 — BITS Jobs"},
    {"keywords": ["schtasks /create"],
     "technique": "T1053.005 — Scheduled Task"},
    {"keywords": ["net use", "net share", "net localgroup"],
     "technique": "T1021 — Remote Services"},
    {"keywords": ["rundll32 javascript"],
     "technique": "T1218.011 — Rundll32 bypass"},
    {"keywords": ["cmd /c echo", "cmd /c copy"],
     "technique": "T1059.003 — Windows Command Shell"},
    {"keywords": ["currentversion\\run", "currentversion/run", "run key"],
     "technique": "T1547.001 — Boot/Logon Autostart: Registry Run Keys"},
]
```

**Embedded normal process list** (patterns that indicate known-benign activity → `[REFUTES]`):
```python
_NORMAL_PATTERNS = [
    "svchost.exe -k",           # normal Windows service host with service group
    "parent=userinit.exe",      # normal explorer.exe parent
    "parent=services.exe",      # normal svchost parent
    "lsass.exe",                # normal credential subsystem
    "csrss.exe",                # normal client/server runtime
]
```

**Confidence score:**
```
confidence = int(SUPPORTS / (SUPPORTS + REFUTES) * 100)
```
If `SUPPORTS + REFUTES == 0`: confidence = 0.
NEUTRAL items are excluded from the denominator.

**Output format:**
```
HUNT ANALYZER — hypothesis-driven threat hunt

Hypothesis: [hypothesis text]
Processing N evidence items...

[SUPPORTS] source: value
  Technique: T1059.001 — PowerShell encoded command (-enc/-EncodedCommand)
  [short explanation]

[REFUTES] source: value
  [short explanation of why this is normal/refuting]

[NEUTRAL] source: value
  [short explanation]

Results:
  SUPPORTS: N | REFUTES: N | NEUTRAL: N
  Confidence score: N / (N + N) x 100 = N%

ASSESSMENT: [HIGH CONFIDENCE / MODERATE CONFIDENCE / LOW CONFIDENCE / INSUFFICIENT EVIDENCE]
  HIGH:       >= 75%
  MODERATE:   >= 50%
  LOW:        >= 25%
  INSUFFICIENT: < 25% or confidence = 0
```

Use `x` not `×` in the confidence formula line (Windows CP1252 safe).

**Done-when:** For challenge_data in case16 (7 evidence items), `hunt_analyzer(data)` output:
- powershell → `[SUPPORTS]`
- certutil → `[SUPPORTS]`
- svchost -k → `[REFUTES]`
- network → `[NEUTRAL]`
- /tmp/update.sh → `[NEUTRAL]`
- registry Run → `[SUPPORTS]`
- explorer parent=userinit → `[REFUTES]`
- `"Confidence score: 3 / (3 + 2) x 100 = 60%"`
- `"MODERATE CONFIDENCE"`

---

### Task 05 — mem_analyzer

**Purpose:** Flags suspicious memory regions from a parsed memory map.

**Input format:** One entry per `"\n"`-separated line (skip blank):
```
PID:N name:PROC base:0xADDR size:N permissions:rwx path:/path/or/[anon]
```
Parse each field by prefix matching: split line on spaces, find token starting with each prefix
(`"PID:"`, `"name:"`, `"base:"`, `"size:"`, `"permissions:"`, `"path:"`).
The `path:` token may contain backslashes or brackets — everything after `"path:"` is the path value.
Since path may include spaces (e.g., `C:\Windows\System32\...`), the path field is everything
in the original line after the `"path:"` prefix.

**Flag logic — evaluate in priority order (first match wins):**
1. `[MALICIOUS]` if `name` (lowercased) is in:
   `{"mimikatz", "meterpreter", "cobalt", "beacon", "cobaltstrike", "empire", "metasploit"}`
2. `[SUSPICIOUS]` if `permissions` contains `"x"` AND
   (`path == "[anon]"` OR `path.startswith("/tmp/")` OR `path.startswith("/dev/shm/")`).
3. `[ANOMALY]` if `size > 50000` AND `name` (lowercased) in:
   `{"svchost", "lsass", "csrss", "smss", "wininit", "winlogon"}`
4. `[OK]` otherwise.

**Output format:**
```
MEM ANALYZER — memory forensics

Scanning N memory entries...

PID:N   name   perms   path (truncated)   [FLAG] reason

FINDINGS:
  [FLAG] PID N — 'name': reason
    Base: 0xADDR | Size: N bytes
    [detail line]
    Recommend: [action]

  (only MALICIOUS, SUSPICIOUS, ANOMALY entries appear in FINDINGS — not OK)
```

If no findings: output `"FINDINGS: None — no suspicious regions detected"`.

**Done-when:** For challenge_data in case17 (6 entries), `mem_analyzer(data)` output:
- PID 1337 (update, rwx, [anon]) → `[SUSPICIOUS]`
- PID 3999 (svchost, size=102400) → `[ANOMALY]`
- All others → `[OK]`
- FINDINGS section contains entries for PID 1337 and PID 3999 only

---

### Task 06 — disk_analyzer

**Purpose:** Flags suspicious file system entries; sorts by suspicion priority.

**Input format:** One entry per `"\n"`-separated line (skip blank), 7 pipe-separated fields:
```
filename|size|created|modified|accessed|deleted:yes/no|path
```
Field 6 is `"deleted:yes"` or `"deleted:no"` — strip the `"deleted:"` prefix to get `"yes"`/`"no"`.

**Flag logic — evaluate in priority order (first match is the PRIMARY flag):**
1. `[MALICIOUS]` if `filename` (lowercased) contains any of:
   `["mimikatz", "meterpreter", "nc.exe", "ncat", "netcat", "pwdump", "fgdump", "wce.exe", "gsecdump"]`
2. `[DELETED]` if deleted field (lowercased) == `"yes"`
3. `[TIMESTOMPED]` if `modified < created` (ISO string comparison — earlier string is smaller)
4. `[SUSPICIOUS]` if path contains any of:
   `["/tmp/", "/dev/shm/", "\\Temp\\", "\\AppData\\Local\\Temp\\"]`
5. `[OK]` otherwise

**Important:** The primary flag determines sort order. But additional properties
(deleted=yes, timestomped) are ALWAYS noted in output even if not the primary flag.
Example: `mimikatz.exe` is `[MALICIOUS]` (primary), but the output notes it is also
DELETED and TIMESTOMPED.

**Sort order:** MALICIOUS first, then DELETED, then TIMESTOMPED, then SUSPICIOUS, then OK.

**Output format:**
```
DISK ANALYZER — file system forensics

Analyzing N file entries...

[MALICIOUS] filename — known credential dumping tool
  Size: NB | Path: path
  Status: DELETED (recovery possible from unallocated space)
  TIMESTOMPED: modified=YYYY-MM-DD < created=YYYY-MM-DD (impossible — timestamp manipulated)

[DELETED] filename
  Size: NB | Path: path
  Created: YYYY-MM-DD | Timestamps consistent (no timestomping)
  Recommend: recover from $MFT or unallocated space

[SUSPICIOUS] filename
  Path: path — non-standard location
  Created: TIMESTAMP — [note if during attack window]

[OK] filename
  Path: path — legitimate system file

Summary: N MALICIOUS | N DELETED | N TIMESTOMPED | N SUSPICIOUS | N OK
Priority finding: [top finding description]
```

Summary line counts each file once by its PRIMARY flag.

**Done-when:** For challenge_data in case18 (6 entries), `disk_analyzer(data)` output:
- mimikatz.exe → `[MALICIOUS]` (primary), also notes DELETED and TIMESTOMPED
- nightwire.exe → `[DELETED]`
- payload.b64 → `[DELETED]`
- update.bat → `[SUSPICIOUS]` (path: `\Windows\Temp\`)
- svchost.exe → `[OK]`
- config.sys → `[OK]`
- mimikatz.exe appears FIRST in output
- `"Summary: 1 MALICIOUS | 2 DELETED | 0 TIMESTOMPED | 1 SUSPICIOUS | 2 OK"`

Note: mimikatz.exe's TIMESTOMPED property is noted in its entry, but summary
counts it as MALICIOUS (primary flag), not TIMESTOMPED.

---

### Task 07 — containment_advisor

**Purpose:** Scores and ranks containment options against scenario parameters.

**Input format:** `challenge_text` split on `"|"`, each token is `key:value` (case-insensitive keys).
Required keys: `asset`, `threat`, `dwell` (integer), `data_sensitivity`, `attribution`.

**Scoring table — 4 options:**

```
Full Isolation (network + account lockout):
  effectiveness: 5
  tip_risk: 5 if (attribution == "known" AND dwell > 14) else 3

Network Isolation (block outbound, keep monitoring):
  effectiveness: 4
  tip_risk: 2

Monitoring Only (observe and collect):
  effectiveness: 2
  tip_risk: 1

Account Lockout Only:
  effectiveness: 3
  tip_risk: 4 if attribution == "known" else 2
```

**Net score** = effectiveness - tip_risk.
**Rank:** sort options by net score descending. Tie-break: lower tip_risk wins.
**Top recommendation** = option with highest net score.

**Output format:**
```
CONTAINMENT ADVISOR — strategy recommendation

Input parameters:
  Asset:            asset_value
  Threat level:     threat_value
  Dwell time:       N days
  Data sensitivity: data_sensitivity_value
  Attribution:      attribution_value

Scoring containment options (effectiveness - tip_risk = net score)...

OPTION 1: Full Isolation (network + account lockout)
  Effectiveness:  N/5 — [description]
  Tip-off risk:   N/5 — [reason]
  Net score:      N
  [Risk or rationale note]

OPTION 2: Network Isolation (block outbound C2, maintain internal monitoring)
  Effectiveness:  N/5 — [description]
  Tip-off risk:   N/5 — [reason]
  Net score:      N   [<- RECOMMENDED if top]
  [Rationale note]

OPTION 3: Monitoring Only
  ...

OPTION 4: Account Lockout Only
  ...

RECOMMENDATION: [Option Name]
  [2-3 line rationale]
```

Options are always output in the order: Full Isolation, Network Isolation, Monitoring Only,
Account Lockout Only — regardless of ranking. The `<- RECOMMENDED` marker appears inline
on the net score line of the top option.

**Done-when:** For challenge_data in case20:
`"asset:domain_controller|threat:critical|dwell:42|data_sensitivity:restricted|attribution:known"`
- Full Isolation: tip_risk=5 (known + dwell=42>14), net=0
- Network Isolation: effectiveness=4, tip_risk=2, net=2 ← RECOMMENDED
- Monitoring Only: net=1
- Account Lockout: tip_risk=4 (known), net=-1
- `"RECOMMENDATION: Network Isolation"` in output

---

### Task 08 — timeline_builder

**Purpose:** Sorts timeline events, annotates gaps, labels IR phases.

**Input format:** One event per `"\n"`-separated line (skip blank), 3 pipe-separated fields:
```
timestamp|source|event_description
```
Timestamps are ISO format: `YYYY-MM-DDTHH:MM:SS`.

**Sorting:** Sort events by timestamp string ascending (ISO format sorts lexicographically).

**Gap detection:**
Parse timestamps using `datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")`.
If the difference between two consecutive events > 3600 seconds (1 hour):
insert a gap annotation line between them:
`"[GAP: Xh Ym — no recorded activity]"`
where X = total_seconds // 3600, Y = (total_seconds % 3600) // 60.

**Phase labeling** — check `event_description.lower()` for keywords:
```python
_PHASE_KEYWORDS = {
    "Preparation": ["policy", "playbook", "training", "alert rule", "monitor"],
    "Detection":   ["alert", "anomaly", "detected", "identified", "flagged", "triggered"],
    "Containment": ["isolated", "blocked", "disabled", "contained", "quarantine"],
    "Eradication": ["removed", "deleted", "patched", "cleaned", "reimaged"],
    "Recovery":    ["restored", "verified", "monitoring", "normal operations", "returned"],
}
```
Assign the FIRST matching phase (in the order listed above). If no keyword matches: `"Unknown"`.

**Phase summary:** After the timeline, output a summary section listing the timestamp of the
first event in each IR phase that appeared (only list phases that actually appear in the data).
Also output total dwell time (first event to last Containment event) and largest gap.

**Output format:**
```
TIMELINE BUILDER — incident reconstruction

Sorting N events from N sources...

[Phase]        TIMESTAMP  source    event_description

[GAP: Xh Ym — no recorded activity]

[Phase]        TIMESTAMP  source    event_description
...

Phase summary:
  [Phase] phase started:    TIMESTAMP
  ...
  Total dwell time:           ~N hours (N.N days)
  Largest gap:                Xh Ym (label)
```

For dwell time: from first event timestamp to first Containment-phase event timestamp.
Format: `~N hours (N.N days)` where hours is rounded and days = hours/24 rounded to 1 decimal.
If no Containment event: use last event timestamp instead.

**Done-when:** For challenge_data in case21 (11 events), `timeline_builder(data)` output:
- Events sorted chronologically with 2026-03-20 events first
- Gap annotation between 2026-03-20T14:02 and 2026-04-05T22:14 shows `"392h 12m"`
- Gap annotation between 2026-04-05T22:20 and 2026-04-11T03:15 shows `"124h 55m"`
- Event `"mimikatz.exe executed then deleted"` labeled `[Eradication]` (contains "deleted")
- Event `"NexusCorp attacker detected"` labeled `[Detection]` (contains "detected")
- Event `"DC-01 network isolated"` labeled `[Containment]` (contains "isolated")
- Events 1-5 (no keywords) labeled `[Unknown]`
- Phase summary includes Detection started `2026-04-11T03:15:00`
- Phase summary includes Containment started `2026-04-11T03:45:00`

---

### Task 09 — coc_reference (static)

**Purpose:** Returns hardcoded chain of custody reference table. Ignores input entirely.

Same pattern as `exec_reference` and `notification_reference` — `challenge_text` parameter
accepted but never used.

**Output:** Return the fixed string (verbatim from spec section 5, case19, Tools Output):
```
CHAIN OF CUSTODY REFERENCE — digital evidence handling

STEP 1: DOCUMENT THE SCENE
  Photograph evidence in place before touching anything.
  Record: location, date, time, who discovered it, system state.

STEP 2: HASH THE EVIDENCE (CRITICAL — DO THIS FIRST)
  Generate SHA-256 (preferred) or MD5 hash of the original evidence.
  Record the hash in the evidence log.
  This is the integrity baseline — proves evidence was not altered.

STEP 3: USE WRITE BLOCKERS
  For physical drives: attach write blocker before connecting to analysis system.
  Write blockers prevent any data from being written to the evidence drive.
  Without a write blocker, simply connecting a drive modifies timestamps.

STEP 4: CREATE FORENSIC COPIES
  Image the evidence using FTK Imager, dd, or similar tool.
  Verify copy hash matches original hash.
  Analyze only the forensic copy — NEVER the original.

STEP 5: SEAL AND STORE ORIGINALS
  Place physical evidence in tamper-evident evidence bags.
  Label with: case number, exhibit number, collector name, date/time.
  Store in secured evidence room with access log.

DOCUMENTATION REQUIREMENTS (each custody transfer):
  Transferring party: name, role, signature
  Receiving party: name, role, signature
  Date and time of transfer
  Reason for transfer
  Evidence description and hash value
  Storage location before and after

COMMON ERRORS TO AVOID:
  - Analyzing originals (use forensic copies)
  - No write blocker during imaging (modifies evidence)
  - Missing hash at collection (cannot prove integrity)
  - Undocumented transfers (breaks chain)
  - Unauthorized access (chain is broken)
```

**Done-when:** `coc_reference("")` and `coc_reference("anything")` both return the same
string containing `"STEP 2: HASH THE EVIDENCE"` and `"COMMON ERRORS TO AVOID"`.

---

### Task 10 — Update _DISPATCH

**File:** `aegis/utils/tools.py`

Add 8 new entries to `_DISPATCH` dict:
```python
"siem_correlator":    siem_correlator,
"log_classifier":     log_classifier,
"hunt_analyzer":      hunt_analyzer,
"mem_analyzer":       mem_analyzer,
"disk_analyzer":      disk_analyzer,
"coc_reference":      coc_reference,
"containment_advisor": containment_advisor,
"timeline_builder":   timeline_builder,
```

---

## Phase 3 — Unit Tests

**File:** `aegis/tests/test_tools_stage3.py`

Follow the pattern from `test_tools_stage2.py`:
- Import from `aegis.utils.tools` using the individual function names
- One `unittest.TestCase` subclass per tool
- Each test method name describes exactly what is being asserted
- All tests deterministic (no randomness, no I/O)

---

### Task 11 — TestSiemCorrelator (5 tests)

```
test_critical_alert_fires
  Input: case14 challenge_data
  Assert: "[ALERT — CRITICAL] R002" in result

test_high_alert_fires_twice
  Input: case14 challenge_data
  Assert: result.count("[ALERT — HIGH] R001") == 2

test_no_alert_for_internal_source
  Input: case14 challenge_data
  Assert: "No alert fired on: 2026-04-05T22:18:00" in result

test_highest_severity_in_summary
  Input: case14 challenge_data
  Assert: "Highest severity: CRITICAL" in result

test_all_matching_rules_fire
  Input: single event matching both R003 and R004
  Rules: "R003|CONDITION:event_type=process_create AND details=powershell|SEVERITY:medium\n
          R004|CONDITION:event_type=network_connect AND details=port=4444|SEVERITY:high"
  Event that matches R003: "2026-01-01T00:00:01|host|process_create|details=powershell"
  Assert both "[ALERT — MEDIUM] R003" and (result does not contain R004 alert for R003 event)
  NOTE: This test verifies that ONLY matching rules fire, not all rules for all events.
  Simpler: use two events (one for each rule), assert both alerts appear in the output.
  Final test: result contains both "[ALERT — MEDIUM] R003" and "[ALERT — HIGH] R004".
```

---

### Task 12 — TestLogClassifier (5 tests)

```
test_failed_login_maps_to_security_log
  Input: "failed login attempt for user admin"
  Assert: "Event 4625" in result

test_dns_query_maps_to_dns_logs
  Input: "DNS query for malicious-domain.com"
  Assert: "DNS server logs" in result

test_scheduled_task_maps_to_event_4698
  Input: "new scheduled task created: WindowsUpdate"
  Assert: "Event 4698" in result

test_usb_maps_to_event_6416
  Input: "USB device inserted: SanDisk 64GB"
  Assert: "Event 6416" in result

test_no_match_returns_unknown
  Input: "quantum entanglement event observed"
  Assert: "Unknown" in result
```

---

### Task 13 — TestHuntAnalyzer (6 tests)

```
test_powershell_enc_is_supports
  Input: "LOLBAS hypothesis|||process:powershell.exe -enc AAAA"
  Assert: "[SUPPORTS]" in result

test_certutil_decode_is_supports
  Input: "LOLBAS hypothesis|||process:certutil.exe -decode file.b64"
  Assert: "[SUPPORTS]" in result

test_svchost_normal_is_refutes
  Input: "LOLBAS hypothesis|||process:svchost.exe -k netsvcs"
  Assert: "[REFUTES]" in result

test_confidence_60_percent_case16
  Input: case16 challenge_data (7 items)
  Assert: "60%" in result

test_confidence_zero_all_neutral
  Input: "LOLBAS hypothesis|||network:192.168.1.1\nfile:document.docx"
  Assert: "0%" in result OR "INSUFFICIENT EVIDENCE" in result

test_registry_run_is_supports
  Input: "LOLBAS hypothesis|||registry:HKLM\\CurrentVersion\\Run modified"
  Assert: "[SUPPORTS]" in result
```

---

### Task 14 — TestMemAnalyzer (5 tests)

```
test_rwx_anon_is_suspicious
  Input: "PID:1337 name:update base:0xFF001000 size:65536 permissions:rwx path:[anon]"
  Assert: "[SUSPICIOUS]" in result

test_large_svchost_is_anomaly
  Input: "PID:3999 name:svchost base:0x00200000 size:102400 permissions:r-x path:C:\\Windows\\System32\\svchost.exe"
  Assert: "[ANOMALY]" in result

test_normal_process_is_ok
  Input: "PID:2048 name:explorer base:0x00400000 size:8192 permissions:r-x path:C:\\Windows\\explorer.exe"
  Assert: "[OK]" in result

test_malicious_name_is_malicious
  Input: "PID:9999 name:mimikatz base:0x10000000 size:1024 permissions:r-x path:C:\\Temp\\mimikatz.exe"
  Assert: "[MALICIOUS]" in result

test_case17_finds_pid_1337
  Input: case17 challenge_data (6 entries)
  Assert: "PID 1337" in result AND "[SUSPICIOUS]" in result
```

---

### Task 15 — TestDiskAnalyzer (6 tests)

```
test_mimikatz_is_malicious
  Input: "mimikatz.exe|1245184|2026-04-05T22:20:00|2026-03-01T00:00:00|2026-04-05T22:20:00|deleted:yes|C:\\Users\\Public\\Downloads\\mimikatz.exe"
  Assert: "[MALICIOUS]" in result

test_timestomped_detected
  Input: "tool.exe|1024|2026-04-05T10:00:00|2026-04-01T00:00:00|2026-04-05T10:00:00|deleted:no|C:\\Windows\\tool.exe"
  Assert: "[TIMESTOMPED]" in result

test_deleted_file_flagged
  Input: "payload.bin|8192|2026-04-05T22:14:00|2026-04-05T22:14:00|2026-04-05T22:14:00|deleted:yes|C:\\Temp\\payload.bin"
  Assert: "[DELETED]" in result

test_suspicious_path_flagged
  Input: "script.sh|512|2026-04-05T22:14:00|2026-04-05T22:14:00|2026-04-05T22:14:00|deleted:no|/tmp/script.sh"
  Assert: "[SUSPICIOUS]" in result

test_malicious_takes_priority_over_deleted
  Input: "mimikatz.exe|512|2026-04-05T10:00:00|2026-04-05T10:00:00|2026-04-05T10:00:00|deleted:yes|C:\\Temp\\mimikatz.exe"
  Assert: "[MALICIOUS]" in result (not "[DELETED]" as primary flag)
  Assert: result.index("[MALICIOUS]") < result.index("[DELETED]") — malicious appears first in output

test_case18_summary_line
  Input: case18 challenge_data (6 entries)
  Assert: "1 MALICIOUS" in result AND "2 DELETED" in result AND "1 SUSPICIOUS" in result
```

---

### Task 16 — TestContainmentAdvisor (4 tests)

```
test_case20_recommends_network_isolation
  Input: "asset:domain_controller|threat:critical|dwell:42|data_sensitivity:restricted|attribution:known"
  Assert: "RECOMMENDATION: Network Isolation" in result

test_full_isolation_high_tip_risk_when_known_long_dwell
  Input: "asset:server|threat:critical|dwell:42|data_sensitivity:restricted|attribution:known"
  Assert: "Tip-off risk:   5/5" in the Full Isolation section of result

test_full_isolation_lower_tip_risk_when_short_dwell
  Input: "asset:workstation|threat:high|dwell:5|data_sensitivity:internal|attribution:unknown"
  Full Isolation tip_risk should be 3 (dwell <= 14)
  Assert: result contains "Tip-off risk:   3/5" (in Full Isolation section)

test_monitoring_only_net_score_is_1
  Input: any valid input
  Assert: the Monitoring Only section contains "Net score:      1"
```

---

### Task 17 — TestTimelineBuilder (6 tests)

```
test_events_sorted_chronologically
  Input: two events out of order:
    "2026-04-05T22:16:30|firewall|C2 beacon\n2026-03-20T14:00:00|disk|file dropped"
  Assert: "2026-03-20" appears before "2026-04-05" in result

test_gap_over_1_hour_annotated
  Input: same two events (392h gap)
  Assert: "[GAP:" in result

test_no_gap_for_events_within_1_hour
  Input: "2026-04-05T22:14:00|syslog|event A\n2026-04-05T22:16:00|sysmon|event B"
  (2 minutes apart — no gap)
  Assert: "[GAP:" not in result

test_deleted_keyword_labels_eradication
  Input: "2026-04-05T22:20:00|disk|mimikatz.exe executed then deleted"
  Assert: "[Eradication]" in result

test_isolated_keyword_labels_containment
  Input: "2026-04-11T03:45:00|ir_team|DC-01 network isolated"
  Assert: "[Containment]" in result

test_case21_gap_annotation_392h
  Input: case21 challenge_data (11 events)
  Assert: "392h 12m" in result
```

---

## Phase 4 — Case JSON Files (case14-21)

Each case file lives at `aegis/content/cases/caseNN.json`.
All fields are required. Escape `\n` as literal `\\n` in challenge_data strings within JSON.
The `"tools"` field is a string (tool description shown to player). The `"learn"` field is a string.
`"valid_answers"` is a list of lowercase strings.

---

### Task 18 — Write case14.json through case21.json

Write all 8 case files. Content verbatim from spec.md section 5, with these reminders:

**case14** — siem_correlator, difficulty 3, xp_base 150
- challenge_data: the 4-rule, 6-event block (rules `|||` events, `\n`-separated within each block)
- valid_answers: `["critical", "critical severity"]`
- tools: `"Evaluates each event against the active correlation rules and reports all alerts that fired with their severity levels."`

**case15** — log_classifier, difficulty 3, xp_base 150
- challenge_data: 6 event description lines `\n`-separated
- valid_answers: `["windows security log", "security log", "event 4698", "windows security log (event 4698)", "sysmon"]`
- tools: `"Maps each event description to its primary log source using the embedded event type reference table."`

**case16** — hunt_analyzer, difficulty 4, xp_base 250
- challenge_data: `"NIGHTWIRE is using...\|\|\|process:powershell...\nprocess:certutil..."`
- valid_answers: `["60", "60%", "60 percent"]`
- tools: `"Evaluates each evidence item against the hunt hypothesis and calculates a confidence score based on supporting vs refuting evidence."`

**case17** — mem_analyzer, difficulty 3, xp_base 150
- challenge_data: 6 memory entries `\n`-separated
- valid_answers: `["1337", "pid 1337", "pid:1337"]`
- tools: `"Analyzes a memory map for injection indicators: anonymous executable regions, RWX permissions, anomalous process sizes, and known malicious process names."`

**case18** — disk_analyzer, difficulty 4, xp_base 250
- challenge_data: 6 file entries `\n`-separated
- valid_answers: `["mimikatz.exe", "mimikatz"]`
- tools: `"Analyzes file system entries for malicious filenames, deleted files, timestomping, and suspicious paths."`

**case19** — coc_reference, difficulty 3, xp_base 150
- challenge_data: the scenario question string (ignored by the tool)
- valid_answers: `["hash", "hash value", "cryptographic hash", "sha256", "md5", "integrity hash", "evidence hash", "checksum"]`
- tools: `"Displays the chain of custody reference including collection steps, documentation requirements, storage procedures, and common errors."`

**case20** — containment_advisor, difficulty 4, xp_base 250
- challenge_data: `"asset:domain_controller|threat:critical|dwell:42|data_sensitivity:restricted|attribution:known"`
- valid_answers: `["network isolation", "network isolation only", "isolate network", "block outbound", "network segment"]`
- tools: `"Scores containment options (full isolation, network isolation, monitoring, account lockout) against scenario parameters and recommends the best strategy."`

**case21** — timeline_builder, difficulty 4, xp_base 250
- challenge_data: 11 timeline events `\n`-separated
- valid_answers: `["392", "392 hours", "approximately 392 hours", "about 392 hours"]`
- tools: `"Sorts timeline events chronologically, identifies gaps over 1 hour, labels each event with the appropriate IR phase, and summarizes phase transitions."`

**All 8 cases share:**
- `"track": "blue"`
- `"cert_objective"`: Domain 1 for case14-16, Domain 3 for case17-21
- `"hints"`: exactly 4 items (escalating: URL → manual → tools → spoiler)
- `"debrief"`: object with `summary`, `real_world`, `next_step`, `cert_link`, `exam_tip`

Verify each file passes `validate_case()` mentally before writing:
- hints.length == 4
- valid_answers is non-empty list
- difficulty in {1,2,3,4}
- tools_type in allowlist (after Task 01)
- debrief has all 5 required keys

---

## Phase 5 — Registry Update

### Task 19 — Extend registry.json with case14-21

**File:** `aegis/content/registry.json`

Append 8 entries to the `"cases"` array (after case13):

```json
{"id": "case14", "title": "SIEM Triage",      "status": "active", "difficulty": 3,
 "cert_objective": "CySA+ CS0-003 Domain 1 — Security Operations"},
{"id": "case15", "title": "Log Sources",       "status": "active", "difficulty": 3,
 "cert_objective": "CySA+ CS0-003 Domain 1 — Security Operations"},
{"id": "case16", "title": "Threat Hunt",       "status": "active", "difficulty": 4,
 "cert_objective": "CySA+ CS0-003 Domain 1 — Security Operations"},
{"id": "case17", "title": "Memory Forensics",  "status": "active", "difficulty": 3,
 "cert_objective": "CySA+ CS0-003 Domain 3 — Incident Response"},
{"id": "case18", "title": "Disk Forensics",    "status": "active", "difficulty": 4,
 "cert_objective": "CySA+ CS0-003 Domain 3 — Incident Response"},
{"id": "case19", "title": "Chain of Custody",  "status": "active", "difficulty": 3,
 "cert_objective": "CySA+ CS0-003 Domain 3 — Incident Response"},
{"id": "case20", "title": "Containment",       "status": "active", "difficulty": 4,
 "cert_objective": "CySA+ CS0-003 Domain 3 — Incident Response"},
{"id": "case21", "title": "Timeline",          "status": "active", "difficulty": 4,
 "cert_objective": "CySA+ CS0-003 Domain 3 — Incident Response"}
```

---

## Done-When (module level)

- [ ] `python aegis/validate_content.py` exits 0 (all 21 cases pass)
- [ ] `python aegis/check_imports.py` exits 0
- [ ] `python -m pytest aegis/tests/ -v` shows all tests passing (42 existing + new Stage 3 tests)
- [ ] Case menu shows case14-21 after case13 with correct titles and difficulties
- [ ] `tools` command in case14 returns SIEM correlator output with CRITICAL alert
- [ ] `tools` command in case16 returns hunt analyzer with 60% confidence
- [ ] `tools` command in case19 returns chain of custody reference (ignores challenge_data)
- [ ] `tools` command in case21 returns timeline with 392h 12m gap annotation
