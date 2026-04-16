"""tools.py — AEGIS CyberForge

Blue Team tool functions for the AEGIS SOC analyst simulator.
Each function accepts a challenge_data string and returns a formatted
string result displayed to the player via the 'tools' command.
"""

import base64
import datetime
import re

# ---------------------------------------------------------------------------
# Tool command aliases
#
# Maps tools_type -> [primary_command, ...extra_aliases]
# The FIRST entry is displayed in the UI ("Type 'nmap' to run the scanner").
# ALL entries (plus the generic 'tools') are accepted in the command loop.
# ---------------------------------------------------------------------------
_TOOL_COMMANDS: dict = {
    "log_filter":             ["grep"],
    "ioc_classifier":         ["ioc-classify"],
    "vuln_scorer":            ["vuln-scan"],
    "process_analyzer":       ["ps"],
    "traffic_analyzer":       ["tcpdump", "wireshark"],
    "ioc_hunter":             ["yara", "ioc-hunt"],
    "attack_mapper":          ["mitre-map"],
    "rule_analyzer":          ["sigma"],
    "risk_scorer":            ["risk-score"],
    "exec_reference":         ["escalation-ref"],
    "remediation_planner":    ["patch-plan", "remediate"],
    "notification_reference": ["notify-ref"],
    "siem_correlator":        ["splunk", "siem"],
    "log_classifier":         ["log-classify"],
    "hunt_analyzer":          ["threat-hunt"],
    "mem_analyzer":           ["volatility"],
    "disk_analyzer":          ["autopsy"],
    "coc_reference":          ["coc"],
    "containment_advisor":    ["isolate", "contain"],
    "timeline_builder":       ["timeline"],
    "vuln_prioritizer":       ["tenable", "vuln-priority"],
    "patch_reference":        ["patch-ref"],
    "surface_analyzer":       ["attack-surface"],
    "sast_analyzer":          ["semgrep", "bandit"],
    "intel_correlator":       ["threat-intel"],
    "metrics_calculator":     ["metrics"],
    "compliance_mapper":      ["nist-map"],
    "sla_tracker":            ["sla-check"],
    "lessons_reference":      ["lessons"],
    "dashboard_filter":       ["dashboard"],
    "none":                   [],
}


def get_tool_commands(tools_type: str) -> list:
    """Return accepted command aliases for a tools_type.

    The first item is the primary display command shown to the player.
    Returns an empty list for tools_type 'none' or unknown types.
    """
    return _TOOL_COMMANDS.get(tools_type, [])


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

def log_filter(challenge_text: str) -> str:
    """Filter web server access log for internal IP + 200 + /admin/dashboard.

    Args:
        challenge_text: Newline-separated Apache/nginx access log entries.

    Returns:
        Formatted analysis showing matching and non-matching entries.
    """
    # Normalize: JSON-loaded challenge_data has real \n; some test inputs use literal \\n
    normalized = challenge_text.replace("\\n", "\n")
    lines = [l for l in normalized.split("\n") if l.strip()]

    matches = []
    others = []
    match_ip = None
    match_count = 0

    for line in lines:
        # Check: internal IP (starts with 10.), path /admin/dashboard, status 200
        is_internal = bool(re.match(r"^10\.", line))
        has_admin_path = "/admin/dashboard" in line
        has_200 = '" 200 ' in line or line.endswith('" 200')

        if is_internal and has_admin_path and has_200:
            matches.append(line)
            match_count += 1
            # Extract IP from the line (first token)
            parts = line.split()
            if parts:
                match_ip = parts[0]
        else:
            others.append(line)

    output = "LOG FILTER — access log analysis\n\n"
    output += "Filtering for: internal IP (10.0.0.x) + status 200 + path /admin/dashboard\n\n"

    if matches:
        for line in matches:
            # Shorten timestamp for display
            display = re.sub(r"\s+\+\d{4}\]", "]", line)
            output += f"[MATCH] {display}\n"
    else:
        output += "[NO MATCHES FOUND]\n"

    output += "\nOther entries (no match):\n"
    for line in others:
        display = re.sub(r"\s+\+\d{4}\]", "]", line)
        output += f"{display}\n"

    if match_ip and match_count:
        output += f"\nAnalysis complete. Source IP identified: {match_ip} ({match_count} requests)"
    else:
        output += "\nAnalysis complete. No suspicious internal access found."

    return output


def ioc_classifier(challenge_text: str) -> str:
    """Classify an artifact string by encoding type and decode it.

    Args:
        challenge_text: The artifact string to analyze.

    Returns:
        Formatted classification report.
    """
    artifact = challenge_text.strip()
    output = "IOC CLASSIFIER — artifact analysis\n\n"
    output += f"Input: {artifact}\n\n"
    output += "Encoding detection:\n"

    # Try Base64 detection
    b64_pattern = re.match(r"^[A-Za-z0-9+/]+=*$", artifact)
    is_b64_len = len(artifact) % 4 == 0 or "=" in artifact or len(artifact) % 4 in (2, 3)
    decoded_value = ""

    if b64_pattern and is_b64_len:
        output += f"  Characters: A-Z, a-z, 0-9 only (no +, / or = in this sample)\n"
        output += f"  Length: {len(artifact)} characters (multiple of 4 — Base64 compatible)\n"
        output += "  Pattern: matches Base64 alphabet\n\n"
        output += "Classification: BASE64 ENCODING\n\n"
        try:
            # Pad if necessary
            padded = artifact + "=" * (4 - len(artifact) % 4) if len(artifact) % 4 else artifact
            decoded_value = base64.b64decode(padded).decode("utf-8")
            output += f"Decoded value: {decoded_value}\n"
        except Exception:
            output += "Decoded value: (unable to decode)\n"
        output += "IOC type: Encoded credential or deployment key\n"
        output += "Severity: HIGH — decoded value appears to be a credential or deployment key"

    elif re.match(r"^[0-9a-fA-F]+$", artifact) and len(artifact) % 2 == 0:
        output += f"  Characters: 0-9, a-f only\n"
        output += f"  Length: {len(artifact)} characters (even — hex compatible)\n\n"
        output += "Classification: HEXADECIMAL ENCODING\n\n"
        output += "IOC type: Encoded artifact (hex)\n"
        output += "Severity: MEDIUM — requires further analysis"

    elif re.match(r"^[A-Za-z]+$", artifact):
        output += f"  Characters: letters only\n"
        output += f"  Length: {len(artifact)} characters\n\n"
        output += "Classification: POSSIBLE ROT ENCODING\n\n"
        output += "IOC type: Encoded text artifact\n"
        output += "Severity: MEDIUM — requires further analysis"

    else:
        output += f"  Characters: mixed\n"
        output += f"  Length: {len(artifact)} characters\n\n"
        output += "Classification: UNKNOWN / MIXED ENCODING\n\n"
        output += "IOC type: Unclassified artifact\n"
        output += "Severity: LOW — manual review required"

    return output


def vuln_scorer(challenge_text: str) -> str:  # noqa: ARG001
    """Score and rank vulnerability scan findings by priority.

    Output is derived from the case03 scan results (hardcoded to match
    the scenario defined in the spec).

    Args:
        challenge_text: Unused — findings are embedded in the case scenario.

    Returns:
        Formatted ranked vulnerability report.
    """
    output = "VULNERABILITY SCORER — scan results for 203.0.113.47\n\n"
    output += "Ranking findings by priority...\n\n"
    output += "RANK 1 [CRITICAL] CVE-FAKE-2024-099\n"
    output += "  Service:  nginx 1.24.0 (port 8080)\n"
    output += "  CVSS:     9.8\n"
    output += "  Impact:   Unauthenticated Remote Code Execution\n"
    output += "  Action:   PATCH IMMEDIATELY — remotely exploitable, no auth required\n\n"
    output += "RANK 2 [MEDIUM] CVE-FAKE-2022-001\n"
    output += "  Service:  OpenSSH 8.9p1 (port 22)\n"
    output += "  CVSS:     5.3\n"
    output += "  Impact:   Information disclosure (version banner)\n"
    output += "  Action:   Patch within 90 days — low exploitability\n\n"
    output += "RANK 3 [INFO] MySQL (port 3306)\n"
    output += "  Service:  Filtered — not reachable\n"
    output += "  Action:   No action required\n\n"
    output += "Top priority: CVE-FAKE-2024-099 — patch nginx immediately."
    return output


def process_analyzer(challenge_text: str) -> str:
    """Analyze a process list and flag anomalous privilege combinations.

    Flags:
        [CRITICAL] — user=root AND SUID=yes AND parent not a system process
        [SUSPICIOUS] — SUID=yes AND interpreter binary (python, perl, etc.)
        [OK] — everything else

    Args:
        challenge_text: Newline-separated process list in format:
            "PID:<n> <name> user:<u> SUID:<yes/no> parent:<p>"

    Returns:
        Formatted process analysis table with findings.
    """
    _SYSTEM_PARENTS = {"systemd", "init", "launchd", "kernel"}
    _DANGEROUS_NAMES = {"python3.10", "python3", "python", "perl", "ruby", "bash", "sh"}

    normalized = challenge_text.replace("\\n", "\n")
    lines = [l for l in normalized.split("\n") if l.strip()]

    output = "PROCESS ANALYZER — anomaly detection\n\n"
    output += "Scanning process list for privilege anomalies...\n\n"

    header = f"{'PID':<6} {'PROCESS':<14} {'USER':<12} {'SUID':<6} {'PARENT':<14} STATUS\n"
    output += header

    critical_findings = []

    for line in lines:
        # Parse: "PID:1001 python3.10 user:www-data SUID:yes parent:bash"
        pid_match = re.search(r"PID:(\S+)", line)
        name_match = re.search(r"PID:\S+\s+(\S+)", line)
        user_match = re.search(r"user:(\S+)", line)
        suid_match = re.search(r"SUID:(\S+)", line)
        parent_match = re.search(r"parent:(\S+)", line)

        if not all([pid_match, name_match, user_match, suid_match, parent_match]):
            continue

        pid = pid_match.group(1)
        name = name_match.group(1)
        user = user_match.group(1)
        suid = suid_match.group(1).lower()
        parent = parent_match.group(1)

        is_suid = suid == "yes"
        is_root = user == "root"
        is_system_parent = parent.lower() in _SYSTEM_PARENTS
        is_dangerous_name = name.lower() in _DANGEROUS_NAMES

        if is_root and is_suid and not is_system_parent:
            status = "[CRITICAL] root process, SUID, non-system parent"
            critical_findings.append((pid, name, user, parent))
        elif is_suid and is_dangerous_name and not is_root:
            status = "[SUSPICIOUS] SUID interpreter, spawned by shell"
        else:
            status = "[OK] expected service"

        output += f"{pid:<6} {name:<14} {user:<12} {suid:<6} {parent:<14} {status}\n"

    if critical_findings:
        output += "\n"
        for pid, name, user, parent in critical_findings:
            output += f"CRITICAL finding: PID {pid}\n"
            output += f"  {name} running as ROOT with SUID bit set\n"
            output += f"  Parent: {parent}\n"
            output += "  This matches the GTFOBins SUID exploit pattern for python3.\n"
            output += "  Likely privilege escalation in progress."
    else:
        output += "\nNo critical findings detected."

    return output


