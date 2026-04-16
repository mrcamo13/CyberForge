# spec.md — AEGIS Stage 3: Cases 14-21
<!--
SCOPE: 8 new cases + 7 new dynamic tool functions + 1 static reference. Zero engine changes.
NOT HERE: AEGIS Stage 4+ → future spec
NOT HERE: Any CIPHER changes
-->

**Module:** aegis-stage3
**Date:** 2026-04-12
**Status:** Draft
**Depends on:** aegis-stage2 (full engine, cases 01-13)
**Modifies DATA_MODEL.md:** No
**Modifies CONSTITUTION.md:** No

---

## 1. Purpose & Scope

### What problem does this module solve?
Stages 1 and 2 left Domain 3 (Incident Response, 22% of CySA+ exam) with only one
case (case05). Stage 3 fills Domain 3 comprehensively — memory forensics, disk
forensics, chain of custody, containment strategy, timeline reconstruction — while
also adding higher-difficulty Domain 1 cases for SIEM triage and threat hunting,
which are the most practical daily SOC analyst skills and appear heavily on the exam.

### What does this module do?
Adds 8 cases (case14-21) and 8 new tool functions (7 dynamic + 1 static). All changes
are additive — no existing engine files modified.

### Success Criteria
- [ ] All 8 new cases visible and playable in case menu after case13
- [ ] All 7 new dynamic tool functions return correct output from parsed input
- [ ] At least one deterministic unit test per new dynamic tool function
- [ ] `validate_content.py` passes on all 21 cases (case01-21)
- [ ] `check_imports.py` passes on all files
- [ ] All existing unit tests still pass

### In Scope
- [ ] aegis/content/cases/case14-21.json — eight case content files
- [ ] aegis/utils/tools.py — add 8 tool functions + dispatch entries
- [ ] aegis/validate_content.py — add 8 new tools_type values to allowlist
- [ ] aegis/content/registry.json — add case14-21 entries in order
- [ ] aegis/tests/test_tools_stage3.py — unit tests for all 7 new dynamic tools

### Out of Scope
- ❌ Engine changes (case_runner.py, main.py, save_manager.py — unchanged)
- ❌ AEGIS Stage 4+ → future
- ❌ Any CIPHER changes
- ❌ Domain 2 or Domain 4 additions (covered in Stage 1+2)

---

## 2. Business Rules

All rules from aegis-stage1 spec apply. No new rules.

---

## 3. Data Model

### New tools_type Allowlist Additions (AEGIS Stage 3)

| tools_type | Tool | Used in |
|-----------|------|---------|
| `siem_correlator` | Evaluates events against correlation rules, flags alert matches | case14 |
| `log_classifier` | Maps event descriptions to their primary log source | case15 |
| `hunt_analyzer` | Scores evidence against a threat hunting hypothesis | case16 |
| `mem_analyzer` | Flags suspicious memory artifacts by permissions and path | case17 |
| `disk_analyzer` | Flags suspicious/deleted/timestomped file system entries | case18 |
| `coc_reference` | Static chain of custody reference table (challenge_data ignored) | case19 |
| `containment_advisor` | Scores containment options against scenario parameters | case20 |
| `timeline_builder` | Sorts events chronologically, labels IR phases, flags gaps | case21 |

Updated tools_type allowlist for Stage 3 validate_content.py:
```python
_TOOLS_TYPE_ALLOWLIST = {
    "log_filter", "ioc_classifier", "vuln_scorer", "process_analyzer", "none",
    "traffic_analyzer", "ioc_hunter", "attack_mapper", "rule_analyzer",
    "risk_scorer", "remediation_planner", "exec_reference", "notification_reference",
    "siem_correlator", "log_classifier", "hunt_analyzer", "mem_analyzer",
    "disk_analyzer", "coc_reference", "containment_advisor", "timeline_builder",
}
```

**Routing rule:**
- case19 uses `tools_type: "coc_reference"` — static reference, challenge_data ignored.
- All other Stage 3 cases use dynamic tools that parse challenge_data.

### challenge_data formats by case

| Case | challenge_data format |
|------|-----------------------|
| case14 | `rule1\nrule2\|\|\|event1\nevent2` — rules: `RULE_ID\|CONDITION:field=value\|SEVERITY:level`; events: `timestamp\|source\|event_type\|details` |
| case15 | Newline-separated event description strings (one per line) |
| case16 | `HYPOTHESIS TEXT\|\|\|source:value\nsource:value` |
| case17 | Newline-separated memory entries: `PID:N name:PROC base:0xADDR size:N permissions:rwx path:/path` |
| case18 | Newline-separated file entries: `filename\|size\|created\|modified\|accessed\|deleted:yes/no\|path` |
| case19 | Any string — ignored by coc_reference |
| case20 | `asset:TYPE\|threat:LEVEL\|dwell:DAYS\|data_sensitivity:LEVEL\|attribution:KNOWN/UNKNOWN` |
| case21 | Newline-separated events: `timestamp\|source\|event_description` |

### Tool parsing contracts

**siem_correlator:** Split challenge_data on `|||` → left = rules, right = events.
Rules format (one per line): `RULE_ID|CONDITION:field=value [AND field=value]|SEVERITY:level`
  - Parse condition as one or more `field=value` tokens joined by AND (all must match).
  - Field matching: check if `field=value` appears as a substring in the event's details string.
Events format (one per line): `timestamp|source|event_type|details`
  - For each event, evaluate all rules in order. Collect ALL matching rules (not first-match).
  - Output: list of triggered alerts with rule ID, severity, and the matching event.

**log_classifier:** Split challenge_data on `\n`. For each non-blank line, search the
embedded log source reference table (keyword → source mapping) for the best match.
Matching: check if any keyword from the table appears as a substring in the lowercased
event description. Return the primary log source for the best-matching entry.
If no match: return "Unknown — manual investigation required".

Embedded log source reference table (hardcoded, ~15 entries):
```
failed login / authentication failure / invalid password  → Windows Security Log (Event 4625) / Linux /var/log/auth.log
successful login / accepted password / logon success      → Windows Security Log (Event 4624) / Linux /var/log/auth.log
account created / new user / useradd                      → Windows Security Log (Event 4720) / Linux /var/log/auth.log
privilege escalation / sudo / elevated                    → Linux /var/log/auth.log / Windows Security Log (Event 4672)
process created / new process / cmd.exe / powershell      → Windows Security Log (Event 4688) / Sysmon (Event 1)
network connection / outbound traffic / port scan         → Firewall logs / Windows Security Log (Event 5156)
DNS query / domain lookup / nslookup                      → DNS server logs / Sysmon (Event 22)
file created / file modified / file deleted               → Windows Security Log (Event 4663) / Sysmon (Event 11)
web request / HTTP / GET / POST / nginx / apache          → Web server access logs (nginx/apache access.log)
email sent / email received / smtp / phishing             → Email gateway logs / Exchange logs
USB inserted / removable media / device connected         → Windows Security Log (Event 6416) / udev logs
firewall blocked / connection denied / dropped packet     → Firewall logs / Windows Filtering Platform (Event 5157)
VPN connected / remote access / tunnel established        → VPN gateway logs / RADIUS logs
scheduled task / cron / task created                      → Windows Security Log (Event 4698) / Linux /var/log/syslog
registry modified / reg add / regedit                     → Windows Security Log (Event 4657) / Sysmon (Event 13)
```

**hunt_analyzer:** Split challenge_data on `|||` → left = hypothesis string, right = evidence.
Normalize hypothesis to lowercase. Parse evidence: split on `\n`, each line is `source:value`.
For each evidence item: check if value (lowercased) contains keywords from the embedded
LOLBAS/APT technique reference (hardcoded ~10 entries). Classify each item as:
  - `[SUPPORTS]` if value matches keywords associated with the hypothesis topic
  - `[REFUTES]` if value contradicts the hypothesis (e.g. clean process list)
  - `[NEUTRAL]` if no strong signal either way
Confidence score: (SUPPORTS count) / (total non-NEUTRAL items) × 100, rounded to int.
If total non-NEUTRAL == 0: confidence = 0.

Embedded LOLBAS reference (hardcoded):
```
powershell -enc / -encodedcommand / -nop / -w hidden  → T1059.001 PowerShell execution
certutil -decode / -urlcache                          → T1105 Ingress Tool Transfer
wmic process call create                              → T1047 Windows Management Instrumentation
regsvr32 /s /u /i                                    → T1218.010 Regsvr32 bypass
mshta vbscript / javascript                           → T1218.005 Mshta bypass
bitsadmin /transfer                                   → T1197 BITS Jobs
schtasks /create                                      → T1053.005 Scheduled Task
net use / net share / net localgroup                  → T1021 Remote Services
rundll32 javascript                                   → T1218.011 Rundll32 bypass
cmd /c echo / cmd /c copy                             → T1059.003 Windows Command Shell
living off the land / lolbas / lolbin                → General LOLBAS technique
```

**mem_analyzer:** Split on `\n`, skip blank lines. Parse each entry:
`PID:N name:PROC base:0xADDR size:N permissions:rwx path:/path/or/[anon]`
Fields parsed by prefix matching (e.g. `PID:` → pid value).
Flag logic:
  - `[MALICIOUS]` if name (lowercased) matches: mimikatz, meterpreter, cobalt, beacon,
    cobaltstrike, empire, metasploit
  - `[SUSPICIOUS]` if permissions contain `x` AND (path contains `[anon]` OR
    path starts with `/tmp/` OR path starts with `/dev/shm/`)
  - `[ANOMALY]` if size > 50000 AND name matches a typically small process:
    (svchost, lsass, csrss, smss, wininit, winlogon)
  - `[OK]` otherwise

