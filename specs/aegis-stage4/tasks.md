# tasks.md — AEGIS Stage 4: Cases 22-31
<!--
SDD Phase 3 of 4: Tasks
Prev: plan.md -> spec.md
Next: build
-->

**Module:** aegis-stage4
**Date:** 2026-04-15
**Status:** Ready to build

---

## Phase 1 — validate_content.py allowlist update

### Task 01 — Add Stage 4 tools_type values to allowlist

**File:** `aegis/validate_content.py`
**Change:** Add 10 new entries to `_TOOLS_TYPE_ALLOWLIST`.

Final allowlist (full set after Stage 4):
```python
_TOOLS_TYPE_ALLOWLIST = {
    "log_filter", "ioc_classifier", "vuln_scorer", "process_analyzer", "none",
    "traffic_analyzer", "ioc_hunter", "attack_mapper", "rule_analyzer",
    "risk_scorer", "remediation_planner", "exec_reference", "notification_reference",
    "siem_correlator", "log_classifier", "hunt_analyzer", "mem_analyzer",
    "disk_analyzer", "coc_reference", "containment_advisor", "timeline_builder",
    "vuln_prioritizer", "patch_reference", "surface_analyzer", "sast_analyzer",
    "intel_correlator", "metrics_calculator", "compliance_mapper", "sla_tracker",
    "lessons_reference", "dashboard_filter",
}
```

No other changes to validate_content.py.

---

## Phase 2 — tools.py: 10 new tool functions

**File:** `aegis/utils/tools.py`

All functions follow the existing pattern: `def tool_name(challenge_text: str) -> str`.
Use ASCII `->` not Unicode right-arrow in output strings (Windows CP1252 terminal safety).
Add all 10 to `_DISPATCH` at the bottom of the file.
`datetime` is already imported from Stage 3.

---

### Task 02 — vuln_prioritizer

**Purpose:** Score and rank CVEs using CVSS + contextual bonuses.

**Input format:** `challenge_text` split on `"\n"`, skip blank lines. Each line:
```
cve_id|cvss_score|asset_criticality|internet_facing|exploit_available|patch_available
```
Fields 0-5 (0-indexed). `patch_available` is parsed but not used in scoring.

**Scoring:**
```python
score = float(cvss_score)
score += {"critical": 3, "high": 2, "medium": 1, "low": 0}.get(asset_criticality.lower(), 0)
score += 2 if exploit_available.lower() == "yes" else 0
score += 2 if internet_facing.lower() == "yes" else 0
```

Sort entries by score descending. Preserve input order for ties.

**Output format:**
```
VULN PRIORITIZER -- contextual risk scoring

CVEs analyzed: 4

[RANK 1] CVE-2021-44228
  CVSS base score:   10.0
  Asset criticality: critical (+3)
  Exploit available: yes (+2)
  Internet facing:   yes (+2)
  Contextual score -> 17.0

[RANK 2] CVE-2021-34527
  ...
  Contextual score -> 12.8

...

Top priority: CVE-2021-44228 (score: 17.0)
Patch immediately -- highest contextual risk in backlog.
```

**Done-when:** `vuln_prioritizer` called with case22 challenge_data:
- Output contains `"[RANK 1] CVE-2021-44228"`
- Output contains `"Contextual score -> 17.0"`
- Output contains `"[RANK 4] CVE-2023-1234"` (score 9.5, lowest)
- Output contains `"Top priority: CVE-2021-44228"`

---

### Task 03 — patch_reference

**Purpose:** Static patch management reference — challenge_data ignored entirely.

**Implementation:** Single function body, no input parsing.

**Output (hardcoded string):**
```
PATCH REFERENCE -- patch management guide

PATCH INHIBITORS (reasons a patch may not be immediately applicable):
  Business continuity   -- system cannot be taken offline (production critical)
  Operational constraint -- patch breaks dependent functionality
  Legacy dependency     -- incompatible with other installed software
  Vendor limitation     -- vendor has not certified the patch
  Testing requirement   -- enterprise policy requires test validation first

REMEDIATION ALTERNATIVES when patching is blocked:

  Compensating control  -- security measure that reduces exploitation risk
                           without applying the patch directly
                           Examples: disable vulnerable feature, access restriction,
                           enhanced monitoring, rate limiting

  Virtual patching      -- WAF or IPS rule blocks exploitation at network layer
                           without modifying the endpoint

  Network segmentation  -- isolate vulnerable system to reduce attacker reach
                           Firewall rules, VLANs, or micro-segmentation

  Enhanced monitoring   -- alert on exploitation indicators for the CVE
                           (process names, network patterns, file paths)

  Risk acceptance       -- formally document the residual risk with CISO sign-off
                           Requires: justification, compensating controls, review date

PATCH EXCEPTION PROCESS:
  1. Document inhibitor and business justification
  2. Risk assessment (likelihood x impact with compensating controls)
  3. CISO approval and formal sign-off
  4. Implement compensating controls
  5. Set mandatory review date (30/60/90 days)
  6. Track in vulnerability management platform

Key principle: A vulnerability without a patch is still a managed risk.
Risk acceptance requires formal documentation -- not informal agreement.
```

**Done-when:** `patch_reference("")` output contains `"Compensating control"` and `"PATCH INHIBITORS"`.

---

### Task 04 — surface_analyzer

**Purpose:** Flag internet-exposed services with no business justification.

**Input format:** `challenge_text` split on `"\n"`, skip blank lines. Each line:
```
service_name|port|protocol|internet_facing|required|category
```

**Flag logic:**
```python
if internet_facing.lower() == "yes" and required.lower() == "no":
    flag = "[REDUCE]"
else:
    flag = "[OK]"
```

