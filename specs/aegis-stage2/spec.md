# spec.md — AEGIS Stage 2: Cases 06-13
<!--
SCOPE: 8 new cases + 6 new tool functions. Zero engine changes.
NOT HERE: AEGIS Stage 3+ → future spec
NOT HERE: Any CIPHER changes
-->

**Module:** aegis-stage2
**Date:** 2026-04-12
**Status:** Reviewed
**Depends on:** aegis-stage1 (full engine, cases 01-05)
**Modifies DATA_MODEL.md:** No
**Modifies CONSTITUTION.md:** No

---

## 1. Purpose & Scope

### What problem does this module solve?
AEGIS Stage 1 covered Domains 1-3 at difficulty 1-3. CySA+ CS0-003 also
tests Domain 4 (Reporting & Communication, 17% of exam) and harder
applied skills: network traffic analysis, MITRE ATT&CK, firewall gaps,
and risk scoring. Stage 2 closes those gaps and finishes the NexusCorp arc.

### What does this module do?
Adds 8 cases (case06-13) and 6 new dynamic tool functions. All changes are
additive — no existing engine files modified. Dynamic tools parse structured
`challenge_data` and compute results rather than returning hardcoded output.

### Success Criteria
- [ ] All 8 new cases visible and playable in case menu
- [ ] All 6 new tool functions return correct output from real parsed input
- [ ] At least one deterministic unit test per new dynamic tool function
- [ ] `validate_content.py` passes on all 13 cases (case01-13)
- [ ] `check_imports.py` passes on all files
- [ ] All existing unit tests still pass

### In Scope
- [ ] aegis/content/cases/case06-13.json — eight case content files
- [ ] aegis/utils/tools.py — add 8 tool functions (6 dynamic + exec_reference + notification_reference) + dispatch entries
- [ ] aegis/validate_content.py — add 8 new tools_type values to allowlist
- [ ] aegis/content/registry.json — add case06-13 entries in order with correct difficulty and cert_objective values
- [ ] aegis/tests/test_tools_stage2.py — unit tests for all 6 new dynamic tool functions

### Out of Scope
- ❌ Engine changes (case_runner.py, main.py, save_manager.py — unchanged)
- ❌ AEGIS Stage 3+ → future
- ❌ Any CIPHER changes

---

## 2. Business Rules

All rules from aegis-stage1 spec §3 apply. No new rules.

---

## 3. Data Model

### New tools_type Allowlist Additions (AEGIS Stage 2)

| tools_type | Tool | Used in |
|-----------|------|---------|
| `traffic_analyzer` | Parses connection records, flags beaconing/exfil | case06 |
| `ioc_hunter` | Searches log data for IOC list matches | case07 |
| `attack_mapper` | Maps behavior description to MITRE ATT&CK technique | case08 |
| `rule_analyzer` | Evaluates traffic against firewall rule set | case09 |
| `risk_scorer` | Computes risk rating from likelihood × impact | case10 |
| `remediation_planner` | Ranks remediation items by impact/effort ratio | case12 |

**Routing rule (final):**
- case11 uses `tools_type: "exec_reference"`
- case13 uses `tools_type: "notification_reference"`
- Both functions return fully static reference tables and do NOT parse
  `challenge_data` at all — the input is ignored entirely.
- Do NOT use `"none"` for these cases. The `"none"` dispatch remains reserved
  for case05 (IR reference) only.

Updated tools_type allowlist for Stage 2 validate_content.py:
```python
_TOOLS_TYPE_ALLOWLIST = {
    "log_filter", "ioc_classifier", "vuln_scorer", "process_analyzer",
    "none",
    "traffic_analyzer", "ioc_hunter", "attack_mapper", "rule_analyzer",
    "risk_scorer", "remediation_planner", "exec_reference",
    "notification_reference",
}
```

### challenge_data formats by case

| Case | challenge_data format |
|------|-----------------------|
| case06 | Newline-separated CSV records: `timestamp,src,dst,port,bytes,interval_sec` |
| case07 | `IOC1,IOC2,IOC3\|\|\|log line 1\nlog line 2` |
| case08 | Behavior description string (keyword search) |
| case09 | `rule1\nrule2\|\|\|traffic1\ntraffic2` |
| case10 | `likelihood:N\|impact:N\|asset:TYPE\|exploited:yes/no` |
| case11 | Any string — ignored by exec_reference |
| case12 | Newline-separated items: `item_id\|ACTION\|EFFORT:N\|IMPACT:N\|DEPENDENCY:item_id_or_none` |
| case13 | Any string — ignored by notification_reference |

### Tool parsing contracts

**traffic_analyzer:** Split on `\n`, parse each record as 6 comma-separated fields.
Trust the `interval_sec` field directly — do NOT derive intervals from timestamps.
Flag as `[BEACON]` if: same dst_ip appears 3+ times AND all interval_sec values
for that dst are equal AND > 0. Flag as `[OK]` otherwise.

**ioc_hunter:** Split challenge_data on `|||` → left = IOC list, right = log data.
Parse IOC list as comma-separated, `.strip()` each value. Commas are not permitted
inside individual IOC values. Search is case-sensitive substring match only.
An IOC of `""` (empty after strip) is skipped.

**attack_mapper:** Behavior description string. Split into lowercase tokens,
search embedded ATT&CK table for keyword matches in technique name/description.
Return all matches sorted by match score (most keyword hits first), top match first.

**rule_analyzer:** Split challenge_data on `|||` → left = rules, right = traffic.
Rule format (one per line): `ACTION DIRECTION SRC DST PORT`
  where ACTION = ALLOW or DENY, DIRECTION = ANY (direction-agnostic for matching in Stage 2).
Traffic format (one per line): `SRC DST PORT DIRECTION`
For each traffic entry, evaluate rules top-down, first match wins.
Direction is used for display only — not factored into rule matching in Stage 2.

**risk_scorer:** Split on `|`, parse each token as `key:value` (case-insensitive keys,
trim whitespace). Required keys: likelihood, impact, asset, exploited.
Accepted asset values: {production, staging, test, workstation}.
Score = int(likelihood) × int(impact). Rating bands: 1-6 LOW, 7-12 MEDIUM,
13-18 HIGH, 19-25 CRITICAL.
`exploited:yes` adds an urgency note to the output — it does NOT change the
numeric score or rating band. The math is always L × I only.

**remediation_planner:** Split on `\n`, parse each item as pipe-separated tokens:
`item_id|ACTION|EFFORT:N|IMPACT:N|DEPENDENCY:item_id_or_none`
Rank by impact/effort ratio (higher = first). Tiebreaker order (deterministic):
  1. Dependency-free items before dependent items
  2. Higher impact first
  3. Lower effort first
  4. Original input order last
Dependent items cannot be scheduled before their dependency's rank.

---

## 4. Technical Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Dynamic tools | Parse challenge_data and compute output | Q3=B — more educational, more realistic |
| exec_reference / notification_reference | Explicit tools_type values | Avoids overloading "none" dispatch |
| case11/case13 tools_type | "exec_reference" / "notification_reference" | Static reference tables, challenge_data ignored entirely |
| challenge_data separator | `\|\|\|` (three pipes) | Unambiguous, won't appear in IPs, ports, or log lines |
| ATT&CK table | ~15 key techniques embedded in attack_mapper | Enough for CySA+ without bloating the tool |
| Risk formula | likelihood × impact (1-5 scale) = 1-25, no exploit modifier | Exploitation adds urgency note only; score stays L×I |
| Rule matching | Direction-agnostic in Stage 2 | Simplicity — direction shown for display, not logic |
| Remediation tiebreak | dep-free first → higher impact → lower effort → input order | Deterministic output regardless of equal ratios |
| IOC matching | Case-sensitive substring, .strip() each IOC, no commas in IOC values | Simple and unambiguous for Stage 2 |
| traffic_analyzer | Trust interval_sec field; do not derive from timestamps | Avoids timestamp parsing complexity |