**disk_analyzer:** Split on `\n`, skip blank lines. Parse each entry as 7 pipe-separated fields:
`filename|size|created|modified|accessed|deleted:yes/no|path`
Flag logic (in priority order — first matching flag wins):
  - `[MALICIOUS]` if filename (lowercased) contains: mimikatz, meterpreter, nc.exe,
    ncat, netcat, pwdump, fgdump, wce.exe, gsecdump
  - `[DELETED]` if deleted field value (lowercased) == "yes"
  - `[TIMESTOMPED]` if modified datetime string < created datetime string
    (string comparison on ISO format: YYYY-MM-DDTHH:MM:SS — earlier string is smaller)
  - `[SUSPICIOUS]` if path contains `/tmp/` OR `/dev/shm/` OR `\Temp\` OR `\AppData\Local\Temp\`
  - `[OK]` otherwise
Sort output by flag priority: MALICIOUS first, then DELETED, then TIMESTOMPED, then SUSPICIOUS, then OK.

**containment_advisor:** Split on `|`, parse each token as `key:value` (case-insensitive keys).
Required keys: asset, threat, dwell, data_sensitivity, attribution.
Accepted values:
  - asset: {server, workstation, laptop, domain_controller, database}
  - threat: {low, medium, high, critical}
  - dwell: integer (days)
  - data_sensitivity: {public, internal, confidential, restricted}
  - attribution: {known, unknown}
Evaluate 4 containment options, score each 1-5 on effectiveness and 1-5 on detection-tip risk:

```
Full isolation (network + account lockout):
  effectiveness: always 5
  tip_risk: 5 if attribution=known AND dwell > 14, else 3
  recommended when: threat=critical OR data_sensitivity=restricted

Network isolation only (block outbound, keep monitoring):
  effectiveness: 4
  tip_risk: 2
  recommended when: threat=high AND dwell <= 14

Monitoring only (observe and collect):
  effectiveness: 2
  tip_risk: 1
  recommended when: dwell <= 7 AND attribution=unknown (still gathering intel)

Account lockout only:
  effectiveness: 3
  tip_risk: 4 if attribution=known, else 2
  recommended when: threat=medium
```

Output: ranked options by (effectiveness - tip_risk) score descending, with rationale.
Top recommendation = highest net score. In a tie: lower tip_risk wins.

**timeline_builder:** Split on `\n`, skip blank lines. Parse each entry as 3 pipe-separated fields:
`timestamp|source|event_description`
Timestamps are ISO format strings (YYYY-MM-DDTHH:MM:SS). Sort entries by timestamp ascending.
Gap detection: if two consecutive events have a time difference > 3600 seconds (1 hour),
insert a gap annotation: `[GAP: Xh Ym — no recorded activity]`.
Phase labeling: assign IR phase to each event based on event_description keywords:
  - Preparation: "policy", "playbook", "training", "alert rule", "monitor"
  - Detection: "alert", "anomaly", "detected", "identified", "flagged", "triggered"
  - Containment: "isolated", "blocked", "disabled", "contained", "quarantine"
  - Eradication: "removed", "deleted", "patched", "cleaned", "reimaged"
  - Recovery: "restored", "verified", "monitoring", "normal operations", "returned"
  - Unknown: no keyword match
Output: sorted timeline with [PHASE] label, source, and description. Gap annotations
inserted between events. Summary section at end listing phase transition timestamps.

**coc_reference:** Fully static — challenge_data ignored entirely.

---

## 4. Technical Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| siem_correlator matching | ALL matching rules fire (not first-match) | SIEM alerts are additive — multiple rules can trigger on one event |
| log_classifier | Keyword substring match against embedded table | Simple, deterministic, educational |
| hunt_analyzer confidence | SUPPORTS / (SUPPORTS + REFUTES) × 100 | Standard threat hunt scoring pattern |
| mem_analyzer ANOMALY | size > 50000 for small system processes | Practical heuristic for injected shellcode detection |
| disk_analyzer sort | Priority order: MALICIOUS > DELETED > TIMESTOMPED > SUSPICIOUS > OK | Most suspicious first for analyst workflow |
| containment_advisor scoring | effectiveness - tip_risk | Balances security outcome against operational intelligence value |
| timeline_builder gap threshold | > 3600 seconds (1 hour) | Meaningful forensic gap, not routine latency |
| timestamp comparison | String comparison on ISO format | Avoids datetime parsing complexity; ISO format sorts correctly |
| coc_reference | Static | Chain of custody is procedural knowledge, not computed |

---

## 5. Content — Cases 14-21

---

### Case 14 — SIEM Alert Triage

**id:** case14
**title:** SIEM Triage
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 1 — Security Operations
**xp_base:** 150
**difficulty:** 3
**tools_type:** siem_correlator

#### challenge_data
```
R001|CONDITION:event_type=auth_failure AND source=external|SEVERITY:high\nR002|CONDITION:event_type=auth_success AND source=external AND details=root|SEVERITY:critical\nR003|CONDITION:event_type=process_create AND details=powershell|SEVERITY:medium\nR004|CONDITION:event_type=network_connect AND details=port=4444|SEVERITY:high|||2026-04-05T22:14:01|firewall|auth_failure|source=external user=admin\n2026-04-05T22:14:03|syslog|auth_failure|source=external user=root\n2026-04-05T22:14:07|syslog|auth_success|source=external user=root details=root\n2026-04-05T22:15:12|sysmon|process_create|details=powershell -enc SQBFAFgA\n2026-04-05T22:16:30|firewall|network_connect|details=dst=185.220.101.45 port=4444\n2026-04-05T22:18:00|syslog|auth_failure|source=internal user=backup
```

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — SIEM PLATFORM
PRIORITY: CRITICAL
ANALYST: YOU

NIGHTWIRE INVESTIGATION — Project MERIDIAN

The SIEM is generating alerts. Your job is to triage the queue
and identify the most severe alert that fired during the
NIGHTWIRE activity window (22:14-22:18 UTC on 2026-04-05).

CORRELATION RULES ACTIVE:
  R001  auth_failure from external source           [HIGH]
  R002  auth_success for root from external source  [CRITICAL]
  R003  process_create with powershell              [MEDIUM]
  R004  network_connect to port 4444                [HIGH]

EVENT LOG (22:14-22:18 UTC):
  22:14:01  firewall  auth_failure     source=external user=admin
  22:14:03  syslog    auth_failure     source=external user=root
  22:14:07  syslog    auth_success     source=external user=root
  22:15:12  sysmon    process_create   powershell -enc SQBFAFgA
  22:16:30  firewall  network_connect  dst=185.220.101.45 port=4444
  22:18:00  syslog    auth_failure     source=internal user=backup

What is the SEVERITY of the highest-priority alert that fired?
```

#### Challenge
`What is the severity level of the highest-priority SIEM alert triggered by events in this log?`

#### Valid Answers
`["critical", "critical severity"]`

#### Hints
```
Hint 1: Go to https://www.elastic.co/guide/en/siem/guide/current/detections-ui-exceptions.html
        Read about SIEM correlation rules and alert severity levels.
        Correlation rules fire when ALL their conditions match a single event.
        Severity levels from lowest to highest: LOW, MEDIUM, HIGH, CRITICAL.

Hint 2: Match each event against the four active rules.
        R001 fires on auth_failure from external — check events 22:14:01 and 22:14:03.
        R002 fires on auth_success for root from external — check event 22:14:07.
        R003 fires on process_create with powershell — check event 22:15:12.
        R004 fires on network_connect to port 4444 — check event 22:16:30.
        Type 'tools' to run the SIEM correlator automatically.

Hint 3: Type 'tools' in the game. The SIEM correlator evaluates each event
        against all rules and lists every alert that fired with its severity.
        Find the alert with the highest severity level.

Hint 4: SPOILER — Event 22:14:07 (auth_success, source=external, user=root)
        matches R002 (CRITICAL). Root login from an external source is the
        most severe event in the log. Type: critical
```

#### Learn Text
```
SIEM (Security Information and Event Management) correlation rules are how
SOC analysts automate detection. A rule defines conditions — when all
conditions match an incoming event, an alert fires.

SIEM alert triage workflow:
  1. Sort alert queue by severity (CRITICAL first)
  2. Correlate related alerts into incidents (same source IP, same user)
  3. Identify true positives vs false positives
  4. Escalate confirmed incidents to incident tickets

Alert severity levels (typical):
  CRITICAL — requires immediate response (active exploitation, critical asset)
  HIGH     — investigate within 1 hour (lateral movement, C2 communication)
  MEDIUM   — investigate within 4 hours (reconnaissance, policy violation)
  LOW      — investigate within 24 hours (informational, single failed login)

False positive reduction:
  Correlation rules reduce false positives by requiring multiple conditions.
  Single-condition rules (any failed login) produce alert fatigue.
  Multi-condition rules (root login from external IP) are more precise.

This scenario uses a rule-based SIEM. Modern SIEMs also use:
  User and Entity Behavior Analytics (UEBA) — baseline + anomaly detection
  Machine learning models — unsupervised pattern detection
  Threat intel enrichment — automatic IOC matching
```

