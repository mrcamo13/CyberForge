# spec.md — LAB Stage 1: Python Script Challenges
<!--
SDD Phase 2 of 4: Spec
Next: tasks.md
-->

**Module:** lab-stage1
**Date:** 2026-04-16
**Status:** Draft

---

## Engine Spec

### Workspace
- On challenge start, game creates/overwrites `lab/workspace/solution.py` with starter code
- Input files (log files, IP lists, etc.) copied into `lab/workspace/` from `lab/content/fixtures/`
- Player edits `solution.py` in their own editor
- Game never modifies `solution.py` after writing it

### Commands (same as AEGIS/CIPHER plus `run`)
```
run         — execute solution.py, validate output, show result
learn       — explain the Python concept behind this challenge
hint        — reveal next hint (4 max, reduces XP)
notes       — view saved notes
note <text> — save a note
skip        — skip challenge
menu        — return to challenge menu
quit        — save and exit
```

### Run Logic
```python
result = subprocess.run(
    [sys.executable, "solution.py"],
    capture_output=True, text=True,
    cwd=workspace_dir, timeout=10
)
```

1. Timeout = 10s (catches infinite loops)
2. If returncode != 0: show stderr (the Python traceback), prompt to fix and run again
3. If returncode == 0: normalize output (strip trailing whitespace per line, strip trailing blank lines)
4. Compare normalized actual vs normalized expected line-by-line
5. PASS: award XP, show debrief
6. FAIL: show diff — up to 5 mismatched lines shown, then "X more lines differ"

### Output Normalization
```python
def normalize(output: str) -> list:
    lines = output.splitlines()
    lines = [line.rstrip() for line in lines]
    while lines and not lines[-1]:
        lines.pop()
    return lines
```

### XP
Same multiplier table as AEGIS (0 hints = 100%, 1 = 75%, 2 = 50%, 3 = 25%, 4 = 10%).
First completion only. Replay shows debrief but no XP.

### Save Schema (mirrors AEGIS)
```json
{
  "player_name": "string",
  "created_at": "ISO",
  "last_played": "ISO",
  "total_time_played_seconds": 0,
  "xp": 0,
  "badges": [],
  "completed": [],
  "skipped": [],
  "in_progress": "",
  "hints_used": {},
  "notes": {},
  "metrics": {}
}
```

---

## Challenge Specs

---

### lab01 — Log Parser

**File:** `lab/content/challenges/lab01.json`
**Fixture:** `lab/content/fixtures/access.log`
**XP base:** 100
**Difficulty:** 1

**Scenario:**
```
LAB TERMINAL v1.0 -- PYTHON SCRIPT LAB

CHALLENGE 01 -- LOG PARSER
Difficulty: * (Beginner)

You are a SOC analyst. The web server at 203.0.113.47 has been
generating errors all morning. Your manager wants a list of every
request that returned a 404 Not Found status code.

The log file is at: workspace/access.log
Your script must read it and print every line that contains a 404.

Open workspace/solution.py in your editor, write your solution,
then type 'run' to test it.
```

**Challenge text:**
```
Read access.log and print every line that contains " 404 ".
One line of output per matching log entry. No extra formatting.
```

**Fixture — access.log (10 lines):**
```
203.0.113.1 - - [01/Apr/2026:08:01:12 +0000] "GET /index.html HTTP/1.1" 200 1024
203.0.113.2 - - [01/Apr/2026:08:01:45 +0000] "GET /admin HTTP/1.1" 404 512
203.0.113.3 - - [01/Apr/2026:08:02:10 +0000] "POST /login HTTP/1.1" 200 256
203.0.113.4 - - [01/Apr/2026:08:02:33 +0000] "GET /secret.txt HTTP/1.1" 404 512
203.0.113.5 - - [01/Apr/2026:08:03:01 +0000] "GET /favicon.ico HTTP/1.1" 200 128
203.0.113.6 - - [01/Apr/2026:08:03:22 +0000] "GET /.env HTTP/1.1" 404 512
203.0.113.7 - - [01/Apr/2026:08:03:55 +0000] "GET /robots.txt HTTP/1.1" 200 64
203.0.113.8 - - [01/Apr/2026:08:04:10 +0000] "GET /wp-admin HTTP/1.1" 404 512
203.0.113.9 - - [01/Apr/2026:08:04:44 +0000] "GET /index.html HTTP/1.1" 200 1024
203.0.113.10 - - [01/Apr/2026:08:05:01 +0000] "GET /shell.php HTTP/1.1" 404 512
```