**Output format:** [REDUCE] entries first (preserve input order within each group), then [OK].
```
SURFACE ANALYZER -- attack surface mapping

Services analyzed: 6

[REDUCE] telnet (port 23/tcp)
  Category:       remote_management
  Internet-facing: yes | Required: no
  Action: Remove from internet exposure -- no business justification

[REDUCE] ftp (port 21/tcp)
  ...

[OK] ssh (port 22/tcp)
  Category:       remote_management
  Internet-facing: yes | Required: yes

...

Summary: 4 services flagged for removal ([REDUCE])
         2 services acceptable ([OK])
Attack surface: remove or firewall-restrict all [REDUCE] services.
```

**Done-when:** `surface_analyzer` called with case24 challenge_data:
- Output contains `"[REDUCE] telnet"`, `"[REDUCE] ftp"`, `"[REDUCE] rdp"`, `"[REDUCE] smb"`
- Output contains `"[OK] ssh"`, `"[OK] https"`
- Output contains `"4 services flagged for removal"`
- All [REDUCE] entries appear before all [OK] entries in output

---

### Task 05 — sast_analyzer

**Purpose:** Sort SAST findings by severity; identify top finding by CWE.

**Input format:** `challenge_text` split on `"\n"`, skip blank lines. Each line:
```
filename|line|cwe_id|severity|description
```

**Severity sort key** (higher = more severe):
```python
_SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}
```
Sort by `_SEVERITY_RANK[severity.lower()]` descending. Preserve input order for equal severity.

**Embedded CWE name table** (hardcoded):
```python
_CWE_NAMES = {
    "CWE-89":  "SQL Injection",
    "CWE-79":  "Cross-Site Scripting (XSS)",
    "CWE-22":  "Path Traversal",
    "CWE-78":  "OS Command Injection",
    "CWE-798": "Use of Hard-coded Credentials",
    "CWE-306": "Missing Authentication for Critical Function",
    "CWE-384": "Session Fixation",
    "CWE-532": "Insertion of Sensitive Information into Log File",
    "CWE-502": "Deserialization of Untrusted Data",
    "CWE-476": "NULL Pointer Dereference",
}
```
If CWE ID not in table: use `"Unknown CWE"`.
Normalize CWE ID to uppercase for lookup (e.g. `cwe_id.upper()`).

**Output format:**
```
SAST ANALYZER -- static analysis findings

Findings analyzed: 5

[CRITICAL] auth.py:45 -- CWE-89 (SQL Injection)
  Description: SQL injection via unsanitized user input in login query

[HIGH] config.py:12 -- CWE-798 (Use of Hard-coded Credentials)
  Description: Hardcoded credential: API_KEY set to production secret value

[HIGH] upload.py:78 -- CWE-22 (Path Traversal)
  Description: Path traversal: filename not validated before file write operation

[MEDIUM] session.py:33 -- CWE-384 (Session Fixation)
  Description: Session fixation: session ID not regenerated after successful login

[LOW] logger.py:91 -- CWE-532 (Insertion of Sensitive Information into Log File)
  Description: Sensitive data in logs: password field written to access.log

Top finding: CWE-89 (SQL Injection) in auth.py line 45
Severity: CRITICAL -- remediate immediately.
```

**Done-when:** `sast_analyzer` called with case25 challenge_data:
- Output contains `"[CRITICAL] auth.py:45 -- CWE-89 (SQL Injection)"`
- Output contains `"[HIGH] config.py:12"` before `"[HIGH] upload.py:78"` (input order preserved within HIGH)
- Output contains `"[LOW] logger.py:91"`
- Output contains `"Top finding: CWE-89 (SQL Injection) in auth.py line 45"`
- `"[CRITICAL]"` appears before `"[HIGH]"` in output

---

### Task 06 — intel_correlator

**Purpose:** Assign tier labels to CVEs based on threat intel; rank for remediation.

**Input format:** `challenge_text` split on `"\n"`, skip blank lines. Each line:
```
cve_id|cvss|exploited_in_wild|poc_available|apt_linked
```

**Tier assignment** (first matching rule wins, checked in order):
```python
if exploited_in_wild.lower() == "yes":
    tier = "IMMEDIATE"
elif poc_available.lower() == "yes":
    tier = "ELEVATED"
elif apt_linked.lower() == "yes":
    tier = "MONITOR"
else:
    tier = "ROUTINE"
```

**Tier sort order** (for output): IMMEDIATE first, then ELEVATED, MONITOR, ROUTINE.
Within same tier: sort by `float(cvss)` descending.

**Output format:**
```
INTEL CORRELATOR -- threat-prioritized vulnerability ranking

CVEs analyzed: 4

[IMMEDIATE] CVE-2023-5678 (CVSS: 7.2)
  Exploited in wild: YES | PoC available: YES | APT-linked: YES
  Action: Patch within 24-48 hours -- active exploitation confirmed.

[ELEVATED] CVE-2022-9876 (CVSS: 8.5)
  Exploited in wild: NO | PoC available: YES | APT-linked: NO
  Action: Patch within 7 days -- public exploit code available.

[MONITOR] CVE-2023-1111 (CVSS: 6.8)
  Exploited in wild: NO | PoC available: NO | APT-linked: YES
  Action: Schedule patch -- APT actor interest noted.

[ROUTINE] CVE-2021-0001 (CVSS: 9.0)
  Exploited in wild: NO | PoC available: NO | APT-linked: NO
  Action: Patch by next cycle -- no active exploitation.

Note: CVE-2021-0001 has highest CVSS (9.0) but is [ROUTINE] tier.
Threat intelligence overrides CVSS-only prioritization.
```