---

## 5. Content — Cases 06-13

---

### Case 06 — Network Traffic Analysis

**id:** case06
**title:** C2 Beaconing
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 1 — Security Operations
**xp_base:** 100
**difficulty:** 2
**tools_type:** traffic_analyzer

#### challenge_data
```
2026-04-11T03:15:00,10.0.0.99,203.0.113.47,443,512,0\n2026-04-11T03:15:30,10.0.0.99,185.220.101.45,4444,128,30\n2026-04-11T03:16:00,10.0.0.99,185.220.101.45,4444,128,30\n2026-04-11T03:16:30,10.0.0.99,185.220.101.45,4444,128,30\n2026-04-11T03:17:00,10.0.0.99,8.8.8.8,53,64,0\n2026-04-11T03:17:30,10.0.0.99,185.220.101.45,4444,128,30\n2026-04-11T03:18:00,10.0.0.99,203.0.113.91,80,4096,0
```
*(fields: timestamp,src_ip,dst_ip,port,bytes,interval_sec)*

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — THREAT HUNT TEAM
PRIORITY: HIGH
ANALYST: YOU

Post-incident review of the NexusCorp compromise. Forensics
captured network flow data from 10.0.0.99 during the attack
window (03:15-03:18 UTC).

NETWORK FLOW — 10.0.0.99 (03:15-03:18 UTC):
TIMESTAMP            SRC           DST                PORT  BYTES  INTERVAL
2026-04-11T03:15:00  10.0.0.99  →  203.0.113.47       443   512    —
2026-04-11T03:15:30  10.0.0.99  →  185.220.101.45     4444  128    30s
2026-04-11T03:16:00  10.0.0.99  →  185.220.101.45     4444  128    30s
2026-04-11T03:16:30  10.0.0.99  →  185.220.101.45     4444  128    30s
2026-04-11T03:17:00  10.0.0.99  →  8.8.8.8            53    64     —
2026-04-11T03:17:30  10.0.0.99  →  185.220.101.45     4444  128    30s
2026-04-11T03:18:00  10.0.0.99  →  203.0.113.91       80    4096   —

One of these destinations shows a classic C2 beaconing pattern.
Identify the C2 server IP.
```

#### Challenge
`What is the external IP address that 10.0.0.99 is beaconing to?`

#### Valid Answers
`["185.220.101.45"]`

#### Hints
```
Hint 1: Go to https://attack.mitre.org/techniques/T1071/
        Read about Command and Control via Application Layer Protocol.
        Beaconing is defined by: regular interval, consistent payload size,
        repeated connections to the same external IP.

Hint 2: Filter the connections: look for repeated outbound connections where
        interval_sec is consistent (same value every time) and bytes is the
        same each time. A 0 interval means no repeated pattern — ignore those.
        Type 'tools' to run the traffic analyzer.

Hint 3: Type 'tools' in the game. The traffic analyzer flags connections
        with a consistent interval and payload as [BEACON]. The flagged
        destination IP is your answer.

Hint 4: SPOILER — 185.220.101.45 on port 4444 receives 4 connections at
        exactly 30-second intervals with exactly 128 bytes each. This is
        textbook C2 beaconing. Type: 185.220.101.45
```

#### Learn Text
```
Command and Control (C2) beaconing is how malware maintains contact with
an attacker's server after initial compromise. The malware calls home at
regular intervals to receive commands and send results.

Beaconing indicators:
  Consistent interval   — exact same number of seconds between connections
  Consistent payload    — same byte count each time (heartbeat packet)
  Unusual port          — non-standard ports (4444, 1337, 9001 are common)
  Non-business hours    — C2 traffic often runs 24/7 regardless of time
  External destination  — connections leaving the network perimeter

How to detect in a SOC:
  1. Baseline normal traffic for each internal host
  2. Alert on connections with < 60s interval to the same external IP
  3. Investigate any non-standard port with repeated connections
  4. Cross-reference destination IP with threat intel feeds

This technique maps to MITRE ATT&CK T1071 — Application Layer Protocol
(Command and Control tactic). CySA+ Domain 1 tests network traffic analysis
as a core SOC analyst skill.
```

#### Tools Field
`"Analyzes network connection records and flags beaconing patterns (consistent interval + consistent payload size)."`

#### Tools Output
```
TRAFFIC ANALYZER — network flow analysis

Analyzing 7 connection records from 10.0.0.99...

Grouping by destination IP...

185.220.101.45:4444 — 4 connections
  Intervals: 30s, 30s, 30s (CONSISTENT)
  Payload:   128, 128, 128 bytes (CONSISTENT)
  Verdict:   [BEACON] Regular interval + consistent payload — C2 indicator

203.0.113.47:443 — 1 connection
  Verdict:   [OK] Single connection, no pattern

8.8.8.8:53 — 1 connection
  Verdict:   [OK] DNS query, expected

203.0.113.91:80 — 1 connection
  Verdict:   [OK] Single connection, no pattern

FINDING: Beaconing detected → 185.220.101.45 port 4444
```

#### Debrief
```
summary: You identified 185.220.101.45 as the C2 server. The compromised
host 10.0.0.99 was beaconing every 30 seconds with a 128-byte heartbeat —
a classic C2 pattern. This confirms the attacker maintained persistent
access after the initial privilege escalation.

real_world: Detecting C2 beaconing is one of the most high-value threat
hunting activities in a SOC. Most SIEM and NDR platforms have built-in
beaconing detection based on interval and payload consistency. Analysts
also manually review NetFlow data for hosts with unusually regular outbound
connection patterns.

next_step: Practice with real tools:
TryHackMe: 'Network Analysis' room
https://tryhackme.com/room/packetsframes

cert_link: CySA+ CS0-003 Domain 1 — Security Operations:
"Given a scenario, analyze data to identify indicators of malicious activity
including network traffic indicators of C2 communication."

exam_tip: On the exam, C2 beaconing questions give you a connection table
and ask you to identify the suspicious destination. Look for: consistent
intervals (same seconds between connections), same payload size, non-standard
ports (anything other than 80, 443, 53), and connections persisting outside
business hours. The combination of regular interval + consistent bytes is
the defining signature.
```

---

### Case 07 — Threat Intelligence

**id:** case07
**title:** IOC Hunt
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 1 — Security Operations
**xp_base:** 100
**difficulty:** 2
**tools_type:** ioc_hunter

#### challenge_data
```
185.220.101.45,deploymaster,/tmp/.x|||2026-04-11T02:14:33 sshd[1234]: Accepted password for deploymaster from 10.0.0.99\n2026-04-11T02:15:01 sudo[1235]: deploymaster : TTY=pts/0 ; COMMAND=/bin/bash\n2026-04-11T02:30:15 nginx[800]: 203.0.113.44 - GET /login HTTP/1.1 200\n2026-04-11T03:02:17 sshd[1290]: Failed password for root from 203.0.113.91\n2026-04-11T03:15:45 cron[1301]: (root) CMD (/tmp/.x)
```
*(format: IOC1,IOC2,IOC3|||log line 1\nlog line 2...)*

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — THREAT INTEL TEAM
PRIORITY: HIGH
ANALYST: YOU

The threat intel team has published a fresh IOC feed for the
NexusCorp attacker. Three indicators have been extracted from
the malware sample and attacker infrastructure.

IOC FEED (NexusCorp Actor):
  185.220.101.45   — Known C2 server IP
  deploymaster     — Attacker credential artifact
  /tmp/.x          — Persistence script path

Cross-reference these IOCs against the authentication and
system logs from the staging server.

How many distinct log entries contain a match?
```