**Expected output (5 lines):**
```
203.0.113.2 - - [01/Apr/2026:08:01:45 +0000] "GET /admin HTTP/1.1" 404 512
203.0.113.4 - - [01/Apr/2026:08:02:33 +0000] "GET /secret.txt HTTP/1.1" 404 512
203.0.113.6 - - [01/Apr/2026:08:03:22 +0000] "GET /.env HTTP/1.1" 404 512
203.0.113.8 - - [01/Apr/2026:08:04:10 +0000] "GET /wp-admin HTTP/1.1" 404 512
203.0.113.10 - - [01/Apr/2026:08:05:01 +0000] "GET /shell.php HTTP/1.1" 404 512
```

**Starter code:**
```python
# lab01 — Log Parser
# Read access.log and print every line that contains a 404 status code.

with open("access.log", "r") as f:
    for line in f:
        # TODO: check if this line contains a 404
        # TODO: if it does, print it (strip the trailing newline)
        pass
```

**Hints:**
1. "The `in` operator checks if a string contains a substring.\n        Try: if \" 404 \" in line"
2. "Use line.strip() to remove the trailing newline before printing.\n        Your loop body should be:\n          if \" 404 \" in line:\n              print(line.strip())"
3. "Full solution structure:\n        with open(\"access.log\", \"r\") as f:\n            for line in f:\n                if \" 404 \" in line:\n                    print(line.strip())"
4. "SPOILER -- Complete solution:\n        with open(\"access.log\", \"r\") as f:\n            for line in f:\n                if \" 404 \" in line:\n                    print(line.strip())"

**Learn:**
```
File I/O and string searching are the foundation of log analysis.

Opening a file in Python:
  with open("filename.txt", "r") as f:   # "r" = read mode
      for line in f:                      # iterates line by line
          print(line.strip())             # strip() removes \n

The 'with' statement:
  Automatically closes the file when the block ends -- even if an
  error occurs. Always use 'with open()' instead of f = open().

String membership test:
  if "404" in line:    # True if "404" appears anywhere in line
  if " 404 " in line:  # More specific -- requires spaces around it
                        # Avoids matching "4040" or "14040"

Why SOC analysts care:
  404 errors in bulk from one IP = directory enumeration attack.
  An attacker is probing for hidden files (/.env, /wp-admin, /shell.php).
  Your script just automated what grep does:
    grep " 404 " access.log
```

**Debrief:**
```json
{
  "summary": "Your script found 5 404 errors -- all probing for sensitive files: /admin, /secret.txt, /.env, /wp-admin, and /shell.php. This is a classic reconnaissance pattern. An attacker is directory-busting the server looking for an entry point.",
  "real_world": "In a real SOC, log parsing is automated by a SIEM (Splunk, Elastic). But analysts still write one-off Python scripts when they need a custom filter the SIEM doesn't support -- or when they're analyzing an exported log file offline. This exact script (read file, filter lines) is used daily.",
  "next_step": "Try extending your script:\n  1. Count how many 404s came from each IP address\n  2. Print only the IPs with more than 2 404s\n  This is alert triage -- identifying the noisiest offenders.",
  "cert_link": "CySA+ CS0-003 Domain 1 -- Security Operations:\n  Log analysis and SIEM correlation are tested in every exam version.",
  "exam_tip": "On the CySA+ exam, log analysis questions give you log output and ask what it indicates. Knowing that bulk 404s from one IP = directory enumeration is a common question pattern."
}
```

---

### lab02 — IP Validator

**File:** `lab/content/challenges/lab02.json`
**Fixture:** `lab/content/fixtures/ip_list.txt`
**XP base:** 100
**Difficulty:** 1

**Scenario:**
```
LAB TERMINAL v1.0 -- PYTHON SCRIPT LAB

CHALLENGE 02 -- IP VALIDATOR
Difficulty: * (Beginner)

Your threat intel team received a feed of IP addresses to block.
The feed is messy -- it includes malformed entries, private IPs
written incorrectly, and junk data mixed in.

Before importing into the firewall, you need to filter the list
to only valid IPv4 addresses.

The list is at: workspace/ip_list.txt
Write a script that prints only the valid IPs.
```