**Done-when:** `intel_correlator` called with case26 challenge_data:
- Output contains `"[IMMEDIATE] CVE-2023-5678"`
- Output contains `"[ELEVATED] CVE-2022-9876"`
- Output contains `"[ROUTINE] CVE-2021-0001"`
- `"[IMMEDIATE]"` appears before `"[ELEVATED]"` in output
- Output contains the "highest CVSS" note referencing CVE-2021-0001

---

### Task 07 — metrics_calculator

**Purpose:** Compute MTTD and MTTR averages from incident timestamp data.

**Input format:** `challenge_text` split on `"\n"`, skip blank lines. Each line:
```
incident_id|compromised_at|detected_at|resolved_at
```
Timestamp format: `"%Y-%m-%dT%H:%M:%S"`. Parse with `datetime.datetime.strptime`.

**Per-incident computation:**
```python
mttd_i = (detected_at - compromised_at).total_seconds() / 3600   # hours, float
mttr_i = (resolved_at - detected_at).total_seconds() / 3600      # hours, float
```

**Aggregate:**
```python
MTTD = round(sum(mttd_list) / len(mttd_list))    # nearest integer
MTTR = round(sum(mttr_list) / len(mttr_list))    # nearest integer
```

**Output format:**
```
METRICS CALCULATOR -- security performance metrics

Incidents analyzed: 3

Incident breakdown:
  INC-001:  MTTD = 516.00h | MTTR =  48.00h
  INC-002:  MTTD =   2.00h | MTTR =  24.00h
  INC-003:  MTTD =  48.00h | MTTR =  60.00h

Aggregate metrics:
  Mean Time to Detect (MTTD): 189 hours
  Mean Time to Respond (MTTR):  44 hours

Note: MTTD measures detection effectiveness. Lower -> better.
Note: MTTR measures response effectiveness. Lower -> better.
Note: INC-001 is a significant outlier (516h MTTD) -- skews the average upward.
```

The outlier note: if any single incident's MTTD is > 3× the average MTTD, add the note
identifying that incident_id as an outlier.
For case27: 516 > 3×189 = 567? No — 516 < 567. Include the note anyway for case27
because INC-001 is > 3× the median (median of [516, 2, 48] = 48, 3× = 144, 516 > 144).
**Simpler rule:** if max(mttd_list) > 3 × median(mttd_list): add outlier note for the
incident with the maximum MTTD. Use `sorted(mttd_list)[len//2]` for median.

**Done-when:** `metrics_calculator` called with case27 challenge_data:
- Output contains `"MTTD = 516.00h"` for INC-001
- Output contains `"MTTD =   2.00h"` for INC-002 (or equivalent spacing)
- Output contains `"Mean Time to Detect (MTTD): 189 hours"`
- Output contains `"Mean Time to Respond (MTTR):  44 hours"`

---

### Task 08 — compliance_mapper

**Purpose:** Compute NIST CSF per-function compliance %; identify biggest gap.

**Input format:** `challenge_text` split on `"\n"`, skip blank lines. Each line:
```
control_id|nist_function|implemented
```
`nist_function` is one of: IDENTIFY, PROTECT, DETECT, RESPOND, RECOVER (compare case-insensitively, store as uppercase for output).
`implemented` is "yes" or "no" (compare case-insensitively).

**Computation:**
```python
# Build dict: function -> {"yes": count, "total": count}
# Per function:
pct = round((yes_count / total_count) * 100)
```

**Gap label per function:**
```python
if pct == 100:
    label = "[MET]"
elif pct >= 75:
    label = "[MINOR GAP]"
elif pct >= 50:
    label = "[MODERATE GAP]"
else:
    label = "[CRITICAL GAP]"
```

**Sort** by pct ascending (lowest compliance first = biggest gap at top).

**Output format:**
```
COMPLIANCE MAPPER -- NIST CSF gap analysis

Controls analyzed: 15

NIST CSF compliance by function (largest gap first):

[CRITICAL GAP] RECOVER:   1/ 6 controls implemented (17%)
[MET]          DETECT:    2/ 2 controls implemented (100%)
[MET]          IDENTIFY:  2/ 2 controls implemented (100%)
[MET]          PROTECT:   3/ 3 controls implemented (100%)
[MET]          RESPOND:   2/ 2 controls implemented (100%)

Top priority gap: RECOVER (17%)
Recommended action: Develop recovery plans, document BCP, test annually.
```

For ties in pct: sort alphabetically by function name.

**Done-when:** `compliance_mapper` called with case28 challenge_data:
- Output contains `"RECOVER"` as first function listed
- Output contains `"17%"` next to RECOVER
- Output contains `"[CRITICAL GAP] RECOVER"`
- Output contains `"Top priority gap: RECOVER"`
- Output contains `"15"` (total controls analyzed)

---

### Task 09 — sla_tracker

**Purpose:** Flag SLA breaches, compute adherence rate.

**Input format:** `challenge_text` split on `"\n"`, skip blank lines. Each line:
```
ticket_id|priority|opened_at|resolved_at|sla_hours
```
Timestamp format: `"%Y-%m-%dT%H:%M:%S"`. `sla_hours` is an integer string.

**Per-ticket computation:**
```python
elapsed = (resolved_at - opened_at).total_seconds() / 3600   # float
status = "[MET]" if elapsed <= float(sla_hours) else "[BREACHED]"
```

**Adherence rate:**
```python
adherence = round((met_count / total_count) * 100)
```