#### Tools Field
`"Evaluates each event against the active correlation rules and reports all alerts that fired with their severity levels."`

#### Tools Output
```
SIEM CORRELATOR — alert correlation engine

Rules loaded: 4
Events to process: 6

Evaluating events...

[ALERT — HIGH] R001 fired on event: 2026-04-05T22:14:01
  Rule: auth_failure from external source
  Event: firewall | auth_failure | source=external user=admin
  Conditions matched: event_type=auth_failure ✓ | source=external ✓

[ALERT — HIGH] R001 fired on event: 2026-04-05T22:14:03
  Rule: auth_failure from external source
  Event: syslog | auth_failure | source=external user=root
  Conditions matched: event_type=auth_failure ✓ | source=external ✓

[ALERT — CRITICAL] R002 fired on event: 2026-04-05T22:14:07
  Rule: auth_success for root from external source
  Event: syslog | auth_success | source=external user=root details=root
  Conditions matched: event_type=auth_success ✓ | source=external ✓ | details=root ✓

[ALERT — MEDIUM] R003 fired on event: 2026-04-05T22:15:12
  Rule: process_create with powershell
  Event: sysmon | process_create | details=powershell -enc SQBFAFgA
  Conditions matched: event_type=process_create ✓ | details=powershell ✓

[ALERT — HIGH] R004 fired on event: 2026-04-05T22:16:30
  Rule: network_connect to port 4444
  Event: firewall | network_connect | details=dst=185.220.101.45 port=4444
  Conditions matched: event_type=network_connect ✓ | details=port=4444 ✓

No alert fired on: 2026-04-05T22:18:00
  source=internal — does not match R001 (requires source=external)

Summary: 5 alerts fired | Highest severity: CRITICAL (R002)
```

#### Debrief
```
summary: The highest-priority alert is CRITICAL — rule R002 fired when root
successfully authenticated from an external IP at 22:14:07. This is the
NIGHTWIRE actor gaining initial foothold via compromised root credentials.
The subsequent alerts (R003 PowerShell, R004 port 4444) confirm execution
and C2 communication followed within minutes.

real_world: SIEM triage is the primary daily workflow for Tier 1 SOC analysts.
In a real SOC, the CRITICAL alert would immediately escalate to a Tier 2
analyst and trigger an incident ticket. The correlated events (same 4-minute
window, escalating severity) form a clear attack narrative.

next_step: Practice with real SIEM tools:
TryHackMe: 'Investigating with ELK 101' room
https://tryhackme.com/room/investigatingwithelk101

cert_link: CySA+ CS0-003 Domain 1 — Security Operations:
"Given a scenario, analyze output from common security tools used for
SIEM monitoring, correlation, and alert triage."

exam_tip: On the exam, SIEM questions test two things: (1) which rule
conditions match which event fields, and (2) which severity is highest.
Remember severity order: CRITICAL > HIGH > MEDIUM > LOW. Also: correlation
rules require ALL conditions to match — a rule with two conditions only fires
when both are present in the same event.
```

---

### Case 15 — Log Source Identification

**id:** case15
**title:** Log Sources
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 1 — Security Operations
**xp_base:** 150
**difficulty:** 3
**tools_type:** log_classifier

#### challenge_data
```
failed login attempt for user administrator\noutbound connection to 185.220.101.45 port 4444\nDNS query for nightwire-c2.xyz\nnew scheduled task created: WindowsUpdate\npowershell.exe spawned by wscript.exe\nUSB device inserted: SanDisk 64GB
```

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — LOG MANAGEMENT TEAM
PRIORITY: MEDIUM
ANALYST: YOU

NIGHTWIRE INVESTIGATION — Project MERIDIAN

The log management team needs to pull raw logs to support the
NIGHTWIRE investigation. They need to know WHICH log source
to query for each event type they're hunting for.

EVENT TYPES TO LOCATE:
  1. Failed login attempt for user administrator
  2. Outbound connection to 185.220.101.45 port 4444
  3. DNS query for nightwire-c2.xyz
  4. New scheduled task created: WindowsUpdate
  5. powershell.exe spawned by wscript.exe
  6. USB device inserted: SanDisk 64GB

For the scheduled task creation event — which log source
would contain this record?
```

#### Challenge
`Which log source records Windows scheduled task creation events?`

#### Valid Answers
`["windows security log", "security log", "event 4698", "windows security log (event 4698)", "sysmon"]`

#### Hints
```
Hint 1: Go to https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/audit-other-object-access-events
        Read about Windows Security Log event IDs for scheduled tasks.
        Windows logs task creation in the Security channel under a specific Event ID.

Hint 2: Windows Security Log records system and security events with Event IDs.
        Scheduled task creation is a persistence technique — it's logged in the
        Security channel. The event ID for 'A scheduled task was created' is 4698.
        Type 'tools' to classify all 6 event types at once.

Hint 3: Type 'tools' in the game. The log classifier maps each event description
        to its primary log source. Find the scheduled task entry in the output.

Hint 4: SPOILER — Scheduled task creation is logged in the Windows Security Log
        under Event ID 4698. Sysmon Event ID 1 (process create) may also capture
        the schtasks.exe execution. Primary source: Windows Security Log (Event 4698).
        Type: windows security log
```

#### Learn Text
```
Knowing which log source records which event is a foundational SOC skill.
Pulling the wrong log wastes investigation time. The CySA+ exam tests this
extensively — for each event type, you must know where to look.

Key log sources and what they record:

Windows Security Log (Security Event Log):
  Event 4624 — Successful logon
  Event 4625 — Failed logon
  Event 4648 — Logon with explicit credentials
  Event 4688 — New process created
  Event 4698 — Scheduled task created
  Event 4720 — User account created
  Event 4663 — File object access
  Event 6416 — New external device recognized (USB)

Sysmon (System Monitor — enhanced endpoint logging):
  Event 1   — Process creation (with command line)
  Event 3   — Network connection
  Event 11  — File created
  Event 13  — Registry modification
  Event 22  — DNS query

Linux log sources:
  /var/log/auth.log    — SSH, sudo, PAM authentication
  /var/log/syslog      — General system events, cron
  /var/log/kern.log    — Kernel messages (USB, hardware)
  Web server logs      — nginx/apache access.log, error.log

Network log sources:
  Firewall logs        — blocked/allowed connections, NAT
  DNS server logs      — all DNS queries by IP
  DHCP logs            — IP assignment records
  Proxy logs           — HTTP/HTTPS traffic with URL detail
```

#### Tools Field
`"Maps each event description to its primary log source using the embedded event type reference table."`

#### Tools Output
```
LOG CLASSIFIER — event source mapping

Classifying 6 event descriptions...

[1] failed login attempt for user administrator
    Primary source: Windows Security Log (Event 4625) / Linux /var/log/auth.log
    Reason: Authentication failure event

[2] outbound connection to 185.220.101.45 port 4444
    Primary source: Firewall logs / Windows Security Log (Event 5156)
    Reason: Network connection event

[3] DNS query for nightwire-c2.xyz
    Primary source: DNS server logs / Sysmon (Event 22)
    Reason: DNS query event

[4] new scheduled task created: WindowsUpdate
    Primary source: Windows Security Log (Event 4698) / Sysmon (Event 1)
    Reason: Scheduled task creation event

[5] powershell.exe spawned by wscript.exe
    Primary source: Windows Security Log (Event 4688) / Sysmon (Event 1)
    Reason: Process creation event

[6] USB device inserted: SanDisk 64GB
    Primary source: Windows Security Log (Event 6416) / udev logs
    Reason: Device connection event

Classification complete. 6/6 events mapped to log sources.
```

#### Debrief
```
summary: Scheduled task creation is recorded in the Windows Security Log
under Event ID 4698. In the NIGHTWIRE investigation, the fake 'WindowsUpdate'
scheduled task was the attacker's persistence mechanism — knowing to check
Event 4698 is what allows analysts to find it quickly.

real_world: Log source knowledge is what separates an analyst who finds
evidence from one who doesn't. In a real investigation, you submit log
pull requests to the SIEM team or log management system — the faster you
identify the right source, the faster the investigation moves.

next_step: Practice with real references:
Windows Event ID reference: https://www.ultimatewindowssecurity.com/securitylog/encyclopedia/

cert_link: CySA+ CS0-003 Domain 1 — Security Operations:
"Given a scenario, identify and use the appropriate log sources and
tools to detect and investigate security events."