#### Challenge
`How many distinct log entries match at least one IOC from the threat intel feed?`

#### Valid Answers
`["3", "three"]`

#### Hints
```
Hint 1: Go to https://www.cisa.gov/topics/cyber-threats-and-advisories/indicators-of-compromise
        Read about how IOC feeds are used in threat hunting. Each IOC is
        a string to search for in logs, file paths, or network data.

Hint 2: Go through the log entries one by one and check each for any of
        the three IOC strings: 185.220.101.45, deploymaster, /tmp/.x
        Count distinct matching lines (a line matches if it contains any IOC).
        Type 'tools' to run the IOC hunter automatically.

Hint 3: Type 'tools' in the game. The IOC hunter searches each log line
        for any of the three IOC strings and marks matches. Count the
        [MATCH] lines — that is your answer.

Hint 4: SPOILER — Three log lines match:
        Line 1: 'deploymaster' in sshd accepted password line
        Line 2: 'deploymaster' in sudo command line
        Line 5: '/tmp/.x' in cron execution line
        Type: 3
```

#### Learn Text
```
Threat intelligence IOC correlation is how SOC analysts connect
attacker artifacts to their own environment. An IOC (Indicator of
Compromise) is evidence of a threat actor — IPs, domains, usernames,
file hashes, or file paths extracted from malware analysis or
incident reports.

IOC correlation workflow:
  1. Receive IOC feed (from ISAC, vendor, internal IR team)
  2. Search logs, EDR telemetry, and network captures for matches
  3. Each match is a potential true positive — investigate further
  4. Confirmed matches escalate to incident tickets

Types of IOCs:
  Network IOCs   — IP addresses, domains, URLs (check firewall/proxy logs)
  Host IOCs      — File hashes, paths, registry keys (check EDR)
  Account IOCs   — Usernames, credentials (check auth logs)
  Behavioral IOCs — Command patterns (check auditd, syslog)

IOC correlation appears in CySA+ Domain 1 threat intelligence objectives.
The exam tests whether you know which log source to check for each IOC type.
```

#### Tools Field
`"Searches each log entry for any IOC from the feed and reports matches with the matching indicator highlighted."`

#### Tools Output
```
IOC HUNTER — threat intelligence correlation

IOC Feed: 185.220.101.45 | deploymaster | /tmp/.x
Scanning 5 log entries...

[MATCH] Line 1 — IOC: 'deploymaster'
  2026-04-11T02:14:33 sshd[1234]: Accepted password for deploymaster from 10.0.0.99

[MATCH] Line 2 — IOC: 'deploymaster'
  2026-04-11T02:15:01 sudo[1235]: deploymaster : TTY=pts/0 ; COMMAND=/bin/bash

[NO MATCH] Line 3
  2026-04-11T02:30:15 nginx[800]: 203.0.113.44 - GET /login HTTP/1.1 200

[NO MATCH] Line 4
  2026-04-11T03:02:17 sshd[1290]: Failed password for root from 203.0.113.91

[MATCH] Line 5 — IOC: '/tmp/.x'
  2026-04-11T03:15:45 cron[1301]: (root) CMD (/tmp/.x)

Results: 3 matches from 5 log entries
IOCs confirmed in environment: deploymaster, /tmp/.x
IOC not found: 185.220.101.45 (check network logs separately)
```

#### Debrief
```
summary: You found 3 log entries matching threat intel IOCs. 'deploymaster'
appeared in both SSH authentication and sudo logs — confirming the attacker
used this credential to gain access. '/tmp/.x' appeared in a cron job —
revealing persistence that was planted after initial access. The C2 IP
185.220.101.45 was not in these logs (it appeared in network flow data
from case06, not auth logs).

real_world: Threat intel teams publish IOC feeds after each major incident.
SOC analysts run automated correlation rules (SIEM) to match new IOCs
against historical log data — this retroactive hunting often uncovers
earlier attacker activity that was missed in real time.

next_step: Practice with real tools:
TryHackMe: 'Threat Intelligence Tools' room
https://tryhackme.com/room/threatinteltools

cert_link: CySA+ CS0-003 Domain 1 — Security Operations:
"Given a scenario, utilize threat intelligence to support incident response
and identify indicators of compromise across log sources."

exam_tip: On the exam, IOC correlation questions test which log source
you check for each IOC type. Network IOCs (IPs, domains) → firewall/proxy
logs. Account IOCs (usernames) → authentication logs (syslog, Windows
Security log). File IOCs (hashes, paths) → EDR/endpoint telemetry.
Hash-based IOCs require exact match; string-based IOCs may have
case-insensitive partial matches.
```

---

### Case 08 — MITRE ATT&CK Mapping

**id:** case08
**title:** ATT&CK Mapping
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 1 — Security Operations
**xp_base:** 150
**difficulty:** 3
**tools_type:** attack_mapper

#### challenge_data
`"python3 binary with SUID bit set exploited to spawn interactive root shell from www-data web process"`

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — THREAT INTEL TEAM
PRIORITY: MEDIUM
ANALYST: YOU

Root cause analysis of the NexusCorp privilege escalation.
The IR team has documented the following observed behavior:

OBSERVED BEHAVIOR:
  - python3 binary had SUID bit set on the staging server
  - Attacker (running as www-data) executed python3 with os.setuid(0)
  - Result: interactive root shell spawned (PID 1004)
  - Vector: SUID misconfiguration, no exploit CVE required

Map this behavior to the correct MITRE ATT&CK technique.
What is the ATT&CK Technique ID?
```

#### Challenge
`What is the MITRE ATT&CK Technique ID for exploiting SUID binaries to gain elevated privileges?`

#### Valid Answers
`["t1548.001", "1548.001"]`
Note: T1548 (parent technique) is not accepted — the challenge asks for the
specific sub-technique for SUID/SGID exploitation.

#### Hints
```
Hint 1: Go to https://attack.mitre.org/
        Search for 'setuid' or 'SUID' in the search bar.
        Navigate to the matching technique and note the Technique ID
        (format: TXXXX or TXXXX.XXX for sub-techniques).

Hint 2: MITRE ATT&CK organizes techniques by Tactic. The relevant tactic
        here is 'Privilege Escalation' — the attacker moved from www-data
        to root. Look for a technique about abusing OS permission mechanisms.
        Type 'tools' to search the embedded ATT&CK reference.

Hint 3: Type 'tools' in the game. The ATT&CK mapper searches for keywords
        from the behavior description. Look for the technique flagged as
        matching 'SUID' or 'setuid' in the output.

Hint 4: SPOILER — T1548.001 is the sub-technique 'Abuse Elevation Control
        Mechanism: Setuid and Setgid'. The parent T1548 is too broad — the
        exam and this challenge expect the specific sub-technique.
        Tactic: Privilege Escalation. Mitigation: remove unnecessary SUID bits.
        Type: T1548.001
```

#### Learn Text
```
MITRE ATT&CK is the industry-standard framework for describing adversary
tactics, techniques, and procedures (TTPs). CySA+ CS0-003 requires
analysts to map observed behaviors to ATT&CK techniques.