_ATTACK_TABLE = [
    {
        "id": "T1548.001",
        "name": "Abuse Elevation Control Mechanism: Setuid and Setgid",
        "tactic": "Privilege Escalation",
        "keywords": ["suid", "sgid", "setuid", "setgid", "suid bit", "python3",
                     "root shell", "privilege escalation", "suid binary"],
        "description": (
            "Adversaries may perform shell escapes or exploit vulnerabilities in an "
            "application with the setuid or setgid bits to get code running in a "
            "different user's context. SUID binaries like python3 can be exploited "
            "to spawn a root shell via os.setuid(0)."
        ),
        "detection": "Audit SUID/SGID file permissions. Monitor for unusual processes spawned by setuid binaries.",
        "mitigation": "M1026 -- Remove unnecessary SUID/SGID bits. Use file integrity monitoring to detect changes.",
    },
    {
        "id": "T1059.004",
        "name": "Command and Scripting Interpreter: Unix Shell",
        "tactic": "Execution",
        "keywords": ["bash", "shell", "unix shell", "command interpreter", "sh", "zsh"],
        "description": (
            "Adversaries may abuse Unix shell commands and scripts for execution. "
            "Unix shells provide a scripting environment that can be used to execute "
            "system commands as part of the attack chain."
        ),
        "detection": "Monitor for shell processes spawned by unusual parents.",
        "mitigation": "M1038 -- Execution prevention. Restrict shell access.",
    },
    {
        "id": "T1190",
        "name": "Exploit Public-Facing Application",
        "tactic": "Initial Access",
        "keywords": ["rce", "exploit", "web exploit", "nginx", "apache", "cve",
                     "public-facing", "unauthenticated"],
        "description": (
            "Adversaries may attempt to take advantage of a weakness in an "
            "Internet-facing host or system using software, data, or commands in "
            "order to cause unintended or unanticipated behavior."
        ),
        "detection": "Monitor for unusual web server processes. IDS/WAF alerts.",
        "mitigation": "M1048 -- Application isolation. Patch management.",
    },
    {
        "id": "T1078",
        "name": "Valid Accounts",
        "tactic": "Initial Access / Persistence",
        "keywords": ["valid accounts", "credentials", "username", "password",
                     "deploymaster", "credential", "authentication"],
        "description": (
            "Adversaries may obtain and abuse credentials of existing accounts "
            "as a means of gaining Initial Access."
        ),
        "detection": "Monitor for unusual account usage. Baseline normal logins.",
        "mitigation": "M1026 -- Privileged account management. MFA.",
    },
    {
        "id": "T1071.001",
        "name": "Application Layer Protocol: Web Protocols",
        "tactic": "Command and Control",
        "keywords": ["http", "https", "web protocol", "c2", "command and control",
                     "beacon", "beaconing", "port 443", "port 80"],
        "description": (
            "Adversaries may communicate using application layer protocols "
            "associated with web traffic to avoid detection."
        ),
        "detection": "Monitor for unusual outbound web traffic patterns.",
        "mitigation": "M1037 -- Network intrusion prevention.",
    },
    {
        "id": "T1071",
        "name": "Application Layer Protocol",
        "tactic": "Command and Control",
        "keywords": ["application layer", "c2 traffic", "port 4444", "covert channel", "callback"],
        "description": (
            "Adversaries may communicate using application layer protocols to "
            "avoid detection by blending in with existing traffic."
        ),
        "detection": "Monitor outbound traffic. Alert on non-standard port connections.",
        "mitigation": "M1037 -- Network intrusion prevention. Egress filtering.",
    },
    {
        "id": "T1053.005",
        "name": "Scheduled Task/Job: Cron",
        "tactic": "Persistence / Execution",
        "keywords": ["cron", "crontab", "scheduled task", "persistence", "cronjob", "/tmp/.x"],
        "description": (
            "Adversaries may abuse the cron job scheduling utility to maintain "
            "persistence, execute commands, or run programs."
        ),
        "detection": "Monitor cron logs and crontab modifications.",
        "mitigation": "M1026 -- Privileged account management. Audit cron entries.",
    },
    {
        "id": "T1027",
        "name": "Obfuscated Files or Information",
        "tactic": "Defense Evasion",
        "keywords": ["obfuscation", "encoded", "base64", "encoded payload", "obfuscated"],
        "description": (
            "Adversaries may attempt to make an executable or file difficult to "
            "discover or analyze by encrypting, encoding, or otherwise obfuscating "
            "its contents."
        ),
        "detection": "Scan for encoded strings in scripts and log anomalies.",
        "mitigation": "M1049 -- Antivirus/antimalware. Behavior monitoring.",
    },
    {
        "id": "T1041",
        "name": "Exfiltration Over C2 Channel",
        "tactic": "Exfiltration",
        "keywords": ["exfil", "exfiltration", "data theft", "data exfiltration", "outbound data"],
        "description": (
            "Adversaries may steal data by exfiltrating it over an existing "
            "command and control channel."
        ),
        "detection": "Monitor for unusually large outbound transfers.",
        "mitigation": "M1057 -- Data loss prevention. Network monitoring.",
    },
    {
        "id": "T1046",
        "name": "Network Service Discovery",
        "tactic": "Discovery",
        "keywords": ["port scan", "nmap", "service discovery", "network scan", "reconnaissance"],
        "description": (
            "Adversaries may attempt to get a listing of services running on "
            "remote hosts, including those that may be vulnerable."
        ),
        "detection": "Monitor for port scanning activity in network logs.",
        "mitigation": "M1030 -- Network segmentation. Rate limiting.",
    },
    {
        "id": "T1110",
        "name": "Brute Force",
        "tactic": "Credential Access",
        "keywords": ["brute force", "password spray", "failed login",
                     "credential stuffing", "dictionary attack"],
        "description": (
            "Adversaries may use brute force techniques to gain access to accounts "
            "when passwords are unknown or when password hashes are obtained."
        ),
        "detection": "Monitor authentication logs for multiple failed attempts.",
        "mitigation": "M1032 -- Multi-factor authentication. Account lockout.",
    },
    {
        "id": "T1136",
        "name": "Create Account",
        "tactic": "Persistence",
        "keywords": ["new account", "user created", "useradd", "backdoor account"],
        "description": (
            "Adversaries may create an account to maintain access to victim systems."
        ),
        "detection": "Monitor account creation events in system logs.",
        "mitigation": "M1030 -- Network segmentation. Privileged account management.",
    },
    {
        "id": "T1083",
        "name": "File and Directory Discovery",
        "tactic": "Discovery",
        "keywords": ["ls", "find", "directory listing", "file enumeration", "hidden file"],
        "description": (
            "Adversaries may enumerate files and directories to find useful "
            "artifacts on a compromised host."
        ),
        "detection": "Monitor for unusual file access patterns.",
        "mitigation": "M1022 -- Restrict file and directory permissions.",
    },
    {
        "id": "T1548",
        "name": "Abuse Elevation Control Mechanism",
        "tactic": "Privilege Escalation",
        "keywords": ["elevation", "privilege abuse", "sudo", "sudoers", "su command"],
        "description": (
            "Adversaries may circumvent mechanisms designed to control elevate "
            "privileges to higher levels."
        ),
        "detection": "Monitor for unusual privilege escalation activity.",
        "mitigation": "M1026 -- Privileged account management.",
    },
    {
        "id": "T1055",
        "name": "Process Injection",
        "tactic": "Defense Evasion / Privilege Escalation",
        "keywords": ["process injection", "dll injection", "memory injection", "ptrace"],
        "description": (
            "Adversaries may inject code into processes to evade process-based "
            "defenses or elevate privileges."
        ),
        "detection": "Monitor for unusual process memory writes.",
        "mitigation": "M1040 -- Behavior prevention on endpoint.",
    },
]


def attack_mapper(challenge_text: str) -> str:
    """Map a behavior description to MITRE ATT&CK techniques via keyword search.

    Uses substring matching against the lowercased input to handle multi-word
    keywords like 'suid bit' and 'root shell'.

    Args:
        challenge_text: Free-text behavior description string.

    Returns:
        Formatted ATT&CK technique lookup report with top match first.
    """
    lowered = challenge_text.lower()

    # Score each technique by number of keyword substring matches
    scored = []
    for technique in _ATTACK_TABLE:
        count = sum(1 for kw in technique["keywords"] if kw in lowered)
        if count > 0:
            scored.append((count, technique))

    # Sort by score descending (stable sort preserves table order for ties)
    scored.sort(key=lambda x: x[0], reverse=True)

    # Build token summary for display (whitespace-split, lowercased)
    tokens = " ".join(lowered.split())

    output = "ATT&CK MAPPER -- technique lookup\n\n"
    output += f"Input: {challenge_text}\n\n"
    output += f"Searching for keywords: {tokens}\n\n"

    if not scored:
        output += "No matching techniques found for the provided behavior description.\n"
        output += "Try describing the behavior with different keywords.\n"
        return output

    top_score, top_tech = scored[0]

    # Format top match
    output += f"MATCH -- {top_tech['id']}: {top_tech['name']}\n"
    output += f"  Tactic:      {top_tech['tactic']}\n"
    output += f"  Description: {top_tech['description']}\n"
    output += f"  Detection:   {top_tech['detection']}\n"
    output += f"  Mitigation:  {top_tech['mitigation']}\n\n"

    # Format secondary matches
    for _, tech in scored[1:]:
        first_sentence = tech["description"].split(".")[0] + "."
        output += f"RELATED -- {tech['id']}: {tech['name']}\n"
        output += f"  Tactic:      {tech['tactic']}\n"
        output += f"  Description: {first_sentence}\n\n"

    output += f"Top match: {top_tech['id']}\n"
    return output


def remediation_planner(challenge_text: str) -> str:
    """Rank remediation items by impact/effort ratio with dependency ordering.

    Tiebreaker order (deterministic):
      1. Dependency-free items before dependent items
      2. Higher impact first
      3. Lower effort first
      4. Original input order last

    Dependent items cannot be scheduled before their dependency's rank.

    Args:
        challenge_text: Newline-separated items in format:
            "item_id|ACTION|EFFORT:N|IMPACT:N|DEPENDENCY:item_id_or_none"

    Returns:
        Formatted ranked remediation plan.
    """
    normalized = challenge_text.replace("\\n", "\n")
    lines = [l.strip() for l in normalized.split("\n") if l.strip()]

    items = []
    for idx, line in enumerate(lines):
        parts = line.split("|")
        if len(parts) != 5:
            continue
        item_id = parts[0].strip()
        action = parts[1].strip()
        effort = int(parts[2].split(":")[1].strip())
        impact = int(parts[3].split(":")[1].strip())
        dep_raw = parts[4].split(":")[1].strip()
        dependency = None if dep_raw.lower() == "none" else dep_raw
        ratio = impact / effort
        items.append({
            "item_id": item_id,
            "action": action,
            "effort": effort,
            "impact": impact,
            "dep": dependency,
            "ratio": ratio,
            "orig_idx": idx,
        })

    # Sort by ratio desc, tiebreaker: dep-free first, higher impact, lower effort, input order
    def _sort_key(item: dict):
        dep_flag = 0 if item["dep"] is None else 1  # 0 = dep-free sorts first
        return (-item["ratio"], dep_flag, -item["impact"], item["effort"], item["orig_idx"])

    sorted_items = sorted(items, key=_sort_key)

    # Topological sort: at each step pick the highest-priority ready item
    # (an item is ready when its dependency has already been scheduled)
    def _toposort(ordered: list) -> list:
        scheduled: set = set()
        result = []
        remaining = list(ordered)  # already sorted by priority

        while remaining:
            ready = [item for item in remaining
                     if item["dep"] is None or item["dep"] in scheduled]
            if not ready:
                # Broken/missing dep — add first item to avoid infinite loop
                ready = [remaining[0]]
            to_schedule = ready[0]  # highest-priority ready item
            result.append(to_schedule)
            scheduled.add(to_schedule["item_id"])
            remaining = [item for item in remaining
                         if item["item_id"] != to_schedule["item_id"]]

        return result

    ranked = _toposort(sorted_items)

    # Build set of item_ids that are depended upon (to note "unblocks X")
    unblocks_map: dict = {}
    for item in items:
        if item["dep"] is not None:
            unblocks_map.setdefault(item["dep"], []).append(item["item_id"])

    output = "REMEDIATION PLANNER -- priority ranking\n\n"
    output += "Calculating impact/effort ratios...\n\n"

    for rank_idx, item in enumerate(ranked, 1):
        dep_display = item["dep"] if item["dep"] else "none"
        output += f"RANK {rank_idx} [{item['item_id']}]: {item['action']}\n"
        output += (
            f"  Effort: {item['effort']} | Impact: {item['impact']} | "
            f"Ratio: {item['ratio']:.2f} | Dependency: {dep_display}\n"
        )

        # Rationale
        if item["ratio"] >= 4.0:
            rationale = "Highest quick-win ratio. High impact at minimal effort."
        elif item["ratio"] >= 2.0:
            rationale = "Good quick-win ratio -- high impact for moderate effort."
        else:
            rationale = "Balanced effort/impact -- schedule after higher-ratio items."
        if item["ratio"] < 1.0:
            rationale = "Low ratio -- important for completeness, schedule last."

        if item["dep"] is not None:
            # Check if dependency appears before this item in ranked list
            dep_ranks = [i for i, r in enumerate(ranked, 1) if r["item_id"] == item["dep"]]
            if dep_ranks and dep_ranks[0] < rank_idx:
                rationale += f" Now unblocked (dependency {item['dep']} complete)."

        if item["item_id"] in unblocks_map:
            ids = ", ".join(unblocks_map[item["item_id"]])
            rationale += f" Unblocks {ids}."

        output += f"  Rationale: {rationale}\n\n"

    exec_order = " -> ".join(item["item_id"] for item in ranked)
    output += f"Recommended execution order: {exec_order}\n"

    return output