**Challenge text:**
```
Read ip_list.txt (one entry per line). Print only valid IPv4 addresses.
A valid IPv4 address has exactly 4 parts separated by dots,
each part a number between 0 and 255 (inclusive).
Print valid IPs in the order they appear. One per line.
```

**Fixture — ip_list.txt (12 lines):**
```
192.168.1.1
10.0.0.256
MALWARE-C2-SERVER
172.16.0.1
999.999.999.999
8.8.8.8
not-an-ip
1.2.3.4
300.1.1.1
185.220.101.47
10.10.10
203.0.113.99
```

**Expected output (6 lines):**
```
192.168.1.1
172.16.0.1
8.8.8.8
1.2.3.4
185.220.101.47
203.0.113.99
```

**Starter code:**
```python
# lab02 -- IP Validator
# Read ip_list.txt and print only valid IPv4 addresses.
# A valid IP has exactly 4 parts, each between 0 and 255.

def is_valid_ip(address):
    parts = address.strip().split(".")
    # TODO: check there are exactly 4 parts
    # TODO: check each part is a number between 0 and 255
    # Hint: use int() to convert, and handle ValueError with try/except
    return False  # replace this

with open("ip_list.txt", "r") as f:
    for line in f:
        ip = line.strip()
        if is_valid_ip(ip):
            print(ip)
```

**Hints:**
1. "Check the number of parts first:\n        if len(parts) != 4:\n            return False\n        Then loop through each part and check it is 0-255."
2. "Use try/except to handle parts that are not numbers:\n        try:\n            num = int(part)\n        except ValueError:\n            return False\n        if num < 0 or num > 255:\n            return False"
3. "Complete is_valid_ip:\n        parts = address.strip().split(\".\")\n        if len(parts) != 4:\n            return False\n        for part in parts:\n            try:\n                num = int(part)\n            except ValueError:\n                return False\n            if num < 0 or num > 255:\n                return False\n        return True"
4. "SPOILER -- The key insight: split on dot, check length == 4,\n        convert each to int (catch ValueError), check 0 <= n <= 255.\n        Return True only if ALL checks pass."

**Learn:**
```
String splitting and type conversion are core Python skills.

.split(delimiter):
  "192.168.1.1".split(".")  ->  ["192", "168", "1", "1"]
  "hello world".split(" ")  ->  ["hello", "world"]

len() -- count items in a list:
  len(["192", "168", "1", "1"])  ->  4

int() -- convert string to integer:
  int("192")   ->  192
  int("abc")   ->  raises ValueError -- must handle with try/except

try/except -- handle errors gracefully:
  try:
      num = int(part)
  except ValueError:
      return False   # not a number, invalid IP

Range checking:
  if num < 0 or num > 255:  ->  invalid octet

Why this matters in security:
  Threat intel feeds are dirty. Before blocking IPs in a firewall,
  you validate them -- a malformed entry could break the firewall rule
  set or accidentally block legitimate traffic.
```

**Debrief:**
```json
{
  "summary": "Your script correctly identified 6 valid IPs from 12 entries. It rejected: 10.0.0.256 (octet > 255), MALWARE-C2-SERVER (not an IP), 999.999.999.999 (all octets invalid), 'not-an-ip' (no dots), 300.1.1.1 (first octet > 255), and 10.10.10 (only 3 octets).",
  "real_world": "IP validation is used in: firewall rule automation, threat intel ingestion pipelines, log enrichment scripts, and blocklist management. Python's ipaddress module (stdlib) has a built-in validator -- but writing it from scratch teaches you what validation actually checks.",
  "next_step": "Try this: import ipaddress and use ipaddress.ip_address(ip) in a try/except block. Compare the result to your manual validator. They should agree on all 12 entries.",
  "cert_link": "CySA+ CS0-003 Domain 2 -- Vulnerability Management:\n  Understanding IP address structure and validation is foundational for network-based vulnerability scanning.",
  "exam_tip": "IPv4 ranges to know: 0-255 per octet, 4 octets total, dot-separated. Private ranges: 10.x.x.x, 172.16-31.x.x, 192.168.x.x. These appear in network analysis questions."
}
```

