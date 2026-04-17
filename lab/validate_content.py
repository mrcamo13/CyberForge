"""validate_content.py — LAB CyberForge content integrity checker.

Run from the cyberforge/lab/ directory:
    python validate_content.py

Checks:
  1. registry.json is valid JSON and lists all challenges
  2. Each challenge JSON exists, is valid JSON, and has all required fields
  3. Each fixture file referenced in a challenge exists
  4. expected_output is non-empty (unless test_cases is present)
  5. starter_code is non-empty
  6. hints list has 4 entries
  7. debrief has all 5 sub-fields
  8. test_cases entries (if present) each have description, expected_output
  9. test_server_port (if present) is an integer 1024-65535
 10. Known fixture SHA-256 checksums are verified

Exit code 0 = all checks passed.
Exit code 1 = one or more failures.
"""

import hashlib
import json
import os
import sys

_LAB_DIR = os.path.dirname(os.path.abspath(__file__))
_CONTENT_DIR = os.path.join(_LAB_DIR, "content")
_CHALLENGES_DIR = os.path.join(_CONTENT_DIR, "challenges")
_FIXTURES_DIR = os.path.join(_CONTENT_DIR, "fixtures")
_REGISTRY_PATH = os.path.join(_CONTENT_DIR, "registry.json")

_REQUIRED_FIELDS = (
    "id", "title", "difficulty", "xp_base",
    "fixtures", "scenario", "challenge",
    "starter_code", "hints", "learn", "debrief",
)

_REQUIRED_DEBRIEF_FIELDS = (
    "summary", "real_world", "next_step",
    "cert_link", "exam_tip",
)

_FIXTURE_CHECKSUMS = {
    "suspicious.bin": "aa3278193c16ca46977ba7a5b9218f08aa9f4aabe4f9e21ebde3d49b09c00402",
    "secret.xor":     "637107862f57747ea9f77246a2e241532cd4b4023ea64c36c2fc2cbed16deefa",
}

_FAILURES = []


def _ok(msg: str) -> None:
    print(f"  [OK]  {msg}")


def _fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")
    _FAILURES.append(msg)


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Registry check
# ---------------------------------------------------------------------------

def check_registry() -> list:
    """Validate registry.json. Returns list of challenge IDs."""
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

    # Check top-level challenges list
    challenges = data.get("challenges", [])
    if not challenges:
        _fail("registry.json has no challenges listed")
        return []

    _ok(f"registry.json loaded — {len(challenges)} challenge(s)")

    # Check stages if present
    stages = data.get("stages", [])
    if stages:
        all_staged = [cid for s in stages for cid in s.get("challenges", [])]
        all_ids = [c["id"] for c in challenges]
        for cid in all_staged:
            if cid not in all_ids:
                _fail(f"Stage references unknown challenge: {cid}")
        _ok(f"  {len(stages)} stage(s) defined")

    ids = []
    for entry in challenges:
        cid = entry.get("id", "")
        title = entry.get("title", "")
        if cid and title:
            _ok(f"  {cid}: {title}")
            ids.append(cid)
        else:
            _fail(f"  Entry missing 'id' or 'title': {entry}")
    return ids


# ---------------------------------------------------------------------------
# Challenge check
# ---------------------------------------------------------------------------