def risk_scorer(challenge_text: str) -> str:
    """Compute risk rating using likelihood x impact matrix.

    Score = likelihood x impact (1-25). Exploitation adds urgency note only —
    it does not modify the numeric score or rating band.

    Args:
        challenge_text: Pipe-delimited key:value pairs in format:
            "likelihood:N|impact:N|asset:TYPE|exploited:yes/no"

    Returns:
        Formatted risk assessment with score, rating, and recommended response.
    """
    params: dict = {}
    for token in challenge_text.split("|"):
        token = token.strip()
        if ":" in token:
            key, _, value = token.partition(":")
            params[key.strip().lower()] = value.strip()

    try:
        likelihood = int(params.get("likelihood", 0))
        impact = int(params.get("impact", 0))
    except ValueError:
        return "RISK SCORER -- error: likelihood and impact must be integers 1-5."

    asset = params.get("asset", "unknown").capitalize()
    exploited = params.get("exploited", "no").lower() == "yes"

    score = likelihood * impact

    if score <= 6:
        rating = "LOW"
        band = "1-6"
        timeframe = "Accept -- patch at next maintenance window"
    elif score <= 12:
        rating = "MEDIUM"
        band = "7-12"
        timeframe = "Mitigate within 90 days"
    elif score <= 18:
        rating = "HIGH"
        band = "13-18"
        timeframe = "Mitigate within 30 days"
    else:
        rating = "CRITICAL"
        band = "19-25"
        timeframe = "PATCH IMMEDIATELY"

    output = "RISK SCORER -- finding risk assessment\n\n"
    output += "Input parameters:\n"
    output += f"  Likelihood:  {likelihood} / 5\n"
    output += f"  Impact:      {impact} / 5\n"
    output += f"  Asset type:  {asset}\n"
    output += f"  Exploited:   {'Yes' if exploited else 'No'}\n\n"
    output += "Calculation:\n"
    output += f"  Base score:  {likelihood} x {impact} = {score}\n"
    output += f"  Rating band: {rating} ({band})\n\n"
    output += "Adjustments:\n"
    output += "  Score is L x I only -- no numeric modifier applied.\n"
    if exploited:
        output += "  Exploited=yes -> urgency escalated (do not wait for next change window)\n"
    else:
        output += "  Exploited=no -> standard remediation timeline applies\n"
    output += "\n"
    output += f"RISK RATING: {rating} (Score: {score}/25)\n"
    output += f"Recommended response: {timeframe}\n"
    if exploited:
        output += "SLA: Emergency -- actively exploited findings require same-day remediation\n"

    return output


def rule_analyzer(challenge_text: str) -> str:
    """Evaluate traffic entries against a firewall ruleset (first match wins).

    Direction field in both rules and traffic is display-only — not used
    in matching logic (direction-agnostic in Stage 2).

    Args:
        challenge_text: Pipe-delimited string in format:
            "rule1\\nrule2|||traffic1\\ntraffic2"
            Rule format:    ACTION DIRECTION SRC DST PORT
            Traffic format: SRC DST PORT DIRECTION

    Returns:
        Formatted rule evaluation report with gap analysis.
    """
    if "|||" not in challenge_text:
        return "RULE ANALYZER — error: expected format 'rules|||traffic'"

    rules_part, traffic_part = challenge_text.split("|||", 1)

    rules_raw = [l.strip() for l in rules_part.replace("\\n", "\n").split("\n") if l.strip()]
    traffic_raw = [l.strip() for l in traffic_part.replace("\\n", "\n").split("\n") if l.strip()]

    # Parse rules: ACTION DIRECTION SRC DST PORT
    rules = []
    for line in rules_raw:
        parts = line.split()
        if len(parts) == 5:
            rules.append({
                "action": parts[0].upper(),
                "direction": parts[1].upper(),
                "src": parts[2],
                "dst": parts[3],
                "port": parts[4],
                "raw": line,
            })

    # Parse traffic: SRC DST PORT DIRECTION
    traffic = []
    for line in traffic_raw:
        parts = line.split()
        if len(parts) == 4:
            traffic.append({
                "src": parts[0],
                "dst": parts[1],
                "port": parts[2],
                "direction": parts[3].upper(),
                "raw": line,
            })

    output = "RULE ANALYZER -- firewall policy evaluation\n\n"
    output += f"Rules loaded: {len(rules)}\n"
    output += f"Traffic entries: {len(traffic)}\n\n"
    output += "Evaluating traffic...\n\n"

    gap_ports: list = []  # catch-all allowed connections
    egress_gaps: list = []  # outbound non-standard port allowed

    def _rule_matches(rule: dict, conn: dict) -> bool:
        """Return True if rule matches connection (direction-agnostic)."""
        src_ok = rule["src"] in ("ANY", "0.0.0.0/0") or rule["src"] == conn["src"]
        dst_ok = rule["dst"] == "ANY" or rule["dst"] == conn["dst"]
        port_ok = rule["port"] == "ANY" or rule["port"] == conn["port"]
        return src_ok and dst_ok and port_ok

    def _is_catch_all(rule: dict) -> bool:
        """Catch-all: DST=ANY AND PORT=ANY (SRC value is irrelevant)."""
        return rule["dst"] == "ANY" and rule["port"] == "ANY"

    _standard_ports = {"80", "443", "53", "22", "3306"}
    _internal_prefix = "10."

    for conn in traffic:
        matched_rule = None
        matched_idx = None
        skipped = []

        for i, rule in enumerate(rules, 1):
            if _rule_matches(rule, conn):
                matched_rule = rule
                matched_idx = i
                break
            else:
                skipped.append((i, rule))

        if matched_rule is None:
            output += f"[NO MATCH — IMPLICIT DENY] {conn['src']} -> {conn['dst']}:{conn['port']}\n\n"
            continue

        action = matched_rule["action"]
        actioned = "ALLOWED" if action == "ALLOW" else "DENIED"

        # Build rule evaluation trace
        if _is_catch_all(matched_rule) and action == "ALLOW":
            match_line = (
                f"  Rule {matched_idx}: {action} ANY:ANY -- MATCH -> {actioned}"
                f" <- GAP: no deny rule for port {conn['port']}\n"
            )
            gap_ports.append(conn)
        else:
            match_line = f"  Rule {matched_idx}: {action} port {matched_rule['port']} -- MATCH -> {actioned}\n"

        # Check egress gap for outbound C2
        if (action == "ALLOW"
                and conn["src"].startswith(_internal_prefix)
                and conn["port"] not in _standard_ports):
            egress_gaps.append(conn)

        output += f"[{action} via Rule {matched_idx}] {conn['src']} -> {conn['dst']}:{conn['port']}\n"
        for i, rule in skipped:
            output += f"  Rule {i}: {rule['action']} port {rule['port']} -- no match\n"
        output += match_line
        if (action == "ALLOW"
                and conn["src"].startswith(_internal_prefix)
                and conn["port"] not in _standard_ports
                and not _is_catch_all(matched_rule)):
            output += f"  <- EGRESS GAP: C2 beacon permitted\n"
        output += "\n"

    # Gap analysis section
    output += "Gap analysis:\n"
    if not gap_ports and not egress_gaps:
        output += "  No gaps detected in this ruleset.\n"
    for conn in gap_ports:
        output += (
            f"  Port {conn['port']}: no explicit DENY -- "
            f"recommend: DENY ANY 0.0.0.0/0 {conn['dst']} {conn['port']}\n"
        )
    seen_egress = set()
    for conn in egress_gaps:
        if conn["port"] not in seen_egress:
            output += (
                f"  Port {conn['port']} outbound: no egress restriction -- "
                f"recommend egress deny for non-standard ports\n"
            )
            seen_egress.add(conn["port"])

    return output


def ioc_hunter(challenge_text: str) -> str:
    """Search log entries for matches against a threat intel IOC list.

    Args:
        challenge_text: Pipe-delimited string in format:
            "IOC1,IOC2,IOC3|||log line 1\\nlog line 2"

    Returns:
        Formatted match report showing which IOCs appeared in which log entries.
    """
    if "|||" not in challenge_text:
        return "IOC HUNTER — error: expected format 'IOC1,IOC2|||log line 1\\nlog line 2'"

    ioc_part, log_part = challenge_text.split("|||", 1)

    # Parse IOC list
    iocs = [ioc.strip() for ioc in ioc_part.split(",")]
    iocs = [ioc for ioc in iocs if ioc]  # drop empty strings

    # Parse log lines
    normalized = log_part.replace("\\n", "\n")
    log_lines = [l for l in normalized.split("\n") if l.strip()]

    output = "IOC HUNTER — threat intelligence correlation\n\n"
    output += "IOC Feed: " + " | ".join(iocs) + "\n"
    output += f"Scanning {len(log_lines)} log entries...\n\n"

    matched_iocs: set = set()
    match_count = 0

    for i, line in enumerate(log_lines, 1):
        first_match = None
        for ioc in iocs:
            if ioc in line:
                first_match = ioc
                matched_iocs.add(ioc)
                break

        if first_match:
            match_count += 1
            output += f"[MATCH] Line {i} -- IOC: '{first_match}'\n"
            output += f"  {line}\n\n"
        else:
            output += f"[NO MATCH] Line {i}\n"
            output += f"  {line}\n\n"

    output += f"Results: {match_count} matches from {len(log_lines)} log entries\n"

    if matched_iocs:
        output += "IOCs confirmed in environment: " + ", ".join(sorted(matched_iocs)) + "\n"

    not_found = [ioc for ioc in iocs if ioc not in matched_iocs]
    for ioc in not_found:
        output += f"IOC not found: {ioc} (check network logs separately)\n"

    return output


