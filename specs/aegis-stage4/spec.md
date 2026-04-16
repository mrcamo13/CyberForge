# spec.md — AEGIS Stage 4: Cases 22-31
<!--
SCOPE: 10 new cases + 10 new tool functions (8 dynamic + 2 static). Zero engine changes.
NOT HERE: AEGIS Stage 5+ → future spec
NOT HERE: Any CIPHER changes
-->

**Module:** aegis-stage4
**Date:** 2026-04-15
**Status:** Draft
**Depends on:** aegis-stage3 (full engine, cases 01-21)
**Modifies DATA_MODEL.md:** No
**Modifies CONSTITUTION.md:** No

---

## 1. Purpose & Scope

### What problem does this module solve?
Stages 1-3 left Domain 2 (Vulnerability Management, 22%) and Domain 4 (Reporting &
Communication, 23%) underrepresented — only 6 combined cases across both domains.
Stage 4 adds 10 cases specifically targeting unmet objectives in Domains 2 and 4,
bringing the simulator to near-complete CySA+ CS0-003 coverage (all 4 domains, 31
total cases).

### What does this module do?
Adds 10 cases (case22-31) and 10 new tool functions (8 dynamic + 2 static). All
changes are additive — no existing engine files modified. Story arc: Operation
IRONCLAD, 4 weeks after Project MERIDIAN closed.

### Success Criteria
- [ ] All 10 new cases visible and playable in case menu after case21
- [ ] All 8 new dynamic tool functions return correct output from parsed input
- [ ] At least one deterministic unit test per new dynamic tool function
- [ ] `validate_content.py` passes on all 31 cases (case01-31)
- [ ] `check_imports.py` passes on all files
- [ ] All existing unit tests still pass

### In Scope
- [ ] aegis/content/cases/case22-31.json — ten case content files
- [ ] aegis/utils/tools.py — add 10 tool functions + dispatch entries
- [ ] aegis/validate_content.py — add 10 new tools_type values to allowlist
- [ ] aegis/content/registry.json — add case22-31 entries in order
- [ ] aegis/tests/test_tools_stage4.py — unit tests for all 8 new dynamic tools

### Out of Scope
- ❌ Engine changes (case_runner.py, main.py, save_manager.py — unchanged)
- ❌ AEGIS Stage 5+ → future
- ❌ Any CIPHER changes
- ❌ Domain 1 or Domain 3 additions (covered in Stages 1-3)

---

## 2. Business Rules

All rules from aegis-stage1 spec apply. No new rules.

---

## 3. Data Model

### New tools_type Allowlist Additions (AEGIS Stage 4)

| tools_type | Tool | Used in |
|-----------|------|---------|
| `vuln_prioritizer` | Score and rank CVEs using CVSS + contextual factors | case22 |
| `patch_reference` | Static patch management reference (inhibitors, compensating controls) | case23 |
| `surface_analyzer` | Flag unnecessary internet-exposed services by attack surface | case24 |
| `sast_analyzer` | Parse SAST output, classify by severity and CWE, identify top finding | case25 |
| `intel_correlator` | Match CVEs against threat intel, reprioritize remediation order | case26 |
| `metrics_calculator` | Compute MTTD and MTTR from incident timestamp data | case27 |
| `compliance_mapper` | Map controls to NIST CSF functions, compute gap percentage | case28 |
| `sla_tracker` | Flag SLA breaches, compute adherence rate from ticket timestamps | case29 |
| `lessons_reference` | Static post-incident lessons learned reference | case30 |
| `dashboard_filter` | Classify metrics as executive-appropriate or operational-only | case31 |

Updated tools_type allowlist for Stage 4 validate_content.py:
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

**Routing rule:**
- case23 uses `tools_type: "patch_reference"` — static reference, challenge_data ignored.
- case30 uses `tools_type: "lessons_reference"` — static reference, challenge_data ignored.
- All other Stage 4 cases use dynamic tools that parse challenge_data.

### challenge_data formats by case

| Case | challenge_data format |
|------|-----------------------|
| case22 | Newline-separated CVE entries: `cve_id\|cvss_score\|asset_criticality\|internet_facing\|exploit_available\|patch_available` |
| case23 | Any string — ignored by patch_reference |
| case24 | Newline-separated service entries: `service_name\|port\|protocol\|internet_facing\|required\|category` |
| case25 | Newline-separated SAST finding entries: `filename\|line\|cwe_id\|severity\|description` |
| case26 | Newline-separated CVE intel entries: `cve_id\|cvss\|exploited_in_wild\|poc_available\|apt_linked` |
| case27 | Newline-separated incident records: `incident_id\|compromised_at\|detected_at\|resolved_at` |
| case28 | Newline-separated control entries: `control_id\|nist_function\|implemented` |
| case29 | Newline-separated ticket entries: `ticket_id\|priority\|opened_at\|resolved_at\|sla_hours` |
| case30 | Any string — ignored by lessons_reference |
| case31 | Newline-separated metric entries: `metric_name\|value` |

### Tool parsing contracts

**vuln_prioritizer:** Split challenge_data on `\n`, skip blank lines. Parse each line
as 6 pipe-separated fields: `cve_id|cvss_score|asset_criticality|internet_facing|exploit_available|patch_available`
Scoring formula:
  - score = CVSS (float) + asset_bonus + exploit_bonus + internet_bonus
  - asset_bonus: critical → +3, high → +2, medium → +1, low → +0
  - exploit_bonus: exploit_available=yes → +2, no → +0
  - internet_bonus: internet_facing=yes → +2, no → +0
Sort by score descending. Output: ranked list with CVE, score breakdown, and total.
Highest score = top priority recommendation.

**patch_reference:** Fully static — challenge_data ignored entirely.
Output: hardcoded patch management reference covering:
  - Patch inhibitors: business continuity, operational constraints, legacy dependencies,
    vendor support limitations, testing requirements
  - Remediation alternatives: compensating controls, virtual patching, network
    segmentation, enhanced monitoring, risk acceptance with documentation
  - Patch exception process: risk assessment, CISO approval, compensating controls,
    scheduled review date, documentation requirements

**surface_analyzer:** Split challenge_data on `\n`, skip blank lines. Parse each line
as 6 pipe-separated fields: `service_name|port|protocol|internet_facing|required|category`
Flag logic:
  - `[REDUCE]` if internet_facing=yes AND required=no (unnecessary exposure)
  - `[OK]` otherwise
Count [REDUCE] services. Sort output: [REDUCE] first, then [OK].
Output: flagged service list, count of unnecessary exposures, attack surface summary.

**sast_analyzer:** Split challenge_data on `\n`, skip blank lines. Parse each line
as 5 pipe-separated fields: `filename|line|cwe_id|severity|description`
Severity order (descending): critical > high > medium > low
Sort findings by severity descending. Within same severity: preserve input order.
Output: sorted findings list with [CRITICAL]/[HIGH]/[MEDIUM]/[LOW] label. Summary
section identifying the top finding (first entry in sorted list) by CWE ID and name.

Embedded CWE reference (hardcoded, ~10 entries):
```
CWE-89   → SQL Injection
CWE-79   → Cross-Site Scripting (XSS)
CWE-22   → Path Traversal
CWE-78   → OS Command Injection
CWE-798  → Use of Hard-coded Credentials
CWE-306  → Missing Authentication for Critical Function
CWE-384  → Session Fixation
CWE-532  → Insertion of Sensitive Information into Log File
CWE-502  → Deserialization of Untrusted Data
CWE-476  → NULL Pointer Dereference
```

**intel_correlator:** Split challenge_data on `\n`, skip blank lines. Parse each line
as 5 pipe-separated fields: `cve_id|cvss|exploited_in_wild|poc_available|apt_linked`
Priority tiers (apply in order — first matching tier wins):
  - `[IMMEDIATE]` if exploited_in_wild=yes (actively exploited — patch now)
  - `[ELEVATED]` if poc_available=yes (exploit code public — patch soon)
  - `[MONITOR]` if apt_linked=yes (threat actor interest — schedule patch)
  - `[ROUTINE]` otherwise
Within same tier: sort by CVSS descending (tie-break: higher CVSS = higher priority).
Output: ranked remediation list with tier label, CVE, CVSS, and rationale.

**metrics_calculator:** Split challenge_data on `\n`, skip blank lines. Parse each line
as 4 pipe-separated fields: `incident_id|compromised_at|detected_at|resolved_at`
Timestamps are ISO format strings (YYYY-MM-DDTHH:MM:SS). Parse with datetime.strptime.
Per-incident calculations:
  - MTTD_i = hours from compromised_at to detected_at (float, rounded to 2 decimal places)
  - MTTR_i = hours from detected_at to resolved_at (float, rounded to 2 decimal places)
Aggregate:
  - MTTD = average of all MTTD_i values, rounded to nearest integer
  - MTTR = average of all MTTR_i values, rounded to nearest integer
Output: per-incident table (incident ID, MTTD hours, MTTR hours), then aggregate
MTTD and MTTR. Note: lower MTTD = faster detection = better security posture.

**compliance_mapper:** Split challenge_data on `\n`, skip blank lines. Parse each line
as 3 pipe-separated fields: `control_id|nist_function|implemented`
Valid nist_function values: IDENTIFY, PROTECT, DETECT, RESPOND, RECOVER (case-insensitive).
For each function: count implemented=yes controls / total controls for that function.
Compliance percentage per function = (implemented / total) × 100, rounded to nearest integer.
Sort functions by compliance percentage ascending (biggest gap first).
Output: per-function compliance table, lowest-compliance function identified as
top priority gap. Summary: overall gap (lowest-scoring function name).

**sla_tracker:** Split challenge_data on `\n`, skip blank lines. Parse each line
as 5 pipe-separated fields: `ticket_id|priority|opened_at|resolved_at|sla_hours`
Timestamps are ISO format strings (YYYY-MM-DDTHH:MM:SS). Parse with datetime.strptime.
Per-ticket:
  - elapsed_hours = hours from opened_at to resolved_at (float)
  - Status: `[MET]` if elapsed_hours <= sla_hours, else `[BREACHED]`
Adherence rate = (MET count / total count) × 100, rounded to nearest integer.
Output: per-ticket table (ticket ID, priority, elapsed hours, SLA hours, status).
Summary: total tickets, MET count, BREACHED count, adherence rate percentage.

**dashboard_filter:** Split challenge_data on `\n`, skip blank lines. Parse each line
as 2 pipe-separated fields: `metric_name|value`
Classification rules (check metric_name, lowercased):
  - `[EXECUTIVE]` if metric_name contains any of: risk_reduction, compliance, critical,
    breach, sla_adherence, open (outcome-focused — tells the story of risk posture)
  - `[OPERATIONAL]` if metric_name contains any of: time_to, alerts_processed,
    scan_cycle, rules_reviewed, tickets_closed, patched_count (process-focused —
    used by security team for operational decisions)
  - `[OPERATIONAL]` if no match (default to operational)
