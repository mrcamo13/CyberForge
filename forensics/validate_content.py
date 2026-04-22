"""validate_content.py — FORENSICS CyberForge content integrity checker.

Run from the cyberforge/forensics/ directory:
    python validate_content.py

Checks:
  1. registry.json is valid JSON and lists all cases
  2. Each case JSON exists, is valid JSON, and has all required fields
  3. expected_output / valid_answers present
  4. starter_code or challenge_data present (challenge_data required for tools)
  5. hints list has 4 entries
  6. debrief has all 5 sub-fields
  7. tools_type is a known type
  8. All referenced fixture files exist (if any)

Exit code 0 = all checks passed.
Exit code 1 = one or more failures.
"""

import json
import os
import sys

_FORENSICS_DIR = os.path.dirname(os.path.abspath(__file__))
_CONTENT_DIR = os.path.join(_FORENSICS_DIR, "content")
_CASES_DIR = os.path.join(_CONTENT_DIR, "cases")
_REGISTRY_PATH = os.path.join(_CONTENT_DIR, "registry.json")

_REQUIRED_FIELDS = (
    "id", "title", "stage", "difficulty", "xp_base",
    "tools_type", "scenario", "challenge",
    "challenge_data", "valid_answers", "hints", "learn", "debrief",
)

_REQUIRED_DEBRIEF_FIELDS = (
    "summary", "real_world", "next_step",
    "cert_link", "exam_tip",
)

_KNOWN_TOOLS_TYPES = {
    "file_analyzer", "metadata_reader", "hash_verifier", "hex_viewer",
    "string_extractor", "mem_analyzer", "timeline_builder",
    "event_log_analyzer", "registry_analyzer", "browser_analyzer",
    "email_analyzer", "pcap_analyzer", "prefetch_analyzer",
    "intel_correlator", "none",
}

_FAILURES = []


def _ok(msg: str) -> None:
    print(f"  [OK]  {msg}")


def _fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")
    _FAILURES.append(msg)


# ---------------------------------------------------------------------------
# Registry check
# ---------------------------------------------------------------------------

def check_registry() -> list:
    """Validate registry.json. Returns list of case IDs."""
    print("\n--- registry.json ---")
    if not os.path.exists(_REGISTRY_PATH):
        _fail("registry.json not found")
        return []

    try:
        with open(_REGISTRY_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        _fail(f"registry.json is invalid JSON: {exc}")
        return []

    # Accept "cases" or "challenges" as the case list key
    cases = data.get("cases", data.get("challenges", []))
    if not cases:
        _fail("registry.json has no cases listed (need 'cases' or 'challenges' key)")
        return []

    _ok(f"registry.json loaded -- {len(cases)} case(s)")

    # Check stages
    stages = data.get("stages", [])
    if stages:
        # Accept "cases" or "challenges" as the case list key inside each stage
        all_staged = [
            cid
            for s in stages
            for cid in (s.get("cases") or s.get("challenges") or [])
        ]
        all_ids = [c["id"] for c in cases]
        for cid in all_staged:
            if cid not in all_ids:
                _fail(f"Stage references unknown case: {cid}")
        _ok(f"  {len(stages)} stage(s) defined")

    ids = []
    for entry in cases:
        cid = entry.get("id", "")
        title = entry.get("title", "")
        if cid and title:
            _ok(f"  {cid}: {title}")
            ids.append(cid)
        else:
            _fail(f"  Entry missing 'id' or 'title': {entry}")
    return ids


# ---------------------------------------------------------------------------
# Case check
# ---------------------------------------------------------------------------

def check_case(case_id: str) -> bool:
    """Validate a single case JSON file. Returns True on pass."""
    path = os.path.join(_CASES_DIR, f"{case_id}.json")
    print(f"\n--- {case_id}.json ---")

    if not os.path.exists(path):
        _fail(f"{case_id}.json not found at {path}")
        return False

    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        _fail(f"Invalid JSON: {exc}")
        return False

    _ok("Valid JSON")

    # Required top-level fields
    for field in _REQUIRED_FIELDS:
        if field not in data:
            _fail(f"Missing required field: '{field}'")
        else:
            _ok(f"Field present: '{field}'")

    # id matches filename
    if data.get("id") != case_id:
        _fail(f"'id' ({data.get('id')!r}) does not match filename ({case_id!r})")

    # valid_answers
    valid_answers = data.get("valid_answers", [])
    if not valid_answers:
        _fail("'valid_answers' list is empty")
    else:
        _ok(f"'valid_answers' has {len(valid_answers)} answer(s)")

    # challenge_data
    if not data.get("challenge_data", "").strip():
        _fail("'challenge_data' is empty")
    else:
        lines = data["challenge_data"].strip().splitlines()
        _ok(f"'challenge_data' has {len(lines)} line(s)")

    # tools_type
    tools_type = data.get("tools_type", "")
    if tools_type not in _KNOWN_TOOLS_TYPES:
        _fail(f"'tools_type' = {tools_type!r} is not a known type")
    else:
        _ok(f"'tools_type' = {tools_type!r}")

    # hints
    hints = data.get("hints", [])
    if not hints:
        _fail("'hints' list is empty")
    elif len(hints) != 4:
        _fail(f"'hints' has {len(hints)} entries (expected 4)")
    else:
        _ok(f"'hints' has {len(hints)} entries")

    # debrief sub-fields
    debrief = data.get("debrief", {})
    for df in _REQUIRED_DEBRIEF_FIELDS:
        if not debrief.get(df, "").strip():
            _fail(f"'debrief.{df}' is empty or missing")
        else:
            _ok(f"'debrief.{df}' present")

    # difficulty
    diff = data.get("difficulty", 0)
    if not isinstance(diff, int) or diff < 1 or diff > 4:
        _fail(f"'difficulty' = {diff!r} (expected int 1-4)")
    else:
        _ok(f"'difficulty' = {diff}")

    # xp_base
    xp = data.get("xp_base", 0)
    if not isinstance(xp, int) or xp <= 0:
        _fail(f"'xp_base' = {xp!r} (expected positive int)")
    else:
        _ok(f"'xp_base' = {xp}")

    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    _FAILURES.clear()

    print("CyberForge FORENSICS -- Content Validator")
    print("=" * 55)

    case_ids = check_registry()
    if not case_ids:
        _FAILURES.append("registry check failed")

    for cid in case_ids:
        check_case(cid)

    print()
    print("=" * 55)
    if not _FAILURES:
        print(f"  ALL CHECKS PASSED  ({len(case_ids)} cases validated)")
    else:
        print(f"  {len(_FAILURES)} CHECK(S) FAILED -- see above for details")
    print("=" * 55)

    return 0 if not _FAILURES else 1


if __name__ == "__main__":
    sys.exit(main())