**Output format:**
```
SLA TRACKER -- incident response SLA adherence

Tickets analyzed: 6

  TKT-001  CRITICAL    2.0h elapsed /   4h SLA -> [MET]
  TKT-002  HIGH       26.0h elapsed /  24h SLA -> [BREACHED]
  TKT-003  MEDIUM     96.0h elapsed /  72h SLA -> [BREACHED]
  TKT-004  CRITICAL    8.0h elapsed /   4h SLA -> [BREACHED]
  TKT-005  HIGH       20.0h elapsed /  24h SLA -> [MET]
  TKT-006  LOW       240.0h elapsed / 120h SLA -> [BREACHED]

Summary:
  Tickets meeting SLA:    2 / 6
  Tickets breaching SLA:  4 / 6
  SLA adherence rate:     33%
```

Output tickets in input order (no sorting).

**Done-when:** `sla_tracker` called with case29 challenge_data:
- Output contains `"TKT-001"` with `"[MET]"`
- Output contains `"TKT-004"` with `"[BREACHED]"` (critical that missed 4h window)
- Output contains `"TKT-005"` with `"[MET]"`
- Output contains `"SLA adherence rate:     33%"`
- Output contains `"2 / 6"` for meeting SLA

---

### Task 10 — lessons_reference

**Purpose:** Static post-incident lessons learned reference — challenge_data ignored.

**Implementation:** Single function body, no input parsing.

**Output (hardcoded string):**
```
LESSONS REFERENCE -- post-incident lessons learned guide

PRIMARY GOAL: Prevent recurrence through root cause analysis.
  Every section of the lessons learned document serves this goal:
  understand WHY it happened so the same attack cannot succeed again.

ROOT CAUSE CATEGORIES:
  Technical failure   -- security control failed or was misconfigured
  Process gap         -- procedure was missing or not followed
  Human error         -- analyst missed indicator or made configuration mistake
  Detection failure   -- log source missing or detection rule not present
  Response gap        -- slow escalation or communication failure

LESSONS LEARNED DOCUMENT STRUCTURE:
  1. Incident summary      -- what happened, when, scope, impact
  2. Timeline              -- reconstructed from multi-source evidence
  3. Root cause            -- primary cause and contributing factors
  4. What went well        -- preserve effective practices
  5. What failed           -- gaps in detection, response, or controls
  6. Corrective actions    -- specific items with owner and target date
  7. Metrics               -- MTTD, MTTR, containment time, total impact
  8. Approvals             -- IR lead and CISO sign-off required

KEY METRICS REVIEWED:
  MTTD (Mean Time to Detect)    -- detection effectiveness
  MTTR (Mean Time to Respond)   -- response effectiveness
  Containment time              -- time from detection to containment
  Eradication time              -- time to remove all attacker artifacts
  Total dwell time              -- initial access to full containment

DISTRIBUTION:
  IR team, security management, affected business units, legal (if applicable)

Blameless principle: focus on systems and processes, not individuals.
Blame inhibits honest reporting. The goal is improvement, not punishment.
```

**Done-when:** `lessons_reference("")` output contains `"PRIMARY GOAL: Prevent recurrence"` and `"ROOT CAUSE CATEGORIES"`.

---

### Task 11 — dashboard_filter

**Purpose:** Classify metrics as executive-appropriate or operational-only.

**Input format:** `challenge_text` split on `"\n"`, skip blank lines. Each line:
```
metric_name|value
```

**Classification** (check `metric_name.lower()`):
```python
_EXECUTIVE_KEYWORDS = [
    "risk_reduction", "compliance", "critical", "breach", "sla_adherence", "open"
]
_OPERATIONAL_KEYWORDS = [
    "time_to", "alerts_processed", "scan_cycle", "rules_reviewed",
    "tickets_closed", "patched_count"
]

# Check executive keywords first
for kw in _EXECUTIVE_KEYWORDS:
    if kw in metric_name.lower():
        label = "[EXECUTIVE]"
        break
else:
    label = "[OPERATIONAL]"   # default (includes operational keyword matches)
```

**Output order:** all [EXECUTIVE] entries first (preserve input order within group),
then all [OPERATIONAL] entries (preserve input order within group).

**Output format:**
```
DASHBOARD FILTER -- executive vs operational metric classification

Metrics analyzed: 8

[EXECUTIVE] overall_risk_reduction: 23 percent
[EXECUTIVE] patch_compliance_rate: 78 percent
[EXECUTIVE] critical_vulnerabilities_open: 12
[EXECUTIVE] sla_adherence_rate: 33 percent

[OPERATIONAL] mean_time_to_detect: 189 hours
[OPERATIONAL] total_alerts_processed: 1247
[OPERATIONAL] average_scan_cycle_time: 14 days
[OPERATIONAL] firewall_rules_reviewed: 847

Executive dashboard:  4 metrics (outcome-focused -- answers "are we safer?")
Operational dashboard: 4 metrics (process-focused -- answers "how is the team performing?")
```

**Done-when:** `dashboard_filter` called with case31 challenge_data:
- Output contains `"[EXECUTIVE] overall_risk_reduction"`
- Output contains `"[EXECUTIVE] patch_compliance_rate"`
- Output contains `"[EXECUTIVE] critical_vulnerabilities_open"`
- Output contains `"[EXECUTIVE] sla_adherence_rate"`
- Output contains `"[OPERATIONAL] mean_time_to_detect"`
- Output contains `"[OPERATIONAL] total_alerts_processed"`
- All [EXECUTIVE] entries appear before all [OPERATIONAL] entries
- Output contains `"Executive dashboard:  4 metrics"`

---

### Task 12 — _DISPATCH update

**File:** `aegis/utils/tools.py`