def traffic_analyzer(challenge_text: str) -> str:
    """Analyze network connection records and flag C2 beaconing patterns.

    Flags a destination as [BEACON] if it receives 3+ connections where all
    interval_sec values are equal and > 0. All other destinations are [OK].

    Args:
        challenge_text: Newline-separated CSV records in format:
            timestamp,src_ip,dst_ip,port,bytes,interval_sec

    Returns:
        Formatted traffic analysis report with beacon/OK verdicts.
    """
    normalized = challenge_text.replace("\\n", "\n")
    lines = [l for l in normalized.split("\n") if l.strip()]

    # Parse records — skip header or malformed lines
    records = []
    for line in lines:
        fields = line.split(",")
        if len(fields) != 6:
            continue
        try:
            interval = int(fields[5].strip())
        except ValueError:
            continue  # skip header line where interval_sec is non-numeric
        records.append({
            "timestamp": fields[0].strip(),
            "src":       fields[1].strip(),
            "dst":       fields[2].strip(),
            "port":      fields[3].strip(),
            "bytes":     int(fields[4].strip()),
            "interval":  interval,
        })

    # Group by dst_ip (preserve insertion order for display)
    groups: dict = {}
    for rec in records:
        groups.setdefault(rec["dst"], []).append(rec)

    # Classify each group
    beacon_groups = []
    ok_groups = []
    for dst, recs in groups.items():
        intervals = [r["interval"] for r in recs]
        all_equal = len(set(intervals)) == 1
        equal_val = intervals[0] if intervals else 0
        is_beacon = len(recs) >= 3 and all_equal and equal_val > 0
        if is_beacon:
            beacon_groups.append((dst, recs))
        else:
            ok_groups.append((dst, recs))

    output = "TRAFFIC ANALYZER — network flow analysis\n\n"
    output += f"Analyzing {len(records)} connection records...\n\n"
    output += "Grouping by destination IP...\n\n"

    def _fmt_group(dst: str, recs: list, is_beacon: bool) -> str:
        port = recs[0]["port"]  # first port seen in the group
        block = f"{dst}:{port} — {len(recs)} connection(s)\n"
        if is_beacon:
            intervals_str = ", ".join(f"{r['interval']}s" for r in recs[1:])  # skip first (no interval)
            bytes_str = ", ".join(str(r["bytes"]) for r in recs)
            block += f"  Intervals: {intervals_str} (CONSISTENT)\n"
            block += f"  Payload:   {bytes_str} bytes (CONSISTENT)\n"
            block += "  Verdict:   [BEACON] Regular interval + consistent payload — C2 indicator\n\n"
        else:
            if len(recs) == 1:
                block += "  Verdict:   [OK] Single connection, no pattern\n\n"
            else:
                block += "  Verdict:   [OK] No consistent interval pattern\n\n"
        return block

    for dst, recs in beacon_groups:
        output += _fmt_group(dst, recs, True)
    for dst, recs in ok_groups:
        output += _fmt_group(dst, recs, False)

    if beacon_groups:
        beacon_dst, beacon_recs = beacon_groups[0]
        beacon_port = beacon_recs[0]["port"]
        output += f"FINDING: Beaconing detected -> {beacon_dst} port {beacon_port}\n"
    else:
        output += "FINDING: No beaconing pattern detected in this traffic sample.\n"

    return output


def exec_reference(challenge_text: str = "") -> str:  # noqa: ARG001
    """Return the standard executive incident report structure reference.

    Static output — challenge_text is ignored entirely.

    Returns:
        Formatted executive report section reference.
    """
    output = "EXEC REPORT REFERENCE -- standard incident report structure\n\n"
    output += "SECTION 1: EXECUTIVE SUMMARY\n"
    output += "  Purpose:  High-level incident overview for C-suite/board\n"
    output += "  Contains: What happened, scope, current status, key decisions needed\n"
    output += "  Length:   1 page maximum\n\n"
    output += "SECTION 2: TIMELINE\n"
    output += "  Purpose:  Chronological sequence of events\n"
    output += "  Contains: Detection time, escalation, containment, recovery milestones\n"
    output += "  Format:   Timestamp | Event | Actor\n\n"
    output += "SECTION 3: TECHNICAL ANALYSIS\n"
    output += "  Purpose:  Root cause and attack vector for security leadership\n"
    output += "  Contains: CVE IDs, affected systems, attack chain, TTPs\n"
    output += "  Audience: CISO, IT management\n\n"
    output += "SECTION 4: BUSINESS IMPACT\n"
    output += "  Purpose:  Business consequences in non-technical terms\n"
    output += "  Contains: Financial cost (recovery, downtime, fines)\n"
    output += "            Operational impact (availability, SLA breach)\n"
    output += "            Reputational impact (customer, press, regulatory)\n"
    output += "            Data impact (PII records, retention obligations)\n\n"
    output += "SECTION 5: RECOMMENDATIONS\n"
    output += "  Purpose:  Prioritized action items to prevent recurrence\n"
    output += "  Contains: Control improvements, estimated costs, timelines, owners\n\n"
    output += "SECTION 6: LESSONS LEARNED\n"
    output += "  Purpose:  IR process improvement\n"
    output += "  Contains: What worked, what didn't, detection gaps, playbook updates\n"
    return output


def notification_reference(challenge_text: str = "") -> str:  # noqa: ARG001
    """Return breach notification requirements for key regulations.

    Static output — challenge_text is ignored entirely.

    Returns:
        Formatted breach notification reference table.
    """
    output = "NOTIFICATION REFERENCE -- breach notification requirements\n\n"
    output += "GDPR (EU -- General Data Protection Regulation)\n"
    output += "  Trigger:       Personal data breach affecting EU residents\n"
    output += "  To regulator:  Without undue delay; where feasible, no later than 72 hours\n"
    output += "                 (Article 33 -- this is the maximum, not the recommended wait time)\n"
    output += "  To subjects:   Without undue delay if high risk to individuals (Article 34)\n"
    output += "  Personal data: Name, email, IP address, location, health data, etc.\n\n"
    output += "HIPAA (US -- Health Insurance Portability and Accountability Act)\n"
    output += "  Trigger:       Unsecured protected health information (PHI) breach\n"
    output += "  To HHS:        60 days from discovery\n"
    output += "  To subjects:   60 days from discovery\n\n"
    output += "PCI DSS (Payment Card Industry)\n"
    output += "  Trigger:       Cardholder data (card numbers, CVV, PIN) compromised\n"
    output += "  To card brands: Immediately upon suspicion\n\n"
    output += "CCPA (California Consumer Privacy Act)\n"
    output += "  Trigger:       California residents' non-encrypted personal data breached\n"
    output += "  To subjects:   Expedient time / without unreasonable delay\n"
    return output


def ir_reference(challenge_text: str = "") -> str:  # noqa: ARG001
    """Return the NIST SP 800-61 IR lifecycle phase reference table.

    Used by case05 (tools_type: "none"). Ignores challenge_text.

    Returns:
        Formatted IR phase reference table.
    """
    output = "IR PHASE REFERENCE — NIST SP 800-61\n\n"
    output += "PHASE 1: PREPARATION\n"
    output += "  Build IR capability before incidents occur.\n"
    output += "  Key actions: policies, playbooks, tools, training, IR team\n\n"
    output += "PHASE 2: DETECTION AND ANALYSIS\n"
    output += "  Identify and scope the incident.\n"
    output += "  Key actions: alert triage, log review, IOC identification,\n"
    output += "               severity rating, stakeholder notification\n\n"
    output += "PHASE 3: CONTAINMENT, ERADICATION, AND RECOVERY\n"
    output += "  Stop damage, remove attacker, restore operations.\n"
    output += "  Containment:  isolate systems, block malicious IPs, disable accounts\n"
    output += "  Eradication:  remove malware/tools, patch vulnerabilities, reset creds\n"
    output += "  Recovery:     restore from backups, verify integrity, monitor for recurrence\n\n"
    output += "PHASE 4: POST-INCIDENT ACTIVITY\n"
    output += "  Learn and improve.\n"
    output += "  Key actions: lessons learned meeting, final report, IOC sharing,\n"
    output += "               control gap analysis, playbook updates\n\n"
    output += "Current incident status maps to: PHASE 3 — ERADICATION\n"
    output += "(Tools removed, server isolated, backups verified)"
    return output


# ---------------------------------------------------------------------------
# Stage 3 — reference data (module-level, hardcoded)
# ---------------------------------------------------------------------------

_LOG_SOURCE_TABLE = [
    {"keywords": ["failed login", "authentication failure", "invalid password", "logon failure"],
     "source": "Windows Security Log (Event 4625) / Linux /var/log/auth.log",
     "reason": "Authentication failure event"},
    {"keywords": ["successful login", "accepted password", "logon success", "auth_success"],
     "source": "Windows Security Log (Event 4624) / Linux /var/log/auth.log",
     "reason": "Successful logon event"},
    {"keywords": ["account created", "new user", "useradd"],
     "source": "Windows Security Log (Event 4720) / Linux /var/log/auth.log",
     "reason": "Account creation event"},
    {"keywords": ["privilege escalation", "sudo", "elevated"],
     "source": "Linux /var/log/auth.log / Windows Security Log (Event 4672)",
     "reason": "Privilege escalation event"},
    {"keywords": ["process created", "new process", "cmd.exe", "powershell"],
     "source": "Windows Security Log (Event 4688) / Sysmon (Event 1)",
     "reason": "Process creation event"},
    {"keywords": ["network connection", "outbound connection", "outbound traffic", "port scan"],
     "source": "Firewall logs / Windows Security Log (Event 5156)",
     "reason": "Network connection event"},
    {"keywords": ["dns query", "domain lookup", "nslookup"],
     "source": "DNS server logs / Sysmon (Event 22)",
     "reason": "DNS query event"},
    {"keywords": ["file created", "file modified", "file deleted"],
     "source": "Windows Security Log (Event 4663) / Sysmon (Event 11)",
     "reason": "File access event"},
    {"keywords": ["web request", "http", "get /", "post /", "nginx", "apache"],
     "source": "Web server access logs (nginx/apache access.log)",
     "reason": "Web server event"},
    {"keywords": ["email sent", "email received", "smtp", "phishing"],
     "source": "Email gateway logs / Exchange logs",
     "reason": "Email event"},
    {"keywords": ["usb inserted", "usb device", "removable media", "device inserted", "device connected"],
     "source": "Windows Security Log (Event 6416) / udev logs",
     "reason": "Device connection event"},
    {"keywords": ["firewall blocked", "connection denied", "dropped packet"],
     "source": "Firewall logs / Windows Filtering Platform (Event 5157)",
     "reason": "Firewall block event"},
    {"keywords": ["vpn connected", "remote access", "tunnel established"],
     "source": "VPN gateway logs / RADIUS logs",
     "reason": "VPN connection event"},
    {"keywords": ["scheduled task", "schtasks", "task created"],
     "source": "Windows Security Log (Event 4698) / Linux /var/log/syslog",
     "reason": "Scheduled task creation event"},
    {"keywords": ["registry modified", "reg add", "regedit"],
     "source": "Windows Security Log (Event 4657) / Sysmon (Event 13)",
     "reason": "Registry modification event"},
]

_LOLBAS_TABLE = [
    {"keywords": ["powershell -enc", "powershell.exe -enc", "powershell -encodedcommand",
                  "powershell.exe -encodedcommand", "-nop -w hidden", "powershell -nop"],
     "technique": "T1059.001 — PowerShell encoded command (-enc/-EncodedCommand)",
     "note": "This is a classic LOLBAS indicator. Legitimate use is rare."},
    {"keywords": ["certutil -decode", "certutil.exe -decode", "certutil -urlcache", "certutil.exe -urlcache"],
     "technique": "T1105 — Ingress Tool Transfer via certutil",
     "note": "certutil -decode is a known file download/decode LOLBAS technique."},
    {"keywords": ["wmic process call create"],
     "technique": "T1047 — Windows Management Instrumentation",
     "note": "WMIC used to spawn processes remotely — LOLBAS technique."},
    {"keywords": ["regsvr32 /s", "regsvr32 /u"],
     "technique": "T1218.010 — Regsvr32 bypass",
     "note": "Signed binary proxy execution via regsvr32."},
    {"keywords": ["mshta vbscript", "mshta javascript"],
     "technique": "T1218.005 — Mshta bypass",
     "note": "Script execution via HTML Application host."},
    {"keywords": ["bitsadmin /transfer"],
     "technique": "T1197 — BITS Jobs",
     "note": "File transfer via Background Intelligent Transfer Service."},
    {"keywords": ["schtasks /create"],
     "technique": "T1053.005 — Scheduled Task",
     "note": "Persistence via scheduled task creation."},
    {"keywords": ["net use", "net share", "net localgroup"],
     "technique": "T1021 — Remote Services",
     "note": "Lateral movement via built-in net commands."},
    {"keywords": ["rundll32 javascript"],
     "technique": "T1218.011 — Rundll32 bypass",
     "note": "Code execution via DLL loader with JavaScript payload."},
    {"keywords": ["cmd /c echo", "cmd /c copy"],
     "technique": "T1059.003 — Windows Command Shell",
     "note": "Command shell used for payload staging."},
    {"keywords": ["currentversion\\run", "currentversion/run", "run key"],
     "technique": "T1547.001 — Boot/Logon Autostart: Registry Run Keys",
     "note": "Persistence via Run key — commonly set by LOLBAS scripts."},
]

_NORMAL_PATTERNS = [
    "svchost.exe -k",
    "parent=userinit.exe",
    "parent=services.exe",
    "lsass.exe",
    "csrss.exe",
]

_SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}

