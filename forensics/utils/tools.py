"""tools.py — FORENSICS CyberForge

Forensic tool command definitions and display functions.

Each tool function receives the pre-canned challenge_data string (the
forensic artifact output already written in the case JSON) and returns it
formatted for display. Unlike AEGIS where tools compute on live data,
FORENSICS tools show pre-formatted output that simulates running real
forensic tools against evidence.
"""

# ---------------------------------------------------------------------------
# Tool command aliases
#
# Maps tools_type -> [primary_command, ...extra_aliases]
# The FIRST entry is displayed in the UI ("Type 'file' to run the tool").
# ALL entries (plus the generic 'tools') are accepted in the command loop.
# ---------------------------------------------------------------------------
_TOOL_COMMANDS: dict = {
    "file_analyzer":     ["file", "magic"],
    "metadata_reader":   ["exiftool"],
    "hash_verifier":     ["sha256sum", "md5sum", "hash"],
    "hex_viewer":        ["hexdump", "xxd"],
    "string_extractor":  ["strings"],
    "mem_analyzer":      ["volatility", "vol"],
    "timeline_builder":  ["timeline", "mactime"],
    "event_log_analyzer":["eventlog", "evtx"],
    "registry_analyzer": ["registry", "reg", "regedit"],
    "browser_analyzer":  ["browser", "hindsight"],
    "email_analyzer":    ["email-trace", "headers", "mha"],
    "pcap_analyzer":     ["wireshark", "tcpdump", "tshark"],
    "prefetch_analyzer": ["prefetch", "pecmd", "winprefetch"],
    "intel_correlator":  ["threat-intel", "mitre", "vt"],
    "none":              [],
}


def get_tool_commands(tools_type: str) -> list:
    """Return accepted command aliases for a tools_type.

    The first item is the primary display command shown to the player.
    Returns an empty list for tools_type 'none' or unknown types.
    """
    return _TOOL_COMMANDS.get(tools_type, [])


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _display_artifact(challenge_data: str) -> str:
    """Format pre-canned forensic tool output for terminal display.

    The challenge_data in each case JSON is the pre-written output of
    running a real forensic tool against the evidence. This function
    applies consistent framing so every tool output looks the same.
    """
    border = "=" * 60
    return f"\n{border}\n{challenge_data.strip()}\n{border}\n"


# ---------------------------------------------------------------------------
# Tool functions
#
# Every function has the same signature: (challenge_data: str) -> str
# They differ only in the header label shown above the artifact output.
# ---------------------------------------------------------------------------

def file_analyzer(challenge_data: str) -> str:
    """Display file magic-byte analysis output."""
    return _display_artifact(challenge_data)


def metadata_reader(challenge_data: str) -> str:
    """Display ExifTool metadata extraction output."""
    return _display_artifact(challenge_data)


def hash_verifier(challenge_data: str) -> str:
    """Display hash verification output."""
    return _display_artifact(challenge_data)


def hex_viewer(challenge_data: str) -> str:
    """Display hex dump output."""
    return _display_artifact(challenge_data)


def string_extractor(challenge_data: str) -> str:
    """Display strings extraction output."""
    return _display_artifact(challenge_data)


def mem_analyzer(challenge_data: str) -> str:
    """Display Volatility memory analysis output."""
    return _display_artifact(challenge_data)


def timeline_builder(challenge_data: str) -> str:
    """Display forensic timeline output."""
    return _display_artifact(challenge_data)


def event_log_analyzer(challenge_data: str) -> str:
    """Display Windows Event Log analysis output."""
    return _display_artifact(challenge_data)


def registry_analyzer(challenge_data: str) -> str:
    """Display Windows Registry analysis output."""
    return _display_artifact(challenge_data)


def browser_analyzer(challenge_data: str) -> str:
    """Display browser forensics output."""
    return _display_artifact(challenge_data)


def email_analyzer(challenge_data: str) -> str:
    """Display email header / trace analysis output."""
    return _display_artifact(challenge_data)


def pcap_analyzer(challenge_data: str) -> str:
    """Display packet capture analysis output."""
    return _display_artifact(challenge_data)


def prefetch_analyzer(challenge_data: str) -> str:
    """Display Windows Prefetch analysis output."""
    return _display_artifact(challenge_data)


def intel_correlator(challenge_data: str) -> str:
    """Display threat intelligence correlation output."""
    return _display_artifact(challenge_data)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_TOOL_FUNCTIONS: dict = {
    "file_analyzer":      file_analyzer,
    "metadata_reader":    metadata_reader,
    "hash_verifier":      hash_verifier,
    "hex_viewer":         hex_viewer,
    "string_extractor":   string_extractor,
    "mem_analyzer":       mem_analyzer,
    "timeline_builder":   timeline_builder,
    "event_log_analyzer": event_log_analyzer,
    "registry_analyzer":  registry_analyzer,
    "browser_analyzer":   browser_analyzer,
    "email_analyzer":     email_analyzer,
    "pcap_analyzer":      pcap_analyzer,
    "prefetch_analyzer":  prefetch_analyzer,
    "intel_correlator":   intel_correlator,
}


def run_tool(tools_type: str, challenge_data: str) -> str:
    """Dispatch to the correct tool function and return formatted output.

    Args:
        tools_type: The tool type string from the case JSON.
        challenge_data: The pre-canned forensic artifact string.

    Returns:
        Formatted string to display to the player.
    """
    fn = _TOOL_FUNCTIONS.get(tools_type)
    if fn is None:
        return _display_artifact(challenge_data) if challenge_data else "(No tool output available.)"
    return fn(challenge_data)