Framework structure:
  Tactics    — the adversary's goal (e.g. Privilege Escalation)
  Techniques — how they achieve it (e.g. T1548)
  Sub-techniques — specific variants (e.g. T1548.001 = Setuid/Setgid)
  Mitigations — how defenders prevent it
  Detections  — how defenders detect it

Key ATT&CK tactics for CySA+:
  Initial Access       — how they got in (T1190 web exploit, T1078 valid accounts)
  Execution            — running malicious code (T1059 command interpreter)
  Persistence          — maintaining access (T1053 scheduled tasks)
  Privilege Escalation — gaining higher access (T1548 SUID/SGID)
  Defense Evasion      — hiding from detection (T1027 obfuscation)
  Command and Control  — communicating with attacker (T1071 app layer protocol)
  Exfiltration         — stealing data (T1041 exfil over C2)

For the NexusCorp attack, the full kill chain maps to:
  T1190 → T1078 → T1059.004 → T1548.001 → T1071.001
```

#### Tools Field
`"Searches the embedded MITRE ATT&CK technique reference for keywords from the behavior description."`

#### Tools Output (attack_mapper output — see §4 technical notes for embedded table)
```
ATT&CK MAPPER — technique lookup

Input: python3 binary with SUID bit set exploited to spawn interactive root shell from www-data web process

Searching for keywords: python3, suid, bit, set, exploited, spawn, root, shell, www-data, web, process

MATCH — T1548.001: Abuse Elevation Control Mechanism: Setuid and Setgid
  Tactic:      Privilege Escalation
  Description: Adversaries may perform shell escapes or exploit
               vulnerabilities in an application with the setuid or
               setgid bits to get code running in a different user's
               context. SUID binaries like python3 can be exploited
               to spawn a root shell via os.setuid(0).
  Detection:   Audit SUID/SGID file permissions. Monitor for unusual
               processes spawned by setuid binaries.
  Mitigation:  M1026 — Remove unnecessary SUID/SGID bits. Use
               file integrity monitoring to detect changes.

RELATED — T1059.004: Command and Scripting Interpreter: Unix Shell
  Tactic:      Execution
  Description: Attacker used Unix shell (bash) spawned by python3
               to execute commands as root.

Top match: T1548.001
```

#### Debrief
```
summary: You mapped the privilege escalation to T1548.001 — Abuse Elevation
Control Mechanism: Setuid and Setgid. This is the ATT&CK sub-technique for
SUID/SGID binary abuse. The full NexusCorp kill chain is:
T1190 (web exploit) → T1078 (valid accounts via deploymaster) →
T1059.004 (Unix shell) → T1548.001 (SUID privesc) → T1071.001 (C2 beaconing).

real_world: Mapping incidents to ATT&CK is standard practice for threat
intel reports and Purple Team exercises. ATT&CK mappings let defenders
identify detection gaps, prioritize security controls, and communicate
incident details to other security teams using a shared language.

next_step: Practice with real tools:
MITRE ATT&CK Navigator: https://mitre-attack.github.io/attack-navigator/

cert_link: CySA+ CS0-003 Domain 1 — Security Operations:
"Given a scenario, use the appropriate tools and techniques to determine
malicious activity and map it to threat intelligence frameworks including
MITRE ATT&CK."

exam_tip: On the exam, ATT&CK mapping questions describe an observed
behavior and ask for the Technique ID or tactic. Key ones to memorize:
T1190 (exploit public-facing app), T1078 (valid accounts), T1548 (SUID/sudo),
T1059 (command interpreter), T1071 (C2 protocol), T1041 (exfiltration over C2).
Also know: Initial Access ≠ Execution ≠ Persistence — tactics are the WHY,
techniques are the HOW.
```

---

### Case 09 — Firewall Rule Gap Analysis

**id:** case09
**title:** Firewall Gap
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 2 — Vulnerability Management
**xp_base:** 150
**difficulty:** 3
**tools_type:** rule_analyzer

#### challenge_data
```
DENY ANY 0.0.0.0/0 203.0.113.47 22\nALLOW ANY 0.0.0.0/0 203.0.113.47 443\nDENY ANY 0.0.0.0/0 203.0.113.47 3306\nALLOW ANY 0.0.0.0/0 ANY ANY|||203.0.113.1 203.0.113.47 8080 INBOUND\n203.0.113.1 203.0.113.47 22 INBOUND\n10.0.0.99 185.220.101.45 4444 OUTBOUND\n203.0.113.44 203.0.113.47 443 INBOUND
```
*(format: rules\nrule2|||traffic1\ntraffic2  — rule format: ACTION ANY SRC DST PORT)*

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — SECURITY ENGINEERING
PRIORITY: HIGH
ANALYST: YOU

Root cause analysis: how did the attacker reach nginx on port 8080?
The firewall team has provided the ruleset active during the attack.

FIREWALL RULES (evaluated top-down, first match wins):
  1. DENY  ANY → 203.0.113.47:22   (block SSH)
  2. ALLOW ANY → 203.0.113.47:443  (allow HTTPS)
  3. DENY  ANY → 203.0.113.47:3306 (block MySQL)
  4. ALLOW ANY → ANY:ANY           (allow everything else)

TRAFFIC DURING ATTACK WINDOW:
  203.0.113.1  → 203.0.113.47:8080  (attacker → nginx)
  203.0.113.1  → 203.0.113.47:22    (attacker → SSH)
  10.0.0.99    → 185.220.101.45:4444 (C2 beacon outbound)
  203.0.113.44 → 203.0.113.47:443   (legitimate HTTPS)

What port should have a DENY rule to prevent the initial compromise?
```

#### Challenge
`Which specific port number should have had an explicit DENY rule in this ruleset to block the attacker's initial access?`

#### Valid Answers
`["8080"]`

#### Hints
```
Hint 1: Go to https://www.cloudflare.com/learning/network-layer/what-is-a-firewall/
        Read about firewall rule ordering — 'first match wins'. A packet
        is allowed or denied by the first rule that matches it.
        Look at what rule matched the attacker's connection to port 8080.

Hint 2: Trace the attacker's connection (203.0.113.1 → 203.0.113.47:8080)
        through the rules top-down. Rule 1 is for port 22 — no match.
        Rule 2 is for port 443 — no match. Rule 3 is for port 3306 — no match.
        Rule 4 is ALLOW ANY → ANY — match. Port 8080 falls through to the
        catch-all ALLOW. Type 'tools' to run the rule analyzer.

Hint 3: Type 'tools' in the game. The rule analyzer evaluates each traffic
        entry against the rules and shows which rule matched. Look for the
        attacker's connection and which port has no specific DENY rule.

Hint 4: SPOILER — Port 8080 had no explicit DENY rule. The catch-all
        ALLOW rule (rule 4) permitted the attacker to reach nginx.
        The fix: add 'DENY ANY 0.0.0.0/0 203.0.113.47 8080' before rule 4.
        Type: 8080
```

#### Learn Text
```
Firewall rule analysis is a core vulnerability management skill. Misconfigurations
in firewall rulesets are one of the most common causes of preventable breaches.

Key concepts:
  First match wins  — rules are evaluated top-down; first matching rule applies
  Implicit deny     — some firewalls deny all traffic not explicitly permitted
  Catch-all ALLOW   — 'ALLOW ANY ANY' at the end defeats implicit deny
  Principle of least privilege — only permit what is explicitly required

Common firewall misconfigurations:
  Catch-all ALLOW rules     — as seen here: port 8080 not explicitly blocked
  Overly broad source ranges — ALLOW from 0.0.0.0/0 instead of specific IPs
  Missing egress rules       — only inbound rules, no outbound (C2 beacon went out)
  Rule ordering errors       — ALLOW before DENY for the same traffic

Firewall review checklist:
  1. Is there an explicit DENY for all unused ports?
  2. Is the catch-all rule DENY rather than ALLOW?
  3. Are management ports (22, 3389) restricted to known admin IPs?
  4. Are egress rules in place for outbound C2 prevention?
```

