"""validate_content.py — AEGIS CyberForge

Validates all JSON content files against required schemas.
Generates SHA-256 checksums for each validated file.

AEGIS-specific checks vs CIPHER:
  - Scans content/cases/ (not content/operations/)
  - tools_type allowlist is AEGIS-specific (includes "none")
  - debrief requires exam_tip field
  - registry uses "cases" key
  - track field must be in {"blue", "full"}

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
    "log_filter",
    "ioc_classifier",
    "vuln_scorer",
    "process_analyzer",
    "none",
    "traffic_analyzer",
    "ioc_hunter",
    "attack_mapper",
    "rule_analyzer",
    "risk_scorer",
    "remediation_planner",
    "exec_reference",
    "notification_reference",
    "siem_correlator",
    "log_classifier",
    "hunt_analyzer",
    "mem_analyzer",
    "disk_analyzer",
    "coc_reference",
    "containment_advisor",
    "timeline_builder",
    "vuln_prioritizer",
    "patch_reference",
    "surface_analyzer",
    "sast_analyzer",
    "intel_correlator",
    "metrics_calculator",
    "compliance_mapper",
    "sla_tracker",
    "lessons_reference",
    "dashboard_filter",
}

_CASE_REQUIRED_FIELDS = (
    "id", "title", "track", "cert_objective", "xp_base", "difficulty",
    "tools_type", "challenge_data", "scenario", "challenge", "valid_answers",
    "hints", "learn", "tools", "debrief",
)

_DEBRIEF_REQUIRED_FIELDS = (
    "summary", "real_world", "next_step", "cert_link", "exam_tip",
)

_REGISTRY_CASE_FIELDS = ("id", "title", "status", "difficulty", "cert_objective")

_VALID_STATUSES = {"active", "coming_soon", "deprecated"}

_VALID_TRACKS = {"blue", "full"}


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

def validate_case(filepath: str, errors: list) -> bool:
    """Validate a single AEGIS case JSON file.

    Checks required fields, track value, hints count, valid_answers list,
    difficulty range, tools_type allowlist, debrief subfields including
    the mandatory exam_tip.
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

    # Required top-level fields
    for field in _CASE_REQUIRED_FIELDS:
        if field not in data:
            _fail(label, f"missing field: {field}", errors)
            ok = False

    if not ok:
        return False

    # track must be in AEGIS allowlist
    track = data.get("track")
    if track not in _VALID_TRACKS:
        _fail(label, f"track must be in {_VALID_TRACKS} (got {track!r})", errors)
        ok = False

    # valid_answers must be a non-empty list
    if not isinstance(data["valid_answers"], list) or len(data["valid_answers"]) == 0:
        _fail(label, "valid_answers must be a non-empty list", errors)
        ok = False

    # hints must be exactly 4 items
    if not isinstance(data["hints"], list) or len(data["hints"]) != 4:
        _fail(
            label,
            f"hints must contain exactly 4 items (found {len(data.get('hints', []))})",
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

    # debrief subfields — including mandatory exam_tip
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


def validate_registry(filepath: str, cases_dir: str, errors: list) -> bool:
    """Validate content/registry.json.

    Checks required fields and that every registered id has a matching
    JSON file in content/cases/.
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

    # AEGIS registry uses "cases" key
    if "cases" not in data:
        _fail(label, "missing 'cases' key in registry", errors)
        ok = False
    else:
        for entry in data["cases"]:
            for field in _REGISTRY_CASE_FIELDS:
                if field not in entry:
                    _fail(label, f"cases entry missing field: {field}", errors)
                    ok = False
            status = entry.get("status")
            if status not in _VALID_STATUSES:
                _fail(label, f"invalid status '{status}' in cases", errors)
                ok = False
            case_id = entry.get("id", "")
            case_file = os.path.join(cases_dir, f"{case_id}.json")
            if not os.path.exists(case_file):
                _fail(label, f"registered id '{case_id}' has no matching JSON in cases/", errors)
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
    cases_dir = os.path.join(here, "content", "cases")
    content_dir = os.path.join(here, "content")
    checksums_path = os.path.join(content_dir, "checksums.json")

    errors: list = []
    validated_files: list = []

    # Validate cases
    if os.path.exists(cases_dir):
        for filename in sorted(os.listdir(cases_dir)):
            if filename.endswith(".json") and filename != ".gitkeep":
                filepath = os.path.join(cases_dir, filename)
                if validate_case(filepath, errors):
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
        if validate_registry(reg_path, cases_dir, errors):
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