Sort: [EXECUTIVE] metrics first, then [OPERATIONAL].
Output: classified metric list with label. Count of executive vs operational metrics.

**lessons_reference:** Fully static — challenge_data ignored entirely.
Output: hardcoded post-incident lessons learned reference covering:
  - Primary goal: prevent recurrence through root cause analysis
  - Root cause categories: technical failure, process gap, human error,
    detection failure, response gap
  - Lessons learned document structure: incident summary, timeline, root cause,
    contributing factors, corrective actions, owner, target date
  - Key metrics reviewed: MTTD, MTTR, containment time, eradication time
  - Distribution: IR team, management, affected business units, security team

---

## 4. Technical Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| vuln_prioritizer scoring | CVSS + asset/exploit/internet bonuses (no patch bonus) | Patch availability affects urgency but CVSS already models exploitability; keeps scoring simple and deterministic |
| intel_correlator priority | Tier-based (exploited > PoC > APT) with CVSS tie-break | Reflects real-world triage: active exploitation beats theoretical risk |
| compliance_mapper framework | NIST CSF (Identify/Protect/Detect/Respond/Recover) | Most common on CySA+ exam; maps directly to 4.1 objectives |
| dashboard_filter classification | Outcome-focused = executive; process-focused = operational | Outcome metrics answer "are we safer?"; process metrics answer "how is the team performing?" |
| metrics_calculator rounding | Per-incident MTTD/MTTR to 2 dp; aggregate to nearest integer | Precision in intermediate steps; clean integer for answer matching |
| sla_tracker adherence | elapsed <= sla_hours → MET (inclusive) | SLA met exactly on time counts as compliant |
| patch_reference | Static | Patch inhibitors are reference knowledge, not computed |
| lessons_reference | Static | Post-incident structure is procedural knowledge, not computed |

---

## 5. Content — Cases 22-31

---

### Case 22 — Vuln Triage

**id:** case22
**title:** Vuln Triage
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 2 — Vulnerability Management
**xp_base:** 150
**difficulty:** 3
**tools_type:** vuln_prioritizer

#### challenge_data
```
CVE-2021-44228|10.0|critical|yes|yes|yes
CVE-2022-30190|7.8|high|no|yes|yes
CVE-2023-1234|6.5|medium|yes|no|yes
CVE-2021-34527|8.8|high|no|yes|no
```

#### Scoring walkthrough
| CVE | CVSS | Asset | Exploit | Internet | Total |
|-----|------|-------|---------|----------|-------|
| CVE-2021-44228 (Log4Shell) | 10.0 | +3 (critical) | +2 (yes) | +2 (yes) | **17.0** |
| CVE-2021-34527 (PrintNightmare) | 8.8 | +2 (high) | +2 (yes) | +0 (no) | **12.8** |
| CVE-2022-30190 (Follina) | 7.8 | +2 (high) | +2 (yes) | +0 (no) | **11.8** |
| CVE-2023-1234 | 6.5 | +1 (medium) | +0 (no) | +2 (yes) | **9.5** |

**challenge:** Which CVE should be patched first based on contextual risk scoring?

**valid_answers:** `["cve-2021-44228", "log4shell", "log4j"]`

#### Scenario
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — VULNERABILITY MANAGEMENT TEAM
PRIORITY: HIGH
ANALYST: YOU

OPERATION IRONCLAD — WEEK 1

Four weeks after NIGHTWIRE was contained, the CISO has launched Operation
IRONCLAD. Your first task: prioritize the vulnerability backlog using a
contextual risk model — not just CVSS scores.

VULNERABILITY BACKLOG (4 CVEs pending remediation):

  CVE-2021-44228  CVSS 10.0  asset:critical  internet:yes  exploit:yes
    Log4j Remote Code Execution — affects logging library used in
    Veridian's customer portal and internal ticketing system

  CVE-2022-30190  CVSS 7.8   asset:high      internet:no   exploit:yes
    Microsoft Follina (MSDT) — RCE via Office documents,
    affects all Windows workstations

  CVE-2023-1234   CVSS 6.5   asset:medium    internet:yes  exploit:no
    Web framework XSS — affects internal reporting dashboard,
    no public exploit available

  CVE-2021-34527  CVSS 8.8   asset:high      internet:no   exploit:yes
    PrintNightmare — Windows Print Spooler privilege escalation,
    patch creates printer compatibility issues

Contextual scoring: CVSS + asset criticality + exploit availability +
internet exposure. Type 'tools' to run the prioritizer.

Which CVE has the highest contextual risk score and should be patched first?
```

#### Hints
1. `Go to https://www.first.org/cvss/v3.1/specification-document\n        Read about CVSS scoring. CVSS alone doesn't capture business context.\n        A CVSS 6.5 on an internet-facing critical asset may be more urgent\n        than a CVSS 9.0 on an isolated internal server.`
2. `The contextual scoring formula adds bonuses to the base CVSS score:\n        - Asset criticality: critical=+3, high=+2, medium=+1, low=+0\n        - Exploit available: +2 if yes\n        - Internet facing: +2 if yes\n        Type 'tools' to compute the scores for all four CVEs.`
3. `Type 'tools' in the game. The prioritizer computes the full contextual score\n        for each CVE and ranks them highest to lowest.\n        The CVE with the highest total score is your top priority.`
4. `SPOILER — CVE-2021-44228 (Log4Shell) scores 17.0:\n        CVSS 10.0 + asset critical (+3) + exploit yes (+2) + internet yes (+2) = 17.0\n        Despite PrintNightmare having a high CVSS (8.8), it scores only 12.8\n        because it is not internet-facing. Context changes everything.\n        Type: cve-2021-44228`

#### Tools description
Scores each CVE using CVSS plus contextual bonuses (asset criticality, exploit availability, internet exposure) and ranks them highest to lowest priority.

#### Learn
```
Vulnerability prioritization is one of the most important — and most misunderstood —
skills in vulnerability management. Raw CVSS scores alone are insufficient for
triage. A CVSS 10.0 on an isolated test server may be less urgent than a CVSS 6.5
on a critical internet-facing system.

Contextual risk scoring adds business context to technical severity:

Asset criticality:
  What is the impact if this asset is compromised?
  Critical assets (domain controllers, customer DBs) need faster patching.
  Lower-criticality assets (dev boxes, test servers) can wait longer.

Exploit availability:
  Is working exploit code publicly available?
  Published exploits dramatically increase the likelihood of attack.
  "No known exploit" lowers urgency (but doesn't eliminate risk).

Internet exposure:
  Is the vulnerable service reachable from the internet?
  Internet-facing assets have a much larger attacker pool.
  Internal-only assets require the attacker to already be inside.

CVSS sub-scores to understand:
  Attack Vector (AV): Network = higher risk than Local
  Attack Complexity (AC): Low = easier to exploit
  Privileges Required (PR): None = no account needed
  User Interaction (UI): None = fully automated exploit possible
  CVSS temporal score: adjusts for exploit maturity and remediation availability

Real-world prioritization frameworks:
  SSVC (Stakeholder-Specific Vulnerability Categorization) — CISA recommended
  EPSS (Exploit Prediction Scoring System) — probability of exploitation in 30 days
  CVSS + Business Impact = Risk-Based Vulnerability Management (RBVM)

Key principle: Patch what the attacker can reach and exploit today, not just what
scores highest on paper.
```

#### Debrief
```json
{
  "summary": "CVE-2021-44228 (Log4Shell) scores 17.0 — the highest in the backlog — because it combines maximum CVSS (10.0) with a critical asset, a public exploit, and internet exposure. PrintNightmare scores 12.8 despite a high CVSS because it is not internet-facing. Contextual scoring captures what pure CVSS cannot: the real-world likelihood and impact of exploitation.",
  "real_world": "CISA's Known Exploited Vulnerabilities (KEV) catalog operationalizes this concept — it mandates federal agencies patch actively exploited CVEs regardless of CVSS score. Log4Shell (CVE-2021-44228) was one of the most widely exploited CVEs ever, affecting millions of systems globally within days of disclosure in December 2021.",
  "next_step": "Explore the CISA KEV catalog: https://www.cisa.gov/known-exploited-vulnerabilities-catalog\nAnd EPSS scoring: https://www.first.org/epss/",
  "cert_link": "CySA+ CS0-003 Domain 2 — Vulnerability Management:\n\"Given a scenario, analyze output from vulnerability assessment tools and prioritize using contextual factors including asset criticality, exploit availability, and patch status.\"",
  "exam_tip": "On the exam, vulnerability prioritization questions always involve contextual factors beyond CVSS. Key rules: internet-facing > internal; critical asset > standard asset; exploit available > theoretical. CISA KEV = patch immediately regardless of CVSS. Know EPSS as a probability-of-exploitation metric (complements CVSS, which measures severity not likelihood)."
}
```

---

### Case 23 — Patch Inhibitors

**id:** case23
**title:** Patch Inhibitors
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 2 — Vulnerability Management
**xp_base:** 150
**difficulty:** 3
**tools_type:** patch_reference

#### challenge_data
```
CVE-2021-34527
```
(Ignored by patch_reference — static tool)

#### challenge
When a security patch cannot be applied due to business constraints, what is the appropriate remediation approach?

**valid_answers:** `["compensating control", "compensating controls", "virtual patching", "network segmentation"]`

#### Scenario
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — VULNERABILITY MANAGEMENT TEAM
PRIORITY: MEDIUM
ANALYST: YOU

OPERATION IRONCLAD — PATCH EXCEPTION REQUEST

CVE-2021-34527 (PrintNightmare) — Windows Print Spooler privilege escalation
CVSS: 8.8 | Exploit: Public | Patch: Available

PROBLEM:
The security team recommends patching. The operations team objects:

  "Applying the PrintNightmare patch breaks our legacy label printers
   connected to the print server. These printers are critical for
   warehouse shipping operations — we process 2,000 shipments per day.
   We cannot test a new print driver configuration for at least 6 weeks.
   Patch is rejected pending operations review."

This is a patch inhibitor — a legitimate business constraint that
prevents immediate remediation. The vulnerability must still be
addressed. Patching is not currently an option.

Type 'tools' to see the patch reference guide.