---

### lab03 — Hash Checker

**File:** `lab/content/challenges/lab03.json`
**Fixture:** `lab/content/fixtures/suspicious.bin`
**XP base:** 150
**Difficulty:** 2

**Scenario:**
```
LAB TERMINAL v1.0 -- PYTHON SCRIPT LAB

CHALLENGE 03 -- HASH CHECKER
Difficulty: ** (Intermediate)

A suspicious file was found on an endpoint during the NIGHTWIRE
investigation. The malware analyst has provided the known SHA-256
hash of the Cobalt Strike beacon that NIGHTWIRE used.

Known bad hash:
  b94f6f125c79e3a5ffaa826f584f507f8b67e8d7b6f2c30b7b9b0a3c8afe5d1

Your job: hash the file and determine if it matches.

The file is at: workspace/suspicious.bin
Write a script that prints MATCH or NO MATCH.
```

**Challenge text:**
```
Compute the SHA-256 hash of suspicious.bin.
Compare it to: b94f6f125c79e3a5ffaa826f584f507f8b67e8d7b6f2c30b7b9b0a3c8afe5d1
Print exactly: MATCH
or exactly:    NO MATCH
```

**Fixture — suspicious.bin:**
A binary file whose SHA-256 hash is `b94f6f125c79e3a5ffaa826f584f507f8b67e8d7b6f2c30b7b9b0a3c8afe5d1`.
Generated at build time: `open("suspicious.bin", "wb").write(b"NIGHTWIRE_BEACON_PAYLOAD_v2\x00" * 16)`
(Pre-compute and verify hash matches at build time.)

**Expected output:**
```
MATCH
```

**Starter code:**
```python
# lab03 -- Hash Checker
# Compute the SHA-256 hash of suspicious.bin and compare to the known bad hash.

import hashlib

KNOWN_HASH = "b94f6f125c79e3a5ffaa826f584f507f8b67e8d7b6f2c30b7b9b0a3c8afe5d1"

# TODO: open suspicious.bin in binary mode ("rb")
# TODO: read its contents
# TODO: compute sha256 hash using hashlib
# TODO: compare to KNOWN_HASH and print MATCH or NO MATCH
```

**Hints:**
1. "Open the file in binary mode:\n        with open(\"suspicious.bin\", \"rb\") as f:\n            data = f.read()\n        Binary mode (\"rb\") is required for non-text files."
2. "Compute the hash:\n        file_hash = hashlib.sha256(data).hexdigest()\n        hexdigest() returns the hash as a hex string."
3. "Compare and print:\n        if file_hash == KNOWN_HASH:\n            print(\"MATCH\")\n        else:\n            print(\"NO MATCH\")"
4. "SPOILER -- Full solution:\n        import hashlib\n        KNOWN_HASH = \"b94f6f125c79e3a5ffaa826f584f507f8b67e8d7b6f2c30b7b9b0a3c8afe5d1\"\n        with open(\"suspicious.bin\", \"rb\") as f:\n            data = f.read()\n        file_hash = hashlib.sha256(data).hexdigest()\n        print(\"MATCH\" if file_hash == KNOWN_HASH else \"NO MATCH\")"

**Learn:**
```
Cryptographic hashing is used constantly in security for file integrity.

hashlib -- Python's built-in crypto hash module:
  import hashlib
  hashlib.sha256(data).hexdigest()  ->  64-char hex string
  hashlib.md5(data).hexdigest()     ->  32-char hex string (weaker)

Binary file mode:
  open("file.bin", "rb")  -- "r" = read, "b" = binary
  Always use "rb" for non-text files (executables, images, zips)
  Text mode ("r") mangles binary data on Windows (line ending conversion)

Hash algorithms to know:
  MD5    -- 128-bit, broken for security, still used for checksums
  SHA-1  -- 160-bit, deprecated
  SHA-256 -- 256-bit, current standard, use this
  SHA-512 -- 512-bit, extra strong

Real-world use:
  VirusTotal checks file hashes against known malware databases.
  SIEM rules trigger on known-bad hashes (IOC matching).
  Software vendors publish SHA-256 hashes so you can verify downloads.
```

