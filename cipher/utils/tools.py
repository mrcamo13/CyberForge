"""tools.py — CIPHER CyberForge

In-game tool functions dispatched by tools_type field in operation JSON.
All tool functions return a formatted string for display.
Engine passes op_data["challenge_data"] as the input to each tool.
"""

import base64
import hashlib
import re


# ---------------------------------------------------------------------------
# Tool command aliases
#
# Maps tools_type -> [primary_command, ...extra_aliases]
# The FIRST entry is displayed in the UI ("Type 'nmap' to run the scanner").
# ALL entries (plus the generic 'tools') are accepted in the command loop.
# ---------------------------------------------------------------------------
_TOOL_COMMANDS: dict = {
    "caesar_decoder": ["caesar", "decode"],
    "base64_decoder": ["base64"],
    "port_scanner":   ["nmap"],
    "log_analyzer":   ["grep", "log-search"],
    "hash_cracker":   ["hashcat", "john"],
    "dir_enumerator": ["gobuster", "dirb"],
    "sqli_tester":    ["sqlmap"],
    "suid_scanner":   ["find-suid"],
}


def get_tool_commands(tools_type: str) -> list:
    """Return accepted command aliases for a tools_type.

    The first item is the primary display command shown to the player.
    Returns an empty list for unknown types.
    """
    return _TOOL_COMMANDS.get(tools_type, [])


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def run_tool(tools_type: str, challenge_text: str) -> str:
    """Dispatch to the correct tool function by tools_type string.

    Returns the formatted output string, or an error message if the
    tools_type is not recognized.
    """
    _dispatch = {
        "caesar_decoder": caesar_decoder,
        "base64_decoder": base64_decoder,
        "port_scanner":   port_scanner,
        "log_analyzer":   log_analyzer,
        "hash_cracker":   hash_cracker,
        "dir_enumerator": dir_enumerator,
        "sqli_tester":    sqli_tester,
        "suid_scanner":   suid_scanner,
    }
    fn = _dispatch.get(tools_type)
    if fn is None:
        return "Unknown tool type."
    return fn(challenge_text)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def caesar_decoder(text: str) -> str:
    """Try all 26 Caesar shifts on the given uppercase text.

    Returns a formatted multi-line string with one result per shift.
    Marks the shift that produces an all-alpha result (no digits) with <--.
    Handles uppercase only — preserves spaces and non-alpha chars.
    """
    lines = [f"CAESAR DECODER — trying all 26 shifts on: {text.upper()}", ""]
    upper = text.upper()

    for shift in range(1, 27):
        decoded_chars = []
        for ch in upper:
            if ch.isalpha():
                decoded_chars.append(chr((ord(ch) - 65 - shift) % 26 + 65))
            else:
                decoded_chars.append(ch)
        decoded = "".join(decoded_chars)

        # Mark shift if result is all alphabetic (no digits, no specials)
        alpha_only = all(c.isalpha() or c == " " for c in decoded)
        marker = "  <--" if alpha_only else ""
        lines.append(f"Shift {shift:02d}: {decoded}{marker}")

    return "\n".join(lines)


def base64_decoder(text: str) -> str:
    """Decode a Base64 string and display the result.

    text: the Base64 encoded string from challenge_data.
    Returns formatted output showing input and decoded output.
    """
    text = text.strip()
    try:
        decoded = base64.b64decode(text).decode("utf-8")
        return (
            f"BASE64 DECODER\n"
            f"Input:  {text}\n"
            f"Output: {decoded}\n\n"
            f"Decoded successfully. Input was valid Base64."
        )
    except Exception:
        return (
            f"BASE64 DECODER\n"
            f"Input:  {text}\n\n"
            f"Error: Input is not valid Base64."
        )