When a patch cannot be applied due to business constraints, what
is the appropriate remediation approach called?
```

#### Hints
1. `Go to https://nvd.nist.gov/vuln/detail/CVE-2021-34527\n        Read about CVE-2021-34527 (PrintNightmare).\n        Note that Microsoft released a patch but it had compatibility issues\n        with some print environments — this is a real-world patch inhibitor.`
2. `Patch inhibitors are legitimate reasons a patch cannot be applied:\n        - Business continuity (critical systems cannot be taken offline)\n        - Operational constraints (patch breaks dependent functionality)\n        - Legacy dependencies (patch incompatible with other software)\n        - Vendor support limitations (vendor hasn't certified the patch)\n        When a patch can't be applied, the risk must still be mitigated.\n        Type 'tools' to see what options are available.`
3. `Type 'tools' in the game. The patch reference tool lists the standard\n        alternatives to patching when a patch inhibitor exists.\n        The primary alternative is a control that reduces risk without\n        applying the patch directly.`
4. `SPOILER — When a patch cannot be applied, the standard response is to\n        implement a COMPENSATING CONTROL — a security measure that reduces\n        the risk of exploitation without fixing the underlying vulnerability.\n        Examples for PrintNightmare: disable Print Spooler on non-print servers,\n        restrict printer operator access, network segment the print server.\n        Type: compensating control`

#### Tools description
Reference guide for patch management: inhibitor categories, compensating control options, virtual patching, the patch exception process, and documentation requirements.

#### Learn
```
Not every vulnerability can be patched immediately. Patch inhibitors are
legitimate obstacles that security teams must navigate daily.

Common patch inhibitors:

Business continuity:
  Patching requires downtime the business cannot afford.
  Example: production database server — zero downtime SLA.
  Response: schedule during next maintenance window; add monitoring now.

Operational constraints:
  The patch breaks dependent functionality (like PrintNightmare + label printers).
  Response: compensating controls until compatibility can be resolved.

Legacy dependencies:
  System runs software incompatible with the patched OS or library version.
  Example: medical device running Windows XP (vendor won't support upgrade).
  Response: network segmentation, enhanced monitoring, risk acceptance.

Vendor support limitations:
  Vendor hasn't certified the patch for their product.
  Example: SCADA system — applying OS patches may void vendor support.
  Response: virtual patching at the network layer (WAF/IPS rule).

Testing requirements:
  Enterprise policy requires patch testing before production deployment.
  Response: schedule test, implement compensating controls during test window.

Compensating controls (primary alternative to patching):
  - Virtual patching: WAF or IPS rule blocks exploitation attempts at the network layer
  - Network segmentation: isolate vulnerable system to reduce attack surface
  - Enhanced monitoring: alert on exploitation indicators (process names, network patterns)
  - Disable vulnerable feature: turn off the vulnerable service/component if not needed
  - Access restriction: limit who can reach the vulnerable system

Patch exception process:
  1. Document the inhibitor and justification
  2. Risk assessment (likelihood x impact with and without compensating controls)
  3. CISO approval and sign-off
  4. Implement compensating controls
  5. Set a review date (typically 30/60/90 days)
  6. Track in vulnerability management platform

Key principle: A vulnerability without a patch is still a vulnerability that must be
managed. The risk must be accepted formally (with compensating controls) or the system
must be removed from service.
```

#### Debrief
```json
{
  "summary": "When a patch cannot be applied (patch inhibitor), the correct response is to implement compensating controls — security measures that reduce the exploitation risk without fixing the underlying vulnerability. For PrintNightmare, this means disabling Print Spooler on non-print servers, restricting access to the print server, and monitoring for exploitation indicators while the operations team prepares a test environment.",
  "real_world": "Compensating controls are a core concept in PCI-DSS, HIPAA, and NIST frameworks. All three require documenting compensating controls when standard controls cannot be met, along with a risk assessment and approval chain. The patch exception process with documented compensating controls, CISO sign-off, and scheduled review date is standard enterprise security practice.",
  "next_step": "Read NIST SP 800-40 Rev 4 (Guide to Enterprise Patch Management):\nhttps://csrc.nist.gov/publications/detail/sp/800-40/rev-4/final",
  "cert_link": "CySA+ CS0-003 Domain 2 — Vulnerability Management:\n\"Given a scenario, identify inhibitors to remediation and recommend appropriate compensating controls.\"",
  "exam_tip": "On the exam, patch inhibitor questions follow a pattern: system has a vulnerability + business constraint prevents patching = compensating control is the answer. Key compensating controls to know: virtual patching (WAF/IPS rule), network segmentation, disable vulnerable feature, enhanced monitoring. Know that risk acceptance requires formal documentation, CISO approval, and a scheduled review date."
}
```

---

### Case 24 — Attack Surface

**id:** case24
**title:** Attack Surface
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 2 — Vulnerability Management
**xp_base:** 250
**difficulty:** 4
**tools_type:** surface_analyzer

#### challenge_data
```
ssh|22|tcp|yes|yes|remote_management
telnet|23|tcp|yes|no|remote_management
ftp|21|tcp|yes|no|file_transfer
https|443|tcp|yes|yes|web_service
rdp|3389|tcp|yes|no|remote_management
smb|445|tcp|yes|no|file_sharing
```

#### Flagging walkthrough
| Service | Internet-facing | Required | Flag |
|---------|----------------|----------|------|
| ssh/22 | yes | yes | [OK] — needed |
| telnet/23 | yes | no | [REDUCE] — unencrypted, not needed |
| ftp/21 | yes | no | [REDUCE] — unencrypted, not needed |
| https/443 | yes | yes | [OK] — web service |
| rdp/3389 | yes | no | [REDUCE] — remote desktop not required externally |
| smb/445 | yes | no | [REDUCE] — file sharing not required externally |

**[REDUCE] count = 4**

**challenge:** How many services should be removed from internet exposure to reduce the attack surface?

**valid_answers:** `["4", "four"]`

#### Scenario
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — VULNERABILITY MANAGEMENT TEAM
PRIORITY: HIGH
ANALYST: YOU

OPERATION IRONCLAD — ATTACK SURFACE REDUCTION

Security scan of Veridian's internet-facing perimeter identified 6 services
exposed to the public internet. Your job: identify which services represent
unnecessary attack surface and should be removed from internet exposure.

INTERNET-FACING SERVICES:

  ssh        port 22   tcp   internet:yes   required:yes   [remote management]
  telnet     port 23   tcp   internet:yes   required:no    [remote management]
  ftp        port 21   tcp   internet:yes   required:no    [file transfer]
  https      port 443  tcp   internet:yes   required:yes   [web service]
  rdp        port 3389 tcp   internet:yes   required:no    [remote access]
  smb        port 445  tcp   internet:yes   required:no    [file sharing]

Note: "required" = business requires this service to be internet-accessible.
Services marked required:no are internet-exposed but have no documented
business justification for external access.

Type 'tools' to run the surface analyzer.

How many services should be removed from internet exposure?
```

#### Hints
1. `Go to https://attack.mitre.org/tactics/TA0043/\n        Read about Reconnaissance in MITRE ATT&CK.\n        Attackers scan for open ports before attacking. Every unnecessary\n        internet-exposed service is an entry point an attacker can probe.`
2. `Attack surface reduction rule: if a service is internet-facing but\n        has no documented business requirement to be internet-accessible,\n        it should be removed from internet exposure.\n        Look at each service: is "required" = yes or no?\n        Services with required:no should be removed from internet exposure.\n        Type 'tools' to run the analysis.`
3. `Type 'tools' in the game. The surface analyzer flags every service\n        that is internet_facing=yes AND required=no as [REDUCE].\n        Count the [REDUCE] flags — that is your answer.`
4. `SPOILER — Four services should be removed:\n        telnet (unencrypted, not needed externally)\n        ftp (unencrypted file transfer, not needed externally)\n        rdp (remote desktop — use VPN instead)\n        smb (Windows file sharing should never be internet-facing)\n        ssh and https remain because they have documented business requirements.\n        Type: 4`

#### Tools description
Parses the service inventory, flags each service as [REDUCE] (internet-facing with no business justification) or [OK], and outputs a count of unnecessary exposures by attack surface category.

#### Learn
```
Attack surface reduction is one of the most effective vulnerability management
practices — it eliminates entire categories of risk before an attacker can exploit
them. If a service doesn't need to be internet-facing, it shouldn't be.

Common unnecessary internet exposures:

Telnet (port 23):
  Unencrypted remote shell. No legitimate reason to expose to the internet in 2026.
  Replace with SSH (encrypted). Attackers scan for open Telnet constantly.

FTP (port 21):
  Unencrypted file transfer. Credentials transmitted in cleartext.
  Replace with SFTP (SSH-based) or FTPS (TLS). Never expose to internet.

RDP (port 3389):
  Windows Remote Desktop. Massive attack surface — BlueKeep, DejaBlue, and others.
  Never expose directly to internet. Use VPN + then RDP internally.
  BlueKeep (CVE-2019-0708) compromised hundreds of thousands of internet-exposed RDP hosts.

SMB (port 445):
  Windows file sharing. Notorious attack vector: EternalBlue (WannaCry, NotPetya).
  Should never be accessible from the internet.
  EternalBlue spread across the internet via exposed SMB in minutes in 2017.

Attack surface categories:
  Network attack surface: open ports/services reachable from outside
  Application attack surface: web endpoints, APIs, login pages
  Social engineering surface: exposed employee info, phishing targets
  Physical attack surface: accessible hardware, USB ports

Reduction techniques:
  Firewall rules: block external access to unnecessary ports
  Network segmentation: isolate services that don't need internet access
  VPN: require VPN before accessing internal services remotely
  Service disabling: turn off services not in use (even internally)
  Cloud security groups: restrict inbound rules to known IPs/ranges

CIS Control 4 (Secure Configuration) and CIS Control 12 (Network Infrastructure
Management) both address attack surface reduction as foundational controls.
```

#### Debrief
```json
{
  "summary": "Four services — telnet, FTP, RDP, and SMB — should be removed from internet exposure. None have documented business requirements for external access, and all four are historically exploited protocols. SSH and HTTPS remain because they have valid business justifications. Attack surface reduction eliminates risk before it can be exploited — it is more effective than reactive patching.",
  "real_world": "Shodan.io indexes all internet-exposed services in real time. Security teams use it to audit their own perimeter (before attackers do). Internet-exposed RDP and SMB were primary vectors for WannaCry (2017) and NotPetya (2017), which caused billions in combined damages. The CIS Controls list attack surface reduction as a top-priority foundational control.",
  "next_step": "Check your attack surface with Shodan (use your own IP/org only):\nhttps://www.shodan.io/\nCIS Controls for secure configuration: https://www.cisecurity.org/controls",
  "cert_link": "CySA+ CS0-003 Domain 2 — Vulnerability Management:\n\"Given a scenario, implement controls to reduce the attack surface including unnecessary services, open ports, and external exposure.\"",
  "exam_tip": "On the exam, attack surface reduction questions test which services should NOT be internet-facing. Know the dangerous protocols: Telnet (23), FTP (21), RDP (3389), SMB (445), TFTP (69), SNMP (161). Key rule: if it doesn't need to be on the internet, remove it. VPN + internal access is the correct answer for RDP. Network segmentation is the answer for services that must exist but shouldn't be directly internet-accessible."
}
```