**Debrief:**
```json
{
  "summary": "The file hash matched the known Cobalt Strike beacon signature. This confirms the file found on the endpoint is the same malware used in the NIGHTWIRE attack. Hash matching is step one of malware triage -- it tells you instantly if a file is a known threat without running it.",
  "real_world": "In a real investigation, you would submit the hash to VirusTotal (virustotal.com) and cross-reference it against threat intel platforms like MISP or OpenCTI. A MATCH on a known-bad hash is enough to escalate to incident response without further analysis.",
  "next_step": "Extend your script: instead of one known hash, read a file of known-bad hashes (one per line) and check if suspicious.bin matches ANY of them. This is how a real hash-based IOC scanner works.",
  "cert_link": "CySA+ CS0-003 Domain 3 -- Incident Response:\n  Hash-based IOC matching is a tested topic under malware analysis and evidence handling.",
  "exam_tip": "On the exam: SHA-256 is the current standard hash for file integrity. MD5 and SHA-1 are deprecated for security use. Know that hashing is used for: malware identification, file integrity monitoring, chain of custody (evidence hasn't been tampered with), and password storage (with salt)."
}
```

---

### lab04 — Base64 Coder

**File:** `lab/content/challenges/lab04.json`
**Fixture:** `lab/content/fixtures/encoded.txt`
**XP base:** 150
**Difficulty:** 2

**Scenario:**
```
LAB TERMINAL v1.0 -- PYTHON SCRIPT LAB

CHALLENGE 04 -- BASE64 DECODER
Difficulty: ** (Intermediate)

During the NIGHTWIRE forensic investigation, the disk image
revealed a script that was pulling commands from a remote server.
The commands were Base64-encoded to evade simple string detection.

You have extracted the encoded strings from memory.
Decode them to reveal the attacker's commands.

The encoded strings are at: workspace/encoded.txt
Write a script that decodes and prints each one.
```

**Challenge text:**
```
Read encoded.txt (one Base64 string per line).
Decode each string and print the plaintext.
One decoded string per line.
```

**Fixture — encoded.txt (5 lines):**
```
d2hvYW1p
aWZjb25maWcgL2FsbA==
bmV0IHVzZXIgYWRtaW4gUEBzc3dvcmQxMjMgL2FkZA==
cG93ZXJzaGVsbCAtZW5jb2RlZGNvbW1hbmQ=
Y21kIC9jIHdob2FtaSAmJiBuZXQgbG9jYWxncm91cA==
```

**Expected output:**
```
whoami
ipconfig /all
net user admin P@ssword123 /add
powershell -encodedcommand
cmd /c whoami && net localgroup
```

**Starter code:**
```python
# lab04 -- Base64 Decoder
# Read encoded.txt and decode each Base64 string.

import base64

with open("encoded.txt", "r") as f:
    for line in f:
        encoded = line.strip()
        # TODO: decode the base64 string
        # Hint: base64.b64decode(encoded) returns bytes
        # Hint: call .decode("utf-8") to convert bytes to string
        # TODO: print the decoded string
        pass
```

**Hints:**
1. "base64.b64decode() takes a string and returns bytes:\n        decoded_bytes = base64.b64decode(encoded)\n        You then need to convert bytes to a string."
2. "Convert bytes to string with .decode():\n        decoded_str = base64.b64decode(encoded).decode(\"utf-8\")\n        Then print(decoded_str)"
3. "Full loop body:\n        encoded = line.strip()\n        decoded = base64.b64decode(encoded).decode(\"utf-8\")\n        print(decoded)"
4. "SPOILER -- Complete solution:\n        import base64\n        with open(\"encoded.txt\", \"r\") as f:\n            for line in f:\n                encoded = line.strip()\n                print(base64.b64decode(encoded).decode(\"utf-8\"))"

**Learn:**
```
Base64 is an encoding (not encryption) that represents binary data
as ASCII text. It is reversible with no key.

import base64

Encode:
  base64.b64encode(b"hello")        ->  b'aGVsbG8='
  base64.b64encode(b"hello").decode("utf-8")  ->  'aGVsbG8='

Decode:
  base64.b64decode("aGVsbG8=")      ->  b'hello'
  base64.b64decode("aGVsbG8=").decode("utf-8")  ->  'hello'

bytes vs str in Python 3:
  b"hello"  -- bytes literal (raw bytes)
  "hello"   -- str (unicode text)
  .encode("utf-8")  -- str -> bytes
  .decode("utf-8")  -- bytes -> str

Why attackers use Base64:
  Simple string searches for "whoami" or "net user" would flag
  a script immediately. Base64 encoding disguises the payload.
  It is not encryption -- any analyst can decode it instantly.
  On the CySA+ exam, spotting Base64 and knowing it is trivially
  reversible is a tested skill.
```

