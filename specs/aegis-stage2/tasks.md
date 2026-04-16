# tasks.md — AEGIS Stage 2: Cases 06-13
<!--
GENERATED from specs/aegis-stage2/plan.md + spec.md
Each task: <30 min | "done when" verifiable in <1 min | one commit
-->

**Source plan:** `specs/aegis-stage2/plan.md`
**Date:** 2026-04-12
**Total tasks:** 19

---

## Phase 1: Tool Functions

### TASK-AG2-01: Add traffic_analyzer to utils/tools.py
- **Files:** `aegis/utils/tools.py`
- **Depends on:** TASK-AG-06 (Stage 1 tools.py must exist)
- **Done when:**
  ```
  python -c "
  from utils.tools import run_tool
  data = '2026-04-11T03:15:30,10.0.0.99,185.220.101.45,4444,128,30\n2026-04-11T03:16:00,10.0.0.99,185.220.101.45,4444,128,30\n2026-04-11T03:16:30,10.0.0.99,185.220.101.45,4444,128,30'
  result = run_tool('traffic_analyzer', data)
  assert '[BEACON]' in result
  print('PASS')
  "
  ```
  (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read aegis/utils/tools.py (the existing Stage 1 tools file — do NOT replace it).
  ADD the traffic_analyzer function and its dispatch entry. Leave all existing
  functions and dispatch entries unchanged.

  traffic_analyzer(challenge_text: str) -> str
    Input: newline-separated CSV records.
    Normalize: challenge_text.replace("\\n", "\n") then split("\n").
    Skip blank lines. Parse each record as 6 comma-separated fields:
      timestamp, src_ip, dst_ip, port, bytes, interval_sec
    Ignore header lines (lines where fields[5] == "interval_sec" or non-numeric).

    Grouping and flagging logic:
      Group records by dst_ip.
      For a dst_ip group to receive [BEACON]:
        - The group must have 3 or more records
        - ALL interval_sec values in the group must be equal (same int value)
        - That equal value must be > 0 (excludes interval_sec=0 entries)
      All other dst_ip groups receive [OK].

    Port display: when building the group header, use the port value from the
    first record in the group (all records in a beacon group will share the
    same port in practice — the beacon hits the same dst:port repeatedly).

    Output format (match this structure exactly):
      "TRAFFIC ANALYZER — network flow analysis\n\n"
      "Analyzing <N> connection records...\n\n"
      "Grouping by destination IP...\n\n"
      For each dst_ip group (beacon groups first, then OK groups):
        "<dst_ip>:<first_port_seen> — <N> connection(s)\n"
        For [BEACON] groups:
          "  Intervals: <interval>, <interval>, ... (CONSISTENT)\n"
          "  Payload:   <bytes>, <bytes>, ... bytes (CONSISTENT)\n"
          "  Verdict:   [BEACON] Regular interval + consistent payload — C2 indicator\n\n"
        For [OK] groups with 1 connection:
          "  Verdict:   [OK] Single connection, no pattern\n\n"
        For [OK] groups with 2+ connections but not all equal intervals:
          "  Verdict:   [OK] No consistent interval pattern\n\n"
      If any [BEACON] group found:
        "FINDING: Beaconing detected → <beacon_dst_ip> port <port>\n"
      Else:
        "FINDING: No beaconing pattern detected in this traffic sample.\n"

  Add to run_tool() dispatch dict:
    "traffic_analyzer": traffic_analyzer,

  stdlib only. Type hints and docstring required.
  ```

---

### TASK-AG2-02: Add ioc_hunter to utils/tools.py
- **Files:** `aegis/utils/tools.py`
- **Depends on:** TASK-AG2-01
- **Done when:**
  ```
  python -c "
  from utils.tools import run_tool
  data = '185.220.101.45,deploymaster|||2026-04-11T02:14:33 sshd: Accepted password for deploymaster\n2026-04-11T02:30:15 nginx: 203.0.113.44 - GET /login'
  result = run_tool('ioc_hunter', data)
  assert '[MATCH]' in result
  assert '[NO MATCH]' in result
  print('PASS')
  "
  ```
  (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read aegis/utils/tools.py.
  ADD the ioc_hunter function and its dispatch entry. Leave all existing
  functions and dispatch entries unchanged.

  ioc_hunter(challenge_text: str) -> str
    Input: pipe-delimited string — "IOC1,IOC2,IOC3|||log line 1\nlog line 2"
    Parsing:
      Split challenge_text on "|||" — exactly one occurrence expected.
      Left side = IOC list (comma-separated). Right side = log data.
      Normalize log data: right_side.replace("\\n", "\n") then split("\n").
      Parse IOC list: comma-split, call .strip() on each value.
      Skip any IOC that is empty string after strip.
      IOC matching is case-sensitive substring search only.
      Commas are not permitted inside individual IOC values.

    Output format (match this structure exactly):
      "IOC HUNTER — threat intelligence correlation\n\n"
      "IOC Feed: <ioc1> | <ioc2> | <ioc3>\n"
      "Scanning <N> log entries...\n\n"
      For each non-blank log line (numbered from 1):
        If line contains ANY IOC as a substring:
          "[MATCH] Line <N> — IOC: '<first_matching_ioc>'\n"
          "  <line>\n\n"
        Else:
          "[NO MATCH] Line <N>\n"
          "  <line>\n\n"
      "Results: <match_count> matches from <total> log entries\n"
      "IOCs confirmed in environment: <comma list of matched IOCs>\n"
      If any IOCs were NOT found:
        "IOC not found: <ioc> (check network logs separately)\n"

  Add to run_tool() dispatch dict:
    "ioc_hunter": ioc_hunter,

  stdlib only. Type hints and docstring required.
  ```

---

### TASK-AG2-03: Add attack_mapper to utils/tools.py
- **Files:** `aegis/utils/tools.py`
- **Depends on:** TASK-AG2-02
- **Done when:**
  ```
  python -c "
  from utils.tools import run_tool
  result = run_tool('attack_mapper', 'python3 SUID bit set root shell spawned')
  assert 'T1548.001' in result
  print('PASS')
  "
  ```
  (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read aegis/utils/tools.py.
  ADD the attack_mapper function and its dispatch entry. Leave all existing
  functions and dispatch entries unchanged.

  attack_mapper(challenge_text: str) -> str
    Input: behavior description string (free text).
    Logic:
      Lowercase the full challenge_text string for matching.
      For each technique in the embedded ATT&CK table (defined below),
      count how many of the technique's keywords appear as substrings
      in the lowercased input string.
      Use str.lower() on challenge_text once; use "keyword in lowered_input"
      for each keyword. This handles multi-word keywords like "suid bit"
      and "root shell" correctly without token splitting.
      A technique matches if count >= 1.
      Sort matches by count descending (most keyword hits first).
      Top match = first result.

    Embedded ATT&CK table (hardcoded — ~15 key CySA+ techniques):
      T1548.001 | Abuse Elevation Control Mechanism: Setuid and Setgid |
        Privilege Escalation |
        keywords: ["suid", "sgid", "setuid", "setgid", "suid bit", "python3", "root shell", "privilege escalation", "suid binary"] |
        description: Adversaries may perform shell escapes or exploit
          vulnerabilities in an application with the setuid or setgid bits
          to get code running in a different user's context. SUID binaries
          like python3 can be exploited to spawn a root shell via os.setuid(0). |
        detection: Audit SUID/SGID file permissions. Monitor for unusual
          processes spawned by setuid binaries. |
        mitigation: M1026 — Remove unnecessary SUID/SGID bits. Use file
          integrity monitoring to detect changes.

      T1059.004 | Command and Scripting Interpreter: Unix Shell |
        Execution |
        keywords: ["bash", "shell", "unix shell", "command interpreter", "sh", "zsh"] |
        description: Adversaries may abuse Unix shell commands and scripts for
          execution. Unix shells provide a scripting environment that can be
          used to execute system commands as part of the attack chain. |
        detection: Monitor for shell processes spawned by unusual parents. |
        mitigation: M1038 — Execution prevention. Restrict shell access.

      T1190 | Exploit Public-Facing Application |
        Initial Access |
        keywords: ["rce", "exploit", "web exploit", "nginx", "apache", "cve", "public-facing", "unauthenticated"] |
        description: Adversaries may attempt to take advantage of a weakness
          in an Internet-facing host or system using software, data, or
          commands in order to cause unintended or unanticipated behavior. |
        detection: Monitor for unusual web server processes. IDS/WAF alerts. |
        mitigation: M1048 — Application isolation. Patch management.

      T1078 | Valid Accounts |
        Initial Access / Persistence |
        keywords: ["valid accounts", "credentials", "username", "password", "deploymaster", "credential", "authentication"] |
        description: Adversaries may obtain and abuse credentials of existing
          accounts as a means of gaining Initial Access. |
        detection: Monitor for unusual account usage. Baseline normal logins. |
        mitigation: M1026 — Privileged account management. MFA.

      T1071.001 | Application Layer Protocol: Web Protocols |
        Command and Control |
        keywords: ["http", "https", "web protocol", "c2", "command and control", "beacon", "beaconing", "port 443", "port 80"] |
        description: Adversaries may communicate using application layer
          protocols associated with web traffic to avoid detection. |
        detection: Monitor for unusual outbound web traffic patterns. |
        mitigation: M1037 — Network intrusion prevention.

      T1071 | Application Layer Protocol |
        Command and Control |
        keywords: ["application layer", "c2 traffic", "port 4444", "covert channel", "callback"] |
        description: Adversaries may communicate using application layer
          protocols to avoid detection by blending in with existing traffic. |
        detection: Monitor outbound traffic. Alert on non-standard port connections. |
        mitigation: M1037 — Network intrusion prevention. Egress filtering.

      T1053.005 | Scheduled Task/Job: Cron |
        Persistence / Execution |
        keywords: ["cron", "crontab", "scheduled task", "persistence", "cronjob", "/tmp/.x"] |
        description: Adversaries may abuse the cron job scheduling utility to
          maintain persistence, execute commands, or run programs. |
        detection: Monitor cron logs and crontab modifications. |
        mitigation: M1026 — Privileged account management. Audit cron entries.

      T1027 | Obfuscated Files or Information |
        Defense Evasion |
        keywords: ["obfuscation", "encoded", "base64", "encoded payload", "obfuscated"] |
        description: Adversaries may attempt to make an executable or file
          difficult to discover or analyze by encrypting, encoding, or
          otherwise obfuscating its contents. |
        detection: Scan for encoded strings in scripts and log anomalies. |
        mitigation: M1049 — Antivirus/antimalware. Behavior monitoring.

      T1041 | Exfiltration Over C2 Channel |
        Exfiltration |
        keywords: ["exfil", "exfiltration", "data theft", "data exfiltration", "outbound data"] |
        description: Adversaries may steal data by exfiltrating it over an
          existing command and control channel. |
        detection: Monitor for unusually large outbound transfers. |
        mitigation: M1057 — Data loss prevention. Network monitoring.

      T1046 | Network Service Discovery |
        Discovery |
        keywords: ["port scan", "nmap", "service discovery", "network scan", "reconnaissance"] |
        description: Adversaries may attempt to get a listing of services
          running on remote hosts, including those that may be vulnerable. |
        detection: Monitor for port scanning activity in network logs. |
        mitigation: M1030 — Network segmentation. Rate limiting.

      T1110 | Brute Force |
        Credential Access |
        keywords: ["brute force", "password spray", "failed login", "credential stuffing", "dictionary attack"] |
        description: Adversaries may use brute force techniques to gain access
          to accounts when passwords are unknown or when password hashes are obtained. |
        detection: Monitor authentication logs for multiple failed attempts. |
        mitigation: M1032 — Multi-factor authentication. Account lockout.

      T1136 | Create Account |
        Persistence |
        keywords: ["new account", "user created", "useradd", "backdoor account"] |
        description: Adversaries may create an account to maintain access to
          victim systems. |
        detection: Monitor account creation events in system logs. |
        mitigation: M1030 — Network segmentation. Privileged account management.

      T1083 | File and Directory Discovery |
        Discovery |
        keywords: ["ls", "find", "directory listing", "file enumeration", "hidden file"] |
        description: Adversaries may enumerate files and directories to find
          useful artifacts on a compromised host. |
        detection: Monitor for unusual file access patterns. |
        mitigation: M1022 — Restrict file and directory permissions.

      T1548 | Abuse Elevation Control Mechanism |
        Privilege Escalation |
        keywords: ["elevation", "privilege abuse", "sudo", "sudoers", "su command"] |
        description: Adversaries may circumvent mechanisms designed to control
          elevate privileges to higher levels. |
        detection: Monitor for unusual privilege escalation activity. |
        mitigation: M1026 — Privileged account management.

      T1055 | Process Injection |
        Defense Evasion / Privilege Escalation |
        keywords: ["process injection", "dll injection", "memory injection", "ptrace"] |
        description: Adversaries may inject code into processes to evade
          process-based defenses or elevate privileges. |
        detection: Monitor for unusual process memory writes. |
        mitigation: M1040 — Behavior prevention on endpoint.

    Output format (match this structure exactly):
      "ATT&CK MAPPER — technique lookup\n\n"
      "Input: <original challenge_text>\n\n"
      "Searching for keywords: <space-separated tokens from input>\n\n"
      If matches found:
        For the top match (highest keyword score):
          "MATCH — <ID>: <name>\n"
          "  Tactic:      <tactic>\n"
          "  Description: <description — word-wrap at ~70 chars with 15-char indent>\n"
          "  Detection:   <detection>\n"
          "  Mitigation:  <mitigation>\n\n"
        For secondary matches (count >= 1 but lower score than top):
          "RELATED — <ID>: <name>\n"
          "  Tactic:      <tactic>\n"
          "  Description: <description — abbreviated to first sentence>\n\n"
        "Top match: <top_match_id>\n"
      If no matches:
        "No matching techniques found for the provided behavior description.\n"
        "Try describing the behavior with different keywords.\n"

  Add to run_tool() dispatch dict:
    "attack_mapper": attack_mapper,

  stdlib only. Type hints and docstring required.
  ```

---

### TASK-AG2-04: Add rule_analyzer to utils/tools.py
- **Files:** `aegis/utils/tools.py`
- **Depends on:** TASK-AG2-03
- **Done when:**
  ```
  python -c "
  from utils.tools import run_tool
  data = 'DENY ANY 0.0.0.0/0 203.0.113.47 22\nALLOW ANY 0.0.0.0/0 ANY ANY|||203.0.113.1 203.0.113.47 8080 INBOUND'
  result = run_tool('rule_analyzer', data)
  assert 'ALLOW' in result
  assert 'Rule 2' in result or 'rule 2' in result.lower() or 'ALLOW ANY:ANY' in result
  print('PASS')
  "
  ```
  (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read aegis/utils/tools.py.
  ADD the rule_analyzer function and its dispatch entry. Leave all existing
  functions and dispatch entries unchanged.

  rule_analyzer(challenge_text: str) -> str
    Input: "rules|||traffic"
    Parsing:
      Split challenge_text on "|||" — exactly one occurrence expected.
      Normalize each side: .replace("\\n", "\n") then split("\n"). Skip blank lines.
      Rule format (one per line): "ACTION DIRECTION SRC DST PORT"
        ACTION = ALLOW or DENY
        DIRECTION = ANY (display-only in Stage 2 — not used for matching logic)
        SRC = IP or CIDR or ANY
        DST = IP or ANY
        PORT = port number or ANY
      Traffic format (one per line): "SRC DST PORT DIRECTION"
        DIRECTION on traffic is display-only — not used for matching logic.

    Matching logic (direction-agnostic in Stage 2):
      For each traffic entry, evaluate rules top-down.
      A rule matches a traffic entry if ALL of the following:
        - rule.SRC == "0.0.0.0/0" or rule.SRC == "ANY" or rule.SRC == traffic.SRC
        - rule.DST == "ANY" or rule.DST == traffic.DST
        - rule.PORT == "ANY" or rule.PORT == traffic.PORT
      First matching rule determines the action. Record which rule number matched.

    Output format (match this structure exactly):
      "RULE ANALYZER — firewall policy evaluation\n\n"
      "Rules loaded: <N>\n"
      "Traffic entries: <M>\n\n"
      "Evaluating traffic...\n\n"
      For each traffic entry:
        "[<ACTION> via Rule <N>] <SRC> → <DST>:<PORT>\n"
        For each rule evaluated before the match (no-match rules):
          "  Rule <N>: <ACTION> port <PORT> — no match\n"
        For the matching rule:
          If it is a catch-all (DST==ANY AND PORT==ANY — regardless of SRC value;
            this covers both "SRC=ANY" and "SRC=0.0.0.0/0" catch-alls):
            "  Rule <N>: <ACTION> ANY:ANY — MATCH → <ACTION>ED ← GAP: no deny rule for port <PORT>\n"
          Else:
            "  Rule <N>: <ACTION> port <PORT> — MATCH → <ACTION>ED\n"
          If action is ALLOW and the port is non-standard (not 80, 443, 53, 22, 3306):
            Append " ← EGRESS GAP: C2 beacon permitted" if SRC is an internal IP (10.x.x.x)
        "\n"
      "Gap analysis:\n"
      For each traffic entry that was ALLOWED via a catch-all rule:
        "  Port <PORT>: no explicit DENY — recommend: DENY ANY 0.0.0.0/0 <DST> <PORT>\n"
      For any ALLOWED outbound connection to non-standard port:
        "  Port <PORT> outbound: no egress restriction — recommend egress deny for non-standard ports\n"

  Add to run_tool() dispatch dict:
    "rule_analyzer": rule_analyzer,

  stdlib only. Type hints and docstring required.
  ```

---

### TASK-AG2-05: Add risk_scorer to utils/tools.py
- **Files:** `aegis/utils/tools.py`
- **Depends on:** TASK-AG2-04
- **Done when:**
  ```
  python -c "
  from utils.tools import run_tool
  result = run_tool('risk_scorer', 'likelihood:4|impact:5|asset:production|exploited:yes')
  assert 'CRITICAL' in result
  assert '20' in result
  print('PASS')
  "
  ```
  (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read aegis/utils/tools.py.
  ADD the risk_scorer function and its dispatch entry. Leave all existing
  functions and dispatch entries unchanged.

  risk_scorer(challenge_text: str) -> str
    Input: pipe-delimited key:value pairs — "likelihood:N|impact:N|asset:TYPE|exploited:yes/no"
    Parsing:
      Split on "|". For each token, split on ":" (first colon only).
      Keys are case-insensitive — normalize to lowercase.
      Strip whitespace from both key and value.
      Required keys: likelihood, impact, asset, exploited.
      Accepted asset values: production, staging, test, workstation.
      likelihood and impact are integers 1-5.

    Calculation:
      score = int(likelihood) × int(impact)
      Rating bands:
        1-6:   LOW
        7-12:  MEDIUM
        13-18: HIGH
        19-25: CRITICAL

    Exploitation flag:
      exploited=yes → adds urgency note to output ONLY.
      Does NOT change the numeric score or rating band.
      The score is always L × I only — no modifier.

    Response timeframe by rating:
      LOW:      Accept — patch at next maintenance window
      MEDIUM:   Mitigate within 90 days
      HIGH:     Mitigate within 30 days
      CRITICAL: PATCH IMMEDIATELY

    Output format (match this structure exactly):
      "RISK SCORER — finding risk assessment\n\n"
      "Input parameters:\n"
      "  Likelihood:  <N> / 5\n"
      "  Impact:      <N> / 5\n"
      "  Asset type:  <asset> (title-cased)\n"
      "  Exploited:   <Yes/No>\n\n"
      "Calculation:\n"
      "  Base score:  <L> × <I> = <score>\n"
      "  Rating band: <RATING> (<band_range>)\n\n"
      "Adjustments:\n"
      "  Score is L × I only — no numeric modifier applied.\n"
      If exploited=yes:
        "  Exploited=yes → urgency escalated (do not wait for next change window)\n"
      Else:
        "  Exploited=no → standard remediation timeline applies\n"
      "\n"
      "RISK RATING: <RATING> (Score: <score>/25)\n"
      "Recommended response: <timeframe>\n"
      If exploited=yes:
        "SLA: Emergency — actively exploited findings require same-day remediation\n"

  Add to run_tool() dispatch dict:
    "risk_scorer": risk_scorer,

  stdlib only. Type hints and docstring required.
  ```

---

### TASK-AG2-06: Add remediation_planner to utils/tools.py
- **Files:** `aegis/utils/tools.py`
- **Depends on:** TASK-AG2-05
- **Done when:**
  ```
  python -c "
  from utils.tools import run_tool
  data = 'item01|patch nginx|EFFORT:1|IMPACT:5|DEPENDENCY:none\nitem02|reset creds|EFFORT:1|IMPACT:4|DEPENDENCY:none'
  result = run_tool('remediation_planner', data)
  assert 'RANK 1' in result
  assert 'patch nginx' in result
  print('PASS')
  "
  ```
  (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read aegis/utils/tools.py.
  ADD the remediation_planner function and its dispatch entry. Leave all
  existing functions and dispatch entries unchanged.

  remediation_planner(challenge_text: str) -> str
    Input: newline-separated items in format:
      "item_id|ACTION|EFFORT:N|IMPACT:N|DEPENDENCY:item_id_or_none"
    Parsing:
      Normalize: challenge_text.replace("\\n", "\n") then split("\n"). Skip blank lines.
      For each line: split on "|" into 5 tokens.
      item_id = tokens[0].strip()
      action = tokens[1].strip()
      effort = int(tokens[2].split(":")[1].strip())  — 1-5
      impact = int(tokens[3].split(":")[1].strip())  — 1-5
      dependency = tokens[4].split(":")[1].strip()   — item_id or "none"
      ratio = impact / effort  (float)

    Ranking algorithm:
      1. Compute ratio for each item.
      2. Identify dependency-free items (dependency == "none").
      3. Sort ALL items by ratio descending, then apply tiebreaker:
         Tiebreaker order (deterministic):
           a. Dependency-free items before dependent items (same ratio)
           b. Higher impact first (among items with same dep-status and ratio)
           c. Lower effort first (among items with same dep-status, ratio, impact)
           d. Original input order last (final tiebreaker)
      4. After ranking, check dependency constraint:
         A dependent item cannot appear before its dependency in the final ranked list.
         If a dependent item's rank is BEFORE its dependency's rank: swap them.
         (In practice: insert the dependent item after its dependency in the final order.)

    Output format (match this structure exactly):
      "REMEDIATION PLANNER — priority ranking\n\n"
      "Calculating impact/effort ratios...\n\n"
      For each item in ranked order:
        "RANK <N> [<item_id>]: <action>\n"
        "  Effort: <E> | Impact: <I> | Ratio: <ratio:.2f> | Dependency: <dep>\n"
        If ratio is 1.0 and tiebreaker was applied:
          "  Tiebreaker applied: <reason>\n"
        "  Rationale: <1-sentence rationale based on ratio and context>\n\n"
      "Recommended execution order: <item_id> → <item_id> → ...\n"

    Rationale generation (hardcode based on ratio bands):
      ratio >= 4.0: "Highest quick-win ratio. High impact at minimal effort."
      ratio >= 2.0: "Good quick-win ratio — high impact for moderate effort."
      ratio >= 1.0: "Balanced effort/impact — schedule after higher-ratio items."
      ratio < 1.0:  "Low ratio — important for completeness, schedule last."
      If item has a dependency that is now complete (ranked before it):
        Append "Now unblocked." to rationale.
      If item unblocks other items (other items depend on this item_id):
        Append "Unblocks <dep_ids>." to rationale.

  Add to run_tool() dispatch dict:
    "remediation_planner": remediation_planner,

  stdlib only. Type hints and docstring required.
  ```

---

### TASK-AG2-07: Add exec_reference and notification_reference to utils/tools.py
- **Files:** `aegis/utils/tools.py`
- **Depends on:** TASK-AG2-06
- **Done when:**
  ```
  python -c "
  from utils.tools import run_tool
  r1 = run_tool('exec_reference', 'anything')
  r2 = run_tool('notification_reference', 'anything')
  assert 'EXECUTIVE SUMMARY' in r1 or 'EXEC REPORT' in r1
  assert 'GDPR' in r2
  assert '72' in r2
  print('PASS')
  "
  ```
  (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read aegis/utils/tools.py.
  ADD exec_reference and notification_reference functions and their dispatch
  entries. Leave all existing functions and dispatch entries unchanged.
  Both functions are fully static — they ignore challenge_text entirely.

  exec_reference(challenge_text: str = "") -> str
    Returns the hardcoded executive incident report structure reference.
    Output (copy exactly):
      "EXEC REPORT REFERENCE — standard incident report structure\n\n"
      "SECTION 1: EXECUTIVE SUMMARY\n"
      "  Purpose:  High-level incident overview for C-suite/board\n"
      "  Contains: What happened, scope, current status, key decisions needed\n"
      "  Length:   1 page maximum\n\n"
      "SECTION 2: TIMELINE\n"
      "  Purpose:  Chronological sequence of events\n"
      "  Contains: Detection time, escalation, containment, recovery milestones\n"
      "  Format:   Timestamp | Event | Actor\n\n"
      "SECTION 3: TECHNICAL ANALYSIS\n"
      "  Purpose:  Root cause and attack vector for security leadership\n"
      "  Contains: CVE IDs, affected systems, attack chain, TTPs\n"
      "  Audience: CISO, IT management\n\n"
      "SECTION 4: BUSINESS IMPACT\n"
      "  Purpose:  Business consequences in non-technical terms\n"
      "  Contains: Financial cost (recovery, downtime, fines)\n"
      "            Operational impact (availability, SLA breach)\n"
      "            Reputational impact (customer, press, regulatory)\n"
      "            Data impact (PII records, retention obligations)\n\n"
      "SECTION 5: RECOMMENDATIONS\n"
      "  Purpose:  Prioritized action items to prevent recurrence\n"
      "  Contains: Control improvements, estimated costs, timelines, owners\n\n"
      "SECTION 6: LESSONS LEARNED\n"
      "  Purpose:  IR process improvement\n"
      "  Contains: What worked, what didn't, detection gaps, playbook updates\n"

  notification_reference(challenge_text: str = "") -> str
    Returns the hardcoded breach notification requirements reference.
    Output (copy exactly):
      "NOTIFICATION REFERENCE — breach notification requirements\n\n"
      "GDPR (EU — General Data Protection Regulation)\n"
      "  Trigger:       Personal data breach affecting EU residents\n"
      "  To regulator:  Without undue delay; where feasible, no later than 72 hours\n"
      "                 (Article 33 — this is the maximum, not the recommended wait time)\n"
      "  To subjects:   Without undue delay if high risk to individuals (Article 34)\n"
      "  Personal data: Name, email, IP address, location, health data, etc.\n\n"
      "HIPAA (US — Health Insurance Portability and Accountability Act)\n"
      "  Trigger:       Unsecured protected health information (PHI) breach\n"
      "  To HHS:        60 days from discovery\n"
      "  To subjects:   60 days from discovery\n\n"
      "PCI DSS (Payment Card Industry)\n"
      "  Trigger:       Cardholder data (card numbers, CVV, PIN) compromised\n"
      "  To card brands: Immediately upon suspicion\n\n"
      "CCPA (California Consumer Privacy Act)\n"
      "  Trigger:       California residents' non-encrypted personal data breached\n"
      "  To subjects:   Expedient time / without unreasonable delay\n"

  Add to run_tool() dispatch dict:
    "exec_reference":          exec_reference,
    "notification_reference":  notification_reference,

  stdlib only. Type hints and docstrings required.
  ```

---

## Phase 2: Unit Tests

### TASK-AG2-08: Build tests/test_tools_stage2.py
- **Files:** `aegis/tests/test_tools_stage2.py`
- **Depends on:** TASK-AG2-01 through TASK-AG2-07
- **Done when:** `python -m unittest tests/test_tools_stage2.py` passes all
  tests (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read aegis/utils/tools.py (Stage 2 additions are now present).
  Build aegis/tests/test_tools_stage2.py — unit tests for all 6 new dynamic
  tool functions (exec_reference and notification_reference are static, no
  dynamic logic to test — verify their output contains expected strings).

  Use unittest.TestCase. One test class per tool.

  class TestTrafficAnalyzer(unittest.TestCase):
    def test_beacon_detected(self):
      # 3 records to same dst with equal interval > 0 → [BEACON] in output
      data = "2026-04-11T03:15:30,10.0.0.99,185.220.101.45,4444,128,30\n" \
             "2026-04-11T03:16:00,10.0.0.99,185.220.101.45,4444,128,30\n" \
             "2026-04-11T03:16:30,10.0.0.99,185.220.101.45,4444,128,30"
      result = run_tool("traffic_analyzer", data)
      self.assertIn("[BEACON]", result)
      self.assertIn("185.220.101.45", result)

    def test_no_beacon_single_connections(self):
      # All single connections → no [BEACON] in output
      data = "2026-04-11T03:15:00,10.0.0.99,203.0.113.47,443,512,0\n" \
             "2026-04-11T03:15:30,10.0.0.99,8.8.8.8,53,64,0"
      result = run_tool("traffic_analyzer", data)
      self.assertNotIn("[BEACON]", result)

    def test_no_beacon_unequal_intervals(self):
      # 3 records to same dst but mixed intervals → no [BEACON]
      data = "2026-04-11T03:15:00,10.0.0.99,185.220.101.45,4444,128,10\n" \
             "2026-04-11T03:15:30,10.0.0.99,185.220.101.45,4444,128,30\n" \
             "2026-04-11T03:16:30,10.0.0.99,185.220.101.45,4444,128,60"
      result = run_tool("traffic_analyzer", data)
      self.assertNotIn("[BEACON]", result)

  class TestIocHunter(unittest.TestCase):
    def test_match_found(self):
      data = "deploymaster,185.220.101.45|||" \
             "sshd: Accepted password for deploymaster from 10.0.0.99\n" \
             "nginx: GET /login 200"
      result = run_tool("ioc_hunter", data)
      self.assertIn("[MATCH]", result)
      self.assertIn("[NO MATCH]", result)

    def test_no_match(self):
      data = "unknownIOC|||sshd: normal log line\nnginx: normal log"
      result = run_tool("ioc_hunter", data)
      self.assertNotIn("[MATCH]", result)

    def test_empty_ioc_skipped(self):
      # IOC list with trailing comma should not match empty string
      data = "deploymaster,|||sshd: Accepted password for deploymaster"
      result = run_tool("ioc_hunter", data)
      # Should still find deploymaster match
      self.assertIn("[MATCH]", result)

  class TestAttackMapper(unittest.TestCase):
    def test_suid_maps_to_t1548_001(self):
      result = run_tool("attack_mapper", "SUID bit python3 root shell")
      self.assertIn("T1548.001", result)

    def test_top_match_first(self):
      result = run_tool("attack_mapper", "SUID bit python3 root shell")
      # T1548.001 should appear as MATCH (not just RELATED)
      self.assertIn("MATCH — T1548.001", result)

    def test_no_match(self):
      result = run_tool("attack_mapper", "zzz qqq www")
      self.assertIn("No matching techniques found", result)

  class TestRuleAnalyzer(unittest.TestCase):
    def test_catch_all_allows_port_8080(self):
      data = "DENY ANY 0.0.0.0/0 203.0.113.47 22\n" \
             "ALLOW ANY 0.0.0.0/0 ANY ANY|||" \
             "203.0.113.1 203.0.113.47 8080 INBOUND"
      result = run_tool("rule_analyzer", data)
      self.assertIn("ALLOW", result)
      self.assertIn("8080", result)

    def test_explicit_deny_blocks(self):
      data = "DENY ANY 0.0.0.0/0 203.0.113.47 22\n" \
             "ALLOW ANY 0.0.0.0/0 ANY ANY|||" \
             "203.0.113.1 203.0.113.47 22 INBOUND"
      result = run_tool("rule_analyzer", data)
      self.assertIn("DENY", result)

  class TestRiskScorer(unittest.TestCase):
    def test_critical_score(self):
      result = run_tool("risk_scorer", "likelihood:4|impact:5|asset:production|exploited:yes")
      self.assertIn("CRITICAL", result)
      self.assertIn("20", result)

    def test_low_score(self):
      result = run_tool("risk_scorer", "likelihood:1|impact:2|asset:test|exploited:no")
      self.assertIn("LOW", result)
      self.assertIn("2", result)

    def test_medium_score(self):
      result = run_tool("risk_scorer", "likelihood:2|impact:4|asset:staging|exploited:no")
      self.assertIn("MEDIUM", result)
      self.assertIn("8", result)

    def test_exploitation_no_score_change(self):
      # exploited=yes should NOT change rating from exploited=no for same L and I
      result_yes = run_tool("risk_scorer", "likelihood:2|impact:3|asset:production|exploited:yes")
      result_no  = run_tool("risk_scorer", "likelihood:2|impact:3|asset:production|exploited:no")
      # Both should show score of 6 and LOW
      self.assertIn("LOW", result_yes)
      self.assertIn("LOW", result_no)

  class TestRemediationPlanner(unittest.TestCase):
    def test_highest_ratio_ranked_first(self):
      data = "item01|patch nginx|EFFORT:1|IMPACT:5|DEPENDENCY:none\n" \
             "item02|reset creds|EFFORT:1|IMPACT:4|DEPENDENCY:none"
      result = run_tool("remediation_planner", data)
      # patch nginx (ratio 5.0) should be RANK 1
      lines = result.split("\n")
      rank1_line = [l for l in lines if "RANK 1" in l][0]
      self.assertIn("patch nginx", rank1_line)

    def test_dependency_respected(self):
      # item02 depends on item01; item02 should appear after item01
      data = "item01|low impact item|EFFORT:1|IMPACT:1|DEPENDENCY:none\n" \
             "item02|high impact item|EFFORT:1|IMPACT:5|DEPENDENCY:item01"
      result = run_tool("remediation_planner", data)
      idx_item01 = result.index("item01")
      idx_item02 = result.index("item02")
      # item01 must appear before item02 (even though item02 has higher ratio)
      self.assertLess(idx_item01, idx_item02)

  class TestStaticReferences(unittest.TestCase):
    def test_exec_reference_contains_sections(self):
      result = run_tool("exec_reference", "ignored input")
      self.assertIn("EXECUTIVE SUMMARY", result)
      self.assertIn("BUSINESS IMPACT", result)
      self.assertIn("LESSONS LEARNED", result)

    def test_notification_reference_contains_gdpr(self):
      result = run_tool("notification_reference", "ignored input")
      self.assertIn("GDPR", result)
      self.assertIn("72", result)
      self.assertIn("HIPAA", result)

  Run: python -m unittest tests/test_tools_stage2.py -v
  Do NOT import from cipher/. stdlib only.
  Import run_tool at top of test file:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.tools import run_tool
  ```

---

## Phase 3: Content Files

### TASK-AG2-09: Create content/cases/case06.json
- **Files:** `aegis/content/cases/case06.json`
- **Depends on:** TASK-AG-01 (folder structure exists)
- **Done when:** `python -c "import json; d=json.load(open('content/cases/case06.json')); assert d['id']=='case06'; assert d['valid_answers']==['185.220.101.45']"` passes (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read specs/aegis-stage2/spec.md §5 Case 06 — Network Traffic Analysis (full content).
  Read aegis/content/cases/case01.json as the reference for JSON structure.
  Create aegis/content/cases/case06.json with ALL fields populated exactly as
  defined in the spec.

  Key field values (verify against spec — do not guess):
    id: "case06"
    title: "C2 Beaconing"
    track: "blue"
    cert_objective: "CySA+ CS0-003 Domain 1 — Security Operations"
    xp_base: 100
    difficulty: 2
    tools_type: "traffic_analyzer"
    challenge_data: (the 7-record CSV string from spec §5, \\n-separated, one string)
      "2026-04-11T03:15:00,10.0.0.99,203.0.113.47,443,512,0\\n2026-04-11T03:15:30,10.0.0.99,185.220.101.45,4444,128,30\\n2026-04-11T03:16:00,10.0.0.99,185.220.101.45,4444,128,30\\n2026-04-11T03:16:30,10.0.0.99,185.220.101.45,4444,128,30\\n2026-04-11T03:17:00,10.0.0.99,8.8.8.8,53,64,0\\n2026-04-11T03:17:30,10.0.0.99,185.220.101.45,4444,128,30\\n2026-04-11T03:18:00,10.0.0.99,203.0.113.91,80,4096,0"
    valid_answers: ["185.220.101.45"]
    hints: exactly 4 hints (copy from spec verbatim)
    debrief: object with keys summary, real_world, next_step, cert_link, exam_tip
             (copy from spec verbatim)
    scenario: (copy narrative from spec verbatim)
    challenge: "What is the external IP address that 10.0.0.99 is beaconing to?"
    learn: (copy learn text from spec verbatim)
    tools: "Analyzes network connection records and flags beaconing patterns (consistent interval + consistent payload size)."

  All field values must be copied exactly from the spec. Do not paraphrase.
  ```

---

### TASK-AG2-10: Create content/cases/case07.json
- **Files:** `aegis/content/cases/case07.json`
- **Depends on:** TASK-AG-01
- **Done when:** `python -c "import json; d=json.load(open('content/cases/case07.json')); assert d['id']=='case07'; assert d['valid_answers']==['3','three']"` passes (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read specs/aegis-stage2/spec.md §5 Case 07 — Threat Intelligence (full content).
  Read aegis/content/cases/case01.json as the reference for JSON structure.
  Create aegis/content/cases/case07.json with ALL fields populated exactly as
  defined in the spec.

  Key field values:
    id: "case07"
    title: "IOC Hunt"
    track: "blue"
    cert_objective: "CySA+ CS0-003 Domain 1 — Security Operations"
    xp_base: 100
    difficulty: 2
    tools_type: "ioc_hunter"
    challenge_data: (IOC list|||log data string from spec §5, \\n-separated)
      "185.220.101.45,deploymaster,/tmp/.x|||2026-04-11T02:14:33 sshd[1234]: Accepted password for deploymaster from 10.0.0.99\\n2026-04-11T02:15:01 sudo[1235]: deploymaster : TTY=pts/0 ; COMMAND=/bin/bash\\n2026-04-11T02:30:15 nginx[800]: 203.0.113.44 - GET /login HTTP/1.1 200\\n2026-04-11T03:02:17 sshd[1290]: Failed password for root from 203.0.113.91\\n2026-04-11T03:15:45 cron[1301]: (root) CMD (/tmp/.x)"
    valid_answers: ["3", "three"]
    hints: exactly 4 hints (copy from spec verbatim)
    debrief: object with summary, real_world, next_step, cert_link, exam_tip
    scenario: (copy narrative from spec verbatim)
    challenge: "How many distinct log entries match at least one IOC from the threat intel feed?"
    learn: (copy learn text from spec verbatim)
    tools: "Searches each log entry for any IOC from the feed and reports matches with the matching indicator highlighted."

  All field values must be copied exactly from the spec.
  ```

---

### TASK-AG2-11: Create content/cases/case08.json
- **Files:** `aegis/content/cases/case08.json`
- **Depends on:** TASK-AG-01
- **Done when:** `python -c "import json; d=json.load(open('content/cases/case08.json')); assert d['id']=='case08'; assert 't1548.001' in d['valid_answers']"` passes (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read specs/aegis-stage2/spec.md §5 Case 08 — MITRE ATT&CK Mapping (full content).
  Read aegis/content/cases/case01.json as the reference for JSON structure.
  Create aegis/content/cases/case08.json with ALL fields populated exactly as
  defined in the spec.

  Key field values:
    id: "case08"
    title: "ATT&CK Mapping"
    track: "blue"
    cert_objective: "CySA+ CS0-003 Domain 1 — Security Operations"
    xp_base: 150
    difficulty: 3
    tools_type: "attack_mapper"
    challenge_data: "python3 binary with SUID bit set exploited to spawn interactive root shell from www-data web process"
    valid_answers: ["t1548.001", "1548.001"]
    IMPORTANT: T1548 (parent) is NOT in valid_answers — only the sub-technique.
    hints: exactly 4 hints (copy from spec verbatim)
    debrief: object with summary, real_world, next_step, cert_link, exam_tip
    scenario: (copy narrative from spec verbatim)
    challenge: "What is the MITRE ATT&CK Technique ID for exploiting SUID binaries to gain elevated privileges?"
    learn: (copy learn text from spec verbatim)
    tools: "Searches the embedded MITRE ATT&CK technique reference for keywords from the behavior description."

  All field values must be copied exactly from the spec.
  ```

---

### TASK-AG2-12: Create content/cases/case09.json
- **Files:** `aegis/content/cases/case09.json`
- **Depends on:** TASK-AG-01
- **Done when:** `python -c "import json; d=json.load(open('content/cases/case09.json')); assert d['id']=='case09'; assert d['valid_answers']==['8080']"` passes (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read specs/aegis-stage2/spec.md §5 Case 09 — Firewall Rule Gap Analysis (full content).
  Read aegis/content/cases/case01.json as the reference for JSON structure.
  Create aegis/content/cases/case09.json with ALL fields populated exactly as
  defined in the spec.

  Key field values:
    id: "case09"
    title: "Firewall Gap"
    track: "blue"
    cert_objective: "CySA+ CS0-003 Domain 2 — Vulnerability Management"
    xp_base: 150
    difficulty: 3
    tools_type: "rule_analyzer"
    challenge_data: (rules|||traffic string from spec §5, \\n-separated within each side)
      "DENY ANY 0.0.0.0/0 203.0.113.47 22\\nALLOW ANY 0.0.0.0/0 203.0.113.47 443\\nDENY ANY 0.0.0.0/0 203.0.113.47 3306\\nALLOW ANY 0.0.0.0/0 ANY ANY|||203.0.113.1 203.0.113.47 8080 INBOUND\\n203.0.113.1 203.0.113.47 22 INBOUND\\n10.0.0.99 185.220.101.45 4444 OUTBOUND\\n203.0.113.44 203.0.113.47 443 INBOUND"
    valid_answers: ["8080"]
    hints: exactly 4 hints (copy from spec verbatim)
    debrief: object with summary, real_world, next_step, cert_link, exam_tip
    scenario: (copy narrative from spec verbatim)
    challenge: "Which specific port number should have had an explicit DENY rule in this ruleset to block the attacker's initial access?"
    learn: (copy learn text from spec verbatim)
    tools: "Evaluates each traffic entry against the firewall rules top-down and shows which rule matched and the resulting action."

  All field values must be copied exactly from the spec.
  ```

---

### TASK-AG2-13: Create content/cases/case10.json
- **Files:** `aegis/content/cases/case10.json`
- **Depends on:** TASK-AG-01
- **Done when:** `python -c "import json; d=json.load(open('content/cases/case10.json')); assert d['id']=='case10'; assert 'critical' in d['valid_answers']"` passes (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read specs/aegis-stage2/spec.md §5 Case 10 — Risk Scoring (full content).
  Read aegis/content/cases/case01.json as the reference for JSON structure.
  Create aegis/content/cases/case10.json with ALL fields populated exactly as
  defined in the spec.

  Key field values:
    id: "case10"
    title: "Risk Score"
    track: "blue"
    cert_objective: "CySA+ CS0-003 Domain 2 — Vulnerability Management"
    xp_base: 150
    difficulty: 3
    tools_type: "risk_scorer"
    challenge_data: "likelihood:4|impact:5|asset:production|exploited:yes"
    valid_answers: ["critical", "critical risk"]
    hints: exactly 4 hints (copy from spec verbatim)
    debrief: object with summary, real_world, next_step, cert_link, exam_tip
    scenario: (copy narrative from spec verbatim)
    challenge: "What is the risk rating for this finding using a 5x5 likelihood × impact matrix?"
    learn: (copy learn text from spec verbatim)
    tools: "Calculates risk score using likelihood × impact and maps to a rating band, adjusting for asset type and active exploitation."

  All field values must be copied exactly from the spec.
  ```

---

### TASK-AG2-14: Create content/cases/case11.json
- **Files:** `aegis/content/cases/case11.json`
- **Depends on:** TASK-AG-01
- **Done when:** `python -c "import json; d=json.load(open('content/cases/case11.json')); assert d['id']=='case11'; assert 'business impact' in d['valid_answers']"` passes (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read specs/aegis-stage2/spec.md §5 Case 11 — Executive Reporting (full content).
  Read aegis/content/cases/case01.json as the reference for JSON structure.
  Create aegis/content/cases/case11.json with ALL fields populated exactly as
  defined in the spec.

  Key field values:
    id: "case11"
    title: "Exec Brief"
    track: "blue"
    cert_objective: "CySA+ CS0-003 Domain 4 — Reporting and Communication"
    xp_base: 100
    difficulty: 2
    tools_type: "exec_reference"
    challenge_data: "The NexusCorp incident resulted in full root compromise of the staging server. Estimated recovery cost: $45,000. No customer PII was accessed. Root cause: unpatched nginx CVE. Remediation: patch applied, firewall rules updated."
    valid_answers: ["business impact", "business impact analysis", "impact", "impact analysis"]
    hints: exactly 4 hints (copy from spec verbatim)
    debrief: object with summary, real_world, next_step, cert_link, exam_tip
    scenario: (copy narrative from spec verbatim)
    challenge: "In which section of a standard executive incident report does the financial recovery cost belong?"
    learn: (copy learn text from spec verbatim)
    tools: "Displays the standard executive incident report structure with section descriptions and content guidance."

  All field values must be copied exactly from the spec.
  ```

---

### TASK-AG2-15: Create content/cases/case12.json
- **Files:** `aegis/content/cases/case12.json`
- **Depends on:** TASK-AG-01
- **Done when:** `python -c "import json; d=json.load(open('content/cases/case12.json')); assert d['id']=='case12'; assert 'patch nginx' in d['valid_answers']"` passes (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read specs/aegis-stage2/spec.md §5 Case 12 — Remediation Prioritization (full content).
  Read aegis/content/cases/case01.json as the reference for JSON structure.
  Create aegis/content/cases/case12.json with ALL fields populated exactly as
  defined in the spec.

  Key field values:
    id: "case12"
    title: "Remediation Order"
    track: "blue"
    cert_objective: "CySA+ CS0-003 Domain 4 — Reporting and Communication"
    xp_base: 250
    difficulty: 4
    tools_type: "remediation_planner"
    challenge_data: (6-item remediation list from spec §5, \\n-separated, one string)
      "item01|patch nginx 1.24.0|EFFORT:1|IMPACT:5|DEPENDENCY:none\\nitem02|reset deploymaster credentials|EFFORT:1|IMPACT:4|DEPENDENCY:none\\nitem03|remove SUID from python3|EFFORT:2|IMPACT:4|DEPENDENCY:none\\nitem04|implement WAF rules|EFFORT:3|IMPACT:3|DEPENDENCY:item01\\nitem05|network segmentation|EFFORT:5|IMPACT:5|DEPENDENCY:none\\nitem06|security awareness training|EFFORT:4|IMPACT:2|DEPENDENCY:none"
    valid_answers: ["patch nginx", "patch nginx 1.24.0"]
    hints: exactly 4 hints (copy from spec verbatim)
    debrief: object with summary, real_world, next_step, cert_link, exam_tip
    scenario: (copy narrative from spec verbatim)
    challenge: "Based on highest impact/effort ratio, what remediation action should be completed first?"
    learn: (copy learn text from spec verbatim)
    tools: "Ranks remediation actions by impact/effort ratio, respects dependency ordering, and outputs a prioritized remediation plan."

  All field values must be copied exactly from the spec.
  ```

---

### TASK-AG2-16: Create content/cases/case13.json
- **Files:** `aegis/content/cases/case13.json`
- **Depends on:** TASK-AG-01
- **Done when:** `python -c "import json; d=json.load(open('content/cases/case13.json')); assert d['id']=='case13'; assert '72' in d['valid_answers']"` passes (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read specs/aegis-stage2/spec.md §5 Case 13 — Breach Notification (full content).
  Read aegis/content/cases/case01.json as the reference for JSON structure.
  Create aegis/content/cases/case13.json with ALL fields populated exactly as
  defined in the spec.

  Key field values:
    id: "case13"
    title: "Breach Notification"
    track: "blue"
    cert_objective: "CySA+ CS0-003 Domain 4 — Reporting and Communication"
    xp_base: 250
    difficulty: 4
    tools_type: "notification_reference"
    challenge_data: "Veridian Systems operates in the EU. The staging server breach involved a database containing 1,200 EU customer email addresses. The breach was confirmed on 2026-04-11T03:15 UTC. No financial data was exposed."
    valid_answers: ["72", "72 hours"]
    hints: exactly 4 hints (copy from spec verbatim)
    debrief: object with summary, real_world, next_step, cert_link, exam_tip
    scenario: (copy narrative from spec verbatim)
    challenge: "Under GDPR, what is the maximum number of hours to notify the supervisory authority after discovering a personal data breach?"
    learn: (copy learn text from spec verbatim)
    tools: "Displays breach notification requirements for key regulations including GDPR, HIPAA, PCI DSS, and CCPA with notification timelines."

  All field values must be copied exactly from the spec.
  ```

---

## Phase 4: Registry + Validator

### TASK-AG2-17: Update content/registry.json
- **Files:** `aegis/content/registry.json`
- **Depends on:** TASK-AG2-09 through TASK-AG2-16
- **Done when:**
  ```
  python -c "
  import json
  d = json.load(open('content/registry.json'))
  ids = [c['id'] for c in d['cases']]
  assert 'case06' in ids and 'case13' in ids
  assert len(d['cases']) == 13
  print('PASS')
  "
  ```
  (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read aegis/content/registry.json (the existing Stage 1 registry with case01-05).
  ADD case06-13 entries to the "cases" array. Do NOT modify case01-05 entries.
  Keep the existing "version" field unchanged.

  Append in order at the end of the "cases" array:
    {
      "id": "case06",
      "title": "C2 Beaconing",
      "status": "active",
      "difficulty": 2,
      "cert_objective": "CySA+ CS0-003 Domain 1 — Security Operations"
    },
    {
      "id": "case07",
      "title": "IOC Hunt",
      "status": "active",
      "difficulty": 2,
      "cert_objective": "CySA+ CS0-003 Domain 1 — Security Operations"
    },
    {
      "id": "case08",
      "title": "ATT&CK Mapping",
      "status": "active",
      "difficulty": 3,
      "cert_objective": "CySA+ CS0-003 Domain 1 — Security Operations"
    },
    {
      "id": "case09",
      "title": "Firewall Gap",
      "status": "active",
      "difficulty": 3,
      "cert_objective": "CySA+ CS0-003 Domain 2 — Vulnerability Management"
    },
    {
      "id": "case10",
      "title": "Risk Score",
      "status": "active",
      "difficulty": 3,
      "cert_objective": "CySA+ CS0-003 Domain 2 — Vulnerability Management"
    },
    {
      "id": "case11",
      "title": "Exec Brief",
      "status": "active",
      "difficulty": 2,
      "cert_objective": "CySA+ CS0-003 Domain 4 — Reporting and Communication"
    },
    {
      "id": "case12",
      "title": "Remediation Order",
      "status": "active",
      "difficulty": 4,
      "cert_objective": "CySA+ CS0-003 Domain 4 — Reporting and Communication"
    },
    {
      "id": "case13",
      "title": "Breach Notification",
      "status": "active",
      "difficulty": 4,
      "cert_objective": "CySA+ CS0-003 Domain 4 — Reporting and Communication"
    }

  The final "cases" array must have 13 entries (case01-13) in order.
  ```

---

### TASK-AG2-18: Update validate_content.py
- **Files:** `aegis/validate_content.py`
- **Depends on:** TASK-AG2-17
- **Done when:** `python validate_content.py` exits 0 and prints [PASS] for
  all 13 cases, placement_test.json, and registry.json (run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Read aegis/validate_content.py (the existing Stage 1 validator).
  Make ONE change: expand the _TOOLS_TYPE_ALLOWLIST to include Stage 2 tools.

  Change this:
    _TOOLS_TYPE_ALLOWLIST = {
        "log_filter", "ioc_classifier", "vuln_scorer", "process_analyzer", "none"
    }

  To this:
    _TOOLS_TYPE_ALLOWLIST = {
        "log_filter", "ioc_classifier", "vuln_scorer", "process_analyzer", "none",
        "traffic_analyzer", "ioc_hunter", "attack_mapper", "rule_analyzer",
        "risk_scorer", "remediation_planner", "exec_reference",
        "notification_reference",
    }

  No other changes. Leave all validation logic, required field checks,
  debrief field checks (including exam_tip), track validation, and
  registry validation unchanged.
  ```

---

## Phase 5: Final Validation

### TASK-AG2-19: Run full validation suite
- **Files:** None (validation only)
- **Depends on:** All previous tasks
- **Done when:** All three commands exit 0:
  1. `python validate_content.py` — [PASS] for all 13 cases
  2. `python check_imports.py` — [PASS] for all files
  3. `python -m unittest tests/test_save_manager.py tests/test_tools_stage2.py -v` — all tests pass
  (all run from inside aegis/)
- **Prompt for coding LLM:**
  ```
  Run these three commands from inside aegis/ and report results:

  1. python validate_content.py
     Expected: [PASS] for all 13 cases (case01-13), placement_test.json,
     registry.json. Exit code 0.

  2. python check_imports.py
     Expected: [PASS] for all .py files in utils/ and engine/. Exit code 0.

  3. python -m unittest tests/test_save_manager.py tests/test_tools_stage2.py -v
     Expected: All tests pass. Exit code 0.

  If any command fails:
    - Read the error message carefully
    - Identify which file has the issue
    - Fix the minimum necessary to make the validation pass
    - Re-run the failing command to confirm fix

  Do not modify passing tests to make them less strict.
  Do not change valid_answers in case JSON files.
  Do not change the _TOOLS_TYPE_ALLOWLIST after it was set in TASK-AG2-18.
  ```