---

### Case 25 — Code Review

**id:** case25
**title:** Code Review
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 2 — Vulnerability Management
**xp_base:** 250
**difficulty:** 4
**tools_type:** sast_analyzer

#### challenge_data
```
auth.py|45|CWE-89|critical|SQL injection via unsanitized user input in login query
config.py|12|CWE-798|high|Hardcoded credential: API_KEY set to production secret value
upload.py|78|CWE-22|high|Path traversal: filename not validated before file write operation
session.py|33|CWE-384|medium|Session fixation: session ID not regenerated after successful login
logger.py|91|CWE-532|low|Sensitive data in logs: password field written to access.log
```

#### Sorted output (by severity)
1. auth.py:45 — CWE-89 SQL Injection [CRITICAL]
2. config.py:12 — CWE-798 Hard-coded Credentials [HIGH]
3. upload.py:78 — CWE-22 Path Traversal [HIGH]
4. session.py:33 — CWE-384 Session Fixation [MEDIUM]
5. logger.py:91 — CWE-532 Sensitive Info in Logs [LOW]

**Top finding: CWE-89 (SQL Injection) in auth.py**

**challenge:** What is the CWE ID of the highest-severity finding in the SAST report?

**valid_answers:** `["cwe-89", "89", "sql injection"]`

#### Scenario
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — APPLICATION SECURITY TEAM
PRIORITY: HIGH
ANALYST: YOU

OPERATION IRONCLAD — CODE SECURITY REVIEW

As part of Operation IRONCLAD, a SAST (Static Application Security Testing)
scan was run on the Veridian customer portal codebase. The scanner identified
5 findings across multiple files.

SAST SCAN RESULTS:

  auth.py     line 45   CWE-89   CRITICAL
    SQL injection via unsanitized user input in login query

  config.py   line 12   CWE-798  HIGH
    Hardcoded credential: API_KEY set to production secret value

  upload.py   line 78   CWE-22   HIGH
    Path traversal: filename not validated before file write

  session.py  line 33   CWE-384  MEDIUM
    Session fixation: session ID not regenerated after login

  logger.py   line 91   CWE-532  LOW
    Sensitive data in logs: password field written to access.log

Type 'tools' to run the SAST analyzer and rank findings by severity.

What is the CWE ID of the highest-severity finding?
```

#### Hints
1. `Go to https://cwe.mitre.org/top25/archive/2023/2023_top25_list.html\n        Read the CWE Top 25 Most Dangerous Software Weaknesses (2023).\n        CWE-89 (SQL Injection) consistently appears in the top 3.\n        Understanding CWE IDs is essential for interpreting SAST output.`
2. `SAST findings are ranked by severity: critical > high > medium > low.\n        The most critical finding is the one that poses the highest immediate risk.\n        SQL Injection (CWE-89) is typically critical because a successful attack\n        can dump the entire database, bypass authentication, or destroy data.\n        Type 'tools' to rank all findings by severity.`
3. `Type 'tools' in the game. The SAST analyzer sorts findings by severity\n        and identifies the top finding with its CWE ID and name.\n        The top finding is the one marked [CRITICAL].`
4. `SPOILER — CWE-89 (SQL Injection) in auth.py line 45 is the top finding.\n        SQL injection in a login function is especially dangerous — it can\n        allow an attacker to bypass authentication entirely (entering\n        ' OR 1=1 -- as a username logs in as any user).\n        Type: cwe-89`

#### Tools description
Parses SAST output, sorts findings by severity (critical > high > medium > low), maps each CWE to its name, and identifies the top finding that should be remediated first.

#### Learn
```
Static Application Security Testing (SAST) analyzes source code without executing it,
identifying security vulnerabilities at development time — before the code ships.

How SAST works:
  - Parses source code into an Abstract Syntax Tree (AST)
  - Traces data flows from input (user-controlled) to sinks (dangerous functions)
  - Flags patterns that match known vulnerability classes (CWE IDs)
  - Output: file, line number, CWE, severity, description

Key CWE IDs for CySA+ exam:

CWE-89 — SQL Injection:
  User-controlled input used directly in a SQL query.
  Impact: data exfiltration, authentication bypass, data destruction.
  Fix: parameterized queries / prepared statements.

CWE-79 — Cross-Site Scripting (XSS):
  Attacker-controlled data rendered as HTML/JS in the browser.
  Impact: session hijacking, credential theft, defacement.
  Fix: output encoding, Content Security Policy.

CWE-22 — Path Traversal:
  Filename input not validated, allows reading files outside intended directory.
  Example: ../../etc/passwd reads the Linux password file.
  Fix: validate filenames, use allowlists, canonicalize paths.

CWE-798 — Hard-coded Credentials:
  Secret keys, passwords, or API tokens embedded in source code.
  Risk: anyone with code access (including git history) has the credentials.
  Fix: secrets management (HashiCorp Vault, AWS Secrets Manager, env vars).

CWE-384 — Session Fixation:
  Session ID not regenerated after login — attacker can force a known session ID.
  Fix: generate new session ID on privilege change (login, role escalation).

CWE-532 — Sensitive Info in Logs:
  Passwords, tokens, or PII written to log files.
  Risk: logs are often accessible to more people than production systems.
  Fix: scrub sensitive fields from logs; never log credentials.

SAST vs DAST:
  SAST: static analysis of source code (shift-left, finds issues early)
  DAST: dynamic testing of running application (black-box, finds runtime issues)
  Best practice: use both (SAST in CI/CD pipeline, DAST before release)

Common SAST tools:
  SonarQube, Semgrep, Checkmarx, Veracode, GitHub Advanced Security (CodeQL)
```

#### Debrief
```json
{
  "summary": "CWE-89 (SQL Injection) in auth.py at line 45 is the top priority finding — it is critical severity and exists in the login function, meaning an attacker could bypass authentication entirely. The hardcoded API key (CWE-798) and path traversal (CWE-22) are also high severity and should follow immediately. SAST findings should be triaged by severity and remediated in priority order.",
  "real_world": "SQL Injection remains one of the most exploited web vulnerabilities despite being completely preventable. The 2021 Log4Shell vulnerability (CVE-2021-44228) was essentially an injection flaw at the logging layer. OWASP Top 10 2021 lists Injection as #3. CWE-89 has appeared in the CWE Top 25 every year since the list was created.",
  "next_step": "Practice SAST concepts:\nOWASP WebGoat (SQL injection lab): https://owasp.org/www-project-webgoat/\nSemgrep (free SAST tool): https://semgrep.dev/",
  "cert_link": "CySA+ CS0-003 Domain 2 — Vulnerability Management:\n\"Given a scenario, analyze output from application security assessments including SAST results and interpret CWE classifications.\"",
  "exam_tip": "On the exam, SAST/software assurance questions test: (1) CWE ID identification (CWE-89=SQLi, CWE-79=XSS, CWE-22=path traversal, CWE-798=hardcoded creds), (2) severity ranking (critical > high > medium > low), and (3) remediation (parameterized queries fix SQLi; output encoding fixes XSS; secrets management fixes hardcoded creds). Know the difference between SAST (source analysis, shift-left) and DAST (runtime testing, black-box)."
}
```

---

### Case 26 — Threat Intel Vulns

**id:** case26
**title:** Threat Intel Vulns
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 2 — Vulnerability Management
**xp_base:** 150
**difficulty:** 3
**tools_type:** intel_correlator

#### challenge_data
```
CVE-2023-5678|7.2|yes|yes|yes
CVE-2022-9876|8.5|no|yes|no
CVE-2023-1111|6.8|no|no|yes
CVE-2021-0001|9.0|no|no|no
```

#### Priority tiers
| CVE | CVSS | Wild | PoC | APT | Tier |
|-----|------|------|-----|-----|------|
| CVE-2023-5678 | 7.2 | yes | yes | yes | **[IMMEDIATE]** |
| CVE-2022-9876 | 8.5 | no | yes | no | [ELEVATED] |
| CVE-2023-1111 | 6.8 | no | no | yes | [MONITOR] |
| CVE-2021-0001 | 9.0 | no | no | no | [ROUTINE] |

**Top priority: CVE-2023-5678 (exploited in wild, overrides higher CVSS)**

**challenge:** Which CVE should be patched first according to threat intelligence enrichment?

**valid_answers:** `["cve-2023-5678", "2023-5678"]`

#### Scenario
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — VULNERABILITY MANAGEMENT TEAM
PRIORITY: CRITICAL
ANALYST: YOU

OPERATION IRONCLAD — THREAT INTELLIGENCE INTEGRATION

The threat intelligence team has enriched the vulnerability backlog with
external intel. Four CVEs now have threat context beyond CVSS scores.

VULNERABILITY BACKLOG WITH THREAT INTEL:

  CVE-2023-5678  CVSS 7.2
    Exploited in wild: YES  (CISA KEV listed, active campaigns)
    PoC available:     YES  (public GitHub proof-of-concept)
    APT-linked:        YES  (attributed to IRONVEIL threat group)

  CVE-2022-9876  CVSS 8.5
    Exploited in wild: NO
    PoC available:     YES  (Metasploit module available)
    APT-linked:        NO

  CVE-2023-1111  CVSS 6.8
    Exploited in wild: NO
    PoC available:     NO
    APT-linked:        YES  (mentioned in IRONVEIL threat actor report)

  CVE-2021-0001  CVSS 9.0
    Exploited in wild: NO
    PoC available:     NO
    APT-linked:        NO

Note: CVE-2021-0001 has the highest CVSS score (9.0) but no active threat intel.
Type 'tools' to run the intel correlator and get a threat-prioritized order.