_PHASE_KEYWORDS = [
    ("Preparation", ["policy", "playbook", "training", "alert rule", "monitor"]),
    ("Detection",   ["alert", "anomaly", "detected", "identified", "flagged", "triggered"]),
    ("Containment", ["isolated", "blocked", "disabled", "contained", "quarantine"]),
    ("Eradication", ["removed", "deleted", "patched", "cleaned", "reimaged"]),
    ("Recovery",    ["restored", "verified", "monitoring", "normal operations", "returned"]),
]


# ---------------------------------------------------------------------------
# Stage 3 — Tool functions
# ---------------------------------------------------------------------------

def siem_correlator(challenge_text: str) -> str:
    """Evaluate log events against correlation rules; all matching rules fire."""
    normalized = challenge_text.replace("\\n", "\n")
    if "|||" not in normalized:
        return "SIEM CORRELATOR — error: input must be RULES|||EVENTS"

    rules_block, events_block = normalized.split("|||", 1)

    # Parse rules
    rules = []
    for line in rules_block.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) < 3:
            continue
        rule_id = parts[0].strip()
        cond_raw = parts[1].strip()
        severity_raw = parts[2].strip()
        if cond_raw.startswith("CONDITION:"):
            cond_raw = cond_raw[len("CONDITION:"):]
        severity = severity_raw.replace("SEVERITY:", "").strip().lower()
        tokens = [t.strip() for t in cond_raw.split(" AND ")]
        rules.append({"id": rule_id, "tokens": tokens, "severity": severity,
                      "raw_cond": cond_raw})

    # Parse events
    events = []
    for line in events_block.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        events.append({
            "timestamp": parts[0].strip(),
            "source":    parts[1].strip(),
            "event_type": parts[2].strip(),
            "details":   parts[3].strip(),
            "raw":       line,
        })

    output = "SIEM CORRELATOR — alert correlation engine\n\n"
    output += "Rules loaded: {}\n".format(len(rules))
    output += "Events to process: {}\n\n".format(len(events))
    output += "Evaluating events...\n\n"

    alerts = []
    no_alert_events = []

    for ev in events:
        fired_rules = []
        for rule in rules:
            match = True
            for token in rule["tokens"]:
                if "=" not in token:
                    match = False
                    break
                field, value = token.split("=", 1)
                field = field.strip()
                value = value.strip()
                if field == "event_type":
                    if ev["event_type"] != value:
                        match = False
                        break
                elif field == "details":
                    # Condition is details=VALUE — check if VALUE appears in details
                    if value not in ev["details"]:
                        match = False
                        break
                else:
                    # For other fields (source, user, etc.) check field=value as substring in details
                    if (field + "=" + value) not in ev["details"]:
                        match = False
                        break
            if match:
                fired_rules.append(rule)

        if fired_rules:
            for rule in fired_rules:
                cond_display = " | ".join(
                    t + " [check]" for t in rule["tokens"]
                )
                output += "[ALERT — {}] {} fired on event: {}\n".format(
                    rule["severity"].upper(), rule["id"], ev["timestamp"])
                output += "  Rule: {}\n".format(rule["raw_cond"])
                output += "  Event: {} | {} | {}\n".format(
                    ev["source"], ev["event_type"], ev["details"])
                output += "  Conditions matched: {}\n\n".format(cond_display)
                alerts.append(rule)
        else:
            no_alert_events.append(ev)

    for ev in no_alert_events:
        output += "No alert fired on: {}\n".format(ev["timestamp"])
        output += "  source={} — no rule conditions matched\n\n".format(ev["source"])

    if alerts:
        best = max(alerts, key=lambda r: _SEVERITY_ORDER.get(r["severity"], 0))
        output += "Summary: {} alert(s) fired | Highest severity: {} ({})".format(
            len(alerts), best["severity"].upper(), best["id"])
    else:
        output += "Summary: 0 alerts fired"

    return output


def log_classifier(challenge_text: str) -> str:
    """Map each event description line to its primary log source."""
    normalized = challenge_text.replace("\\n", "\n")
    lines = [l for l in normalized.split("\n") if l.strip()]

    output = "LOG CLASSIFIER — event source mapping\n\n"
    output += "Classifying {} event descriptions...\n\n".format(len(lines))

    for i, line in enumerate(lines, 1):
        lowered = line.lower()
        matched = None
        for entry in _LOG_SOURCE_TABLE:
            if any(kw in lowered for kw in entry["keywords"]):
                matched = entry
                break
        output += "[{}] {}\n".format(i, line)
        if matched:
            output += "    Primary source: {}\n".format(matched["source"])
            output += "    Reason: {}\n\n".format(matched["reason"])
        else:
            output += "    Primary source: Unknown — manual investigation required\n"
            output += "    Reason: No matching log source found — manual investigation required\n\n"

    output += "Classification complete. {}/{} events mapped to log sources.".format(
        len(lines), len(lines))
    return output


def hunt_analyzer(challenge_text: str) -> str:
    """Score evidence items against a threat hunting hypothesis."""
    normalized = challenge_text.replace("\\n", "\n")
    if "|||" not in normalized:
        return "HUNT ANALYZER — error: input must be HYPOTHESIS|||EVIDENCE"

    hypothesis, evidence_block = normalized.split("|||", 1)
    hypothesis = hypothesis.strip()

    items = []
    for line in evidence_block.split("\n"):
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            source, value = line.split(":", 1)
        else:
            source, value = "unknown", line
        items.append({"source": source.strip(), "value": value.strip()})

    output = "HUNT ANALYZER — hypothesis-driven threat hunt\n\n"
    output += "Hypothesis: {}\n".format(hypothesis)
    output += "Processing {} evidence items...\n\n".format(len(items))

    supports = 0
    refutes = 0
    neutral = 0

    for item in items:
        lowered = item["value"].lower()
        # Check LOLBAS reference
        lolbas_match = None
        for entry in _LOLBAS_TABLE:
            if any(kw in lowered for kw in entry["keywords"]):
                lolbas_match = entry
                break

        if lolbas_match:
            label = "[SUPPORTS]"
            supports += 1
            output += "{} {}: {}\n".format(label, item["source"], item["value"])
            output += "  Technique: {}\n".format(lolbas_match["technique"])
            output += "  {}\n\n".format(lolbas_match["note"])
        elif any(pat in lowered for pat in _NORMAL_PATTERNS):
            label = "[REFUTES]"
            refutes += 1
            output += "{} {}: {}\n".format(label, item["source"], item["value"])
            output += "  Normal Windows process — expected on all systems.\n\n"
        else:
            label = "[NEUTRAL]"
            neutral += 1
            output += "{} {}: {}\n".format(label, item["source"], item["value"])
            output += "  No strong signal for or against the hypothesis.\n\n"

    denom = supports + refutes
    confidence = int(supports / denom * 100) if denom > 0 else 0

    if confidence >= 75:
        assessment = "HIGH CONFIDENCE"
    elif confidence >= 50:
        assessment = "MODERATE CONFIDENCE"
    elif confidence >= 25:
        assessment = "LOW CONFIDENCE"
    else:
        assessment = "INSUFFICIENT EVIDENCE"

    output += "Results:\n"
    output += "  SUPPORTS: {} | REFUTES: {} | NEUTRAL: {}\n".format(
        supports, refutes, neutral)
    output += "  Confidence score: {} / ({} + {}) x 100 = {}%\n\n".format(
        supports, supports, refutes, confidence)
    output += "ASSESSMENT: {} — hypothesis is {}.".format(
        assessment,
        "well supported" if confidence >= 75
        else "supported but not conclusive" if confidence >= 50
        else "weakly supported" if confidence >= 25
        else "not supported by current evidence"
    )
    return output


def mem_analyzer(challenge_text: str) -> str:
    """Flag suspicious memory regions from a parsed memory map."""
    _MALICIOUS_NAMES = {
        "mimikatz", "meterpreter", "cobalt", "beacon",
        "cobaltstrike", "empire", "metasploit",
    }
    _SMALL_PROCS = {
        "svchost", "lsass", "csrss", "smss", "wininit", "winlogon",
    }

    normalized = challenge_text.replace("\\n", "\n")
    lines = [l for l in normalized.split("\n") if l.strip()]

    output = "MEM ANALYZER — memory forensics\n\n"
    output += "Scanning {} memory entries...\n\n".format(len(lines))

    findings = []
    summary_lines = []

    for line in lines:
        fields = {}
        for token in line.split():
            if ":" in token:
                k, v = token.split(":", 1)
                fields[k] = v

        # path may contain spaces — extract everything after "path:"
        path_start = line.find("path:")
        path_val = line[path_start + 5:].strip() if path_start != -1 else ""

        pid = fields.get("PID", "?")
        name = fields.get("name", "?")
        base = fields.get("base", "?")
        try:
            size = int(fields.get("size", "0"))
        except ValueError:
            size = 0
        perms = fields.get("permissions", "")

        name_lower = name.lower()

        # Flag priority
        if name_lower in _MALICIOUS_NAMES:
            flag = "[MALICIOUS]"
            reason = "Known malicious process name"
        elif "x" in perms and (
            path_val == "[anon]"
            or path_val.startswith("/tmp/")
            or path_val.startswith("/dev/shm/")
        ):
            flag = "[SUSPICIOUS]"
            reason = "Execute permission on anonymous region -- shellcode indicator"
        elif size > 50000 and name_lower in _SMALL_PROCS:
            flag = "[ANOMALY]"
            reason = "size={} unusually large for {} -- possible injection".format(
                size, name)
        else:
            flag = "[OK]"
            reason = "Normal"

        # Truncate path for display
        display_path = path_val if len(path_val) <= 30 else "..." + path_val[-27:]
        summary_lines.append("PID:{:<5} {:<12} {:<5} {:<32} {}{}".format(
            pid, name, perms, display_path, flag,
            " " + reason if flag != "[OK]" else " Normal process"))

        if flag != "[OK]":
            findings.append({
                "flag": flag, "pid": pid, "name": name,
                "base": base, "size": size, "reason": reason, "path": path_val,
            })

    for sl in summary_lines:
        output += sl + "\n"

    output += "\nFINDINGS:\n"
    if not findings:
        output += "  None -- no suspicious regions detected"
    else:
        for f in findings:
            output += "  {} PID {} -- '{}': {}\n".format(
                f["flag"], f["pid"], f["name"], f["reason"])
            output += "    Base: {} | Size: {} bytes\n".format(f["base"], f["size"])
            if f["flag"] == "[SUSPICIOUS]":
                output += "    Anonymous memory + executable = fileless malware / shellcode injection\n"
                output += "    Recommend: extract and analyze memory region with Volatility malfind\n"
            elif f["flag"] == "[ANOMALY]":
                output += "    Normal {} range: ~4000-20000 bytes\n".format(f["name"])
                output += "    Recommend: compare against known-good baseline\n"
            elif f["flag"] == "[MALICIOUS]":
                output += "    Recommend: immediately isolate process and dump memory\n"

    return output