Add all 10 new entries to `_DISPATCH` dict at bottom of file:
```python
"vuln_prioritizer":  vuln_prioritizer,
"patch_reference":   patch_reference,
"surface_analyzer":  surface_analyzer,
"sast_analyzer":     sast_analyzer,
"intel_correlator":  intel_correlator,
"metrics_calculator": metrics_calculator,
"compliance_mapper": compliance_mapper,
"sla_tracker":       sla_tracker,
"lessons_reference": lessons_reference,
"dashboard_filter":  dashboard_filter,
```

**Done-when:** `run_tool("vuln_prioritizer", "x")` and `run_tool("dashboard_filter", "x")` do not raise `KeyError`.

---

## Phase 3 — Case JSON files (case22-31)

**File per case:** `aegis/content/cases/caseNN.json`

All cases must pass `validate_content.py`. Required fields (from validator):
`id`, `title`, `track`, `cert_objective`, `xp_base`, `difficulty`, `tools_type`,
`challenge_data`, `scenario`, `challenge`, `valid_answers` (list),
`hints` (list of 4), `tools`, `learn`, `debrief` (object with 5 keys:
`summary`, `real_world`, `next_step`, `cert_link`, `exam_tip`).

All content is fully specified in spec.md Section 5. Copy exactly.

---

### Task 13 — case22.json

**tools_type:** `vuln_prioritizer` | **difficulty:** 3 | **xp_base:** 150
**valid_answers:** `["cve-2021-44228", "log4shell", "log4j"]`

challenge_data (exact, newline-separated):
```
CVE-2021-44228|10.0|critical|yes|yes|yes
CVE-2022-30190|7.8|high|no|yes|yes
CVE-2023-1234|6.5|medium|yes|no|yes
CVE-2021-34527|8.8|high|no|yes|no
```

In JSON: `\n` between lines, no trailing newline.

---

### Task 14 — case23.json

**tools_type:** `patch_reference` | **difficulty:** 3 | **xp_base:** 150
**valid_answers:** `["compensating control", "compensating controls", "virtual patching", "network segmentation"]`

challenge_data: `"CVE-2021-34527"` (ignored by static tool).

---

### Task 15 — case24.json

**tools_type:** `surface_analyzer` | **difficulty:** 4 | **xp_base:** 250
**valid_answers:** `["4", "four"]`

challenge_data (exact, 6 lines):
```
ssh|22|tcp|yes|yes|remote_management
telnet|23|tcp|yes|no|remote_management
ftp|21|tcp|yes|no|file_transfer
https|443|tcp|yes|yes|web_service
rdp|3389|tcp|yes|no|remote_management
smb|445|tcp|yes|no|file_sharing
```

---

### Task 16 — case25.json

**tools_type:** `sast_analyzer` | **difficulty:** 4 | **xp_base:** 250
**valid_answers:** `["cwe-89", "89", "sql injection"]`

challenge_data (exact, 5 lines):
```
auth.py|45|CWE-89|critical|SQL injection via unsanitized user input in login query
config.py|12|CWE-798|high|Hardcoded credential: API_KEY set to production secret value
upload.py|78|CWE-22|high|Path traversal: filename not validated before file write operation
session.py|33|CWE-384|medium|Session fixation: session ID not regenerated after successful login
logger.py|91|CWE-532|low|Sensitive data in logs: password field written to access.log
```

---

### Task 17 — case26.json

**tools_type:** `intel_correlator` | **difficulty:** 3 | **xp_base:** 150
**valid_answers:** `["cve-2023-5678", "2023-5678"]`

challenge_data (exact, 4 lines):
```
CVE-2023-5678|7.2|yes|yes|yes
CVE-2022-9876|8.5|no|yes|no
CVE-2023-1111|6.8|no|no|yes
CVE-2021-0001|9.0|no|no|no
```

---

### Task 18 — case27.json

**tools_type:** `metrics_calculator` | **difficulty:** 3 | **xp_base:** 150
**valid_answers:** `["189", "189 hours"]`

challenge_data (exact, 3 lines):
```
INC-001|2026-03-01T00:00:00|2026-03-22T12:00:00|2026-03-24T12:00:00
INC-002|2026-03-15T10:00:00|2026-03-15T12:00:00|2026-03-16T12:00:00
INC-003|2026-03-28T00:00:00|2026-03-30T00:00:00|2026-04-01T12:00:00
```

---

### Task 19 — case28.json

**tools_type:** `compliance_mapper` | **difficulty:** 4 | **xp_base:** 250
**valid_answers:** `["recover", "recovery"]`

challenge_data (exact, 15 lines):
```
ID-AM-01|IDENTIFY|yes
ID-RA-01|IDENTIFY|yes
PR-AC-01|PROTECT|yes
PR-DS-01|PROTECT|yes
PR-IP-01|PROTECT|yes
DE-AE-01|DETECT|yes
DE-CM-01|DETECT|yes
RS-RP-01|RESPOND|yes
RS-CO-01|RESPOND|yes
RC-RP-01|RECOVER|no
RC-RP-02|RECOVER|no
RC-IM-01|RECOVER|no
RC-IM-02|RECOVER|no
RC-CO-01|RECOVER|no
RC-CO-02|RECOVER|yes
```

---

### Task 20 — case29.json

**tools_type:** `sla_tracker` | **difficulty:** 3 | **xp_base:** 150
**valid_answers:** `["33%", "33", "33 percent"]`

challenge_data (exact, 6 lines):
```
TKT-001|critical|2026-04-01T08:00:00|2026-04-01T10:00:00|4
TKT-002|high|2026-04-02T09:00:00|2026-04-03T11:00:00|24
TKT-003|medium|2026-04-03T14:00:00|2026-04-07T14:00:00|72
TKT-004|critical|2026-04-05T22:00:00|2026-04-06T06:00:00|4
TKT-005|high|2026-04-08T10:00:00|2026-04-09T06:00:00|24
TKT-006|low|2026-04-10T11:00:00|2026-04-20T11:00:00|120
```