Which CVE should be patched first?
```

#### Hints
1. `Go to https://www.cisa.gov/known-exploited-vulnerabilities-catalog\n        Read about the CISA Known Exploited Vulnerabilities (KEV) catalog.\n        CISA mandates federal agencies patch KEV-listed CVEs within 2 weeks,\n        regardless of CVSS score. Active exploitation = immediate action.`
2. `Threat intelligence enrichment changes patch priority:\n        - Actively exploited (in the wild): patch immediately — attackers are using it now\n        - PoC available: patch soon — exploit code is public, mass exploitation follows\n        - APT-linked: monitor and schedule — a threat actor has shown interest\n        - CVSS only: routine — schedule based on score\n        A CVSS 7.2 being actively exploited is more urgent than a CVSS 9.0 with no exploit.\n        Type 'tools' to compute the threat-prioritized order.`
3. `Type 'tools' in the game. The intel correlator assigns a priority tier\n        to each CVE based on threat intel: IMMEDIATE > ELEVATED > MONITOR > ROUTINE.\n        The CVE in the IMMEDIATE tier is your first patch.`
4. `SPOILER — CVE-2023-5678 is the top priority despite having the lowest CVSS\n        of the actively-discussed CVEs (7.2). It is being actively exploited in\n        the wild, has a public PoC, and is linked to the IRONVEIL APT group.\n        CVE-2021-0001 has CVSS 9.0 but no active exploitation — it is ROUTINE.\n        Type: cve-2023-5678`

#### Tools description
Matches each CVE against threat intelligence indicators (exploited in wild, PoC availability, APT attribution) and outputs a threat-prioritized remediation order with tier labels.

#### Learn
```
Threat intelligence integration transforms vulnerability management from reactive
(patch by CVSS score) to predictive (patch what attackers are actually using).

Threat intel priority tiers:

[IMMEDIATE] — Exploited in wild:
  Active exploitation means attackers are compromising systems today.
  The window between disclosure and mass exploitation shrinks every year
  (2021 avg: 15 days; 2023 avg: 5 days for high-profile CVEs).
  Source: CISA KEV catalog, threat intel feeds (Recorded Future, Mandiant).

[ELEVATED] — PoC available:
  Public exploit code (GitHub, Metasploit) accelerates attack capability.
  "Scriptkids" can now exploit what previously required expert skills.
  Metasploit module = mass exploitation likely within days.

[MONITOR] — APT-linked:
  A tracked threat actor has shown interest but isn't actively exploiting yet.
  May indicate an upcoming campaign — patch before they strike.

[ROUTINE] — CVSS only:
  No known exploitation, no PoC, no APT interest.
  Prioritize by CVSS score as tie-break. Schedule normally.

Why CVSS alone is insufficient:
  CVE-2021-0001 (CVSS 9.0, no exploit) is theoretically severe but practically
  irrelevant today — no attacker capability exists yet.
  CVE-2023-5678 (CVSS 7.2, actively exploited) is your real problem.

Threat intel sources for vulnerability enrichment:
  CISA KEV catalog     — mandated, free, authoritative
  FIRST/EPSS           — probability of exploitation in 30 days (free)
  NVD                  — CVSS scores and CVE details (free)
  Shodan/Censys        — see how many systems are still vulnerable (free)
  Recorded Future      — commercial threat intel platform
  Mandiant Advantage   — commercial, APT attribution
  AlienVault OTX       — community threat intel, free tier available

The intel_correlator models the core logic of Risk-Based Vulnerability Management
(RBVM) platforms like Tenable Lumin and Qualys TruRisk.
```

#### Debrief
```json
{
  "summary": "CVE-2023-5678 is the immediate priority despite having the lowest CVSS (7.2) of the enriched CVEs. Active exploitation in the wild — confirmed by CISA KEV listing and attribution to the IRONVEIL threat group — makes it the most dangerous in practice. CVE-2021-0001 has the highest CVSS (9.0) but no exploitation activity — it is a routine patch. Threat intelligence inverts CVSS-based rankings when exploitation evidence exists.",
  "real_world": "The CISA KEV catalog was created specifically because federal agencies were spending time patching high-CVSS CVEs with no exploitation history while missing lower-CVSS CVEs being actively exploited. When Log4Shell broke in Dec 2021, CISA mandated patching within 2 weeks — for high-risk systems, the actual window before exploitation was hours. Threat intel integration is now the standard for enterprise vulnerability programs.",
  "next_step": "Explore the CISA KEV catalog and EPSS:\nhttps://www.cisa.gov/known-exploited-vulnerabilities-catalog\nhttps://www.first.org/epss/data_stats",
  "cert_link": "CySA+ CS0-003 Domain 2 — Vulnerability Management:\n\"Given a scenario, integrate threat intelligence to prioritize vulnerability remediation beyond CVSS-based scoring.\"",
  "exam_tip": "On the exam, threat intel integration questions test the tier model: exploited in wild > PoC available > APT-linked > CVSS only. A low-CVSS CVE being actively exploited always beats a high-CVSS CVE with no exploitation history. Know the CISA KEV catalog as the authoritative source for US federal mandated patches. EPSS complements CVSS by estimating exploitation probability in the next 30 days."
}
```

---

### Case 27 — Security Metrics

**id:** case27
**title:** Security Metrics
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 4 — Reporting & Communication
**xp_base:** 150
**difficulty:** 3
**tools_type:** metrics_calculator

#### challenge_data
```
INC-001|2026-03-01T00:00:00|2026-03-22T12:00:00|2026-03-24T12:00:00
INC-002|2026-03-15T10:00:00|2026-03-15T12:00:00|2026-03-16T12:00:00
INC-003|2026-03-28T00:00:00|2026-03-30T00:00:00|2026-04-01T12:00:00
```

#### Metrics walkthrough
| Incident | Compromised | Detected | Resolved | MTTD | MTTR |
|----------|-------------|----------|----------|------|------|
| INC-001 | 2026-03-01T00:00 | 2026-03-22T12:00 | 2026-03-24T12:00 | 516h | 48h |
| INC-002 | 2026-03-15T10:00 | 2026-03-15T12:00 | 2026-03-16T12:00 | 2h | 24h |
| INC-003 | 2026-03-28T00:00 | 2026-03-30T00:00 | 2026-04-01T12:00 | 48h | 60h |

- MTTD = (516 + 2 + 48) / 3 = 566 / 3 = 188.67 → **189 hours**
- MTTR = (48 + 24 + 60) / 3 = 132 / 3 = 44.0 → **44 hours**

**challenge:** What is the Mean Time to Detect (MTTD) across all three incidents, rounded to the nearest hour?

**valid_answers:** `["189", "189 hours"]`

#### Scenario
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — SECURITY METRICS TEAM
PRIORITY: MEDIUM
ANALYST: YOU

OPERATION IRONCLAD — SECURITY METRICS BASELINE

As part of Operation IRONCLAD, you have been asked to calculate Veridian's
security metrics baseline for the past quarter. Three incidents have been
selected as the metric sample set.

INCIDENT DATA:

  INC-001:
    Compromised:  2026-03-01 00:00  (NIGHTWIRE initial access)
    Detected:     2026-03-22 12:00  (21.5 days later — slow detection)
    Resolved:     2026-03-24 12:00

  INC-002:
    Compromised:  2026-03-15 10:00  (phishing-based credential theft)
    Detected:     2026-03-15 12:00  (2 hours — fast detection)
    Resolved:     2026-03-16 12:00

  INC-003:
    Compromised:  2026-03-28 00:00  (unpatched web server exploit)
    Detected:     2026-03-30 00:00  (48 hours — medium detection time)
    Resolved:     2026-04-01 12:00

Type 'tools' to calculate MTTD and MTTR across all three incidents.

What is the Mean Time to Detect (MTTD) across all three incidents,
rounded to the nearest hour?
```

#### Hints
1. `Go to https://www.crowdstrike.com/cybersecurity-101/mean-time-to-detect-mttd/\n        Read about MTTD (Mean Time to Detect) and MTTR (Mean Time to Respond).\n        These are the two most important security metrics for demonstrating\n        detection and response effectiveness to management.`
2. `MTTD = average time from initial compromise to detection.\n        For each incident: MTTD_i = hours from "Compromised" to "Detected"\n        Then average all MTTD values.\n        INC-001: March 1 00:00 to March 22 12:00 = 21 days + 12h = 516h\n        INC-002: March 15 10:00 to March 15 12:00 = 2h\n        INC-003: March 28 00:00 to March 30 00:00 = 48h\n        Type 'tools' to compute the average.`
3. `Type 'tools' in the game. The metrics calculator computes per-incident\n        MTTD and MTTR, then averages them. The average MTTD is your answer.\n        Average = sum of all MTTD values / number of incidents.`
4. `SPOILER — MTTD = (516 + 2 + 48) / 3 = 566 / 3 = 188.67 → 189 hours.\n        INC-001 heavily skews the average upward — the NIGHTWIRE incident\n        went undetected for 21.5 days (516h). This is why a single slow\n        detection event can make an organization look much worse on metrics.\n        Type: 189`

#### Tools description
Computes per-incident MTTD (compromise to detection) and MTTR (detection to resolution) from timestamp data, then calculates aggregate averages for the metric report.

#### Learn
```
Security metrics translate technical security activities into business language.
MTTD and MTTR are the two most commonly reported security KPIs.

Mean Time to Detect (MTTD):
  Definition: average time from initial compromise to security team detection.
  Formula: sum of (detected_at - compromised_at) for all incidents / incident count
  Units: hours (sometimes days for longer timeframes)
  Better = lower. Target: industry leaders achieve < 24h MTTD.
  
  Why it matters: the longer an attacker goes undetected, the more damage they cause.
  MTTD is a direct measure of detection capability effectiveness.

Mean Time to Respond (MTTR):
  Definition: average time from detection to containment/resolution.
  Formula: sum of (resolved_at - detected_at) for all incidents / incident count
  Units: hours
  Better = lower. Target: SLA-driven (critical incidents often have 4h MTTR targets).
  
  Note: "respond" and "resolve" are used interchangeably on the exam.
  Sometimes MTTR means detection-to-containment; sometimes detection-to-resolution.
  Clarify which milestone is used in your organization.

Industry benchmarks (CrowdStrike 2023 Global Threat Report):
  Average MTTD for all incidents: ~21 days
  Top quartile MTTD: < 24 hours
  Average MTTR: ~5 days
  Best-in-class MTTR: < 1 hour

Other security metrics:
  Patch compliance rate:    % of systems patched within SLA window
  SLA adherence rate:       % of incidents resolved within SLA
  Vulnerability closure rate: % of critical vulns remediated within 30 days
  Mean Time Between Failures (MTBF): uptime/reliability metric

Metric improvement strategies:
  Lower MTTD: better threat detection rules, EDR coverage, UEBA
  Lower MTTR: playbook automation, SOAR platform, pre-approved response actions
  Higher patch compliance: automated patch deployment, exception tracking

Reporting context:
  MTTD/MTTR are operational metrics — used by security team and IR managers.
  For executive reporting, translate to: "Average breach goes undetected 21 days"
  or "We detect active threats 5x faster than industry average."
```