**Debrief:**
```json
{
  "summary": "The decoded commands reveal the attacker's post-exploitation playbook: whoami (who am I running as), ipconfig /all (network recon), net user admin /add (creating a backdoor admin account), powershell -encodedcommand (launching an encoded PowerShell payload), and cmd /c whoami && net localgroup (checking group membership). This is a complete privilege escalation sequence.",
  "real_world": "Base64-encoded commands in PowerShell are one of the most common living-off-the-land techniques. Defenders look for: long Base64 strings in process arguments, base64.b64decode in Python scripts, and [System.Convert]::FromBase64String in PowerShell. Your script is the manual version of what a SIEM alert rule does automatically.",
  "next_step": "Try encoding your own strings with base64.b64encode() and decoding them back. Then try decoding a PowerShell -EncodedCommand string -- they use a variant called UTF-16LE: base64.b64decode(encoded).decode('utf-16-le')",
  "cert_link": "CySA+ CS0-003 Domain 1 -- Security Operations:\n  Identifying and decoding obfuscated content is tested under malware analysis and threat hunting.",
  "exam_tip": "On the exam: Base64 strings end in = or == (padding). They use A-Z, a-z, 0-9, +, /. If you see a long string of those characters in a script or log, it is almost certainly Base64. It is encoding, not encryption -- no key needed to reverse it."
}
```

---

### lab05 — Port Scanner

**File:** `lab/content/challenges/lab05.json`
**XP base:** 200
**Difficulty:** 3

**Scenario:**
```
LAB TERMINAL v1.0 -- PYTHON SCRIPT LAB

CHALLENGE 05 -- PORT SCANNER
Difficulty: *** (Intermediate+)

You are about to learn how nmap works under the hood.

A TCP connect scan works by attempting to open a socket connection
to each port. If the connection succeeds, the port is OPEN.
If it is refused or times out, the port is CLOSED.

The game has started a small test server on localhost port 7005.
Scan ports 7000 through 7010 on 127.0.0.1.

Write the scanner. No external libraries -- sockets only.
```

**Challenge text:**
```
Scan ports 7000-7010 on 127.0.0.1 using Python sockets.
For each port, print exactly:
  PORT 7000: CLOSED
  PORT 7001: CLOSED
  ...
  PORT 7005: OPEN
  ...
Print ports in order 7000 to 7010.
```

**Expected output (11 lines):**
```
PORT 7000: CLOSED
PORT 7001: CLOSED
PORT 7002: CLOSED
PORT 7003: CLOSED
PORT 7004: CLOSED
PORT 7005: OPEN
PORT 7006: CLOSED
PORT 7007: CLOSED
PORT 7008: CLOSED
PORT 7009: CLOSED
PORT 7010: CLOSED
```

Note: The challenge_runner starts a background thread server on port 7005
before running solution.py, and stops it after.

**Starter code:**
```python
# lab05 -- Port Scanner
# Scan ports 7000-7010 on localhost using sockets.
# Print "PORT XXXX: OPEN" or "PORT XXXX: CLOSED" for each.

import socket

HOST = "127.0.0.1"
START_PORT = 7000
END_PORT = 7010

for port in range(START_PORT, END_PORT + 1):
    # TODO: create a socket
    # TODO: set a short timeout (0.5 seconds)
    # TODO: try to connect to HOST:port
    # TODO: if connection succeeds: print OPEN, close socket
    # TODO: if connection fails (exception): print CLOSED
    pass
```