exam_tip: Memorize these Event IDs for the exam: 4624 (logon), 4625 (failed logon),
4688 (process create), 4698 (scheduled task), 4720 (account create), 4663 (file access),
6416 (USB). For Linux: auth.log = authentication, syslog = general, kern.log = hardware.
For network: firewall logs = connections, DNS logs = domain queries.
```

---

### Case 16 — Threat Hunting

**id:** case16
**title:** Threat Hunt
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 1 — Security Operations
**xp_base:** 250
**difficulty:** 4
**tools_type:** hunt_analyzer

#### challenge_data
```
NIGHTWIRE is using living-off-the-land techniques to avoid detection|||process:powershell.exe -enc SQBFAFgA\nprocess:certutil.exe -decode payload.b64\nprocess:svchost.exe -k netsvcs\nnetwork:10.0.0.15 to 185.220.101.45:443\nfile:/tmp/update.sh created\nregistry:HKLM\Software\Microsoft\Windows\CurrentVersion\Run modified\nprocess:explorer.exe parent=userinit.exe
```

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — THREAT HUNT TEAM
PRIORITY: HIGH
ANALYST: YOU

NIGHTWIRE INVESTIGATION — Project MERIDIAN

Intelligence suggests NIGHTWIRE uses living-off-the-land (LOLBAS)
techniques — abusing built-in Windows tools to avoid AV detection.

HUNT HYPOTHESIS:
  "NIGHTWIRE is using living-off-the-land techniques to avoid detection"

EVIDENCE COLLECTED FROM HOST 10.0.0.15:
  process  powershell.exe -enc SQBFAFgA
  process  certutil.exe -decode payload.b64
  process  svchost.exe -k netsvcs
  network  10.0.0.15 to 185.220.101.45:443
  file     /tmp/update.sh created
  registry HKLM\...\CurrentVersion\Run modified
  process  explorer.exe parent=userinit.exe

What is the confidence score (as a percentage) that the evidence
SUPPORTS the hypothesis that NIGHTWIRE is using LOLBAS techniques?
```

#### Challenge
`Based on the evidence collected, what is the threat hunt confidence score (as a percentage, 0-100) that NIGHTWIRE is using living-off-the-land techniques?`

#### Valid Answers
`["60", "60%", "60 percent"]`

Note: confidence = SUPPORTS / (SUPPORTS + REFUTES) × 100.
Evidence breakdown: powershell -enc [SUPPORTS], certutil -decode [SUPPORTS],
svchost normal [REFUTES], network to C2 [NEUTRAL], /tmp/update.sh [NEUTRAL],
registry Run [SUPPORTS], explorer.exe normal parent [REFUTES].
SUPPORTS=3, REFUTES=2 → 3/(3+2) × 100 = 60.

#### Hints
```
Hint 1: Go to https://lolbas-project.github.io/
        Read about Living Off the Land Binaries and Scripts (LOLBAS).
        These are legitimate Windows tools (certutil, powershell, mshta, etc.)
        abused by attackers to run malicious code without dropping new files.

Hint 2: For each evidence item, decide if it SUPPORTS, REFUTES, or is NEUTRAL
        for the LOLBAS hypothesis:
        powershell -enc (encoded command)  → SUPPORTS (classic LOLBAS)
        certutil -decode                   → SUPPORTS (file transfer via LOLBAS)
        svchost.exe -k netsvcs             → REFUTES (normal system process)
        network to 185.220.101.45:443      → NEUTRAL (C2 traffic, not LOLBAS-specific)
        /tmp/update.sh                     → NEUTRAL (Linux artifact)
        registry Run modified              → SUPPORTS (persistence via LOLBAS pattern)
        explorer.exe normal parent         → REFUTES (normal process tree)
        Type 'tools' to run the hunt analyzer.

Hint 3: Type 'tools' in the game. The hunt analyzer scores each evidence item
        and calculates: confidence = SUPPORTS / (SUPPORTS + REFUTES) × 100.
        Count the SUPPORTS and REFUTES items, then calculate.

Hint 4: SPOILER — 3 items SUPPORT (powershell -enc, certutil -decode, registry Run),
        2 items REFUTE (svchost normal, explorer normal parent), 2 are NEUTRAL.
        Confidence = 3 / (3 + 2) × 100 = 60%. Type: 60
```

#### Learn Text
```
Threat hunting is proactive — analysts form a hypothesis and look for evidence
to confirm or refute it, rather than waiting for alerts to fire.

Threat hunting methodology:
  1. HYPOTHESIS   — Form a specific, testable statement about attacker behavior
                    Good: "Attacker is using certutil for file transfer"
                    Bad:  "Something suspicious is happening"
  2. DATA SOURCES — Identify which logs/telemetry to examine
  3. HUNT         — Search for evidence using queries, scripts, or tools
  4. CLASSIFY     — For each finding: supports / refutes / neutral
  5. CONFIDENCE   — Score = SUPPORTS / (SUPPORTS + REFUTES) × 100
  6. ESCALATE     — High confidence → escalate to incident response

Living-off-the-Land (LOLBAS) techniques — key indicators:
  powershell -EncodedCommand  — Base64-encoded payload execution
  certutil -decode / -urlcache — File download via built-in CA tool
  wmic process call create    — Remote process creation
  bitsadmin /transfer         — File transfer via BITS service
  regsvr32 /s /u /i http://   — Signed binary proxy execution
  mshta vbscript:             — Script execution via HTML Application host
  schtasks /create            — Persistence via scheduled task
  rundll32 javascript:        — Code execution via DLL loader

LOLBAS detection is in CySA+ Domain 1 — hunting for these patterns in
Sysmon Event 1 (process create with command line) is the primary method.
```

#### Tools Field
`"Evaluates each evidence item against the hunt hypothesis and calculates a confidence score based on supporting vs refuting evidence."`

#### Tools Output
```
HUNT ANALYZER — hypothesis-driven threat hunt

Hypothesis: NIGHTWIRE is using living-off-the-land techniques to avoid detection
Processing 7 evidence items...

[SUPPORTS] process: powershell.exe -enc SQBFAFgA
  Technique: T1059.001 — PowerShell encoded command (-enc/-EncodedCommand)
  This is a classic LOLBAS indicator. Legitimate use is rare.

[SUPPORTS] process: certutil.exe -decode payload.b64
  Technique: T1105 — Ingress Tool Transfer via certutil
  certutil -decode is a known file download/decode LOLBAS technique.

[REFUTES] process: svchost.exe -k netsvcs
  Normal Windows service host process. Expected on all Windows systems.

[NEUTRAL] network: 10.0.0.15 to 185.220.101.45:443
  C2 communication indicator — consistent with compromise but not LOLBAS-specific.

[NEUTRAL] file: /tmp/update.sh created
  Linux artifact — not relevant to Windows LOLBAS hypothesis.

[SUPPORTS] registry: HKLM\...\CurrentVersion\Run modified
  Technique: Persistence via Run key — commonly set by LOLBAS scripts.

[REFUTES] process: explorer.exe parent=userinit.exe
  Normal Windows process tree. Expected parent for explorer.exe.

Results:
  SUPPORTS: 3 | REFUTES: 2 | NEUTRAL: 2
  Confidence score: 3 / (3 + 2) × 100 = 60%

ASSESSMENT: MODERATE CONFIDENCE — hypothesis is supported but not conclusive.
Recommend: collect additional PowerShell script block logging (Event 4104)
and Sysmon command-line data to increase confidence.
```

#### Debrief
```
summary: The hunt returned 60% confidence — three LOLBAS indicators
(encoded PowerShell, certutil decode, Run key persistence) vs two normal
process entries. This is moderate confidence: enough to escalate to an
IR investigation, not enough to definitively attribute to NIGHTWIRE.
The encoded PowerShell command (SQBFAFgA decodes to 'IEX' — Invoke-Expression)
is a particularly strong indicator.

real_world: Threat hunting teams use confidence scores to prioritize
their findings. A 60% score typically triggers a Tier 2 investigation
to collect more specific evidence before escalating to full IR.
Tools like Splunk, Elastic, and Velociraptor are used to run hunts
at scale across thousands of endpoints simultaneously.

next_step: Practice with real tools:
LOLBAS Project: https://lolbas-project.github.io/
TryHackMe: 'Threat Hunting: Introduction' room

cert_link: CySA+ CS0-003 Domain 1 — Security Operations:
"Given a scenario, perform threat hunting activities and apply
threat intelligence to identify and analyze threats."

exam_tip: On the exam, threat hunting questions test the methodology:
hypothesis first, then evidence collection, then confidence scoring.
Key LOLBAS binaries to memorize: certutil, powershell -enc, wmic,
bitsadmin, mshta, regsvr32, rundll32. If you see these with unusual
arguments, they support a LOLBAS hypothesis.
```

---

### Case 17 — Memory Forensics

**id:** case17
**title:** Memory Forensics
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 3 — Incident Response
**xp_base:** 150
**difficulty:** 3
**tools_type:** mem_analyzer

#### challenge_data
```
PID:4 name:System base:0x00000000 size:8192 permissions:r-- path:[kernel]\nPID:892 name:svchost base:0x7FFE0000 size:4096 permissions:r-x path:C:\Windows\System32\svchost.exe\nPID:1337 name:update base:0xFF001000 size:65536 permissions:rwx path:[anon]\nPID:2048 name:explorer base:0x00400000 size:8192 permissions:r-x path:C:\Windows\explorer.exe\nPID:3001 name:powershell base:0x10000000 size:4096 permissions:r-x path:C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe\nPID:3999 name:svchost base:0x00200000 size:102400 permissions:r-x path:C:\Windows\System32\svchost.exe
```

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — DIGITAL FORENSICS TEAM
PRIORITY: HIGH
ANALYST: YOU

NIGHTWIRE INVESTIGATION — Project MERIDIAN

Memory forensics on host 10.0.0.15. A memory dump was acquired
using WinPmem. The forensic team extracted the process memory map.

MEMORY MAP — host 10.0.0.15:
  PID:4     System      base:0x00000000  size:8192    r--   [kernel]
  PID:892   svchost     base:0x7FFE0000  size:4096    r-x   C:\Windows\System32\svchost.exe
  PID:1337  update      base:0xFF001000  size:65536   rwx   [anon]
  PID:2048  explorer    base:0x00400000  size:8192    r-x   C:\Windows\explorer.exe
  PID:3001  powershell  base:0x10000000  size:4096    r-x   C:\Windows\System32\...
  PID:3999  svchost     base:0x00200000  size:102400  r-x   C:\Windows\System32\svchost.exe