#### Debrief
```json
{
  "summary": "MTTD = 189 hours (~7.9 days). The average is heavily skewed by INC-001 (NIGHTWIRE), which went undetected for 516 hours (21.5 days). INC-002 was detected in just 2 hours — excellent detection. INC-001 is a clear outlier that should drive investment in detection capability. MTTR = 44 hours — faster than the industry average of ~5 days, indicating the response team is effective once detection occurs.",
  "real_world": "MTTD and MTTR are reported quarterly to CISOs and annually to boards in most enterprise security programs. After high-profile breaches like SolarWinds (undetected for 9 months, MTTD ~6,000 hours), companies dramatically increased investment in detection tooling. IBM Cost of a Data Breach Report 2023: identifying a breach in < 200 days saves an average of $1.02M compared to > 200 days.",
  "next_step": "Read the IBM Cost of a Data Breach Report 2023:\nhttps://www.ibm.com/reports/data-breach\nCrowdStrike Global Threat Report 2023: https://www.crowdstrike.com/global-threat-report/",
  "cert_link": "CySA+ CS0-003 Domain 4 — Reporting & Communication:\n\"Given a scenario, calculate and interpret security metrics including MTTD, MTTR, and patch compliance rate.\"",
  "exam_tip": "On the exam, MTTD = time from initial compromise (or initial access) to detection. MTTR = time from detection to resolution/containment. Both are averages across multiple incidents. Lower = better. Know that MTTD measures detection effectiveness and MTTR measures response effectiveness. A high MTTD indicates detection capability problems; a high MTTR indicates response process problems."
}
```

---

### Case 28 — Compliance Gap

**id:** case28
**title:** Compliance Gap
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 4 — Reporting & Communication
**xp_base:** 250
**difficulty:** 4
**tools_type:** compliance_mapper

#### challenge_data
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

#### Compliance per function
| Function | Implemented | Total | Compliance |
|----------|------------|-------|-----------|
| IDENTIFY | 2 | 2 | 100% |
| PROTECT | 3 | 3 | 100% |
| DETECT | 2 | 2 | 100% |
| RESPOND | 2 | 2 | 100% |
| RECOVER | 1 | 6 | **17%** |

**Lowest: RECOVER at 17%**

**challenge:** Which NIST CSF function has the lowest compliance percentage and represents the biggest gap?

**valid_answers:** `["recover", "recovery"]`

#### Scenario
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — COMPLIANCE TEAM
PRIORITY: HIGH
ANALYST: YOU

OPERATION IRONCLAD — NIST CSF GAP ASSESSMENT

The CISO has requested a NIST Cybersecurity Framework (CSF) compliance
assessment before the board presentation. You have been given 15 control
mappings across all 5 NIST CSF functions.

NIST CSF CONTROL STATUS:

  IDENTIFY:
    ID-AM-01  Asset inventory maintained              IMPLEMENTED
    ID-RA-01  Risk assessment conducted annually      IMPLEMENTED

  PROTECT:
    PR-AC-01  Identity management and access control  IMPLEMENTED
    PR-DS-01  Data-at-rest encryption                 IMPLEMENTED
    PR-IP-01  Configuration baseline documented       IMPLEMENTED

  DETECT:
    DE-AE-01  Network anomaly detection active        IMPLEMENTED
    DE-CM-01  Continuous monitoring in place          IMPLEMENTED

  RESPOND:
    RS-RP-01  Incident response plan documented       IMPLEMENTED
    RS-CO-01  Response team communications protocol   IMPLEMENTED

  RECOVER:
    RC-RP-01  Recovery plan documented                NOT IMPLEMENTED
    RC-RP-02  Business continuity plan tested         NOT IMPLEMENTED
    RC-IM-01  Recovery improvements tracked           NOT IMPLEMENTED
    RC-IM-02  Lessons learned formally captured       NOT IMPLEMENTED
    RC-CO-01  Recovery communications plan exists     NOT IMPLEMENTED
    RC-CO-02  External communications contacts list   IMPLEMENTED

Type 'tools' to run the compliance mapper and identify the biggest gap.

Which NIST CSF function has the lowest compliance percentage?
```

#### Hints
1. `Go to https://www.nist.gov/cyberframework\n        Read about the NIST Cybersecurity Framework (CSF).\n        The 5 functions (Identify, Protect, Detect, Respond, Recover) form\n        the backbone of cybersecurity program maturity assessment.`
2. `Calculate compliance per function:\n        implemented controls / total controls for that function × 100\n        Count how many controls are marked IMPLEMENTED vs NOT IMPLEMENTED\n        for each of the 5 NIST CSF functions.\n        The function with the lowest percentage is the biggest gap.\n        Type 'tools' to compute the percentages.`
3. `Type 'tools' in the game. The compliance mapper calculates the percentage\n        for each NIST CSF function and ranks them from lowest to highest.\n        The function at the bottom of the list is your answer.`
4. `SPOILER — RECOVER has only 1 of 6 controls implemented = 17% compliance.\n        Identify, Protect, Detect, and Respond are all at 100%.\n        The NIGHTWIRE incident exposed this gap — Veridian had no documented\n        recovery plan or business continuity test.\n        Type: recover`

#### Tools description
Maps implemented controls to NIST CSF functions (Identify, Protect, Detect, Respond, Recover), computes compliance percentage per function, and ranks functions from largest to smallest gap.

#### Learn
```
Compliance gap analysis identifies where an organization's security controls fall
short of a framework standard. The gap is the distance between current state and
target state.

NIST Cybersecurity Framework (CSF) — 5 Functions:

IDENTIFY (ID):
  Know your assets, risks, and business environment.
  Sub-categories: Asset Management (AM), Risk Assessment (RA), Risk Management (RM)
  Foundational — you can't protect what you don't know you have.

PROTECT (PR):
  Implement safeguards to limit impact of threats.
  Sub-categories: Access Control (AC), Data Security (DS), Protective Technology (PT)
  Preventive controls — the "locks on the doors."

DETECT (DE):
  Identify cybersecurity events when they occur.
  Sub-categories: Anomalies (AE), Continuous Monitoring (CM), Detection Processes (DP)
  Detective controls — the "security cameras."

RESPOND (RS):
  Take action on detected cybersecurity events.
  Sub-categories: Response Planning (RP), Communications (CO), Analysis (AN)
  Responsive controls — the "incident response team."

RECOVER (RC):
  Restore capabilities impaired by incidents.
  Sub-categories: Recovery Planning (RP), Improvements (IM), Communications (CO)
  Resiliency controls — the "disaster recovery plan."

Gap analysis process:
  1. Map implemented controls to framework sub-categories
  2. Calculate compliance % per function (implemented / total × 100)
  3. Rank functions by compliance (lowest = biggest gap)
  4. Build remediation roadmap targeting lowest-compliance functions first
  5. Present to CISO/board with gap visualization (radar chart is common)

Common compliance frameworks on CySA+ exam:
  NIST CSF        — voluntary, widely adopted, 5 functions
  NIST SP 800-53  — federal systems, 20 control families
  ISO 27001       — international, Annex A domains
  PCI-DSS         — payment card industry, 12 requirements
  HIPAA           — healthcare, safeguards (administrative, physical, technical)
  SOC 2           — service organizations, 5 trust service criteria

Why RECOVER is often the weakest function:
  Recovery planning and business continuity testing are perceived as "not urgent"
  until a disaster occurs. Organizations invest heavily in Protect and Detect
  but neglect Recover — then discover the gap during an actual incident.
```

#### Debrief
```json
{
  "summary": "RECOVER has the lowest compliance at 17% (1 of 6 controls implemented). Identify, Protect, Detect, and Respond are all at 100%. The NIGHTWIRE incident directly exposed this gap — Veridian had no documented recovery plan, no business continuity test, and no formal lessons-learned process. Operation IRONCLAD must prioritize RECOVER function controls to close this gap before the board presentation.",
  "real_world": "NIST CSF compliance assessments are used by CISOs to build board-level security roadmaps. The gap analysis output (typically a radar/spider chart) visually shows which functions are mature vs. underdeveloped. After a major incident like NIGHTWIRE, the RECOVER function consistently shows the largest gaps — the incident itself proves the recovery controls were insufficient. NIST CSF 2.0 (released 2024) added GOVERN as a sixth function.",
  "next_step": "Explore the NIST CSF:\nhttps://www.nist.gov/cyberframework\nNIST CSF 2.0 (new in 2024): https://csrc.nist.gov/pubs/cswp/29/final",
  "cert_link": "CySA+ CS0-003 Domain 4 — Reporting & Communication:\n\"Given a scenario, perform compliance gap analysis and map controls to NIST CSF or other frameworks.\"",
  "exam_tip": "On the exam, compliance gap analysis questions test NIST CSF function knowledge. Know the 5 functions in order: Identify, Protect, Detect, Respond, Recover (IPDRR). Gap = lowest compliance percentage = biggest remediation priority. Know that ISO 27001 uses Annex A control domains (not functions), and PCI-DSS uses 12 requirements. NIST CSF 2.0 added GOVERN as a 6th function — this may appear in newer exam versions."
}
```

---

### Case 29 — SLA Tracking

**id:** case29
**title:** SLA Tracking
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 4 — Reporting & Communication
**xp_base:** 150
**difficulty:** 3
**tools_type:** sla_tracker

#### challenge_data
```
TKT-001|critical|2026-04-01T08:00:00|2026-04-01T10:00:00|4
TKT-002|high|2026-04-02T09:00:00|2026-04-03T11:00:00|24
TKT-003|medium|2026-04-03T14:00:00|2026-04-07T14:00:00|72
TKT-004|critical|2026-04-05T22:00:00|2026-04-06T06:00:00|4
TKT-005|high|2026-04-08T10:00:00|2026-04-09T06:00:00|24
TKT-006|low|2026-04-10T11:00:00|2026-04-20T11:00:00|120
```

#### SLA status walkthrough
| Ticket | Priority | Elapsed | SLA | Status |
|--------|----------|---------|-----|--------|
| TKT-001 | critical | 2h | 4h | **[MET]** |
| TKT-002 | high | 26h | 24h | [BREACHED] |
| TKT-003 | medium | 96h | 72h | [BREACHED] |
| TKT-004 | critical | 8h | 4h | [BREACHED] |
| TKT-005 | high | 20h | 24h | **[MET]** |
| TKT-006 | low | 240h | 120h | [BREACHED] |

**MET: 2 / Total: 6 = 33.3% → 33%**

**challenge:** What is the SLA adherence rate (percentage of tickets resolved within SLA)?

**valid_answers:** `["33%", "33", "33 percent"]`

#### Scenario
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — OPERATIONS TEAM
PRIORITY: MEDIUM
ANALYST: YOU

OPERATION IRONCLAD — SLA PERFORMANCE REVIEW