#### Tools Field
`"Evaluates each traffic entry against the firewall rules top-down and shows which rule matched and the resulting action."`

#### Tools Output
```
RULE ANALYZER — firewall policy evaluation

Rules loaded: 4
Traffic entries: 4

Evaluating traffic...

[ALLOW via Rule 4] 203.0.113.1 → 203.0.113.47:8080
  Rule 1: DENY port 22 — no match
  Rule 2: ALLOW port 443 — no match
  Rule 3: DENY port 3306 — no match
  Rule 4: ALLOW ANY:ANY — MATCH → ALLOWED ← GAP: no deny rule for port 8080

[DENY via Rule 1] 203.0.113.1 → 203.0.113.47:22
  Rule 1: DENY port 22 — MATCH → DENIED

[ALLOW via Rule 4] 10.0.0.99 → 185.220.101.45:4444
  Rules 1-3: no match
  Rule 4: ALLOW ANY:ANY — MATCH → ALLOWED ← EGRESS GAP: C2 beacon permitted

[ALLOW via Rule 2] 203.0.113.44 → 203.0.113.47:443
  Rule 2: ALLOW port 443 — MATCH → ALLOWED (expected)

Gap analysis:
  Port 8080: no explicit DENY — recommend: DENY ANY 0.0.0.0/0 203.0.113.47 8080
  Port 4444 outbound: no egress restriction — recommend egress deny for non-standard ports
```

#### Debrief
```
summary: You identified port 8080 as the firewall gap. The catch-all ALLOW
rule permitted all traffic not explicitly denied — and port 8080 was never
explicitly denied. The fix is to add a specific DENY rule for port 8080
before the catch-all. The egress gap (port 4444 C2 beacon allowed out) is
a bonus finding that would have contained the compromise earlier.

real_world: Firewall rule reviews are a standard part of vulnerability
management programs. Security teams periodically audit rulesets to identify
catch-all ALLOWs, unused open ports, and missing egress controls. Many
compliance frameworks (PCI DSS, ISO 27001) require periodic firewall reviews.

next_step: Practice with real tools:
TryHackMe: 'Firewalls' room
https://tryhackme.com/room/redteamfirewalls

cert_link: CySA+ CS0-003 Domain 2 — Vulnerability Management:
"Given a scenario, analyze and interpret output from security technologies
and identify misconfigurations that create vulnerability exposure."

exam_tip: On the exam, firewall rule questions often ask you to trace a
packet through a ruleset and identify the matching rule. Remember: first
match wins, rules are evaluated top-down. Also know: implicit deny vs
explicit deny, and that egress filtering (blocking outbound C2) is just
as important as ingress filtering.
```

---

### Case 10 — Risk Scoring

**id:** case10
**title:** Risk Score
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 2 — Vulnerability Management
**xp_base:** 150
**difficulty:** 3
**tools_type:** risk_scorer

#### challenge_data
`"likelihood:4|impact:5|asset:production|exploited:yes"`

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — RISK MANAGEMENT TEAM
PRIORITY: HIGH
ANALYST: YOU

Post-incident risk assessment for the NexusCorp finding.
The risk committee needs a formal risk rating for the
nginx 1.24.0 RCE vulnerability (CVE-FAKE-2024-099) before
approving the emergency patch budget.

FINDING DETAILS:
  Vulnerability:   CVE-FAKE-2024-099 — nginx 1.24.0 Unauth RCE
  Likelihood:      4 out of 5 (actively exploited in the wild)
  Impact:          5 out of 5 (production server, full root access)
  Asset type:      Production (customer-facing)
  Exploited:       Yes (confirmed in this incident)

Using a standard 5×5 likelihood × impact risk matrix,
what is the risk RATING for this finding?
```

#### Challenge
`What is the risk rating for this finding using a 5x5 likelihood × impact matrix?`

#### Valid Answers
`["critical", "critical risk"]`

#### Hints
```
Hint 1: Go to https://www.risksense.com/blog/risk-rating-methodology/
        Read about likelihood × impact risk matrices. The formula is simple:
        Risk Score = Likelihood × Impact. Map the score to a rating band.

Hint 2: Calculate: Likelihood (4) × Impact (5) = 20.
        Standard rating bands for a 5×5 matrix (max score 25):
          1-6:   LOW
          7-12:  MEDIUM
          13-18: HIGH
          19-25: CRITICAL
        Type 'tools' to run the risk scorer and verify.

Hint 3: Type 'tools' in the game. The risk scorer calculates likelihood × impact,
        maps to a rating band, and adds an urgency note if exploited=yes.
        The rating itself comes from the score alone — read it in the output.

Hint 4: SPOILER — 4 × 5 = 20. Score 20 falls in the CRITICAL band (19-25).
        The 'actively exploited' flag confirms immediate action required.
        Type: critical
```

#### Learn Text
```
Risk scoring is how security teams communicate finding severity in business
terms. Raw CVSS scores tell you about the vulnerability — risk scores
tell you about the risk to YOUR specific environment.

Standard 5×5 risk matrix:
  Score = Likelihood (1-5) × Impact (1-5) = 1 to 25
  LOW:      1-6   — accept, patch at next maintenance window
  MEDIUM:   7-12  — mitigate within 90 days
  HIGH:     13-18 — mitigate within 30 days
  CRITICAL: 19-25 — mitigate immediately

Likelihood factors:
  1 = Theoretical only, no known exploits
  3 = Public exploit exists, not widely used
  5 = Actively exploited in the wild, trivial to exploit

Impact factors:
  1 = No business impact (test system, no data)
  3 = Moderate (internal system, limited data)
  5 = Severe (production, customer data, full system compromise)

Risk vs CVSS:
  CVSS scores the vulnerability in isolation.
  Risk scores the vulnerability in your context.
  A CVSS 9.8 on an air-gapped test system may be LOW risk.
  A CVSS 5.3 on your primary customer database may be HIGH risk.
```

#### Tools Field
`"Calculates risk score using likelihood × impact and maps to a rating band, adjusting for asset type and active exploitation."`

#### Tools Output
```
RISK SCORER — finding risk assessment

Input parameters:
  Likelihood:  4 / 5 (actively exploited in the wild)
  Impact:      5 / 5 (production server, full root access)
  Asset type:  Production
  Exploited:   Yes (confirmed in incident)

Calculation:
  Base score:  4 × 5 = 20
  Rating band: CRITICAL (19-25)

Adjustments:
  Score is L × I only — no numeric modifier applied.
  Exploited=yes → urgency escalated (do not wait for next change window)

RISK RATING: CRITICAL (Score: 20/25)
Recommended response: PATCH IMMEDIATELY
SLA: Emergency — exploited critical findings require same-day remediation
```

#### Debrief
```
summary: You correctly scored the finding as CRITICAL (20/25). Likelihood 4
(actively exploited) × Impact 5 (production + full root compromise) = 20,
placing it firmly in the CRITICAL band. The confirmed exploitation in this
incident removes any ambiguity about the risk level.

real_world: Risk scoring is used to justify security budgets and prioritize
remediation queues. When you tell the CISO 'CRITICAL risk, score 20/25,
actively exploited in production', that language maps directly to emergency
patch approval processes. Risk ratings also drive SLA — most organizations
require CRITICAL findings to be remediated within 24-48 hours.