def port_scanner(target: str) -> str:
    """Simulate an nmap -sV style port scan on the target IP.

    target: IP address string from challenge_data.
    Output header includes the target value dynamically.
    Port table is hardcoded to match the NexusCorp scenario.
    """
    target = target.strip()
    return (
        f"PORT SCANNER — target: {target}\n\n"
        f"Starting simulated scan...\n\n"
        f"PORT     STATE    SERVICE    VERSION\n"
        f"22/tcp   open     ssh        OpenSSH 8.9p1\n"
        f"80/tcp   closed   http       -\n"
        f"443/tcp  closed   https      -\n"
        f"3306/tcp filtered mysql      -\n"
        f"8080/tcp open     http-alt   nginx 1.24.0\n"
        f"8443/tcp closed   https-alt  -\n\n"
        f"Scan complete. 2 open ports found."
    )


def log_analyzer(log_snippet: str) -> str:
    """Parse a log snippet and highlight 200-status internal IP requests.

    log_snippet: newline-separated log entries from challenge_data.
    Separates lines into MATCH (internal IP + 200 status) and Other.
    Counts unique paths in MATCH lines for the summary.
    """
    lines = [l for l in log_snippet.split("\\n") if l.strip()]
    # Also handle real newlines in case the string was loaded from JSON
    if len(lines) == 1:
        lines = [l for l in log_snippet.split("\n") if l.strip()]

    matches = []
    others = []

    for line in lines:
        is_internal = _log_line_is_internal(line)
        is_200 = _log_line_status(line) == "200"
        if is_internal and is_200:
            matches.append(line)
        else:
            others.append(line)

    # Count unique paths in match lines
    unique_paths = set()
    for line in matches:
        path = _log_line_path(line)
        if path:
            unique_paths.add(path)

    output_lines = [
        "LOG ANALYZER — nexuscorp-access.log",
        "",
        "Scanning for 200-status requests from internal IPs (10.0.0.x)...",
        "",
    ]

    if matches:
        for m in matches:
            output_lines.append(f"[MATCH] {m}")
    else:
        output_lines.append("No internal 200-status entries found.")

    output_lines.append("")
    output_lines.append("Other entries (external IPs or non-200):")
    for o in others:
        output_lines.append(o)

    output_lines.append("")
    output_lines.append(
        f"Analysis complete. {len(unique_paths)} unique internal "
        f"path(s) with 200 status found."
    )

    return "\n".join(output_lines)


def _log_line_is_internal(line: str) -> bool:
    """Return True if the log line's IP starts with '10.'."""
    return line.startswith("10.")


def _log_line_status(line: str) -> str:
    """Extract the HTTP status code from a standard access log line.

    Standard format: IP - - [timestamp] "METHOD /path HTTP/ver" STATUS SIZE
    Status code is the first token after the closing quote.
    """
    match = re.search(r'" (\d{3}) ', line)
    if match:
        return match.group(1)
    return ""


def _log_line_path(line: str) -> str:
    """Extract the request path from a standard access log line."""
    match = re.search(r'"(?:GET|POST|PUT|DELETE|HEAD|OPTIONS) (/[^ ]*)', line)
    if match:
        return match.group(1)
    return ""


def hash_cracker(hash_value: str) -> str:
    """Simulate an MD5 dictionary attack against hash_value.

    hash_value: MD5 hex string from challenge_data.
    Shows each word tested and prints MATCH FOUND with plaintext on match.
    Intentionally reveals the cracked password — educational by design.
    """
    hash_value = hash_value.strip().lower()

    wordlist = [
        "admin", "letmein", "welcome", "nexuscorp", "123456",
        "password", "password1", "qwerty", "abc123", "iloveyou",
        "monkey", "dragon", "master", "shadow", "sunshine",
        "princess", "solo", "football", "charlie", "donald",
    ]

    lines = [
        f"HASH CRACKER — MD5 dictionary attack",
        f"Target: {hash_value}",
        f"",
        f"Loading wordlist... {len(wordlist)} words loaded.",
        f"",
    ]

    for word in wordlist:
        candidate = hashlib.md5(word.encode()).hexdigest()
        if candidate == hash_value:
            lines.append(f"Testing: {word:<12} -> {candidate} [MATCH FOUND]")
            lines.append(f"")
            lines.append(f"Cracked in {wordlist.index(word) + 1} attempts.")
            lines.append(f"Hash:      {hash_value}")
            lines.append(f"Password:  {word}")
            return "\n".join(lines)
        else:
            lines.append(f"Testing: {word:<12} -> {candidate} [no match]")

    lines.append("")
    lines.append("Hash not found in wordlist.")
    return "\n".join(lines)