One process shows a clear memory injection indicator.
What is the PID of the suspicious process?
```

#### Challenge
`What is the PID of the process showing memory injection indicators (executable anonymous memory region)?`

#### Valid Answers
`["1337", "pid 1337", "pid:1337"]`

#### Hints
```
Hint 1: Go to https://attack.mitre.org/techniques/T1055/
        Read about Process Injection in MITRE ATT&CK.
        Memory injection leaves specific artifacts: executable code in memory
        regions that have no backing file on disk (anonymous regions).

Hint 2: Look at the permissions and path columns together.
        Normal processes: r-x permissions, path points to an executable on disk.
        Injected shellcode: rwx permissions (writable + executable) OR
        r-x permissions but path is [anon] (no disk-backed file).
        Type 'tools' to run the memory analyzer.

Hint 3: Type 'tools' in the game. The memory analyzer flags regions where
        permissions include execute (x) AND path is [anon]. That combination
        indicates code running in memory with no file on disk — a hallmark
        of shellcode injection.

Hint 4: SPOILER — PID 1337 ('update') has rwx permissions and path=[anon].
        Execute permission on an anonymous (non-file-backed) memory region
        is a textbook shellcode injection indicator. Type: 1337
```

#### Learn Text
```
Memory forensics reveals what was running in a system at the time of
compromise — including malware that never touched disk. This is critical
for detecting fileless malware and process injection attacks.

Key memory forensics indicators:

Anonymous executable regions ([anon] with r-x or rwx):
  Normal processes have memory backed by files on disk.
  Injected shellcode lives in anonymous memory — no corresponding file.
  This is how fileless malware and Cobalt Strike beacons hide.

RWX permissions (read + write + execute):
  Memory that is simultaneously writable and executable is suspicious.
  Legitimate code: loaded read-only or read-execute. Not writable.
  Malware: writes shellcode then executes it in the same region.

Process hollowing indicators:
  Legitimate process path but unusual base address or size.
  svchost.exe with very large size or unusual memory layout.

Common memory forensics tools:
  Volatility     — Python framework, plugin-based, supports Windows/Linux/macOS
  Rekall         — Volatility fork, cloud forensics focus
  WinPmem        — Windows memory acquisition tool
  LiME           — Linux memory acquisition kernel module

Volatility plugins for this scenario:
  vol.py -f memory.dmp windows.malfind     — finds injected code regions
  vol.py -f memory.dmp windows.pslist      — process list
  vol.py -f memory.dmp windows.cmdline     — process command lines
```

#### Tools Field
`"Analyzes a memory map for injection indicators: anonymous executable regions, RWX permissions, anomalous process sizes, and known malicious process names."`

#### Tools Output
```
MEM ANALYZER — memory forensics

Scanning 6 memory entries...

PID:4     System      r--   [kernel]               [OK] Kernel process, expected
PID:892   svchost     r-x   ...svchost.exe          [OK] Normal service host
PID:1337  update      rwx   [anon]                  [SUSPICIOUS] Execute permission on
                                                    anonymous region — shellcode indicator
PID:2048  explorer    r-x   ...explorer.exe         [OK] Normal explorer process
PID:3001  powershell  r-x   ...powershell.exe       [OK] Legitimate path
PID:3999  svchost     r-x   ...svchost.exe          [ANOMALY] size=102400 unusually
                                                    large for svchost — possible injection

FINDINGS:
  [SUSPICIOUS] PID 1337 — 'update': rwx permissions on anonymous region
    Base: 0xFF001000 | Size: 65536 bytes
    Anonymous memory + executable = fileless malware / shellcode injection
    Recommend: extract and analyze memory region with Volatility malfind

  [ANOMALY] PID 3999 — 'svchost': unusually large memory size (102400 bytes)
    Normal svchost range: ~4000-20000 bytes
    Possible process hollowing or large shellcode payload
    Recommend: compare against known-good svchost baseline
```

#### Debrief
```
summary: PID 1337 ('update') shows the clearest injection indicator:
rwx permissions on an anonymous (non-file-backed) memory region.
This is textbook shellcode injection — the NIGHTWIRE implant is running
entirely in memory with no file on disk, which is why endpoint AV missed it.
PID 3999 (svchost, 102400 bytes) is also anomalous and warrants investigation.

real_world: Memory forensics is essential for detecting fileless malware,
which now accounts for a significant portion of APT intrusions. Tools like
Volatility's 'malfind' plugin automate the detection of anonymous executable
regions. Memory acquisition must happen before the system is powered off —
RAM is volatile evidence.

next_step: Practice with real tools:
TryHackMe: 'Volatility' room — https://tryhackme.com/room/volatility

cert_link: CySA+ CS0-003 Domain 3 — Incident Response:
"Given a scenario, perform incident response activities including the
collection and analysis of digital forensic evidence."

exam_tip: On the exam, memory forensics questions focus on: (1) what tools
acquire memory (WinPmem, LiME), (2) what Volatility plugins find malware
(malfind for injection, pslist for processes, cmdline for commands), and
(3) what constitutes a memory injection indicator (anonymous executable
regions, RWX permissions). Fileless malware lives in memory — disk forensics
won't find it.
```

---

### Case 18 — Disk Forensics

**id:** case18
**title:** Disk Forensics
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 3 — Incident Response
**xp_base:** 250
**difficulty:** 4
**tools_type:** disk_analyzer

#### challenge_data
```
nightwire.exe|45056|2026-03-20T14:00:00|2026-03-20T14:00:00|2026-04-05T22:15:00|deleted:yes|C:\Users\Public\nightwire.exe\nupdate.bat|512|2026-04-05T22:14:30|2026-04-05T22:14:30|2026-04-05T22:14:30|deleted:no|C:\Windows\Temp\update.bat\nsvchost.exe|28672|2026-03-15T09:00:00|2026-03-15T09:00:00|2026-04-05T22:16:00|deleted:no|C:\Windows\System32\svchost.exe\nmimikatz.exe|1245184|2026-04-05T22:20:00|2026-03-01T00:00:00|2026-04-05T22:20:00|deleted:yes|C:\Users\Public\Downloads\mimikatz.exe\nconfig.sys|128|2021-01-01T00:00:00|2021-01-01T00:00:00|2026-04-05T22:10:00|deleted:no|C:\Windows\System32\config.sys\npayload.b64|8192|2026-04-05T22:14:00|2026-04-05T22:14:00|2026-04-05T22:14:00|deleted:yes|C:\Temp\payload.b64
```

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — DIGITAL FORENSICS TEAM
PRIORITY: HIGH
ANALYST: YOU

NIGHTWIRE INVESTIGATION — Project MERIDIAN

Disk forensics on host 10.0.0.15. File system artifacts collected
using an FTK Imager image of the system drive.

FILE SYSTEM ARTIFACTS:
  nightwire.exe    45056B  created:2026-03-20  modified:2026-03-20  DELETED
                   path: C:\Users\Public\
  update.bat       512B    created:2026-04-05  modified:2026-04-05  exists
                   path: C:\Windows\Temp\
  svchost.exe      28672B  created:2026-03-15  modified:2026-03-15  exists
                   path: C:\Windows\System32\
  mimikatz.exe     1245184B created:2026-04-05 modified:2026-03-01  DELETED
                   path: C:\Users\Public\Downloads\
  config.sys       128B    created:2021-01-01  modified:2021-01-01  exists
                   path: C:\Windows\System32\
  payload.b64      8192B   created:2026-04-05  modified:2026-04-05  DELETED
                   path: C:\Temp\

One file shows evidence of timestomping (modified before created).
What is the NAME of that file?
```

#### Challenge
`Which filename shows evidence of timestomping (modified timestamp earlier than created timestamp)?`

#### Valid Answers
`["mimikatz.exe", "mimikatz"]`

#### Hints
```
Hint 1: Go to https://attack.mitre.org/techniques/T1070/006/
        Read about Timestomping in MITRE ATT&CK (T1070.006).
        Timestomping is when an attacker modifies file timestamps to make
        malicious files look older or to hide when they were created.

Hint 2: Compare the 'created' and 'modified' timestamps for each file.
        Under normal circumstances, a file's modified date cannot be earlier
        than its created date (you can't modify something before it exists).
        If modified < created: the timestamps were altered.
        Type 'tools' to run the disk analyzer.

Hint 3: Type 'tools' in the game. The disk analyzer flags files where the
        modified timestamp string is earlier than the created timestamp string.
        ISO format (YYYY-MM-DDTHH:MM:SS) sorts correctly as strings.

Hint 4: SPOILER — mimikatz.exe has created=2026-04-05 but modified=2026-03-01.
        Modified (March 1) is BEFORE created (April 5) — impossible normally.
        The attacker used a timestomping tool to make mimikatz look like an
        older, legitimate file. Type: mimikatz.exe
```