next_step: Practice with real tools:
NIST Risk Management Framework: https://csrc.nist.gov/projects/risk-management

cert_link: CySA+ CS0-003 Domain 2 — Vulnerability Management:
"Given a scenario, apply risk-based prioritization to remediation of
vulnerabilities using likelihood and impact analysis."

exam_tip: On the exam, risk scoring questions give you likelihood and impact
values and ask for the rating. Memorize the 5×5 bands: 1-6 LOW, 7-12 MEDIUM,
13-18 HIGH, 19-25 CRITICAL. Also know: risk = likelihood × impact (NOT
likelihood + impact). And: CVSS measures vulnerability severity; risk
measures business exposure — they are not the same.
```

---

### Case 11 — Executive Reporting

**id:** case11
**title:** Exec Brief
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 4 — Reporting and Communication
**xp_base:** 100
**difficulty:** 2
**tools_type:** exec_reference

#### challenge_data
`"The NexusCorp incident resulted in full root compromise of the staging server. Estimated recovery cost: $45,000. No customer PII was accessed. Root cause: unpatched nginx CVE. Remediation: patch applied, firewall rules updated."`

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — CISO OFFICE
PRIORITY: MEDIUM
ANALYST: YOU

The CISO needs an executive incident report for the NexusCorp
compromise. You are drafting the report sections.

The incident resulted in:
  - Full root compromise of the staging server
  - Estimated recovery cost: $45,000
  - No customer PII accessed or exfiltrated
  - Root cause: unpatched nginx RCE (CVE-FAKE-2024-099)
  - Remediation: patch applied, firewall rules updated

Executive reports follow a standard structure. The $45,000
recovery cost estimate belongs in a specific named section.

In which section of a standard executive incident report does
the recovery cost estimate belong?
```

#### Challenge
`In which section of a standard executive incident report does the financial recovery cost belong?`

#### Valid Answers
`["business impact", "business impact analysis", "impact", "impact analysis"]`

#### Hints
```
Hint 1: Go to https://www.sans.org/white-papers/incident-handlers-handbook/
        Read the section on incident reporting. Executive reports have
        named sections. Financial impact belongs in the section that
        describes consequences to the organization, not the technical details.

Hint 2: Standard executive report sections:
        Executive Summary, Timeline, Technical Analysis,
        Business Impact, Recommendations, Lessons Learned.
        The $45,000 recovery cost is a business consequence, not a
        technical finding. Which section covers business consequences?
        Type 'tools' to see the full exec report structure reference.

Hint 3: Type 'tools' in the game. The exec report reference table
        shows each section with its purpose and what belongs in it.
        Match the recovery cost to the correct section.

Hint 4: SPOILER — Recovery costs, operational downtime, and reputational
        impact belong in the 'Business Impact' section. This section
        translates technical findings into business language for
        non-technical executives. Type: business impact
```

#### Learn Text
```
Executive reporting is how security teams communicate incidents to leadership.
Executives need business context, not technical details — your job is to
translate findings into terms that drive decisions.

Standard executive incident report sections:

1. EXECUTIVE SUMMARY
   One page. What happened, when, how contained, current status.
   Audience: CEO, board. No technical jargon.

2. TIMELINE
   Chronological sequence: when detected, when escalated, when contained.
   Key dates and actions. Use timestamps.

3. TECHNICAL ANALYSIS
   Root cause, attack vector, affected systems. Technical details for IT/security
   leadership. CVE IDs, affected software versions, attack chain.

4. BUSINESS IMPACT
   Financial cost (recovery, downtime, regulatory fines).
   Operational impact (systems unavailable, SLA breaches).
   Reputational impact (customer notification, press).
   Data impact (records affected, PII involved).

5. RECOMMENDATIONS
   Prioritized list of controls to prevent recurrence.
   Includes cost estimates and implementation timelines.

6. LESSONS LEARNED
   What worked, what didn't, gaps in detection/response.
   Process improvements for the IR playbook.

CySA+ Domain 4 tests whether you can structure, write, and deliver
reports appropriate for the audience (technical vs executive).
```

#### Tools Field
`"Displays the standard executive incident report structure with section descriptions and content guidance."`

#### Tools Output
```
EXEC REPORT REFERENCE — standard incident report structure

SECTION 1: EXECUTIVE SUMMARY
  Purpose:  High-level incident overview for C-suite/board
  Contains: What happened, scope, current status, key decisions needed
  Length:   1 page maximum

SECTION 2: TIMELINE
  Purpose:  Chronological sequence of events
  Contains: Detection time, escalation, containment, recovery milestones
  Format:   Timestamp | Event | Actor

SECTION 3: TECHNICAL ANALYSIS
  Purpose:  Root cause and attack vector for security leadership
  Contains: CVE IDs, affected systems, attack chain, TTPs
  Audience: CISO, IT management

SECTION 4: BUSINESS IMPACT
  Purpose:  Business consequences in non-technical terms
  Contains: Financial cost (recovery, downtime, fines)
            Operational impact (availability, SLA breach)
            Reputational impact (customer, press, regulatory)
            Data impact (PII records, retention obligations)

SECTION 5: RECOMMENDATIONS
  Purpose:  Prioritized action items to prevent recurrence
  Contains: Control improvements, estimated costs, timelines, owners

SECTION 6: LESSONS LEARNED
  Purpose:  IR process improvement
  Contains: What worked, what didn't, detection gaps, playbook updates
```

#### Debrief
```
summary: Recovery costs belong in the Business Impact section. This section
translates the technical incident into business language — dollars, downtime,
data exposure — that executives use to make resource allocation decisions.
The $45,000 recovery cost is a business consequence, not a technical finding.

real_world: Security analysts often write the technical analysis section but
work with a communications team or their manager to write the executive
summary and business impact sections. The key skill is knowing which
information goes where so the report reaches the right audience with the
right level of detail.

next_step: Practice with real examples:
SANS Incident Handler's Handbook: https://www.sans.org/white-papers/incident-handlers-handbook/

cert_link: CySA+ CS0-003 Domain 4 — Reporting and Communication:
"Given a scenario, create and deliver reports and communicate results
of vulnerability assessments and incidents to various stakeholders."

exam_tip: On the exam, reporting questions test audience awareness. Technical
details (CVEs, attack chains, tool output) go in Technical Analysis.
Business consequences (costs, downtime, data records) go in Business Impact.
Action items (what to fix and when) go in Recommendations. The exam often
presents a finding and asks which section it belongs in.
```

---

### Case 12 — Remediation Prioritization

**id:** case12
**title:** Remediation Order
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 4 — Reporting and Communication
**xp_base:** 250
**difficulty:** 4
**tools_type:** remediation_planner

#### challenge_data
```
item01|patch nginx 1.24.0|EFFORT:1|IMPACT:5|DEPENDENCY:none\nitem02|reset deploymaster credentials|EFFORT:1|IMPACT:4|DEPENDENCY:none\nitem03|remove SUID from python3|EFFORT:2|IMPACT:4|DEPENDENCY:none\nitem04|implement WAF rules|EFFORT:3|IMPACT:3|DEPENDENCY:item01\nitem05|network segmentation|EFFORT:5|IMPACT:5|DEPENDENCY:none\nitem06|security awareness training|EFFORT:4|IMPACT:2|DEPENDENCY:none
```
*(format: item_id|ACTION|EFFORT:N|IMPACT:N|DEPENDENCY:item_id_or_none — effort/impact 1-5)*

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — SECURITY ENGINEERING
PRIORITY: HIGH
ANALYST: YOU