---

### Task 21 — case30.json

**tools_type:** `lessons_reference` | **difficulty:** 3 | **xp_base:** 150
**valid_answers:** `["prevent recurrence", "prevention", "identify root cause", "root cause analysis"]`

challenge_data: `"NIGHTWIRE"` (ignored by static tool).

---

### Task 22 — case31.json

**tools_type:** `dashboard_filter` | **difficulty:** 4 | **xp_base:** 250
**valid_answers:** `["4", "four"]`

challenge_data (exact, 8 lines):
```
mean_time_to_detect|189 hours
overall_risk_reduction|23 percent
patch_compliance_rate|78 percent
total_alerts_processed|1247
critical_vulnerabilities_open|12
average_scan_cycle_time|14 days
sla_adherence_rate|33 percent
firewall_rules_reviewed|847
```

---

## Phase 4 — registry.json update

### Task 23 — Extend registry.json with case22-31

**File:** `aegis/content/registry.json`

Append 10 entries to the existing array (after case21):
```json
{"id": "case22", "title": "Vuln Triage",       "difficulty": 3, "domain": 2},
{"id": "case23", "title": "Patch Inhibitors",   "difficulty": 3, "domain": 2},
{"id": "case24", "title": "Attack Surface",     "difficulty": 4, "domain": 2},
{"id": "case25", "title": "Code Review",        "difficulty": 4, "domain": 2},
{"id": "case26", "title": "Threat Intel Vulns", "difficulty": 3, "domain": 2},
{"id": "case27", "title": "Security Metrics",   "difficulty": 3, "domain": 4},
{"id": "case28", "title": "Compliance Gap",     "difficulty": 4, "domain": 4},
{"id": "case29", "title": "SLA Tracking",       "difficulty": 3, "domain": 4},
{"id": "case30", "title": "Lessons Learned",    "difficulty": 3, "domain": 4},
{"id": "case31", "title": "Executive Report",   "difficulty": 4, "domain": 4}
```

**Done-when:** registry.json has exactly 31 entries; `validate_content.py` loads all 31 without error.

---

## Phase 5 — Unit tests (test_tools_stage4.py)

**File:** `aegis/tests/test_tools_stage4.py`

**Target:** 40 tests across 8 test classes (one per dynamic tool).
All existing 82 tests must still pass after adding Stage 4 tools.

Import pattern (same as test_tools_stage3.py):
```python
import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from aegis.utils.tools import (
    vuln_prioritizer, surface_analyzer, sast_analyzer,
    intel_correlator, metrics_calculator, compliance_mapper,
    sla_tracker, dashboard_filter
)
```

---

### Task 24 — TestVulnPrioritizer (5 tests)

```python
CASE22_DATA = (
    "CVE-2021-44228|10.0|critical|yes|yes|yes\n"
    "CVE-2022-30190|7.8|high|no|yes|yes\n"
    "CVE-2023-1234|6.5|medium|yes|no|yes\n"
    "CVE-2021-34527|8.8|high|no|yes|no"
)

class TestVulnPrioritizer(unittest.TestCase):

    def test_top_priority_is_log4shell(self):
        result = vuln_prioritizer(CASE22_DATA)
        self.assertIn("[RANK 1] CVE-2021-44228", result)

    def test_log4shell_score_17(self):
        result = vuln_prioritizer(CASE22_DATA)
        self.assertIn("17.0", result)

    def test_lowest_priority_is_cve_2023_1234(self):
        result = vuln_prioritizer(CASE22_DATA)
        self.assertIn("[RANK 4] CVE-2023-1234", result)

    def test_rank_order_correct(self):
        result = vuln_prioritizer(CASE22_DATA)
        pos1 = result.index("[RANK 1]")
        pos2 = result.index("[RANK 2]")
        pos3 = result.index("[RANK 3]")
        pos4 = result.index("[RANK 4]")
        self.assertLess(pos1, pos2)
        self.assertLess(pos2, pos3)
        self.assertLess(pos3, pos4)

    def test_no_internet_no_bonus(self):
        # CVE-2022-30190 internet_facing=no -> score 7.8+2+2+0 = 11.8
        result = vuln_prioritizer(CASE22_DATA)
        self.assertIn("11.8", result)
```

---

### Task 25 — TestSurfaceAnalyzer (5 tests)

```python
CASE24_DATA = (
    "ssh|22|tcp|yes|yes|remote_management\n"
    "telnet|23|tcp|yes|no|remote_management\n"
    "ftp|21|tcp|yes|no|file_transfer\n"
    "https|443|tcp|yes|yes|web_service\n"
    "rdp|3389|tcp|yes|no|remote_management\n"
    "smb|445|tcp|yes|no|file_sharing"
)

class TestSurfaceAnalyzer(unittest.TestCase):

    def test_four_reduce_services(self):
        result = surface_analyzer(CASE24_DATA)
        self.assertIn("4 services flagged", result)

    def test_reduce_flags_correct(self):
        result = surface_analyzer(CASE24_DATA)
        self.assertIn("[REDUCE] telnet", result)
        self.assertIn("[REDUCE] ftp", result)
        self.assertIn("[REDUCE] rdp", result)
        self.assertIn("[REDUCE] smb", result)

    def test_ok_flags_correct(self):
        result = surface_analyzer(CASE24_DATA)
        self.assertIn("[OK] ssh", result)
        self.assertIn("[OK] https", result)

    def test_reduce_before_ok_in_output(self):
        result = surface_analyzer(CASE24_DATA)
        first_reduce = result.index("[REDUCE]")
        first_ok = result.index("[OK]")
        self.assertLess(first_reduce, first_ok)

    def test_required_yes_never_reduce(self):
        data = "webapp|443|tcp|yes|yes|web_service"
        result = surface_analyzer(data)
        self.assertIn("[OK]", result)
        self.assertNotIn("[REDUCE]", result)
```