def disk_analyzer(challenge_text: str) -> str:
    """Flag suspicious file system entries; sort by suspicion priority."""
    _MALICIOUS_NAMES = [
        "mimikatz", "meterpreter", "nc.exe", "ncat", "netcat",
        "pwdump", "fgdump", "wce.exe", "gsecdump",
    ]
    _SUSPICIOUS_PATHS = ["/tmp/", "/dev/shm/", "\\Temp\\", "\\AppData\\Local\\Temp\\"]
    _FLAG_ORDER = {"MALICIOUS": 0, "DELETED": 1, "TIMESTOMPED": 2, "SUSPICIOUS": 3, "OK": 4}

    normalized = challenge_text.replace("\\n", "\n")
    lines = [l for l in normalized.split("\n") if l.strip()]

    output = "DISK ANALYZER -- file system forensics\n\n"
    output += "Analyzing {} file entries...\n\n".format(len(lines))

    entries = []
    for line in lines:
        parts = line.split("|")
        if len(parts) < 7:
            continue
        filename = parts[0].strip()
        size = parts[1].strip()
        created = parts[2].strip()
        modified = parts[3].strip()
        accessed = parts[4].strip()
        deleted_field = parts[5].strip().lower().replace("deleted:", "")
        path = parts[6].strip()

        fn_lower = filename.lower()
        is_malicious = any(m in fn_lower for m in _MALICIOUS_NAMES)
        is_deleted = deleted_field == "yes"
        is_timestomped = modified < created  # ISO string comparison
        is_suspicious = any(sp in path for sp in _SUSPICIOUS_PATHS)

        if is_malicious:
            primary = "MALICIOUS"
        elif is_deleted:
            primary = "DELETED"
        elif is_timestomped:
            primary = "TIMESTOMPED"
        elif is_suspicious:
            primary = "SUSPICIOUS"
        else:
            primary = "OK"

        entries.append({
            "filename": filename, "size": size, "created": created,
            "modified": modified, "accessed": accessed,
            "deleted": is_deleted, "timestomped": is_timestomped,
            "path": path, "primary": primary,
        })

    # Sort by flag priority
    entries.sort(key=lambda e: _FLAG_ORDER[e["primary"]])

    counts = {k: 0 for k in _FLAG_ORDER}
    for e in entries:
        counts[e["primary"]] += 1

    for e in entries:
        flag = e["primary"]
        if flag == "MALICIOUS":
            output += "[MALICIOUS] {} -- known malicious tool\n".format(e["filename"])
            output += "  Size: {}B | Path: {}\n".format(e["size"], e["path"])
            if e["deleted"]:
                output += "  Status: DELETED (recovery possible from unallocated space)\n"
            if e["timestomped"]:
                # Extract date portion for display
                mod_date = e["modified"].split("T")[0] if "T" in e["modified"] else e["modified"]
                cre_date = e["created"].split("T")[0] if "T" in e["created"] else e["created"]
                output += "  TIMESTOMPED: modified={} < created={} (impossible -- timestamp manipulated)\n".format(
                    mod_date, cre_date)
        elif flag == "DELETED":
            output += "[DELETED] {}\n".format(e["filename"])
            output += "  Size: {}B | Path: {}\n".format(e["size"], e["path"])
            output += "  Created: {} | Timestamps consistent (no timestomping)\n".format(
                e["created"].split("T")[0] if "T" in e["created"] else e["created"])
            output += "  Recommend: recover from $MFT or unallocated space\n"
        elif flag == "TIMESTOMPED":
            output += "[TIMESTOMPED] {}\n".format(e["filename"])
            output += "  Size: {}B | Path: {}\n".format(e["size"], e["path"])
            mod_date = e["modified"].split("T")[0] if "T" in e["modified"] else e["modified"]
            cre_date = e["created"].split("T")[0] if "T" in e["created"] else e["created"]
            output += "  modified={} < created={} -- timestamps were altered\n".format(
                mod_date, cre_date)
        elif flag == "SUSPICIOUS":
            output += "[SUSPICIOUS] {}\n".format(e["filename"])
            output += "  Path: {} -- non-standard location\n".format(e["path"])
            output += "  Created: {}\n".format(e["created"])
        else:
            output += "[OK] {}\n".format(e["filename"])
            output += "  Path: {} -- legitimate system file\n".format(e["path"])

        output += "\n"

    output += "Summary: {} MALICIOUS | {} DELETED | {} TIMESTOMPED | {} SUSPICIOUS | {} OK\n".format(
        counts["MALICIOUS"], counts["DELETED"], counts["TIMESTOMPED"],
        counts["SUSPICIOUS"], counts["OK"])

    # Priority finding
    for e in entries:
        if e["primary"] != "OK":
            output += "Priority finding: {} -- {}".format(e["filename"], e["primary"])
            if e["deleted"] and e["primary"] == "MALICIOUS":
                output += " + DELETED + TIMESTOMPED" if e["timestomped"] else " + DELETED"
            break

    return output


def containment_advisor(challenge_text: str) -> str:
    """Score and rank containment options against scenario parameters."""
    params = {}
    for token in challenge_text.split("|"):
        token = token.strip()
        if ":" in token:
            k, v = token.split(":", 1)
            params[k.strip().lower()] = v.strip().lower()

    asset = params.get("asset", "unknown")
    threat = params.get("threat", "unknown")
    try:
        dwell = int(params.get("dwell", "0"))
    except ValueError:
        dwell = 0
    data_sens = params.get("data_sensitivity", "unknown")
    attribution = params.get("attribution", "unknown")

    # Score each option
    full_eff = 5
    full_tip = 5 if (attribution == "known" and dwell > 14) else 3
    net_eff = 4
    net_tip = 2
    mon_eff = 2
    mon_tip = 1
    acc_eff = 3
    acc_tip = 4 if attribution == "known" else 2

    options = [
        {"name": "Full Isolation (network + account lockout)",
         "short": "Full Isolation",
         "eff": full_eff, "tip": full_tip,
         "eff_desc": "stops all attacker access",
         "tip_desc": "attribution=known + dwell={} days (>14) = high reaction risk".format(dwell)
                     if attribution == "known" and dwell > 14
                     else "moderate tip-off risk",
         "note": "Risk: Nation-state actor with long dwell may trigger destructive payload upon detecting isolation."
                 if full_tip == 5 else
                 "Consider for threat=critical with short dwell time."},
        {"name": "Network Isolation (block outbound C2, maintain internal monitoring)",
         "short": "Network Isolation",
         "eff": net_eff, "tip": net_tip,
         "eff_desc": "cuts C2 channel, maintains visibility",
         "tip_desc": "appears as network issue, not obvious detection",
         "note": "Best balance for known APT with long dwell. Stops active exfiltration while preserving forensic collection."},
        {"name": "Monitoring Only",
         "short": "Monitoring Only",
         "eff": mon_eff, "tip": mon_tip,
         "eff_desc": "attacker continues operating",
         "tip_desc": "no tip-off",
         "note": "Risk: allows continued access to sensitive data." if data_sens in ("restricted", "confidential") else
                 "Best for early investigation phase with unknown actor."},
        {"name": "Account Lockout Only",
         "short": "Account Lockout Only",
         "eff": acc_eff, "tip": acc_tip,
         "eff_desc": "removes credential access",
         "tip_desc": "attribution=known, attacker monitors their accounts"
                     if attribution == "known" else "low tip-off risk",
         "note": "Attacker may have non-credential persistence mechanisms after long dwell."
                 if dwell > 14 else "Effective when attacker relies solely on credential access."},
    ]

    # Rank: highest net score first; tie-break: lower tip_risk
    def sort_key(o):
        return (-(o["eff"] - o["tip"]), o["tip"])

    ranked = sorted(options, key=sort_key)
    top = ranked[0]

    output = "CONTAINMENT ADVISOR -- strategy recommendation\n\n"
    output += "Input parameters:\n"
    output += "  Asset:            {}\n".format(asset)
    output += "  Threat level:     {}\n".format(threat)
    output += "  Dwell time:       {} days\n".format(dwell)
    output += "  Data sensitivity: {}\n".format(data_sens)
    output += "  Attribution:      {}\n\n".format(attribution)
    output += "Scoring containment options (effectiveness - tip_risk = net score)...\n\n"

    for i, opt in enumerate(options, 1):
        net = opt["eff"] - opt["tip"]
        marker = "   <- RECOMMENDED" if opt["short"] == top["short"] else ""
        output += "OPTION {}: {}\n".format(i, opt["name"])
        output += "  Effectiveness:  {}/5 -- {}\n".format(opt["eff"], opt["eff_desc"])
        output += "  Tip-off risk:   {}/5 -- {}\n".format(opt["tip"], opt["tip_desc"])
        output += "  Net score:      {}{}  \n".format(net, marker)
        output += "  {}\n\n".format(opt["note"])

    output += "RECOMMENDATION: {}\n".format(top["short"])
    output += "  {}\n".format(top["note"])
    if top["short"] == "Network Isolation":
        output += "  Block all outbound connections from the asset.\n"
        output += "  Maintain internal monitoring and log collection.\n"
        output += "  Brief legal and executive team before executing."

    return output


def timeline_builder(challenge_text: str) -> str:
    """Sort timeline events, annotate gaps, label IR phases."""
    _TS_FMT = "%Y-%m-%dT%H:%M:%S"

    normalized = challenge_text.replace("\\n", "\n")
    lines = [l for l in normalized.split("\n") if l.strip()]

    events = []
    sources = set()
    for line in lines:
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        ts_str = parts[0].strip()
        source = parts[1].strip()
        desc = parts[2].strip()
        try:
            dt = datetime.datetime.strptime(ts_str, _TS_FMT)
        except ValueError:
            continue
        sources.add(source)
        events.append({"ts": ts_str, "dt": dt, "source": source, "desc": desc})

    events.sort(key=lambda e: e["ts"])

    def _label_phase(desc):
        desc_lower = desc.lower()
        for phase, keywords in _PHASE_KEYWORDS:
            if any(kw in desc_lower for kw in keywords):
                return phase
        return "Unknown"

    output = "TIMELINE BUILDER -- incident reconstruction\n\n"
    output += "Sorting {} events from {} sources...\n\n".format(
        len(events), len(sources))

    phase_starts = {}
    last_dt = None
    largest_gap_seconds = 0
    largest_gap_label = ""

    for ev in events:
        # Gap check
        if last_dt is not None:
            diff = int((ev["dt"] - last_dt).total_seconds())
            if diff > 3600:
                h = diff // 3600
                m = (diff % 3600) // 60
                gap_label = "{}h {}m".format(h, m)
                output += "[GAP: {} -- no recorded activity]\n\n".format(gap_label)
                if diff > largest_gap_seconds:
                    largest_gap_seconds = diff
                    largest_gap_label = gap_label
        last_dt = ev["dt"]

        phase = _label_phase(ev["desc"])
        if phase not in phase_starts:
            phase_starts[phase] = ev["ts"]

        output += "[{:<11}] {}  {:<10}  {}\n".format(
            phase, ev["ts"], ev["source"], ev["desc"])

    # Phase summary
    output += "\nPhase summary:\n"
    phase_order = ["Preparation", "Detection", "Containment", "Eradication", "Recovery", "Unknown"]
    for p in phase_order:
        if p in phase_starts and p != "Unknown":
            output += "  {} phase started:    {}\n".format(p, phase_starts[p])

    # Dwell time: first event to first Containment (or last event)
    if events:
        first_dt = events[0]["dt"]
        contain_ts = phase_starts.get("Containment")
        if contain_ts:
            end_dt = datetime.datetime.strptime(contain_ts, _TS_FMT)
        else:
            end_dt = events[-1]["dt"]
        dwell_secs = int((end_dt - first_dt).total_seconds())
        dwell_h = round(dwell_secs / 3600)
        dwell_days = round(dwell_h / 24, 1)
        output += "  Total dwell time:           ~{} hours ({} days)\n".format(
            dwell_h, dwell_days)

    if largest_gap_label:
        output += "  Largest gap:                {} (attacker dormancy period)".format(
            largest_gap_label)

    return output


def coc_reference(challenge_text: str = "") -> str:
    """Return the static chain of custody reference table. Input ignored."""
    return (
        "CHAIN OF CUSTODY REFERENCE -- digital evidence handling\n\n"
        "STEP 1: DOCUMENT THE SCENE\n"
        "  Photograph evidence in place before touching anything.\n"
        "  Record: location, date, time, who discovered it, system state.\n\n"
        "STEP 2: HASH THE EVIDENCE (CRITICAL -- DO THIS FIRST)\n"
        "  Generate SHA-256 (preferred) or MD5 hash of the original evidence.\n"
        "  Record the hash in the evidence log.\n"
        "  This is the integrity baseline -- proves evidence was not altered.\n\n"
        "STEP 3: USE WRITE BLOCKERS\n"
        "  For physical drives: attach write blocker before connecting to analysis system.\n"
        "  Write blockers prevent any data from being written to the evidence drive.\n"
        "  Without a write blocker, simply connecting a drive modifies timestamps.\n\n"
        "STEP 4: CREATE FORENSIC COPIES\n"
        "  Image the evidence using FTK Imager, dd, or similar tool.\n"
        "  Verify copy hash matches original hash.\n"
        "  Analyze only the forensic copy -- NEVER the original.\n\n"
        "STEP 5: SEAL AND STORE ORIGINALS\n"
        "  Place physical evidence in tamper-evident evidence bags.\n"
        "  Label with: case number, exhibit number, collector name, date/time.\n"
        "  Store in secured evidence room with access log.\n\n"
        "DOCUMENTATION REQUIREMENTS (each custody transfer):\n"
        "  Transferring party: name, role, signature\n"
        "  Receiving party: name, role, signature\n"
        "  Date and time of transfer\n"
        "  Reason for transfer\n"
        "  Evidence description and hash value\n"
        "  Storage location before and after\n\n"
        "COMMON ERRORS TO AVOID:\n"
        "  - Analyzing originals (use forensic copies)\n"
        "  - No write blocker during imaging (modifies evidence)\n"
        "  - Missing hash at collection (cannot prove integrity)\n"
        "  - Undocumented transfers (breaks chain)\n"
        "  - Unauthorized access (chain is broken)"
    )