The remediation plan for the NexusCorp incident has been drafted.
Six actions are identified. The team has limited bandwidth — they
need to know what to do FIRST.

REMEDIATION ITEMS:
  item01  Patch nginx 1.24.0              [Effort: 1, Impact: 5, No deps]
  item02  Reset deploymaster credentials  [Effort: 1, Impact: 4, No deps]
  item03  Remove SUID from python3        [Effort: 2, Impact: 4, No deps]
  item04  Implement WAF rules             [Effort: 3, Impact: 3, Requires: item01]
  item05  Network segmentation            [Effort: 5, Impact: 5, No deps]
  item06  Security awareness training     [Effort: 4, Impact: 2, No deps]

Effort and Impact are rated 1-5 (1=lowest).
Priority = Impact ÷ Effort ratio (higher = do first).
Items with dependencies cannot be started until their dependency is done.
Tiebreaker: dependency-free first, then higher impact, then lower effort.

What is the NAME of the remediation action that should be executed FIRST?
```

#### Challenge
`Based on highest impact/effort ratio, what remediation action should be completed first?`

#### Valid Answers
`["patch nginx", "patch nginx 1.24.0"]`
Canonical answer: **"patch nginx"** — the challenge and tool output both use this
short form. "patch nginx 1.24.0" accepted as a natural variant.

#### Hints
```
Hint 1: Go to https://www.cisa.gov/known-exploited-vulnerabilities-catalog
        Read about how CISA prioritizes known exploited vulnerabilities.
        The principle: highest impact for lowest effort = highest priority
        (also called 'quick wins' — easy to do, big security payoff).

Hint 2: Calculate the impact/effort ratio for each item:
        item01 patch nginx:    5 ÷ 1 = 5.0  ← highest ratio
        item02 reset creds:    4 ÷ 1 = 4.0
        item03 remove SUID:    4 ÷ 2 = 2.0
        item04 WAF rules:      3 ÷ 3 = 1.0  (also blocked — depends on item01)
        item05 segmentation:   5 ÷ 5 = 1.0
        item06 awareness:      2 ÷ 4 = 0.5
        Type 'tools' to run the remediation planner automatically.

Hint 3: Type 'tools' in the game. The remediation planner calculates
        impact/effort ratios, respects dependencies, and outputs a
        ranked plan. The first item in the ranked output is your answer.

Hint 4: SPOILER — Patch nginx 1.24.0 has the highest ratio (5.0) because
        it closes the original entry point (CVSS 9.8 actively exploited)
        with minimal effort (a single package update). It also unblocks
        the WAF rule implementation. Type: patch nginx 1.24.0
```

#### Learn Text
```
Remediation prioritization is a critical skill when you have more findings
than time. The goal is maximum risk reduction for minimum effort.

Impact/Effort ratio method (quick wins first):
  Priority = Impact ÷ Effort
  High ratio = high impact, low effort = do first
  Low ratio  = low impact, high effort = defer or deprioritize

Additional prioritization factors:
  Active exploitation  — if being exploited NOW, patch regardless of ratio
  Dependencies         — some actions unlock others (sequence matters)
  Asset criticality    — production > staging > test
  Compliance deadline  — regulatory requirements can override ratio
  Cost                 — financial budget constraints

Common prioritization frameworks:
  CISA KEV catalog   — known exploited vulns, must patch within deadline
  CVSS + context     — CVSS score adjusted for your environment
  Risk score         — likelihood × impact (as in case10)
  DREAD model        — Damage, Reproducibility, Exploitability, Affected, Discoverability

Remediation sequencing:
  Dependencies must be respected — implementing WAF rules without patching
  the underlying nginx first may be bypassed by the same exploit vector.
  Always identify dependencies before building the remediation schedule.
```

#### Tools Field
`"Ranks remediation actions by impact/effort ratio, respects dependency ordering, and outputs a prioritized remediation plan."`

#### Tools Output
```
REMEDIATION PLANNER — priority ranking

Calculating impact/effort ratios...

RANK 1 [item01]: patch nginx
  Effort: 1 | Impact: 5 | Ratio: 5.00 | Dependency: none
  Rationale: Highest quick-win ratio. Closes CVE-FAKE-2024-099 entry point.
             Unblocks item04 (WAF rules).

RANK 2 [item02]: reset deploymaster credentials
  Effort: 1 | Impact: 4 | Ratio: 4.00 | Dependency: none
  Rationale: High ratio, removes attacker's known valid credential.

RANK 3 [item03]: remove SUID from python3
  Effort: 2 | Impact: 4 | Ratio: 2.00 | Dependency: none
  Rationale: Closes privilege escalation vector from T1548.001.

RANK 4 [item05]: network segmentation
  Effort: 5 | Impact: 5 | Ratio: 1.00 | Dependency: none
  Tiebreaker applied: dep-free before item04 (which requires item01 done first)
  Rationale: High impact — plan as longer-term project.

RANK 5 [item04]: implement WAF rules
  Effort: 3 | Impact: 3 | Ratio: 1.00 | Dependency: item01 [RANK 1 — complete]
  Rationale: Now unblocked. Schedule after item01 completion.

RANK 6 [item06]: security awareness training
  Effort: 4 | Impact: 2 | Ratio: 0.50 | Dependency: none
  Rationale: Lowest ratio — important but schedule last.

Recommended execution order: item01 → item02 → item03 → item05 → item04 → item06
```

#### Debrief
```
summary: Patching nginx 1.24.0 is the highest priority — it has the best
impact/effort ratio (5.0) and closes the original entry point that allowed
the entire compromise. It also unblocks the WAF rule implementation. The
next two quick wins (reset credentials, remove SUID) are also low-effort
and should follow immediately.

real_world: Remediation prioritization is a constant negotiation between
security teams and operations. Security wants everything patched immediately;
operations has change windows and maintenance schedules. Impact/effort
analysis gives security a defensible, data-driven argument for sequencing.
CISA's Known Exploited Vulnerabilities catalog effectively forces the
conversation by setting mandatory deadlines.

next_step: Practice with real tools:
CISA KEV Catalog: https://www.cisa.gov/known-exploited-vulnerabilities-catalog

cert_link: CySA+ CS0-003 Domain 4 — Reporting and Communication:
"Given a scenario, develop and recommend remediation strategies based
on risk prioritization and organizational constraints."

exam_tip: On the exam, remediation prioritization questions give you a list
of findings and ask which to address first. The answer is almost always:
(1) actively exploited Critical findings first, (2) then high impact/low
effort quick wins, (3) then remaining by CVSS or risk score. Dependencies
and compliance deadlines can override ratio ordering — watch for those.
```

---

### Case 13 — Breach Notification

**id:** case13
**title:** Breach Notification
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 4 — Reporting and Communication
**xp_base:** 250
**difficulty:** 4
**tools_type:** notification_reference

#### challenge_data
`"Veridian Systems operates in the EU. The staging server breach involved a database containing 1,200 EU customer email addresses. The breach was confirmed on 2026-04-11T03:15 UTC. No financial data was exposed."`

#### Narrative
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — LEGAL AND COMPLIANCE
PRIORITY: CRITICAL
ANALYST: YOU

The NexusCorp post-incident review has confirmed a data exposure.
The staging server database contained 1,200 EU customer email
addresses. The breach was confirmed at 03:15 UTC on 2026-04-11.

Legal has two questions before filing the notification:
  1. Which regulation applies to EU customer data?
  2. What is the notification deadline?

SCENARIO FACTS:
  - Organization: Veridian Systems (operates in EU)
  - Data exposed: 1,200 EU customer email addresses (personal data)
  - Breach confirmed: 2026-04-11 at 03:15 UTC
  - Financial data: none exposed
  - Affected individuals: 1,200

Under the applicable regulation, what is the maximum number
of hours after breach discovery that Veridian must notify
the supervisory authority?
```

