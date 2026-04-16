"""check_imports.py — CIPHER CyberForge

Scans all .py files in engine/ and utils/ and verifies that every
top-level import is on the stdlib allowlist defined in CONSTITUTION.md §4.

Exit 0 if all files pass. Exit 1 if any file has an unauthorized import.
"""

import ast
import os
import sys

# Stdlib allowlist from CONSTITUTION.md §4
STDLIB_ALLOWLIST: set = {
    "os", "sys", "json", "re", "datetime", "pathlib", "unittest",
    "hashlib", "base64", "collections", "itertools", "functools",
    "string", "time", "random", "math", "copy", "io", "textwrap",
}

# Local packages inside cipher/ that are always allowed
_LOCAL_PACKAGES: set = {"utils", "engine"}

# Directories to scan (relative to this file's location)
_SCAN_DIRS = ("engine", "utils")


def _get_top_level_module(module_name: str) -> str:
    """Return the top-level package name from a dotted module path."""
    return module_name.split(".")[0]


def check_file(filepath: str) -> list:
    """Parse a Python file and return list of unauthorized import names."""
    with open(filepath, "r", encoding="utf-8") as fh:
        source = fh.read()

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as exc:
        return [f"<syntax error: {exc}>"]

    unauthorized: list = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = _get_top_level_module(alias.name)
                if top not in STDLIB_ALLOWLIST and top not in _LOCAL_PACKAGES:
                    unauthorized.append(top)
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            top = _get_top_level_module(node.module)
            if top not in STDLIB_ALLOWLIST and top not in _LOCAL_PACKAGES:
                unauthorized.append(top)

    return unauthorized


def main() -> int:
    """Scan engine/ and utils/ and report pass/fail per file.

    Returns 0 if all files pass, 1 if any fail.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    all_passed = True

    for scan_dir in _SCAN_DIRS:
        dirpath = os.path.join(here, scan_dir)
        if not os.path.exists(dirpath):
            continue
        for root, _dirs, files in os.walk(dirpath):
            for filename in sorted(files):
                if not filename.endswith(".py"):
                    continue
                filepath = os.path.join(root, filename)
                rel = os.path.relpath(filepath, here)
                unauthorized = check_file(filepath)
                if unauthorized:
                    for mod in unauthorized:
                        print(f"[FAIL] {rel} — unauthorized: {mod}")
                    all_passed = False
                else:
                    print(f"[PASS] {rel}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
