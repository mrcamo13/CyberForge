"""test_challenge_runner.py — LAB CyberForge unit tests.

Tests for engine functions in lab/engine/challenge_runner.py.

Run from cyberforge/lab/:
    python -m unittest tests.test_challenge_runner -v

Test groups:
    TestNormalize         (3) — normalize_output edge cases
    TestValidate          (4) — validate_output pass/fail scenarios
    TestRunSolution       (4) — _run_solution subprocess: args, timeout, errors
    TestSetupWorkspace    (3) — _setup_workspace fixture copying and reset
    TestMultiTestCase     (3) — _run_all_test_cases multi-case validation
    TestBackgroundServer  (2) — _start_test_server connect/banner
"""

import os
import sys
import socket
import tempfile
import threading
import time
import unittest

_LAB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _LAB_DIR not in sys.path:
    sys.path.insert(0, _LAB_DIR)

from engine.challenge_runner import (
    normalize_output,
    validate_output,
    _run_solution,
    _setup_workspace,
    _reset_starter,
    _run_all_test_cases,
    _start_test_server,
)


# ---------------------------------------------------------------------------
# TestNormalize
# ---------------------------------------------------------------------------

class TestNormalize(unittest.TestCase):

    def test_trailing_newline_stripped(self):
        raw = "line one\nline two\n\n\n"
        self.assertEqual(normalize_output(raw), ["line one", "line two"])

    def test_rstrip_each_line(self):
        raw = "hello   \nworld  \n"
        self.assertEqual(normalize_output(raw), ["hello", "world"])

    def test_empty_string(self):
        self.assertEqual(normalize_output(""), [])


# ---------------------------------------------------------------------------
# TestValidate
# ---------------------------------------------------------------------------

class TestValidate(unittest.TestCase):

    def test_exact_match_passes(self):
        passed, diff = validate_output("line1\nline2\n", "line1\nline2\n")
        self.assertTrue(passed)
        self.assertEqual(diff, [])

    def test_trailing_whitespace_ignored(self):
        passed, _ = validate_output("PORT 7005: OPEN   \n", "PORT 7005: OPEN\n")
        self.assertTrue(passed)

    def test_wrong_line_fails(self):
        passed, diff = validate_output("PORT 7005: CLOSED\n", "PORT 7005: OPEN\n")
        self.assertFalse(passed)
        self.assertTrue(len(diff) > 0)

    def test_missing_line_fails(self):
        passed, diff = validate_output("line1\n", "line1\nline2\n")
        self.assertFalse(passed)
        self.assertIn("<missing>", "\n".join(diff))


# ---------------------------------------------------------------------------
# TestRunSolution
# ---------------------------------------------------------------------------

class TestRunSolution(unittest.TestCase):

    def _make_workspace(self, code: str) -> str:
        ws = tempfile.mkdtemp()
        with open(os.path.join(ws, "solution.py"), "w", encoding="utf-8") as fh:
            fh.write(code)
        return ws

    def test_successful_script(self):
        ws = self._make_workspace('print("hello world")\n')
        stdout, stderr, error_msg = _run_solution(ws)
        self.assertIsNone(error_msg)
        self.assertIn("hello world", stdout)

    def test_syntax_error_captured(self):
        ws = self._make_workspace("def broken(\n")
        stdout, stderr, error_msg = _run_solution(ws)
        self.assertIsNone(error_msg)  # process ran, just errored
        self.assertTrue(len(stderr) > 0 or len(stdout) == 0)

    def test_timeout(self):
        ws = self._make_workspace("import time\ntime.sleep(60)\n")
        _, _, error_msg = _run_solution(ws, timeout=1)
        self.assertIsNotNone(error_msg)
        self.assertIn("timed out", error_msg.lower())

    def test_sys_argv_passed(self):
        """Args are forwarded to the script via sys.argv."""
        ws = self._make_workspace(
            "import sys\nprint(sys.argv[1])\nprint(sys.argv[2])\n"
        )
        stdout, _, error_msg = _run_solution(ws, args=["hello", "world"])
        self.assertIsNone(error_msg)
        lines = normalize_output(stdout)
        self.assertEqual(lines, ["hello", "world"])


# ---------------------------------------------------------------------------
# TestSetupWorkspace
# ---------------------------------------------------------------------------