# ---------------------------------------------------------------------------
# Stage 4 tool functions — Domain 2 (Vulnerability Management)
# ---------------------------------------------------------------------------

def vuln_prioritizer(challenge_text: str) -> str:
    """Score and rank CVEs using CVSS + contextual bonuses.

    Input: newline-separated lines: cve_id|cvss|asset_criticality|internet_facing|exploit_available|patch_available
    Scoring: CVSS + asset_bonus(critical=3,high=2,medium=1,low=0) + exploit_bonus(+2) + internet_bonus(+2)
    """
    lines = [l for l in challenge_text.split("\n") if l.strip()]
    asset_bonus_map = {"critical": 3, "high": 2, "medium": 1, "low": 0}

    entries = []
    for line in lines:
        parts = line.split("|")
        if len(parts) < 6:
            continue
        cve_id, cvss_str, asset_crit, internet_facing, exploit_avail, patch_avail = (
            parts[0].strip(), parts[1].strip(), parts[2].strip().lower(),
            parts[3].strip().lower(), parts[4].strip().lower(), parts[5].strip().lower()
        )
        try:
            score = float(cvss_str)
        except ValueError:
            continue
        score += asset_bonus_map.get(asset_crit, 0)
        score += 2 if exploit_avail == "yes" else 0
        score += 2 if internet_facing == "yes" else 0
        entries.append({
            "cve_id": cve_id,
            "cvss": float(cvss_str),
            "asset_crit": asset_crit,
            "internet_facing": internet_facing,
            "exploit_avail": exploit_avail,
            "score": score,
        })

    # Sort by score descending, preserve input order for ties
    entries.sort(key=lambda e: e["score"], reverse=True)

    output = "VULN PRIORITIZER -- contextual risk scoring\n\n"
    output += f"CVEs analyzed: {len(entries)}\n\n"

    for rank, e in enumerate(entries, 1):
        ab = asset_bonus_map.get(e["asset_crit"], 0)
        eb = 2 if e["exploit_avail"] == "yes" else 0
        ib = 2 if e["internet_facing"] == "yes" else 0
        output += f"[RANK {rank}] {e['cve_id']}\n"
        output += f"  CVSS base score:   {e['cvss']}\n"
        output += f"  Asset criticality: {e['asset_crit']} (+{ab})\n"
        output += f"  Exploit available: {e['exploit_avail']} (+{eb})\n"
        output += f"  Internet facing:   {e['internet_facing']} (+{ib})\n"
        output += f"  Contextual score -> {e['score']:.1f}\n\n"

    if entries:
        top = entries[0]
        output += f"Top priority: {top['cve_id']} (score: {top['score']:.1f})\n"
        output += "Patch immediately -- highest contextual risk in backlog."

    return output


def patch_reference(_challenge_text: str) -> str:
    """Static patch management reference. Input ignored."""
    return (
        "PATCH REFERENCE -- patch management guide\n\n"
        "PATCH INHIBITORS (reasons a patch may not be immediately applicable):\n"
        "  Business continuity   -- system cannot be taken offline (production critical)\n"
        "  Operational constraint -- patch breaks dependent functionality\n"
        "  Legacy dependency     -- incompatible with other installed software\n"
        "  Vendor limitation     -- vendor has not certified the patch\n"
        "  Testing requirement   -- enterprise policy requires test validation first\n\n"
        "REMEDIATION ALTERNATIVES when patching is blocked:\n\n"
        "  Compensating control  -- security measure that reduces exploitation risk\n"
        "                           without applying the patch directly\n"
        "                           Examples: disable vulnerable feature, access restriction,\n"
        "                           enhanced monitoring, rate limiting\n\n"
        "  Virtual patching      -- WAF or IPS rule blocks exploitation at network layer\n"
        "                           without modifying the endpoint\n\n"
        "  Network segmentation  -- isolate vulnerable system to reduce attacker reach\n"
        "                           Firewall rules, VLANs, or micro-segmentation\n\n"
        "  Enhanced monitoring   -- alert on exploitation indicators for the CVE\n"
        "                           (process names, network patterns, file paths)\n\n"
        "  Risk acceptance       -- formally document the residual risk with CISO sign-off\n"
        "                           Requires: justification, compensating controls, review date\n\n"
        "PATCH EXCEPTION PROCESS:\n"
        "  1. Document inhibitor and business justification\n"
        "  2. Risk assessment (likelihood x impact with compensating controls)\n"
        "  3. CISO approval and formal sign-off\n"
        "  4. Implement compensating controls\n"
        "  5. Set mandatory review date (30/60/90 days)\n"
        "  6. Track in vulnerability management platform\n\n"
        "Key principle: A vulnerability without a patch is still a managed risk.\n"
        "Risk acceptance requires formal documentation -- not informal agreement."
    )


def surface_analyzer(challenge_text: str) -> str:
    """Flag internet-exposed services with no business justification.

    Input: newline-separated lines: service_name|port|protocol|internet_facing|required|category
    Flag [REDUCE] if internet_facing=yes AND required=no.
    """
    lines = [l for l in challenge_text.split("\n") if l.strip()]

    reduce_list = []
    ok_list = []

    for line in lines:
        parts = line.split("|")
        if len(parts) < 6:
            continue
        svc, port, proto, internet_facing, required, category = (
            parts[0].strip(), parts[1].strip(), parts[2].strip(),
            parts[3].strip().lower(), parts[4].strip().lower(), parts[5].strip()
        )
        if internet_facing == "yes" and required == "no":
            reduce_list.append((svc, port, proto, internet_facing, required, category))
        else:
            ok_list.append((svc, port, proto, internet_facing, required, category))

    total = len(reduce_list) + len(ok_list)
    output = "SURFACE ANALYZER -- attack surface mapping\n\n"
    output += f"Services analyzed: {total}\n\n"

    for svc, port, proto, iface, req, cat in reduce_list:
        output += f"[REDUCE] {svc} (port {port}/{proto})\n"
        output += f"  Category:        {cat}\n"
        output += f"  Internet-facing: {iface} | Required: {req}\n"
        output += "  Action: Remove from internet exposure -- no business justification\n\n"

    for svc, port, proto, iface, req, cat in ok_list:
        output += f"[OK] {svc} (port {port}/{proto})\n"
        output += f"  Category:        {cat}\n"
        output += f"  Internet-facing: {iface} | Required: {req}\n\n"

    output += f"Summary: {len(reduce_list)} services flagged for removal ([REDUCE])\n"
    output += f"         {len(ok_list)} services acceptable ([OK])\n"
    output += "Attack surface: remove or firewall-restrict all [REDUCE] services."

    return output