The operations manager needs a SLA adherence report for the past 3 weeks.
Six incident tickets have been reviewed. Each ticket has a priority-based
SLA target (time from opening to resolution).

SLA TARGETS BY PRIORITY:
  Critical:  4 hours
  High:      24 hours
  Medium:    72 hours
  Low:       120 hours

TICKET HISTORY:

  TKT-001  CRITICAL  opened:2026-04-01 08:00  resolved:2026-04-01 10:00
  TKT-002  HIGH      opened:2026-04-02 09:00  resolved:2026-04-03 11:00
  TKT-003  MEDIUM    opened:2026-04-03 14:00  resolved:2026-04-07 14:00
  TKT-004  CRITICAL  opened:2026-04-05 22:00  resolved:2026-04-06 06:00
  TKT-005  HIGH      opened:2026-04-08 10:00  resolved:2026-04-09 06:00
  TKT-006  LOW       opened:2026-04-10 11:00  resolved:2026-04-20 11:00

Type 'tools' to compute elapsed time per ticket and flag SLA breaches.

What is the SLA adherence rate as a percentage?
```

#### Hints
1. `Go to https://www.atlassian.com/incident-management/incident-response/sla\n        Read about SLA (Service Level Agreement) in incident response.\n        SLA adherence rate is a key metric reported to management — it\n        measures whether the team is meeting its response commitments.`
2. `For each ticket: calculate elapsed hours from "opened" to "resolved".\n        Compare elapsed to the SLA target for that priority.\n        If elapsed <= SLA hours: ticket MET its SLA.\n        If elapsed > SLA hours: ticket BREACHED its SLA.\n        Adherence rate = MET count / total count × 100.\n        Type 'tools' to compute elapsed times for all 6 tickets.`
3. `Type 'tools' in the game. The SLA tracker computes elapsed time for\n        each ticket, flags [MET] or [BREACHED], and calculates adherence rate.\n        Count the [MET] tickets and divide by 6.`
4. `SPOILER — Only 2 tickets met their SLA:\n        TKT-001: 2h elapsed, 4h SLA -> MET\n        TKT-005: 20h elapsed, 24h SLA -> MET\n        The other 4 are BREACHED. 2/6 = 33%.\n        TKT-004 (critical) took 8h but had a 4h SLA -- a midnight incident\n        that missed the critical response window.\n        Type: 33%`

#### Tools description
Computes elapsed resolution time per ticket, compares to priority-based SLA targets, flags each ticket as [MET] or [BREACHED], and calculates overall adherence rate.

#### Learn
```
SLA (Service Level Agreement) tracking measures whether the security team is
meeting its response commitments. SLA adherence is a contractual and operational
metric reported to management, auditors, and sometimes clients.

SLA in incident response:

Priority tiers and typical SLA targets:
  Critical (P1):  4 hours — system down, active breach, immediate business impact
  High (P2):      24 hours — significant impact, no workaround available
  Medium (P3):    72 hours (3 days) — moderate impact, workaround available
  Low (P4):       120 hours (5 days) — minimal impact, informational

Why SLAs matter:
  Legal/contractual: MSP/MSSP contracts may include financial penalties for SLA breach
  Operational: SLA adherence measures team capacity and process efficiency
  Regulatory: some frameworks (SOC 2, ISO 27001) require defined response times
  Business trust: stakeholders need confidence incidents will be handled promptly

SLA breach root causes:
  Staffing gaps: insufficient analysts during off-hours (TKT-004: midnight critical)
  Alert fatigue: too many tickets for the team size
  Escalation failures: ticket not routed to correct team
  Tool failures: ticketing system or monitoring platform outage
  Complexity: some tickets take longer due to investigation depth

Improving SLA adherence:
  On-call rotations for critical incidents (24/7 coverage)
  SOAR automation for common incident types (reduce analyst time)
  Proper ticket prioritization (prevent P1 misclassification)
  SLA monitoring dashboards with proactive alerts before breach
  Post-breach review for patterns (which ticket types consistently miss SLA?)

Reporting SLA adherence:
  Operational report: per-ticket status, breach details, elapsed times (for team)
  Management report: adherence % by priority tier, trend over time (for manager)
  Executive report: overall adherence %, major breaches only (for CISO/board)
```

#### Debrief
```json
{
  "summary": "SLA adherence rate is 33% — only 2 of 6 tickets resolved within SLA. TKT-004 is the most notable breach: a critical incident opened at 22:00 took 8 hours but had a 4-hour SLA. This indicates insufficient overnight coverage for critical incidents. TKT-006 (low priority) ran 240 hours against a 120-hour SLA — low-priority tickets are being deprioritized to the point of doubling their SLA target.",
  "real_world": "SLA adherence below 50% is a significant operational concern that would appear in a security program health report. The TKT-004 pattern (midnight critical with no coverage) is a common finding in organizations without formal on-call programs. MSSP contracts often include financial SLA penalties — a 33% adherence rate would result in contractual penalties in a managed service environment.",
  "next_step": "PagerDuty on on-call management for security teams:\nhttps://www.pagerduty.com/resources/learn/incident-response-on-call/",
  "cert_link": "CySA+ CS0-003 Domain 4 — Reporting & Communication:\n\"Given a scenario, track SLA adherence and generate reports demonstrating security team performance against defined response time targets.\"",
  "exam_tip": "On the exam, SLA adherence questions test: (1) SLA calculation (elapsed time vs. target), (2) MET vs. BREACHED classification (elapsed <= SLA = MET), and (3) adherence rate (MET / total × 100). Know that SLA targets are priority-based (critical = hours, low = days). Know that SLA adherence is an operational metric reported to management — not an executive metric."
}
```

---

### Case 30 — Lessons Learned

**id:** case30
**title:** Lessons Learned
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 4 — Reporting & Communication
**xp_base:** 150
**difficulty:** 3
**tools_type:** lessons_reference

#### challenge_data
```
NIGHTWIRE
```
(Ignored by lessons_reference — static tool)

#### challenge
What is the primary goal of the post-incident lessons learned process?

**valid_answers:** `["prevent recurrence", "prevention", "identify root cause", "root cause analysis"]`

#### Scenario
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — INCIDENT RESPONSE TEAM
PRIORITY: MEDIUM
ANALYST: YOU

OPERATION IRONCLAD — PROJECT MERIDIAN CLOSE-OUT

Project MERIDIAN is officially closed. The final deliverable is the
Post-Incident Lessons Learned report for the NIGHTWIRE incident.

IR MANAGER'S BRIEF:

  "The lessons learned meeting is scheduled for next Tuesday. All
   IR team members are required to attend. The purpose is not to
   assign blame — it is to understand what happened, why it happened,
   and what we can do to make sure it doesn't happen again.

   Every section of the document serves this goal. The technical
   findings, the timeline, the detection gap analysis, the response
   critique — all of it feeds into one primary objective.

   Before the meeting, review the lessons learned reference. Your
   first task is simple: what is the PRIMARY GOAL of this process?"

Type 'tools' to open the lessons learned reference guide.

What is the primary goal of the post-incident lessons learned process?
```

#### Hints
1. `Go to https://www.cisa.gov/sites/default/files/publications/Incident-Response-Plan-Basics_508c.pdf\n        Read about Post-Incident Activity in NIST SP 800-61.\n        The lessons learned process is the final phase of incident response.\n        It is documented in the After-Action Report (AAR) or Post-Incident Report.`
2. `Think about what a lessons learned meeting accomplishes:\n        1. What happened? (timeline reconstruction)\n        2. Why did it happen? (root cause analysis)\n        3. What could we have done better? (gap identification)\n        4. What will we change? (corrective actions)\n        All four questions serve one primary goal. What is that goal?\n        Type 'tools' to see the lessons learned reference structure.`
3. `Type 'tools' in the game. The lessons learned reference lists the\n        primary goal, root cause categories, document structure, and\n        required corrective action owners.\n        The primary goal is stated at the top of the reference.`
4. `SPOILER — The primary goal of post-incident lessons learned is to\n        PREVENT RECURRENCE. Every section of the lessons learned document\n        serves this goal: understanding root cause so the same attack\n        vector cannot be used again. The process is not punitive —\n        it is preventive.\n        Type: prevent recurrence`

#### Tools description
Reference guide for post-incident lessons learned: primary goal, root cause categories, document structure, key metrics reviewed, corrective action tracking, and distribution requirements.

#### Learn
```
Post-incident lessons learned (also called After-Action Review, AAR, or Post-Incident
Review) is the final phase of NIST SP 800-61 incident response. It transforms
incident experience into organizational improvement.

Primary goal: PREVENT RECURRENCE

Every element of the lessons learned process serves this goal:
  - Root cause analysis explains WHY the incident happened
  - Gap identification shows WHAT failed (detection, response, controls)
  - Corrective actions define WHAT WILL CHANGE to prevent it happening again
  - Documentation preserves the knowledge for future responders

Root cause categories:

Technical failure:
  Security control failed (misconfigured firewall, patching gap, weak credentials)
  Tool failure (SIEM missed the alert, EDR not deployed on compromised host)

Process gap:
  Missing procedure (no playbook for this incident type)
  Process not followed (response steps skipped or out of order)

Human error:
  Analyst missed indicator (alert fatigue, insufficient training)
  Configuration mistake (change management failure)

Detection failure:
  Log source missing (no visibility into compromised system)
  Detection rule gap (attacker TTP not covered by existing rules)

Response gap:
  Slow escalation (MTTD high but MTTR also high)
  Communication failure (stakeholders not notified in time)

Lessons learned document structure:
  1. Incident summary — what happened, when, impact
  2. Timeline — reconstructed from multi-source evidence
  3. Root cause — primary and contributing factors
  4. What went well — preserve effective practices
  5. What failed — gaps in detection, response, controls
  6. Corrective actions — specific action items, owner, target date
  7. Metrics — MTTD, MTTR, containment time, total impact
  8. Approvals — IR lead, CISO sign-off

Key principle: Blameless post-mortems (from SRE culture) focus on systems and
processes, not individuals. Blame inhibits honest reporting. The goal is
improvement, not punishment.
```