---

### Task 26 — TestSastAnalyzer (5 tests)

```python
CASE25_DATA = (
    "auth.py|45|CWE-89|critical|SQL injection via unsanitized user input in login query\n"
    "config.py|12|CWE-798|high|Hardcoded credential: API_KEY set to production secret value\n"
    "upload.py|78|CWE-22|high|Path traversal: filename not validated before file write operation\n"
    "session.py|33|CWE-384|medium|Session fixation: session ID not regenerated after successful login\n"
    "logger.py|91|CWE-532|low|Sensitive data in logs: password field written to access.log"
)

class TestSastAnalyzer(unittest.TestCase):

    def test_top_finding_is_cwe89(self):
        result = sast_analyzer(CASE25_DATA)
        self.assertIn("Top finding: CWE-89", result)

    def test_critical_before_high(self):
        result = sast_analyzer(CASE25_DATA)
        self.assertLess(result.index("[CRITICAL]"), result.index("[HIGH]"))

    def test_high_before_medium(self):
        result = sast_analyzer(CASE25_DATA)
        self.assertLess(result.index("[HIGH]"), result.index("[MEDIUM]"))

    def test_medium_before_low(self):
        result = sast_analyzer(CASE25_DATA)
        self.assertLess(result.index("[MEDIUM]"), result.index("[LOW]"))

    def test_cwe_name_resolved(self):
        result = sast_analyzer(CASE25_DATA)
        self.assertIn("SQL Injection", result)
        self.assertIn("Use of Hard-coded Credentials", result)
```

---

### Task 27 — TestIntelCorrelator (5 tests)

```python
CASE26_DATA = (
    "CVE-2023-5678|7.2|yes|yes|yes\n"
    "CVE-2022-9876|8.5|no|yes|no\n"
    "CVE-2023-1111|6.8|no|no|yes\n"
    "CVE-2021-0001|9.0|no|no|no"
)

class TestIntelCorrelator(unittest.TestCase):

    def test_exploited_wild_gets_immediate(self):
        result = intel_correlator(CASE26_DATA)
        self.assertIn("[IMMEDIATE] CVE-2023-5678", result)

    def test_poc_only_gets_elevated(self):
        result = intel_correlator(CASE26_DATA)
        self.assertIn("[ELEVATED] CVE-2022-9876", result)

    def test_apt_only_gets_monitor(self):
        result = intel_correlator(CASE26_DATA)
        self.assertIn("[MONITOR] CVE-2023-1111", result)

    def test_high_cvss_no_intel_gets_routine(self):
        result = intel_correlator(CASE26_DATA)
        self.assertIn("[ROUTINE] CVE-2021-0001", result)

    def test_immediate_before_routine_in_output(self):
        result = intel_correlator(CASE26_DATA)
        self.assertLess(
            result.index("[IMMEDIATE]"),
            result.index("[ROUTINE]")
        )
```

---

### Task 28 — TestMetricsCalculator (5 tests)

```python
CASE27_DATA = (
    "INC-001|2026-03-01T00:00:00|2026-03-22T12:00:00|2026-03-24T12:00:00\n"
    "INC-002|2026-03-15T10:00:00|2026-03-15T12:00:00|2026-03-16T12:00:00\n"
    "INC-003|2026-03-28T00:00:00|2026-03-30T00:00:00|2026-04-01T12:00:00"
)

class TestMetricsCalculator(unittest.TestCase):

    def test_mttd_189(self):
        result = metrics_calculator(CASE27_DATA)
        self.assertIn("189 hours", result)

    def test_mttr_44(self):
        result = metrics_calculator(CASE27_DATA)
        self.assertIn("44 hours", result)

    def test_inc001_mttd_516(self):
        result = metrics_calculator(CASE27_DATA)
        self.assertIn("516.00h", result)

    def test_inc002_mttd_2(self):
        result = metrics_calculator(CASE27_DATA)
        self.assertIn("2.00h", result)

    def test_single_incident_mttd(self):
        data = "INC-X|2026-01-01T00:00:00|2026-01-03T00:00:00|2026-01-04T00:00:00"
        result = metrics_calculator(data)
        self.assertIn("48 hours", result)  # MTTD = 48h, MTTR = 24h
```

---

### Task 29 — TestComplianceMapper (5 tests)

```python
CASE28_DATA = (
    "ID-AM-01|IDENTIFY|yes\n"
    "ID-RA-01|IDENTIFY|yes\n"
    "PR-AC-01|PROTECT|yes\n"
    "PR-DS-01|PROTECT|yes\n"
    "PR-IP-01|PROTECT|yes\n"
    "DE-AE-01|DETECT|yes\n"
    "DE-CM-01|DETECT|yes\n"
    "RS-RP-01|RESPOND|yes\n"
    "RS-CO-01|RESPOND|yes\n"
    "RC-RP-01|RECOVER|no\n"
    "RC-RP-02|RECOVER|no\n"
    "RC-IM-01|RECOVER|no\n"
    "RC-IM-02|RECOVER|no\n"
    "RC-CO-01|RECOVER|no\n"
    "RC-CO-02|RECOVER|yes"
)

class TestComplianceMapper(unittest.TestCase):

    def test_recover_lowest(self):
        result = compliance_mapper(CASE28_DATA)
        self.assertIn("17%", result)

    def test_recover_is_top_gap(self):
        result = compliance_mapper(CASE28_DATA)
        self.assertIn("Top priority gap: RECOVER", result)

    def test_recover_critical_gap_label(self):
        result = compliance_mapper(CASE28_DATA)
        self.assertIn("[CRITICAL GAP] RECOVER", result)

    def test_identify_100_percent(self):
        result = compliance_mapper(CASE28_DATA)
        self.assertIn("100%", result)

    def test_recover_appears_first(self):
        result = compliance_mapper(CASE28_DATA)
        pos_recover = result.index("RECOVER")
        pos_identify = result.index("IDENTIFY")
        self.assertLess(pos_recover, pos_identify)
```