#### Learn Text
```
Disk forensics reconstructs attacker activity from file system artifacts.
Even deleted files leave traces — forensic tools can recover them from
unallocated disk space.

Key disk forensics indicators:

Timestomping (T1070.006):
  Attackers modify file timestamps to blend in with legitimate files.
  Detection: modified timestamp earlier than created timestamp.
  Tools: Autopsy, FTK, Sleuth Kit (istat command).

Deleted files:
  Deletion removes directory entries but not file content (until overwritten).
  Recovery: carving from unallocated space, $MFT analysis (Windows NTFS).
  Key insight: deleted files often contain the most incriminating evidence.

Suspicious file locations:
  C:\Users\Public\          — world-readable, no user context
  C:\Windows\Temp\          — temporary files, often abused
  C:\Temp\                  — non-standard temp, suspicious
  AppData\Local\Temp\       — user temp, common malware location

NTFS forensic artifacts:
  $MFT (Master File Table) — every file and directory metadata
  $LogFile               — file system transaction log (last ~days)
  $UsnJrnl               — change journal (file create/delete/modify history)
  $RECYCLE.BIN           — recycled files with original path and time

Common disk forensics tools:
  Autopsy        — open source forensic suite, GUI
  FTK Imager     — disk imaging and preview
  Sleuth Kit     — command line, underpins Autopsy
  Plaso/Log2timeline — timeline generation from forensic artifacts
```

#### Tools Field
`"Analyzes file system entries for malicious filenames, deleted files, timestomping, and suspicious paths."`

#### Tools Output
```
DISK ANALYZER — file system forensics

Analyzing 6 file entries...

[MALICIOUS] mimikatz.exe — known credential dumping tool
  Size: 1245184B | Path: C:\Users\Public\Downloads\
  Status: DELETED (recovery possible from unallocated space)
  TIMESTOMPED: modified=2026-03-01 < created=2026-04-05 (impossible — timestamp manipulated)

[DELETED] nightwire.exe
  Size: 45056B | Path: C:\Users\Public\
  Created: 2026-03-20 | Timestamps consistent (no timestomping)
  Recommend: recover from $MFT or unallocated space

[DELETED] payload.b64
  Size: 8192B | Path: C:\Temp\
  Created/modified: 2026-04-05 | Suspicious path
  Likely certutil decode output — recover and analyze

[SUSPICIOUS] update.bat
  Path: C:\Windows\Temp\ — non-standard location for batch file
  Created: 2026-04-05T22:14:30 — during attack window

[OK] svchost.exe
  Path: C:\Windows\System32\ — legitimate system file

[OK] config.sys
  Path: C:\Windows\System32\ — legitimate system file

Summary: 1 MALICIOUS | 2 DELETED | 1 SUSPICIOUS | 2 OK
Priority finding: mimikatz.exe — MALICIOUS + DELETED + TIMESTOMPED
```

#### Debrief
```
summary: mimikatz.exe is the priority finding — it is simultaneously
[MALICIOUS] (known credential dumper), [DELETED] (attacker attempted cleanup),
and [TIMESTOMPED] (modified before created, impossible normally). The attacker
used timestomping to make mimikatz look older than it was, then deleted it.
Both the artifact recovery and the timestomping detection are essential IR skills.

real_world: In real investigations, the presence of mimikatz (even deleted
and timestomped) means the attacker likely has all password hashes from the
system — every account on that host must be treated as compromised. The
NTFS $MFT and $UsnJrnl often retain evidence even after deletion.

next_step: Practice with real tools:
TryHackMe: 'Autopsy' room — https://tryhackme.com/room/btautopsye0

cert_link: CySA+ CS0-003 Domain 3 — Incident Response:
"Given a scenario, perform incident response activities including
forensic data collection, preservation, and analysis."

exam_tip: On the exam, disk forensics questions test: (1) timestomping
detection (modified < created = impossible = manipulation), (2) suspicious
file locations (Temp, Public, AppData), (3) NTFS artifacts ($MFT, $UsnJrnl),
and (4) forensic tools (Autopsy, FTK, Sleuth Kit). Know that deleted files
are recoverable until the disk space is overwritten.
```

---

### Case 19 — Chain of Custody

**id:** case19
**title:** Chain of Custody
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 3 — Incident Response
**xp_base:** 150
**difficulty:** 3
**tools_type:** coc_reference

#### challenge_data
`"The NIGHTWIRE investigation has identified forensic artifacts on host 10.0.0.15. Evidence includes a memory dump (memory.dmp, 8GB), disk image (disk.img, 512GB), and USB drive found in the server room. Legal has been notified. What must be documented FIRST when taking physical custody of the USB drive?"`

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — LEGAL AND COMPLIANCE
PRIORITY: HIGH
ANALYST: YOU

NIGHTWIRE INVESTIGATION — Project MERIDIAN

The NIGHTWIRE investigation has escalated to potential legal
proceedings. Evidence collected so far:
  - Memory dump: memory.dmp (8GB) from host 10.0.0.15
  - Disk image: disk.img (512GB) from host 10.0.0.15
  - Physical USB drive: found in server room, no label

Legal has requested all evidence be handled with full chain of
custody documentation before any further analysis.

A colleague is about to start analyzing the USB drive directly.
You need to stop them — what must happen FIRST before the USB
is touched for analysis?

What must be documented FIRST when taking physical custody
of the USB drive evidence?
```

#### Challenge
`What must be documented first when establishing chain of custody for physical evidence like a USB drive?`

#### Valid Answers
`["hash", "hash value", "cryptographic hash", "sha256", "md5", "integrity hash", "evidence hash", "checksum"]`

#### Hints
```
Hint 1: Go to https://www.sans.org/white-papers/451/
        Read about digital forensics evidence handling. The first action
        when taking custody of physical digital evidence is to establish
        its integrity so you can prove it was not altered later.

Hint 2: Before touching any digital evidence for analysis, you must create
        a cryptographic record of its original state. This record allows you
        to prove in court that the evidence was not altered during investigation.
        Type 'tools' to see the full chain of custody procedure reference.

Hint 3: Type 'tools' in the game. The chain of custody reference lists the
        exact order of steps for physical evidence handling. The very first
        step creates a verifiable fingerprint of the evidence.

Hint 4: SPOILER — The first step is always to document the cryptographic hash
        (SHA-256 or MD5) of the evidence BEFORE any analysis. This hash is the
        integrity baseline — any change to the evidence would produce a different
        hash, proving tampering. Type: hash
```

#### Learn Text
```
Chain of custody is the documented, unbroken sequence of possession for
evidence. In legal proceedings, broken chain of custody can make evidence
inadmissible — the entire investigation can be thrown out.

Chain of custody for digital evidence:

COLLECTION:
  1. Document the scene (photographs, notes, location, time)
  2. Hash the evidence BEFORE collection (SHA-256 preferred)
  3. Use write blockers when imaging drives (prevents modification)
  4. Create forensic copies — never analyze originals
  5. Hash the copy and verify it matches the original hash

DOCUMENTATION (required for each transfer):
  - Description of evidence (type, serial number, size)
  - Date and time of collection/transfer
  - Person collecting/receiving (full name, role, signature)
  - Location (where collected, where stored)
  - Reason for transfer
  - Hash values (before and after)

STORAGE:
  - Physical: evidence bags, tamper-evident seals, secure room
  - Digital: write-protected storage, access logging, off-site backup

COMMON CHAIN OF CUSTODY ERRORS:
  - Analyzing originals instead of forensic copies
  - Forgetting to use a write blocker during imaging
  - Missing documentation on a transfer
  - Not re-hashing after storage to verify integrity
  - Allowing unauthorized personnel to access evidence

If chain of custody is broken:
  Evidence may be deemed inadmissible in court.
  Investigation credibility is damaged.
  Attacker prosecution may fail.
```

#### Tools Field
`"Displays the chain of custody reference including collection steps, documentation requirements, storage procedures, and common errors."`

#### Tools Output
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

#### Debrief
```
summary: The first step is always to hash the evidence. The cryptographic
hash (SHA-256 or MD5) is the integrity baseline that proves the evidence
was not altered during investigation. Without an original hash, you cannot
defend the evidence in court. Everything else — write blockers, forensic
copies, storage — comes after establishing that baseline hash.

real_world: In real forensic investigations, analysts use tools like FTK
Imager or sha256sum to hash evidence immediately at the scene, before any
analysis. The hash is recorded on the evidence log and signed by witnesses.
Many organizations use automated evidence management systems that compute
and record hashes automatically on intake.

next_step: Practice with real procedures:
SANS Digital Forensics Poster: https://www.sans.org/posters/windows-forensics/

cert_link: CySA+ CS0-003 Domain 3 — Incident Response:
"Given a scenario, explain the importance of chain of custody and legal
considerations in digital forensics and incident response."

exam_tip: On the exam, chain of custody questions focus on: (1) hashing
first (before analysis), (2) write blockers (before imaging), (3) forensic
copies (never analyze originals), and (4) what breaks the chain (unauthorized
access, undocumented transfers, missing hashes). The correct sequence is:
document → hash → write block → image → verify → analyze copy.
```

---

### Case 20 — Containment Strategy

**id:** case20
**title:** Containment
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 3 — Incident Response
**xp_base:** 250
**difficulty:** 4
**tools_type:** containment_advisor

#### challenge_data
`"asset:domain_controller|threat:critical|dwell:42|data_sensitivity:restricted|attribution:known"`

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — INCIDENT RESPONSE TEAM
PRIORITY: CRITICAL
ANALYST: YOU

NIGHTWIRE INVESTIGATION — Project MERIDIAN

The NIGHTWIRE APT has been active on the Veridian domain controller
for 42 days. Attribution is confirmed — a nation-state actor.

ASSET DETAILS:
  Asset type:       Domain controller (DC-01)
  Threat level:     CRITICAL (confirmed APT, nation-state)
  Dwell time:       42 days
  Data sensitivity: RESTRICTED (AD credentials, group policies)
  Attribution:      KNOWN (nation-state actor, confirmed TTPs)

The IR team needs a containment recommendation. The challenge:
if the attacker knows they've been detected (tipped off), they
may destroy evidence, exfiltrate remaining data, or activate
destructive payloads before we can contain them.

What containment strategy should be applied first?
```