#### Debrief
```json
{
  "summary": "The primary goal of post-incident lessons learned is to prevent recurrence — to understand what happened and why, so that the same attack cannot succeed again. For NIGHTWIRE, the key corrective actions include: deploying EDR on all servers (detection gap), creating a threat hunting schedule (NIGHTWIRE was active for 21 days before detection), and documenting recovery procedures (the RECOVER gap identified in the compliance assessment).",
  "real_world": "The lessons learned report is the most important deliverable of incident response — it's how organizations actually improve over time. Without it, the same vulnerabilities, detection gaps, and response failures recur. NIST SP 800-61 Rev 2 dedicates an entire section to Post-Incident Activity. Google's SRE book popularized blameless post-mortems in the tech industry, now widely adopted in security.",
  "next_step": "Read NIST SP 800-61 Rev 2 (Computer Security Incident Handling Guide), Section 3.4:\nhttps://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final",
  "cert_link": "CySA+ CS0-003 Domain 4 — Reporting & Communication:\n\"Given a scenario, develop post-incident documentation including lessons learned, root cause analysis, and corrective action tracking.\"",
  "exam_tip": "On the exam, post-incident questions test: (1) primary goal = prevent recurrence / identify root cause, (2) NIST IR phases = Preparation, Detection, Containment, Eradication, Recovery, Post-Incident Activity, (3) lessons learned document structure (root cause, corrective actions, owner, date). Know that NIST SP 800-61 is the primary reference for incident response procedures. Blameless = process-focused, not person-focused."
}
```

---

### Case 31 — Executive Report

**id:** case31
**title:** Executive Report
**track:** blue
**cert_objective:** CySA+ CS0-003 Domain 4 — Reporting & Communication
**xp_base:** 250
**difficulty:** 4
**tools_type:** dashboard_filter

#### challenge_data
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

#### Classification
| Metric | Type | Rationale |
|--------|------|-----------|
| mean_time_to_detect | [OPERATIONAL] | Process metric — how fast the team detects |
| overall_risk_reduction | [EXECUTIVE] | Outcome metric — the board cares about risk |
| patch_compliance_rate | [EXECUTIVE] | Outcome metric — compliance posture |
| total_alerts_processed | [OPERATIONAL] | Volume metric — operational throughput |
| critical_vulnerabilities_open | [EXECUTIVE] | Outcome metric — open exposure count |
| average_scan_cycle_time | [OPERATIONAL] | Process metric — team workflow speed |
| sla_adherence_rate | [EXECUTIVE] | Outcome metric — commitment fulfillment |
| firewall_rules_reviewed | [OPERATIONAL] | Activity metric — team work item count |

**Executive count: 4**

**challenge:** How many of the 8 metrics are appropriate for an executive-level dashboard?

**valid_answers:** `["4", "four"]`

#### Scenario
```
AEGIS TERMINAL v1.0 — VERIDIAN SYSTEMS SOC

INCOMING TICKET — REPORTING TEAM
PRIORITY: MEDIUM
ANALYST: YOU

OPERATION IRONCLAD — BOARD PRESENTATION PREP

The CISO is presenting Operation IRONCLAD results to the board next week.
The security team has compiled 8 metrics from the past quarter. Your job:
filter the metrics to identify which ones belong on the EXECUTIVE dashboard
vs. the OPERATIONAL dashboard.

EXECUTIVE dashboard: for the board and CISO — outcome-focused, strategic
OPERATIONAL dashboard: for security team and managers — process-focused, tactical

AVAILABLE METRICS:

  mean_time_to_detect        189 hours
  overall_risk_reduction     23 percent
  patch_compliance_rate      78 percent
  total_alerts_processed     1247
  critical_vulnerabilities_open  12
  average_scan_cycle_time    14 days
  sla_adherence_rate         33 percent
  firewall_rules_reviewed    847

Type 'tools' to classify each metric and filter the executive dashboard.

How many of these metrics are appropriate for the executive-level dashboard?
```

#### Hints
1. `Go to https://www.sans.org/white-papers/security-metrics/\n        Read about security metrics for executive reporting.\n        The key question for each metric: does this answer "are we safer?"\n        (executive) or "how is the team performing?" (operational)?`
2. `Executive metrics answer: "What is our risk posture? Are we improving?"\n        They are outcome-focused — the result of security work.\n        Examples: risk reduction %, breach cost avoided, compliance rate.\n\n        Operational metrics answer: "How much work is the team doing?"\n        They are process-focused — the activities of security work.\n        Examples: alert count, scan frequency, rules reviewed.\n\n        Type 'tools' to classify all 8 metrics.`
3. `Type 'tools' in the game. The dashboard filter classifies each metric\n        as [EXECUTIVE] or [OPERATIONAL] based on whether it is outcome-focused\n        or process-focused. Count the [EXECUTIVE] results.`
4. `SPOILER — 4 metrics are executive-appropriate:\n        overall_risk_reduction (outcome: how much safer are we?)\n        patch_compliance_rate (outcome: what % of systems are patched?)\n        critical_vulnerabilities_open (outcome: how many open critical risks?)\n        sla_adherence_rate (outcome: are we meeting our commitments?)\n        The other 4 (MTTD, alert volume, scan cycle, rules reviewed) are\n        operational — important for the team but not for the board.\n        Type: 4`

#### Tools description
Classifies each metric as [EXECUTIVE] (outcome-focused, risk posture) or [OPERATIONAL] (process-focused, team activities) and outputs a filtered executive dashboard with count.

#### Learn
```
Reporting and communication is the bridge between technical security work and
business decision-making. The wrong metrics in the wrong report wastes executive
attention and obscures what matters.

The core distinction:

EXECUTIVE metrics (outcome-focused):
  Answer: "Are we safer? What is our risk posture?"
  Audience: board of directors, C-suite, CISO
  Examples:
    overall_risk_reduction        — "We reduced risk by 23% this quarter"
    patch_compliance_rate         — "78% of critical systems are fully patched"
    critical_vulnerabilities_open — "12 critical vulnerabilities remain open"
    sla_adherence_rate            — "We met our response SLA 33% of the time"
    breach_cost_avoided           — "Controls prevented estimated $2M in losses"

OPERATIONAL metrics (process-focused):
  Answer: "How is the team performing? Are processes working?"
  Audience: security team leads, SOC managers, vulnerability management team
  Examples:
    mean_time_to_detect      — operational efficiency of detection processes
    total_alerts_processed   — team workload and alert volume
    average_scan_cycle_time  — vulnerability management process speed
    firewall_rules_reviewed  — security engineering activity volume
    tickets_closed_per_week  — team throughput

Why this distinction matters:
  Executives cannot act on "we processed 1,247 alerts" — they have no context.
  Executives CAN act on "12 critical vulnerabilities remain open on payment systems."
  The board approves budgets based on "23% risk reduction" not "847 rules reviewed."

Reporting principles:
  1. Know your audience — tailor depth and terminology
  2. Lead with outcomes — what changed, not what you did
  3. Benchmark — "189h MTTD" is meaningless; "189h vs. 500h industry average" is not
  4. Action-oriented — every metric should connect to a decision or action
  5. Trend over time — a single snapshot is less useful than direction of travel

Common executive security metrics:
  Risk posture score (composite index)
  Patch compliance rate (by criticality tier)
  Mean Time to Detect/Respond (with industry benchmark)
  SLA adherence rate (% of incidents resolved on time)
  Critical vulnerabilities open > 30 days (aging metric)
  Security awareness training completion rate (human risk)
```

#### Debrief
```json
{
  "summary": "Four metrics belong on the executive dashboard: overall_risk_reduction (23%), patch_compliance_rate (78%), critical_vulnerabilities_open (12), and sla_adherence_rate (33%). The other four — MTTD, total alerts processed, scan cycle time, and firewall rules reviewed — are operational metrics that answer 'how is the team working' rather than 'are we safer.' The board presentation should lead with risk reduction and compliance posture, then note the 33% SLA adherence as a team capacity concern requiring investment.",
  "real_world": "CISOs who speak in operational metrics lose their audience and their budget. CISOs who translate operational data into risk outcomes get budget approved. The CISO who says 'We processed 1,247 alerts this quarter' loses to the one who says 'We detected threats 5x faster than industry average, reducing our exposure window from 21 days to 4 days.' The underlying data is the same — the framing is everything.",
  "next_step": "SANS reading on security metrics:\nhttps://www.sans.org/white-papers/security-metrics/\nCISO executive communication: https://www.gartner.com/en/documents/security-board-reporting",
  "cert_link": "CySA+ CS0-003 Domain 4 — Reporting & Communication:\n\"Given a scenario, select appropriate metrics for executive vs. operational audiences and construct a reporting framework that communicates risk posture effectively.\"",
  "exam_tip": "On the exam, executive vs. operational metric questions follow the outcome/process rule: outcome metrics (risk %, compliance %, open vulns) = executive; process metrics (alert counts, scan times, review counts) = operational. MTTD and MTTR are operational metrics unless translated to business impact. The key question: can a board member make a budget decision based on this number? If yes, it is executive-appropriate."
}
```

---

## 6. Verification Checklist

### Tool function contracts — quick reference

| Tool | Input | Key computation | Answer field |
|------|-------|-----------------|-------------|
| vuln_prioritizer | 6-field pipe-separated lines | CVSS + bonuses, sort desc | highest score CVE |
| surface_analyzer | 6-field pipe-separated lines | internet AND not required → [REDUCE] | count of [REDUCE] |
| sast_analyzer | 5-field pipe-separated lines | sort by severity desc | top finding CWE |
| intel_correlator | 5-field pipe-separated lines | tier by wild > PoC > APT > routine | [IMMEDIATE] CVE |
| metrics_calculator | 4-field pipe-separated lines | avg MTTD = sum/n rounded to int | 189 |
| compliance_mapper | 3-field pipe-separated lines | per-function %, lowest = gap | RECOVER |
| sla_tracker | 5-field pipe-separated lines | elapsed <= sla → MET; MET/total×100 | 33 |
| dashboard_filter | 2-field pipe-separated lines | outcome = executive; process = operational | count of [EXECUTIVE] |

### Numeric answers — pre-verified

| Case | Answer | Verification |
|------|--------|--------------|
| case22 | CVE-2021-44228 | 10.0+3+2+2=17.0 (highest) |
| case24 | 4 | telnet, ftp, rdp, smb = 4 × [REDUCE] |
| case25 | CWE-89 | auth.py:45 = critical (only critical in list) |
| case26 | CVE-2023-5678 | exploited_in_wild=yes → [IMMEDIATE] (only one) |
| case27 | 189 | (516+2+48)/3=188.67→189 |
| case28 | RECOVER | 1/6=16.7%→17% (lowest of 5 functions) |
| case29 | 33% | 2/6=33.3%→33% |
| case31 | 4 | risk_reduction, patch_compliance, critical_vulns, sla_adherence |

---

## 7. Open Questions (Resolved)

| Question | Resolution |
|----------|-----------|
| vuln_prioritizer input format | Pipe-separated (6 fields), newline per CVE |
| compliance_mapper framework | NIST CSF (Identify/Protect/Detect/Respond/Recover) |
| intel_correlator tie-break | CVSS descending within same tier |
| dashboard_filter classification | Outcome-focused = executive; process-focused = operational |