def check_challenge(challenge_id: str) -> bool:
    """Validate a single challenge JSON file. Returns True on pass."""
    path = os.path.join(_CHALLENGES_DIR, f"{challenge_id}.json")
    print(f"\n--- {challenge_id}.json ---")

    if not os.path.exists(path):
        _fail(f"{challenge_id}.json not found at {path}")
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
    if data.get("id") != challenge_id:
        _fail(f"'id' ({data.get('id')!r}) does not match filename ({challenge_id!r})")

    # expected_output vs test_cases
    has_test_cases = bool(data.get("test_cases"))
    if has_test_cases:
        _ok(f"'test_cases' present ({len(data['test_cases'])} case(s))")
        for i, tc in enumerate(data["test_cases"]):
            if not tc.get("description"):
                _fail(f"  test_cases[{i}] missing 'description'")
            else:
                _ok(f"  test_cases[{i}] description: {tc['description']!r}")
            if not tc.get("expected_output", "").strip():
                _fail(f"  test_cases[{i}] 'expected_output' is empty")
            else:
                lines = tc["expected_output"].strip().splitlines()
                _ok(f"  test_cases[{i}] expected_output: {len(lines)} line(s)")
    else:
        if not data.get("expected_output", "").strip():
            _fail("'expected_output' is empty (and no test_cases present)")
        else:
            lines = data["expected_output"].strip().splitlines()
            _ok(f"'expected_output' has {len(lines)} line(s)")

    # starter_code
    if not data.get("starter_code", "").strip():
        _fail("'starter_code' is empty")
    else:
        _ok("'starter_code' is non-empty")

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

    # fixture files
    for fixture_name in data.get("fixtures", []):
        fixture_path = os.path.join(_FIXTURES_DIR, fixture_name)
        if not os.path.exists(fixture_path):
            _fail(f"Fixture not found: {fixture_name}")
        else:
            _ok(f"Fixture exists: {fixture_name}")
            if fixture_name in _FIXTURE_CHECKSUMS:
                actual = _sha256(fixture_path)
                expected = _FIXTURE_CHECKSUMS[fixture_name]
                if actual == expected:
                    _ok(f"  SHA-256 verified: {fixture_name}")
                else:
                    _fail(
                        f"  SHA-256 MISMATCH for {fixture_name}\n"
                        f"    expected: {expected}\n"
                        f"    actual:   {actual}"
                    )

    # Per-test-case fixtures
    if has_test_cases:
        for i, tc in enumerate(data.get("test_cases", [])):
            for fname in tc.get("fixtures", []):
                fpath = os.path.join(_FIXTURES_DIR, fname)
                if not os.path.exists(fpath):
                    _fail(f"  test_cases[{i}] fixture not found: {fname}")
                else:
                    _ok(f"  test_cases[{i}] fixture exists: {fname}")

    # test_server_port
    if "test_server_port" in data:
        port = data["test_server_port"]
        if isinstance(port, int) and 1024 <= port <= 65535:
            _ok(f"'test_server_port' = {port} (valid)")
        else:
            _fail(f"'test_server_port' = {port!r} (must be int 1024-65535)")

    return True


# ---------------------------------------------------------------------------
# Fixture checksum sweep
# ---------------------------------------------------------------------------

def check_all_fixture_checksums() -> None:
    """Verify all known fixture checksums."""
    print("\n--- fixture checksums ---")
    for fname, expected_hash in _FIXTURE_CHECKSUMS.items():
        path = os.path.join(_FIXTURES_DIR, fname)
        if not os.path.exists(path):
            _fail(f"{fname} not found")
            continue
        actual = _sha256(path)
        if actual == expected_hash:
            _ok(f"{fname}: SHA-256 verified")
        else:
            _fail(f"{fname}: SHA-256 mismatch")
            _fail(f"  expected: {expected_hash}")
            _fail(f"  actual:   {actual}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    _FAILURES.clear()

    print("CyberForge Script Lab — Content Validator")
    print("=" * 55)

    challenge_ids = check_registry()
    if not challenge_ids:
        _FAILURES.append("registry check failed")

    for cid in challenge_ids:
        check_challenge(cid)

    check_all_fixture_checksums()

    print()
    print("=" * 55)
    if not _FAILURES:
        print(f"  ALL CHECKS PASSED  ({len(challenge_ids)} challenges validated)")
    else:
        print(f"  {len(_FAILURES)} CHECK(S) FAILED -- see above for details")
    print("=" * 55)

    return 0 if not _FAILURES else 1


if __name__ == "__main__":
    sys.exit(main())