#### Challenge
`Under GDPR, what is the maximum number of hours to notify the supervisory authority after discovering a personal data breach?`

#### Valid Answers
`["72", "72 hours"]`

#### Hints
```
Hint 1: Go to https://gdpr-info.eu/art-33-gdpr/
        Read Article 33 of the GDPR — 'Notification of a personal data
        breach to the supervisory authority'. Look for the time limit.

Hint 2: The scenario involves EU customer personal data (email addresses).
        The applicable regulation is GDPR (General Data Protection Regulation).
        GDPR Article 33 sets a specific hour limit for breach notification
        to the supervisory authority (e.g. the ICO in the UK, CNIL in France).
        Type 'tools' to see the breach notification reference table.

Hint 3: Type 'tools' in the game. The notification reference table lists
        key regulations with their notification timelines. Find GDPR and
        read the supervisory authority notification requirement.

Hint 4: SPOILER — GDPR Article 33 requires notification to the supervisory
        authority 'without undue delay and, where feasible, not later than
        72 hours' after becoming aware of the breach. Type: 72
```

#### Learn Text
```
Breach notification requirements are determined by which regulations apply
to your organization and the type of data involved. Analysts must know
the key timeframes to avoid regulatory penalties.

Key breach notification regulations:

GDPR (EU — General Data Protection Regulation):
  Applies to:   Any org processing EU residents' personal data
  To regulator: Within 72 hours of becoming aware (Article 33)
  To subjects:  'Without undue delay' if high risk to individuals (Article 34)
  Penalty:      Up to €20M or 4% of global annual turnover

HIPAA (US — Health Insurance Portability and Accountability Act):
  Applies to:   Healthcare providers, insurers, and their business associates
  To HHS:       Within 60 days of discovery
  To subjects:  Within 60 days; within 60 days via media if >500 in a state
  Penalty:      Up to $1.9M per violation category per year

PCI DSS (Payment Card Industry Data Security Standard):
  Applies to:   Any org storing, processing, or transmitting cardholder data
  To brands:    Immediately upon suspicion
  To law enf.:  Within 72 hours in some jurisdictions
  Penalty:      Fines and loss of card processing rights

CCPA (California Consumer Privacy Act):
  Applies to:   Businesses serving California residents (revenue thresholds)
  To subjects:  'In the most expedient time possible'
  Penalty:      $100-$750 per consumer per incident

Notification triggers (GDPR):
  Personal data breach = any breach of security leading to accidental/unlawful
  destruction, loss, alteration, unauthorized disclosure or access.
  Email addresses = personal data under GDPR → notification required.
```

#### Tools Field
`"Displays breach notification requirements for key regulations including GDPR, HIPAA, PCI DSS, and CCPA with notification timelines."`

#### Tools Output
```
NOTIFICATION REFERENCE — breach notification requirements

GDPR (EU — General Data Protection Regulation)
  Trigger:       Personal data breach affecting EU residents
  To regulator:  Without undue delay; where feasible, no later than 72 hours
                 (Article 33 — this is the maximum, not the recommended wait time)
  To subjects:   Without undue delay if high risk to individuals (Article 34)
  Personal data: Name, email, IP address, location, health data, etc.
  Applies here:  YES — EU customer email addresses = personal data

HIPAA (US — Health Insurance Portability and Accountability Act)
  Trigger:       Unsecured protected health information (PHI) breach
  To HHS:        60 days from discovery
  To subjects:   60 days from discovery
  Applies here:  NO — no health data involved

PCI DSS (Payment Card Industry)
  Trigger:       Cardholder data (card numbers, CVV, PIN) compromised
  To card brands: Immediately upon suspicion
  Applies here:  NO — no payment card data involved

CCPA (California Consumer Privacy Act)
  Trigger:       California residents' non-encrypted personal data breached
  To subjects:   Expedient time / without unreasonable delay
  Applies here:  POSSIBLY — depends on California residency of affected users

VERDICT for this scenario:
  Primary regulation: GDPR (Article 33)
  Requirement: Notify without undue delay; no later than 72 hours maximum
  Deadline: 72 hours from 2026-04-11T03:15 UTC = by 2026-04-12T03:15 UTC
  Action: Notify supervisory authority now — do not wait for the 72-hour limit
```

#### Debrief
```
summary: You correctly identified GDPR as the applicable regulation and 72
hours as the notification deadline. EU customer email addresses are personal
data under GDPR — any unauthorized access triggers the Article 33
notification obligation. With the breach confirmed at 03:15 UTC on April 11,
Veridian must notify their supervisory authority by 03:15 UTC on April 12.

real_world: Missing a notification deadline carries significant regulatory
risk — GDPR fines for late notification can reach €10M or 2% of global
turnover. Security analysts work closely with legal and compliance teams
to identify applicable regulations and prepare notification documents.
The analyst's role is to provide accurate technical facts (what was accessed,
when, how many records) that legal uses to complete the notification.

next_step: Practice with real examples:
GDPR Article 33: https://gdpr-info.eu/art-33-gdpr/

cert_link: CySA+ CS0-003 Domain 4 — Reporting and Communication:
"Given a scenario, identify the appropriate communication plan and
notification requirements for data breaches including regulatory obligations."

exam_tip: On the exam, breach notification questions always specify the
regulation or the type of data — read carefully. GDPR = 72 hours to
regulator. HIPAA = 60 days. PCI DSS = immediately to card brands.
The exam also tests: who to notify (regulator vs individuals vs both),
and what triggers notification (not all breaches require individual
notification — only those posing 'high risk' under GDPR).
```

---

## 6. Pre-Flight Checklist

- [x] 8 cases defined with full content
- [x] All cert objectives verified against CySA+ CS0-003 domains
- [x] Difficulty reset: 2, 2, 3, 3, 3, 2, 4, 4
- [x] XP values: 100, 100, 150, 150, 150, 100, 250, 250
- [x] All valid_answers normalized (lowercase)
- [x] All tools_type values defined, distinct, no "none" ambiguity
- [x] exec_reference and notification_reference as explicit tools_type values (static, ignore challenge_data)
- [x] Dynamic tool parsing contracts defined in §3 (formats, edge cases, tiebreakers)
- [x] challenge_data separator `|||` defined and consistent
- [x] Case12 uses stable item IDs (item01-item06) for dependency references
- [x] case08 valid_answers restricted to sub-technique T1548.001 only
- [x] risk_scorer: exploitation adds urgency note only, no score modifier
- [x] remediation_planner: deterministic tiebreaker defined
- [x] rule_analyzer: direction-agnostic matching, direction display-only
- [x] ioc_hunter: case-sensitive substring, .strip() on IOCs
- [x] traffic_analyzer: trusts interval_sec field, no timestamp math
- [x] exam_tip in every debrief
- [x] All hints escalate: URL → manual → tools → spoiler
- [x] Mirror story: NexusCorp arc closes in case13
- [x] Unit tests required for all 6 new dynamic tools

---

## 7. Definition of Done

- [ ] All tasks in tasks.md marked complete
- [ ] All 8 new cases visible in case menu after case05
- [ ] All 6 new tool functions return correct output
- [ ] `validate_content.py` passes on all 13 cases
- [ ] `check_imports.py` passes on all files
- [ ] All unit tests still pass
- [ ] spec status → Complete