#### Challenge
`Given a known APT on a domain controller with 42-day dwell time and restricted data sensitivity, what is the recommended first containment action?`

#### Valid Answers
`["network isolation", "network isolation only", "isolate network", "block outbound", "network segment"]`

Note: containment_advisor scoring for this scenario:
  - asset=domain_controller, threat=critical, dwell=42, data_sensitivity=restricted, attribution=known
  - Full isolation: effectiveness=5, tip_risk=5 (known + dwell>14). Net = 0.
  - Network isolation: effectiveness=4, tip_risk=2. Net = 2. ← highest net score
  - Monitoring only: effectiveness=2, tip_risk=1. Net = 1.
  - Account lockout: effectiveness=3, tip_risk=4 (attribution=known). Net = -1.
  Network isolation wins (net score 2).

#### Hints
```
Hint 1: Go to https://www.cisa.gov/sites/default/files/publications/Incident-Response-Plan-Basics_508c.pdf
        Read about containment strategies in incident response.
        The key tension: contain the threat vs. tip off the attacker.
        Nation-state actors may destroy evidence if they know they're burned.

Hint 2: Consider the scenario parameters:
        - Threat is CRITICAL — must act
        - Dwell is 42 days (known actor, 42 > 14) — full isolation is risky
        - Attribution is KNOWN — attacker may react if they notice isolation
        - Data sensitivity is RESTRICTED — cannot let them keep accessing it
        Full isolation stops them completely but they'll know instantly.
        Network isolation blocks outbound C2 while allowing monitoring.
        Type 'tools' to run the containment advisor.

Hint 3: Type 'tools' in the game. The containment advisor scores each option
        by effectiveness minus detection-tip risk. The option with the best
        net score is the recommendation.

Hint 4: SPOILER — Network isolation (block outbound C2, keep monitoring)
        has the best net score for this scenario. It stops the attacker's
        active C2 channel while limiting the tip-off risk compared to
        full isolation. Full isolation would trigger immediate attacker
        response given the 42-day dwell and known attribution.
        Type: network isolation
```

#### Learn Text
```
Containment strategy is one of the hardest decisions in incident response.
The goal is to stop the threat while preserving evidence and avoiding
triggering attacker countermeasures.

Containment options:

FULL ISOLATION (network + account lockout):
  Stops all attacker access immediately.
  High tip-off risk — attacker knows immediately.
  Risk: attacker may trigger destructive payload or evidence wipe.
  Best for: ransomware (already noisy), low dwell time, unknown actor.

NETWORK ISOLATION (block external C2, keep internal monitoring):
  Cuts attacker's command channel while maintaining visibility.
  Lower tip-off risk — attacker may think it's a network issue.
  Allows continued monitoring to gather forensic evidence.
  Best for: long dwell APT, known actor, intelligence gathering phase.

MONITORING ONLY (observe without intervening):
  Maximum intelligence collection. Zero tip-off risk.
  Low effectiveness — attacker continues operating.
  Best for: very early in investigation, unknown actor, < 7 day dwell.

ACCOUNT LOCKOUT ONLY:
  Removes attacker's credential access.
  High tip-off risk if attacker has established monitoring of their accounts.
  Moderate effectiveness — attacker may have other persistence mechanisms.

Decision factors:
  Dwell time     — longer dwell = more persistence = higher containment urgency
  Attribution    — known actor = higher tip-off risk
  Asset type     — domain controller = high priority but high risk if tipped
  Data sensitivity — RESTRICTED = cannot allow continued access
  Legal requirements — law enforcement may want continued monitoring

The NIST SP 800-61 principle: containment must balance "stopping the bleeding"
against the intelligence value of continued observation.
```

#### Tools Field
`"Scores containment options (full isolation, network isolation, monitoring, account lockout) against scenario parameters and recommends the best strategy."`

#### Tools Output
```
CONTAINMENT ADVISOR — strategy recommendation

Input parameters:
  Asset:            domain_controller
  Threat level:     critical
  Dwell time:       42 days
  Data sensitivity: restricted
  Attribution:      known

Scoring containment options (effectiveness - tip_risk = net score)...

OPTION 1: Full Isolation (network + account lockout)
  Effectiveness:  5/5 — stops all attacker access
  Tip-off risk:   5/5 — attribution=known + dwell=42 days (>14) = high reaction risk
  Net score:      0
  Risk: Nation-state actor with 42-day dwell likely has backup persistence
        and may trigger destructive payload upon detecting isolation.

OPTION 2: Network Isolation (block outbound C2, maintain internal monitoring)
  Effectiveness:  4/5 — cuts C2 channel, maintains visibility
  Tip-off risk:   2/5 — appears as network issue, not obvious detection
  Net score:      2   ← RECOMMENDED
  Rationale: Best balance for known APT with long dwell. Stops active
             exfiltration while preserving forensic collection opportunity.

OPTION 3: Monitoring Only
  Effectiveness:  2/5 — attacker continues operating
  Tip-off risk:   1/5 — no tip-off
  Net score:      1
  Risk: data_sensitivity=restricted — cannot allow continued access to AD.

OPTION 4: Account Lockout Only
  Effectiveness:  3/5 — removes credential access
  Tip-off risk:   4/5 — attribution=known, attacker monitors their accounts
  Net score:      -1
  Risk: Attacker likely has service account or certificate-based persistence
        beyond standard credentials after 42-day dwell.

RECOMMENDATION: Network Isolation
  Block all outbound connections from DC-01.
  Maintain internal monitoring and log collection.
  Brief legal and executive team before executing.
  Prepare full isolation as immediate follow-on action.
```

#### Debrief
```
summary: Network isolation is the recommended first action — it has the
best net score (effectiveness 4 minus tip-risk 2 = 2) for this scenario.
Full isolation would be ideal but the 42-day dwell with known attribution
makes it too likely the attacker would trigger countermeasures. Cutting
the C2 channel while maintaining monitoring balances stopping the breach
against preserving forensic evidence and intelligence value.

real_world: APT containment decisions are made by senior IR leads, often
with legal, executive, and sometimes law enforcement input. The decision
to contain vs. observe is documented in the IR plan and requires sign-off.
The intelligence community sometimes asks organizations to maintain
monitoring on APT actors to gather attribution evidence.

next_step: Practice with real frameworks:
CISA IR Guide: https://www.cisa.gov/sites/default/files/publications/Incident-Response-Plan-Basics_508c.pdf

cert_link: CySA+ CS0-003 Domain 3 — Incident Response:
"Given a scenario, select and implement the appropriate containment,
eradication, and recovery strategy for an incident."

exam_tip: On the exam, containment questions test the trade-off between
effectiveness and evidence preservation. Key rules: ransomware → full
isolation immediately (already noisy). APT with long dwell → network
isolation first (preserve intelligence). Unknown actor → monitoring first.
Also know: NIST IR phases are Preparation → Detection → Containment →
Eradication → Recovery → Post-Incident.
```

---

### Case 21 — Incident Timeline

**id:** case21
**title:** Timeline
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 3 — Incident Response
**xp_base:** 250
**difficulty:** 4
**tools_type:** timeline_builder

#### challenge_data
```
2026-03-20T14:00:00|disk|nightwire.exe dropped to C:\Users\Public\n2026-03-20T14:02:00|registry|HKLM\...\Run key modified — persistence established\n2026-04-05T22:14:07|syslog|auth_success — external root login\n2026-04-05T22:15:12|sysmon|powershell -enc SQBFAFgA executed\n2026-04-05T22:16:30|firewall|outbound connection to 185.220.101.45:4444\n2026-04-05T22:20:00|disk|mimikatz.exe executed then deleted\n2026-04-11T03:15:00|syslog|NexusCorp attacker detected — separate incident triggered IR\n2026-04-11T03:20:00|ir_team|NIGHTWIRE artifacts identified during NexusCorp investigation\n2026-04-11T03:45:00|ir_team|DC-01 network isolated — NIGHTWIRE C2 channel blocked\n2026-04-11T04:30:00|ir_team|forensic imaging of DC-01 initiated\n2026-04-12T09:00:00|ir_team|NIGHTWIRE investigation formally opened — Project MERIDIAN
```

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — INCIDENT RESPONSE TEAM
PRIORITY: HIGH
ANALYST: YOU

NIGHTWIRE INVESTIGATION — Project MERIDIAN

The final task: reconstruct the complete NIGHTWIRE incident timeline
from multi-source evidence. Events have been gathered from disk
forensics, registry analysis, syslog, sysmon, firewall logs, and
IR team notes.