---

### Task 30 — TestSlaTracker (5 tests)

```python
CASE29_DATA = (
    "TKT-001|critical|2026-04-01T08:00:00|2026-04-01T10:00:00|4\n"
    "TKT-002|high|2026-04-02T09:00:00|2026-04-03T11:00:00|24\n"
    "TKT-003|medium|2026-04-03T14:00:00|2026-04-07T14:00:00|72\n"
    "TKT-004|critical|2026-04-05T22:00:00|2026-04-06T06:00:00|4\n"
    "TKT-005|high|2026-04-08T10:00:00|2026-04-09T06:00:00|24\n"
    "TKT-006|low|2026-04-10T11:00:00|2026-04-20T11:00:00|120"
)

class TestSlaTracker(unittest.TestCase):

    def test_adherence_rate_33(self):
        result = sla_tracker(CASE29_DATA)
        self.assertIn("33%", result)

    def test_tkt001_met(self):
        result = sla_tracker(CASE29_DATA)
        idx = result.index("TKT-001")
        snippet = result[idx:idx+60]
        self.assertIn("[MET]", snippet)

    def test_tkt004_breached(self):
        result = sla_tracker(CASE29_DATA)
        idx = result.index("TKT-004")
        snippet = result[idx:idx+60]
        self.assertIn("[BREACHED]", snippet)

    def test_tkt005_met(self):
        result = sla_tracker(CASE29_DATA)
        idx = result.index("TKT-005")
        snippet = result[idx:idx+60]
        self.assertIn("[MET]", snippet)

    def test_exact_sla_is_met(self):
        # elapsed == sla_hours -> MET (inclusive boundary)
        data = "TKT-X|high|2026-01-01T00:00:00|2026-01-02T00:00:00|24"
        result = sla_tracker(data)
        self.assertIn("[MET]", result)
```

---

### Task 31 — TestDashboardFilter (5 tests)

```python
CASE31_DATA = (
    "mean_time_to_detect|189 hours\n"
    "overall_risk_reduction|23 percent\n"
    "patch_compliance_rate|78 percent\n"
    "total_alerts_processed|1247\n"
    "critical_vulnerabilities_open|12\n"
    "average_scan_cycle_time|14 days\n"
    "sla_adherence_rate|33 percent\n"
    "firewall_rules_reviewed|847"
)

class TestDashboardFilter(unittest.TestCase):

    def test_four_executive_metrics(self):
        result = dashboard_filter(CASE31_DATA)
        self.assertIn("Executive dashboard:  4 metrics", result)

    def test_executive_metrics_correct(self):
        result = dashboard_filter(CASE31_DATA)
        self.assertIn("[EXECUTIVE] overall_risk_reduction", result)
        self.assertIn("[EXECUTIVE] patch_compliance_rate", result)
        self.assertIn("[EXECUTIVE] critical_vulnerabilities_open", result)
        self.assertIn("[EXECUTIVE] sla_adherence_rate", result)

    def test_operational_metrics_correct(self):
        result = dashboard_filter(CASE31_DATA)
        self.assertIn("[OPERATIONAL] mean_time_to_detect", result)
        self.assertIn("[OPERATIONAL] total_alerts_processed", result)

    def test_executive_before_operational_in_output(self):
        result = dashboard_filter(CASE31_DATA)
        first_exec = result.index("[EXECUTIVE]")
        first_oper = result.index("[OPERATIONAL]")
        self.assertLess(first_exec, first_oper)

    def test_single_executive_metric(self):
        data = "overall_risk_reduction|15 percent"
        result = dashboard_filter(data)
        self.assertIn("[EXECUTIVE]", result)
        self.assertNotIn("[OPERATIONAL]", result)
```

---

## Phase 6 — Smoke test

### Task 32 — Run full test suite

```bash
cd aegis
python -m pytest tests/ -v
```

**Expected:** 122 tests passing (82 existing + 40 new).
If any test fails: fix before proceeding.

### Task 33 — Run validate_content.py on all 31 cases

```bash
cd aegis
python validate_content.py
```

**Expected:** `All N cases valid.` with no errors.

### Task 34 — Run check_imports.py

```bash
cd aegis
python check_imports.py
```

**Expected:** No import errors on any file.

---

## Summary

| Phase | Tasks | Deliverable |
|-------|-------|-------------|
| 1 | 01 | validate_content.py — 10 new tools_type values |
| 2 | 02-12 | tools.py — 10 new functions + dispatch |
| 3 | 13-22 | case22-31.json — 10 case files |
| 4 | 23 | registry.json — extended to 31 entries |
| 5 | 24-31 | test_tools_stage4.py — 40 unit tests |
| 6 | 32-34 | Smoke tests pass (122 total, all 31 cases valid) |

**Total tasks: 34**
**New tests: 40 (122 total after Stage 4)**
**XP added: 1900 (six diff-3 × 150 = 900 + four diff-4 × 250 = 1000)**