def dir_enumerator(target_url: str) -> str:
    """Simulate a gobuster-style directory scan on target_url.

    target_url: base URL string from challenge_data.
    Output header includes target_url dynamically.
    Path table is hardcoded to match the NexusCorp scenario.
    """
    target_url = target_url.strip()
    return (
        f"DIR ENUMERATOR — target: {target_url}\n\n"
        f"Starting simulated scan with common wordlist...\n\n"
        f"/              [Status: 200] [Size: 8192]\n"
        f"/about         [Status: 200] [Size: 3104]\n"
        f"/login         [Status: 200] [Size: 2048]\n"
        f"/admin         [Status: 301] [-> /admin/dashboard]\n"
        f"/backup        [Status: 200] [Size: 51204]\n"
        f"/assets        [Status: 200] [Size: 1024]\n"
        f"/favicon.ico   [Status: 200] [Size: 318]\n\n"
        f"Scan complete. 7 paths found. 1 potentially sensitive path identified."
    )


def sqli_tester(payload: str) -> str:
    """Simulate testing an SQL injection payload against a login form.

    payload: the injection string from challenge_data.
    Shows how the payload is inserted into the query and the result.
    Hardcoded for the NexusCorp reporting system scenario.
    """
    payload = payload.strip()
    return (
        f"SQL INJECTION TESTER — target: /backup/report-login\n\n"
        f"Payload: {payload}\n\n"
        f"Constructing query with payload in username field:\n"
        f"  SELECT * FROM users WHERE username='{payload}' AND password=''\n\n"
        f"Query sent to database:\n"
        f"  SELECT * FROM users WHERE username='admin'\n"
        f"  [Everything after -- is treated as a comment and ignored]\n\n"
        f"Result: LOGIN BYPASSED\n"
        f"  Returned row: {{id: 1, username: 'admin', role: 'superuser'}}\n\n"
        f"Authentication bypass successful.\n"
        f"Password check was never evaluated."
    )


def suid_scanner(search_path: str) -> str:
    """Simulate a find command scanning for SUID binaries.

    search_path: directory path from challenge_data.
    Output header includes search_path dynamically.
    Results are hardcoded for the NexusCorp server scenario.
    python3.10 is flagged as exploitable via GTFOBins.
    """
    search_path = search_path.strip()
    return (
        f"SUID SCANNER — scanning: {search_path}\n\n"
        f"Running: find {search_path} -perm -4000 -type f\n\n"
        f"Results:\n"
        f"  /usr/bin/passwd       [SUID] owner: root  — expected, low risk\n"
        f"  /usr/bin/sudo         [SUID] owner: root  — expected, low risk\n"
        f"  /usr/bin/python3.10   [SUID] owner: root  — *** FLAGGED: in GTFOBins ***\n"
        f"  /usr/bin/mount        [SUID] owner: root  — expected, low risk\n"
        f"  /usr/bin/su           [SUID] owner: root  — expected, low risk\n\n"
        f"Scan complete. 5 SUID binaries found. 1 flagged as potentially exploitable.\n\n"
        f"GTFOBins entry: https://gtfobins.github.io/gtfobins/python/\n"
        f"Exploit: python3 -c 'import os; os.execl(\"/bin/sh\", \"sh\", \"-p\")'"
    )