**Hints:**
1. "Create a socket and set a timeout:\n        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n        s.settimeout(0.5)\n        AF_INET = IPv4, SOCK_STREAM = TCP"
2. "Try to connect and handle the result:\n        try:\n            s.connect((HOST, port))\n            print(f\"PORT {port}: OPEN\")\n            s.close()\n        except (socket.timeout, ConnectionRefusedError, OSError):\n            print(f\"PORT {port}: CLOSED\")"
3. "Put it together in the loop:\n        for port in range(START_PORT, END_PORT + 1):\n            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n            s.settimeout(0.5)\n            try:\n                s.connect((HOST, port))\n                print(f\"PORT {port}: OPEN\")\n                s.close()\n            except (socket.timeout, ConnectionRefusedError, OSError):\n                print(f\"PORT {port}: CLOSED\")"
4. "SPOILER -- The full solution is hint 3. The key concepts:\n        socket() creates a TCP socket\n        settimeout() prevents hanging on closed ports\n        connect() raises an exception if the port is closed\n        catching the exception lets you print CLOSED and move on"

**Learn:**
```
Sockets are the foundation of all network communication in Python.

import socket

Creating a TCP socket:
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  AF_INET     = IPv4 addresses
  SOCK_STREAM = TCP (reliable, connection-oriented)
  SOCK_DGRAM  = UDP (faster, no connection)

Setting a timeout:
  s.settimeout(0.5)   -- wait max 0.5 seconds for connection
  Without this, closed ports can hang for 30+ seconds

Connecting:
  s.connect(("127.0.0.1", 80))
  Raises ConnectionRefusedError if port is closed
  Raises socket.timeout if no response within timeout

f-strings (Python 3.6+):
  port = 8080
  print(f"PORT {port}: OPEN")   ->  "PORT 8080: OPEN"

How nmap does it:
  nmap -sT (TCP connect scan) does EXACTLY what your script does:
  for each port, open a socket, try to connect, record the result.
  The difference: nmap is parallelized (thousands of ports at once)
  and can do stealth scans (SYN scan = half-open connection).
```

**Debrief:**
```json
{
  "summary": "Your scanner correctly identified port 7005 as OPEN and all others as CLOSED. This is a TCP connect scan -- the same technique nmap -sT uses. You just wrote the core logic of one of the most important tools in both red team and blue team work.",
  "real_world": "Port scanners are used by: attackers (reconnaissance), pentesters (scoping), and defenders (asset discovery, finding rogue services). Understanding socket-level scanning helps you interpret nmap output, write custom network automation, and understand why certain firewall rules exist.",
  "next_step": "Upgrade your scanner:\n  1. Scan a wider range (1-1024) -- these are the well-known ports\n  2. Look up the service name: socket.getservbyport(port, 'tcp')\n  3. Only print OPEN ports (skip the CLOSED output)\n  4. Try scanning multiple hosts",
  "cert_link": "PenTest+ PT0-003 Domain 2 -- Reconnaissance:\n  TCP connect scanning and port enumeration are core tested skills.\n  CySA+ CS0-003 Domain 1 -- Understanding scanning techniques\n  helps analysts interpret attacker recon activity in logs.",
  "exam_tip": "Know the difference: TCP connect scan (full 3-way handshake, logged by target) vs SYN scan (half-open, stealthier, requires raw sockets/root). nmap defaults to SYN scan when run as root. Your Python socket script does a TCP connect scan."
}
```

---

## Registry Spec

**File:** `lab/content/registry.json`
```json
{
  "version": "1.0",
  "simulator": "lab",
  "challenges": [
    {"id": "lab01", "title": "Log Parser",    "difficulty": 1},
    {"id": "lab02", "title": "IP Validator",  "difficulty": 1},
    {"id": "lab03", "title": "Hash Checker",  "difficulty": 2},
    {"id": "lab04", "title": "Base64 Coder",  "difficulty": 2},
    {"id": "lab05", "title": "Port Scanner",  "difficulty": 3}
  ]
}
```

---

## play.py Update

Add `[3] LAB -- Script Lab (Python automation)` to the selector.
LAB launches `lab/main.py` the same way CIPHER and AEGIS are launched.

---

## Validation Spec

**File:** `lab/validate_content.py`
Checks:
- All challenge JSON files have required fields
- Required fields: id, title, difficulty, xp_base, scenario, challenge, starter_code, expected_output, hints (4), learn, debrief
- Debrief has: summary, real_world, next_step, cert_link, exam_tip
- Registry references all challenge files and all files exist
- Fixture files exist for challenges that need them