RAW EVENTS (unsorted):
  disk      nightwire.exe dropped                    2026-03-20T14:00
  registry  Run key persistence established          2026-03-20T14:02
  syslog    external root login success              2026-04-05T22:14
  sysmon    powershell -enc executed                 2026-04-05T22:15
  firewall  C2 beacon to 185.220.101.45:4444         2026-04-05T22:16
  disk      mimikatz executed and deleted            2026-04-05T22:20
  syslog    NexusCorp attacker triggers IR           2026-04-11T03:15
  ir_team   NIGHTWIRE artifacts found                2026-04-11T03:20
  ir_team   DC-01 network isolated                   2026-04-11T03:45
  ir_team   forensic imaging initiated               2026-04-11T04:30
  ir_team   Project MERIDIAN formally opened         2026-04-12T09:00

How many hours elapsed between NIGHTWIRE's initial persistence
(Run key modification) and their first confirmed active operation
(external root login)?
```

#### Challenge
`How many hours elapsed between NIGHTWIRE establishing persistence (2026-03-20T14:02) and their first confirmed active operation (2026-04-05T22:14)?`

#### Valid Answers
`["392", "392 hours", "approximately 392 hours", "about 392 hours"]`

Note: from 2026-03-20T14:02 to 2026-04-05T22:14 =
16 days × 24h + (22:14 - 14:02) = 384h + 8h 12m ≈ 392 hours.
Exact: March 20 14:02 to April 5 22:14.
March 20 to April 5 = 16 days = 384 hours.
14:02 to 22:14 = 8 hours 12 minutes = 8.2 hours.
Total = 392.2 hours → round to 392.

#### Hints
```
Hint 1: Go to https://www.crowdstrike.com/cybersecurity-101/threat-intelligence/threat-actor-dwell-time/
        Read about APT dwell time — the gap between initial access and
        active operations. Nation-state APTs often wait weeks or months
        before becoming active to avoid detection.

Hint 2: Find the two key timestamps in the timeline:
        Initial persistence: 2026-03-20T14:02 (Run key modified)
        First active operation: 2026-04-05T22:14 (external root login)
        Calculate the difference in hours between these two timestamps.
        March 20 to April 5 = 16 days = 384 hours. Add the time difference.
        Type 'tools' to see the full sorted timeline with gap analysis.

Hint 3: Type 'tools' in the game. The timeline builder sorts all events,
        labels IR phases, and annotates gaps. Find the gap annotation
        between the persistence phase and the active operations phase.

Hint 4: SPOILER — From 2026-03-20T14:02 to 2026-04-05T22:14:
        16 days × 24h = 384 hours, plus 22:14 minus 14:02 = 8h 12m ≈ 8 hours.
        Total: approximately 392 hours (16.3 days of dormancy).
        This is classic APT behavior — establish persistence, go quiet,
        activate weeks later when defenders have stopped looking.
        Type: 392
```

#### Learn Text
```
Incident timeline reconstruction is how IR teams understand the full scope
of a breach — from first foothold to containment. Timelines are built from
multi-source evidence and presented in final IR reports.

Timeline reconstruction process:
  1. Collect timestamps from all available sources
     (logs, file system metadata, memory artifacts, EDR telemetry)
  2. Normalize timestamps to UTC (different sources may use local time)
  3. Sort chronologically
  4. Identify gaps — periods with no recorded activity
  5. Map events to IR phases (Preparation, Detection, Containment, etc.)
  6. Identify the initial access event (earliest attacker activity)

Key timeline concepts:

Dwell time:
  Time between initial compromise and detection.
  NIGHTWIRE dwell: ~22 days (March 20 to April 11).
  Industry average APT dwell: ~21 days (2023, CrowdStrike data).

Initial access vs. first active operation:
  Attackers often establish persistence, then go dormant.
  Dormancy avoids detection by blending into normal baselines.
  Activation comes later when defenders have relaxed.

Timeline gaps:
  Gaps > 1 hour in forensic evidence may indicate:
  - Log rotation or deletion (attacker covering tracks)
  - Attacker dormancy (waiting for opportunity)
  - Evidence collection gap (log source not captured)

IR phase timeline:
  Detection phase start: when the first alert fired or anomaly was noticed.
  Containment phase start: when the first containment action was taken.
  Eradication phase start: when attacker tools were removed.
  Recovery phase start: when normal operations resumed.

The timeline is the backbone of the final IR report and is used to calculate
metrics like Mean Time to Detect (MTTD) and Mean Time to Respond (MTTR).
```

#### Tools Field
`"Sorts timeline events chronologically, identifies gaps over 1 hour, labels each event with the appropriate IR phase, and summarizes phase transitions."`

#### Tools Output
```
TIMELINE BUILDER — incident reconstruction

Sorting 11 events from 4 sources...

[Unknown]      2026-03-20T14:00:00  disk      nightwire.exe dropped to C:\Users\Public
[Unknown]      2026-03-20T14:02:00  registry  HKLM\...\Run key modified — persistence established

[GAP: 392h 12m — no recorded activity]

[Unknown]      2026-04-05T22:14:07  syslog    auth_success — external root login
[Unknown]      2026-04-05T22:15:12  sysmon    powershell -enc SQBFAFgA executed
[Unknown]      2026-04-05T22:16:30  firewall  outbound connection to 185.220.101.45:4444
[Eradication]  2026-04-05T22:20:00  disk      mimikatz.exe executed then deleted

[GAP: 124h 55m — no recorded activity]

[Detection]    2026-04-11T03:15:00  syslog    NexusCorp attacker detected — separate incident
[Detection]    2026-04-11T03:20:00  ir_team   NIGHTWIRE artifacts identified
[Containment]  2026-04-11T03:45:00  ir_team   DC-01 network isolated — NIGHTWIRE C2 blocked
[Unknown]      2026-04-11T04:30:00  ir_team   forensic imaging of DC-01 initiated
[Unknown]      2026-04-12T09:00:00  ir_team   NIGHTWIRE investigation formally opened

Phase summary:
  Detection phase started:    2026-04-11T03:15:00
  Containment phase started:  2026-04-11T03:45:00
  Total dwell time:           ~518 hours (21.6 days)
  Largest gap:                392h 12m (attacker dormancy period)
```

#### Debrief
```
summary: NIGHTWIRE established persistence on March 20, then went dormant
for approximately 392 hours (16 days) before activating on April 5.
This dormancy is classic APT technique — wait until the defender's attention
has moved elsewhere, then activate. The full dwell time (initial access to
containment) was 21.5 days. The NexusCorp incident on April 11 accidentally
led to NIGHTWIRE's discovery — without it, NIGHTWIRE might have remained
undetected indefinitely.

real_world: Timeline reconstruction is submitted as part of the formal IR
report and may be used in legal proceedings, regulatory notifications, and
after-action reviews. Tools like Plaso (log2timeline) automate timeline
construction from forensic artifacts. Analysts normalize all timestamps to
UTC to avoid errors from timezone-mismatched log sources.

next_step: Practice with real tools:
TryHackMe: 'Investigating Windows' room
https://tryhackme.com/room/investigatingwindows

cert_link: CySA+ CS0-003 Domain 3 — Incident Response:
"Given a scenario, perform post-incident activities including developing
a timeline, after-action report, and lessons learned documentation."

exam_tip: On the exam, timeline questions test: (1) dwell time calculation
(initial access to detection), (2) IR phase identification (which event
starts containment vs. eradication), and (3) MTTD/MTTR metrics. Key formula:
MTTD = time from initial compromise to detection. MTTR = time from detection
to containment/resolution. Shorter MTTD and MTTR = better security posture.
```

---

## 6. Pre-Flight Checklist

- [x] 8 cases defined with full content (case14-21)
- [x] All cert objectives verified against CySA+ CS0-003 domains
- [x] Difficulty distribution: 3,3,4,3,4,3,4,4 (four diff-3, four diff-4)
- [x] XP values: 150,150,250,150,250,150,250,250
- [x] All valid_answers normalized (lowercase)
- [x] All tools_type values defined and distinct
- [x] coc_reference: static, challenge_data ignored (same pattern as exec_reference)
- [x] siem_correlator: ALL matching rules fire (not first-match)
- [x] hunt_analyzer: confidence = SUPPORTS/(SUPPORTS+REFUTES) × 100; NEUTRAL excluded from denominator
- [x] case16 valid_answers: ["60","60%","60 percent"] — math verified (3/5×100=60)
- [x] case20 valid_answers: network isolation — scoring math verified (net=2 beats full isolation net=0)
- [x] disk_analyzer: TIMESTOMPED detection uses string comparison on ISO format
- [x] timeline_builder: gap threshold > 3600 seconds; phase labeling by keyword
- [x] case21 tools output corrected: gap1=392h 12m, gap2=124h 55m; phase labels per keyword rules (events 1-5 [Unknown], event 6 [Eradication], event 10 [Unknown])
- [x] containment_advisor: net score = effectiveness - tip_risk; tie → lower tip_risk wins
- [x] All hints escalate: URL → manual → tools → spoiler
- [x] NIGHTWIRE/Project MERIDIAN narrative consistent across all 8 cases
- [x] exam_tip in every debrief
- [x] Unit tests required for all 7 new dynamic tools

---

## 7. Definition of Done

- [ ] All tasks in tasks.md marked complete
- [ ] All 8 new cases visible in case menu after case13
- [ ] All 7 new dynamic tool functions return correct output
- [ ] `validate_content.py` passes on all 21 cases
- [ ] `check_imports.py` passes on all files
- [ ] All unit tests still pass
- [ ] spec status → Complete