class TestSetupWorkspace(unittest.TestCase):

    def test_starter_code_written(self):
        challenge_data = {
            "starter_code": "# test starter\nprint('hello')\n",
            "fixtures": [],
        }
        # Remove any existing solution.py so _setup_workspace writes fresh
        workspace = _setup_workspace(challenge_data)
        solution_path = os.path.join(workspace, "solution.py")
        if os.path.exists(solution_path):
            os.remove(solution_path)
        workspace = _setup_workspace(challenge_data)
        self.assertTrue(os.path.exists(solution_path))
        with open(solution_path, "r", encoding="utf-8") as fh:
            content = fh.read()
        self.assertIn("# test starter", content)

    def test_missing_fixture_skipped(self):
        challenge_data = {
            "starter_code": "pass\n",
            "fixtures": ["nonexistent_file.txt"],
        }
        try:
            _setup_workspace(challenge_data)
        except Exception as exc:
            self.fail(f"_setup_workspace raised {exc!r} on missing fixture")

    def test_reset_starter(self):
        """_reset_starter overwrites solution.py with starter code."""
        challenge_data = {
            "starter_code": "# original starter\n",
            "fixtures": [],
        }
        workspace = _setup_workspace(challenge_data)
        # Overwrite the file
        solution_path = os.path.join(workspace, "solution.py")
        with open(solution_path, "w", encoding="utf-8") as fh:
            fh.write("# player code\n")
        # Reset
        _reset_starter(challenge_data)
        with open(solution_path, "r", encoding="utf-8") as fh:
            content = fh.read()
        self.assertIn("# original starter", content)


# ---------------------------------------------------------------------------
# TestMultiTestCase
# ---------------------------------------------------------------------------

class TestMultiTestCase(unittest.TestCase):

    def _make_workspace_with_solution(self, code: str) -> str:
        ws = tempfile.mkdtemp()
        with open(os.path.join(ws, "solution.py"), "w", encoding="utf-8") as fh:
            fh.write(code)
        return ws

    def test_all_pass(self):
        """All test cases pass when the script handles each arg correctly."""
        ws = self._make_workspace_with_solution(
            "import sys\nprint(sys.argv[1])\n"
        )
        test_cases = [
            {"description": "case 1", "args": ["alpha"], "fixtures": [],
             "expected_output": "alpha"},
            {"description": "case 2", "args": ["beta"], "fixtures": [],
             "expected_output": "beta"},
        ]
        all_passed, results = _run_all_test_cases(ws, test_cases)
        self.assertTrue(all_passed)
        self.assertEqual(len(results), 2)

    def test_partial_fail(self):
        """If one test case fails, all_passed is False."""
        ws = self._make_workspace_with_solution(
            "import sys\nprint('always alpha')\n"
        )
        test_cases = [
            {"description": "should pass", "args": [], "fixtures": [],
             "expected_output": "always alpha"},
            {"description": "should fail", "args": [], "fixtures": [],
             "expected_output": "beta"},
        ]
        all_passed, results = _run_all_test_cases(ws, test_cases)
        self.assertFalse(all_passed)
        self.assertTrue(results[0][0])   # first passed
        self.assertFalse(results[1][0])  # second failed

    def test_empty_test_cases(self):
        """Empty test_cases list returns (True, [])."""
        ws = self._make_workspace_with_solution("pass\n")
        all_passed, results = _run_all_test_cases(ws, [])
        self.assertTrue(all_passed)
        self.assertEqual(results, [])


# ---------------------------------------------------------------------------
# TestBackgroundServer
# ---------------------------------------------------------------------------

class TestBackgroundServer(unittest.TestCase):

    def _get_free_port(self) -> int:
        """Get an available port for testing."""
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def test_plain_server_accepts_connection(self):
        """Plain server (no banner) accepts a TCP connection."""
        port = self._get_free_port()
        stop = _start_test_server(port)
        try:
            s = socket.socket()
            s.settimeout(2)
            s.connect(("127.0.0.1", port))
            s.close()
        finally:
            stop.set()

    def test_banner_server_sends_banner(self):
        """Banner server sends the expected string on connect."""
        port = self._get_free_port()
        banner = "TEST-BANNER-1.0"
        stop = _start_test_server(port, banner=banner)
        try:
            s = socket.socket()
            s.settimeout(2)
            s.connect(("127.0.0.1", port))
            data = s.recv(256).decode().strip()
            s.close()
            self.assertEqual(data, banner)
        finally:
            stop.set()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