# Embedded CWE name reference for sast_analyzer
_CWE_NAMES: dict = {
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

_SEVERITY_RANK: dict = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def sast_analyzer(challenge_text: str) -> str:
    """Sort SAST findings by severity; identify top finding by CWE.

    Input: newline-separated lines: filename|line|cwe_id|severity|description
    """
    lines = [l for l in challenge_text.split("\n") if l.strip()]

    findings = []
    for line in lines:
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        filename, lineno, cwe_id, severity, description = (
            parts[0].strip(), parts[1].strip(), parts[2].strip().upper(),
            parts[3].strip().lower(), parts[4].strip()
        )
        findings.append({
            "filename": filename,
            "lineno": lineno,
            "cwe_id": cwe_id,
            "severity": severity,
            "description": description,
            "rank": _SEVERITY_RANK.get(severity, 0),
        })

    # Sort by severity rank descending; stable sort preserves input order within same rank
    findings.sort(key=lambda f: f["rank"], reverse=True)

    output = "SAST ANALYZER -- static analysis findings\n\n"
    output += f"Findings analyzed: {len(findings)}\n\n"

    for f in findings:
        label = f["severity"].upper()
        cwe_name = _CWE_NAMES.get(f["cwe_id"], "Unknown CWE")
        output += f"[{label}] {f['filename']}:{f['lineno']} -- {f['cwe_id']} ({cwe_name})\n"
        output += f"  Description: {f['description']}\n\n"

    if findings:
        top = findings[0]
        cwe_name = _CWE_NAMES.get(top["cwe_id"], "Unknown CWE")
        output += f"Top finding: {top['cwe_id']} ({cwe_name}) in {top['filename']} line {top['lineno']}\n"
        output += f"Severity: {top['severity'].upper()} -- remediate immediately."

    return output


def intel_correlator(challenge_text: str) -> str:
    """Assign threat intel tiers to CVEs; rank for remediation.

    Input: newline-separated lines: cve_id|cvss|exploited_in_wild|poc_available|apt_linked
    Tiers: IMMEDIATE > ELEVATED > MONITOR > ROUTINE. CVSS tie-break within tier.
    """
    lines = [l for l in challenge_text.split("\n") if l.strip()]

    tier_order = {"IMMEDIATE": 0, "ELEVATED": 1, "MONITOR": 2, "ROUTINE": 3}
    entries = []

    for line in lines:
        parts = line.split("|")
        if len(parts) < 5:
            continue
        cve_id, cvss_str, wild, poc, apt = (
            parts[0].strip(), parts[1].strip(),
            parts[2].strip().lower(), parts[3].strip().lower(), parts[4].strip().lower()
        )
        try:
            cvss = float(cvss_str)
        except ValueError:
            cvss = 0.0

        if wild == "yes":
            tier = "IMMEDIATE"
        elif poc == "yes":
            tier = "ELEVATED"
        elif apt == "yes":
            tier = "MONITOR"
        else:
            tier = "ROUTINE"

        entries.append({
            "cve_id": cve_id, "cvss": cvss,
            "wild": wild, "poc": poc, "apt": apt,
            "tier": tier,
        })

    # Sort by tier order asc, then CVSS desc within tier
    entries.sort(key=lambda e: (tier_order[e["tier"]], -e["cvss"]))

    _tier_action = {
        "IMMEDIATE": "Patch within 24-48 hours -- active exploitation confirmed.",
        "ELEVATED":  "Patch within 7 days -- public exploit code available.",
        "MONITOR":   "Schedule patch -- APT actor interest noted.",
        "ROUTINE":   "Patch by next cycle -- no active exploitation.",
    }

    output = "INTEL CORRELATOR -- threat-prioritized vulnerability ranking\n\n"
    output += f"CVEs analyzed: {len(entries)}\n\n"

    for e in entries:
        output += f"[{e['tier']}] {e['cve_id']} (CVSS: {e['cvss']})\n"
        output += (f"  Exploited in wild: {e['wild'].upper()} | "
                   f"PoC available: {e['poc'].upper()} | "
                   f"APT-linked: {e['apt'].upper()}\n")
        output += f"  Action: {_tier_action[e['tier']]}\n\n"

    # Note if highest-CVSS CVE is not IMMEDIATE
    if entries:
        highest_cvss_entry = max(entries, key=lambda e: e["cvss"])
        if highest_cvss_entry["tier"] != "IMMEDIATE":
            output += (f"Note: {highest_cvss_entry['cve_id']} has highest CVSS "
                       f"({highest_cvss_entry['cvss']}) but is [{highest_cvss_entry['tier']}] tier.\n"
                       "Threat intelligence overrides CVSS-only prioritization.")

    return output


# ---------------------------------------------------------------------------
# Stage 4 tool functions — Domain 4 (Reporting & Communication)
# ---------------------------------------------------------------------------

def metrics_calculator(challenge_text: str) -> str:
    """Compute MTTD and MTTR averages from incident timestamp data.

    Input: newline-separated lines: incident_id|compromised_at|detected_at|resolved_at
    MTTD = avg hours from compromised to detected. MTTR = avg hours from detected to resolved.
    """
    lines = [l for l in challenge_text.split("\n") if l.strip()]
    fmt = "%Y-%m-%dT%H:%M:%S"

    rows = []
    for line in lines:
        parts = line.split("|")
        if len(parts) < 4:
            continue
        inc_id = parts[0].strip()
        try:
            compromised = datetime.datetime.strptime(parts[1].strip(), fmt)
            detected    = datetime.datetime.strptime(parts[2].strip(), fmt)
            resolved    = datetime.datetime.strptime(parts[3].strip(), fmt)
        except ValueError:
            continue
        mttd_i = (detected - compromised).total_seconds() / 3600
        mttr_i = (resolved - detected).total_seconds() / 3600
        rows.append({"id": inc_id, "mttd": mttd_i, "mttr": mttr_i})

    output = "METRICS CALCULATOR -- security performance metrics\n\n"
    output += f"Incidents analyzed: {len(rows)}\n\n"

    if not rows:
        output += "No valid incident data found."
        return output

    output += "Incident breakdown:\n"
    for r in rows:
        output += f"  {r['id']:>8}:  MTTD = {r['mttd']:6.2f}h | MTTR = {r['mttr']:6.2f}h\n"

    mttd_avg = round(sum(r["mttd"] for r in rows) / len(rows))
    mttr_avg = round(sum(r["mttr"] for r in rows) / len(rows))

    output += "\nAggregate metrics:\n"
    output += f"  Mean Time to Detect (MTTD): {mttd_avg} hours\n"
    output += f"  Mean Time to Respond (MTTR): {mttr_avg:>2} hours\n\n"
    output += "Note: MTTD measures detection effectiveness. Lower -> better.\n"
    output += "Note: MTTR measures response effectiveness. Lower -> better."

    # Outlier note: if max MTTD > 3x median MTTD
    if len(rows) >= 2:
        mttd_list = sorted(r["mttd"] for r in rows)
        median_mttd = mttd_list[len(mttd_list) // 2]
        max_mttd = mttd_list[-1]
        if median_mttd > 0 and max_mttd > 3 * median_mttd:
            outlier = max(rows, key=lambda r: r["mttd"])
            output += f"\nNote: {outlier['id']} is a significant outlier ({outlier['mttd']:.0f}h MTTD) -- skews the average upward."

    return output


def compliance_mapper(challenge_text: str) -> str:
    """Map controls to NIST CSF functions; compute gap percentage per function.

    Input: newline-separated lines: control_id|nist_function|implemented
    """
    lines = [l for l in challenge_text.split("\n") if l.strip()]

    # Build per-function counts
    func_counts: dict = {}
    for line in lines:
        parts = line.split("|")
        if len(parts) < 3:
            continue
        func = parts[1].strip().upper()
        impl = parts[2].strip().lower()
        if func not in func_counts:
            func_counts[func] = {"yes": 0, "total": 0}
        func_counts[func]["total"] += 1
        if impl == "yes":
            func_counts[func]["yes"] += 1

    total_controls = sum(v["total"] for v in func_counts.values())

    # Compute pct and label per function
    results = []
    for func, counts in func_counts.items():
        pct = round((counts["yes"] / counts["total"]) * 100) if counts["total"] > 0 else 0
        if pct == 100:
            label = "[MET]"
        elif pct >= 75:
            label = "[MINOR GAP]"
        elif pct >= 50:
            label = "[MODERATE GAP]"
        else:
            label = "[CRITICAL GAP]"
        results.append({"func": func, "yes": counts["yes"], "total": counts["total"],
                        "pct": pct, "label": label})

    # Sort by pct ascending, then alphabetically for ties
    results.sort(key=lambda r: (r["pct"], r["func"]))

    output = "COMPLIANCE MAPPER -- NIST CSF gap analysis\n\n"
    output += f"Controls analyzed: {total_controls}\n\n"
    output += "NIST CSF compliance by function (largest gap first):\n\n"

    for r in results:
        output += (f"{r['label']:<16} {r['func']:<9} "
                   f"{r['yes']:>2}/{r['total']:>2} controls implemented ({r['pct']}%)\n")

    if results:
        top_gap = results[0]
        output += f"\nTop priority gap: {top_gap['func']} ({top_gap['pct']}%)\n"
        output += "Recommended action: Develop recovery plans, document BCP, test annually."

    return output


def sla_tracker(challenge_text: str) -> str:
    """Flag SLA breaches and compute adherence rate.

    Input: newline-separated lines: ticket_id|priority|opened_at|resolved_at|sla_hours
    """
    lines = [l for l in challenge_text.split("\n") if l.strip()]
    fmt = "%Y-%m-%dT%H:%M:%S"

    tickets = []
    for line in lines:
        parts = line.split("|")
        if len(parts) < 5:
            continue
        tkt_id, priority, opened_str, resolved_str, sla_str = (
            parts[0].strip(), parts[1].strip(),
            parts[2].strip(), parts[3].strip(), parts[4].strip()
        )
        try:
            opened   = datetime.datetime.strptime(opened_str, fmt)
            resolved = datetime.datetime.strptime(resolved_str, fmt)
            sla_h    = float(sla_str)
        except ValueError:
            continue
        elapsed = (resolved - opened).total_seconds() / 3600
        status = "[MET]" if elapsed <= sla_h else "[BREACHED]"
        tickets.append({
            "id": tkt_id, "priority": priority,
            "elapsed": elapsed, "sla": sla_h, "status": status,
        })

    met_count = sum(1 for t in tickets if t["status"] == "[MET]")
    total = len(tickets)
    adherence = round((met_count / total) * 100) if total > 0 else 0

    output = "SLA TRACKER -- incident response SLA adherence\n\n"
    output += f"Tickets analyzed: {total}\n\n"

    for t in tickets:
        output += (f"  {t['id']:<8} {t['priority'].upper():<9} "
                   f"{t['elapsed']:6.1f}h elapsed / {t['sla']:4.0f}h SLA -> {t['status']}\n")

    output += "\nSummary:\n"
    output += f"  Tickets meeting SLA:    {met_count} / {total}\n"
    output += f"  Tickets breaching SLA:  {total - met_count} / {total}\n"
    output += f"  SLA adherence rate:     {adherence}%"

    return output


def lessons_reference(_challenge_text: str) -> str:
    """Static post-incident lessons learned reference. Input ignored."""
    return (
        "LESSONS REFERENCE -- post-incident lessons learned guide\n\n"
        "PRIMARY GOAL: Prevent recurrence through root cause analysis.\n"
        "  Every section of the lessons learned document serves this goal:\n"
        "  understand WHY it happened so the same attack cannot succeed again.\n\n"
        "ROOT CAUSE CATEGORIES:\n"
        "  Technical failure   -- security control failed or was misconfigured\n"
        "  Process gap         -- procedure was missing or not followed\n"
        "  Human error         -- analyst missed indicator or made configuration mistake\n"
        "  Detection failure   -- log source missing or detection rule not present\n"
        "  Response gap        -- slow escalation or communication failure\n\n"
        "LESSONS LEARNED DOCUMENT STRUCTURE:\n"
        "  1. Incident summary      -- what happened, when, scope, impact\n"
        "  2. Timeline              -- reconstructed from multi-source evidence\n"
        "  3. Root cause            -- primary cause and contributing factors\n"
        "  4. What went well        -- preserve effective practices\n"
        "  5. What failed           -- gaps in detection, response, or controls\n"
        "  6. Corrective actions    -- specific items with owner and target date\n"
        "  7. Metrics               -- MTTD, MTTR, containment time, total impact\n"
        "  8. Approvals             -- IR lead and CISO sign-off required\n\n"
        "KEY METRICS REVIEWED:\n"
        "  MTTD (Mean Time to Detect)    -- detection effectiveness\n"
        "  MTTR (Mean Time to Respond)   -- response effectiveness\n"
        "  Containment time              -- time from detection to containment\n"
        "  Eradication time              -- time to remove all attacker artifacts\n"
        "  Total dwell time              -- initial access to full containment\n\n"
        "DISTRIBUTION:\n"
        "  IR team, security management, affected business units, legal (if applicable)\n\n"
        "Blameless principle: focus on systems and processes, not individuals.\n"
        "Blame inhibits honest reporting. The goal is improvement, not punishment."
    )


_EXECUTIVE_KEYWORDS = [
    "risk_reduction", "compliance", "critical", "breach", "sla_adherence", "open"
]


def dashboard_filter(challenge_text: str) -> str:
    """Classify metrics as executive-appropriate or operational-only.

    Input: newline-separated lines: metric_name|value
    Executive: outcome-focused. Operational: process-focused (default).
    """
    lines = [l for l in challenge_text.split("\n") if l.strip()]

    executive = []
    operational = []

    for line in lines:
        parts = line.split("|", 1)
        if len(parts) < 2:
            continue
        metric_name = parts[0].strip()
        value = parts[1].strip()
        name_lower = metric_name.lower()

        label = "[OPERATIONAL]"
        for kw in _EXECUTIVE_KEYWORDS:
            if kw in name_lower:
                label = "[EXECUTIVE]"
                break

        if label == "[EXECUTIVE]":
            executive.append((metric_name, value))
        else:
            operational.append((metric_name, value))

    output = "DASHBOARD FILTER -- executive vs operational metric classification\n\n"
    output += f"Metrics analyzed: {len(executive) + len(operational)}\n\n"

    for name, val in executive:
        output += f"[EXECUTIVE] {name}: {val}\n"

    if executive and operational:
        output += "\n"

    for name, val in operational:
        output += f"[OPERATIONAL] {name}: {val}\n"

    output += f"\nExecutive dashboard:  {len(executive)} metrics (outcome-focused -- answers \"are we safer?\")\n"
    output += f"Operational dashboard: {len(operational)} metrics (process-focused -- answers \"how is the team performing?\")"

    return output


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_DISPATCH: dict = {
    "log_filter":       log_filter,
    "ioc_classifier":   ioc_classifier,
    "vuln_scorer":      vuln_scorer,
    "process_analyzer": process_analyzer,
    "none":             ir_reference,
    "traffic_analyzer": traffic_analyzer,
    "ioc_hunter":       ioc_hunter,
    "attack_mapper":    attack_mapper,
    "rule_analyzer":    rule_analyzer,
    "risk_scorer":          risk_scorer,
    "remediation_planner":   remediation_planner,
    "exec_reference":        exec_reference,
    "notification_reference": notification_reference,
    "siem_correlator":    siem_correlator,
    "log_classifier":     log_classifier,
    "hunt_analyzer":      hunt_analyzer,
    "mem_analyzer":       mem_analyzer,
    "disk_analyzer":      disk_analyzer,
    "coc_reference":      coc_reference,
    "containment_advisor": containment_advisor,
    "timeline_builder":   timeline_builder,
    "vuln_prioritizer":   vuln_prioritizer,
    "patch_reference":    patch_reference,
    "surface_analyzer":   surface_analyzer,
    "sast_analyzer":      sast_analyzer,
    "intel_correlator":   intel_correlator,
    "metrics_calculator": metrics_calculator,
    "compliance_mapper":  compliance_mapper,
    "sla_tracker":        sla_tracker,
    "lessons_reference":  lessons_reference,
    "dashboard_filter":   dashboard_filter,
}


def run_tool(tools_type: str, challenge_text: str) -> str:
    """Dispatch to the correct tool function by tools_type string.

    Args:
        tools_type: The tools_type value from the case JSON.
        challenge_text: The challenge_data value passed to the tool.

    Returns:
        Formatted tool output string, or error message if unknown type.
    """
    fn = _DISPATCH.get(tools_type)
    if fn is None:
        return "Unknown tool type."
    return fn(challenge_text)
