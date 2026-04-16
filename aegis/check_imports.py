"""check_imports.py — AEGIS CyberForge

Scans all .py files in aegis/engine/ and aegis/utils/ and verifies
that every import is either in the stdlib allowlist or a local package.

Exit 0 if all pass. Exit 1 if any fail.
"""

import ast
import os
import sys

# ---------------------------------------------------------------------------
# Allowlists
# ---------------------------------------------------------------------------

STDLIB_ALLOWLIST: set = {
    "os", "sys", "json", "re", "datetime", "pathlib", "unittest",
    "hashlib", "base64", "collections", "itertools", "functools",
    "string", "time", "random", "math", "copy", "io", "textwrap",
    "runpy",
}

_LOCAL_PACKAGES: set = {"utils", "engine"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fail(label: str, reason: str, errors: list) -> None:
    """Record a failure and print it immediately."""
    msg = f"[FAIL] {label} — {reason}"
    print(msg)
    errors.append(msg)


def _pass(label: str) -> None:
    """Print a pass line."""
    print(f"[PASS] {label}")


# ---------------------------------------------------------------------------
# Core checker
# ---------------------------------------------------------------------------

def check_file(filepath: str, errors: list) -> bool:
    """Parse a .py file and check all imports against the allowlist.

    Returns True if the file passes.
    """
    label = os.path.relpath(filepath)
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            source = fh.read()
    except OSError as exc:
        _fail(label, f"cannot read: {exc}", errors)
        return False

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as exc:
        _fail(label, f"syntax error: {exc}", errors)
        return False

    ok = True
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top not in STDLIB_ALLOWLIST and top not in _LOCAL_PACKAGES:
                    _fail(label, f"unauthorized import: {top}", errors)
                    ok = False
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            top = node.module.split(".")[0]
            if top not in STDLIB_ALLOWLIST and top not in _LOCAL_PACKAGES:
                _fail(label, f"unauthorized import: {top}", errors)
                ok = False

    if ok:
        _pass(label)
    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    """Scan engine/ and utils/ directories. Return 0 if all pass."""
    here = os.path.dirname(os.path.abspath(__file__))
    scan_dirs = [
        os.path.join(here, "engine"),
        os.path.join(here, "utils"),
    ]

    errors: list = []
    found_any = False

    for scan_dir in scan_dirs:
        if not os.path.exists(scan_dir):
            continue
        for root, _, files in os.walk(scan_dir):
            for filename in sorted(files):
                if filename.endswith(".py"):
                    found_any = True
                    check_file(os.path.join(root, filename), errors)

    if not found_any:
        print("[WARN] No .py files found in engine/ or utils/")

    if not errors:
        print("\nAll imports OK.")
        return 0
    else:
        print(f"\n{len(errors)} import violation(s) found.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
