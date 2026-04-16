"""validate_content.py — CIPHER CyberForge

Validates all JSON content files against required schemas.
Generates SHA-256 checksums for each validated file.

Exit 0 if all pass. Exit 1 if any fail.
"""

import hashlib
import json
import os
import sys

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TOOLS_TYPE_ALLOWLIST = {
    "caesar_decoder",
    "base64_decoder",
    "port_scanner",
    "log_analyzer",
    "hash_cracker",
    "dir_enumerator",
    "sqli_tester",
    "suid_scanner",
}

_OP_REQUIRED_FIELDS = (
    "id", "title", "track", "cert_objective", "xp_base", "difficulty",
    "tools_type", "challenge_data", "scenario", "challenge", "valid_answers",
    "hints", "learn", "tools", "debrief",
)

_DEBRIEF_REQUIRED_FIELDS = ("summary", "real_world", "next_step", "cert_link")

_REGISTRY_OP_FIELDS = ("id", "title", "status", "difficulty", "cert_objective")

_VALID_STATUSES = {"active", "coming_soon", "deprecated"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha256(filepath: str) -> str:
    """Return hex SHA-256 digest of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _fail(label: str, reason: str, errors: list) -> None:
    """Record a failure and print it immediately."""
    msg = f"[FAIL] {label} — {reason}"
    print(msg)
    errors.append(msg)


def _pass(label: str) -> None:
    """Print a pass line."""
    print(f"[PASS] {label}")


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


def validate_operation(filepath: str, errors: list) -> bool:
    """Validate a single CIPHER operation JSON file.

    Checks required fields, hints count, valid_answers list,
    difficulty range, tools_type allowlist, and debrief subfields.
    Returns True if valid.
    """
    label = os.path.basename(filepath)
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        _fail(label, f"cannot read/parse: {exc}", errors)
        return False

    ok = True

    for field in _OP_REQUIRED_FIELDS:
        if field not in data:
            _fail(label, f"missing field: {field}", errors)
            ok = False

    if ok:
        # valid_answers must be a non-empty list
        if not isinstance(data["valid_answers"], list) or len(data["valid_answers"]) == 0:
            _fail(label, "valid_answers must be a non-empty list", errors)
            ok = False

        # hints must be exactly 4 items
        if not isinstance(data["hints"], list) or len(data["hints"]) != 4:
            _fail(
                label,
                f"hints must contain exactly 4 items (found "
                f"{len(data.get('hints', []))})",
                errors,
            )
            ok = False

        # difficulty must be 1-4
        difficulty = data.get("difficulty")
        if not isinstance(difficulty, int) or difficulty not in range(1, 5):
            _fail(label, f"difficulty must be integer 1-4 (got {difficulty!r})", errors)
            ok = False

        # tools_type must be in allowlist
        tt = data.get("tools_type")
        if tt not in _TOOLS_TYPE_ALLOWLIST:
            _fail(label, f"tools_type '{tt}' not in allowlist", errors)
            ok = False

        # debrief subfields
        debrief = data.get("debrief", {})
        for sub in _DEBRIEF_REQUIRED_FIELDS:
            if sub not in debrief:
                _fail(label, f"missing debrief.{sub}", errors)
                ok = False

    if ok:
        _pass(label)
    return ok


def validate_placement_test(filepath: str, errors: list) -> bool:
    """Validate content/placement_test.json.

    Checks pass_threshold <= question count, 4 options per question,
    correct_index is 0-3.
    """
    label = os.path.basename(filepath)
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        _fail(label, f"cannot read/parse: {exc}", errors)
        return False

    ok = True
    questions = data.get("questions", [])
    threshold = data.get("pass_threshold", 0)

    if threshold > len(questions):
        _fail(
            label,
            f"pass_threshold ({threshold}) exceeds question count ({len(questions)})",
            errors,
        )
        ok = False

    for i, q in enumerate(questions):
        opts = q.get("options", [])
        if len(opts) != 4:
            _fail(label, f"question {i+1} must have exactly 4 options (found {len(opts)})", errors)
            ok = False
        ci = q.get("correct_index")
        if ci not in (0, 1, 2, 3):
            _fail(label, f"question {i+1} correct_index must be 0-3 (got {ci!r})", errors)
            ok = False

    if ok:
        _pass(label)
    return ok


def validate_registry(filepath: str, ops_dir: str, errors: list) -> bool:
    """Validate content/registry.json.

    Checks required fields and that every registered id has a matching
    JSON file in content/operations/.
    """
    label = os.path.basename(filepath)
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        _fail(label, f"cannot read/parse: {exc}", errors)
        return False

    ok = True

    if "version" not in data:
        _fail(label, "missing field: version", errors)
        ok = False

    for section in ("operations", "cases"):
        entries = data.get(section, [])
        for entry in entries:
            for field in _REGISTRY_OP_FIELDS:
                if field not in entry:
                    _fail(label, f"{section} entry missing field: {field}", errors)
                    ok = False
            status = entry.get("status")
            if status not in _VALID_STATUSES:
                _fail(label, f"invalid status '{status}' in {section}", errors)
                ok = False
            op_id = entry.get("id", "")
            op_file = os.path.join(ops_dir, f"{op_id}.json")
            if not os.path.exists(op_file):
                _fail(label, f"registered id '{op_id}' has no matching JSON in operations/", errors)
                ok = False

    if ok:
        _pass(label)
    return ok


# ---------------------------------------------------------------------------
# Checksum
# ---------------------------------------------------------------------------


def write_checksums(validated_files: list, checksums_path: str) -> None:
    """Write SHA-256 checksums for all validated files to checksums.json."""
    checksums: dict = {}
    for filepath in validated_files:
        key = os.path.basename(filepath)
        checksums[key] = _sha256(filepath)
    with open(checksums_path, "w", encoding="utf-8") as fh:
        json.dump(checksums, fh, indent=2)
    print(f"[OK] checksums.json updated — {len(checksums)} file(s) verified")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    """Run all validators. Return 0 if all pass, 1 if any fail."""
    here = os.path.dirname(os.path.abspath(__file__))
    ops_dir = os.path.join(here, "content", "operations")
    content_dir = os.path.join(here, "content")
    checksums_path = os.path.join(content_dir, "checksums.json")

    errors: list = []
    validated_files: list = []

    # Validate operations
    if os.path.exists(ops_dir):
        for filename in sorted(os.listdir(ops_dir)):
            if filename.endswith(".json") and filename != ".gitkeep":
                filepath = os.path.join(ops_dir, filename)
                if validate_operation(filepath, errors):
                    validated_files.append(filepath)

    # Validate placement test
    pt_path = os.path.join(content_dir, "placement_test.json")
    if os.path.exists(pt_path):
        if validate_placement_test(pt_path, errors):
            validated_files.append(pt_path)
    else:
        _fail("placement_test.json", "file not found", errors)

    # Validate registry
    reg_path = os.path.join(content_dir, "registry.json")
    if os.path.exists(reg_path):
        if validate_registry(reg_path, ops_dir, errors):
            validated_files.append(reg_path)
    else:
        _fail("registry.json", "file not found", errors)

    if not errors:
        write_checksums(validated_files, checksums_path)
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
